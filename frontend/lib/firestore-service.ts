import {
  doc,
  getDoc,
  setDoc,
  updateDoc,
  collection,
  addDoc,
  getDocs,
  query,
  orderBy,
  deleteDoc,
  serverTimestamp
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

export interface ProcurementHistoryRecord {
  procurement_id: string;
  uid: string;
  company_name: string;
  analysis_created_at: string;
  updated_at: string;
  request_status: string;
  request: {
    description?: string;
    requirements: any[];
  };
  items: any[];
  budget: {
    total_budget?: number | null;
    expected_unit_cost?: number | null;
    tolerance?: number | null;
  };
  location: {
    latitude?: number | null;
    longitude?: number | null;
    location_label?: string;
  };
  search: {
    radius?: number | null;
    search_expansion_status?: string;
  };
  sourcing: {
    sourcing_strategy: string;
    official_record_count: number;
    verified_supplier_count: number;
    recommendation_summary: string;
  };
  analysis: {
    readiness?: number;
    standards_matches: any[];
    supplier_results: any[];
    cost_results: any[];
    verification_results: any[];
    response_snapshot: any;
  };
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

export async function recordProcurementHistoryFirestore(
  fbUser: { uid: string },
  request: any,
  response: any
): Promise<boolean> {
  if (typeof window === 'undefined' || !fbUser?.uid || !response?.request_id) return false;
  const db = getFirestoreDb();
  if (!db) return false;

  const nowIso = new Date().toISOString();
  const recommendations = response.recommendations || [];
  const record: ProcurementHistoryRecord = {
    procurement_id: response.request_id,
    uid: fbUser.uid,
    company_name: response.company || request.company || 'Enterprise Buyer',
    analysis_created_at: serverTimestamp() as any,
    updated_at: serverTimestamp() as any,
    request_status: 'COMPLETED',
    request: {
      description: request.description,
      requirements: request.requirements || []
    },
    items: (response.items || []).map((item: any) => ({
      item_id: item.item_id,
      item_name: item.item_name,
      quantity: item.normalized_profile?.quantity,
      unit: item.normalized_profile?.unit,
      specifications: item.normalized_profile?.specifications,
      applicable_standards: (item.standards || []).map((standard: any) => standard.is_code),
      compliance_status: item.compliance_status
    })),
    budget: {
      total_budget: request.budget_amount ?? null,
      expected_unit_cost: null,
      tolerance: request.budget_tolerance_pct ?? null
    },
    location: {
      latitude: request.buyer_latitude ?? null,
      longitude: request.buyer_longitude ?? null,
      location_label: response.buyer_location?.city || 'Not provided'
    },
    search: {
      radius: request.search_radius_km ?? null,
      search_expansion_status: response.search_expansion?.message || 'Not expanded'
    },
    sourcing: {
      sourcing_strategy: response.package_sourcing?.strategy || 'ITEM_BY_ITEM_SOURCING',
      official_record_count: (response.official_records || []).length,
      verified_supplier_count: recommendations.filter((item: any) => item.vendor_identity?.gstin_verification?.status === 'VERIFIED').length,
      recommendation_summary: response.package_sourcing?.explanation || ''
    },
    analysis: {
      readiness: response.package_evaluation?.overall_readiness_score,
      standards_matches: (response.items || []).flatMap((item: any) => (item.standards || []).map((standard: any) => standard.is_code)),
      supplier_results: recommendations,
      cost_results: recommendations.map((item: any) => item.cost_assessment),
      verification_results: recommendations.map((item: any) => item.vendor_identity?.gstin_verification),
      response_snapshot: response
    }
  };

  try {
    await setDoc(doc(db, 'users', fbUser.uid, 'procurement_history', response.request_id), record);
    return true;
  } catch (err) {
    console.warn('[FIRESTORE] Procurement history save note:', err);
    return false;
  }
}

export async function listProcurementHistoryFirestore(
  fbUser: { uid: string }
): Promise<{ records: ProcurementHistoryRecord[]; error: boolean }> {
  if (typeof window === 'undefined' || !fbUser?.uid) return { records: [], error: true };
  const db = getFirestoreDb();
  if (!db) return { records: [], error: true };
  try {
    const historyQuery = query(collection(db, 'users', fbUser.uid, 'procurement_history'), orderBy('analysis_created_at', 'desc'));
    const snapshot = await getDocs(historyQuery);
    const records = snapshot.docs.map((item) => {
      const data = item.data() as any;
      const normalizeTimestamp = (value: any): string => {
        if (value?.toDate) return value.toDate().toISOString();
        return typeof value === 'string' ? value : new Date(0).toISOString();
      };
      return {
        ...data,
        analysis_created_at: normalizeTimestamp(data.analysis_created_at),
        updated_at: normalizeTimestamp(data.updated_at)
      } as ProcurementHistoryRecord;
    });
    return { records, error: false };
  } catch (err) {
    console.warn('[FIRESTORE] Procurement history list note:', err);
    return { records: [], error: true };
  }
}

export async function deleteProcurementHistoryFirestore(uid: string, procurementId: string): Promise<boolean> {
  if (typeof window === 'undefined' || !uid || !procurementId) return false;
  const db = getFirestoreDb();
  if (!db) return false;
  try {
    await deleteDoc(doc(db, 'users', uid, 'procurement_history', procurementId));
    return true;
  } catch (err) {
    console.warn('[FIRESTORE] Procurement history delete note:', err);
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
