#!/usr/bin/env python3
"""
Pipeline Orchestrator - LangGraph 12-Stage Workflow
SPD Site Plan Development - Core Component #3

Orchestrates the complete site plan development analysis pipeline using LangGraph.
Provides state management, checkpointing, and fault-tolerant execution.

12 Stages:
1. Discovery    - Find municipality/parcel data
2. Survey       - Property survey and boundaries
3. Zoning       - Zoning district and regulations
4. Constraints  - Site constraints analysis
5. Parking      - Parking requirements calculation
6. Traffic      - Traffic impact assessment
7. Utilities    - Utility availability check
8. Stormwater   - Stormwater management requirements
9. Layout       - Site layout optimization
10. Feasibility - Financial feasibility analysis
11. Reporting   - Generate reports (DOCX/PDF)
12. Archive     - Store results and cleanup

Author: BidDeed.AI / Everest Capital USA
"""

import os
import json
import uuid
import asyncio
import logging
from typing import Dict, List, Any, Optional, TypedDict, Annotated, Literal
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
import operator

logger = logging.getLogger(__name__)


# =============================================================================
# STAGE DEFINITIONS
# =============================================================================

class StageStatus(Enum):
    """Status of a pipeline stage"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class PipelineStage(Enum):
    """The 12 stages of the SPD pipeline"""
    DISCOVERY = "stage_1_discovery"
    SURVEY = "stage_2_survey"
    ZONING = "stage_3_zoning"
    CONSTRAINTS = "stage_4_constraints"
    PARKING = "stage_5_parking"
    TRAFFIC = "stage_6_traffic"
    UTILITIES = "stage_7_utilities"
    STORMWATER = "stage_8_stormwater"
    LAYOUT = "stage_9_layout"
    FEASIBILITY = "stage_10_feasibility"
    REPORTING = "stage_11_reporting"
    ARCHIVE = "stage_12_archive"


# Stage execution order
STAGE_ORDER = [
    PipelineStage.DISCOVERY,
    PipelineStage.SURVEY,
    PipelineStage.ZONING,
    PipelineStage.CONSTRAINTS,
    PipelineStage.PARKING,
    PipelineStage.TRAFFIC,
    PipelineStage.UTILITIES,
    PipelineStage.STORMWATER,
    PipelineStage.LAYOUT,
    PipelineStage.FEASIBILITY,
    PipelineStage.REPORTING,
    PipelineStage.ARCHIVE,
]

# Stage dependencies (which stages must complete before this one)
STAGE_DEPENDENCIES = {
    PipelineStage.DISCOVERY: [],
    PipelineStage.SURVEY: [PipelineStage.DISCOVERY],
    PipelineStage.ZONING: [PipelineStage.DISCOVERY],
    PipelineStage.CONSTRAINTS: [PipelineStage.SURVEY, PipelineStage.ZONING],
    PipelineStage.PARKING: [PipelineStage.ZONING],
    PipelineStage.TRAFFIC: [PipelineStage.DISCOVERY],
    PipelineStage.UTILITIES: [PipelineStage.SURVEY],
    PipelineStage.STORMWATER: [PipelineStage.SURVEY, PipelineStage.CONSTRAINTS],
    PipelineStage.LAYOUT: [PipelineStage.CONSTRAINTS, PipelineStage.PARKING, PipelineStage.STORMWATER],
    PipelineStage.FEASIBILITY: [PipelineStage.LAYOUT],
    PipelineStage.REPORTING: [PipelineStage.FEASIBILITY],
    PipelineStage.ARCHIVE: [PipelineStage.REPORTING],
}

# Performance thresholds (milliseconds)
STAGE_THRESHOLDS = {
    PipelineStage.DISCOVERY: 5000,
    PipelineStage.SURVEY: 10000,
    PipelineStage.ZONING: 15000,
    PipelineStage.CONSTRAINTS: 8000,
    PipelineStage.PARKING: 5000,
    PipelineStage.TRAFFIC: 12000,
    PipelineStage.UTILITIES: 10000,
    PipelineStage.STORMWATER: 8000,
    PipelineStage.LAYOUT: 20000,
    PipelineStage.FEASIBILITY: 15000,
    PipelineStage.REPORTING: 8000,
    PipelineStage.ARCHIVE: 5000,
}


# =============================================================================
# STATE DEFINITIONS
# =============================================================================

@dataclass
class StageResult:
    """Result from a single stage execution"""
    stage: str
    status: StageStatus
    data: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "stage": self.stage,
            "status": self.status.value,
            "data": self.data,
            "errors": self.errors,
            "warnings": self.warnings,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_ms": self.duration_ms
        }


@dataclass
class PipelineState:
    """Complete state of a pipeline run"""
    run_id: str
    municipality_id: str
    parcel_id: Optional[str] = None
    typology: str = "single_family"  # single_family, multi_family, commercial, etc.
    
    # Input parameters
    input_params: Dict[str, Any] = field(default_factory=dict)
    
    # Stage results
    stage_results: Dict[str, StageResult] = field(default_factory=dict)
    
    # Accumulated data across stages
    municipality_data: Dict[str, Any] = field(default_factory=dict)
    parcel_data: Dict[str, Any] = field(default_factory=dict)
    zoning_data: Dict[str, Any] = field(default_factory=dict)
    constraints_data: Dict[str, Any] = field(default_factory=dict)
    requirements_data: Dict[str, Any] = field(default_factory=dict)
    layout_data: Dict[str, Any] = field(default_factory=dict)
    feasibility_data: Dict[str, Any] = field(default_factory=dict)
    report_data: Dict[str, Any] = field(default_factory=dict)
    
    # Pipeline metadata
    current_stage: Optional[str] = None
    status: str = "pending"
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    
    # Error tracking
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "municipality_id": self.municipality_id,
            "parcel_id": self.parcel_id,
            "typology": self.typology,
            "input_params": self.input_params,
            "stage_results": {k: v.to_dict() for k, v in self.stage_results.items()},
            "current_stage": self.current_stage,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "errors": self.errors,
            "warnings": self.warnings
        }
    
    def get_stage_status(self, stage: PipelineStage) -> StageStatus:
        """Get status of a specific stage"""
        if stage.value in self.stage_results:
            return self.stage_results[stage.value].status
        return StageStatus.PENDING
    
    def is_stage_complete(self, stage: PipelineStage) -> bool:
        """Check if a stage is complete"""
        return self.get_stage_status(stage) == StageStatus.COMPLETED
    
    def are_dependencies_met(self, stage: PipelineStage) -> bool:
        """Check if all dependencies for a stage are met"""
        deps = STAGE_DEPENDENCIES.get(stage, [])
        return all(self.is_stage_complete(dep) for dep in deps)


# =============================================================================
# LANGGRAPH STATE TYPE
# =============================================================================

class GraphState(TypedDict):
    """LangGraph state type"""
    run_id: str
    municipality_id: str
    parcel_id: Optional[str]
    typology: str
    input_params: Dict[str, Any]
    
    # Stage data accumulator
    stage_data: Annotated[Dict[str, Any], operator.or_]
    
    # Current execution
    current_stage: str
    stage_status: str
    
    # Results
    municipality_data: Dict[str, Any]
    parcel_data: Dict[str, Any]
    zoning_data: Dict[str, Any]
    constraints_data: Dict[str, Any]
    requirements_data: Dict[str, Any]
    layout_data: Dict[str, Any]
    feasibility_data: Dict[str, Any]
    report_data: Dict[str, Any]
    
    # Errors
    errors: List[str]
    warnings: List[str]


# =============================================================================
# STAGE EXECUTORS
# =============================================================================

class StageExecutor:
    """Base class for stage executors"""
    
    def __init__(self, supabase_client=None, scraper=None):
        self.supabase = supabase_client
        self.scraper = scraper
    
    async def execute(self, state: GraphState) -> GraphState:
        """Execute the stage - override in subclasses"""
        raise NotImplementedError


class DiscoveryExecutor(StageExecutor):
    """Stage 1: Discovery - Find municipality and parcel data"""
    
    async def execute(self, state: GraphState) -> GraphState:
        logger.info(f"Executing Discovery stage for {state['municipality_id']}")
        
        try:
            municipality_data = {}
            
            # Fetch municipality from Supabase
            if self.supabase:
                muni = self.supabase.get_municipality_by_id(state['municipality_id'])
                if muni:
                    municipality_data = muni
                    logger.info(f"Found municipality: {muni.get('name')}")
            
            # Fetch parcel if provided
            parcel_data = {}
            if state.get('parcel_id') and self.supabase:
                # Query parcel data from BCPAO or local DB
                pass  # Parcel lookup logic here
            
            state['municipality_data'] = municipality_data
            state['parcel_data'] = parcel_data
            state['stage_data'] = {
                PipelineStage.DISCOVERY.value: {
                    "status": "completed",
                    "municipality_found": bool(municipality_data),
                    "parcel_found": bool(parcel_data)
                }
            }
            state['stage_status'] = 'completed'
            
        except Exception as e:
            logger.error(f"Discovery failed: {e}")
            state['errors'].append(f"Discovery: {str(e)}")
            state['stage_status'] = 'failed'
        
        return state


class SurveyExecutor(StageExecutor):
    """Stage 2: Survey - Property survey and boundaries"""
    
    async def execute(self, state: GraphState) -> GraphState:
        logger.info("Executing Survey stage")
        
        try:
            # Get property boundaries, lot size, dimensions
            parcel_data = state.get('parcel_data', {})
            
            survey_data = {
                "lot_size_acres": parcel_data.get('lot_size_acres', 0),
                "lot_size_sqft": parcel_data.get('lot_size_sqft', 0),
                "dimensions": parcel_data.get('dimensions', {}),
                "frontage": parcel_data.get('frontage', 0),
                "depth": parcel_data.get('depth', 0),
                "shape": parcel_data.get('shape', 'rectangular'),
                "topography": parcel_data.get('topography', 'flat'),
            }
            
            state['parcel_data'].update(survey_data)
            state['stage_data'] = {
                PipelineStage.SURVEY.value: {
                    "status": "completed",
                    "lot_size_sqft": survey_data.get('lot_size_sqft', 0)
                }
            }
            state['stage_status'] = 'completed'
            
        except Exception as e:
            logger.error(f"Survey failed: {e}")
            state['errors'].append(f"Survey: {str(e)}")
            state['stage_status'] = 'failed'
        
        return state


class ZoningExecutor(StageExecutor):
    """Stage 3: Zoning - Fetch zoning district and regulations"""
    
    async def execute(self, state: GraphState) -> GraphState:
        logger.info("Executing Zoning stage")
        
        try:
            zoning_data = {}
            
            # Fetch zoning districts from Supabase
            if self.supabase:
                result = self.supabase.get_zoning_districts(state['municipality_id'])
                if result.success and result.data:
                    zoning_data['districts'] = result.data
                    zoning_data['district_count'] = len(result.data)
                    logger.info(f"Found {len(result.data)} zoning districts")
                
                # Fetch site plan requirements
                reqs = self.supabase.get_site_plan_requirements(state['municipality_id'])
                if reqs.success and reqs.data:
                    zoning_data['requirements'] = reqs.data
                    zoning_data['requirements_count'] = len(reqs.data)
            
            # If no data and scraper available, trigger scrape
            if not zoning_data.get('districts') and self.scraper:
                muni_name = state.get('municipality_data', {}).get('name', '').lower().replace(' ', '_')
                if muni_name:
                    logger.info(f"No cached data, scraping {muni_name}")
                    result = await self.scraper.scrape_municipality(muni_name)
                    if result.zoning_districts:
                        zoning_data['districts'] = [z.__dict__ for z in result.zoning_districts]
                        zoning_data['requirements'] = [r.__dict__ for r in result.requirements]
            
            state['zoning_data'] = zoning_data
            state['stage_data'] = {
                PipelineStage.ZONING.value: {
                    "status": "completed",
                    "districts_found": zoning_data.get('district_count', 0),
                    "requirements_found": zoning_data.get('requirements_count', 0)
                }
            }
            state['stage_status'] = 'completed'
            
        except Exception as e:
            logger.error(f"Zoning failed: {e}")
            state['errors'].append(f"Zoning: {str(e)}")
            state['stage_status'] = 'failed'
        
        return state


class ConstraintsExecutor(StageExecutor):
    """Stage 4: Constraints - Analyze site constraints"""
    
    async def execute(self, state: GraphState) -> GraphState:
        logger.info("Executing Constraints stage")
        
        try:
            constraints = {
                "setbacks": {},
                "easements": [],
                "flood_zone": None,
                "wetlands": False,
                "environmental": [],
                "buildable_area_sqft": 0,
            }
            
            # Get setbacks from zoning requirements
            zoning_reqs = state.get('zoning_data', {}).get('requirements', [])
            for req in zoning_reqs:
                if isinstance(req, dict) and req.get('requirement_type') == 'setback':
                    # Parse setback values
                    desc = req.get('description', '')
                    if 'front' in desc.lower():
                        constraints['setbacks']['front'] = req.get('standard', '25 ft')
                    elif 'rear' in desc.lower():
                        constraints['setbacks']['rear'] = req.get('standard', '20 ft')
                    elif 'side' in desc.lower():
                        constraints['setbacks']['side'] = req.get('standard', '10 ft')
            
            # Calculate buildable area (simplified)
            lot_sqft = state.get('parcel_data', {}).get('lot_size_sqft', 0)
            if lot_sqft > 0:
                # Assume 60% buildable after setbacks (rough estimate)
                constraints['buildable_area_sqft'] = int(lot_sqft * 0.60)
            
            state['constraints_data'] = constraints
            state['stage_data'] = {
                PipelineStage.CONSTRAINTS.value: {
                    "status": "completed",
                    "buildable_sqft": constraints['buildable_area_sqft']
                }
            }
            state['stage_status'] = 'completed'
            
        except Exception as e:
            logger.error(f"Constraints failed: {e}")
            state['errors'].append(f"Constraints: {str(e)}")
            state['stage_status'] = 'failed'
        
        return state


class ParkingExecutor(StageExecutor):
    """Stage 5: Parking - Calculate parking requirements"""
    
    async def execute(self, state: GraphState) -> GraphState:
        logger.info("Executing Parking stage")
        
        try:
            typology = state.get('typology', 'single_family')
            
            # Default parking ratios by typology
            PARKING_RATIOS = {
                'single_family': 2,      # 2 spaces per unit
                'multi_family': 1.5,     # 1.5 spaces per unit
                'commercial': 4,         # 4 per 1000 sqft
                'retail': 5,             # 5 per 1000 sqft
                'office': 3,             # 3 per 1000 sqft
                'industrial': 1,         # 1 per 1000 sqft
                'mixed_use': 2,          # Varies
                'assisted_living': 0.5,  # 0.5 per bed
            }
            
            parking = {
                "required_spaces": 0,
                "ratio": PARKING_RATIOS.get(typology, 2),
                "typology": typology,
                "ada_required": 1,  # Minimum ADA spaces
                "loading_spaces": 0,
            }
            
            # Check for custom requirement from zoning
            zoning_reqs = state.get('zoning_data', {}).get('requirements', [])
            for req in zoning_reqs:
                if isinstance(req, dict) and req.get('requirement_type') == 'parking':
                    standard = req.get('standard', '')
                    # Try to parse numeric value
                    import re
                    match = re.search(r'(\d+(?:\.\d+)?)', standard)
                    if match:
                        parking['ratio'] = float(match.group(1))
            
            # Calculate based on input params
            units = state.get('input_params', {}).get('units', 1)
            sqft = state.get('input_params', {}).get('building_sqft', 0)
            
            if typology in ['single_family', 'multi_family', 'assisted_living']:
                parking['required_spaces'] = int(units * parking['ratio'])
            else:
                parking['required_spaces'] = int((sqft / 1000) * parking['ratio'])
            
            # ADA calculation (simplified)
            if parking['required_spaces'] > 25:
                parking['ada_required'] = 2
            if parking['required_spaces'] > 100:
                parking['ada_required'] = 4
            
            state['requirements_data']['parking'] = parking
            state['stage_data'] = {
                PipelineStage.PARKING.value: {
                    "status": "completed",
                    "required_spaces": parking['required_spaces']
                }
            }
            state['stage_status'] = 'completed'
            
        except Exception as e:
            logger.error(f"Parking failed: {e}")
            state['errors'].append(f"Parking: {str(e)}")
            state['stage_status'] = 'failed'
        
        return state


class TrafficExecutor(StageExecutor):
    """Stage 6: Traffic - Traffic impact assessment"""
    
    async def execute(self, state: GraphState) -> GraphState:
        logger.info("Executing Traffic stage")
        
        try:
            traffic = {
                "daily_trips": 0,
                "peak_hour_trips": 0,
                "impact_study_required": False,
                "access_points": 1,
            }
            
            # ITE Trip Generation (simplified)
            typology = state.get('typology', 'single_family')
            units = state.get('input_params', {}).get('units', 1)
            sqft = state.get('input_params', {}).get('building_sqft', 0)
            
            ITE_RATES = {
                'single_family': 9.44,      # trips per unit
                'multi_family': 6.65,
                'commercial': 42.7,         # per 1000 sqft
                'retail': 37.75,
                'office': 9.74,
            }
            
            rate = ITE_RATES.get(typology, 9.44)
            
            if typology in ['single_family', 'multi_family']:
                traffic['daily_trips'] = int(units * rate)
            else:
                traffic['daily_trips'] = int((sqft / 1000) * rate)
            
            traffic['peak_hour_trips'] = int(traffic['daily_trips'] * 0.10)
            
            # Impact study threshold (typically 100+ peak hour trips)
            if traffic['peak_hour_trips'] > 100:
                traffic['impact_study_required'] = True
            
            state['requirements_data']['traffic'] = traffic
            state['stage_data'] = {
                PipelineStage.TRAFFIC.value: {
                    "status": "completed",
                    "daily_trips": traffic['daily_trips']
                }
            }
            state['stage_status'] = 'completed'
            
        except Exception as e:
            logger.error(f"Traffic failed: {e}")
            state['errors'].append(f"Traffic: {str(e)}")
            state['stage_status'] = 'failed'
        
        return state


class UtilitiesExecutor(StageExecutor):
    """Stage 7: Utilities - Check utility availability"""
    
    async def execute(self, state: GraphState) -> GraphState:
        logger.info("Executing Utilities stage")
        
        try:
            utilities = {
                "water": {"available": True, "provider": "Municipal"},
                "sewer": {"available": True, "provider": "Municipal"},
                "electric": {"available": True, "provider": "FPL"},
                "gas": {"available": False, "provider": None},
                "telecom": {"available": True, "provider": "Various"},
                "impact_fees": {},
            }
            
            # Estimate impact fees based on typology
            typology = state.get('typology', 'single_family')
            units = state.get('input_params', {}).get('units', 1)
            
            # Brevard County typical impact fees (approximate)
            IMPACT_FEES = {
                'single_family': {'water': 2500, 'sewer': 3000, 'transportation': 4500},
                'multi_family': {'water': 1800, 'sewer': 2200, 'transportation': 2800},
                'commercial': {'water': 5000, 'sewer': 6000, 'transportation': 8000},
            }
            
            fees = IMPACT_FEES.get(typology, IMPACT_FEES['single_family'])
            utilities['impact_fees'] = {
                "water": fees['water'] * units,
                "sewer": fees['sewer'] * units,
                "transportation": fees['transportation'] * units,
                "total": sum(fees.values()) * units
            }
            
            state['requirements_data']['utilities'] = utilities
            state['stage_data'] = {
                PipelineStage.UTILITIES.value: {
                    "status": "completed",
                    "total_impact_fees": utilities['impact_fees']['total']
                }
            }
            state['stage_status'] = 'completed'
            
        except Exception as e:
            logger.error(f"Utilities failed: {e}")
            state['errors'].append(f"Utilities: {str(e)}")
            state['stage_status'] = 'failed'
        
        return state


class StormwaterExecutor(StageExecutor):
    """Stage 8: Stormwater - Stormwater management requirements"""
    
    async def execute(self, state: GraphState) -> GraphState:
        logger.info("Executing Stormwater stage")
        
        try:
            lot_sqft = state.get('parcel_data', {}).get('lot_size_sqft', 0)
            
            stormwater = {
                "retention_required": lot_sqft > 10000,  # Typically required for larger lots
                "retention_volume_cf": 0,
                "impervious_limit_pct": 70,
                "permit_required": False,
                "sjrwmd_permit": False,  # St Johns River WMD
            }
            
            # Calculate retention (simplified: 1 inch of runoff from impervious)
            impervious_sqft = lot_sqft * 0.50  # Assume 50% impervious
            stormwater['retention_volume_cf'] = int(impervious_sqft * (1/12))  # 1 inch = 1/12 foot
            
            # SJRWMD permit thresholds
            if lot_sqft > 43560:  # > 1 acre
                stormwater['permit_required'] = True
            if lot_sqft > 435600:  # > 10 acres
                stormwater['sjrwmd_permit'] = True
            
            state['requirements_data']['stormwater'] = stormwater
            state['stage_data'] = {
                PipelineStage.STORMWATER.value: {
                    "status": "completed",
                    "retention_cf": stormwater['retention_volume_cf']
                }
            }
            state['stage_status'] = 'completed'
            
        except Exception as e:
            logger.error(f"Stormwater failed: {e}")
            state['errors'].append(f"Stormwater: {str(e)}")
            state['stage_status'] = 'failed'
        
        return state


class LayoutExecutor(StageExecutor):
    """Stage 9: Layout - Optimize site layout"""
    
    async def execute(self, state: GraphState) -> GraphState:
        logger.info("Executing Layout stage")
        
        try:
            buildable_sqft = state.get('constraints_data', {}).get('buildable_area_sqft', 0)
            parking_spaces = state.get('requirements_data', {}).get('parking', {}).get('required_spaces', 0)
            
            layout = {
                "building_footprint_sqft": 0,
                "parking_area_sqft": parking_spaces * 180,  # ~180 sqft per space
                "landscape_area_sqft": 0,
                "open_space_sqft": 0,
                "efficiency_pct": 0,
            }
            
            # Calculate remaining area for building
            remaining = buildable_sqft - layout['parking_area_sqft']
            
            # Landscape requirement (typically 15-20%)
            layout['landscape_area_sqft'] = int(buildable_sqft * 0.15)
            remaining -= layout['landscape_area_sqft']
            
            # Building footprint is remaining area
            layout['building_footprint_sqft'] = max(0, remaining)
            
            # Open space
            layout['open_space_sqft'] = buildable_sqft - layout['building_footprint_sqft'] - layout['parking_area_sqft']
            
            # Efficiency
            if buildable_sqft > 0:
                layout['efficiency_pct'] = round(layout['building_footprint_sqft'] / buildable_sqft * 100, 1)
            
            state['layout_data'] = layout
            state['stage_data'] = {
                PipelineStage.LAYOUT.value: {
                    "status": "completed",
                    "building_sqft": layout['building_footprint_sqft'],
                    "efficiency": layout['efficiency_pct']
                }
            }
            state['stage_status'] = 'completed'
            
        except Exception as e:
            logger.error(f"Layout failed: {e}")
            state['errors'].append(f"Layout: {str(e)}")
            state['stage_status'] = 'failed'
        
        return state


class FeasibilityExecutor(StageExecutor):
    """Stage 10: Feasibility - Financial analysis"""
    
    async def execute(self, state: GraphState) -> GraphState:
        logger.info("Executing Feasibility stage")
        
        try:
            typology = state.get('typology', 'single_family')
            units = state.get('input_params', {}).get('units', 1)
            building_sqft = state.get('layout_data', {}).get('building_footprint_sqft', 0)
            impact_fees = state.get('requirements_data', {}).get('utilities', {}).get('impact_fees', {}).get('total', 0)
            
            # Cost estimates (per sqft, Brevard County typical)
            CONSTRUCTION_COSTS = {
                'single_family': 150,
                'multi_family': 120,
                'commercial': 100,
                'retail': 110,
                'office': 130,
                'industrial': 80,
                'assisted_living': 180,
            }
            
            # Revenue estimates (per sqft or per unit)
            REVENUE_PSF = {
                'single_family': 250,     # Sale price PSF
                'multi_family': 1.50,     # Rent PSF/month
                'commercial': 18,         # NNN rent PSF/year
                'retail': 22,
                'office': 20,
                'industrial': 10,
                'assisted_living': 4500,  # Per bed/month
            }
            
            cost_psf = CONSTRUCTION_COSTS.get(typology, 150)
            revenue = REVENUE_PSF.get(typology, 250)
            
            feasibility = {
                "land_cost": state.get('input_params', {}).get('land_cost', 100000),
                "construction_cost": building_sqft * cost_psf,
                "soft_costs": building_sqft * cost_psf * 0.15,  # 15% of hard costs
                "impact_fees": impact_fees,
                "total_cost": 0,
                "revenue": 0,
                "profit": 0,
                "roi_pct": 0,
                "feasible": False,
            }
            
            feasibility['total_cost'] = (
                feasibility['land_cost'] +
                feasibility['construction_cost'] +
                feasibility['soft_costs'] +
                feasibility['impact_fees']
            )
            
            # Revenue calculation
            if typology == 'single_family':
                feasibility['revenue'] = building_sqft * revenue
            elif typology in ['multi_family', 'assisted_living']:
                # Annual revenue
                feasibility['revenue'] = units * revenue * 12
            else:
                # Annual revenue for commercial
                feasibility['revenue'] = building_sqft * revenue
            
            # Profit and ROI
            if typology == 'single_family':
                feasibility['profit'] = feasibility['revenue'] - feasibility['total_cost']
            else:
                # For rental, use 10x annual revenue as value
                feasibility['profit'] = (feasibility['revenue'] * 10) - feasibility['total_cost']
            
            if feasibility['total_cost'] > 0:
                feasibility['roi_pct'] = round(feasibility['profit'] / feasibility['total_cost'] * 100, 1)
            
            feasibility['feasible'] = feasibility['roi_pct'] > 15  # 15% threshold
            
            state['feasibility_data'] = feasibility
            state['stage_data'] = {
                PipelineStage.FEASIBILITY.value: {
                    "status": "completed",
                    "roi_pct": feasibility['roi_pct'],
                    "feasible": feasibility['feasible']
                }
            }
            state['stage_status'] = 'completed'
            
        except Exception as e:
            logger.error(f"Feasibility failed: {e}")
            state['errors'].append(f"Feasibility: {str(e)}")
            state['stage_status'] = 'failed'
        
        return state


class ReportingExecutor(StageExecutor):
    """Stage 11: Reporting - Generate analysis report"""
    
    async def execute(self, state: GraphState) -> GraphState:
        logger.info("Executing Reporting stage")
        
        try:
            report = {
                "generated_at": datetime.utcnow().isoformat(),
                "run_id": state['run_id'],
                "municipality": state.get('municipality_data', {}).get('name', 'Unknown'),
                "typology": state['typology'],
                "summary": {
                    "zoning_districts": state.get('zoning_data', {}).get('district_count', 0),
                    "parking_required": state.get('requirements_data', {}).get('parking', {}).get('required_spaces', 0),
                    "building_sqft": state.get('layout_data', {}).get('building_footprint_sqft', 0),
                    "roi_pct": state.get('feasibility_data', {}).get('roi_pct', 0),
                    "feasible": state.get('feasibility_data', {}).get('feasible', False),
                },
                "errors": state.get('errors', []),
                "warnings": state.get('warnings', []),
            }
            
            # Store in Supabase
            if self.supabase:
                self.supabase._client.table('reports').upsert({
                    "id": str(uuid.uuid4()),
                    "run_id": state['run_id'],
                    "municipality_id": state['municipality_id'],
                    "report_type": "feasibility_analysis",
                    "content": report,
                    "created_at": datetime.utcnow().isoformat()
                }).execute()
            
            state['report_data'] = report
            state['stage_data'] = {
                PipelineStage.REPORTING.value: {
                    "status": "completed",
                    "report_generated": True
                }
            }
            state['stage_status'] = 'completed'
            
        except Exception as e:
            logger.error(f"Reporting failed: {e}")
            state['errors'].append(f"Reporting: {str(e)}")
            state['stage_status'] = 'failed'
        
        return state


class ArchiveExecutor(StageExecutor):
    """Stage 12: Archive - Store results and cleanup"""
    
    async def execute(self, state: GraphState) -> GraphState:
        logger.info("Executing Archive stage")
        
        try:
            # Update pipeline run in Supabase
            if self.supabase:
                self.supabase.update_pipeline_status(
                    state['run_id'],
                    "completed",
                    results={
                        "stages_completed": len([s for s in state.get('stage_data', {}).values() 
                                                if s.get('status') == 'completed']),
                        "feasible": state.get('feasibility_data', {}).get('feasible', False),
                        "roi_pct": state.get('feasibility_data', {}).get('roi_pct', 0),
                    }
                )
            
            state['stage_data'] = {
                PipelineStage.ARCHIVE.value: {
                    "status": "completed",
                    "archived_at": datetime.utcnow().isoformat()
                }
            }
            state['stage_status'] = 'completed'
            
        except Exception as e:
            logger.error(f"Archive failed: {e}")
            state['errors'].append(f"Archive: {str(e)}")
            state['stage_status'] = 'failed'
        
        return state


# =============================================================================
# PIPELINE ORCHESTRATOR
# =============================================================================

class SPDPipelineOrchestrator:
    """
    Main pipeline orchestrator using LangGraph patterns.
    
    Usage:
        orchestrator = SPDPipelineOrchestrator(supabase_client=client)
        
        result = await orchestrator.run_pipeline(
            municipality_id="8f8ed567-9052-492e-905c-436455e90f7d",
            typology="single_family",
            input_params={"units": 1, "land_cost": 150000}
        )
    """
    
    def __init__(self, supabase_client=None, scraper=None):
        self.supabase = supabase_client
        self.scraper = scraper
        
        # Initialize executors
        self.executors = {
            PipelineStage.DISCOVERY: DiscoveryExecutor(supabase_client, scraper),
            PipelineStage.SURVEY: SurveyExecutor(supabase_client, scraper),
            PipelineStage.ZONING: ZoningExecutor(supabase_client, scraper),
            PipelineStage.CONSTRAINTS: ConstraintsExecutor(supabase_client, scraper),
            PipelineStage.PARKING: ParkingExecutor(supabase_client, scraper),
            PipelineStage.TRAFFIC: TrafficExecutor(supabase_client, scraper),
            PipelineStage.UTILITIES: UtilitiesExecutor(supabase_client, scraper),
            PipelineStage.STORMWATER: StormwaterExecutor(supabase_client, scraper),
            PipelineStage.LAYOUT: LayoutExecutor(supabase_client, scraper),
            PipelineStage.FEASIBILITY: FeasibilityExecutor(supabase_client, scraper),
            PipelineStage.REPORTING: ReportingExecutor(supabase_client, scraper),
            PipelineStage.ARCHIVE: ArchiveExecutor(supabase_client, scraper),
        }
        
        logger.info("SPD Pipeline Orchestrator initialized")
    
    def _create_initial_state(
        self,
        municipality_id: str,
        parcel_id: Optional[str] = None,
        typology: str = "single_family",
        input_params: Optional[Dict] = None
    ) -> GraphState:
        """Create initial pipeline state"""
        return {
            "run_id": str(uuid.uuid4()),
            "municipality_id": municipality_id,
            "parcel_id": parcel_id,
            "typology": typology,
            "input_params": input_params or {},
            "stage_data": {},
            "current_stage": "",
            "stage_status": "pending",
            "municipality_data": {},
            "parcel_data": {},
            "zoning_data": {},
            "constraints_data": {},
            "requirements_data": {},
            "layout_data": {},
            "feasibility_data": {},
            "report_data": {},
            "errors": [],
            "warnings": [],
        }
    
    async def run_stage(self, stage: PipelineStage, state: GraphState) -> GraphState:
        """Execute a single pipeline stage"""
        logger.info(f"Running stage: {stage.value}")
        
        state['current_stage'] = stage.value
        state['stage_status'] = 'running'
        
        start_time = datetime.utcnow()
        
        try:
            executor = self.executors[stage]
            state = await executor.execute(state)
            
            # Check for timeout
            duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            threshold = STAGE_THRESHOLDS.get(stage, 10000)
            
            if duration_ms > threshold:
                state['warnings'].append(f"{stage.value} exceeded threshold: {duration_ms:.0f}ms > {threshold}ms")
            
        except Exception as e:
            logger.error(f"Stage {stage.value} failed: {e}")
            state['errors'].append(f"{stage.value}: {str(e)}")
            state['stage_status'] = 'failed'
        
        return state
    
    async def run_pipeline(
        self,
        municipality_id: str,
        parcel_id: Optional[str] = None,
        typology: str = "single_family",
        input_params: Optional[Dict] = None,
        start_from: Optional[PipelineStage] = None,
        stop_at: Optional[PipelineStage] = None
    ) -> GraphState:
        """
        Run the complete 12-stage pipeline.
        
        Args:
            municipality_id: UUID of the municipality
            parcel_id: Optional specific parcel to analyze
            typology: Development type (single_family, multi_family, etc.)
            input_params: Additional parameters (units, land_cost, etc.)
            start_from: Optional stage to start from (for resume)
            stop_at: Optional stage to stop at (for partial runs)
        
        Returns:
            Final pipeline state with all results
        """
        # Create initial state
        state = self._create_initial_state(
            municipality_id=municipality_id,
            parcel_id=parcel_id,
            typology=typology,
            input_params=input_params
        )
        
        # Create pipeline run record
        if self.supabase:
            run_id = self.supabase.create_pipeline_run(
                municipality_id=municipality_id,
                pipeline_type="spd_full_analysis",
                metadata={
                    "typology": typology,
                    "input_params": input_params
                }
            )
            if run_id:
                state['run_id'] = run_id
        
        logger.info(f"Starting pipeline run: {state['run_id']}")
        
        # Determine which stages to run
        stages_to_run = STAGE_ORDER.copy()
        
        if start_from:
            start_idx = stages_to_run.index(start_from)
            stages_to_run = stages_to_run[start_idx:]
        
        if stop_at:
            stop_idx = stages_to_run.index(stop_at) + 1
            stages_to_run = stages_to_run[:stop_idx]
        
        # Execute stages in order
        for stage in stages_to_run:
            state = await self.run_stage(stage, state)
            
            # Stop on critical failure
            if state['stage_status'] == 'failed':
                if stage in [PipelineStage.DISCOVERY, PipelineStage.ZONING]:
                    logger.error(f"Critical stage {stage.value} failed, stopping pipeline")
                    break
        
        # Mark completion
        completed_stages = len([s for s in state.get('stage_data', {}).values() 
                               if s.get('status') == 'completed'])
        
        if completed_stages == len(stages_to_run):
            state['stage_status'] = 'completed'
            logger.info(f"Pipeline completed: {completed_stages}/{len(stages_to_run)} stages")
        else:
            state['stage_status'] = 'partial'
            logger.warning(f"Pipeline partial: {completed_stages}/{len(stages_to_run)} stages")
        
        return state
    
    async def run_malabar_poc(self) -> GraphState:
        """Run pipeline for Malabar POC validation"""
        MALABAR_ID = "8f8ed567-9052-492e-905c-436455e90f7d"
        
        return await self.run_pipeline(
            municipality_id=MALABAR_ID,
            typology="single_family",
            input_params={
                "units": 1,
                "land_cost": 100000,
                "building_sqft": 2000
            }
        )


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def get_pipeline_stages() -> List[Dict[str, Any]]:
    """Get list of all pipeline stages with info"""
    return [
        {
            "stage": stage.value,
            "name": stage.name,
            "order": i + 1,
            "threshold_ms": STAGE_THRESHOLDS.get(stage, 10000),
            "dependencies": [d.value for d in STAGE_DEPENDENCIES.get(stage, [])]
        }
        for i, stage in enumerate(STAGE_ORDER)
    ]


async def run_quick_feasibility(
    municipality_id: str,
    typology: str = "single_family",
    units: int = 1,
    land_cost: int = 100000
) -> Dict[str, Any]:
    """Quick feasibility check without full pipeline"""
    orchestrator = SPDPipelineOrchestrator()
    
    state = await orchestrator.run_pipeline(
        municipality_id=municipality_id,
        typology=typology,
        input_params={"units": units, "land_cost": land_cost},
        stop_at=PipelineStage.FEASIBILITY
    )
    
    return {
        "feasible": state.get('feasibility_data', {}).get('feasible', False),
        "roi_pct": state.get('feasibility_data', {}).get('roi_pct', 0),
        "total_cost": state.get('feasibility_data', {}).get('total_cost', 0),
        "errors": state.get('errors', [])
    }


if __name__ == "__main__":
    import sys
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    async def main():
        print("=" * 60)
        print("SPD Pipeline Orchestrator - Test Run")
        print("=" * 60)
        
        # Show stages
        print("\n12-Stage Pipeline:")
        for stage_info in get_pipeline_stages():
            print(f"  {stage_info['order']:2d}. {stage_info['name']:15s} (threshold: {stage_info['threshold_ms']}ms)")
        
        # Run Malabar POC
        print("\n" + "-" * 60)
        print("Running Malabar POC...")
        
        orchestrator = SPDPipelineOrchestrator()
        state = await orchestrator.run_malabar_poc()
        
        print(f"\nPipeline Status: {state['stage_status']}")
        print(f"Stages Completed: {len([s for s in state.get('stage_data', {}).values() if s.get('status') == 'completed'])}/12")
        
        if state.get('feasibility_data'):
            print(f"\nFeasibility Results:")
            print(f"  ROI: {state['feasibility_data'].get('roi_pct', 0)}%")
            print(f"  Feasible: {'Yes' if state['feasibility_data'].get('feasible') else 'No'}")
            print(f"  Total Cost: ${state['feasibility_data'].get('total_cost', 0):,.0f}")
        
        if state.get('errors'):
            print(f"\nErrors: {state['errors']}")
    
    asyncio.run(main())
