import axios from 'axios';
import {
  RecommendationResponse,
  StandardDetailResponse,
  GraphResponse,
  HealthStatus,
  ProcurementAnalysisRequest,
  ProcurementAnalysisResponse,
  SourceEvidenceResponse,
  SourceVerificationResponse,
  ManualVerifyRequest,
  AuthUser,
  AuthResponse,
  SignUpPayload,
  SignInPayload
} from '../types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
  timeout: 120000, // 120s — accommodates Gemini synthesis + full procurement pipeline
});

// Set Authorization token on apiClient headers
export const setAuthToken = (token: string | null) => {
  if (token && typeof token === 'string' && token.trim().length > 0 && token !== 'null' && token !== 'undefined') {
    apiClient.defaults.headers.common['Authorization'] = `Bearer ${token.trim()}`;
  } else {
    delete apiClient.defaults.headers.common['Authorization'];
  }
};
// Dynamic token injection via Axios request interceptor:
// Ensures fresh, valid Firebase ID tokens are attached to outgoing API requests
apiClient.interceptors.request.use(
  async (config) => {
    if (typeof window !== 'undefined') {
      try {
        const { getFirebaseAuth } = await import('./firebase');
        const fbAuth = getFirebaseAuth();
        if (fbAuth && fbAuth.currentUser) {
          const freshToken = await fbAuth.currentUser.getIdToken();
          if (freshToken && typeof freshToken === 'string' && freshToken.trim().length > 0) {
            config.headers = config.headers || {};
            config.headers['Authorization'] = `Bearer ${freshToken.trim()}`;
          }
        }
      } catch (err) {
        console.warn('[API] Could not dynamically refresh Firebase ID token:', err);
      }
    }
    return config;
  },
  (error) => Promise.reject(error)
);

export const getHealth = async (): Promise<HealthStatus> => {
  const response = await apiClient.get<HealthStatus>('/health');
  return response.data;
};
export const getRecommendations = async (
  query: string,
  topK: number = 10
): Promise<RecommendationResponse> => {
  const response = await apiClient.post<RecommendationResponse>('/recommend', {
    query,
    top_k: topK,
  });
  return response.data;
};
export const getStandardDetails = async (standardId: string): Promise<StandardDetailResponse> => {
  const response = await apiClient.get<StandardDetailResponse>(`/standards/${standardId}`);
  return response.data;
};

export const getGraphData = async (standardId: string): Promise<GraphResponse> => {
  const response = await apiClient.get<GraphResponse>(`/graph/${standardId}`);
  return response.data;
};

export const analyzeProcurement = async (
  payload: ProcurementAnalysisRequest
): Promise<ProcurementAnalysisResponse> => {
  // Serialize requirements precisely — exclude blank rows and coerce quantity to number
  const serializedRequirements = (payload.requirements ?? [])
    .filter((r) => r.item && r.item.trim().length > 0)
    .map((r) => ({
      item: r.item.trim(),
      quantity: r.quantity != null ? Number(r.quantity) : 1,
      unit: r.unit ?? '',
      specifications: r.specifications ?? '',
    }));

  const backendPayload = {
    company: payload.company.trim(),
    requirements: serializedRequirements,
    top_k_per_item: payload.top_k_per_item ?? 5,
    ...(payload.description ? { description: payload.description } : {})
    ,...(payload.buyer_latitude != null ? { buyer_latitude: payload.buyer_latitude } : {})
    ,...(payload.buyer_longitude != null ? { buyer_longitude: payload.buyer_longitude } : {})
    ,...(payload.search_radius_km != null ? { search_radius_km: payload.search_radius_km } : {})
    ,...(payload.budget_amount != null ? { budget_amount: payload.budget_amount } : {})
    ,...(payload.budget_tolerance_pct != null ? { budget_tolerance_pct: payload.budget_tolerance_pct } : {})
  };

  const response = await apiClient.post<ProcurementAnalysisResponse>(
    '/procurement/analyze',
    backendPayload,
    { timeout: 120000 }
  );
  return response.data;
};

export const getSources = async (params?: Record<string, string>): Promise<any[]> => {
  const response = await apiClient.get<any[]>('/procurement/sources', { params });
  return response.data;
};

export const getSourceDetails = async (source_id: string): Promise<any> => {
  const response = await apiClient.get<any>(`/procurement/sources/${source_id}`);
  return response.data;
};

export const getSourceEvidence = async (source_id: string): Promise<SourceEvidenceResponse> => {
  const response = await apiClient.get<SourceEvidenceResponse>(`/procurement/sources/${source_id}/evidence`);
  return response.data;
};

export const getSourceVerification = async (source_id: string): Promise<SourceVerificationResponse> => {
  const response = await apiClient.get<SourceVerificationResponse>(`/procurement/sources/${source_id}/verification`);
  return response.data;
};

export const submitManualVerification = async (
  source_id: string,
  payload: ManualVerifyRequest
): Promise<SourceVerificationResponse> => {
  const response = await apiClient.post<SourceVerificationResponse>(`/procurement/sources/${source_id}/verify`, payload);
  return response.data;
};

export const getHealthStatus = getHealth;
export const getSourcingSources = getSources;

// Authentication APIs
export const signUpApi = async (payload: SignUpPayload): Promise<AuthResponse> => {
  const response = await apiClient.post<AuthResponse>('/auth/signup', payload);
  if (response.data.token) {
    setAuthToken(response.data.token);
  }
  return response.data;
};

export const signInApi = async (payload: SignInPayload): Promise<AuthResponse> => {
  const response = await apiClient.post<AuthResponse>('/auth/signin', payload);
  if (response.data.token) {
    setAuthToken(response.data.token);
  }
  return response.data;
};

export const signOutApi = async (): Promise<{ message: string }> => {
  try {
    const response = await apiClient.post<{ message: string }>('/auth/signout');
    setAuthToken(null);
    return response.data;
  } catch (error) {
    setAuthToken(null);
    return { message: 'Signed out' };
  }
};

export const getCurrentUserApi = async (token?: string | null): Promise<AuthUser> => {
  const headers: Record<string, string> = {};
  if (token && typeof token === 'string' && token.trim().length > 0) {
    headers['Authorization'] = `Bearer ${token.trim()}`;
    setAuthToken(token);
  }
  const response = await apiClient.get<AuthUser>('/auth/me', { headers });
  return response.data;
};

export const syncFirebaseProfileApi = async (
  payload: { name?: string; organization?: string },
  token?: string | null
): Promise<AuthResponse> => {
  const headers: Record<string, string> = {};
  if (token && typeof token === 'string' && token.trim().length > 0) {
    headers['Authorization'] = `Bearer ${token.trim()}`;
    setAuthToken(token);
  }
  const response = await apiClient.post<AuthResponse>('/auth/firebase-sync', payload, { headers });
  return response.data;
};
