import { initializeApp, getApps, getApp, FirebaseApp } from 'firebase/app';
import { getAuth, Auth, GoogleAuthProvider } from 'firebase/auth';
import { getFirestore, Firestore } from 'firebase/firestore';
import { getAnalytics, Analytics, isSupported } from 'firebase/analytics';

export interface FirebaseClientConfig {
  apiKey: string;
  authDomain: string;
  projectId: string;
  storageBucket: string;
  messagingSenderId: string;
  appId: string;
  measurementId?: string;
}

/**
 * Safely retrieve Firebase client configuration from environment variables.
 * Returns null if required configuration variables are missing.
 * Never fabricates or hardcodes secrets.
 */
export function getFirebaseConfig(): FirebaseClientConfig | null {
  const apiKey = process.env.NEXT_PUBLIC_FIREBASE_API_KEY;
  const projectId = process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID;

  if (!apiKey || !projectId) {
    return null;
  }

  return {
    apiKey,
    authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN || `${projectId}.firebaseapp.com`,
    projectId,
    storageBucket: process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET || `${projectId}.firebasestorage.app`,
    messagingSenderId: process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID || '',
    appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID || '',
    measurementId: process.env.NEXT_PUBLIC_FIREBASE_MEASUREMENT_ID || undefined
  };
}

/**
 * Checks whether Firebase client is fully configured and running in a browser environment.
 */
export function isFirebaseConfigured(): boolean {
  if (typeof window === 'undefined') {
    return false;
  }
  return !!process.env.NEXT_PUBLIC_FIREBASE_API_KEY && !!process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID;
}

let appInstance: FirebaseApp | null = null;
let authInstance: Auth | null = null;
let firestoreInstance: Firestore | null = null;
let googleProviderInstance: GoogleAuthProvider | null = null;

/**
 * Safe singleton getter for FirebaseApp.
 * NEVER initializes during SSR (Node.js server context).
 */
export function getFirebaseApp(): FirebaseApp | null {
  if (typeof window === 'undefined') {
    return null;
  }
  if (appInstance) {
    return appInstance;
  }
  const config = getFirebaseConfig();
  if (!config) {
    return null;
  }
  const existingApps = getApps();
  if (existingApps.length > 0) {
    appInstance = getApp();
  } else {
    appInstance = initializeApp(config);
  }
  return appInstance;
}

/**
 * Safe singleton getter for FirebaseAuth.
 * Returns null on the server or when Firebase is unconfigured.
 */
export function getFirebaseAuth(): Auth | null {
  if (typeof window === 'undefined') {
    return null;
  }
  if (authInstance) {
    return authInstance;
  }
  const fbApp = getFirebaseApp();
  if (!fbApp) {
    return null;
  }
  try {
    authInstance = getAuth(fbApp);
    return authInstance;
  } catch (err) {
    console.warn('[FIREBASE] Error initializing client auth:', err);
    return null;
  }
}

/**
 * Safe singleton getter for Cloud Firestore database.
 * Returns null on the server or when Firebase is unconfigured.
 */
export function getFirestoreDb(): Firestore | null {
  if (typeof window === 'undefined') {
    return null;
  }
  if (firestoreInstance) {
    return firestoreInstance;
  }
  const fbApp = getFirebaseApp();
  if (!fbApp) {
    return null;
  }
  try {
    firestoreInstance = getFirestore(fbApp);
    return firestoreInstance;
  } catch (err) {
    console.warn('[FIREBASE] Error initializing client Firestore:', err);
    return null;
  }
}

/**
 * Safe singleton getter for GoogleAuthProvider.
 */
export function getGoogleAuthProvider(): GoogleAuthProvider | null {
  if (typeof window === 'undefined') {
    return null;
  }
  if (!googleProviderInstance) {
    googleProviderInstance = new GoogleAuthProvider();
    googleProviderInstance.setCustomParameters({
      prompt: 'select_account'
    });
  }
  return googleProviderInstance;
}

// Backwards-compatible safe exports
export const app: FirebaseApp | null = typeof window !== 'undefined' ? getFirebaseApp() : null;
export const auth: Auth | null = typeof window !== 'undefined' ? getFirebaseAuth() : null;
export const db: Firestore | null = typeof window !== 'undefined' ? getFirestoreDb() : null;

// Safe client-side analytics initialization
let analytics: Analytics | null = null;
if (typeof window !== 'undefined') {
  isSupported().then((supported) => {
    const currentApp = getFirebaseApp();
    if (supported && currentApp) {
      analytics = getAnalytics(currentApp);
    }
  }).catch(() => {
    // Analytics optional in local/restricted environments
  });
}

export { analytics };
