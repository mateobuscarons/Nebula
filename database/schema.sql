-- Adaptive Learning OS - Database Schema
-- SQLite database for user profiles, learning paths, and progress tracking

-- User profile and current state
CREATE TABLE IF NOT EXISTS user_profile (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_context TEXT,  -- What the user already knows (baseline)
    learning_goal TEXT NOT NULL,  -- What the user wants to achieve (objective)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Learning path storage
CREATE TABLE IF NOT EXISTS learning_path (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    path_json TEXT NOT NULL,  -- Full learning_path_output.json as JSON string
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES user_profile(id) ON DELETE CASCADE
);

-- Module challenges storage (includes pre-generated primers)
CREATE TABLE IF NOT EXISTS module_challenges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    module_number INTEGER NOT NULL,
    challenges_json TEXT NOT NULL,  -- Full module_X_challenges.json as JSON string (includes primers)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES user_profile(id) ON DELETE CASCADE,
    UNIQUE(user_id, module_number)  -- One challenge set per module per user
);

-- Challenge progress tracking (minimal - just tracking status)
CREATE TABLE IF NOT EXISTS challenge_progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    module_number INTEGER NOT NULL,
    challenge_number INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'not_started' CHECK(status IN ('not_started', 'in_progress', 'completed')),
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES user_profile(id) ON DELETE CASCADE,
    UNIQUE(user_id, module_number, challenge_number)  -- One progress entry per challenge per user
);

-- Indexes for faster queries
CREATE INDEX IF NOT EXISTS idx_learning_path_user ON learning_path(user_id);
CREATE INDEX IF NOT EXISTS idx_module_challenges_user ON module_challenges(user_id);
CREATE INDEX IF NOT EXISTS idx_module_challenges_module ON module_challenges(user_id, module_number);
CREATE INDEX IF NOT EXISTS idx_challenge_progress_user ON challenge_progress(user_id);
CREATE INDEX IF NOT EXISTS idx_challenge_progress_module ON challenge_progress(user_id, module_number);
CREATE INDEX IF NOT EXISTS idx_challenge_progress_status ON challenge_progress(user_id, status);
