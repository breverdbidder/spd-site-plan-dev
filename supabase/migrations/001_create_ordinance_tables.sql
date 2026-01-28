-- SPD Ordinance Scraper - Supabase Schema
-- Migration: 001_create_ordinance_tables

-- Municipalities table
CREATE TABLE IF NOT EXISTS municipalities (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  state TEXT NOT NULL,
  county TEXT,
  municode_url TEXT,
  last_scraped TIMESTAMPTZ,
  scrape_status TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(name, state)
);

-- Zoning districts table
CREATE TABLE IF NOT EXISTS zoning_districts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  municipality_id UUID REFERENCES municipalities(id) ON DELETE CASCADE,
  code TEXT NOT NULL,
  name TEXT,
  description TEXT,
  source_section TEXT,
  flum_designation TEXT,
  min_lot_size TEXT,
  max_density TEXT,
  setbacks JSONB,
  permitted_uses TEXT[],
  conditional_uses TEXT[],
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(municipality_id, code)
);

-- Ordinance sections table
CREATE TABLE IF NOT EXISTS ordinance_sections (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  municipality_id UUID REFERENCES municipalities(id) ON DELETE CASCADE,
  section_type TEXT NOT NULL, -- 'toc', 'site_plan_review', 'zoning', 'stormwater', etc.
  title TEXT NOT NULL,
  node_id TEXT,
  municode_url TEXT,
  content_sample TEXT,
  full_content TEXT,
  parent_section_id UUID REFERENCES ordinance_sections(id),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(municipality_id, node_id)
);

-- Site plan requirements table
CREATE TABLE IF NOT EXISTS site_plan_requirements (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  municipality_id UUID REFERENCES municipalities(id) ON DELETE CASCADE,
  requirement_type TEXT NOT NULL, -- 'trigger', 'document', 'process', 'fee'
  description TEXT NOT NULL,
  threshold_value TEXT,
  threshold_unit TEXT,
  source_section TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Raw scrape results table
CREATE TABLE IF NOT EXISTS scrape_results (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  municipality TEXT NOT NULL,
  state TEXT NOT NULL,
  scraped_at TIMESTAMPTZ NOT NULL,
  status TEXT NOT NULL,
  raw_data JSONB,
  error_message TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_zoning_districts_municipality ON zoning_districts(municipality_id);
CREATE INDEX IF NOT EXISTS idx_ordinance_sections_municipality ON ordinance_sections(municipality_id);
CREATE INDEX IF NOT EXISTS idx_ordinance_sections_type ON ordinance_sections(section_type);
CREATE INDEX IF NOT EXISTS idx_site_plan_requirements_municipality ON site_plan_requirements(municipality_id);
CREATE INDEX IF NOT EXISTS idx_scrape_results_municipality ON scrape_results(municipality, state);

-- Enable RLS
ALTER TABLE municipalities ENABLE ROW LEVEL SECURITY;
ALTER TABLE zoning_districts ENABLE ROW LEVEL SECURITY;
ALTER TABLE ordinance_sections ENABLE ROW LEVEL SECURITY;
ALTER TABLE site_plan_requirements ENABLE ROW LEVEL SECURITY;
ALTER TABLE scrape_results ENABLE ROW LEVEL SECURITY;

-- Public read policy (adjust as needed)
CREATE POLICY "Public read access" ON municipalities FOR SELECT USING (true);
CREATE POLICY "Public read access" ON zoning_districts FOR SELECT USING (true);
CREATE POLICY "Public read access" ON ordinance_sections FOR SELECT USING (true);
CREATE POLICY "Public read access" ON site_plan_requirements FOR SELECT USING (true);
CREATE POLICY "Public read access" ON scrape_results FOR SELECT USING (true);

-- Service role write policy
CREATE POLICY "Service role insert" ON municipalities FOR INSERT WITH CHECK (true);
CREATE POLICY "Service role update" ON municipalities FOR UPDATE USING (true);
CREATE POLICY "Service role insert" ON zoning_districts FOR INSERT WITH CHECK (true);
CREATE POLICY "Service role update" ON zoning_districts FOR UPDATE USING (true);
CREATE POLICY "Service role insert" ON ordinance_sections FOR INSERT WITH CHECK (true);
CREATE POLICY "Service role update" ON ordinance_sections FOR UPDATE USING (true);
CREATE POLICY "Service role insert" ON site_plan_requirements FOR INSERT WITH CHECK (true);
CREATE POLICY "Service role insert" ON scrape_results FOR INSERT WITH CHECK (true);
