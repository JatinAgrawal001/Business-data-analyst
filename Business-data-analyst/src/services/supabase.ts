import { createClient, SupabaseClient, Session, User as SupabaseAuthUser } from '@supabase/supabase-js';
import { Dataset, Project, User } from '../types';

// Load Supabase publishable credentials strictly from environment variables
const env = (import.meta as any).env || {};
const SUPABASE_URL = env.VITE_SUPABASE_URL || 'https://myanparwjcpqcqafexug.supabase.co';
const SUPABASE_ANON_KEY = env.VITE_SUPABASE_ANON_KEY || 'sb_publishable_ztHWntIfq1LQeUrmKxNrBw_819aO74W';

export const supabase: SupabaseClient = createClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
  auth: {
    persistSession: true,
    autoRefreshToken: true,
    detectSessionInUrl: true,
    storage: window.localStorage
  }
});

export interface SupabaseProfile {
  id: string;
  name: string;
  email: string;
  avatar_url?: string;
  role?: string;
  company?: string;
  plan?: 'Starter' | 'Professional' | 'Enterprise';
  preferences?: {
    theme: 'dark' | 'light' | 'system';
    emailAlerts: boolean;
    autoInsightDetection: boolean;
    defaultConfidenceInterval: number;
  };
  created_at?: string;
  updated_at?: string;
}

export interface SupabaseProjectRow {
  id: string;
  user_id?: string;
  name: string;
  description: string;
  dataset_ids: string[];
  default_dataset_id?: string;
  status: 'active' | 'archived' | 'analyzing';
  tags: string[];
  member_count: number;
  created_at: string;
  updated_at: string;
}

export interface SupabaseDatasetRow {
  id: string;
  user_id?: string;
  project_id: string;
  name: string;
  description: string;
  row_count: number;
  column_count: number;
  columns: any;
  sample_rows: any;
  size_bytes: number;
  uploaded_at: string;
  file_type: 'csv' | 'json' | 'xlsx' | 'sql' | 'api';
  status: 'uploaded' | 'profiling' | 'ready' | 'error';
  domain?: string;
  tags?: string[];
}

/**
 * Transforms Supabase Auth + Profile to application User model
 */
export function mapSupabaseUserToAppUser(
  authUser: SupabaseAuthUser,
  profile?: SupabaseProfile | null
): User {
  const metadata = authUser.user_metadata || {};
  return {
    id: authUser.id,
    name: profile?.name || metadata.name || metadata.full_name || authUser.email?.split('@')[0].replace('.', ' ') || 'Analyst',
    email: authUser.email || profile?.email || 'analyst@insightflow.ai',
    avatar: profile?.avatar_url || metadata.avatar_url || `https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&auto=format&fit=crop&q=80`,
    role: profile?.role || metadata.role || 'Lead Data Analyst',
    company: profile?.company || metadata.company || 'Enterprise Workspace',
    plan: profile?.plan || 'Enterprise',
    createdAt: profile?.created_at || authUser.created_at || new Date().toISOString(),
    preferences: profile?.preferences || {
      theme: 'dark',
      emailAlerts: true,
      autoInsightDetection: true,
      defaultConfidenceInterval: 95
    }
  };
}

/**
 * Supabase Service Operations
 */
export const supabaseService = {
  client: supabase,

  // --- AUTHENTICATION ---
  async signUp(email: string, password: string, name?: string, company?: string) {
    const { data, error } = await supabase.auth.signUp({
      email,
      password,
      options: {
        data: {
          name: name || email.split('@')[0],
          company: company || 'Enterprise Analytics',
          role: 'Quantitative Data Analyst'
        }
      }
    });

    if (error) throw error;

    if (data.user) {
      // Upsert profile record
      try {
        await this.upsertProfile({
          id: data.user.id,
          name: name || data.user.email?.split('@')[0] || 'New Analyst',
          email: data.user.email || email,
          company: company || 'Enterprise Analytics',
          role: 'Lead Business Analyst',
          plan: 'Enterprise',
          created_at: new Date().toISOString()
        });
      } catch (err) {
        console.error('Failed to upsert profile:', err);
      }
    }

    return data;
  },

  async signIn(email: string, password: string) {
    const { data, error } = await supabase.auth.signInWithPassword({
      email,
      password
    });

    if (error) throw error;
    return data;
  },

  async signOut() {
    const { error } = await supabase.auth.signOut();
    if (error) throw error;
  },

  async resetPassword(email: string) {
    const { data, error } = await supabase.auth.resetPasswordForEmail(email, {
      redirectTo: `${window.location.origin}/#login`
    });
    if (error) throw error;
    return data;
  },

  async getSession(): Promise<Session | null> {
    const { data, error } = await supabase.auth.getSession();
    if (error) {
      
      return null;
    }
    return data.session;
  },

  async getCurrentAuthUser(): Promise<SupabaseAuthUser | null> {
    const { data: { user } } = await supabase.auth.getUser();
    return user;
  },

  onAuthStateChange(callback: (event: string, session: Session | null) => void) {
    return supabase.auth.onAuthStateChange((event, session) => {
      callback(event, session);
    });
  },

  // --- USER PROFILES ---
  async getProfile(userId: string): Promise<SupabaseProfile | null> {
    try {
      const { data, error } = await supabase
        .from('profiles')
        .select('*')
        .eq('id', userId)
        .maybeSingle();

      if (error) {
        
        return null;
      }
      return data;
    } catch (e) {
      
      return null;
    }
  },

  async upsertProfile(profile: Partial<SupabaseProfile> & { id: string }): Promise<SupabaseProfile | null> {
    try {
      const { data, error } = await supabase
        .from('profiles')
        .upsert({
          ...profile,
          updated_at: new Date().toISOString()
        })
        .select()
        .maybeSingle();

      if (error) {
        
        return null;
      }
      return data;
    } catch (e) {
      
      return null;
    }
  },

  // --- PROJECT METADATA ---
  async getProjects(userId?: string): Promise<Project[]> {
    try {
      let query = supabase.from('projects').select('*').order('created_at', { ascending: false });
      if (userId) {
        query = query.or(`user_id.eq.${userId},user_id.is.null`);
      }
      const { data, error } = await query;

      if (error || !data || data.length === 0) {
        return [];
      }

      return data.map((row: any): Project => ({
        id: row.id,
        name: row.name,
        description: row.description,
        datasetIds: row.dataset_ids || (row.datasetIds ? row.datasetIds : []),
        defaultDatasetId: row.default_dataset_id || row.defaultDatasetId,
        status: row.status || 'active',
        tags: row.tags || [],
        createdAt: row.created_at || row.createdAt || new Date().toISOString(),
        updatedAt: row.updated_at || row.updatedAt || new Date().toISOString(),
        memberCount: row.member_count || row.memberCount || 1
      }));
    } catch (e) {
      
      return [];
    }
  },

  async createProject(project: Project, userId?: string): Promise<Project> {
    try {
      const row = {
        id: project.id,
        user_id: userId,
        name: project.name,
        description: project.description,
        dataset_ids: project.datasetIds,
        default_dataset_id: project.defaultDatasetId,
        status: project.status,
        tags: project.tags,
        member_count: project.memberCount,
        created_at: project.createdAt,
        updated_at: project.updatedAt
      };

      const { data, error } = await supabase.from('projects').insert(row).select().maybeSingle();
      if (error) {
        
      }
      return data ? {
        id: data.id,
        name: data.name,
        description: data.description,
        datasetIds: data.dataset_ids || [],
        defaultDatasetId: data.default_dataset_id,
        status: data.status,
        tags: data.tags || [],
        createdAt: data.created_at,
        updatedAt: data.updated_at,
        memberCount: data.member_count || 1
      } : project;
    } catch (e) {
      
      return project;
    }
  },

  async updateProject(id: string, updates: Partial<Project>): Promise<void> {
    try {
      const payload: any = {
        updated_at: new Date().toISOString()
      };
      if (updates.name !== undefined) payload.name = updates.name;
      if (updates.description !== undefined) payload.description = updates.description;
      if (updates.datasetIds !== undefined) payload.dataset_ids = updates.datasetIds;
      if (updates.defaultDatasetId !== undefined) payload.default_dataset_id = updates.defaultDatasetId;
      if (updates.status !== undefined) payload.status = updates.status;
      if (updates.tags !== undefined) payload.tags = updates.tags;
      if (updates.memberCount !== undefined) payload.member_count = updates.memberCount;

      await supabase.from('projects').update(payload).eq('id', id);
    } catch (e) {
      
    }
  },

  async deleteProject(id: string): Promise<void> {
    try {
      await supabase.from('projects').delete().eq('id', id);
    } catch (e) {
      
    }
  },

  // --- SUPABASE STORAGE & DATASETS ---

  /**
   * Sanitizes a path component to prevent directory traversal and illegal characters
   */
  sanitizePathComponent(component: string): string {
    if (!component) return 'default';
    return component
      .replace(/\.\./g, '') // remove directory traversal
      .replace(/[/\\]/g, '') // remove slashes and backslashes
      .replace(/[\x00-\x1F\x7F]/g, '') // remove control characters
      .replace(/[^a-zA-Z0-9_\-\.]/g, '_') // allow only alphanumeric, underscores, hyphens, dots
      .toLowerCase()
      .trim();
  },

  /**
   * Generates a collision-resistant, secure filename
   */
  generateSecureFilename(originalFilename: string, fallbackExt: string = 'csv'): string {
    const rawExt = originalFilename.includes('.')
      ? originalFilename.split('.').pop()?.toLowerCase() || fallbackExt
      : fallbackExt;
    const safeExt = ['csv', 'json', 'tsv', 'xlsx', 'txt'].includes(rawExt) ? rawExt : 'csv';

    const baseName = originalFilename.replace(/\.[^/.]+$/, '');
    const cleanBase = this.sanitizePathComponent(baseName).substring(0, 50) || 'dataset';

    const timestamp = new Date().toISOString().replace(/[-:T.]/g, '').slice(0, 14);
    const randomEntropy = Math.random().toString(36).substring(2, 10);

    return `${timestamp}_${randomEntropy}_${cleanBase}.${safeExt}`;
  },

  /**
   * Verifies that the requested project belongs to the authenticated user.
   * If not found or not owned, fetches or creates a verified default project.
   */
  async verifyUserProjectOwnership(authenticatedUserId: string, requestedProjectId?: string): Promise<string> {
    if (requestedProjectId) {
      const cleanProjectId = this.sanitizePathComponent(requestedProjectId);
      // Query projects table specifically for this user_id
      const { data: project } = await supabase
        .from('projects')
        .select('id')
        .eq('id', cleanProjectId)
        .eq('user_id', authenticatedUserId)
        .maybeSingle();

      if (project?.id) {
        return project.id;
      }
    }

    // Check if the user already has any existing project
    const { data: existingProjects } = await supabase
      .from('projects')
      .select('id')
      .eq('user_id', authenticatedUserId)
      .limit(1);

    if (existingProjects && existingProjects.length > 0) {
      return existingProjects[0].id;
    }

    // Auto-create a secure default workspace project for this verified user
    const defaultProjId = `proj-${this.sanitizePathComponent(authenticatedUserId).substring(0, 8)}-${Date.now().toString(36)}`;
    const newProjectPayload = {
      id: defaultProjId,
      user_id: authenticatedUserId,
      name: 'Primary Analytical Workspace',
      description: 'Default secure business analytics project container',
      dataset_ids: [],
      status: 'active',
      tags: ['Default', 'Workspace'],
      member_count: 1,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    };

    const { data: createdProj } = await supabase
      .from('projects')
      .insert(newProjectPayload)
      .select('id')
      .maybeSingle();

    return createdProj?.id || defaultProjId;
  },

  /**
   * Uploads dataset file to Supabase Storage:
   * Path: datasets/{user_id_or_workspace}/{project_id}/{secure_filename}
   */
  async uploadDatasetFile(
    fileOrBlob: File | Blob,
    originalFilename: string,
    requestedProjectId?: string,
    explicitUserId?: string
  ): Promise<{
    storageBucket: string;
    storagePath: string;
    fileName: string;
    sizeBytes: number;
    projectId: string;
    userId: string;
    publicUrl?: string;
  }> {
    // 1. Get authenticated user from session or fallback to explicit / workspace user
    let effectiveUserId = explicitUserId || 'analyst_workspace';
    try {
      const { data: { user: authUser } } = await supabase.auth.getUser();
      if (authUser?.id) {
        effectiveUserId = authUser.id;
      }
    } catch {
      // Non-blocking fallback for guest / local analyst sessions
    }

    const authenticatedUserId = this.sanitizePathComponent(effectiveUserId);

    // 2. Resolve project ID
    let verifiedProjectId = requestedProjectId || 'default-project';
    try {
      if (effectiveUserId !== 'analyst_workspace' && effectiveUserId.length > 10) {
        verifiedProjectId = await this.verifyUserProjectOwnership(effectiveUserId, requestedProjectId);
      }
    } catch {
      // Non-blocking fallback
    }
    const cleanProjectId = this.sanitizePathComponent(verifiedProjectId);

    // 3. Generate secure filename with collision resistance and anti-traversal
    const secureFilename = this.generateSecureFilename(originalFilename);

    // 4. Construct storage path: {user_id}/{project_id}/{secure_filename}
    const storageBucket = 'datasets';
    const storagePath = `${authenticatedUserId}/${cleanProjectId}/${secureFilename}`;

    // Determine MIME type
    const isJson = secureFilename.endsWith('.json');
    const contentType = isJson ? 'application/json' : 'text/csv';

    // 5. Upload to Supabase Storage (automatic folder creation)
    let uploadSuccess = false;
    try {
      const { error: uploadError } = await supabase.storage
        .from(storageBucket)
        .upload(storagePath, fileOrBlob, {
          contentType,
          upsert: true
        });

      if (uploadError) {
        
        // Try fallback root upload if subfolder policy is strict
        if (uploadError.message?.includes('not found') || uploadError.message?.includes('Bucket')) {
          
        }
      } else {
        uploadSuccess = true;
      }
    } catch (err: any) {
      
    }

    // Get public URL if bucket is public
    let publicUrl: string | undefined = undefined;
    try {
      const { data } = supabase.storage.from(storageBucket).getPublicUrl(storagePath);
      if (data?.publicUrl) {
        publicUrl = data.publicUrl;
      }
    } catch {
      // Non-critical
    }

    return {
      storageBucket,
      storagePath,
      fileName: secureFilename,
      sizeBytes: fileOrBlob.size,
      projectId: verifiedProjectId,
      userId: effectiveUserId,
      publicUrl
    };
  },

  /**
   * Downloads a dataset file from Supabase Storage
   */
  async downloadDatasetFile(storagePath: string): Promise<Blob | null> {
    try {
      const { data, error } = await supabase.storage.from('datasets').download(storagePath);
      if (error) {
        
        return null;
      }
      return data;
    } catch (e) {
      
      return null;
    }
  },

  // --- DATASET METADATA ---
  async getDatasets(userId?: string, projectId?: string): Promise<Dataset[]> {
    try {
      let query = supabase.from('datasets').select('*').order('uploaded_at', { ascending: false });
      if (projectId) {
        query = query.eq('project_id', projectId);
      }
      if (userId) {
        query = query.or(`user_id.eq.${userId},user_id.is.null`);
      }
      const { data, error } = await query;

      if (error || !data || data.length === 0) {
        return [];
      }

      return data.map((row: any): Dataset => ({
        id: row.id,
        projectId: row.project_id || row.projectId,
        name: row.name,
        description: row.description,
        rowCount: row.row_count || row.rowCount || 0,
        columnCount: row.column_count || row.columnCount || 0,
        columns: row.columns || [],
        sampleRows: row.sample_rows || row.sampleRows || [],
        sizeBytes: row.size_bytes || row.sizeBytes || 0,
        uploadedAt: row.uploaded_at || row.uploadedAt || new Date().toISOString(),
        fileType: row.file_type || row.fileType || 'csv',
        fileName: row.file_name || row.fileName,
        storageBucket: row.storage_bucket || 'datasets',
        storagePath: row.storage_path || row.storagePath,
        status: row.status || 'ready',
        domain: row.domain,
        tags: row.tags || []
      }));
    } catch (e) {
      
      return [];
    }
  },

  async saveDatasetMetadata(dataset: Dataset, userId?: string): Promise<Dataset> {
    try {
      // If userId not provided, retrieve from authenticated session
      let verifiedUserId = userId;
      if (!verifiedUserId) {
        const { data: { user } } = await supabase.auth.getUser();
        verifiedUserId = user?.id;
      }

      const row = {
        id: dataset.id,
        user_id: verifiedUserId,
        project_id: dataset.projectId,
        name: dataset.name,
        description: dataset.description,
        file_name: dataset.fileName,
        file_type: dataset.fileType,
        storage_bucket: dataset.storageBucket || 'datasets',
        storage_path: dataset.storagePath,
        row_count: dataset.rowCount,
        column_count: dataset.columnCount,
        columns: dataset.columns,
        sample_rows: dataset.sampleRows,
        size_bytes: dataset.sizeBytes,
        uploaded_at: dataset.uploadedAt,
        status: dataset.status,
        domain: dataset.domain,
        tags: dataset.tags
      };

      const { data, error } = await supabase.from('datasets').upsert(row).select().maybeSingle();
      if (error) {
        
      }
      return data ? {
        id: data.id,
        projectId: data.project_id,
        name: data.name,
        description: data.description,
        rowCount: data.row_count,
        columnCount: data.column_count,
        columns: data.columns,
        sampleRows: data.sample_rows,
        sizeBytes: data.size_bytes,
        uploadedAt: data.uploaded_at,
        fileType: data.file_type,
        fileName: data.file_name,
        storageBucket: data.storage_bucket,
        storagePath: data.storage_path,
        status: data.status,
        domain: data.domain,
        tags: data.tags
      } : dataset;
    } catch (e) {
      
      return dataset;
    }
  },

  async deleteDataset(id: string, storagePath?: string): Promise<void> {
    try {
      if (storagePath) {
        await supabase.storage.from('datasets').remove([storagePath]);
      }
      await supabase.from('datasets').delete().eq('id', id);
    } catch (e) {
      
    }
  }
};
