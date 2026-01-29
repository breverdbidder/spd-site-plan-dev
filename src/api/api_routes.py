#!/usr/bin/env python3
"""
API Routes - FastAPI REST Endpoints
SPD Site Plan Development - Core Component #4

Exposes all pipeline functionality via REST API.
Integrates with Core #1 (Supabase), Core #2 (Scraper), Core #3 (Pipeline).

Endpoints:
- /api/health          - Health check
- /api/chat            - AI chat interface
- /api/municipalities  - Municipality CRUD
- /api/zoning          - Zoning data access
- /api/feasibility     - Feasibility analysis
- /api/pipeline        - Pipeline execution
- /api/scrape          - Trigger Municode scraping

Author: BidDeed.AI / Everest Capital USA
"""

import os
import uuid
import asyncio
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from enum import Enum

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Query, Path, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator

logger = logging.getLogger(__name__)

# =============================================================================
# PYDANTIC MODELS - Request/Response Schemas
# =============================================================================

class HealthResponse(BaseModel):
    """Health check response"""
    status: str = "healthy"
    version: str = "1.0.0"
    timestamp: str
    database: str = "connected"
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "timestamp": "2026-01-29T03:00:00Z",
                "database": "connected"
            }
        }


class Typology(str, Enum):
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
    """Chat request model"""
    message: str = Field(..., min_length=1, max_length=4000, description="User message")
    session_id: Optional[str] = Field(None, description="Session ID for conversation continuity")
    municipality_id: Optional[str] = Field(None, description="Municipality context")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional context")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "What are the zoning requirements for Malabar?",
                "session_id": "abc123",
                "municipality_id": "8f8ed567-9052-492e-905c-436455e90f7d"
            }
        }


class ChatResponse(BaseModel):
    """Chat response model"""
    response: str
    session_id: str
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)
    timestamp: str


class MunicipalityCreate(BaseModel):
    """Create municipality request"""
    name: str = Field(..., min_length=2, max_length=100)
    county: str = Field(..., min_length=2, max_length=100)
    state: str = Field(default="FL", min_length=2, max_length=2)
    municode_url: Optional[str] = None
    population: Optional[int] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Malabar",
                "county": "Brevard",
                "state": "FL",
                "municode_url": "https://library.municode.com/fl/malabar"
            }
        }


class MunicipalityResponse(BaseModel):
    """Municipality response model"""
    id: str
    name: str
    county: str
    state: str
    municode_url: Optional[str]
    population: Optional[int]
    last_scraped: Optional[str]
    zoning_count: int = 0
    requirements_count: int = 0


class ZoningDistrictResponse(BaseModel):
    """Zoning district response"""
    id: str
    code: str
    name: str
    description: Optional[str]
    category: Optional[str]
    source_url: Optional[str]


class SitePlanRequirementResponse(BaseModel):
    """Site plan requirement response"""
    id: str
    requirement_type: str
    description: str
    standard: Optional[str]
    zoning_code: Optional[str]
    source_url: Optional[str]


class FeasibilityRequest(BaseModel):
    """Feasibility analysis request"""
    municipality_id: str = Field(..., description="Municipality UUID")
    parcel_id: Optional[str] = Field(None, description="Specific parcel to analyze")
    typology: Typology = Field(default=Typology.SINGLE_FAMILY)
    units: int = Field(default=1, ge=1, le=1000, description="Number of units")
    land_cost: float = Field(default=100000, ge=0, description="Land acquisition cost")
    building_sqft: Optional[float] = Field(None, ge=0, description="Target building square footage")
    
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
    municipality_name: str
    typology: str
    feasible: bool
    roi_pct: float
    total_cost: float
    revenue: float
    profit: float
    
    # Detailed breakdown
    land_cost: float
    construction_cost: float
    soft_costs: float
    impact_fees: float
    
    # Requirements summary
    parking_required: int
    building_sqft: float
    
    # Metadata
    stages_completed: int
    duration_seconds: float
    timestamp: str
    errors: List[str] = Field(default_factory=list)


class PipelineRequest(BaseModel):
    """Full pipeline execution request"""
    municipality_id: str
    parcel_id: Optional[str] = None
    typology: Typology = Typology.SINGLE_FAMILY
    input_params: Dict[str, Any] = Field(default_factory=dict)
    start_from: Optional[str] = Field(None, description="Stage to start from (for resume)")
    stop_at: Optional[str] = Field(None, description="Stage to stop at (for partial runs)")


class PipelineStatusResponse(BaseModel):
    """Pipeline status response"""
    run_id: str
    status: str
    current_stage: Optional[str]
    stages_completed: int
    total_stages: int = 12
    progress_pct: float
    started_at: str
    updated_at: str
    errors: List[str] = Field(default_factory=list)


class ScrapeRequest(BaseModel):
    """Municode scrape request"""
    municipality_key: str = Field(..., description="Municipality key or custom URL")
    municipality_id: Optional[str] = Field(None, description="Existing municipality UUID")
    force_refresh: bool = Field(default=False, description="Force re-scrape even if cached")
    
    class Config:
        json_schema_extra = {
            "example": {
                "municipality_key": "malabar",
                "force_refresh": False
            }
        }


class ScrapeResponse(BaseModel):
    """Scrape response"""
    municipality_id: str
    municipality_name: str
    status: str
    zoning_count: int
    requirements_count: int
    pages_scraped: int
    duration_seconds: float
    errors: List[str] = Field(default_factory=list)


class ErrorResponse(BaseModel):
    """Error response model"""
    error: str
    detail: Optional[str] = None
    code: str = "UNKNOWN_ERROR"
    timestamp: str


# =============================================================================
# DEPENDENCY INJECTION
# =============================================================================

class ServiceContainer:
    """Dependency injection container for services"""
    
    _supabase = None
    _scraper = None
    _orchestrator = None
    
    @classmethod
    def get_supabase(cls):
        """Get or create Supabase client"""
        if cls._supabase is None:
            try:
                from src.db.supabase_client import get_supabase_client
                cls._supabase = get_supabase_client()
            except Exception as e:
                logger.error(f"Failed to initialize Supabase: {e}")
                raise HTTPException(status_code=503, detail="Database unavailable")
        return cls._supabase
    
    @classmethod
    def get_scraper(cls):
        """Get or create Municode scraper"""
        if cls._scraper is None:
            try:
                from src.scrapers.municode_scraper import MunicodeScraper
                cls._scraper = MunicodeScraper(
                    supabase_client=cls.get_supabase(),
                    headless=True
                )
            except Exception as e:
                logger.error(f"Failed to initialize scraper: {e}")
                raise HTTPException(status_code=503, detail="Scraper unavailable")
        return cls._scraper
    
    @classmethod
    def get_orchestrator(cls):
        """Get or create pipeline orchestrator"""
        if cls._orchestrator is None:
            try:
                from src.pipeline.pipeline_orchestrator import SPDPipelineOrchestrator
                cls._orchestrator = SPDPipelineOrchestrator(
                    supabase_client=cls.get_supabase(),
                    scraper=cls.get_scraper()
                )
            except Exception as e:
                logger.error(f"Failed to initialize orchestrator: {e}")
                raise HTTPException(status_code=503, detail="Pipeline unavailable")
        return cls._orchestrator


def get_supabase():
    """Dependency for Supabase client"""
    return ServiceContainer.get_supabase()


def get_scraper():
    """Dependency for scraper"""
    return ServiceContainer.get_scraper()


def get_orchestrator():
    """Dependency for pipeline orchestrator"""
    return ServiceContainer.get_orchestrator()


# =============================================================================
# FASTAPI APPLICATION
# =============================================================================

app = FastAPI(
    title="SPD Site Plan Development API",
    description="""
    API for the Site Plan Development (SPD) agentic AI platform.
    
    ## Features
    - **Chat**: AI-powered natural language interface
    - **Municipalities**: Manage Florida municipality data
    - **Zoning**: Access zoning districts and requirements
    - **Feasibility**: Run financial feasibility analysis
    - **Pipeline**: Execute full 12-stage analysis pipeline
    - **Scrape**: Trigger Municode data extraction
    
    ## Authentication
    Bearer token authentication (coming soon)
    
    ## Rate Limits
    - Free: 10 requests/minute
    - Pro: 60 requests/minute  
    - Enterprise: 300 requests/minute
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# HEALTH ENDPOINTS
# =============================================================================

@app.get("/api/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Health check endpoint.
    
    Returns system status and database connectivity.
    """
    db_status = "disconnected"
    
    try:
        supabase = ServiceContainer.get_supabase()
        health = supabase.health_check()
        db_status = health.get("status", "unknown")
    except Exception:
        db_status = "error"
    
    return HealthResponse(
        status="healthy" if db_status == "healthy" else "degraded",
        version="1.0.0",
        timestamp=datetime.utcnow().isoformat(),
        database=db_status
    )


@app.get("/api/stats", tags=["Health"])
async def get_stats():
    """Get database statistics"""
    try:
        supabase = ServiceContainer.get_supabase()
        stats = supabase.get_data_stats()
        return {
            "status": "success",
            "stats": stats,
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
    AI chat interface for natural language queries.
    
    Supports questions about:
    - Zoning requirements
    - Site plan standards
    - Feasibility analysis
    - Development recommendations
    """
    session_id = request.session_id or str(uuid.uuid4())
    
    try:
        # Get context from Supabase if municipality provided
        context_data = {}
        suggestions = []
        sources = []
        
        if request.municipality_id:
            supabase = ServiceContainer.get_supabase()
            
            # Get municipality info
            muni = supabase.get_municipality_by_id(request.municipality_id)
            if muni:
                context_data["municipality"] = muni
                sources.append({
                    "type": "municipality",
                    "name": muni.get("name"),
                    "id": muni.get("id")
                })
            
            # Get zoning data
            zoning = supabase.get_zoning_districts(request.municipality_id)
            if zoning.success and zoning.data:
                context_data["zoning_districts"] = zoning.data[:10]  # First 10
                sources.append({
                    "type": "zoning",
                    "count": zoning.count
                })
            
            # Get requirements
            reqs = supabase.get_site_plan_requirements(request.municipality_id)
            if reqs.success and reqs.data:
                context_data["requirements"] = reqs.data[:10]
                sources.append({
                    "type": "requirements",
                    "count": reqs.count
                })
        
        # Generate response (simplified - would integrate with LLM)
        response_text = _generate_chat_response(request.message, context_data)
        
        # Generate suggestions
        suggestions = _generate_suggestions(request.message, context_data)
        
        return ChatResponse(
            response=response_text,
            session_id=session_id,
            sources=sources,
            suggestions=suggestions,
            timestamp=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _generate_chat_response(message: str, context: Dict) -> str:
    """Generate chat response based on context (placeholder for LLM integration)"""
    message_lower = message.lower()
    
    # Check for zoning questions
    if "zoning" in message_lower:
        if context.get("zoning_districts"):
            zones = context["zoning_districts"]
            zone_list = ", ".join([z.get("code", "?") for z in zones[:5]])
            return f"Based on the municipality data, I found {len(zones)} zoning districts including: {zone_list}. Would you like details on any specific zone?"
    
    # Check for requirement questions
    if any(word in message_lower for word in ["parking", "setback", "requirement", "standard"]):
        if context.get("requirements"):
            reqs = context["requirements"]
            types = list(set([r.get("requirement_type", "unknown") for r in reqs]))
            return f"I found {len(reqs)} site plan requirements covering: {', '.join(types)}. Which requirement would you like to know more about?"
    
    # Check for feasibility questions
    if any(word in message_lower for word in ["feasibility", "roi", "cost", "profit"]):
        return "I can run a feasibility analysis for you. Please provide the property details or use the /api/feasibility endpoint with your parameters."
    
    # Default response
    muni_name = context.get("municipality", {}).get("name", "your selected municipality")
    return f"I'm ready to help with site plan development questions for {muni_name}. You can ask about zoning, requirements, or run a feasibility analysis."


def _generate_suggestions(message: str, context: Dict) -> List[str]:
    """Generate follow-up suggestions"""
    suggestions = []
    
    if context.get("zoning_districts"):
        suggestions.append("Show me all residential zones")
        suggestions.append("What are the setback requirements?")
    
    if context.get("requirements"):
        suggestions.append("What are the parking requirements?")
        suggestions.append("Tell me about landscaping requirements")
    
    suggestions.append("Run a feasibility analysis")
    
    return suggestions[:4]  # Limit to 4 suggestions


# =============================================================================
# MUNICIPALITY ENDPOINTS
# =============================================================================

@app.get("/api/municipalities", tags=["Municipalities"])
async def list_municipalities(
    county: Optional[str] = Query(None, description="Filter by county"),
    state: str = Query("FL", description="Filter by state"),
    limit: int = Query(100, ge=1, le=500)
):
    """List all municipalities with optional filtering"""
    try:
        supabase = ServiceContainer.get_supabase()
        result = supabase.get_municipalities(county=county, state=state, limit=limit)
        
        if not result.success:
            raise HTTPException(status_code=500, detail=result.error)
        
        return {
            "municipalities": result.data,
            "count": result.count,
            "query_time_ms": result.query_time_ms
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/municipalities/{municipality_id}", response_model=MunicipalityResponse, tags=["Municipalities"])
async def get_municipality(municipality_id: str = Path(..., description="Municipality UUID")):
    """Get a specific municipality with zoning stats"""
    try:
        supabase = ServiceContainer.get_supabase()
        
        muni = supabase.get_municipality_by_id(municipality_id)
        if not muni:
            raise HTTPException(status_code=404, detail="Municipality not found")
        
        # Get counts
        zoning = supabase.get_zoning_districts(municipality_id)
        reqs = supabase.get_site_plan_requirements(municipality_id)
        
        return MunicipalityResponse(
            id=muni["id"],
            name=muni["name"],
            county=muni["county"],
            state=muni.get("state", "FL"),
            municode_url=muni.get("municode_url"),
            population=muni.get("population"),
            last_scraped=muni.get("last_scraped"),
            zoning_count=zoning.count if zoning.success else 0,
            requirements_count=reqs.count if reqs.success else 0
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/municipalities", response_model=MunicipalityResponse, tags=["Municipalities"])
async def create_municipality(request: MunicipalityCreate):
    """Create a new municipality"""
    try:
        supabase = ServiceContainer.get_supabase()
        
        # Check if exists
        existing = supabase.get_municipality_by_name(request.name, request.county)
        if existing:
            raise HTTPException(status_code=409, detail="Municipality already exists")
        
        # Create
        from src.db.supabase_client import Municipality
        
        muni = Municipality(
            id=str(uuid.uuid4()),
            name=request.name,
            county=request.county,
            state=request.state,
            municode_url=request.municode_url,
            population=request.population
        )
        
        if not supabase.upsert_municipality(muni):
            raise HTTPException(status_code=500, detail="Failed to create municipality")
        
        return MunicipalityResponse(
            id=muni.id,
            name=muni.name,
            county=muni.county,
            state=muni.state,
            municode_url=muni.municode_url,
            population=muni.population,
            last_scraped=None,
            zoning_count=0,
            requirements_count=0
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# ZONING ENDPOINTS
# =============================================================================

@app.get("/api/municipalities/{municipality_id}/zoning", tags=["Zoning"])
async def get_zoning_districts(
    municipality_id: str = Path(..., description="Municipality UUID"),
    category: Optional[str] = Query(None, description="Filter by category (residential, commercial, etc.)")
):
    """Get zoning districts for a municipality"""
    try:
        supabase = ServiceContainer.get_supabase()
        result = supabase.get_zoning_districts(municipality_id, category=category)
        
        if not result.success:
            raise HTTPException(status_code=500, detail=result.error)
        
        return {
            "zoning_districts": result.data,
            "count": result.count,
            "query_time_ms": result.query_time_ms
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/municipalities/{municipality_id}/zoning/{code}", tags=["Zoning"])
async def get_zoning_by_code(
    municipality_id: str = Path(...),
    code: str = Path(..., description="Zoning code (e.g., RS-1, C-1)")
):
    """Get a specific zoning district by code"""
    try:
        supabase = ServiceContainer.get_supabase()
        zone = supabase.get_zoning_by_code(municipality_id, code)
        
        if not zone:
            raise HTTPException(status_code=404, detail=f"Zoning code {code} not found")
        
        return zone
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/municipalities/{municipality_id}/requirements", tags=["Zoning"])
async def get_site_plan_requirements(
    municipality_id: str = Path(...),
    zoning_code: Optional[str] = Query(None, description="Filter by zoning code"),
    requirement_type: Optional[str] = Query(None, description="Filter by type (parking, setback, etc.)")
):
    """Get site plan requirements for a municipality"""
    try:
        supabase = ServiceContainer.get_supabase()
        result = supabase.get_site_plan_requirements(
            municipality_id,
            zoning_code=zoning_code,
            requirement_type=requirement_type
        )
        
        if not result.success:
            raise HTTPException(status_code=500, detail=result.error)
        
        return {
            "requirements": result.data,
            "count": result.count,
            "query_time_ms": result.query_time_ms
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# FEASIBILITY ENDPOINTS
# =============================================================================

@app.post("/api/feasibility", response_model=FeasibilityResponse, tags=["Feasibility"])
async def run_feasibility_analysis(request: FeasibilityRequest):
    """
    Run a feasibility analysis for a development project.
    
    Executes the full 12-stage pipeline and returns financial metrics.
    """
    try:
        orchestrator = ServiceContainer.get_orchestrator()
        supabase = ServiceContainer.get_supabase()
        
        # Get municipality name
        muni = supabase.get_municipality_by_id(request.municipality_id)
        muni_name = muni.get("name", "Unknown") if muni else "Unknown"
        
        # Build input params
        input_params = {
            "units": request.units,
            "land_cost": request.land_cost,
        }
        if request.building_sqft:
            input_params["building_sqft"] = request.building_sqft
        
        # Run pipeline
        start_time = datetime.utcnow()
        
        state = await orchestrator.run_pipeline(
            municipality_id=request.municipality_id,
            parcel_id=request.parcel_id,
            typology=request.typology.value,
            input_params=input_params
        )
        
        duration = (datetime.utcnow() - start_time).total_seconds()
        
        # Extract results
        feasibility = state.get("feasibility_data", {})
        requirements = state.get("requirements_data", {})
        layout = state.get("layout_data", {})
        
        stages_completed = len([
            s for s in state.get("stage_data", {}).values()
            if s.get("status") == "completed"
        ])
        
        return FeasibilityResponse(
            run_id=state.get("run_id", str(uuid.uuid4())),
            municipality_name=muni_name,
            typology=request.typology.value,
            feasible=feasibility.get("feasible", False),
            roi_pct=feasibility.get("roi_pct", 0),
            total_cost=feasibility.get("total_cost", 0),
            revenue=feasibility.get("revenue", 0),
            profit=feasibility.get("profit", 0),
            land_cost=feasibility.get("land_cost", request.land_cost),
            construction_cost=feasibility.get("construction_cost", 0),
            soft_costs=feasibility.get("soft_costs", 0),
            impact_fees=feasibility.get("impact_fees", 0),
            parking_required=requirements.get("parking", {}).get("required_spaces", 0),
            building_sqft=layout.get("building_footprint_sqft", 0),
            stages_completed=stages_completed,
            duration_seconds=duration,
            timestamp=datetime.utcnow().isoformat(),
            errors=state.get("errors", [])
        )
        
    except Exception as e:
        logger.error(f"Feasibility error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/feasibility/quick", tags=["Feasibility"])
async def quick_feasibility(
    municipality_id: str = Query(...),
    typology: Typology = Query(Typology.SINGLE_FAMILY),
    units: int = Query(1, ge=1),
    land_cost: float = Query(100000, ge=0)
):
    """
    Quick feasibility check (stops at feasibility stage, skips reporting).
    
    Faster than full analysis for initial screening.
    """
    try:
        from src.pipeline.pipeline_orchestrator import run_quick_feasibility
        
        result = await run_quick_feasibility(
            municipality_id=municipality_id,
            typology=typology.value,
            units=units,
            land_cost=int(land_cost)
        )
        
        return {
            "feasible": result.get("feasible", False),
            "roi_pct": result.get("roi_pct", 0),
            "total_cost": result.get("total_cost", 0),
            "errors": result.get("errors", []),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# PIPELINE ENDPOINTS
# =============================================================================

@app.post("/api/pipeline/execute", tags=["Pipeline"])
async def execute_pipeline(
    request: PipelineRequest,
    background_tasks: BackgroundTasks
):
    """
    Execute the full 12-stage pipeline.
    
    Returns immediately with run_id, execution happens in background.
    Use /api/pipeline/{run_id}/status to check progress.
    """
    run_id = str(uuid.uuid4())
    
    try:
        # Start pipeline in background
        background_tasks.add_task(
            _run_pipeline_background,
            run_id,
            request.municipality_id,
            request.parcel_id,
            request.typology.value,
            request.input_params,
            request.start_from,
            request.stop_at
        )
        
        return {
            "run_id": run_id,
            "status": "started",
            "message": "Pipeline execution started. Check /api/pipeline/{run_id}/status for progress.",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def _run_pipeline_background(
    run_id: str,
    municipality_id: str,
    parcel_id: Optional[str],
    typology: str,
    input_params: Dict,
    start_from: Optional[str],
    stop_at: Optional[str]
):
    """Background task for pipeline execution"""
    try:
        orchestrator = ServiceContainer.get_orchestrator()
        
        # Convert stage strings to enums if provided
        from src.pipeline.pipeline_orchestrator import PipelineStage
        
        start_stage = None
        stop_stage = None
        
        if start_from:
            for stage in PipelineStage:
                if stage.value == start_from or stage.name == start_from:
                    start_stage = stage
                    break
        
        if stop_at:
            for stage in PipelineStage:
                if stage.value == stop_at or stage.name == stop_at:
                    stop_stage = stage
                    break
        
        await orchestrator.run_pipeline(
            municipality_id=municipality_id,
            parcel_id=parcel_id,
            typology=typology,
            input_params=input_params,
            start_from=start_stage,
            stop_at=stop_stage
        )
        
    except Exception as e:
        logger.error(f"Background pipeline error: {e}")


@app.get("/api/pipeline/{run_id}/status", response_model=PipelineStatusResponse, tags=["Pipeline"])
async def get_pipeline_status(run_id: str = Path(...)):
    """Get the status of a pipeline run"""
    try:
        supabase = ServiceContainer.get_supabase()
        
        # Query pipeline_runs table
        response = supabase.client.table("pipeline_runs").select("*").eq("id", run_id).single().execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Pipeline run not found")
        
        run = response.data
        
        # Calculate progress
        results = run.get("results", {})
        stages_completed = results.get("stages_completed", 0) if isinstance(results, dict) else 0
        
        return PipelineStatusResponse(
            run_id=run["id"],
            status=run.get("status", "unknown"),
            current_stage=run.get("current_stage"),
            stages_completed=stages_completed,
            total_stages=12,
            progress_pct=round(stages_completed / 12 * 100, 1),
            started_at=run.get("started_at", ""),
            updated_at=run.get("updated_at", ""),
            errors=[run.get("error")] if run.get("error") else []
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/pipeline/stages", tags=["Pipeline"])
async def get_pipeline_stages():
    """Get information about all 12 pipeline stages"""
    try:
        from src.pipeline.pipeline_orchestrator import get_pipeline_stages
        return {"stages": get_pipeline_stages()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# SCRAPE ENDPOINTS
# =============================================================================

@app.post("/api/scrape", response_model=ScrapeResponse, tags=["Scrape"])
async def trigger_scrape(request: ScrapeRequest):
    """
    Trigger Municode scraping for a municipality.
    
    Extracts zoning districts and site plan requirements from Municode library.
    """
    try:
        scraper = ServiceContainer.get_scraper()
        supabase = ServiceContainer.get_supabase()
        
        # Check if we need to scrape
        if not request.force_refresh and request.municipality_id:
            muni = supabase.get_municipality_by_id(request.municipality_id)
            if muni and muni.get("last_scraped"):
                # Check if recently scraped (within 24 hours)
                last_scraped = datetime.fromisoformat(muni["last_scraped"].replace("Z", "+00:00"))
                if (datetime.utcnow().replace(tzinfo=last_scraped.tzinfo) - last_scraped).total_seconds() < 86400:
                    zoning = supabase.get_zoning_districts(request.municipality_id)
                    reqs = supabase.get_site_plan_requirements(request.municipality_id)
                    
                    return ScrapeResponse(
                        municipality_id=request.municipality_id,
                        municipality_name=muni["name"],
                        status="cached",
                        zoning_count=zoning.count,
                        requirements_count=reqs.count,
                        pages_scraped=0,
                        duration_seconds=0,
                        errors=[]
                    )
        
        # Run scrape
        result, run_id = await scraper.scrape_and_store(
            municipality_key=request.municipality_key,
            municipality_id=request.municipality_id
        )
        
        # Get municipality ID
        muni_id = request.municipality_id
        if not muni_id:
            muni = supabase.get_municipality_by_name(result.municipality_name)
            muni_id = muni["id"] if muni else str(uuid.uuid4())
        
        return ScrapeResponse(
            municipality_id=muni_id,
            municipality_name=result.municipality_name,
            status=result.status.value,
            zoning_count=len(result.zoning_districts),
            requirements_count=len(result.requirements),
            pages_scraped=result.pages_scraped,
            duration_seconds=result.duration_seconds,
            errors=result.errors
        )
        
    except Exception as e:
        logger.error(f"Scrape error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/scrape/municipalities", tags=["Scrape"])
async def get_available_municipalities():
    """Get list of known municipalities that can be scraped"""
    try:
        from src.scrapers.municode_scraper import get_available_municipalities
        return {"municipalities": get_available_municipalities()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# ERROR HANDLERS
# =============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.detail,
            code=f"HTTP_{exc.status_code}",
            timestamp=datetime.utcnow().isoformat()
        ).model_dump()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal server error",
            detail=str(exc),
            code="INTERNAL_ERROR",
            timestamp=datetime.utcnow().isoformat()
        ).model_dump()
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
    print("  - /docs          - Swagger UI")
    print("  - /redoc         - ReDoc")
    print("  - /api/health    - Health check")
    print("  - /api/chat      - AI chat")
    print("  - /api/feasibility - Feasibility analysis")
    print("")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
