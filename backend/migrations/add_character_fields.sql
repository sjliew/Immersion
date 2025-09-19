-- Migration: Add character fields to users table
-- This migration adds fields needed for character-based journal and conversation system

-- Add character fields to users table
ALTER TABLE users
ADD COLUMN IF NOT EXISTS character_name VARCHAR(100),
ADD COLUMN IF NOT EXISTS character_emoji VARCHAR(10),
ADD COLUMN IF NOT EXISTS character_location VARCHAR(50),
ADD COLUMN IF NOT EXISTS character_age_group VARCHAR(20),
ADD COLUMN IF NOT EXISTS character_gender VARCHAR(20),
ADD COLUMN IF NOT EXISTS character_start_date TIMESTAMPTZ;

-- Add indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_users_character_location ON users(character_location);
CREATE INDEX IF NOT EXISTS idx_users_character_age_group ON users(character_age_group);
CREATE INDEX IF NOT EXISTS idx_users_character_start_date ON users(character_start_date);

-- Add character attributes to conversations table for filtering
ALTER TABLE conversations
ADD COLUMN IF NOT EXISTS target_location VARCHAR(50),
ADD COLUMN IF NOT EXISTS target_age_group VARCHAR(20),
ADD COLUMN IF NOT EXISTS target_gender VARCHAR(20),
ADD COLUMN IF NOT EXISTS difficulty_progression INT DEFAULT 1;

-- Create a character_progress table to track character journey
CREATE TABLE IF NOT EXISTS character_progress (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    conversation_id UUID REFERENCES conversations(id),
    day_number INT,
    emotional_state VARCHAR(50),
    confidence_level INT,
    completed_at TIMESTAMPTZ DEFAULT NOW(),
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add indexes for character_progress
CREATE INDEX IF NOT EXISTS idx_character_progress_user_id ON character_progress(user_id);
CREATE INDEX IF NOT EXISTS idx_character_progress_day_number ON character_progress(day_number);

-- Add sample data for character-specific conversations
-- These would be filtered based on location, age group, and progression level
COMMENT ON COLUMN conversations.target_location IS 'Target location for this conversation (new-york, los-angeles, etc.)';
COMMENT ON COLUMN conversations.target_age_group IS 'Target age group (18-24, 25-34, etc.)';
COMMENT ON COLUMN conversations.target_gender IS 'Target gender (male, female, other, any)';
COMMENT ON COLUMN conversations.difficulty_progression IS 'Day range: 1=days 1-7, 2=days 8-30, 3=days 31-60, 4=days 60+';