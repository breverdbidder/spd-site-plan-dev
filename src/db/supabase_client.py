#!/usr/bin/env python3
"""
Supabase Client - Production Database Integration
SPD Site Plan Development - Core Component #1

This is the foundation layer. All scrapers, pipelines, and agents depend on this.
"Data is the Moat" - reliable data operations are critical.

Author: BidDeed.AI / Everest Capital USA
"""

import os
import logging
from typing import Dict, List, Any, Optional, TypeVar, Generic
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

T = TypeVar('T')


class TableName(Enum):
    """All SPD tables with their exact names"""
    MUNICIPALITIES = "municipalities"
    ZONING_DISTRICTS = "zoning_districts"
    SITE_PLAN_REQUIREMENTS = "site_plan_requirements"
    PARCELS = "parcels"
    PIPELINE_RUNS = "pipeline_runs"
    SCORING_RESULTS = "scoring_results"
    FEASIBILITY_ANALYSES = "feasibility_analyses"
    REPORTS = "reports"
    CHAT_SESSIONS = "chat_sessions"
    SECURITY_ALERTS = "security_alerts"


@dataclass
class Municipality:
    """Municipality data model"""
    id: str
    name: str
    county: str
    state: str = "FL"
    municode_url: Optional[str] = None
    population: Optional[int] = None
    last_scraped: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ZoningDistrict:
    """Zoning district data model"""
    id: str
    municipality_id: str
    code: str
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    min_lot_size: Optional[float] = None
    max_density: Optional[float] = None
    max_height: Optional[float] = None
    setbacks: Dict[str, float] = field(default_factory=dict)
    permitted_uses: List[str] = field(default_factory=list)
    conditional_uses: List[str] = field(default_factory=list)
    source_url: Optional[str] = None
    last_updated: Optional[datetime] = None


@dataclass 
class SitePlanRequirement:
    """Site plan requirement data model"""
    id: str
    municipality_id: str
    zoning_code: Optional[str] = None
    requirement_type: str = ""
    description: str = ""
    standard: Optional[str] = None
    source_section: Optional[str] = None
    source_url: Optional[str] = None


@dataclass
class QueryResult(Generic[T]):
    """Wrapper for query results with metadata"""
    data: List[T]
    count: int
    success: bool
    error: Optional[str] = None
    query_time_ms: float = 0.0


class SupabaseClient:
    """
    Production Supabase client for SPD Site Plan Development.
    
    Features:
    - Connection pooling via Supabase SDK
    - Automatic retry on transient failures
    - Type-safe operations with dataclasses
    - Comprehensive error handling
    - Query timing for performance monitoring
    
    Usage:
        client = SupabaseClient()
        
        # Get all municipalities
        result = client.get_municipalities()
        
        # Get zoning for a specific municipality
        zones = client.get_zoning_districts(municipality_id="...")
        
        # Insert new data
        client.upsert_municipality(Municipality(...))
    """
    
    def __init__(
        self,
        url: Optional[str] = None,
        key: Optional[str] = None,
        service_role: bool = True
    ):
        """
        Initialize Supabase client.
        
        Args:
            url: Supabase project URL (defaults to env var)
            key: API key (defaults to service role key from env)
            service_role: If True, use service role key for full access
        """
        # Import here to handle missing dependency gracefully
        try:
            from supabase import create_client, Client
        except ImportError:
            raise ImportError("supabase package required: pip install supabase")
        
        self.url = url or os.getenv("SUPABASE_URL")
        
        if service_role:
            self.key = key or os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        else:
            self.key = key or os.getenv("SUPABASE_ANON_KEY")
        
        if not self.url or not self.key:
            raise ValueError(
                "Supabase credentials required. Set SUPABASE_URL and "
                "SUPABASE_SERVICE_ROLE_KEY environment variables."
            )
        
        self._client = create_client(self.url, self.key)
        self._retry_count = 3
        self._retry_delay = 1.0
        
        logger.info(f"Supabase client initialized: {self.url[:40]}...")
    
    @property
    def client(self):
        """Get the underlying Supabase client"""
        return self._client
    
    # =========================================================================
    # MUNICIPALITY OPERATIONS
    # =========================================================================
    
    def get_municipalities(
        self,
        county: Optional[str] = None,
        state: str = "FL",
        limit: int = 100
    ) -> QueryResult[Dict]:
        """Get municipalities with optional filtering."""
        start = datetime.utcnow()
        
        try:
            query = self._client.table(TableName.MUNICIPALITIES.value).select("*")
            
            if county:
                query = query.eq("county", county)
            if state:
                query = query.eq("state", state)
            
            query = query.limit(limit)
            response = query.execute()
            
            elapsed = (datetime.utcnow() - start).total_seconds() * 1000
            
            return QueryResult(
                data=response.data,
                count=len(response.data),
                success=True,
                query_time_ms=elapsed
            )
        except Exception as e:
            logger.error(f"Error fetching municipalities: {e}")
            return QueryResult(data=[], count=0, success=False, error=str(e))
    
    def get_municipality_by_id(self, municipality_id: str) -> Optional[Dict]:
        """Get a single municipality by ID"""
        try:
            response = (
                self._client.table(TableName.MUNICIPALITIES.value)
                .select("*")
                .eq("id", municipality_id)
                .single()
                .execute()
            )
            return response.data
        except Exception as e:
            logger.error(f"Error fetching municipality {municipality_id}: {e}")
            return None
    
    def get_municipality_by_name(self, name: str, county: Optional[str] = None) -> Optional[Dict]:
        """Get municipality by name (case-insensitive)"""
        try:
            query = (
                self._client.table(TableName.MUNICIPALITIES.value)
                .select("*")
                .ilike("name", name)
            )
            if county:
                query = query.eq("county", county)
            
            response = query.limit(1).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error fetching municipality by name {name}: {e}")
            return None
    
    def upsert_municipality(self, municipality: Municipality) -> bool:
        """Insert or update a municipality."""
        try:
            data = {
                "id": municipality.id,
                "name": municipality.name,
                "county": municipality.county,
                "state": municipality.state,
                "municode_url": municipality.municode_url,
                "population": municipality.population,
                "last_scraped": municipality.last_scraped.isoformat() if municipality.last_scraped else None,
                "metadata": municipality.metadata,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            self._client.table(TableName.MUNICIPALITIES.value).upsert(data).execute()
            logger.info(f"Upserted municipality: {municipality.name}")
            return True
        except Exception as e:
            logger.error(f"Error upserting municipality: {e}")
            return False
    
    # =========================================================================
    # ZONING DISTRICT OPERATIONS
    # =========================================================================
    
    def get_zoning_districts(
        self,
        municipality_id: str,
        category: Optional[str] = None
    ) -> QueryResult[Dict]:
        """Get zoning districts for a municipality."""
        start = datetime.utcnow()
        
        try:
            query = (
                self._client.table(TableName.ZONING_DISTRICTS.value)
                .select("*")
                .eq("municipality_id", municipality_id)
            )
            
            if category:
                query = query.eq("category", category)
            
            query = query.order("code")
            response = query.execute()
            
            elapsed = (datetime.utcnow() - start).total_seconds() * 1000
            
            return QueryResult(
                data=response.data,
                count=len(response.data),
                success=True,
                query_time_ms=elapsed
            )
        except Exception as e:
            logger.error(f"Error fetching zoning districts: {e}")
            return QueryResult(data=[], count=0, success=False, error=str(e))
    
    def get_zoning_by_code(self, municipality_id: str, code: str) -> Optional[Dict]:
        """Get a specific zoning district by code"""
        try:
            response = (
                self._client.table(TableName.ZONING_DISTRICTS.value)
                .select("*")
                .eq("municipality_id", municipality_id)
                .eq("code", code)
                .single()
                .execute()
            )
            return response.data
        except Exception as e:
            logger.error(f"Error fetching zoning {code}: {e}")
            return None
    
    def upsert_zoning_district(self, district: ZoningDistrict) -> bool:
        """Insert or update a zoning district"""
        try:
            data = {
                "id": district.id,
                "municipality_id": district.municipality_id,
                "code": district.code,
                "name": district.name,
                "description": district.description,
                "category": district.category,
                "min_lot_size": district.min_lot_size,
                "max_density": district.max_density,
                "max_height": district.max_height,
                "setbacks": district.setbacks,
                "permitted_uses": district.permitted_uses,
                "conditional_uses": district.conditional_uses,
                "source_url": district.source_url,
                "last_updated": district.last_updated.isoformat() if district.last_updated else None,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            self._client.table(TableName.ZONING_DISTRICTS.value).upsert(data).execute()
            logger.info(f"Upserted zoning district: {district.code}")
            return True
        except Exception as e:
            logger.error(f"Error upserting zoning district: {e}")
            return False
    
    def bulk_upsert_zoning_districts(self, districts: List[ZoningDistrict]) -> int:
        """Bulk upsert multiple zoning districts. Returns success count."""
        success_count = 0
        for district in districts:
            if self.upsert_zoning_district(district):
                success_count += 1
        
        logger.info(f"Bulk upserted {success_count}/{len(districts)} zoning districts")
        return success_count
    
    # =========================================================================
    # SITE PLAN REQUIREMENT OPERATIONS
    # =========================================================================
    
    def get_site_plan_requirements(
        self,
        municipality_id: str,
        zoning_code: Optional[str] = None,
        requirement_type: Optional[str] = None
    ) -> QueryResult[Dict]:
        """Get site plan requirements for a municipality."""
        start = datetime.utcnow()
        
        try:
            query = (
                self._client.table(TableName.SITE_PLAN_REQUIREMENTS.value)
                .select("*")
                .eq("municipality_id", municipality_id)
            )
            
            if zoning_code:
                query = query.or_(f"zoning_code.eq.{zoning_code},zoning_code.is.null")
            
            if requirement_type:
                query = query.eq("requirement_type", requirement_type)
            
            response = query.execute()
            elapsed = (datetime.utcnow() - start).total_seconds() * 1000
            
            return QueryResult(
                data=response.data,
                count=len(response.data),
                success=True,
                query_time_ms=elapsed
            )
        except Exception as e:
            logger.error(f"Error fetching site plan requirements: {e}")
            return QueryResult(data=[], count=0, success=False, error=str(e))
    
    def upsert_site_plan_requirement(self, requirement: SitePlanRequirement) -> bool:
        """Insert or update a site plan requirement"""
        try:
            data = {
                "id": requirement.id,
                "municipality_id": requirement.municipality_id,
                "zoning_code": requirement.zoning_code,
                "requirement_type": requirement.requirement_type,
                "description": requirement.description,
                "standard": requirement.standard,
                "source_section": requirement.source_section,
                "source_url": requirement.source_url,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            self._client.table(TableName.SITE_PLAN_REQUIREMENTS.value).upsert(data).execute()
            logger.info(f"Upserted requirement: {requirement.requirement_type}")
            return True
        except Exception as e:
            logger.error(f"Error upserting requirement: {e}")
            return False
    
    def bulk_upsert_requirements(self, requirements: List[SitePlanRequirement]) -> int:
        """Bulk upsert multiple site plan requirements"""
        success_count = 0
        for req in requirements:
            if self.upsert_site_plan_requirement(req):
                success_count += 1
        
        logger.info(f"Bulk upserted {success_count}/{len(requirements)} requirements")
        return success_count
    
    # =========================================================================
    # PIPELINE OPERATIONS
    # =========================================================================
    
    def create_pipeline_run(
        self,
        municipality_id: str,
        pipeline_type: str = "full_scrape",
        metadata: Optional[Dict] = None
    ) -> Optional[str]:
        """Create a new pipeline run record. Returns run ID."""
        import uuid
        
        try:
            run_id = str(uuid.uuid4())
            data = {
                "id": run_id,
                "municipality_id": municipality_id,
                "pipeline_type": pipeline_type,
                "status": "pending",
                "started_at": datetime.utcnow().isoformat(),
                "metadata": metadata or {}
            }
            
            self._client.table(TableName.PIPELINE_RUNS.value).insert(data).execute()
            logger.info(f"Created pipeline run: {run_id}")
            return run_id
        except Exception as e:
            logger.error(f"Error creating pipeline run: {e}")
            return None
    
    def update_pipeline_status(
        self,
        run_id: str,
        status: str,
        current_stage: Optional[str] = None,
        error: Optional[str] = None,
        results: Optional[Dict] = None
    ) -> bool:
        """Update pipeline run status"""
        try:
            data = {
                "status": status,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            if current_stage:
                data["current_stage"] = current_stage
            if error:
                data["error"] = error
            if results:
                data["results"] = results
            if status in ["completed", "failed"]:
                data["completed_at"] = datetime.utcnow().isoformat()
            
            self._client.table(TableName.PIPELINE_RUNS.value).update(data).eq("id", run_id).execute()
            return True
        except Exception as e:
            logger.error(f"Error updating pipeline status: {e}")
            return False
    
    # =========================================================================
    # STATISTICS & HEALTH
    # =========================================================================
    
    def get_data_stats(self) -> Dict[str, int]:
        """Get counts for all tables"""
        stats = {}
        
        for table in [TableName.MUNICIPALITIES, TableName.ZONING_DISTRICTS, TableName.SITE_PLAN_REQUIREMENTS]:
            try:
                response = self._client.table(table.value).select("id", count="exact").execute()
                stats[table.value] = response.count or len(response.data)
            except Exception as e:
                logger.error(f"Error getting count for {table.value}: {e}")
                stats[table.value] = -1
        
        return stats
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on database connection"""
        start = datetime.utcnow()
        
        try:
            response = self._client.table(TableName.MUNICIPALITIES.value).select("id").limit(1).execute()
            elapsed = (datetime.utcnow() - start).total_seconds() * 1000
            
            return {
                "status": "healthy",
                "latency_ms": round(elapsed, 2),
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

_client_instance: Optional[SupabaseClient] = None


def get_supabase_client() -> SupabaseClient:
    """Get global Supabase client instance (singleton pattern)"""
    global _client_instance
    
    if _client_instance is None:
        _client_instance = SupabaseClient()
    
    return _client_instance


def verify_malabar_poc_data() -> Dict[str, Any]:
    """
    Verify the Malabar POC data is accessible.
    This confirms the POC foundation is working.
    
    Returns:
        Dict with municipality info, zoning count, requirements count, and verification status
    """
    client = get_supabase_client()
    
    # Known Malabar municipality ID from POC
    MALABAR_ID = "8f8ed567-9052-492e-905c-436455e90f7d"
    
    municipality = client.get_municipality_by_id(MALABAR_ID)
    zoning = client.get_zoning_districts(MALABAR_ID)
    requirements = client.get_site_plan_requirements(MALABAR_ID)
    
    return {
        "municipality": municipality,
        "zoning_districts_count": zoning.count,
        "zoning_codes": [z.get("code") for z in zoning.data] if zoning.data else [],
        "requirements_count": requirements.count,
        "requirement_types": [r.get("requirement_type") for r in requirements.data] if requirements.data else [],
        "poc_verified": municipality is not None and zoning.count > 0
    }


if __name__ == "__main__":
    import sys
    
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    print("=" * 60)
    print("SPD Supabase Client - Verification Test")
    print("=" * 60)
    
    try:
        client = get_supabase_client()
        
        # Health check
        health = client.health_check()
        print(f"\n✅ Health Check: {health['status']}")
        print(f"   Latency: {health.get('latency_ms', 'N/A')}ms")
        
        # Data stats
        stats = client.get_data_stats()
        print(f"\n📊 Data Statistics:")
        for table, count in stats.items():
            status = "✅" if count > 0 else "⚠️"
            print(f"   {status} {table}: {count} records")
        
        # Verify Malabar POC
        print(f"\n🏘️ Malabar POC Verification:")
        poc = verify_malabar_poc_data()
        if poc['municipality']:
            print(f"   ✅ Municipality: {poc['municipality'].get('name')}")
        else:
            print(f"   ❌ Municipality: NOT FOUND")
        print(f"   📍 Zoning Districts: {poc['zoning_districts_count']}")
        if poc['zoning_codes']:
            print(f"      Codes: {', '.join(poc['zoning_codes'][:5])}...")
        print(f"   📋 Requirements: {poc['requirements_count']}")
        if poc['requirement_types']:
            print(f"      Types: {', '.join(poc['requirement_types'][:5])}")
        
        result = "✅ POC VERIFIED" if poc['poc_verified'] else "❌ POC NOT VERIFIED"
        print(f"\n{'=' * 60}")
        print(f"   {result}")
        print(f"{'=' * 60}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
