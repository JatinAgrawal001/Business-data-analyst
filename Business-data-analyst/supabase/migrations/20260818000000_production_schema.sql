-- ==============================================================================
-- PRODUCTION SUPABASE MIGRATION: InsightFlow AI Platform
-- ==============================================================================
-- Description: Complete schema migration for multi-tenant analytical workspace.
-- Features:
--   1. UUID Primary Keys (gen_random_uuid())
--   2. Strict Foreign Key Cascades & Constraints
--   3. Auto-updating Timestamps & Triggers
--   4. Performance Indexes for Foreign Keys & Filtering
--   5. Row Level Security (RLS) & Idempotent Granular Policies
--   6. Supabase Storage Bucket & Storage Security Policies
--   7. Automatic User Profile Provisioning Trigger
-- ==============================================================================

-- 0. EXTENSIONS & UTILITIES
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Reusable timestamp updater trigger function
CREATE OR REPLACE FUNCTION public.handle_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;


-- ==============================================================================
-- 1. TABLE: profiles
-- ==============================================================================
CREATE TABLE IF NOT EXISTS public.profiles (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  email TEXT NOT NULL,
  avatar_url TEXT,
  role TEXT DEFAULT 'Business Data Analyst',
  company TEXT,
  plan TEXT DEFAULT 'Starter' CHECK (plan IN ('Starter', 'Professional', 'Enterprise')),
  preferences JSONB DEFAULT '{"theme": "dark", "emailAlerts": true, "autoInsightDetection": true, "defaultConfidenceInterval": 95}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view their own profile" ON public.profiles;
CREATE POLICY "Users can view their own profile"
  ON public.profiles FOR SELECT
  USING (auth.uid() = id);

DROP POLICY IF EXISTS "Users can insert their own profile" ON public.profiles;
CREATE POLICY "Users can insert their own profile"
  ON public.profiles FOR INSERT
  WITH CHECK (auth.uid() = id);

DROP POLICY IF EXISTS "Users can update their own profile" ON public.profiles;
CREATE POLICY "Users can update their own profile"
  ON public.profiles FOR UPDATE
  USING (auth.uid() = id)
  WITH CHECK (auth.uid() = id);

DROP POLICY IF EXISTS "Users can delete their own profile" ON public.profiles;
CREATE POLICY "Users can delete their own profile"
  ON public.profiles FOR DELETE
  USING (auth.uid() = id);

DROP TRIGGER IF EXISTS set_profiles_updated_at ON public.profiles;
CREATE TRIGGER set_profiles_updated_at
  BEFORE UPDATE ON public.profiles
  FOR EACH ROW
  EXECUTE FUNCTION public.handle_updated_at();

-- Auto-provision profile on auth.users registration
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.profiles (id, name, email, avatar_url, role, company, plan)
  VALUES (
    NEW.id,
    COALESCE(NEW.raw_user_meta_data->>'name', split_part(NEW.email, '@', 1)),
    NEW.email,
    COALESCE(NEW.raw_user_meta_data->>'avatar_url', 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&auto=format&fit=crop&q=80'),
    COALESCE(NEW.raw_user_meta_data->>'role', 'Business Data Analyst'),
    COALESCE(NEW.raw_user_meta_data->>'company', 'Enterprise Workspace'),
    COALESCE(NEW.raw_user_meta_data->>'plan', 'Starter')
  )
  ON CONFLICT (id) DO UPDATE SET
    email = EXCLUDED.email,
    updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();


-- ==============================================================================
-- 2. TABLE: projects
-- ==============================================================================
CREATE TABLE IF NOT EXISTS public.projects (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  description TEXT,
  status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'archived', 'analyzing')),
  tags TEXT[] DEFAULT ARRAY[]::TEXT[],
  default_dataset_id UUID,
  member_count INT NOT NULL DEFAULT 1,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE public.projects ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can select own projects" ON public.projects;
CREATE POLICY "Users can select own projects"
  ON public.projects FOR SELECT
  USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert own projects" ON public.projects;
CREATE POLICY "Users can insert own projects"
  ON public.projects FOR INSERT
  WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own projects" ON public.projects;
CREATE POLICY "Users can update own projects"
  ON public.projects FOR UPDATE
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete own projects" ON public.projects;
CREATE POLICY "Users can delete own projects"
  ON public.projects FOR DELETE
  USING (auth.uid() = user_id);

CREATE INDEX IF NOT EXISTS idx_projects_user_id ON public.projects(user_id);
CREATE INDEX IF NOT EXISTS idx_projects_status ON public.projects(status);
CREATE INDEX IF NOT EXISTS idx_projects_created_at ON public.projects(created_at DESC);

DROP TRIGGER IF EXISTS set_projects_updated_at ON public.projects;
CREATE TRIGGER set_projects_updated_at
  BEFORE UPDATE ON public.projects
  FOR EACH ROW
  EXECUTE FUNCTION public.handle_updated_at();


-- ==============================================================================
-- 3. TABLE: datasets
-- (Raw CSV/XLS/XLSX file binaries stored in Supabase Storage bucket `datasets`)
-- ==============================================================================
CREATE TABLE IF NOT EXISTS public.datasets (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
  project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  description TEXT,
  file_name TEXT,
  file_type TEXT NOT NULL CHECK (file_type IN ('csv', 'json', 'xlsx', 'sql', 'api')),
  storage_bucket TEXT DEFAULT 'datasets',
  storage_path TEXT, -- Object key inside Supabase Storage (e.g. 'user_id/project_id/file.csv')
  size_bytes BIGINT NOT NULL DEFAULT 0,
  row_count INT NOT NULL DEFAULT 0,
  column_count INT NOT NULL DEFAULT 0,
  columns JSONB NOT NULL DEFAULT '[]'::jsonb,
  sample_rows JSONB NOT NULL DEFAULT '[]'::jsonb,
  status TEXT NOT NULL DEFAULT 'ready' CHECK (status IN ('uploaded', 'profiling', 'ready', 'error')),
  domain TEXT,
  tags TEXT[] DEFAULT ARRAY[]::TEXT[],
  uploaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Safely add foreign key for default_dataset_id on projects if not already existing
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_projects_default_dataset'
  ) THEN
    ALTER TABLE public.projects
      ADD CONSTRAINT fk_projects_default_dataset
      FOREIGN KEY (default_dataset_id)
      REFERENCES public.datasets(id)
      ON DELETE SET NULL;
  END IF;
END $$;

ALTER TABLE public.datasets ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can select own datasets" ON public.datasets;
CREATE POLICY "Users can select own datasets"
  ON public.datasets FOR SELECT
  USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert own datasets" ON public.datasets;
CREATE POLICY "Users can insert own datasets"
  ON public.datasets FOR INSERT
  WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own datasets" ON public.datasets;
CREATE POLICY "Users can update own datasets"
  ON public.datasets FOR UPDATE
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete own datasets" ON public.datasets;
CREATE POLICY "Users can delete own datasets"
  ON public.datasets FOR DELETE
  USING (auth.uid() = user_id);

CREATE INDEX IF NOT EXISTS idx_datasets_user_id ON public.datasets(user_id);
CREATE INDEX IF NOT EXISTS idx_datasets_project_id ON public.datasets(project_id);
CREATE INDEX IF NOT EXISTS idx_datasets_status ON public.datasets(status);
CREATE INDEX IF NOT EXISTS idx_datasets_created_at ON public.datasets(created_at DESC);

DROP TRIGGER IF EXISTS set_datasets_updated_at ON public.datasets;
CREATE TRIGGER set_datasets_updated_at
  BEFORE UPDATE ON public.datasets
  FOR EACH ROW
  EXECUTE FUNCTION public.handle_updated_at();


-- ==============================================================================
-- 4. TABLE: analyses
-- ==============================================================================
CREATE TABLE IF NOT EXISTS public.analyses (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
  project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
  dataset_id UUID NOT NULL REFERENCES public.datasets(id) ON DELETE CASCADE,
  status TEXT NOT NULL DEFAULT 'completed' CHECK (status IN ('queued', 'running', 'completed', 'failed')),
  progress_percentage INT NOT NULL DEFAULT 100 CHECK (progress_percentage BETWEEN 0 AND 100),
  current_step TEXT DEFAULT 'Analysis complete',
  kpis JSONB NOT NULL DEFAULT '[]'::jsonb,
  charts JSONB NOT NULL DEFAULT '[]'::jsonb,
  statistical_summary JSONB NOT NULL DEFAULT '{}'::jsonb,
  anomalies_detected_count INT NOT NULL DEFAULT 0,
  correlation_matrix JSONB NOT NULL DEFAULT '[]'::jsonb,
  completed_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE public.analyses ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can select own analyses" ON public.analyses;
CREATE POLICY "Users can select own analyses"
  ON public.analyses FOR SELECT
  USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert own analyses" ON public.analyses;
CREATE POLICY "Users can insert own analyses"
  ON public.analyses FOR INSERT
  WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own analyses" ON public.analyses;
CREATE POLICY "Users can update own analyses"
  ON public.analyses FOR UPDATE
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete own analyses" ON public.analyses;
CREATE POLICY "Users can delete own analyses"
  ON public.analyses FOR DELETE
  USING (auth.uid() = user_id);

CREATE INDEX IF NOT EXISTS idx_analyses_user_id ON public.analyses(user_id);
CREATE INDEX IF NOT EXISTS idx_analyses_dataset_id ON public.analyses(dataset_id);
CREATE INDEX IF NOT EXISTS idx_analyses_project_id ON public.analyses(project_id);
CREATE INDEX IF NOT EXISTS idx_analyses_created_at ON public.analyses(created_at DESC);

DROP TRIGGER IF EXISTS set_analyses_updated_at ON public.analyses;
CREATE TRIGGER set_analyses_updated_at
  BEFORE UPDATE ON public.analyses
  FOR EACH ROW
  EXECUTE FUNCTION public.handle_updated_at();


-- ==============================================================================
-- 5. TABLE: insights
-- ==============================================================================
CREATE TABLE IF NOT EXISTS public.insights (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
  analysis_id UUID REFERENCES public.analyses(id) ON DELETE CASCADE,
  dataset_id UUID NOT NULL REFERENCES public.datasets(id) ON DELETE CASCADE,
  project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
  title TEXT NOT NULL,
  description TEXT NOT NULL,
  category TEXT NOT NULL CHECK (category IN ('trend', 'anomaly', 'correlation', 'distribution', 'performance', 'segment')),
  priority TEXT NOT NULL CHECK (priority IN ('critical', 'high', 'medium', 'low')),
  score NUMERIC(5,2) NOT NULL DEFAULT 85.00 CHECK (score BETWEEN 0 AND 100),
  key_metrics JSONB DEFAULT '[]'::jsonb,
  impact TEXT,
  action_required BOOLEAN NOT NULL DEFAULT FALSE,
  relevant_columns TEXT[] DEFAULT ARRAY[]::TEXT[],
  suggested_action TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE public.insights ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can select own insights" ON public.insights;
CREATE POLICY "Users can select own insights"
  ON public.insights FOR SELECT
  USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert own insights" ON public.insights;
CREATE POLICY "Users can insert own insights"
  ON public.insights FOR INSERT
  WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own insights" ON public.insights;
CREATE POLICY "Users can update own insights"
  ON public.insights FOR UPDATE
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete own insights" ON public.insights;
CREATE POLICY "Users can delete own insights"
  ON public.insights FOR DELETE
  USING (auth.uid() = user_id);

CREATE INDEX IF NOT EXISTS idx_insights_user_id ON public.insights(user_id);
CREATE INDEX IF NOT EXISTS idx_insights_dataset_id ON public.insights(dataset_id);
CREATE INDEX IF NOT EXISTS idx_insights_analysis_id ON public.insights(analysis_id);
CREATE INDEX IF NOT EXISTS idx_insights_priority ON public.insights(priority);
CREATE INDEX IF NOT EXISTS idx_insights_category ON public.insights(category);

DROP TRIGGER IF EXISTS set_insights_updated_at ON public.insights;
CREATE TRIGGER set_insights_updated_at
  BEFORE UPDATE ON public.insights
  FOR EACH ROW
  EXECUTE FUNCTION public.handle_updated_at();


-- ==============================================================================
-- 6. TABLE: recommendations
-- ==============================================================================
CREATE TABLE IF NOT EXISTS public.recommendations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
  analysis_id UUID REFERENCES public.analyses(id) ON DELETE CASCADE,
  dataset_id UUID NOT NULL REFERENCES public.datasets(id) ON DELETE CASCADE,
  project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
  title TEXT NOT NULL,
  executive_summary TEXT NOT NULL,
  detailed_steps TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
  expected_impact TEXT NOT NULL,
  impact_score INT NOT NULL DEFAULT 80 CHECK (impact_score BETWEEN 0 AND 100),
  confidence INT NOT NULL DEFAULT 90 CHECK (confidence BETWEEN 0 AND 100),
  difficulty TEXT NOT NULL CHECK (difficulty IN ('easy', 'moderate', 'hard')),
  timeframe TEXT NOT NULL,
  category TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'new' CHECK (status IN ('new', 'in_review', 'implemented', 'dismissed')),
  metrics_influenced TEXT[] DEFAULT ARRAY[]::TEXT[],
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE public.recommendations ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can select own recommendations" ON public.recommendations;
CREATE POLICY "Users can select own recommendations"
  ON public.recommendations FOR SELECT
  USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert own recommendations" ON public.recommendations;
CREATE POLICY "Users can insert own recommendations"
  ON public.recommendations FOR INSERT
  WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own recommendations" ON public.recommendations;
CREATE POLICY "Users can update own recommendations"
  ON public.recommendations FOR UPDATE
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete own recommendations" ON public.recommendations;
CREATE POLICY "Users can delete own recommendations"
  ON public.recommendations FOR DELETE
  USING (auth.uid() = user_id);

CREATE INDEX IF NOT EXISTS idx_recommendations_user_id ON public.recommendations(user_id);
CREATE INDEX IF NOT EXISTS idx_recommendations_dataset_id ON public.recommendations(dataset_id);
CREATE INDEX IF NOT EXISTS idx_recommendations_status ON public.recommendations(status);
CREATE INDEX IF NOT EXISTS idx_recommendations_created_at ON public.recommendations(created_at DESC);

DROP TRIGGER IF EXISTS set_recommendations_updated_at ON public.recommendations;
CREATE TRIGGER set_recommendations_updated_at
  BEFORE UPDATE ON public.recommendations
  FOR EACH ROW
  EXECUTE FUNCTION public.handle_updated_at();


-- ==============================================================================
-- 7. TABLE: forecasts
-- ==============================================================================
CREATE TABLE IF NOT EXISTS public.forecasts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
  analysis_id UUID REFERENCES public.analyses(id) ON DELETE CASCADE,
  dataset_id UUID NOT NULL REFERENCES public.datasets(id) ON DELETE CASCADE,
  project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
  target_metric_key TEXT NOT NULL,
  target_metric_label TEXT NOT NULL,
  time_column_key TEXT NOT NULL,
  historical_data JSONB NOT NULL DEFAULT '[]'::jsonb,
  forecast_data JSONB NOT NULL DEFAULT '[]'::jsonb,
  all_points JSONB DEFAULT '[]'::jsonb,
  confidence_interval INT NOT NULL DEFAULT 95,
  growth_rate NUMERIC(8,2) NOT NULL DEFAULT 0.00,
  model_used TEXT NOT NULL DEFAULT 'ARIMA + Exponential Smoothing Hybrid',
  horizon_periods INT NOT NULL DEFAULT 12,
  scenario_multipliers JSONB DEFAULT '{"optimistic": 1.15, "baseline": 1.0, "pessimistic": 0.85}'::jsonb,
  key_drivers JSONB NOT NULL DEFAULT '[]'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE public.forecasts ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can select own forecasts" ON public.forecasts;
CREATE POLICY "Users can select own forecasts"
  ON public.forecasts FOR SELECT
  USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert own forecasts" ON public.forecasts;
CREATE POLICY "Users can insert own forecasts"
  ON public.forecasts FOR INSERT
  WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own forecasts" ON public.forecasts;
CREATE POLICY "Users can update own forecasts"
  ON public.forecasts FOR UPDATE
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete own forecasts" ON public.forecasts;
CREATE POLICY "Users can delete own forecasts"
  ON public.forecasts FOR DELETE
  USING (auth.uid() = user_id);

CREATE INDEX IF NOT EXISTS idx_forecasts_user_id ON public.forecasts(user_id);
CREATE INDEX IF NOT EXISTS idx_forecasts_dataset_id ON public.forecasts(dataset_id);
CREATE INDEX IF NOT EXISTS idx_forecasts_created_at ON public.forecasts(created_at DESC);

DROP TRIGGER IF EXISTS set_forecasts_updated_at ON public.forecasts;
CREATE TRIGGER set_forecasts_updated_at
  BEFORE UPDATE ON public.forecasts
  FOR EACH ROW
  EXECUTE FUNCTION public.handle_updated_at();


-- ==============================================================================
-- 8. TABLE: chat_sessions
-- ==============================================================================
CREATE TABLE IF NOT EXISTS public.chat_sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
  project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
  dataset_id UUID REFERENCES public.datasets(id) ON DELETE SET NULL,
  title TEXT NOT NULL DEFAULT 'Analytical Consultation',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE public.chat_sessions ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can select own chat sessions" ON public.chat_sessions;
CREATE POLICY "Users can select own chat sessions"
  ON public.chat_sessions FOR SELECT
  USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert own chat sessions" ON public.chat_sessions;
CREATE POLICY "Users can insert own chat sessions"
  ON public.chat_sessions FOR INSERT
  WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own chat sessions" ON public.chat_sessions;
CREATE POLICY "Users can update own chat sessions"
  ON public.chat_sessions FOR UPDATE
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete own chat sessions" ON public.chat_sessions;
CREATE POLICY "Users can delete own chat sessions"
  ON public.chat_sessions FOR DELETE
  USING (auth.uid() = user_id);

CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_id ON public.chat_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_project_id ON public.chat_sessions(project_id);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_dataset_id ON public.chat_sessions(dataset_id);

DROP TRIGGER IF EXISTS set_chat_sessions_updated_at ON public.chat_sessions;
CREATE TRIGGER set_chat_sessions_updated_at
  BEFORE UPDATE ON public.chat_sessions
  FOR EACH ROW
  EXECUTE FUNCTION public.handle_updated_at();


-- ==============================================================================
-- 9. TABLE: chat_messages
-- ==============================================================================
CREATE TABLE IF NOT EXISTS public.chat_messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID NOT NULL REFERENCES public.chat_sessions(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
  role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
  content TEXT NOT NULL,
  suggested_questions TEXT[] DEFAULT ARRAY[]::TEXT[],
  generated_chart JSONB,
  sql_query TEXT,
  data_filter JSONB,
  reference_columns TEXT[] DEFAULT ARRAY[]::TEXT[],
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE public.chat_messages ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can select own chat messages" ON public.chat_messages;
CREATE POLICY "Users can select own chat messages"
  ON public.chat_messages FOR SELECT
  USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert own chat messages" ON public.chat_messages;
CREATE POLICY "Users can insert own chat messages"
  ON public.chat_messages FOR INSERT
  WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own chat messages" ON public.chat_messages;
CREATE POLICY "Users can update own chat messages"
  ON public.chat_messages FOR UPDATE
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete own chat messages" ON public.chat_messages;
CREATE POLICY "Users can delete own chat messages"
  ON public.chat_messages FOR DELETE
  USING (auth.uid() = user_id);

CREATE INDEX IF NOT EXISTS idx_chat_messages_session_id ON public.chat_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_user_id ON public.chat_messages(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_created_at ON public.chat_messages(created_at ASC);


-- ==============================================================================
-- 10. TABLE: reports
-- ==============================================================================
CREATE TABLE IF NOT EXISTS public.reports (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
  project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
  dataset_id UUID NOT NULL REFERENCES public.datasets(id) ON DELETE CASCADE,
  title TEXT NOT NULL,
  subtitle TEXT,
  executive_summary TEXT NOT NULL,
  author TEXT NOT NULL,
  sections JSONB NOT NULL DEFAULT '[]'::jsonb,
  status TEXT NOT NULL DEFAULT 'published' CHECK (status IN ('published', 'draft', 'scheduled')),
  format TEXT NOT NULL DEFAULT 'html' CHECK (format IN ('pdf', 'html', 'presentation')),
  cadence TEXT DEFAULT 'on_demand' CHECK (cadence IN ('daily', 'weekly', 'monthly', 'on_demand')),
  generated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE public.reports ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can select own reports" ON public.reports;
CREATE POLICY "Users can select own reports"
  ON public.reports FOR SELECT
  USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert own reports" ON public.reports;
CREATE POLICY "Users can insert own reports"
  ON public.reports FOR INSERT
  WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own reports" ON public.reports;
CREATE POLICY "Users can update own reports"
  ON public.reports FOR UPDATE
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete own reports" ON public.reports;
CREATE POLICY "Users can delete own reports"
  ON public.reports FOR DELETE
  USING (auth.uid() = user_id);

CREATE INDEX IF NOT EXISTS idx_reports_user_id ON public.reports(user_id);
CREATE INDEX IF NOT EXISTS idx_reports_project_id ON public.reports(project_id);
CREATE INDEX IF NOT EXISTS idx_reports_dataset_id ON public.reports(dataset_id);
CREATE INDEX IF NOT EXISTS idx_reports_created_at ON public.reports(created_at DESC);

DROP TRIGGER IF EXISTS set_reports_updated_at ON public.reports;
CREATE TRIGGER set_reports_updated_at
  BEFORE UPDATE ON public.reports
  FOR EACH ROW
  EXECUTE FUNCTION public.handle_updated_at();


-- ==============================================================================
-- 11. SUPABASE STORAGE: datasets bucket
-- Path Structure: datasets/{authenticated_user_id}/{project_id}/{secure_filename}
-- ==============================================================================
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
  'datasets',
  'datasets',
  false,
  52428800, -- 50 MB
  ARRAY[
    'text/csv',
    'application/json',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'text/plain'
  ]
)
ON CONFLICT (id) DO UPDATE SET
  file_size_limit = EXCLUDED.file_size_limit,
  allowed_mime_types = EXCLUDED.allowed_mime_types;

-- Clean up any old policy names if present
DROP POLICY IF EXISTS "Allow authenticated users to read own uploaded files" ON storage.objects;
DROP POLICY IF EXISTS "Allow authenticated users to upload files to own folder" ON storage.objects;
DROP POLICY IF EXISTS "Allow authenticated users to update own files" ON storage.objects;
DROP POLICY IF EXISTS "Allow authenticated users to delete own files" ON storage.objects;

-- Storage Row Level Security: datasets bucket with {user_id}/{project_id}/{secure_filename}
DROP POLICY IF EXISTS "Allow authenticated users to read own project dataset files" ON storage.objects;
CREATE POLICY "Allow authenticated users to read own project dataset files"
  ON storage.objects FOR SELECT
  TO authenticated
  USING (
    bucket_id = 'datasets' AND
    (storage.foldername(name))[1] = auth.uid()::text AND
    (
      (storage.foldername(name))[2] IS NULL OR
      EXISTS (
        SELECT 1 FROM public.projects p
        WHERE p.id::text = (storage.foldername(name))[2]
        AND p.user_id = auth.uid()
      )
    )
  );

DROP POLICY IF EXISTS "Allow authenticated users to upload to own project dataset folder" ON storage.objects;
CREATE POLICY "Allow authenticated users to upload to own project dataset folder"
  ON storage.objects FOR INSERT
  TO authenticated
  WITH CHECK (
    bucket_id = 'datasets' AND
    (storage.foldername(name))[1] = auth.uid()::text AND
    (
      (storage.foldername(name))[2] IS NULL OR
      EXISTS (
        SELECT 1 FROM public.projects p
        WHERE p.id::text = (storage.foldername(name))[2]
        AND p.user_id = auth.uid()
      )
    )
  );

DROP POLICY IF EXISTS "Allow authenticated users to update own project dataset files" ON storage.objects;
CREATE POLICY "Allow authenticated users to update own project dataset files"
  ON storage.objects FOR UPDATE
  TO authenticated
  USING (
    bucket_id = 'datasets' AND
    (storage.foldername(name))[1] = auth.uid()::text AND
    (
      (storage.foldername(name))[2] IS NULL OR
      EXISTS (
        SELECT 1 FROM public.projects p
        WHERE p.id::text = (storage.foldername(name))[2]
        AND p.user_id = auth.uid()
      )
    )
  );

DROP POLICY IF EXISTS "Allow authenticated users to delete own project dataset files" ON storage.objects;
CREATE POLICY "Allow authenticated users to delete own project dataset files"
  ON storage.objects FOR DELETE
  TO authenticated
  USING (
    bucket_id = 'datasets' AND
    (storage.foldername(name))[1] = auth.uid()::text AND
    (
      (storage.foldername(name))[2] IS NULL OR
      EXISTS (
        SELECT 1 FROM public.projects p
        WHERE p.id::text = (storage.foldername(name))[2]
        AND p.user_id = auth.uid()
      )
    )
  );
