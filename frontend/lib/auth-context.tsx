'use client';

import React, { createContext, useContext, useState, useEffect, ReactNode, useCallback } from 'react';
import {
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signInWithPopup,
  signOut as firebaseSignOut,
  onAuthStateChanged,
  updateProfile,
  User as FirebaseUser
} from 'firebase/auth';
import { getFirebaseAuth, getGoogleAuthProvider, isFirebaseConfigured } from './firebase';
import { AuthUser, SignInPayload, SignUpPayload } from '../types';
import {
  getCurrentUserApi,
  signOutApi,
  syncFirebaseProfileApi,
  setAuthToken
} from './api';
import { syncUserProfileFirestore } from './firestore-service';

export type AuthState = 'INITIALIZING' | 'SIGNED_IN' | 'SIGNED_OUT';

interface AuthContextType {
  user: AuthUser | null;
  loading: boolean;
  authState: AuthState;
  isAuthenticated: boolean;
  isConfigured: boolean;
  signIn: (payload: SignInPayload) => Promise<void>;
  signUp: (payload: SignUpPayload) => Promise<void>;
  signInWithGoogle: () => Promise<void>;
  signOut: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [authState, setAuthState] = useState<AuthState>('INITIALIZING');
  const [isConfigured, setIsConfigured] = useState<boolean>(true);

  /**
   * Refresh the authenticated user profile.
   * STRICT GUARANTEE: Never calls protected backend endpoints if signed out.
   */
  const refreshUser = useCallback(async () => {
    const firebaseAuth = getFirebaseAuth();
    const currentFbUser = firebaseAuth?.currentUser;

    if (!currentFbUser) {
      // Signed out: set state immediately without calling protected APIs
      setAuthToken(null);
      setUser(null);
      setAuthState('SIGNED_OUT');
      setLoading(false);
      return;
    }

    try {
      const token = await currentFbUser.getIdToken();
      setAuthToken(token);
      const currentUser = await getCurrentUserApi(token);
      setUser(currentUser);
      setAuthState('SIGNED_IN');
    } catch (err) {
      console.warn('[AUTH] Error refreshing user profile from backend:', err);
      setUser({
        id: currentFbUser.uid,
        email: currentFbUser.email || '',
        name: currentFbUser.displayName || (currentFbUser.email ? currentFbUser.email.split('@')[0] : 'Enterprise User'),
        organization: 'Enterprise Buyer',
        created_at: new Date().toISOString()
      });
      setAuthState('SIGNED_IN');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    // 1. Guard against Server-Side Rendering execution
    if (typeof window === 'undefined') {
      return;
    }

    const firebaseAuth = getFirebaseAuth();
    if (!firebaseAuth) {
      // Firebase configuration is missing or incomplete
      setIsConfigured(false);
      setAuthToken(null);
      setUser(null);
      setAuthState('SIGNED_OUT');
      setLoading(false);
      return;
    }

    setIsConfigured(true);

    // 2. Attach client-side Firebase Auth state listener
    const unsubscribe = onAuthStateChanged(
      firebaseAuth,
      async (fbUser: FirebaseUser | null) => {
        if (fbUser) {
          // AUTH STATE = SIGNED_IN
          try {
            const token = await fbUser.getIdToken();
            setAuthToken(token);

            // Fetch or sync user profile with valid token explicitly provided
            try {
              const currentUser = await getCurrentUserApi(token);
              setUser(currentUser);
            } catch (syncErr) {
              console.warn('[AUTH] Profile sync note during auth state change:', syncErr);
              setUser({
                id: fbUser.uid,
                email: fbUser.email || '',
                name: fbUser.displayName || (fbUser.email ? fbUser.email.split('@')[0] : 'Enterprise User'),
                organization: 'Enterprise Buyer',
                created_at: new Date().toISOString()
              });
            }
            setAuthState('SIGNED_IN');
          } catch (tokenErr) {
            console.warn('[AUTH] Error obtaining Firebase token:', tokenErr);
            setAuthToken(null);
            setUser(null);
            setAuthState('SIGNED_OUT');
          } finally {
            setLoading(false);
          }
        } else {
          // AUTH STATE = SIGNED_OUT
          // STRICT RULE: No protected API call is made when user is signed out
          setAuthToken(null);
          setUser(null);
          setAuthState('SIGNED_OUT');
          setLoading(false);
        }
      },
      (error) => {
        console.warn('[AUTH] Firebase onAuthStateChanged note:', error);
        setAuthToken(null);
        setUser(null);
        setAuthState('SIGNED_OUT');
        setLoading(false);
      }
    );

    return () => {
      unsubscribe();
    };
  }, []);

  const signIn = async (payload: SignInPayload) => {
    const firebaseAuth = getFirebaseAuth();

    if (!firebaseAuth) {
      throw new Error(
        'Firebase Authentication is not configured locally. Please supply NEXT_PUBLIC_FIREBASE_* variables in frontend/.env.local.'
      );
    }

    try {
      // 1. Authenticate with Firebase Authentication
      const userCredential = await signInWithEmailAndPassword(firebaseAuth, payload.email, payload.password);
      const token = await userCredential.user.getIdToken();
      setAuthToken(token);

      // 2. Synchronize profile with backend database
      try {
        const res = await syncFirebaseProfileApi(
          { name: userCredential.user.displayName || undefined },
          token
        );
        setUser(res.user);
      } catch (syncErr) {
        console.warn('[AUTH] Background profile sync note:', syncErr);
        setUser({
          id: userCredential.user.uid,
          email: userCredential.user.email || payload.email,
          name: userCredential.user.displayName || payload.email.split('@')[0],
          organization: 'Enterprise Buyer',
          created_at: new Date().toISOString()
        });
      }
      // 3. Synchronize user profile with Firestore
      try {
        await syncUserProfileFirestore(userCredential.user, {
          displayName: userCredential.user.displayName || undefined,
          authProvider: 'password'
        });
      } catch (fsErr) {
        console.warn('[FIRESTORE] Background profile sync note:', fsErr);
      }

      setAuthState('SIGNED_IN');
    } catch (fbErr: any) {
      if (
        fbErr.code === 'auth/user-not-found' ||
        fbErr.code === 'auth/wrong-password' ||
        fbErr.code === 'auth/invalid-credential'
      ) {
        throw new Error('Invalid work email or password.');
      }
      if (fbErr.code === 'auth/too-many-requests') {
        throw new Error('Access temporarily disabled due to many failed attempts. Try again later.');
      }
      if (fbErr.code === 'auth/invalid-email') {
        throw new Error('Please enter a valid work email address.');
      }
      throw new Error(fbErr?.message || 'Authentication failed. Please verify your credentials.');
    }
  };

  const signUp = async (payload: SignUpPayload) => {
    const firebaseAuth = getFirebaseAuth();

    if (!firebaseAuth) {
      throw new Error(
        'Firebase Authentication is not configured locally. Please supply NEXT_PUBLIC_FIREBASE_* variables in frontend/.env.local.'
      );
    }

    try {
      // 1. Create user in Firebase Authentication
      const userCredential = await createUserWithEmailAndPassword(firebaseAuth, payload.email, payload.password);
      if (payload.name) {
        try {
          await updateProfile(userCredential.user, { displayName: payload.name });
        } catch (profileErr) {
          console.warn('[AUTH] Firebase updateProfile note:', profileErr);
        }
      }
      const token = await userCredential.user.getIdToken();
      setAuthToken(token);

      // 2. Synchronize user profile with backend database
      try {
        const res = await syncFirebaseProfileApi(
          {
            name: payload.name,
            organization: payload.organization
          },
          token
        );
        setUser(res.user);
      } catch (syncErr) {
        console.warn('[AUTH] Background profile sync note:', syncErr);
        setUser({
          id: userCredential.user.uid,
          email: userCredential.user.email || payload.email,
          name: payload.name || userCredential.user.displayName || payload.email.split('@')[0],
          organization: payload.organization || 'Enterprise Buyer',
          created_at: new Date().toISOString()
        });
      }

      // 3. Synchronize user profile with Cloud Firestore
      try {
        await syncUserProfileFirestore(userCredential.user, {
          displayName: payload.name,
          organization: payload.organization,
          authProvider: 'password'
        });
      } catch (fsErr) {
        console.warn('[FIRESTORE] Background signup sync note:', fsErr);
      }

      setAuthState('SIGNED_IN');
    } catch (fbErr: any) {
      if (fbErr.code === 'auth/email-already-in-use') {
        throw new Error('An account with this work email already exists.');
      }
      if (fbErr.code === 'auth/weak-password') {
        throw new Error('Password must be at least 8 characters long.');
      }
      if (fbErr.code === 'auth/invalid-email') {
        throw new Error('Please enter a valid work email address.');
      }
      throw new Error(fbErr?.message || 'Registration failed. Please check your details and try again.');
    }
  };

  /**
   * Google Sign-In using Firebase Authentication GoogleAuthProvider.
   * Derives verified identity from Google credentials and synchronizes with Neon & Firestore.
   */
  const signInWithGoogle = async () => {
    const firebaseAuth = getFirebaseAuth();

    if (!firebaseAuth) {
      throw new Error(
        'Firebase Authentication is not configured locally. Please supply NEXT_PUBLIC_FIREBASE_* variables in frontend/.env.local.'
      );
    }

    const provider = getGoogleAuthProvider();
    if (!provider) {
      throw new Error('Google Authentication provider could not be initialized.');
    }

    try {
      // 1. Authenticate with Google via popup
      const result = await signInWithPopup(firebaseAuth, provider);
      const fbUser = result.user;
      const token = await fbUser.getIdToken();
      setAuthToken(token);

      // 2. Synchronize user profile with backend database
      try {
        const res = await syncFirebaseProfileApi(
          {
            name: fbUser.displayName || undefined
          },
          token
        );
        setUser(res.user);
      } catch (syncErr) {
        console.warn('[AUTH] Background Google profile sync note:', syncErr);
        setUser({
          id: fbUser.uid,
          email: fbUser.email || '',
          name: fbUser.displayName || (fbUser.email ? fbUser.email.split('@')[0] : 'Google User'),
          organization: 'Enterprise Buyer',
          created_at: new Date().toISOString()
        });
      }

      // 3. Synchronize user profile with Cloud Firestore
      try {
        await syncUserProfileFirestore(fbUser, {
          displayName: fbUser.displayName || undefined,
          authProvider: 'google'
        });
      } catch (fsErr) {
        console.warn('[FIRESTORE] Background Google sync note:', fsErr);
      }

      setAuthState('SIGNED_IN');
    } catch (fbErr: any) {
      if (fbErr.code === 'auth/popup-closed-by-user') {
        throw new Error('Google sign-in was cancelled.');
      }
      if (fbErr.code === 'auth/popup-blocked') {
        throw new Error('Sign-in popup was blocked by your browser. Please allow popups for this site and try again.');
      }
      if (fbErr.code === 'auth/operation-not-allowed') {
        throw new Error('Google Sign-In is not enabled in Firebase Console. Please enable Google under Authentication → Sign-in method.');
      }
      if (fbErr.code === 'auth/unauthorized-domain') {
        throw new Error('This domain is not authorized for Google Sign-In in Firebase Console. Add localhost to Authorized Domains.');
      }
      if (fbErr.code === 'auth/account-exists-with-different-credential') {
        throw new Error('An account already exists with the same email address using a different sign-in method.');
      }
      if (fbErr.code === 'auth/network-request-failed') {
        throw new Error('Network error during Google sign-in. Please check your internet connection.');
      }
      throw new Error(fbErr?.message || 'Google Sign-In failed. Please try again.');
    }
  };

  const signOut = async () => {
    const firebaseAuth = getFirebaseAuth();
    if (firebaseAuth) {
      try {
        await firebaseSignOut(firebaseAuth);
      } catch (err) {
        console.warn('[AUTH] Firebase signOut note:', err);
      }
    }
    try {
      await signOutApi();
    } finally {
      setUser(null);
      setAuthState('SIGNED_OUT');
      setAuthToken(null);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        authState,
        isAuthenticated: !!user,
        isConfigured,
        signIn,
        signUp,
        signInWithGoogle,
        signOut,
        refreshUser
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
