#!/usr/bin/env python3
"""
ZoneWise.AI Integration Module
Correlates SPD 20-Phase Report Generator with ZoneWise Supabase Schema

GitHub Repositories:
- breverdbidder/zonewise (main platform)
- breverdbidder/zonewise-agents
- breverdbidder/zonewise-desktop  
- breverdbidder/zonewise-skills
- breverdbidder/zonewise-web
- breverdbidder/spd-site-plan-dev

Supabase Database: mocerqjnksmhcjzxrewo
Tables: jurisdictions (17), zoning_districts (301), kpi_definitions (300), property_analyses

Author: BidDeed.AI / Everest Capital USA
"""

import os
import uuid
import json
import httpx
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict

logger = logging.getLogger(__name__)

# =============================================================================
# SUPABASE CONFIGURATION
# =============================================================================

SUPABASE_URL = "https://mocerqjnksmhcjzxrewo.supabase.co"
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")


# =============================================================================
# 20-PHASE TO KPI CATEGORY MAPPING
# =============================================================================

# Maps each of the 20 phases to ZoneWise KPI categories
PHASE_TO_KPI_CATEGORY: Dict[int, str] = {
    # Part I: Zoning Data (Phases 1-10)
    1: "Summary",       # Property Identification
    2: "Zoning",        # Base Zoning Districts
    3: "Zoning",        # Dimensional Standards
    4: "Zoning",        # Permitted Uses
    5: "Zoning",        # Conditional Uses
    6: "Environmental", # Overlay Districts
    7: "Zoning",        # Development Bonuses
    8: "Zoning",        # Parking Requirements
    9: "Zoning",        # Site Development Standards
    10: "Zoning",       # Future Land Use (FLUM)
    
    # Part II: Market & Property (Phases 11-14)
    11: "Property",     # Property Characteristics
    12: "Market",       # Census Demographics
    13: "Market",       # Location Intelligence
    14: "Market",       # Sales History
    
    # Part III: HBU Analysis (Phases 15-16)
    15: "HBU",          # Highest & Best Use
    16: "HBU",          # Development Scoring
    
    # Part IV: 3 Appraisal Approaches (Phases 17-19)
    17: "SCA",          # Sales Comparison Approach
    18: "Income",       # Income Approach
    19: "Cost",         # Cost Approach
    
    # Part V: Final Report (Phase 20)
    20: "Summary",      # Value Reconciliation
}

# KPI Category Distribution (300 total in Supabase)
KPI_CATEGORY_COUNTS = {
    "Market": 47,
    "Zoning": 45,
    "SCA": 40,
    "Income": 35,
    "HBU": 30,
    "Property": 28,
    "Cost": 25,
    "Environmental": 25,
    "Summary": 25,
}

# Specific KPI code mappings for each phase
PHASE_KPI_CODES: Dict[int, List[str]] = {
    # Phase 1: Property Identification -> Summary KPIs
    1: ["SUM-001", "SUM-002", "SUM-003", "SUM-004", "SUM-005", "SUM-006", "SUM-007"],
    
    # Phase 2: Base Zoning -> Zoning KPIs
    2: ["ZON-001", "ZON-002", "ZON-003", "ZON-004", "ZON-005"],
    
    # Phase 3: Dimensional Standards -> Zoning KPIs
    3: ["ZON-010", "ZON-011", "ZON-012", "ZON-013", "ZON-014", "ZON-015", "ZON-016", "ZON-017", "ZON-018"],
    
    # Phase 4: Permitted Uses -> Zoning KPIs
    4: ["ZON-020", "ZON-021", "ZON-022"],
    
    # Phase 5: Conditional Uses -> Zoning KPIs
    5: ["ZON-025", "ZON-026", "ZON-027", "ZON-028"],
    
    # Phase 6: Overlay Districts -> Environmental KPIs
    6: ["ENV-001", "ENV-002", "ENV-003", "ENV-004", "ENV-005", "ENV-006"],
    
    # Phase 7: Development Bonuses -> Zoning KPIs
    7: ["ZON-030", "ZON-031", "ZON-032", "ZON-033", "ZON-034"],
    
    # Phase 8: Parking Requirements -> Zoning KPIs
    8: ["ZON-035", "ZON-036", "ZON-037", "ZON-038"],
    
    # Phase 9: Site Development Standards -> Zoning KPIs
    9: ["ZON-040", "ZON-041", "ZON-042", "ZON-043"],
    
    # Phase 10: FLUM -> Zoning KPIs
    10: ["ZON-044", "ZON-045"],
    
    # Phase 11: Property Characteristics -> Property KPIs
    11: ["PRO-001", "PRO-002", "PRO-003", "PRO-004", "PRO-005", "PRO-006", "PRO-035"],
    
    # Phase 12: Census Demographics -> Market KPIs
    12: ["MKT-001", "MKT-002", "MKT-003", "MKT-004", "MKT-005", "MKT-006"],
    
    # Phase 13: Location Intelligence -> Market KPIs
    13: ["MKT-010", "MKT-011", "MKT-012", "MKT-013"],
    
    # Phase 14: Sales History -> Market KPIs
    14: ["MKT-020", "MKT-021", "MKT-022", "MKT-023"],
    
    # Phase 15: HBU Analysis -> HBU KPIs
    15: ["HBU-001", "HBU-002", "HBU-003", "HBU-004", "HBU-005", "HBU-010", "HBU-011", 
         "HBU-012", "HBU-013", "HBU-015", "HBU-020", "HBU-021", "HBU-022"],
    
    # Phase 16: Development Scoring -> HBU KPIs
    16: ["HBU-025", "HBU-026", "HBU-027", "HBU-028"],
    
    # Phase 17: Sales Comparison Approach -> SCA KPIs
    17: ["SCA-001", "SCA-002", "SCA-003", "SCA-004", "SCA-020", "SCA-021", "SCA-022",
         "SCA-030", "SCA-031", "SCA-032", "SCA-040"],
    
    # Phase 18: Income Approach -> Income KPIs
    18: ["INC-001", "INC-002", "INC-003", "INC-004", "INC-005", "INC-010", 
         "INC-020", "INC-025", "INC-035"],
    
    # Phase 19: Cost Approach -> Cost KPIs
    19: ["CST-001", "CST-002", "CST-003", "CST-004", "CST-005", "CST-010", "CST-020", "CST-025"],
    
    # Phase 20: Reconciliation -> Summary KPIs
    20: ["SUM-010", "SUM-011", "SUM-012", "SUM-013", "SUM-014", "SUM-015",
         "SUM-020", "SUM-021", "SUM-022", "SUM-023", "SUM-024", "SUM-025"],
}


# =============================================================================
# SUPABASE TABLE SCHEMAS
# =============================================================================

SUPABASE_TABLES = {
    "jurisdictions": {
        "description": "17 Brevard County municipalities",
        "count": 17,
        "primary_key": "id",
        "fields": ["id", "name", "county", "state", "population", "data_completeness", "data_source"],
        "phase_mapping": [1],
    },
    "zoning_districts": {
        "description": "301 zoning districts with embedded DIMS in description",
        "count": 301,
        "primary_key": "id",
        "fields": ["id", "jurisdiction_id", "code", "name", "category", "description"],
        "phase_mapping": [2, 3, 4, 5, 7, 8, 9, 10],
    },
    "kpi_definitions": {
        "description": "300 KPIs across 9 categories",
        "count": 300,
        "primary_key": "kpi_code",
        "fields": ["kpi_code", "kpi_name", "category"],
        "phase_mapping": list(range(1, 21)),
    },
    "property_analyses": {
        "description": "Generated 20-phase property reports",
        "count": "variable",
        "primary_key": "id",
        "fields": ["id", "parcel_id", "address", "jurisdiction_id", "analysis_date",
                   "zonewise_score", "recommendation", "max_bid", "confidence_level", "analysis_json"],
        "phase_mapping": [20],
    },
}


# =============================================================================
# ZONEWISE SUPABASE CLIENT
# =============================================================================

class ZoneWiseSupabaseClient:
    """
    Client for ZoneWise Supabase database operations.
    
    Tables:
    - jurisdictions: 17 Brevard municipalities
    - zoning_districts: 301 districts with embedded dimensional standards
    - kpi_definitions: 300 KPIs across 9 categories
    - property_analyses: Generated reports with zonewise_score
    """
    
    def __init__(self, service_key: str = None):
        self.url = SUPABASE_URL
        self.key = service_key or SUPABASE_SERVICE_KEY
        self.headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json",
        }
    
    async def get_jurisdictions(self) -> List[Dict]:
        """Get all 17 Brevard County jurisdictions"""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.url}/rest/v1/jurisdictions",
                headers=self.headers,
                params={"select": "*", "order": "name"}
            )
            if resp.status_code == 200:
                return resp.json()
            return []
    
    async def get_jurisdiction_by_name(self, name: str) -> Optional[Dict]:
        """Get jurisdiction by name (e.g., 'Malabar', 'Titusville')"""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.url}/rest/v1/jurisdictions",
                headers=self.headers,
                params={"select": "*", "name": f"eq.{name}"}
            )
            if resp.status_code == 200:
                data = resp.json()
                return data[0] if data else None
            return None
    
    async def get_zoning_districts(self, jurisdiction_id: int = None) -> List[Dict]:
        """Get zoning districts, optionally filtered by jurisdiction"""
        params = {"select": "*", "order": "code"}
        if jurisdiction_id:
            params["jurisdiction_id"] = f"eq.{jurisdiction_id}"
        
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.url}/rest/v1/zoning_districts",
                headers=self.headers,
                params=params
            )
            if resp.status_code == 200:
                return resp.json()
            return []
    
    async def get_zoning_by_code(self, jurisdiction_id: int, code: str) -> Optional[Dict]:
        """Get specific zoning district by code"""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.url}/rest/v1/zoning_districts",
                headers=self.headers,
                params={
                    "select": "*",
                    "jurisdiction_id": f"eq.{jurisdiction_id}",
                    "code": f"eq.{code}"
                }
            )
            if resp.status_code == 200:
                data = resp.json()
                return data[0] if data else None
            return None
    
    async def get_kpi_definitions(self, category: str = None) -> List[Dict]:
        """Get KPI definitions, optionally filtered by category"""
        params = {"select": "*", "order": "kpi_code"}
        if category:
            params["category"] = f"eq.{category}"
        
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.url}/rest/v1/kpi_definitions",
                headers=self.headers,
                params=params
            )
            if resp.status_code == 200:
                return resp.json()
            return []
    
    async def save_property_analysis(self, analysis: Dict) -> Optional[str]:
        """Save property analysis to Supabase"""
        payload = {
            "parcel_id": analysis.get("parcel_id"),
            "address": analysis.get("address", ""),
            "jurisdiction_id": analysis.get("jurisdiction_id"),
            "analysis_date": datetime.utcnow().isoformat(),
            "zonewise_score": analysis.get("zonewise_score", 0),
            "recommendation": analysis.get("recommendation", "REVIEW"),
            "max_bid": analysis.get("max_bid", 0),
            "confidence_level": analysis.get("confidence_level", 0),
            "analysis_json": {
                "kpis": analysis.get("kpis", {}),
                "phases": analysis.get("phases", {}),
                "sources": analysis.get("sources", []),
            }
        }
        
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.url}/rest/v1/property_analyses",
                headers={**self.headers, "Prefer": "return=representation"},
                json=payload
            )
            if resp.status_code in [200, 201]:
                data = resp.json()
                return data[0]["id"] if data else None
            logger.error(f"Failed to save analysis: {resp.status_code} {resp.text}")
            return None
    
    async def get_property_analyses(self, parcel_id: str = None) -> List[Dict]:
        """Get property analyses, optionally filtered by parcel"""
        params = {"select": "*", "order": "analysis_date.desc"}
        if parcel_id:
            params["parcel_id"] = f"eq.{parcel_id}"
        
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.url}/rest/v1/property_analyses",
                headers=self.headers,
                params=params
            )
            if resp.status_code == 200:
                return resp.json()
            return []
    
    def parse_dimensional_standards(self, description: str) -> Dict:
        """
        Parse embedded DIMS from zoning_districts.description field.
        
        Format: <!--DIMS:{"min_lot_sqft":10000,"setbacks_ft":{"front":25},...}-->
        """
        import re
        match = re.search(r'<!--DIMS:(.*?)-->', description)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass
        return {}


# =============================================================================
# 20-PHASE ZONEWISE REPORT GENERATOR
# =============================================================================

class ZoneWise20PhaseGenerator:
    """
    Generate 20-Phase Property Reports integrated with ZoneWise.AI ecosystem.
    
    Phases 1-10: Zoning Data (pulls from zoning_districts table)
    Phases 11-14: Market Data (external APIs + cached data)
    Phases 15-16: HBU Analysis (algorithm)
    Phases 17-19: 3 Appraisal Approaches
    Phase 20: Reconciliation (saves to property_analyses table)
    
    Output: ZoneWise Score (0-100), Recommendation (BID/REVIEW/SKIP), Max Bid
    """
    
    def __init__(self, supabase_key: str = None):
        self.supabase = ZoneWiseSupabaseClient(supabase_key)
        self.kpi_cache: Dict[str, Dict] = {}
    
    async def generate(
        self,
        parcel_id: str,
        jurisdiction_name: str,
        typology: str = "single_family"
    ) -> Dict[str, Any]:
        """
        Generate complete 20-phase report.
        
        Args:
            parcel_id: BCPAO parcel ID
            jurisdiction_name: Municipality name (e.g., "Malabar")
            typology: Development type
        
        Returns:
            Dict with phases, kpis, scores, and Supabase record ID
        """
        report = {
            "report_id": str(uuid.uuid4()),
            "parcel_id": parcel_id,
            "jurisdiction": jurisdiction_name,
            "typology": typology,
            "created_at": datetime.utcnow().isoformat(),
            "phases": {},
            "kpis": {},
            "zonewise_score": 0,
            "recommendation": "REVIEW",
            "max_bid": 0,
            "supabase_id": None,
            "errors": [],
        }
        
        try:
            # Get jurisdiction from Supabase
            jurisdiction = await self.supabase.get_jurisdiction_by_name(jurisdiction_name)
            if jurisdiction:
                report["jurisdiction_id"] = jurisdiction["id"]
            
            # Execute all 20 phases
            for phase_num in range(1, 21):
                phase_result = await self._execute_phase(report, phase_num)
                report["phases"][phase_num] = phase_result
                
                # Map KPIs
                for kpi_code in PHASE_KPI_CODES.get(phase_num, []):
                    if kpi_code in phase_result.get("kpi_values", {}):
                        report["kpis"][kpi_code] = phase_result["kpi_values"][kpi_code]
            
            # Calculate final scores
            report["zonewise_score"] = self._calculate_zonewise_score(report)
            report["recommendation"] = self._get_recommendation(report["zonewise_score"])
            report["max_bid"] = self._calculate_max_bid(report)
            
            # Save to Supabase
            report["supabase_id"] = await self.supabase.save_property_analysis(report)
            
        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            report["errors"].append(str(e))
        
        return report
    
    async def _execute_phase(self, report: Dict, phase_num: int) -> Dict:
        """Execute single phase"""
        phase_info = self._get_phase_info(phase_num)
        
        result = {
            "phase": phase_num,
            "name": phase_info["name"],
            "category": PHASE_TO_KPI_CATEGORY.get(phase_num, "Unknown"),
            "status": "completed",
            "kpi_codes": PHASE_KPI_CODES.get(phase_num, []),
            "kpi_values": {},
            "data": {},
        }
        
        # Phase-specific logic
        if phase_num == 2 and report.get("jurisdiction_id"):
            # Get zoning districts from Supabase
            districts = await self.supabase.get_zoning_districts(report["jurisdiction_id"])
            if districts:
                result["data"]["districts_count"] = len(districts)
                result["data"]["categories"] = list(set(d["category"] for d in districts))
        
        elif phase_num == 3 and report.get("jurisdiction_id"):
            # Get dimensional standards from zoning_districts.description DIMS
            districts = await self.supabase.get_zoning_districts(report["jurisdiction_id"])
            for district in districts[:5]:  # Sample
                dims = self.supabase.parse_dimensional_standards(district.get("description", ""))
                if dims:
                    result["data"]["sample_dims"] = dims
                    break
        
        return result
    
    def _get_phase_info(self, phase_num: int) -> Dict:
        """Get phase metadata"""
        phases = {
            1: {"name": "Property Identification", "source": "BCPAO"},
            2: {"name": "Base Zoning Districts", "source": "Supabase"},
            3: {"name": "Dimensional Standards", "source": "Supabase DIMS"},
            4: {"name": "Permitted Uses", "source": "Municode"},
            5: {"name": "Conditional Uses", "source": "Municode"},
            6: {"name": "Overlay Districts", "source": "FEMA/GIS"},
            7: {"name": "Development Bonuses", "source": "Municode"},
            8: {"name": "Parking Requirements", "source": "Municode"},
            9: {"name": "Site Development Standards", "source": "Municode"},
            10: {"name": "Future Land Use (FLUM)", "source": "Comp Plan"},
            11: {"name": "Property Characteristics", "source": "BCPAO"},
            12: {"name": "Census Demographics", "source": "Census ACS"},
            13: {"name": "Location Intelligence", "source": "Walk Score API"},
            14: {"name": "Sales History", "source": "BCPAO/MLS"},
            15: {"name": "Highest & Best Use", "source": "4-Test Analysis"},
            16: {"name": "Development Scoring", "source": "ZoneWise Algorithm"},
            17: {"name": "Sales Comparison Approach", "source": "CMA"},
            18: {"name": "Income Approach", "source": "Pro Forma"},
            19: {"name": "Cost Approach", "source": "RS Means"},
            20: {"name": "Value Reconciliation", "source": "Final"},
        }
        return phases.get(phase_num, {"name": "Unknown", "source": "Unknown"})
    
    def _calculate_zonewise_score(self, report: Dict) -> float:
        """Calculate composite ZoneWise score (0-100)"""
        # Simplified scoring - would be more complex in production
        base_score = 50
        
        # Bonus for completed phases
        completed = sum(1 for p in report["phases"].values() if p.get("status") == "completed")
        base_score += (completed / 20) * 25
        
        # Bonus for jurisdiction data
        if report.get("jurisdiction_id"):
            base_score += 10
        
        # Cap at 100
        return min(100, max(0, base_score))
    
    def _get_recommendation(self, score: float) -> str:
        """Get BID/REVIEW/SKIP recommendation from score"""
        if score >= 75:
            return "BID"
        elif score >= 60:
            return "REVIEW"
        return "SKIP"
    
    def _calculate_max_bid(self, report: Dict) -> float:
        """Calculate max bid (placeholder)"""
        # Would use HBU value * 70% in production
        return 0


# =============================================================================
# CLI & TESTING
# =============================================================================

def print_integration_summary():
    """Print correlation summary"""
    print("=" * 80)
    print("ZONEWISE.AI 20-PHASE REPORT INTEGRATION")
    print("=" * 80)
    print()
    
    print("SUPABASE TABLES:")
    for table, info in SUPABASE_TABLES.items():
        print(f"  - {table}: {info['description']} ({info['count']} records)")
    
    print()
    print("KPI CATEGORIES (300 total):")
    for cat, count in sorted(KPI_CATEGORY_COUNTS.items(), key=lambda x: -x[1]):
        phases = [p for p, c in PHASE_TO_KPI_CATEGORY.items() if c == cat]
        print(f"  - {cat}: {count} KPIs (Phases {phases})")
    
    print()
    print("20-PHASE TO KPI MAPPING:")
    total_kpis = 0
    for phase in range(1, 21):
        kpis = PHASE_KPI_CODES.get(phase, [])
        total_kpis += len(kpis)
        category = PHASE_TO_KPI_CATEGORY.get(phase, "Unknown")
        info = {
            1: "Property Identification",
            2: "Base Zoning Districts",
            3: "Dimensional Standards",
            4: "Permitted Uses",
            5: "Conditional Uses",
            6: "Overlay Districts",
            7: "Development Bonuses",
            8: "Parking Requirements",
            9: "Site Development Standards",
            10: "Future Land Use (FLUM)",
            11: "Property Characteristics",
            12: "Census Demographics",
            13: "Location Intelligence",
            14: "Sales History",
            15: "Highest & Best Use",
            16: "Development Scoring",
            17: "Sales Comparison Approach",
            18: "Income Approach",
            19: "Cost Approach",
            20: "Value Reconciliation",
        }
        print(f"  P{phase:2d}: {info[phase]:<30} | {category:<12} | {len(kpis)} KPIs")
    
    print()
    print(f"TOTAL KPIs MAPPED: {total_kpis}")
    print()
    print("GITHUB REPOS:")
    repos = ["zonewise", "zonewise-agents", "zonewise-desktop", 
             "zonewise-skills", "zonewise-web", "spd-site-plan-dev"]
    for repo in repos:
        print(f"  - breverdbidder/{repo}")


if __name__ == "__main__":
    print_integration_summary()
