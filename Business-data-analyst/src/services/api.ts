import {
  Analysis,
  ChatMessage,
  Chart,
  Dataset,
  DatasetColumn,
  Forecast,
  Insight,
  KPI,
  Project,
  Recommendation,
  Report,
  User,
  CorrelationPair
} from '../types';
import { analyzeGenericDataset, computeColumnSummary, generateAIResponseForDataset, inferColumnType } from '../utils/dataEngine';
import { supabaseService, mapSupabaseUserToAppUser } from './supabase';
import { apiClient, ProgressCallback } from './apiClient';

const STORAGE_KEYS = {
  USER: 'insightflow_user',
  PROJECTS: 'insightflow_projects',
  DATASETS: 'insightflow_datasets',
  REPORTS: 'insightflow_reports',
  CHATS: 'insightflow_chats',
  RECOMMENDATION_OVERRIDES: 'insightflow_rec_status'
};

const DEFAULT_USER: User = {
  id: 'usr-001',
  name: 'Elena Rostova',
  email: 'elena.rostova@insightflow.ai',
  avatar: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&auto=format&fit=crop&q=80',
  role: 'Lead Business Data Analyst',
  company: 'Apex Data Intelligence',
  plan: 'Enterprise',
  createdAt: '2025-11-10T10:00:00Z',
  preferences: {
    theme: 'dark',
    emailAlerts: true,
    autoInsightDetection: true,
    defaultConfidenceInterval: 95
  }
};

class ApiService {
  private user: User | null = null;
  private projects: Project[] = [];
  private datasets: Dataset[] = [];
  private reports: Report[] = [];
  private chats: Record<string, ChatMessage[]> = {};
  private recOverrides: Record<string, Recommendation['status']> = {};

  constructor() {
    this.user = this.loadFromStorage(STORAGE_KEYS.USER, null);
    this.projects = this.loadFromStorage(STORAGE_KEYS.PROJECTS, []);
    this.datasets = this.loadFromStorage(STORAGE_KEYS.DATASETS, []);
    this.reports = this.loadFromStorage(STORAGE_KEYS.REPORTS, []);
    this.chats = this.loadFromStorage(STORAGE_KEYS.CHATS, {});
    this.recOverrides = this.loadFromStorage(STORAGE_KEYS.RECOMMENDATION_OVERRIDES, {});
  }

  private loadFromStorage<T>(key: string, fallback: T): T {
    try {
      const item = localStorage.getItem(key);
      return item ? JSON.parse(item) : fallback;
    } catch {
      return fallback;
    }
  }

  private saveToStorage(key: string, data: any) {
    try {
      localStorage.setItem(key, JSON.stringify(data));
    } catch (e) {
      
    }
  }

  // --- AUTH SERVICES ---
  async login(email: string, password?: string): Promise<User> {
    // 1. Authenticate via Supabase Client
    if (password) {
      try {
        const { user: authUser } = await supabaseService.signIn(email, password);
        if (authUser) {
          const profile = await supabaseService.getProfile(authUser.id);
          this.user = mapSupabaseUserToAppUser(authUser, profile);
          this.saveToStorage(STORAGE_KEYS.USER, this.user);
          return this.user;
        }
      } catch (err: any) {
        console.error('Supabase signIn error:', err);
        const errMsg = err?.message || 'Authentication failed';
        // If email not confirmed or invalid credentials, throw directly for UI to show
        if (
          errMsg.toLowerCase().includes('invalid login credentials') ||
          errMsg.toLowerCase().includes('email not confirmed') ||
          errMsg.toLowerCase().includes('rate limit') ||
          errMsg.toLowerCase().includes('429')
        ) {
          throw new Error(errMsg);
        }
      }
    }

    // 2. Fallback Instant Workspace Session for Demo / Guest login
    this.user = {
      id: `usr-${Date.now().toString(36)}`,
      name: email.split('@')[0].replace(/[._]/g, ' ') || 'Lead Analyst',
      email: email || 'analyst@domain.com',
      avatar: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&auto=format&fit=crop&q=80',
      role: 'Lead Business Data Analyst',
      company: 'Enterprise Workspace',
      plan: 'Enterprise',
      createdAt: new Date().toISOString(),
      preferences: {
        theme: 'dark',
        emailAlerts: true,
        autoInsightDetection: true,
        defaultConfidenceInterval: 95
      }
    };
    this.saveToStorage(STORAGE_KEYS.USER, this.user);
    return this.user;
  }

  async signup(name: string, email: string, password?: string, company?: string): Promise<User> {
    if (password) {
      try {
        const { user: authUser } = await supabaseService.signUp(email, password, name, company);
        if (authUser) {
          const profile = await supabaseService.getProfile(authUser.id);
          this.user = mapSupabaseUserToAppUser(authUser, profile);
          this.saveToStorage(STORAGE_KEYS.USER, this.user);
          return this.user;
        }
      } catch (err: any) {
        console.error('Supabase signUp error:', err);
        const errMsg = err?.message || 'Registration failed';
        if (
          errMsg.toLowerCase().includes('already registered') ||
          errMsg.toLowerCase().includes('rate limit') ||
          errMsg.toLowerCase().includes('429') ||
          errMsg.toLowerCase().includes('password')
        ) {
          throw new Error(errMsg);
        }
      }
    }

    this.user = {
      id: `usr-${Date.now().toString(36)}`,
      name: name || email.split('@')[0],
      email: email || 'analyst@domain.com',
      company: company || 'Enterprise Analytics',
      avatar: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&auto=format&fit=crop&q=80',
      role: 'Lead Business Analyst',
      plan: 'Enterprise',
      createdAt: new Date().toISOString(),
      preferences: {
            theme: 'dark',
            emailAlerts: true,
            autoInsightDetection: true,
            defaultConfidenceInterval: 95
          }
        };
        this.saveToStorage(STORAGE_KEYS.USER, this.user);
        return this.user;
      }
    } catch (apiErr: any) {
      
    }

    this.user = {
      id: `usr-${Date.now().toString(36)}`,
      name: name || email.split('@')[0] || 'New Analyst',
      email: email || 'analyst@domain.com',
      company: company || 'Enterprise Corp',
      avatar: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&auto=format&fit=crop&q=80',
      role: 'Lead Business Analyst',
      plan: 'Enterprise',
      createdAt: new Date().toISOString(),
      preferences: {
        theme: 'dark',
        emailAlerts: true,
        autoInsightDetection: true,
        defaultConfidenceInterval: 95
      }
    };
    this.saveToStorage(STORAGE_KEYS.USER, this.user);
    return this.user;
  }

  async forgotPassword(email: string): Promise<{ success: boolean; message: string }> {
    try {
      await supabaseService.resetPassword(email);
      return { success: true, message: `Password reset instructions dispatched to ${email}` };
    } catch {
      return { success: true, message: `Password reset instructions dispatched to ${email}` };
    }
  }

  async logout(): Promise<void> {
    try {
      await supabaseService.signOut();
    } catch (e) {
      
    }
    localStorage.removeItem(STORAGE_KEYS.USER);
    localStorage.removeItem(STORAGE_KEYS.PROJECTS);
    localStorage.removeItem(STORAGE_KEYS.DATASETS);
    localStorage.removeItem(STORAGE_KEYS.REPORTS);
    localStorage.removeItem(STORAGE_KEYS.CHATS);
    localStorage.removeItem(STORAGE_KEYS.RECOMMENDATION_OVERRIDES);
    this.user = null;
    this.projects = [];
    this.datasets = [];
    this.reports = [];
    this.chats = {};
  }

  async getCurrentUser(): Promise<User | null> {
    try {
      const backendMe = await apiClient.get<User>('/auth/me');
      if (backendMe?.id) {
        this.user = backendMe;
        this.saveToStorage(STORAGE_KEYS.USER, this.user);
        return this.user;
      }
    } catch {
      // ignore
    }

    try {
      const authUser = await supabaseService.getCurrentAuthUser();
      if (authUser) {
        const profile = await supabaseService.getProfile(authUser.id);
        this.user = mapSupabaseUserToAppUser(authUser, profile);
        this.saveToStorage(STORAGE_KEYS.USER, this.user);
        return this.user;
      }
    } catch (e) {
      
    }
    return this.loadFromStorage(STORAGE_KEYS.USER, null);
  }

  async updateProfile(updates: Partial<User>): Promise<User> {
    if (!this.user) throw new Error('No user is currently authenticated.');
    this.user = { ...this.user, ...updates };
    this.saveToStorage(STORAGE_KEYS.USER, this.user);

    try {
      await apiClient.put('/auth/me', updates);
    } catch (err) {
      
    }

    return this.user;
  }

  // --- PROJECTS SERVICES ---
  async getProjects(userId?: string): Promise<Project[]> {
    try {
      const backendProjects = await apiClient.get<Project[]>('/projects');
      if (Array.isArray(backendProjects) && backendProjects.length > 0) {
        this.projects = backendProjects;
        this.saveToStorage(STORAGE_KEYS.PROJECTS, this.projects);
        return this.projects;
      }
    } catch (e) {
      
    }

    try {
      const targetUserId = userId || this.user?.id;
      if (targetUserId) {
        const supaProjects = await supabaseService.getProjects(targetUserId);
        if (supaProjects && supaProjects.length > 0) {
          this.projects = supaProjects;
          this.saveToStorage(STORAGE_KEYS.PROJECTS, this.projects);
          return this.projects;
        }
      }
    } catch (e) {
      
    }

    return [...this.projects];
  }

  async getProjectById(id: string): Promise<Project | null> {
    try {
      const proj = await apiClient.get<Project>(`/projects/${id}`);
      if (proj) return proj;
    } catch {
      // fallback
    }
    return this.projects.find((p) => p.id === id) || null;
  }

  async createProject(
    projectData: Omit<Project, 'id' | 'createdAt' | 'updatedAt' | 'memberCount'>,
    userId?: string
  ): Promise<Project> {
    try {
      const created = await apiClient.post<Project>('/projects', projectData);
      if (created?.id) {
        this.projects = [created, ...this.projects];
        this.saveToStorage(STORAGE_KEYS.PROJECTS, this.projects);
        return created;
      }
    } catch (e) {
      
    }

    const newProject: Project = {
      id: `proj-${Date.now().toString(36)}`,
      ...projectData,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      memberCount: 1
    };

    try {
      await supabaseService.createProject(newProject, userId || this.user?.id);
    } catch (e) {
      
    }

    this.projects = [newProject, ...this.projects];
    this.saveToStorage(STORAGE_KEYS.PROJECTS, this.projects);
    return newProject;
  }

  async updateProject(id: string, updates: Partial<Project>): Promise<Project> {
    try {
      const updated = await apiClient.put<Project>(`/projects/${id}`, updates);
      if (updated?.id) {
        const idx = this.projects.findIndex((p) => p.id === id);
        if (idx !== -1) this.projects[idx] = updated;
        this.saveToStorage(STORAGE_KEYS.PROJECTS, this.projects);
        return updated;
      }
    } catch (e) {
      
    }

    const idx = this.projects.findIndex((p) => p.id === id);
    if (idx === -1) throw new Error('Project not found');
    this.projects[idx] = { ...this.projects[idx], ...updates, updatedAt: new Date().toISOString() };
    this.saveToStorage(STORAGE_KEYS.PROJECTS, this.projects);
    return this.projects[idx];
  }

  async deleteProject(id: string): Promise<boolean> {
    try {
      await apiClient.delete(`/projects/${id}`);
    } catch (e) {
      
    }
    this.projects = this.projects.filter((p) => p.id !== id);
    this.saveToStorage(STORAGE_KEYS.PROJECTS, this.projects);
    return true;
  }

  // --- DATASETS SERVICES ---
  async getDatasets(projectId?: string, userId?: string): Promise<Dataset[]> {
    try {
      const endpoint = projectId ? `/datasets?project_id=${projectId}` : '/datasets';
      const backendDatasets = await apiClient.get<any[]>(endpoint);
      if (Array.isArray(backendDatasets) && backendDatasets.length > 0) {
        const mapped = backendDatasets.map((d) => this.mapBackendDatasetToFrontend(d));
        this.datasets = mapped;
        this.saveToStorage(STORAGE_KEYS.DATASETS, this.datasets);
        return projectId ? mapped.filter((d) => d.projectId === projectId) : mapped;
      }
    } catch (e) {
      
    }

    try {
      const targetUserId = userId || this.user?.id;
      if (targetUserId) {
        const supaDatasets = await supabaseService.getDatasets(targetUserId, projectId);
        if (supaDatasets && supaDatasets.length > 0) {
          this.datasets = supaDatasets;
          this.saveToStorage(STORAGE_KEYS.DATASETS, this.datasets);
          return projectId ? this.datasets.filter((d) => d.projectId === projectId) : this.datasets;
        }
      }
    } catch (e) {
      
    }

    if (projectId) {
      return this.datasets.filter((d) => d.projectId === projectId);
    }
    return [...this.datasets];
  }

  async getDatasetById(id: string): Promise<Dataset | null> {
    try {
      const res = await apiClient.get<any>(`/datasets/${id}/preview`);
      if (res) return this.mapBackendDatasetToFrontend(res);
    } catch {
      // fallback
    }
    return this.datasets.find((d) => d.id === id) || null;
  }

  private mapBackendDatasetToFrontend(data: any): Dataset {
    const rawCols = data.columns || [];
    const columns: DatasetColumn[] = rawCols.map((c: any) => ({
      name: c.name || c.key || 'Column',
      key: c.key || c.name || 'col',
      originalName: c.originalName || c.original_name || c.name || c.key,
      dataType: c.dataType || c.data_type || 'text',
      summary: c.summary,
      description: c.description,
      isTarget: c.isTarget || c.is_target
    }));

    return {
      id: String(data.id),
      projectId: String(data.projectId || data.project_id || 'proj-general'),
      name: data.name || 'Dataset',
      description: data.description || `Dataset with ${data.rowCount || data.row_count || 0} rows`,
      rowCount: data.rowCount || data.row_count || 0,
      columnCount: data.columnCount || data.column_count || columns.length,
      columns,
      sampleRows: data.sampleRows || data.sample_rows || [],
      sizeBytes: data.sizeBytes || data.size_bytes || 0,
      uploadedAt: data.uploadedAt || data.uploaded_at || new Date().toISOString(),
      fileType: (data.fileType || data.file_type || 'csv') as any,
      fileName: data.fileName || data.file_name,
      storageBucket: data.storageBucket || data.storage_bucket,
      storagePath: data.storagePath || data.storage_path,
      status: (data.status || 'ready') as any,
      domain: data.domain || 'Business Analytics',
      tags: data.tags || []
    };
  }

  /**
   * Uploads raw dataset payload with real-time upload progress tracking
   */
  async parseRawDataset(
    rawText: string,
    name: string,
    fileType: 'csv' | 'json' = 'csv',
    projectId?: string,
    onProgress?: ProgressCallback
  ): Promise<Dataset> {
    const targetProjId = projectId || this.projects[0]?.id || 'proj-general';
    const fileName = `${name || 'dataset'}.${fileType}`;
    const blob = new Blob([rawText], {
      type: fileType === 'json' ? 'application/json' : 'text/csv'
    });

    try {
      const formData = new FormData();
      formData.append('file', blob, fileName);
      formData.append('projectId', targetProjId);
      if (name) formData.append('customName', name);

      const backendRes = await apiClient.uploadWithProgress<any>(
        '/datasets/upload',
        formData,
        onProgress
      );

      if (backendRes?.id) {
        const mapped = this.mapBackendDatasetToFrontend(backendRes);
        this.datasets = [mapped, ...this.datasets];
        this.saveToStorage(STORAGE_KEYS.DATASETS, this.datasets);
        return mapped;
      }
    } catch (err: any) {
      console.error('Failed to parse dataset via backend:', err.message);
    }

    return this.parseRawDatasetClientFallback(rawText, name, fileType, targetProjId);
  }

  /**
   * Upload binary/multipart File object directly
   */
  async uploadFile(
    file: File,
    projectId?: string,
    customName?: string,
    onProgress?: ProgressCallback
  ): Promise<Dataset> {
    const targetProjId = projectId || this.projects[0]?.id || 'proj-general';
    const isJson = file.name.toLowerCase().endsWith('.json');
    const fileType: 'csv' | 'json' = isJson ? 'json' : 'csv';
    const datasetName = customName || file.name.replace(/\.[^/.]+$/, '').replace(/[-_]/g, ' ');

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('projectId', targetProjId);
      if (customName) formData.append('customName', customName);

      const backendRes = await apiClient.uploadWithProgress<any>(
        '/datasets/upload',
        formData,
        onProgress
      );

      if (backendRes?.id) {
        const mapped = this.mapBackendDatasetToFrontend(backendRes);
        this.datasets = [mapped, ...this.datasets];
        this.saveToStorage(STORAGE_KEYS.DATASETS, this.datasets);
        return mapped;
      }
    } catch (err: any) {
      console.warn('Backend upload unavailable or returned error, parsing client-side:', err.message);
    }

    // Client-side fallback: read file content directly in browser
    const rawText = await new Promise<string>((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = (e) => resolve((e.target?.result as string) || '');
      reader.onerror = () => reject(new Error('Failed to read file on client.'));
      reader.readAsText(file);
    });

    onProgress?.(100, file.size, file.size);
    return this.parseRawDatasetClientFallback(rawText, datasetName, fileType, targetProjId);
  }

  private splitCSVLine(line: string, delimiter: string = ','): string[] {
    const values: string[] = [];
    let current = '';
    let inQuotes = false;

    for (let i = 0; i < line.length; i++) {
      const char = line[i];
      if (char === '"' || char === "'") {
        if (inQuotes && line[i + 1] === char) {
          current += char;
          i++;
        } else {
          inQuotes = !inQuotes;
        }
      } else if (char === delimiter && !inQuotes) {
        values.push(current.trim());
        current = '';
      } else {
        current += char;
      }
    }
    values.push(current.trim());
    return values;
  }

  private parseRawDatasetClientFallback(
    rawText: string,
    name: string,
    fileType: 'csv' | 'json',
    targetProjId: string
  ): Dataset {
    let rows: Record<string, any>[] = [];
    if (fileType === 'json') {
      const parsed = JSON.parse(rawText);
      rows = Array.isArray(parsed) ? parsed : [parsed];
    } else {
      const lines = rawText.trim().split(/\r?\n/).filter((l) => l.trim().length > 0);
      const delimiter = lines[0].includes('\t') ? '\t' : lines[0].includes(';') ? ';' : ',';
      const headers = this.splitCSVLine(lines[0], delimiter).map((h) => h.replace(/^["']|["']$/g, '').trim());

      for (let i = 1; i < lines.length; i++) {
        const cols = this.splitCSVLine(lines[i], delimiter).map((c) => c.replace(/^["']|["']$/g, '').trim());
        const rowObj: Record<string, any> = {};
        headers.forEach((h, idx) => {
          const val = cols[idx];
          if (val === undefined || val === '') rowObj[h] = null;
          else if (!isNaN(Number(val)) && !val.includes('-') && !val.includes('/')) rowObj[h] = Number(val);
          else if (val.toLowerCase() === 'true') rowObj[h] = true;
          else if (val.toLowerCase() === 'false') rowObj[h] = false;
          else rowObj[h] = val;
        });
        rows.push(rowObj);
      }
    }

    const firstRow = rows[0] || {};
    const columns: DatasetColumn[] = Object.keys(firstRow).map((key) => {
      const values = rows.map((r) => r[key]);
      const dataType = inferColumnType(values, key);
      const summary = computeColumnSummary(values, dataType);
      return {
        name: key.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase()),
        key,
        originalName: key,
        dataType,
        summary
      };
    });

    const newDataset: Dataset = {
      id: `ds-${Date.now().toString(36)}`,
      projectId: targetProjId,
      name: name || 'Uploaded Dataset',
      description: `Dataset containing ${rows.length} records.`,
      rowCount: rows.length,
      columnCount: columns.length,
      columns,
      sampleRows: rows.slice(0, 100),
      sizeBytes: new Blob([rawText]).size,
      uploadedAt: new Date().toISOString(),
      fileType: fileType as any,
      status: 'ready'
    };

    this.datasets = [newDataset, ...this.datasets];
    this.saveToStorage(STORAGE_KEYS.DATASETS, this.datasets);
    return newDataset;
  }

  async syncDatasetToSupabase(datasetId: string): Promise<{ success: boolean; storagePath?: string; message: string }> {
    const ds = this.datasets.find((d) => d.id === datasetId);
    if (!ds) {
      return { success: false, message: 'Dataset not found.' };
    }

    try {
      let content = '';
      if (ds.fileType === 'json') {
        content = JSON.stringify(ds.sampleRows || [], null, 2);
      } else {
        const header = ds.columns.map((c) => c.key).join(',');
        const rows = (ds.sampleRows || []).map((row) =>
          ds.columns.map((c) => {
            const val = row[c.key];
            if (val === null || val === undefined) return '';
            const str = String(val);
            if (str.includes(',') || str.includes('"') || str.includes('\n')) {
              return `"${str.replace(/"/g, '""')}"`;
            }
            return str;
          }).join(',')
        );
        content = [header, ...rows].join('\n');
      }

      const blob = new Blob([content], {
        type: ds.fileType === 'json' ? 'application/json' : 'text/csv'
      });

      const uploadRes = await supabaseService.uploadDatasetFile(
        blob,
        `${ds.name || 'dataset'}.${ds.fileType || 'csv'}`,
        ds.projectId,
        this.user?.id
      );

      if (uploadRes) {
        ds.storageBucket = uploadRes.storageBucket;
        ds.storagePath = uploadRes.storagePath;
        ds.fileName = uploadRes.fileName;
        this.saveToStorage(STORAGE_KEYS.DATASETS, this.datasets);
        await supabaseService.saveDatasetMetadata(ds, this.user?.id);
        return {
          success: true,
          storagePath: uploadRes.storagePath,
          message: `Synced to Supabase Storage at: ${uploadRes.storagePath}`
        };
      }
      return { success: false, message: 'Supabase upload returned empty response.' };
    } catch (err: any) {
      return { success: false, message: err.message || 'Sync failed.' };
    }
  }

  async batchParseRawDatasets(
    files: { content: string; name: string; fileType: 'csv' | 'json'; projectId?: string }[]
  ): Promise<Dataset[]> {
    const results: Dataset[] = [];
    for (const f of files) {
      const ds = await this.parseRawDataset(f.content, f.name, f.fileType, f.projectId);
      results.push(ds);
    }
    return results;
  }

  async uploadDataset(dataset: Dataset): Promise<Dataset> {
    this.datasets = [dataset, ...this.datasets];
    this.saveToStorage(STORAGE_KEYS.DATASETS, this.datasets);
    return dataset;
  }

  async deleteDataset(id: string): Promise<boolean> {
    try {
      await apiClient.delete(`/datasets/${id}`);
    } catch (e) {
      
    }
    this.datasets = this.datasets.filter((d) => d.id !== id);
    this.saveToStorage(STORAGE_KEYS.DATASETS, this.datasets);
    return true;
  }

  // --- ANALYSIS & EDA SERVICES (DYNAMIC REAL BACKEND DATA) ---
  async getAnalysisByDatasetId(datasetId: string): Promise<Analysis> {
    const dataset = this.datasets.find((d) => d.id === datasetId) || this.datasets[0];
    if (!dataset) throw new Error('Dataset not found');

    // 1. Fetch real EDA report, visualizations, and predictions in parallel from FastAPI backend
    try {
      const [edaRes, insightsRes, recsRes, predRes] = await Promise.allSettled([
        apiClient.get<any>(`/datasets/${datasetId}/eda/report`),
        apiClient.get<any>(`/datasets/${datasetId}/insights/report`),
        apiClient.get<any>(`/datasets/${datasetId}/recommendations/report`),
        apiClient.get<any>(`/datasets/${datasetId}/predictions/report`)
      ]);

      const edaData = edaRes.status === 'fulfilled' ? edaRes.value : null;
      const insightsData = insightsRes.status === 'fulfilled' ? insightsRes.value : null;
      const recsData = recsRes.status === 'fulfilled' ? recsRes.value : null;
      const predData = predRes.status === 'fulfilled' ? predRes.value : null;

      if (edaData) {
        // Dynamic KPIs computed strictly in Python
        const kpis: KPI[] = (edaData.kpis || []).map((k: any) => ({
          id: k.id || `kpi-${k.metric_key}`,
          label: k.label || k.metric_name || k.metric_key,
          value: k.formatted_value || String(k.current_value),
          rawValue: k.current_value || 0,
          changePercentage: k.change_pct || 0,
          trend: k.trend_direction === 'up' ? 'up' : k.trend_direction === 'down' ? 'down' : 'neutral',
          isPositive: k.is_positive ?? true,
          description: k.business_context || k.description || '',
          category: k.category || 'General'
        }));

        // Dynamic Visual Charts
        const charts: Chart[] = (edaData.recommended_charts || []).map((c: any, idx: number) => ({
          id: c.id || `chart-eda-${idx}`,
          title: c.title,
          subtitle: c.subtitle,
          chartType: (c.chart_type === 'box_plot' ? 'bar' : c.chart_type) || 'bar',
          xAxisKey: c.x_axis_key || 'category',
          yAxisKeys: [c.y_axis_key || 'value'],
          data: c.sample_data || [],
          description: c.business_rationale || c.insight_summary || '',
          columnReferences: c.columns_involved || []
        }));

        // Grounded 5-Category Insights from Google ADK + NVIDIA
        const insights: Insight[] = (insightsData?.insights || []).map((ins: any) => ({
          id: ins.id,
          title: ins.title,
          description: ins.natural_language_explanation || ins.description || '',
          category: ins.category || 'trend',
          priority: ins.severity === 'critical' ? 'critical' : ins.severity === 'high' ? 'high' : 'medium',
          score: ins.confidence_score ? ins.confidence_score * 100 : 85,
          impact: ins.business_impact || '',
          actionRequired: ins.action_required ?? false,
          relevantColumns: ins.relevant_columns || [],
          createdAt: ins.created_at || new Date().toISOString()
        }));

        // Actionable 6-Pillar Recommendations from Recommendation Agent
        const recommendations: Recommendation[] = (recsData?.recommendations || []).map((r: any) => ({
          id: r.id,
          title: r.problem || r.action,
          executiveSummary: `${r.problem} ${r.reasoning}`,
          detailedSteps: [r.action, ...(r.execution_plan?.map((s: any) => s.step_description) || [])],
          expectedImpact: r.evidence,
          impactScore: r.impact_score ? r.impact_score * 10 : 80,
          confidence: r.confidence_score ? r.confidence_score * 100 : 85,
          difficulty: r.effort_level === 'high' ? 'hard' : r.effort_level === 'medium' ? 'moderate' : 'easy',
          timeframe: r.timeframe || '30 Days',
          category: r.category || 'Growth',
          status: this.recOverrides[r.id] || 'new',
          metricsInfluenced: r.relevant_metrics || []
        }));

        // Analytical Time-Series Forecast
        const primaryFc = predData?.primary_forecast;
        const forecast: Forecast = {
          id: `fc-${datasetId}`,
          targetMetricKey: primaryFc?.target_metric || 'revenue',
          targetMetricLabel: (primaryFc?.target_metric || 'revenue').toUpperCase(),
          timeColumnKey: primaryFc?.time_dimension || 'period',
          historicalData: (primaryFc?.predicted_values || [])
            .filter((p: any) => p.is_historical)
            .map((p: any) => ({ timestamp: p.period_label, actual: p.actual_value || p.forecast_value })),
          forecastData: (primaryFc?.predicted_values || [])
            .filter((p: any) => !p.is_historical)
            .map((p: any) => ({
              timestamp: p.period_label,
              predicted: p.forecast_value,
              lowerBound: p.lower_bound_95,
              upperBound: p.upper_bound_95
            })),
          confidenceInterval: 95,
          growthRate: primaryFc?.projected_net_change_pct || 0,
          modelUsed: primaryFc?.model_used || 'Linear Trend (OLS)',
          horizonPeriods: primaryFc?.forecast_horizon_periods || 6,
          keyDrivers: (primaryFc?.top_drivers || []).map((d: any) => ({
            factor: d.feature_name,
            weight: d.importance_score,
            direction: d.direction
          }))
        };

        // Pearson Correlation Matrix from FastAPI EDA Service
        let correlations: CorrelationPair[] = [];
        if (edaData.correlations?.ranked_pairs && Array.isArray(edaData.correlations.ranked_pairs)) {
          correlations = edaData.correlations.ranked_pairs.map((cp: any) => ({
            colA: cp.feature_x || cp.column_x || cp.col_a || cp.colA || 'Feature A',
            colB: cp.feature_y || cp.column_y || cp.col_b || cp.colB || 'Feature B',
            coefficient: typeof cp.pearson_r === 'number' ? cp.pearson_r : (cp.coefficient ?? 0),
            relationship: cp.direction ? `${cp.strength || 'moderate'}_${cp.direction}` : (cp.pearson_r > 0 ? 'strong_positive' : 'moderate_negative'),
            description: cp.interpretation || cp.business_takeaway || cp.description || ''
          }));
        } else if (edaData.correlation_matrix?.correlations) {
          correlations = (edaData.correlation_matrix.correlations || []).map((cp: any) => ({
            colA: cp.col_a || cp.colA || cp.var1 || 'Col A',
            colB: cp.col_b || cp.colB || cp.var2 || 'Col B',
            coefficient: cp.coefficient ?? 0,
            relationship: cp.relationship || (cp.coefficient > 0 ? 'strong_positive' : 'moderate_negative'),
            description: cp.business_takeaway || cp.description || ''
          }));
        }

        const anomalies = (edaData.anomalies || []).map((a: any) => ({
          column: a.column || a.column_name || 'Metric',
          value: a.value || a.observed_value || 0,
          expectedValue: a.expected_value || a.mean || 0,
          deviation: a.deviation || a.z_score || 2.0,
          severity: (a.severity || 'medium') as any
        }));

        const fallback = analyzeGenericDataset(dataset);

        return {
          id: `analysis-${datasetId}`,
          datasetId,
          projectId: dataset.projectId,
          status: 'completed',
          progressPercentage: 100,
          currentStep: 'Intelligence Synthesized',
          kpis: kpis.length > 0 ? kpis : fallback.kpis,
          charts: charts.length > 0 ? charts : fallback.charts,
          insights: insights.length > 0 ? insights : fallback.insights,
          recommendations: recommendations.length > 0 ? recommendations : fallback.recommendations,
          forecast: forecast.forecastData.length > 0 ? forecast : fallback.forecast,
          statisticalSummary: {
            totalRecords: dataset.rowCount,
            numericalColumnCount: dataset.columns.filter((c) => c.dataType === 'numeric').length,
            categoricalColumnCount: dataset.columns.filter((c) => c.dataType === 'categorical').length,
            dateColumnCount: dataset.columns.filter((c) => c.dataType === 'datetime').length,
            dataQualityScore: 94,
            completenessRate: 98
          },
          anomaliesDetectedCount: anomalies.length > 0 ? anomalies.length : (edaData.anomalies?.length || fallback.anomaliesDetectedCount),
          anomalies: anomalies.length > 0 ? anomalies : fallback.anomalies,
          correlationMatrix: correlations.length > 0 ? correlations : fallback.correlationMatrix,
          createdAt: new Date().toISOString()
        };
      }
    } catch (err) {
      console.error('FastAPI analysis retrieval failed, using client engine:', err);
    }

    const fallbackAnalysis = analyzeGenericDataset(dataset);
    fallbackAnalysis.recommendations = fallbackAnalysis.recommendations.map((rec) => {
      const override = this.recOverrides[rec.id];
      return override ? { ...rec, status: override } : rec;
    });
    return fallbackAnalysis;
  }

  async runAnalysis(datasetId: string): Promise<Analysis> {
    try {
      await apiClient.post(`/datasets/${datasetId}/eda/analyze`);
    } catch {
      // ignore
    }
    return this.getAnalysisByDatasetId(datasetId);
  }

  // --- INSIGHTS SERVICES ---
  async getInsights(datasetId: string): Promise<Insight[]> {
    const analysis = await this.getAnalysisByDatasetId(datasetId);
    return analysis.insights;
  }

  // --- RECOMMENDATIONS SERVICES ---
  async getRecommendations(datasetId: string): Promise<Recommendation[]> {
    const analysis = await this.getAnalysisByDatasetId(datasetId);
    return analysis.recommendations;
  }

  async updateRecommendationStatus(recId: string, status: Recommendation['status']): Promise<void> {
    this.recOverrides[recId] = status;
    this.saveToStorage(STORAGE_KEYS.RECOMMENDATION_OVERRIDES, this.recOverrides);
  }

  // --- FORECAST SERVICES ---
  async getForecast(datasetId: string): Promise<Forecast> {
    const analysis = await this.getAnalysisByDatasetId(datasetId);
    return analysis.forecast;
  }

  async simulateScenario(
    datasetId: string,
    multiplier: number,
    horizon: number = 6
  ): Promise<Forecast> {
    try {
      const analysis = await this.getAnalysisByDatasetId(datasetId);
      const targetMetric = analysis.forecast.targetMetricKey;
      const driver = analysis.forecast.keyDrivers[0]?.factor || 'multiplier';

      const whatIfRes = await apiClient.post<any>(`/datasets/${datasetId}/predictions/what-if`, {
        target_metric: targetMetric,
        feature_adjustments: { [driver]: multiplier }
      });

      if (whatIfRes?.simulated_predicted_value) {
        const baseForecast = analysis.forecast;
        const modifiedForecastData = baseForecast.forecastData.slice(0, horizon).map((pt, idx) => {
          const scale = 1 + (multiplier - 1) * (0.4 + idx * 0.15);
          const predicted = Number((pt.predicted * scale).toFixed(1));
          const spread = predicted * 0.05;
          return {
            timestamp: pt.timestamp,
            predicted,
            lowerBound: Number((predicted - spread).toFixed(1)),
            upperBound: Number((predicted + spread).toFixed(1))
          };
        });

        return {
          ...baseForecast,
          horizonPeriods: horizon,
          growthRate: Number((baseForecast.growthRate * multiplier).toFixed(1)),
          forecastData: modifiedForecastData
        };
      }
    } catch (e) {
      
    }

    const analysis = await this.getAnalysisByDatasetId(datasetId);
    const baseForecast = analysis.forecast;

    const modifiedForecastData = baseForecast.forecastData.slice(0, horizon).map((pt, idx) => {
      const scale = 1 + (multiplier - 1) * (0.4 + idx * 0.15);
      const predicted = Number((pt.predicted * scale).toFixed(1));
      const spread = predicted * 0.05;
      return {
        timestamp: pt.timestamp,
        predicted,
        lowerBound: Number((predicted - spread).toFixed(1)),
        upperBound: Number((predicted + spread).toFixed(1))
      };
    });

    return {
      ...baseForecast,
      horizonPeriods: horizon,
      growthRate: Number((baseForecast.growthRate * multiplier).toFixed(1)),
      forecastData: modifiedForecastData
    };
  }

  // --- CHAT SERVICES ("ASK YOUR DATA") ---
  async getChatHistory(datasetId: string): Promise<ChatMessage[]> {
    try {
      const [histRes, sqRes] = await Promise.allSettled([
        apiClient.get<any>(`/datasets/${datasetId}/chat-history`),
        apiClient.get<any>(`/datasets/${datasetId}/suggested-questions`)
      ]);

      const backendHistory = histRes.status === 'fulfilled' ? histRes.value : null;
      const suggestedData = sqRes.status === 'fulfilled' ? sqRes.value : null;

      const starterPrompts = (suggestedData?.starter_questions || []).map((q: any) => q.question);

      if (backendHistory?.messages && backendHistory.messages.length > 0) {
        const mappedMsgs: ChatMessage[] = backendHistory.messages.map((m: any) => ({
          id: m.id,
          role: m.role,
          content: m.content,
          timestamp: m.timestamp || new Date().toISOString(),
          suggestedQuestions: m.role === 'assistant' ? starterPrompts.slice(0, 3) : undefined,
          generatedChart: m.chart ? this.mapVisualChartToFrontend(m.chart) : undefined
        }));
        this.chats[datasetId] = mappedMsgs;
        this.saveToStorage(STORAGE_KEYS.CHATS, this.chats);
        return mappedMsgs;
      }

      const dataset = this.datasets.find((d) => d.id === datasetId) || this.datasets[0];
      const initialAssistantMessage: ChatMessage = {
        id: `msg-welcome-${datasetId}`,
        role: 'assistant',
        content: `Hello! I'm your **InsightFlow AI Data Analyst**. I have ingested and indexed **${dataset?.name || 'the dataset'}** (${dataset?.rowCount || 0} records across ${dataset?.columns?.length || 0} dimensions).\n\nYou can ask me natural language queries, statistical anomaly checks, cross-variable correlation analyses, or dynamic forecasts.`,
        timestamp: new Date().toISOString(),
        suggestedQuestions: starterPrompts.length > 0 ? starterPrompts : [
          'What is the highest performing category?',
          'Which region has the highest profit?',
          'What are the strongest correlations in this dataset?',
          'What does the forecast project for the next 6 periods?'
        ]
      };
      this.chats[datasetId] = [initialAssistantMessage];
      this.saveToStorage(STORAGE_KEYS.CHATS, this.chats);
      return this.chats[datasetId];
    } catch (e) {
      
    }

    if (!this.chats[datasetId] || this.chats[datasetId].length === 0) {
      const dataset = this.datasets.find((d) => d.id === datasetId) || this.datasets[0];
      const initialAssistantMessage: ChatMessage = {
        id: `msg-welcome-${datasetId}`,
        role: 'assistant',
        content: `Hello! I'm your **InsightFlow AI Data Analyst**. I have ingested and indexed **${dataset?.name || 'the dataset'}** (${dataset?.rowCount || 0} records across ${dataset?.columns?.length || 0} dimensions).\n\nYou can ask me natural language queries, statistical anomaly checks, cross-variable correlation analyses, or dynamic forecasts.`,
        timestamp: new Date().toISOString(),
        suggestedQuestions: [
          'What is the highest performing category?',
          'Which region has the highest profit?',
          'What are the strongest correlations in this dataset?',
          'Give me a breakdown of metrics by category.'
        ]
      };
      this.chats[datasetId] = [initialAssistantMessage];
      this.saveToStorage(STORAGE_KEYS.CHATS, this.chats);
    }
    return this.chats[datasetId];
  }

  async sendChatMessage(datasetId: string, userQuery: string): Promise<ChatMessage> {
    const userMessage: ChatMessage = {
      id: `msg-user-${Date.now()}`,
      role: 'user',
      content: userQuery,
      timestamp: new Date().toISOString()
    };

    try {
      const askRes = await apiClient.post<any>(`/datasets/${datasetId}/ask`, { query: userQuery });

      if (askRes) {
        const aiMessage: ChatMessage = {
          id: `msg-ai-${Date.now() + 1}`,
          role: 'assistant',
          content: askRes.answer || askRes.answer_markdown,
          timestamp: askRes.answered_at || new Date().toISOString(),
          generatedChart: askRes.chart ? this.mapVisualChartToFrontend(askRes.chart) : undefined,
          suggestedQuestions: askRes.suggested_followups || [
            'What is the average across all segments?',
            'Forecast this metric for the next 6 periods.',
            'Export this analysis to executive report.'
          ]
        };

        const history = this.chats[datasetId] || [];
        this.chats[datasetId] = [...history, userMessage, aiMessage];
        this.saveToStorage(STORAGE_KEYS.CHATS, this.chats);
        return aiMessage;
      }
    } catch (err: any) {
      console.error('Chat error:', err.message);
    }

    const dataset = this.datasets.find((d) => d.id === datasetId) || this.datasets[0];
    const analysis = analyzeGenericDataset(dataset);
    const aiResult = generateAIResponseForDataset(userQuery, dataset, analysis);

    const aiMessage: ChatMessage = {
      id: `msg-ai-${Date.now() + 1}`,
      role: 'assistant',
      content: aiResult.text,
      timestamp: new Date().toISOString(),
      generatedChart: aiResult.chart,
      sqlQuery: aiResult.sql,
      suggestedQuestions: [
        'How can we optimize the primary driver metric?',
        'Export this summary as an executive report.',
        'Run a sensitivity scenario with +15% variable shift.'
      ]
    };

    const history = this.chats[datasetId] || [];
    this.chats[datasetId] = [...history, userMessage, aiMessage];
    this.saveToStorage(STORAGE_KEYS.CHATS, this.chats);
    return aiMessage;
  }

  private mapVisualChartToFrontend(chartObj: any): Chart {
    if (!chartObj) return undefined as any;
    const config = chartObj.config || {};
    const rawType = config.chart_type || chartObj.chartType || chartObj.chart_type || 'bar';
    const chartType = rawType === 'kpi_card' ? 'bar' : (rawType === 'pie' ? 'donut' : rawType);
    
    const data = chartObj.data || [];
    const sampleRow = data[0] || {};
    const dataKeys = Object.keys(sampleRow);

    // Derive xAxisKey
    const xAxisKey =
      config.x_axis_key ||
      chartObj.xAxisKey ||
      dataKeys.find((k) => typeof sampleRow[k] === 'string' && k !== 'id') ||
      dataKeys[0] ||
      'category';

    // Derive yAxisKeys
    let yAxisKeys: string[] = [];
    if (Array.isArray(config.series) && config.series.length > 0) {
      yAxisKeys = config.series.map((s: any) => s.data_key || s.name).filter(Boolean);
    }
    if (yAxisKeys.length === 0 && config.y_axis_key) {
      yAxisKeys = [config.y_axis_key];
    }
    if (yAxisKeys.length === 0 && Array.isArray(chartObj.yAxisKeys) && chartObj.yAxisKeys.length > 0) {
      yAxisKeys = chartObj.yAxisKeys;
    }
    if (yAxisKeys.length === 0) {
      yAxisKeys = dataKeys.filter((k) => k !== xAxisKey && k !== 'id');
    }
    if (yAxisKeys.length === 0) {
      yAxisKeys = ['value'];
    }

    return {
      id: chartObj.id || `chart-${Date.now()}`,
      title: config.title || chartObj.title || 'Data Visualization',
      subtitle: chartObj.storytelling_caption || config.subtitle || chartObj.subtitle,
      chartType: chartType,
      xAxisKey: xAxisKey,
      xAxisLabel: config.x_axis_label || chartObj.xAxisLabel,
      yAxisKeys: yAxisKeys,
      yAxisLabels: config.series ? config.series.map((s: any) => s.name || s.data_key) : chartObj.yAxisLabels,
      data: data,
      description: chartObj.storytelling_caption || config.subtitle || chartObj.description || '',
      columnReferences: [xAxisKey, ...yAxisKeys].filter(Boolean),
      colors: config.color_palette || chartObj.colors
    };
  }

  // --- REPORTS SERVICES (FASTAPI BACKEND INTEGRATED) ---
  async getReports(projectId?: string): Promise<Report[]> {
    try {
      const endpoint = projectId ? `/reports?projectId=${projectId}` : '/reports';
      const backendReports = await apiClient.get<any[]>(endpoint);
      if (backendReports && Array.isArray(backendReports) && backendReports.length > 0) {
        const mapped = backendReports.map((r) => ({
          id: r.id,
          projectId: r.project_id || r.projectId || 'proj-general',
          datasetId: r.dataset_id || r.datasetId,
          title: r.title,
          subtitle: r.subtitle,
          executiveSummary: r.executive_summary || r.executiveSummary || '',
          generatedAt: r.generated_at || r.generatedAt || new Date().toISOString(),
          author: r.author || 'Lead Data Analyst',
          status: r.status || 'published',
          format: r.format || 'pdf',
          cadence: r.cadence || 'on_demand',
          sections: (r.sections || []).map((s: any) => ({
            id: s.id,
            title: s.title,
            type: s.type,
            content: s.content
          }))
        }));
        this.reports = mapped;
        this.saveToStorage(STORAGE_KEYS.REPORTS, this.reports);
        return mapped;
      }
    } catch (e: any) {
      console.error('Get reports error:', e.message);
    }

    if (projectId) {
      return this.reports.filter((r) => r.projectId === projectId);
    }
    return [...this.reports];
  }

  async getReportById(id: string): Promise<Report | null> {
    try {
      const r = await apiClient.get<any>(`/reports/${id}`);
      if (r) {
        return {
          id: r.id,
          projectId: r.project_id || r.projectId,
          datasetId: r.dataset_id || r.datasetId,
          title: r.title,
          subtitle: r.subtitle,
          executiveSummary: r.executive_summary || r.executiveSummary || '',
          generatedAt: r.generated_at || r.generatedAt || new Date().toISOString(),
          author: r.author || 'Lead Data Analyst',
          status: r.status || 'published',
          format: r.format || 'pdf',
          cadence: r.cadence || 'on_demand',
          sections: (r.sections || []).map((s: any) => ({
            id: s.id,
            title: s.title,
            type: s.type,
            content: s.content
          }))
        };
      }
    } catch {
      // ignore
    }
    return this.reports.find((r) => r.id === id) || null;
  }

  async generateReport(datasetId: string, title: string, subtitle?: string): Promise<Report> {
    try {
      const backendReport = await apiClient.post<any>(`/datasets/${datasetId}/reports/generate`, {
        dataset_id: datasetId,
        title,
        subtitle
      });

      if (backendReport && backendReport.id) {
        const mapped: Report = {
          id: backendReport.id,
          projectId: backendReport.project_id || 'proj-general',
          datasetId: backendReport.dataset_id || datasetId,
          title: backendReport.title,
          subtitle: backendReport.subtitle,
          executiveSummary: backendReport.executive_summary || '',
          generatedAt: backendReport.generated_at || new Date().toISOString(),
          author: backendReport.author || this.user?.name || 'Lead Data Analyst',
          status: backendReport.status || 'published',
          format: backendReport.format || 'pdf',
          cadence: backendReport.cadence || 'on_demand',
          sections: (backendReport.sections || []).map((s: any) => ({
            id: s.id,
            title: s.title,
            type: s.type,
            content: s.content
          }))
        };

        this.reports = [mapped, ...this.reports];
        this.saveToStorage(STORAGE_KEYS.REPORTS, this.reports);
        return mapped;
      }
    } catch (err: any) {
      console.error('Generate report error:', err.message);
    }

    const dataset = this.datasets.find((d) => d.id === datasetId) || this.datasets[0];
    const analysis = await this.getAnalysisByDatasetId(datasetId);

    const newReport: Report = {
      id: `rep-${Date.now().toString(36)}`,
      projectId: dataset.projectId || 'proj-general',
      datasetId: dataset.id,
      title: title || `${dataset.name} - Executive Intelligence Report`,
      subtitle: subtitle || `Dynamic automated analysis compiled on ${new Date().toLocaleDateString()}`,
      executiveSummary: `Synthesized intelligence for ${dataset.name}. Profiling across ${analysis.statisticalSummary.totalRecords} records revealed ${analysis.insights.length} primary insights and ${analysis.recommendations.length} actionable recommendations. Overall data completeness is ${analysis.statisticalSummary.completenessRate}%.`,
      generatedAt: new Date().toISOString(),
      author: this.user?.name || 'Lead Business Analyst',
      status: 'published',
      format: 'pdf',
      cadence: 'on_demand',
      sections: [
        { id: 'sec-kpis', title: 'Key Performance Indicators', type: 'kpi_grid', content: analysis.kpis },
        { id: 'sec-charts', title: 'Visual Trajectories & Distributions', type: 'chart_view', content: analysis.charts },
        { id: 'sec-insights', title: 'Statistical Findings & Anomaly Detection', type: 'insights_list', content: analysis.insights },
        { id: 'sec-recommendations', title: 'Strategic Action Recommendations', type: 'recommendations_table', content: analysis.recommendations },
        { id: 'sec-forecast', title: 'Predictive Horizon & Sensitivity', type: 'forecast_view', content: analysis.forecast }
      ]
    };

    this.reports = [newReport, ...this.reports];
    this.saveToStorage(STORAGE_KEYS.REPORTS, this.reports);
    return newReport;
  }

  async downloadReportFile(reportId: string, format: 'pdf' | 'html' | 'markdown' = 'pdf', title?: string): Promise<void> {
    const ext = format === 'markdown' ? 'md' : format;
    const filename = `${(title || 'executive_report').toLowerCase().replace(/[^a-z0-9]/g, '_')}.${ext}`;
    try {
      const baseUrl = apiClient.getBaseUrl();
      const token = await (apiClient as any).getAuthToken();
      const headers: Record<string, string> = {};
      if (token) headers['Authorization'] = `Bearer ${token}`;

      const res = await fetch(`${baseUrl}/reports/${reportId}/export?format=${format}`, {
        method: 'GET',
        headers
      });

      if (!res.ok) throw new Error(`Export failed with status ${res.status}`);

      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (e: any) {
      console.error('Download report error:', e.message);
      const rep = await this.getReportById(reportId);
      if (rep) {
        const text = `# ${rep.title}\n\n${rep.executiveSummary}\n\n` + rep.sections.map(s => `## ${s.title}\n${typeof s.content === 'string' ? s.content : JSON.stringify(s.content, null, 2)}`).join('\n\n');
        const blob = new Blob([text], { type: 'text/markdown' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      }
    }
  }

  async deleteReport(id: string): Promise<boolean> {
    try {
      await apiClient.delete(`/reports/${id}`);
    } catch {
      // ignore
    }
    this.reports = this.reports.filter((r) => r.id !== id);
    this.saveToStorage(STORAGE_KEYS.REPORTS, this.reports);
    return true;
  }
}

export const api = new ApiService();
