-- Nebula - Supabase PostgreSQL Schema
-- Multi-tenant schema for adaptive learning platform
-- Run this in Supabase SQL Editor: Dashboard → SQL Editor → New Query

-- ============================================================
-- 1. USERS TABLE (Real user accounts from Google OAuth)
-- ============================================================
-- This table is automatically managed by Supabase Auth
-- We just need to create a profile table that references it

CREATE TABLE IF NOT EXISTS public.user_profiles (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    user_context TEXT,          -- What the user already knows (baseline)
    learning_goal TEXT,          -- What they want to learn (objective)
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_active TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id)  -- One learning profile per user
);

-- ============================================================
-- 2. LEARNING PATHS TABLE
-- ============================================================
-- Stores AI-generated learning curricula per user

CREATE TABLE IF NOT EXISTS public.learning_paths (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    path_json JSONB NOT NULL,  -- PostgreSQL native JSON (faster than TEXT)
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- 3. MODULE CHALLENGES TABLE
-- ============================================================
-- Stores lesson plans with URAC framework per module per user

CREATE TABLE IF NOT EXISTS public.module_challenges (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    module_number INTEGER NOT NULL,
    challenges_json JSONB NOT NULL,  -- Module lesson plans, URAC blueprints
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, module_number)  -- One challenge set per module per user
);

-- ============================================================
-- 4. CHALLENGE PROGRESS TABLE
-- ============================================================
-- Tracks individual challenge completion status per user

CREATE TABLE IF NOT EXISTS public.challenge_progress (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    module_number INTEGER NOT NULL,
    challenge_number INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'not_started' CHECK(status IN ('not_started', 'in_progress', 'completed')),
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, module_number, challenge_number)  -- One progress entry per challenge per user
);

-- ============================================================
-- 5. TOKEN USAGE TABLE (NEW - for admin monitoring)
-- ============================================================
-- Tracks AI API token consumption per user for cost monitoring

CREATE TABLE IF NOT EXISTS public.token_usage (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    agent_name TEXT NOT NULL,  -- 'learning_path', 'module_planner', 'mastery_engine', 'pre_recall_primer'
    prompt_tokens INTEGER NOT NULL DEFAULT 0,
    completion_tokens INTEGER NOT NULL DEFAULT 0,
    total_tokens INTEGER NOT NULL DEFAULT 0,
    model_name TEXT,  -- 'gemini-flash', 'groq-llama-3.3-70b', etc.
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- 6. ADMIN USERS TABLE (NEW - for admin dashboard access)
-- ============================================================
-- Tracks which users have admin privileges

CREATE TABLE IF NOT EXISTS public.admin_users (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id)
);

-- ============================================================
-- INDEXES (for faster queries)
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_user_profiles_user_id ON public.user_profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_learning_paths_user_id ON public.learning_paths(user_id);
CREATE INDEX IF NOT EXISTS idx_module_challenges_user_id ON public.module_challenges(user_id);
CREATE INDEX IF NOT EXISTS idx_module_challenges_user_module ON public.module_challenges(user_id, module_number);
CREATE INDEX IF NOT EXISTS idx_challenge_progress_user_id ON public.challenge_progress(user_id);
CREATE INDEX IF NOT EXISTS idx_challenge_progress_user_module ON public.challenge_progress(user_id, module_number);
CREATE INDEX IF NOT EXISTS idx_challenge_progress_status ON public.challenge_progress(user_id, status);
CREATE INDEX IF NOT EXISTS idx_token_usage_user_id ON public.token_usage(user_id);
CREATE INDEX IF NOT EXISTS idx_token_usage_created_at ON public.token_usage(created_at);
CREATE INDEX IF NOT EXISTS idx_admin_users_user_id ON public.admin_users(user_id);

-- ============================================================
-- ROW LEVEL SECURITY (RLS) - Data Isolation Per User
-- ============================================================
-- This ensures users can ONLY access their own data

-- Enable RLS on all tables
ALTER TABLE public.user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.learning_paths ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.module_challenges ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.challenge_progress ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.token_usage ENABLE ROW LEVEL SECURITY;

-- Policies: Users can only read/write their own data
CREATE POLICY "Users can view own profile" ON public.user_profiles
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can update own profile" ON public.user_profiles
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can view own learning paths" ON public.learning_paths
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can manage own learning paths" ON public.learning_paths
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can view own module challenges" ON public.module_challenges
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can manage own module challenges" ON public.module_challenges
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can view own challenge progress" ON public.challenge_progress
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can manage own challenge progress" ON public.challenge_progress
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can view own token usage" ON public.token_usage
    FOR SELECT USING (auth.uid() = user_id);

-- ============================================================
-- ADMIN POLICIES - Admins can view all data
-- ============================================================

CREATE POLICY "Admins can view all user profiles" ON public.user_profiles
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM public.admin_users
            WHERE admin_users.user_id = auth.uid()
        )
    );

CREATE POLICY "Admins can view all token usage" ON public.token_usage
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM public.admin_users
            WHERE admin_users.user_id = auth.uid()
        )
    );

-- ============================================================
-- HELPER FUNCTION - Auto-update updated_at timestamp
-- ============================================================

CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-update updated_at on challenge_progress
CREATE TRIGGER update_challenge_progress_updated_at
    BEFORE UPDATE ON public.challenge_progress
    FOR EACH ROW
    EXECUTE FUNCTION public.update_updated_at_column();

-- ============================================================
-- INITIAL SETUP COMPLETE
-- ============================================================
-- You can now:
-- 1. Users will auto-create when they sign in with Google
-- 2. Backend will create user_profiles when they first use the app
-- 3. Row Level Security ensures data isolation per user
