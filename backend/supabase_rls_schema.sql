-- ============================================================================
-- SUPABASE ROW-LEVEL SECURITY (RLS) MIGRATION & HARDENING SCRIPT
-- Application: InsightFlow Analytics Platform
-- ============================================================================

-- 1. PROJECTS TABLE
CREATE TABLE IF NOT EXISTS public.projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    dataset_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE public.projects ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can only view their own projects"
ON public.projects FOR SELECT
USING (auth.uid() = user_id);

CREATE POLICY "Users can only insert projects for themselves"
ON public.projects FOR INSERT
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can only update their own projects"
ON public.projects FOR UPDATE
USING (auth.uid() = user_id);

CREATE POLICY "Users can only delete their own projects"
ON public.projects FOR DELETE
USING (auth.uid() = user_id);

-- 2. DATASETS TABLE
CREATE TABLE IF NOT EXISTS public.datasets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    project_id UUID REFERENCES public.projects(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    file_name TEXT NOT NULL,
    file_type TEXT NOT NULL,
    storage_bucket TEXT DEFAULT 'datasets',
    storage_path TEXT NOT NULL,
    row_count INTEGER DEFAULT 0,
    column_count INTEGER DEFAULT 0,
    columns JSONB DEFAULT '[]'::jsonb,
    sample_rows JSONB DEFAULT '[]'::jsonb,
    size_bytes BIGINT DEFAULT 0,
    status TEXT DEFAULT 'completed',
    error_message TEXT,
    tags TEXT[] DEFAULT ARRAY[]::TEXT[],
    processing_time_ms NUMERIC,
    uploaded_at TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE public.datasets ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can only view their own datasets"
ON public.datasets FOR SELECT
USING (auth.uid() = user_id);

CREATE POLICY "Users can only insert datasets for themselves"
ON public.datasets FOR INSERT
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can only update their own datasets"
ON public.datasets FOR UPDATE
USING (auth.uid() = user_id);

CREATE POLICY "Users can only delete their own datasets"
ON public.datasets FOR DELETE
USING (auth.uid() = user_id);

-- 3. CHAT HISTORY TABLE
CREATE TABLE IF NOT EXISTS public.chat_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    dataset_id UUID REFERENCES public.datasets(id) ON DELETE CASCADE,
    query TEXT NOT NULL,
    answer TEXT NOT NULL,
    relevant_columns TEXT[] DEFAULT ARRAY[]::TEXT[],
    supporting_metrics JSONB DEFAULT '{}'::jsonb,
    chart_config JSONB,
    created_at TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE public.chat_history ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can only view their own chat history"
ON public.chat_history FOR SELECT
USING (auth.uid() = user_id);

CREATE POLICY "Users can only insert chat messages for themselves"
ON public.chat_history FOR INSERT
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can only delete their own chat history"
ON public.chat_history FOR DELETE
USING (auth.uid() = user_id);

-- 4. STORAGE BUCKET ROW LEVEL SECURITY (datasets bucket)
-- Allows users to upload/download strictly inside their own user folder: {user_id}/...
INSERT INTO storage.buckets (id, name, public) 
VALUES ('datasets', 'datasets', false)
ON CONFLICT (id) DO NOTHING;

CREATE POLICY "Users can view their own dataset storage files"
ON storage.objects FOR SELECT
TO authenticated
USING (bucket_id = 'datasets' AND (storage.foldername(name))[1] = auth.uid()::text);

CREATE POLICY "Users can upload their own dataset storage files"
ON storage.objects FOR INSERT
TO authenticated
WITH CHECK (bucket_id = 'datasets' AND (storage.foldername(name))[1] = auth.uid()::text);

CREATE POLICY "Users can delete their own dataset storage files"
ON storage.objects FOR DELETE
TO authenticated
USING (bucket_id = 'datasets' AND (storage.foldername(name))[1] = auth.uid()::text);
