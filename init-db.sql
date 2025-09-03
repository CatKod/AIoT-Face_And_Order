-- Create database if not exists (PostgreSQL automatically creates it)
-- This script runs during container initialization

-- Create extension for UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create indexes for better performance
DO $$
BEGIN
    -- Check if we need to create indexes after tables are created
    -- This will be run by the application initialization
END $$;
