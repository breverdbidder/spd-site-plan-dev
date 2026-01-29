#!/usr/bin/env python3
"""
API Routes - FastAPI HTTP Interface
SPD Site Plan Development - Core Component #4

Exposes all SPD functionality via RESTful API endpoints.
Integrates with Core #1 (Supabase), Core #2 (Scraper), Core #3 (Pipeline).

Endpoints:
- /api/chat - NLP chat interface
- /api/feasibility/analyze - Run feasibility analysis
- /api/municipalities - Municipality CRUD
- /api/zoning - Zoning data access
- /api/pipeline - Pipeline execution and status
- /api/scrape - Trigger Municode scraping
- /api/health - Health check

Author: BidDeed.AI / Everest Capital USA
"""

import os
import uuid
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from enum import Enum

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Query, Path, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator

logger = logging.getLogger(__name__)

# =============================================================================
# PYDANTIC MODELS - REQUEST/RESPONSE SCHEMAS
# =============================================================================

class TypologyEnum(str, Enum):
    """Supported development typologies"""
    SINGLE_FAMILY = "single_family"
    MULTI_FAMILY = "multi_family"
    COMMERCIAL = "commercial"
    RETAIL = "retail"
    OFFICE = "office"
    INDUSTRIAL = "industrial"
    MIXED_USE = "mixed_use"
    ASSISTED_LIVING = "assisted_living"


class ChatRequest(BaseModel):
    """Chat request payload"""
    message: str = Field(..., min_length=1, max_length=2000, description="User message")
    session_id: Optional[str] = Field(None, description="Session ID for conversation continuity")
    municipality_id: Optional[str] = Field(None, description="Municipality context")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "What are the zoning requirements for building a duplex in Malabar?",
                "municipality_id": "8f8ed567-9052-492e-905c-436455e90f7d"
            }
        }


class ChatResponse(BaseModel):
    """Chat response payload"""
    response: str
    session_id: str
    sources: List[Dict[str, Any]] = []
    suggested_actions: List[str] = []


class FeasibilityRequest(BaseModel):
    """Feasibility analysis request"""
    municipality_id: str = Field(..., description="Municipality UUID")
    parcel_id: Optional[str] = Field(None, description="Specific parcel to analyze")
    typology: TypologyEnum = Field(TypologyEnum.SINGLE_FAMILY, description="Development type")
    units: int = Field(1, ge=1, le=1000, description="Number of units")
    building_sqft: Optional[int] = Field(None, ge=100, le=1000000, description="Building square footage")
    land_cost: int = Field(100000, ge=0, description="Land acquisition cost")
    
    class Config:
        json_schema_extra = {
            "example": {
                "municipality_id": "8f8ed567-9052-492e-905c-436455e90f7d",
                "typology": "single_family",
                "units": 1,
                "land_cost": 150000
            }
        }


class FeasibilityResponse(BaseModel):
    """Feasibility analysis response"""
    run_id: str
    status: str
    feasible: bool
    roi_pct: float
    total_cost: int
    summary: Dict[str, Any]
    stages_completed: int
    errors: List[str] = []
    warnings: List[str] = []


class MunicipalityCreate(BaseModel):
    """Municipality creation request"""
    name: str = Field(..., min_length=1, max_length=100)
    county: str = Field(..., min_length=1, max_length=100)
    state: str = Field("FL", min_length=2, max_length=2)
    municode_url: Optional[str] = None
    population: Optional[int] = Field(None, ge=0)


class MunicipalityResponse(BaseModel):
    """Municipality response"""
    id: str
    name: str
    county: str
    state: str
    municode_url: Optional[str] = None
    population: Optional[int] = None
    last_scraped: Optional[str] = None
    zoning_districts_count: int = 0
    requirements_count: int = 0


class ZoningDistrictResponse(BaseModel):
    """Zoning district response"""
    id: str
    code: str
    name: str
    category: Optional[str] = None
    description: Optional[str] = None
    min_lot_size: Optional[float] = None
    max_density: Optional[float] = None
    max_height: Optional[float] = None


class SitePlanRequirementResponse(BaseModel):
    """Site plan requirement response"""
    id: str
    requirement_type: str
    description: str
    standard: Optional[str] = None
    zoning_code: Optional[str] = None


class ScrapeRequest(BaseModel):
    """Scrape trigger request"""
    municipality_key: str = Field(..., description="Municipality key (e.g., 'malabar') or URL")
    municipality_id: Optional[str] = Field(None, description="Existing municipality UUID")
    force: bool = Field(False, description="Force re-scrape even if data exists")


class ScrapeResponse(BaseModel):
    """Scrape response"""
    run_id: str
    status: str
    message: str
    zoning_count: int = 0
    requirements_count: int = 0
    duration_seconds: float = 0.0


class PipelineStatusResponse(BaseModel):
    """Pipeline run status response"""
    run_id: str
    status: str
    current_stage: Optional[str] = None
    stages_completed: int
    stages_total: int = 12
    results: Optional[Dict[str, Any]] = None
    errors: List[str] = []
    created_at: str
    updated_at: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    timestamp: str
    database: Dict[str, Any]
    components: Dict[str, str]


class ErrorResponse(BaseModel):
    """Error response"""
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None


# =============================================================================
# DEPENDENCY INJECTION
# =============================================================================

_supabase_client = None
_scraper = None
_orchestrator = None


def get_supabase():
    """Get Supabase client instance"""
    global _supabase_client
    if _supabase_client is None:
        try:
            from src.db.supabase_client import get_supabase_client
            _supabase_client = get_supabase_client()
        except Exception as e:
            logger.error(f"Failed to initialize Supabase: {e}")
            raise HTTPException(status_code=503, detail="Database unavailable")
    return _supabase_client


def get_scraper():
    """Get Municode scraper instance"""
    global _scraper
    if _scraper is None:
        try:
            from src.scrapers.municode_scraper import MunicodeScraper
            _scraper = MunicodeScraper(supabase_client=get_supabase(), headless=True)
        except Exception as e:
            logger.error(f"Failed to initialize scraper: {e}")
            raise HTTPException(status_code=503, detail="Scraper unavailable")
    return _scraper


def get_orchestrator():
    """Get pipeline orchestrator instance"""
    global _orchestrator
    if _orchestrator is None:
        try:
            from src.pipeline.pipeline_orchestrator import SPDPipelineOrchestrator
            _orchestrator = SPDPipelineOrchestrator(
                supabase_client=get_supabase(),
                scraper=get_scraper()
            )
        except Exception as e:
            logger.error(f"Failed to initialize orchestrator: {e}")
            raise HTTPException(status_code=503, detail="Pipeline unavailable")
    return _orchestrator


# =============================================================================
# FASTAPI APPLICATION
# =============================================================================

app = FastAPI(
    title="SPD Site Plan Development API",
    description="""
    Agentic AI platform for site plan development analysis.
    
    ## Features
    - **Chat**: NLP interface for zoning and development queries
    - **Feasibility Analysis**: 12-stage pipeline for property analysis
    - **Zoning Data**: Access to scraped zoning codes and requirements
    - **Municode Scraping**: Automated zoning data extraction
    
    ## Authentication
    API key authentication required for production endpoints.
    """,
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# HEALTH & STATUS ENDPOINTS
# =============================================================================

@app.get("/api/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Health check endpoint.
    
    Returns API status, version, and component health.
    """
    db_health = {"status": "unknown", "latency_ms": 0}
    
    try:
        supabase = get_supabase()
        db_check = supabase.health_check()
        db_health = {
            "status": db_check.get("status", "unknown"),
            "latency_ms": db_check.get("latency_ms", 0)
        }
    except Exception as e:
        db_health = {"status": "unhealthy", "error": str(e)}
    
    return HealthResponse(
        status="healthy" if db_health["status"] == "healthy" else "degraded",
        version="1.0.0",
        timestamp=datetime.utcnow().isoformat(),
        database=db_health,
        components={
            "api": "healthy",
            "database": db_health["status"],
            "scraper": "available",
            "pipeline": "available"
        }
    )


@app.get("/api/stats", tags=["Health"])
async def get_stats():
    """Get data statistics"""
    try:
        supabase = get_supabase()
        stats = supabase.get_data_stats()
        return {
            "status": "success",
            "data": stats,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# CHAT ENDPOINTS
# =============================================================================

@app.post("/api/chat", response_model=ChatResponse, tags=["Chat"])
async def chat(request: ChatRequest):
    """
    NLP chat interface for zoning and development queries.
    
    Supports natural language questions about:
    - Zoning requirements
    - Setbacks and constraints
    - Parking requirements
    - Development feasibility
    """
    session_id = request.session_id or str(uuid.uuid4())
    
    try:
        supabase = get_supabase()
        
        # Simple keyword-based response (can be enhanced with LLM)
        message_lower = request.message.lower()
        response_text = ""
        sources = []
        suggested_actions = []
        
        # Check for municipality context
        if request.municipality_id:
            muni = supabase.get_municipality_by_id(request.municipality_id)
            if muni:
                muni_name = muni.get("name", "Unknown")
                
                # Zoning query
                if any(word in message_lower for word in ["zoning", "zone", "district", "code"]):
                    zoning = supabase.get_zoning_districts(request.municipality_id)
                    if zoning.success and zoning.data:
                        codes = [f"{z['code']}: {z['name']}" for z in zoning.data[:5]]
                        response_text = f"{muni_name} has {len(zoning.data)} zoning districts including: {', '.join(codes)}."
                        if len(zoning.data) > 5:
                            response_text += f" ...and {len(zoning.data) - 5} more."
                        sources = [{"type": "zoning_districts", "count": len(zoning.data)}]
                        suggested_actions = ["View all zoning districts", "Run feasibility analysis"]
                
                # Requirements query
                elif any(word in message_lower for word in ["requirement", "parking", "setback", "landscap"]):
                    reqs = supabase.get_site_plan_requirements(request.municipality_id)
                    if reqs.success and reqs.data:
                        req_types = list(set(r['requirement_type'] for r in reqs.data if r.get('requirement_type')))
                        response_text = f"{muni_name} has {len(reqs.data)} site plan requirements covering: {', '.join(req_types[:5])}."
                        sources = [{"type": "requirements", "count": len(reqs.data)}]
                        suggested_actions = ["View specific requirement", "Run feasibility analysis"]
                
                # Default with context
                else:
                    zoning = supabase.get_zoning_districts(request.municipality_id)
                    reqs = supabase.get_site_plan_requirements(request.municipality_id)
                    response_text = f"I have data for {muni_name}: {zoning.count} zoning districts and {reqs.count} site plan requirements. What would you like to know?"
                    suggested_actions = ["What are the zoning districts?", "What are the parking requirements?", "Run a feasibility analysis"]
            else:
                response_text = "Municipality not found. Would you like me to search for available municipalities?"
                suggested_actions = ["List municipalities", "Scrape a new municipality"]
        else:
            response_text = "Please specify a municipality to get zoning information. You can search by name or provide a municipality ID."
            suggested_actions = ["List municipalities", "Search by name"]
        
        return ChatResponse(
            response=response_text,
            session_id=session_id,
            sources=sources,
            suggested_actions=suggested_actions
        )
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# FEASIBILITY ENDPOINTS
# =============================================================================

@app.post("/api/feasibility/analyze", response_model=FeasibilityResponse, tags=["Feasibility"])
async def analyze_feasibility(
    request: FeasibilityRequest,
    background_tasks: BackgroundTasks
):
    """
    Run full 12-stage feasibility analysis.
    
    Executes the complete SPD pipeline:
    1. Discovery → 2. Survey → 3. Zoning → 4. Constraints →
    5. Parking → 6. Traffic → 7. Utilities → 8. Stormwater →
    9. Layout → 10. Feasibility → 11. Reporting → 12. Archive
    """
    try:
        orchestrator = get_orchestrator()
        
        # Run the pipeline
        state = await orchestrator.run_pipeline(
            municipality_id=request.municipality_id,
            parcel_id=request.parcel_id,
            typology=request.typology.value,
            input_params={
                "units": request.units,
                "building_sqft": request.building_sqft or (request.units * 2000),
                "land_cost": request.land_cost
            }
        )
        
        # Count completed stages
        stages_completed = len([
            s for s in state.get('stage_data', {}).values()
            if s.get('status') == 'completed'
        ])
        
        feasibility = state.get('feasibility_data', {})
        
        return FeasibilityResponse(
            run_id=state['run_id'],
            status=state['stage_status'],
            feasible=feasibility.get('feasible', False),
            roi_pct=feasibility.get('roi_pct', 0),
            total_cost=feasibility.get('total_cost', 0),
            summary={
                "municipality": state.get('municipality_data', {}).get('name', 'Unknown'),
                "typology": request.typology.value,
                "units": request.units,
                "parking_required": state.get('requirements_data', {}).get('parking', {}).get('required_spaces', 0),
                "building_sqft": state.get('layout_data', {}).get('building_footprint_sqft', 0),
                "impact_fees": state.get('requirements_data', {}).get('utilities', {}).get('impact_fees', {}).get('total', 0),
            },
            stages_completed=stages_completed,
            errors=state.get('errors', []),
            warnings=state.get('warnings', [])
        )
        
    except Exception as e:
        logger.error(f"Feasibility analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/feasibility/quick", tags=["Feasibility"])
async def quick_feasibility(
    municipality_id: str = Query(..., description="Municipality UUID"),
    typology: TypologyEnum = Query(TypologyEnum.SINGLE_FAMILY),
    units: int = Query(1, ge=1, le=100),
    land_cost: int = Query(100000, ge=0)
):
    """
    Quick feasibility check (runs to stage 10 only).
    
    Faster than full analysis - skips reporting and archiving.
    """
    try:
        orchestrator = get_orchestrator()
        from src.pipeline.pipeline_orchestrator import PipelineStage
        
        state = await orchestrator.run_pipeline(
            municipality_id=municipality_id,
            typology=typology.value,
            input_params={"units": units, "land_cost": land_cost},
            stop_at=PipelineStage.FEASIBILITY
        )
        
        feasibility = state.get('feasibility_data', {})
        
        return {
            "feasible": feasibility.get('feasible', False),
            "roi_pct": feasibility.get('roi_pct', 0),
            "total_cost": feasibility.get('total_cost', 0),
            "construction_cost": feasibility.get('construction_cost', 0),
            "impact_fees": feasibility.get('impact_fees', 0),
            "errors": state.get('errors', [])
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# MUNICIPALITY ENDPOINTS
# =============================================================================

@app.get("/api/municipalities", response_model=List[MunicipalityResponse], tags=["Municipalities"])
async def list_municipalities(
    county: Optional[str] = Query(None, description="Filter by county"),
    state: str = Query("FL", description="Filter by state"),
    limit: int = Query(50, ge=1, le=100)
):
    """List all municipalities with optional filtering"""
    try:
        supabase = get_supabase()
        result = supabase.get_municipalities(county=county, state=state, limit=limit)
        
        if not result.success:
            raise HTTPException(status_code=500, detail=result.error)
        
        municipalities = []
        for muni in result.data:
            # Get counts
            zoning = supabase.get_zoning_districts(muni['id'])
            reqs = supabase.get_site_plan_requirements(muni['id'])
            
            municipalities.append(MunicipalityResponse(
                id=muni['id'],
                name=muni['name'],
                county=muni['county'],
                state=muni['state'],
                municode_url=muni.get('municode_url'),
                population=muni.get('population'),
                last_scraped=muni.get('last_scraped'),
                zoning_districts_count=zoning.count,
                requirements_count=reqs.count
            ))
        
        return municipalities
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/municipalities/{municipality_id}", response_model=MunicipalityResponse, tags=["Municipalities"])
async def get_municipality(municipality_id: str = Path(..., description="Municipality UUID")):
    """Get a specific municipality by ID"""
    try:
        supabase = get_supabase()
        muni = supabase.get_municipality_by_id(municipality_id)
        
        if not muni:
            raise HTTPException(status_code=404, detail="Municipality not found")
        
        zoning = supabase.get_zoning_districts(municipality_id)
        reqs = supabase.get_site_plan_requirements(municipality_id)
        
        return MunicipalityResponse(
            id=muni['id'],
            name=muni['name'],
            county=muni['county'],
            state=muni['state'],
            municode_url=muni.get('municode_url'),
            population=muni.get('population'),
            last_scraped=muni.get('last_scraped'),
            zoning_districts_count=zoning.count,
            requirements_count=reqs.count
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/municipalities", response_model=MunicipalityResponse, tags=["Municipalities"])
async def create_municipality(request: MunicipalityCreate):
    """Create a new municipality"""
    try:
        supabase = get_supabase()
        from src.db.supabase_client import Municipality
        
        municipality = Municipality(
            id=str(uuid.uuid4()),
            name=request.name,
            county=request.county,
            state=request.state,
            municode_url=request.municode_url,
            population=request.population
        )
        
        if not supabase.upsert_municipality(municipality):
            raise HTTPException(status_code=500, detail="Failed to create municipality")
        
        return MunicipalityResponse(
            id=municipality.id,
            name=municipality.name,
            county=municipality.county,
            state=municipality.state,
            municode_url=municipality.municode_url,
            population=municipality.population,
            zoning_districts_count=0,
            requirements_count=0
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# ZONING ENDPOINTS
# =============================================================================

@app.get("/api/municipalities/{municipality_id}/zoning", response_model=List[ZoningDistrictResponse], tags=["Zoning"])
async def get_zoning_districts(
    municipality_id: str = Path(..., description="Municipality UUID"),
    category: Optional[str] = Query(None, description="Filter by category")
):
    """Get zoning districts for a municipality"""
    try:
        supabase = get_supabase()
        result = supabase.get_zoning_districts(municipality_id, category=category)
        
        if not result.success:
            raise HTTPException(status_code=500, detail=result.error)
        
        return [
            ZoningDistrictResponse(
                id=z['id'],
                code=z['code'],
                name=z['name'],
                category=z.get('category'),
                description=z.get('description'),
                min_lot_size=z.get('min_lot_size'),
                max_density=z.get('max_density'),
                max_height=z.get('max_height')
            )
            for z in result.data
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/municipalities/{municipality_id}/requirements", response_model=List[SitePlanRequirementResponse], tags=["Zoning"])
async def get_site_plan_requirements(
    municipality_id: str = Path(..., description="Municipality UUID"),
    requirement_type: Optional[str] = Query(None, description="Filter by type")
):
    """Get site plan requirements for a municipality"""
    try:
        supabase = get_supabase()
        result = supabase.get_site_plan_requirements(
            municipality_id,
            requirement_type=requirement_type
        )
        
        if not result.success:
            raise HTTPException(status_code=500, detail=result.error)
        
        return [
            SitePlanRequirementResponse(
                id=r['id'],
                requirement_type=r.get('requirement_type', 'unknown'),
                description=r.get('description', ''),
                standard=r.get('standard'),
                zoning_code=r.get('zoning_code')
            )
            for r in result.data
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# SCRAPE ENDPOINTS
# =============================================================================

@app.post("/api/scrape", response_model=ScrapeResponse, tags=["Scraping"])
async def trigger_scrape(
    request: ScrapeRequest,
    background_tasks: BackgroundTasks
):
    """
    Trigger Municode scraping for a municipality.
    
    Extracts zoning districts and site plan requirements.
    """
    run_id = str(uuid.uuid4())
    
    try:
        scraper = get_scraper()
        
        # Check if data exists and force is not set
        if not request.force and request.municipality_id:
            supabase = get_supabase()
            zoning = supabase.get_zoning_districts(request.municipality_id)
            if zoning.count > 0:
                return ScrapeResponse(
                    run_id=run_id,
                    status="skipped",
                    message=f"Data already exists ({zoning.count} districts). Use force=true to re-scrape.",
                    zoning_count=zoning.count
                )
        
        # Run scrape
        if request.municipality_id:
            result, pipeline_run_id = await scraper.scrape_and_store(
                request.municipality_key,
                request.municipality_id
            )
            run_id = pipeline_run_id or run_id
        else:
            result = await scraper.scrape_municipality(request.municipality_key)
        
        return ScrapeResponse(
            run_id=run_id,
            status=result.status.value,
            message=f"Scraped {result.municipality_name}",
            zoning_count=len(result.zoning_districts),
            requirements_count=len(result.requirements),
            duration_seconds=result.duration_seconds
        )
        
    except Exception as e:
        logger.error(f"Scrape error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/scrape/available", tags=["Scraping"])
async def list_available_municipalities():
    """List municipalities available for scraping"""
    try:
        from src.scrapers.municode_scraper import get_available_municipalities
        municipalities = get_available_municipalities()
        
        return {
            "status": "success",
            "count": len(municipalities),
            "municipalities": [
                {
                    "key": key,
                    "name": info["name"],
                    "county": info["county"],
                    "url": info["url"]
                }
                for key, info in municipalities.items()
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# PIPELINE ENDPOINTS
# =============================================================================

@app.get("/api/pipeline/{run_id}", response_model=PipelineStatusResponse, tags=["Pipeline"])
async def get_pipeline_status(run_id: str = Path(..., description="Pipeline run ID")):
    """Get status of a pipeline run"""
    try:
        supabase = get_supabase()
        
        # Query pipeline_runs table
        response = supabase.client.table("pipeline_runs").select("*").eq("id", run_id).single().execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Pipeline run not found")
        
        run = response.data
        results = run.get('results', {}) or {}
        
        return PipelineStatusResponse(
            run_id=run['id'],
            status=run.get('status', 'unknown'),
            current_stage=run.get('current_stage'),
            stages_completed=results.get('stages_completed', 0),
            stages_total=12,
            results=results,
            errors=run.get('errors', []) or [],
            created_at=run.get('started_at', ''),
            updated_at=run.get('updated_at')
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/pipeline/stages", tags=["Pipeline"])
async def list_pipeline_stages():
    """List all pipeline stages with info"""
    try:
        from src.pipeline.pipeline_orchestrator import get_pipeline_stages
        stages = get_pipeline_stages()
        
        return {
            "status": "success",
            "total_stages": len(stages),
            "stages": stages
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# POC ENDPOINTS
# =============================================================================

@app.get("/api/poc/malabar", tags=["POC"])
async def verify_malabar_poc():
    """Verify Malabar POC data is accessible"""
    try:
        supabase = get_supabase()
        from src.db.supabase_client import verify_malabar_poc_data
        
        poc_data = verify_malabar_poc_data()
        
        return {
            "status": "success",
            "poc_verified": poc_data['poc_verified'],
            "municipality": poc_data['municipality'].get('name') if poc_data['municipality'] else None,
            "municipality_id": "8f8ed567-9052-492e-905c-436455e90f7d",
            "zoning_districts": poc_data['zoning_districts_count'],
            "zoning_codes": poc_data['zoning_codes'],
            "requirements": poc_data['requirements_count'],
            "requirement_types": poc_data['requirement_types']
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/poc/malabar/feasibility", response_model=FeasibilityResponse, tags=["POC"])
async def run_malabar_poc_feasibility():
    """Run feasibility analysis on Malabar POC"""
    try:
        orchestrator = get_orchestrator()
        
        state = await orchestrator.run_malabar_poc()
        
        stages_completed = len([
            s for s in state.get('stage_data', {}).values()
            if s.get('status') == 'completed'
        ])
        
        feasibility = state.get('feasibility_data', {})
        
        return FeasibilityResponse(
            run_id=state['run_id'],
            status=state['stage_status'],
            feasible=feasibility.get('feasible', False),
            roi_pct=feasibility.get('roi_pct', 0),
            total_cost=feasibility.get('total_cost', 0),
            summary={
                "municipality": "Malabar",
                "typology": "single_family",
                "units": 1
            },
            stages_completed=stages_completed,
            errors=state.get('errors', []),
            warnings=state.get('warnings', [])
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# ERROR HANDLERS
# =============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "code": f"HTTP_{exc.status_code}"}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)}
    )


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("=" * 60)
    print("SPD API Server")
    print("=" * 60)
    print("\nEndpoints:")
    print("  - Health:       GET  /api/health")
    print("  - Chat:         POST /api/chat")
    print("  - Feasibility:  POST /api/feasibility/analyze")
    print("  - Municipalities: GET /api/municipalities")
    print("  - Zoning:       GET  /api/municipalities/{id}/zoning")
    print("  - Scrape:       POST /api/scrape")
    print("  - Pipeline:     GET  /api/pipeline/{run_id}")
    print("  - POC:          GET  /api/poc/malabar")
    print("\nDocs: http://localhost:8000/api/docs")
    print("=" * 60)
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
