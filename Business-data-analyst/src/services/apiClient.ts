/**
 * InsightFlow Centralized API Client
 * Connects Frontend directly to FastAPI Backend with:
 * - Environment Variable configuration (VITE_API_URL / VITE_API_BASE_URL)
 * - Authenticated Bearer token injection
 * - Automatic exponential backoff retry for transient network / 5xx errors
 * - Upload progress tracking for large datasets
 * - Zero secret leakage to the client
 */

import { supabaseService } from './supabase';

export interface ApiClientConfig {
  baseUrl?: string;
  timeoutMs?: number;
  maxRetries?: number;
  retryDelayMs?: number;
}

export interface ProgressCallback {
  (progressPercent: number, loadedBytes: number, totalBytes: number): void;
}

export class ApiError extends Error {
  public status: number;
  public details?: any;

  constructor(message: string, status: number = 500, details?: any) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.details = details;
  }
}

class CentralizedApiClient {
  private baseUrl: string;
  private timeoutMs: number;
  private maxRetries: number;
  private retryDelayMs: number;

  constructor(config?: ApiClientConfig) {
    const rawUrl =
      import.meta.env.VITE_API_URL ||
      import.meta.env.VITE_API_BASE_URL ||
      (import.meta.env.PROD
        ? 'https://insightflow-backend-lx2d.onrender.com/api/v1'
        : 'http://localhost:8000/api/v1');

    // Normalize base URL: strip trailing slash
    this.baseUrl = (config?.baseUrl || rawUrl).replace(/\/+$/, '');
    this.timeoutMs = config?.timeoutMs || 45000;
    this.maxRetries = config?.maxRetries || 2;
    this.retryDelayMs = config?.retryDelayMs || 800;
  }

  public getBaseUrl(): string {
    return this.baseUrl;
  }

  /**
   * Retrieves active auth Bearer token from Supabase session or localStorage
   */
  private async getAuthToken(): Promise<string | null> {
    try {
      const session = await supabaseService.getSession();
      if (session?.access_token) {
        return session.access_token;
      }
    } catch {
      // ignore
    }

    try {
      const stored = localStorage.getItem('insightflow_user');
      if (stored) {
        const parsed = JSON.parse(stored);
        if (parsed.token) return parsed.token;
      }
    } catch {
      // ignore
    }

    return null;
  }

  /**
   * Build complete URL
   */
  private buildUrl(path: string): string {
    if (path.startsWith('http://') || path.startsWith('https://')) {
      return path;
    }
    const cleanPath = path.startsWith('/') ? path : `/${path}`;
    return `${this.baseUrl}${cleanPath}`;
  }

  /**
   * Sleep helper for exponential backoff retry
   */
  private sleep(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  /**
   * Execute authenticated fetch request with retry and timeout
   */
  public async request<T>(
    endpoint: string,
    options: RequestInit = {},
    retryCount: number = 0
  ): Promise<T> {
    const url = this.buildUrl(endpoint);
    const token = await this.getAuthToken();

    const headers: Record<string, string> = {
      Accept: 'application/json',
      ...((options.headers as Record<string, string>) || {})
    };

    // Inject Bearer token
    if (token && !headers['Authorization']) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    // Only set Content-Type if body is not FormData
    if (!(options.body instanceof FormData) && !headers['Content-Type']) {
      headers['Content-Type'] = 'application/json';
    }

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeoutMs);

    try {
      const response = await fetch(url, {
        ...options,
        headers,
        signal: controller.signal
      });

      clearTimeout(timeoutId);

      // Handle non-2xx HTTP responses
      if (!response.ok) {
        let errorMsg = `HTTP Error ${response.status}: ${response.statusText}`;
        let details: any = null;

        try {
          const errorJson = await response.json();
          details = errorJson;
          if (errorJson.detail) {
            errorMsg =
              typeof errorJson.detail === 'string'
                ? errorJson.detail
                : errorJson.detail.message || JSON.stringify(errorJson.detail);
          } else if (errorJson.message) {
            errorMsg = errorJson.message;
          }
        } catch {
          // Response body was not JSON
        }

        // Auto retry on 502, 503, 504, 429
        const isTransient = [502, 503, 504, 429].includes(response.status);
        if (isTransient && retryCount < this.maxRetries) {
          const delay = this.retryDelayMs * Math.pow(2, retryCount);
          await this.sleep(delay);
          return this.request<T>(endpoint, options, retryCount + 1);
        }

        throw new ApiError(errorMsg, response.status, details);
      }

      // Handle 204 No Content
      if (response.status === 204) {
        return {} as T;
      }

      return await response.json();
    } catch (err: any) {
      clearTimeout(timeoutId);

      if (err instanceof ApiError) {
        throw err;
      }

      // Handle network errors or timeout with retry
      const isAbort = err.name === 'AbortError';
      const msg = isAbort
        ? `Request timeout after ${this.timeoutMs}ms`
        : err.message || 'Network connection failure';

      if (retryCount < this.maxRetries && !isAbort) {
        const delay = this.retryDelayMs * Math.pow(2, retryCount);
        await this.sleep(delay);
        return this.request<T>(endpoint, options, retryCount + 1);
      }

      throw new ApiError(msg, isAbort ? 408 : 0, { originalError: err.message });
    }
  }

  /**
   * Upload file with upload progress tracking via XMLHttpRequest
   */
  public uploadWithProgress<T>(
    endpoint: string,
    formData: FormData,
    onProgress?: ProgressCallback
  ): Promise<T> {
    return new Promise(async (resolve, reject) => {
      const url = this.buildUrl(endpoint);
      const token = await this.getAuthToken();
      const xhr = new XMLHttpRequest();

      xhr.open('POST', url);
      xhr.timeout = 120000; // 2 minutes for dataset uploads

      if (token) {
        xhr.setRequestHeader('Authorization', `Bearer ${token}`);
      }
      xhr.setRequestHeader('Accept', 'application/json');

      if (onProgress && xhr.upload) {
        xhr.upload.onprogress = (event) => {
          if (event.lengthComputable) {
            const percent = Math.round((event.loaded / event.total) * 100);
            onProgress(percent, event.loaded, event.total);
          }
        };
      }

      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            const json = JSON.parse(xhr.responseText);
            resolve(json);
          } catch {
            resolve({} as T);
          }
        } else {
          let errorMsg = `Upload failed [${xhr.status}]: ${xhr.statusText}`;
          try {
            const json = JSON.parse(xhr.responseText);
            if (json.detail) {
              errorMsg = typeof json.detail === 'string' ? json.detail : json.detail.message || JSON.stringify(json.detail);
            }
          } catch {
            // ignore
          }
          reject(new ApiError(errorMsg, xhr.status));
        }
      };

      xhr.onerror = () => {
        reject(new ApiError('Network failure during file upload', 0));
      };

      xhr.ontimeout = () => {
        reject(new ApiError('File upload timed out', 408));
      };

      xhr.send(formData);
    });
  }

  // Convenience HTTP methods
  public get<T>(endpoint: string, options?: RequestInit): Promise<T> {
    return this.request<T>(endpoint, { ...options, method: 'GET' });
  }

  public post<T>(endpoint: string, body?: any, options?: RequestInit): Promise<T> {
    const isForm = body instanceof FormData;
    return this.request<T>(endpoint, {
      ...options,
      method: 'POST',
      body: isForm ? body : JSON.stringify(body)
    });
  }

  public put<T>(endpoint: string, body?: any, options?: RequestInit): Promise<T> {
    const isForm = body instanceof FormData;
    return this.request<T>(endpoint, {
      ...options,
      method: 'PUT',
      body: isForm ? body : JSON.stringify(body)
    });
  }

  public delete<T>(endpoint: string, options?: RequestInit): Promise<T> {
    return this.request<T>(endpoint, { ...options, method: 'DELETE' });
  }
}

export const apiClient = new CentralizedApiClient();
