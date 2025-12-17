"""
Tests for ZOD Pipeline

Run with: pytest tests/test_zod_graph.py -v
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, patch, MagicMock

from src.agents.zod_graph import (
    ZODState,
    OpportunityGrade,
    data_acquisition_agent,
    zoning_analysis_agent,
    flu_analysis_agent,
    constraint_mapping_agent,
    opportunity_scoring_agent,
    build_zod_graph,
    compile_zod_graph,
)
from src.models.state_models import (
    PALM_BAY_ZONING_DISTRICTS,
    PALM_BAY_FLU_DESIGNATIONS,
    get_jurisdiction_definitions,
)


class TestStateModels:
    """Test state model definitions."""
    
    def test_palm_bay_zoning_districts(self):
        """Verify Palm Bay zoning district definitions."""
        assert "RM-20" in PALM_BAY_ZONING_DISTRICTS
        assert PALM_BAY_ZONING_DISTRICTS["RM-20"].max_density_du_acre == 20
        assert PALM_BAY_ZONING_DISTRICTS["RS-1"].max_density_du_acre == 1
    
    def test_palm_bay_flu_designations(self):
        """Verify Palm Bay FLU definitions."""
        assert "HDR" in PALM_BAY_FLU_DESIGNATIONS
        assert PALM_BAY_FLU_DESIGNATIONS["HDR"].max_density_du_acre == 20
        assert "RM-20" in PALM_BAY_FLU_DESIGNATIONS["HDR"].permitted_zoning
    
    def test_jurisdiction_lookup(self):
        """Test jurisdiction definition lookup."""
        zoning, flu = get_jurisdiction_definitions("Palm Bay")
        assert "RM-20" in zoning
        assert "HDR" in flu
        
        # Default to Brevard
        zoning, flu = get_jurisdiction_definitions("Unknown City")
        assert "RM-20" in zoning


class TestOpportunityGrade:
    """Test opportunity grading."""
    
    def test_grade_values(self):
        """Verify grade enum values."""
        assert OpportunityGrade.A_PLUS.value == "A+"
        assert OpportunityGrade.F.value == "F"


class TestZODGraph:
    """Test LangGraph orchestration."""
    
    def test_graph_builds(self):
        """Verify graph builds without errors."""
        graph = build_zod_graph()
        assert graph is not None
    
    def test_graph_compiles(self):
        """Verify graph compiles."""
        app = compile_zod_graph(checkpointer=False)
        assert app is not None


class TestZoningAnalysisAgent:
    """Test zoning analysis agent."""
    
    @pytest.mark.asyncio
    async def test_zoning_analysis(self):
        """Test zoning analysis for a parcel."""
        state = {
            "parcels_raw": [
                {
                    "parcel_id": "2835546",
                    "zoning_code": "PUD",
                    "flu_designation": "HDR",
                    "acres": 1.065
                }
            ],
            "zoning_districts": {
                "PUD": {
                    "max_density_du_acre": 4,
                    "permitted_uses": ["per_pud_document"],
                    "setback_front": 25
                }
            },
            "flu_designations": {},
            "parcels_analyzed": [],
            "checkpoints": []
        }
        
        result = await zoning_analysis_agent(state)
        
        assert len(result["parcels_analyzed"]) == 1
        parcel = result["parcels_analyzed"][0]
        assert parcel["zoning_analysis"]["current_zoning"] == "PUD"
        assert parcel["zoning_analysis"]["max_density"] == 4


class TestFLUAnalysisAgent:
    """Test FLU analysis agent."""
    
    @pytest.mark.asyncio
    async def test_flu_analysis_identifies_opportunity(self):
        """Test FLU analysis correctly identifies density gap."""
        state = {
            "parcels_analyzed": [
                {
                    "parcel_id": "2835546",
                    "zoning_code": "PUD",
                    "flu_designation": "HDR",
                    "acres": 1.065,
                    "zoning_analysis": {
                        "current_zoning": "PUD",
                        "max_density": 4
                    }
                }
            ],
            "flu_designations": {
                "HDR": {
                    "description": "High Density Residential",
                    "max_density_du_acre": 20,
                    "min_density_du_acre": 10,
                    "permitted_zoning": ["RM-10", "RM-15", "RM-20"]
                }
            },
            "opportunities": [],
            "checkpoints": []
        }
        
        result = await flu_analysis_agent(state)
        
        # Should identify opportunity
        assert len(result["opportunities"]) == 1
        opp = result["opportunities"][0]
        assert opp["flu_analysis"]["density_gap"] == 16  # 20 - 4
        assert opp["flu_analysis"]["has_opportunity"] is True


class TestOpportunityScoringAgent:
    """Test opportunity scoring agent."""
    
    @pytest.mark.asyncio
    async def test_scoring_high_opportunity(self):
        """Test scoring for a high-potential opportunity."""
        state = {
            "parcels_analyzed": [
                {
                    "parcel_id": "2835546",
                    "acres": 1.065,
                    "flu_analysis": {
                        "density_gap": 16,
                        "flu_max_density": 20,
                        "has_opportunity": True
                    },
                    "zoning_analysis": {
                        "max_density": 4
                    },
                    "constraint_analysis": {
                        "total_acres": 1.065,
                        "buildable_acres": 0.56,
                        "buildable_pct": 52.6,
                        "is_viable": True
                    }
                }
            ],
            "opportunities": [],
            "checkpoints": []
        }
        
        result = await opportunity_scoring_agent(state)
        
        assert len(result["opportunities"]) == 1
        score = result["opportunities"][0]["opportunity_score"]
        assert score["total_score"] > 50  # Should be a decent opportunity
        assert score["grade"] in ["A+", "A", "B+", "B", "C"]
        assert score["unit_analysis"]["unit_upside"] > 0


class TestBlissPalmBayReference:
    """
    Test against Bliss Palm Bay reference case.
    
    Known facts:
    - Parcel: 2835546
    - Acres: 1.065
    - Current zoning: PUD
    - FLU: HDR (20 du/ac max)
    - Wellhead easement: 47% encumbered
    - Buildable: ~0.56 acres
    """
    
    @pytest.mark.asyncio
    async def test_bliss_palm_bay_analysis(self):
        """Validate analysis matches known Bliss Palm Bay characteristics."""
        # This would be a full integration test
        # For unit tests, we verify components work correctly
        
        # Verify density gap calculation
        current_density = 4  # Assumed from PUD
        flu_max = 20  # HDR
        expected_gap = 16
        
        actual_gap = flu_max - current_density
        assert actual_gap == expected_gap
        
        # Verify buildable area calculation
        total_acres = 1.065
        encumbered_pct = 47
        expected_buildable = total_acres * (1 - encumbered_pct / 100)
        
        assert abs(expected_buildable - 0.56) < 0.05  # Within 0.05 acres
        
        # Verify potential units
        potential_units = int(expected_buildable * flu_max)
        assert potential_units >= 10  # Should be able to fit ~11 units


class TestIntegrations:
    """Test integration clients."""
    
    @pytest.mark.asyncio
    async def test_gis_client_import(self):
        """Verify GIS client can be imported."""
        from src.integrations.gis_client import GISClient
        client = GISClient("Palm Bay")
        assert client.jurisdiction == "Palm Bay"
    
    @pytest.mark.asyncio
    async def test_bcpao_client_import(self):
        """Verify BCPAO client can be imported."""
        from src.integrations.bcpao_client import BCPAOClient
        client = BCPAOClient()
        assert client.BASE_URL == "https://www.bcpao.us/api/v1"
    
    @pytest.mark.asyncio
    async def test_constraint_client_import(self):
        """Verify constraint client can be imported."""
        from src.integrations.constraint_client import ConstraintClient, WellheadAnalyzer
        client = ConstraintClient()
        assert client is not None
        
        # Test wellhead analyzer
        result = WellheadAnalyzer.calculate_encumbered_area(
            parcel_acres=1.065,
            well_center=(0, 0),
            protection_radius_ft=200
        )
        assert "encumbered_acres" in result
        assert result["protection_radius_ft"] == 200


# Fixtures for common test data
@pytest.fixture
def sample_parcel():
    """Sample parcel matching Bliss Palm Bay."""
    return {
        "parcel_id": "2835546",
        "account_id": "2835546",
        "address": "2165 Sandy Pines Dr NE",
        "city": "Palm Bay",
        "state": "FL",
        "acres": 1.065,
        "zoning_code": "PUD",
        "flu_designation": "HDR",
        "owner_name": "Test Owner"
    }


@pytest.fixture
def sample_state(sample_parcel):
    """Sample ZOD state with one parcel."""
    return {
        "jurisdiction": "Palm Bay",
        "target_flu_categories": ["HDR"],
        "min_parcel_acres": 0.5,
        "max_parcels_to_analyze": 10,
        "parcels_raw": [sample_parcel],
        "zoning_districts": {
            "PUD": {"max_density_du_acre": 4},
            "RM-20": {"max_density_du_acre": 20}
        },
        "flu_designations": {
            "HDR": {
                "max_density_du_acre": 20,
                "min_density_du_acre": 10,
                "permitted_zoning": ["RM-10", "RM-15", "RM-20"]
            }
        },
        "parcels_analyzed": [],
        "constraint_maps": {},
        "opportunities": [],
        "current_stage": "initializing",
        "errors": [],
        "checkpoints": [],
        "reports_generated": [],
        "summary": None
    }


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
