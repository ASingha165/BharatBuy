import {
  doc,
  getDoc,
  setDoc,
  updateDoc,
  collection,
  addDoc
} from 'firebase/firestore';
import { getFirestoreDb } from './firebase';

export interface FirestoreUserProfile {
  firebase_uid: string;
  email: string;
  organization_name: string;
  display_name: string;
  role: string;
  created_at: string;
  updated_at: string;
  auth_provider: 'password' | 'google';
}

export interface SyncProfileOptions {
  organization?: string;
  displayName?: string;
  role?: string;
  authProvider?: 'password' | 'google';
}

/**
 * Synchronizes user profile to Cloud Firestore collection: users/{firebase_uid}
 * - Guaranteed: Uses verified firebase_uid as the document ID.
 * - Guaranteed: Never overwrites existing organization/role on repeat logins.
 * - Guaranteed: Never stores passwords, secrets, or API keys.
 */
export async function syncUserProfileFirestore(
  fbUser: { uid: string; email?: string | null; displayName?: string | null },
  options: SyncProfileOptions = {}
): Promise<boolean> {
  if (typeof window === 'undefined' || !fbUser || !fbUser.uid) {
    return false;
  }

  const db = getFirestoreDb();
  if (!db) {
    return false;
  }

  try {
    const userRef = doc(db, 'users', fbUser.uid);
    const userSnap = await getDoc(userRef);
    const nowIso = new Date().toISOString();

    if (!userSnap.exists()) {
      // First-time user creation
      const profileData: FirestoreUserProfile = {
        firebase_uid: fbUser.uid,
        email: (fbUser.email || '').trim().toLowerCase(),
        organization_name: (options.organization || 'Enterprise Buyer').trim(),
        display_name: (options.displayName || fbUser.displayName || fbUser.email?.split('@')[0] || 'Enterprise User').trim(),
        role: (options.role || 'buyer').trim(),
        created_at: nowIso,
        updated_at: nowIso,
        auth_provider: options.authProvider || 'password'
      };

      await setDoc(userRef, profileData);
      console.log(`[FIRESTORE] Created user document for ${fbUser.uid}`);
    } else {
      // Existing user: safely update auth metadata without overwriting organization or role
      const existingData = userSnap.data();
      const updates: Record<string, any> = {
        updated_at: nowIso
      };

      if (options.authProvider && options.authProvider !== existingData.auth_provider) {
        updates.auth_provider = options.authProvider;
      }
      if (options.displayName && options.displayName !== existingData.display_name) {
        updates.display_name = options.displayName;
      }
      if (options.organization && (!existingData.organization_name || existingData.organization_name === 'Enterprise Buyer')) {
        updates.organization_name = options.organization;
      }

      await updateDoc(userRef, updates);
      console.log(`[FIRESTORE] Updated user document for ${fbUser.uid}`);
    }

    return true;
  } catch (err) {
    console.warn('[FIRESTORE] User profile sync note:', err);
    return false;
  }
}

/**
 * Persists a completed procurement analysis to Cloud Firestore:
 * - procurement_requests/{request_id}
 * - procurement_requests/{request_id}/items/{item_id}
 * - user_activity/{activity_id}
 */
export async function recordProcurementRequestFirestore(
  fbUser: { uid: string },
  requestData: {
    requestId: string;
    organizationName?: string;
    requirements: any;
    normalizedMetadata?: any;
    status?: string;
    items?: Array<{
      item_id: string;
      product_type?: string;
      specifications?: any;
      matched_standards?: any[];
      compliance_status?: string;
    }>;
  }
): Promise<boolean> {
  if (typeof window === 'undefined' || !fbUser || !fbUser.uid || !requestData.requestId) {
    return false;
  }

  const db = getFirestoreDb();
  if (!db) {
    return false;
  }

  try {
    const nowIso = new Date().toISOString();
    const reqRef = doc(db, 'procurement_requests', requestData.requestId);

    const docPayload = {
      firebase_uid: fbUser.uid,
      organization_name: requestData.organizationName || 'Enterprise Buyer',
      procurement_requirements: requestData.requirements,
      normalized_request_metadata: requestData.normalizedMetadata || {},
      status: requestData.status || 'COMPLETED',
      created_at: nowIso,
      updated_at: nowIso
    };

    await setDoc(reqRef, docPayload);

    // Save individual items to subcollection if present
    if (requestData.items && requestData.items.length > 0) {
      for (const item of requestData.items) {
        const itemRef = doc(db, 'procurement_requests', requestData.requestId, 'items', item.item_id);
        await setDoc(itemRef, {
          item_id: item.item_id,
          product_type: item.product_type || 'General Procurement',
          specifications: item.specifications || {},
          matched_standards: item.matched_standards || [],
          compliance_status: item.compliance_status || 'UNKNOWN',
          created_at: nowIso
        });
      }
    }

    // Log lightweight user activity entry
    await recordUserActivityFirestore(fbUser, 'PROCUREMENT_ANALYZED', requestData.requestId);

    console.log(`[FIRESTORE] Recorded procurement request ${requestData.requestId} for ${fbUser.uid}`);
    return true;
  } catch (err) {
    console.warn('[FIRESTORE] Error recording procurement request:', err);
    return false;
  }
}

/**
 * Records lightweight user activity entry in: user_activity/{activity_id}
 */
export async function recordUserActivityFirestore(
  fbUser: { uid: string },
  action: string,
  requestId?: string
): Promise<boolean> {
  if (typeof window === 'undefined' || !fbUser || !fbUser.uid) {
    return false;
  }

  const db = getFirestoreDb();
  if (!db) {
    return false;
  }

  try {
    const nowIso = new Date().toISOString();
    const activityCollection = collection(db, 'user_activity');

    await addDoc(activityCollection, {
      firebase_uid: fbUser.uid,
      action: action.trim().toUpperCase(),
      request_id: requestId || null,
      timestamp: nowIso
    });

    return true;
  } catch (err) {
    console.warn('[FIRESTORE] User activity recording note:', err);
    return false;
  }
}
