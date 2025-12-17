#!/usr/bin/env python3
"""
Supabase Integration for SPD Rough Diamond Pipeline
Stores, scores, and queries parcels for annexation arbitrage opportunities

Author: BidDeed.AI / Everest Capital USA
Database: mocerqjnksmhcjzxrewo.supabase.co
"""

import os
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

# Use standard library for HTTP (no external deps required)
import urllib.request
import urllib.parse

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class SupabaseConfig:
    """Supabase configuration"""
    url: str = "https://mocerqjnksmhcjzxrewo.supabase.co"
    anon_key: str = ""  # Set via environment or direct
    service_key: str = ""  # Set via environment for write access
    
    # Table names
    parcels_table: str = "rough_diamond_parcels"
    scores_table: str = "parcel_scores"
    search_runs_table: str = "search_runs"


class SupabaseClient:
    """
    Lightweight Supabase client using standard library
    For production, consider using supabase-py
    """
    
    def __init__(self, config: SupabaseConfig = None):
        self.config = config or SupabaseConfig()
        
        # Try to get keys from environment
        self.config.anon_key = os.environ.get('SUPABASE_ANON_KEY', self.config.anon_key)
        self.config.service_key = os.environ.get('SUPABASE_SERVICE_KEY', self.config.service_key)
        
        if not self.config.service_key and not self.config.anon_key:
            logger.warning("No Supabase keys configured - database operations will fail")
    
    def _get_headers(self, use_service_key: bool = True) -> Dict[str, str]:
        """Get headers for Supabase API requests"""
        key = self.config.service_key if use_service_key else self.config.anon_key
        return {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }
    
    def _make_request(self, method: str, endpoint: str, data: Any = None) -> Dict:
        """Make HTTP request to Supabase REST API"""
        url = f"{self.config.url}/rest/v1/{endpoint}"
        
        headers = self._get_headers()
        
        if data:
            data_bytes = json.dumps(data).encode('utf-8')
        else:
            data_bytes = None
        
        req = urllib.request.Request(url, data=data_bytes, headers=headers, method=method)
        
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                return json.loads(response.read().decode())
        except urllib.error.HTTPError as e:
            error_body = e.read().decode() if e.fp else str(e)
            logger.error(f"Supabase error {e.code}: {error_body}")
            raise
        except Exception as e:
            logger.error(f"Request failed: {e}")
            raise
    
    def insert_parcel(self, parcel: Dict[str, Any]) -> Dict:
        """Insert a single parcel record"""
        # Map BCPAO fields to database schema
        record = {
            "account": parcel.get('account'),
            "parcel_id": parcel.get('parcelID') or parcel.get('parcel_id'),
            "address": parcel.get('siteAddress') or parcel.get('address'),
            "acres": float(parcel.get('acreage') or parcel.get('acres') or 0),
            "taxing_district": parcel.get('taxingDistrict') or parcel.get('district'),
            "land_use_code": parcel.get('landUseCode') or parcel.get('land_use'),
            "market_value": float(parcel.get('marketValue') or parcel.get('market_value') or 0),
            "owner": parcel.get('owners') or parcel.get('owner'),
            "bcpao_url": parcel.get('bcpao_url') or f"https://www.bcpao.us/PropertySearch/#/account/{parcel.get('account')}",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        return self._make_request("POST", self.config.parcels_table, record)
    
    def insert_parcels_batch(self, parcels: List[Dict]) -> List[Dict]:
        """Insert multiple parcel records"""
        records = []
        for p in parcels:
            records.append({
                "account": p.get('account'),
                "parcel_id": p.get('parcelID') or p.get('parcel_id'),
                "address": p.get('siteAddress') or p.get('address'),
                "acres": float(p.get('acreage') or p.get('acres') or 0),
                "taxing_district": p.get('taxingDistrict') or p.get('district'),
                "land_use_code": p.get('landUseCode') or p.get('land_use'),
                "market_value": float(p.get('marketValue') or p.get('market_value') or 0),
                "owner": p.get('owners') or p.get('owner'),
                "bcpao_url": f"https://www.bcpao.us/PropertySearch/#/account/{p.get('account')}",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            })
        
        return self._make_request("POST", self.config.parcels_table, records)
    
    def insert_score(self, scored_parcel: Dict[str, Any]) -> Dict:
        """Insert a parcel score record"""
        record = {
            "account": scored_parcel.get('account'),
            "score": scored_parcel.get('score'),
            "recommendation": scored_parcel.get('recommendation'),
            "risk_level": scored_parcel.get('risk_level'),
            "timeline": scored_parcel.get('timeline'),
            "action": scored_parcel.get('action'),
            "scoring_factors": json.dumps(scored_parcel.get('scoring_factors', [])),
            "component_scores": json.dumps(scored_parcel.get('component_scores', {})),
            "scored_at": datetime.now().isoformat()
        }
        
        return self._make_request("POST", self.config.scores_table, record)
    
    def insert_scores_batch(self, scored_parcels: List[Dict]) -> List[Dict]:
        """Insert multiple score records"""
        records = []
        for sp in scored_parcels:
            records.append({
                "account": sp.get('account'),
                "score": sp.get('score'),
                "recommendation": sp.get('recommendation'),
                "risk_level": sp.get('risk_level'),
                "timeline": sp.get('timeline'),
                "action": sp.get('action'),
                "scoring_factors": json.dumps(sp.get('scoring_factors', [])),
                "component_scores": json.dumps(sp.get('component_scores', {})),
                "scored_at": datetime.now().isoformat()
            })
        
        return self._make_request("POST", self.config.scores_table, records)
    
    def log_search_run(self, run_data: Dict[str, Any]) -> Dict:
        """Log a search run for tracking"""
        record = {
            "run_type": run_data.get('run_type', 'bcpao_search'),
            "total_found": run_data.get('total_found', 0),
            "bid_count": run_data.get('bid_count', 0),
            "review_count": run_data.get('review_count', 0),
            "parameters": json.dumps(run_data.get('parameters', {})),
            "status": run_data.get('status', 'completed'),
            "run_at": datetime.now().isoformat()
        }
        
        return self._make_request("POST", self.config.search_runs_table, record)
    
    def get_bid_parcels(self, limit: int = 50) -> List[Dict]:
        """Get top BID recommendation parcels"""
        endpoint = f"{self.config.scores_table}?recommendation=like.*BID*&order=score.desc&limit={limit}"
        return self._make_request("GET", endpoint)
    
    def get_parcels_by_district(self, district_pattern: str, limit: int = 100) -> List[Dict]:
        """Get parcels matching a district pattern"""
        endpoint = f"{self.config.parcels_table}?taxing_district=ilike.*{district_pattern}*&limit={limit}"
        return self._make_request("GET", endpoint)
    
    def get_high_value_parcels(self, min_score: int = 75, limit: int = 50) -> List[Dict]:
        """Get parcels with score above threshold"""
        endpoint = f"{self.config.scores_table}?score=gte.{min_score}&order=score.desc&limit={limit}"
        return self._make_request("GET", endpoint)


# SQL for creating tables (run in Supabase SQL editor)
SUPABASE_SCHEMA = """
-- Rough Diamond Parcels table
CREATE TABLE IF NOT EXISTS rough_diamond_parcels (
    id BIGSERIAL PRIMARY KEY,
    account VARCHAR(20) UNIQUE NOT NULL,
    parcel_id VARCHAR(30),
    address TEXT,
    acres DECIMAL(10,2),
    taxing_district VARCHAR(100),
    land_use_code TEXT,
    market_value DECIMAL(15,2),
    owner TEXT,
    bcpao_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for fast lookups
CREATE INDEX IF NOT EXISTS idx_parcels_account ON rough_diamond_parcels(account);
CREATE INDEX IF NOT EXISTS idx_parcels_district ON rough_diamond_parcels(taxing_district);
CREATE INDEX IF NOT EXISTS idx_parcels_acres ON rough_diamond_parcels(acres);

-- Parcel Scores table
CREATE TABLE IF NOT EXISTS parcel_scores (
    id BIGSERIAL PRIMARY KEY,
    account VARCHAR(20) REFERENCES rough_diamond_parcels(account),
    score INTEGER NOT NULL,
    recommendation VARCHAR(20),
    risk_level VARCHAR(20),
    timeline VARCHAR(20),
    action TEXT,
    scoring_factors JSONB,
    component_scores JSONB,
    scored_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for score queries
CREATE INDEX IF NOT EXISTS idx_scores_score ON parcel_scores(score DESC);
CREATE INDEX IF NOT EXISTS idx_scores_rec ON parcel_scores(recommendation);

-- Search Runs tracking table
CREATE TABLE IF NOT EXISTS search_runs (
    id BIGSERIAL PRIMARY KEY,
    run_type VARCHAR(50),
    total_found INTEGER,
    bid_count INTEGER,
    review_count INTEGER,
    parameters JSONB,
    status VARCHAR(20),
    run_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable Row Level Security (optional)
ALTER TABLE rough_diamond_parcels ENABLE ROW LEVEL SECURITY;
ALTER TABLE parcel_scores ENABLE ROW LEVEL SECURITY;
ALTER TABLE search_runs ENABLE ROW LEVEL SECURITY;

-- Policies (adjust as needed)
CREATE POLICY "Allow all for service role" ON rough_diamond_parcels FOR ALL USING (true);
CREATE POLICY "Allow all for service role" ON parcel_scores FOR ALL USING (true);
CREATE POLICY "Allow all for service role" ON search_runs FOR ALL USING (true);
"""


def get_supabase_client() -> SupabaseClient:
    """Factory function to get configured Supabase client"""
    config = SupabaseConfig()
    return SupabaseClient(config)


if __name__ == "__main__":
    # Print schema for manual setup
    print("=" * 60)
    print("SUPABASE SCHEMA - Run this in Supabase SQL Editor")
    print("=" * 60)
    print(SUPABASE_SCHEMA)
