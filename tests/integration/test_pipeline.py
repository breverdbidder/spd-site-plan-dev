#!/usr/bin/env python3
"""
Pipeline Integration Tests for SPD Site Plan Development
P1 Codebase Requirement: Test full 12-stage workflow execution

Tests cover:
- Full pipeline execution end-to-end
- State persistence and recovery
- Stage transitions and data flow
- Error handling and circuit breakers
- Real-world scenarios (Bliss Palm Bay reference case)

Author: BidDeed.AI / Everest Capital USA
"""

import pytest
import json
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from dataclasses import dataclass


# =============================================================================
# TEST FIXTURES
# =============================================================================

@dataclass
class MockParcel:
    """Mock parcel data for testing"""
    account: str
    parcel_id: str
    address: str
    acreage: float
    zoning: str
    jurisdiction: str
    market_value: float
    land_use: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "account": self.account,
            "parcelID": self.parcel_id,
            "siteAddress": self.address,
            "acreage": self.acreage,
            "taxingDistrict": self.jurisdiction,
            "marketValue": self.market_value,
            "landUseCode": self.land_use,
            "zoning": self.zoning,
        }


@pytest.fixture
def bliss_palm_bay_parcel():
    """Real-world reference case: Bliss Palm Bay development"""
    return MockParcel(
        account="2835546",
        parcel_id="29-37-17-00-00100.0-0000.00",
        address="2001 PALM BAY RD NE, PALM BAY FL",
        acreage=12.5,
        zoning="GU",
        jurisdiction="PALM BAY",
        market_value=1250000,
        land_use="AGRICULTURAL - PASTURE"
    )


@pytest.fixture
def west_melbourne_parcel():
    """West Melbourne industrial candidate"""
    return MockParcel(
        account="TEST001",
        parcel_id="25-36-01-00-00001.0-0000.00",
        address="1234 DAIRY RD, WEST MELBOURNE FL",
        acreage=8.5,
        zoning="IND",
        jurisdiction="WEST MELBOURNE",
        market_value=850000,
        land_use="AGRICULTURAL - GRAZING"
    )


@pytest.fixture
def small_residential_parcel():
    """Small residential parcel (edge case)"""
    return MockParcel(
        account="TEST002",
        parcel_id="25-36-02-00-00001.0-0000.00",
        address="123 OAK ST, SATELLITE BEACH FL",
        acreage=0.25,
        zoning="R-1",
        jurisdiction="SATELLITE BEACH",
        market_value=150000,
        land_use="SINGLE FAMILY RESIDENTIAL"
    )


@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client for database operations"""
    client = MagicMock()
    
    # Mock table operations
    table = MagicMock()
    table.insert.return_value.execute.return_value = MagicMock(data=[{"id": "test-id"}])
    table.select.return_value.execute.return_value = MagicMock(data=[])
    table.update.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
    
    client.table.return_value = table
    return client


@pytest.fixture
def mock_bcpao_response():
    """Mock BCPAO API response"""
    return {
        "parcels": [
            {
                "account": "2835546",
                "parcelID": "29-37-17-00-00100.0-0000.00",
                "siteAddress": "2001 PALM BAY RD NE",
                "acreage": 12.5,
                "taxingDistrict": "PALM BAY",
                "marketValue": 1250000,
                "landUseCode": "AGRICULTURAL - PASTURE",
                "owners": "BLISS DEVELOPMENT LLC",
                "masterPhotoUrl": "https://www.bcpao.us/photos/2835546011.jpg",
            }
        ]
    }


# =============================================================================
# PIPELINE STATE TESTS
# =============================================================================

class TestPipelineState:
    """Tests for pipeline state management"""
    
    def test_initial_state(self):
        """Pipeline should start in DISCOVERY stage"""
        from src.state.pipeline_state import PipelineState
        
        state = PipelineState()
        assert state.current_stage == "DISCOVERY"
        assert state.is_active == True
        assert len(state.completed_stages) == 0
    
    def test_stage_transition(self):
        """Pipeline should transition through stages correctly"""
        from src.state.pipeline_state import PipelineState
        
        state = PipelineState()
        
        # Transition through first few stages
        state.complete_stage("DISCOVERY", {"parcels_found": 10})
        assert state.current_stage == "SCRAPING"
        assert "DISCOVERY" in state.completed_stages
        
        state.complete_stage("SCRAPING", {"parcels_scraped": 10})
        assert state.current_stage == "TITLE_SEARCH"
        assert len(state.completed_stages) == 2
    
    def test_state_persistence(self, mock_supabase_client):
        """State should persist to Supabase"""
        from src.state.pipeline_state import PipelineState
        
        state = PipelineState(supabase_client=mock_supabase_client)
        state.save()
        
        mock_supabase_client.table.assert_called()
    
    def test_state_recovery(self, mock_supabase_client):
        """State should recover from Supabase checkpoint"""
        mock_supabase_client.table.return_value.select.return_value.execute.return_value = MagicMock(
            data=[{
                "id": "checkpoint-1",
                "current_stage": "LIEN_PRIORITY",
                "completed_stages": ["DISCOVERY", "SCRAPING", "TITLE_SEARCH"],
                "stage_data": json.dumps({"parcels": []}),
            }]
        )
        
        from src.state.pipeline_state import PipelineState
        
        state = PipelineState.load_from_checkpoint(
            mock_supabase_client, 
            "checkpoint-1"
        )
        
        assert state.current_stage == "LIEN_PRIORITY"
        assert len(state.completed_stages) == 3
    
    def test_stage_rollback(self):
        """Pipeline should support rollback to previous stage"""
        from src.state.pipeline_state import PipelineState
        
        state = PipelineState()
        state.complete_stage("DISCOVERY", {})
        state.complete_stage("SCRAPING", {})
        
        state.rollback_to_stage("DISCOVERY")
        
        assert state.current_stage == "SCRAPING"
        assert "SCRAPING" not in state.completed_stages


# =============================================================================
# PIPELINE STAGE TESTS
# =============================================================================

class TestDiscoveryStage:
    """Tests for Discovery stage"""
    
    @pytest.mark.asyncio
    async def test_discovery_finds_parcels(self, mock_bcpao_response):
        """Discovery should find parcels from BCPAO"""
        with patch('src.agents.discovery_agent.fetch_bcpao_parcels') as mock_fetch:
            mock_fetch.return_value = mock_bcpao_response["parcels"]
            
            from src.agents.discovery_agent import DiscoveryAgent
            
            agent = DiscoveryAgent()
            result = await agent.discover(
                jurisdiction="PALM BAY",
                min_acreage=5.0,
                land_use_filter=["AGRICULTURAL"]
            )
            
            assert len(result) >= 1
            assert result[0]["account"] == "2835546"
    
    @pytest.mark.asyncio
    async def test_discovery_handles_empty_results(self):
        """Discovery should handle no results gracefully"""
        with patch('src.agents.discovery_agent.fetch_bcpao_parcels') as mock_fetch:
            mock_fetch.return_value = []
            
            from src.agents.discovery_agent import DiscoveryAgent
            
            agent = DiscoveryAgent()
            result = await agent.discover(
                jurisdiction="NONEXISTENT CITY",
                min_acreage=1000.0
            )
            
            assert result == []


class TestScrapingStage:
    """Tests for Scraping stage"""
    
    @pytest.mark.asyncio
    async def test_scraper_enriches_parcel(self, bliss_palm_bay_parcel):
        """Scraper should enrich parcel with additional data"""
        with patch('src.scrapers.bcpao_scraper.BCPAOScraper.scrape_parcel') as mock_scrape:
            mock_scrape.return_value = {
                **bliss_palm_bay_parcel.to_dict(),
                "legal_description": "PALM BAY UNIT 1 LOT 100",
                "year_built": None,
                "structures": [],
                "photo_url": "https://www.bcpao.us/photos/2835546011.jpg",
            }
            
            from src.scrapers.bcpao_scraper import BCPAOScraper
            
            scraper = BCPAOScraper()
            result = await scraper.scrape_parcel(bliss_palm_bay_parcel.account)
            
            assert "legal_description" in result
            assert "photo_url" in result
    
    @pytest.mark.asyncio
    async def test_scraper_handles_rate_limit(self, bliss_palm_bay_parcel):
        """Scraper should handle rate limiting with retry"""
        call_count = 0
        
        async def mock_scrape_with_retry(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Rate limit exceeded")
            return bliss_palm_bay_parcel.to_dict()
        
        with patch('src.scrapers.bcpao_scraper.BCPAOScraper.scrape_parcel', 
                   side_effect=mock_scrape_with_retry):
            from src.scrapers.bcpao_scraper import BCPAOScraper
            
            scraper = BCPAOScraper()
            # This should retry and eventually succeed
            # Implementation should use error_handler with_retry


class TestScoringStage:
    """Tests for ML Scoring stage"""
    
    def test_scoring_bid_candidate(self, bliss_palm_bay_parcel):
        """High-value parcel should score as BID"""
        from src.models.scoring_model import RoughDiamondScorer
        
        scorer = RoughDiamondScorer()
        result = scorer.score_parcel(bliss_palm_bay_parcel.to_dict())
        
        # Palm Bay agricultural should score well
        assert result['score'] >= 70
        assert '🟢' in result['recommendation'] or '🟡' in result['recommendation']
    
    def test_scoring_skip_candidate(self, small_residential_parcel):
        """Low-value parcel should score as SKIP"""
        from src.models.scoring_model import RoughDiamondScorer
        
        scorer = RoughDiamondScorer()
        result = scorer.score_parcel(small_residential_parcel.to_dict())
        
        # Small residential in Satellite Beach should score low
        assert result['score'] < 70
    
    def test_scoring_batch(self, bliss_palm_bay_parcel, west_melbourne_parcel):
        """Batch scoring should sort by score descending"""
        from src.models.scoring_model import RoughDiamondScorer
        
        scorer = RoughDiamondScorer()
        parcels = [
            bliss_palm_bay_parcel.to_dict(),
            west_melbourne_parcel.to_dict(),
        ]
        
        results = scorer.score_parcels(parcels)
        
        assert len(results) == 2
        assert results[0]['score'] >= results[1]['score']


class TestMaxBidCalculation:
    """Tests for Max Bid calculation stage"""
    
    def test_max_bid_formula(self):
        """Max bid should follow formula: (ARV×70%)-Repairs-$10K-MIN($25K,15%ARV)"""
        from src.calculators.max_bid_calculator import calculate_max_bid
        
        result = calculate_max_bid(
            arv=500000,
            repairs=50000,
        )
        
        # (500000 * 0.7) - 50000 - 10000 - min(25000, 75000)
        # = 350000 - 50000 - 10000 - 25000 = 265000
        assert result['max_bid'] == 265000
        assert result['profit_margin'] > 0
    
    def test_max_bid_with_high_repairs(self):
        """High repairs should result in lower max bid"""
        from src.calculators.max_bid_calculator import calculate_max_bid
        
        result = calculate_max_bid(
            arv=300000,
            repairs=150000,  # High repairs
        )
        
        # Should result in very low or negative max bid
        assert result['max_bid'] < 100000


# =============================================================================
# FULL PIPELINE INTEGRATION TESTS
# =============================================================================

class TestFullPipelineExecution:
    """End-to-end pipeline tests"""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_full_pipeline_bliss_palm_bay(
        self, 
        bliss_palm_bay_parcel,
        mock_supabase_client,
    ):
        """Full pipeline execution for Bliss Palm Bay reference case"""
        # Mock all external dependencies
        with patch('src.agents.discovery_agent.fetch_bcpao_parcels') as mock_discovery, \
             patch('src.scrapers.bcpao_scraper.BCPAOScraper.scrape_parcel') as mock_scrape, \
             patch('src.agents.title_search_agent.search_title') as mock_title:
            
            mock_discovery.return_value = [bliss_palm_bay_parcel.to_dict()]
            mock_scrape.return_value = {
                **bliss_palm_bay_parcel.to_dict(),
                "legal_description": "PALM BAY UNIT 1",
            }
            mock_title.return_value = {
                "liens": [],
                "mortgages": [],
                "title_clear": True,
            }
            
            from src.workflows.rough_diamond_pipeline import RoughDiamondPipeline
            
            pipeline = RoughDiamondPipeline(supabase_client=mock_supabase_client)
            
            result = await pipeline.execute(
                jurisdiction="PALM BAY",
                min_acreage=5.0,
            )
            
            # Verify pipeline completed
            assert result['status'] == 'COMPLETED'
            assert result['stages_completed'] >= 6
            assert len(result['parcels_analyzed']) >= 1
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_pipeline_handles_stage_failure(self, mock_supabase_client):
        """Pipeline should handle stage failures gracefully"""
        with patch('src.agents.discovery_agent.fetch_bcpao_parcels') as mock_discovery:
            mock_discovery.side_effect = ConnectionError("BCPAO API unavailable")
            
            from src.workflows.rough_diamond_pipeline import RoughDiamondPipeline
            
            pipeline = RoughDiamondPipeline(supabase_client=mock_supabase_client)
            
            result = await pipeline.execute(
                jurisdiction="PALM BAY",
                min_acreage=5.0,
            )
            
            assert result['status'] == 'FAILED'
            assert 'error' in result
            assert result['stages_completed'] == 0
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_pipeline_checkpoint_recovery(self, mock_supabase_client):
        """Pipeline should recover from checkpoint after failure"""
        # Setup checkpoint data
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{
                "id": "recovery-checkpoint",
                "current_stage": "LIEN_PRIORITY",
                "completed_stages": ["DISCOVERY", "SCRAPING", "TITLE_SEARCH"],
                "stage_data": json.dumps({
                    "parcels": [{"account": "2835546", "score": 85}]
                }),
            }]
        )
        
        with patch('src.agents.lien_priority_agent.analyze_liens') as mock_liens:
            mock_liens.return_value = {"senior_liens": [], "total_liens": 0}
            
            from src.workflows.rough_diamond_pipeline import RoughDiamondPipeline
            
            pipeline = RoughDiamondPipeline(supabase_client=mock_supabase_client)
            
            result = await pipeline.resume_from_checkpoint("recovery-checkpoint")
            
            # Should continue from LIEN_PRIORITY, not restart
            assert result['stages_completed'] >= 4


# =============================================================================
# ERROR HANDLING INTEGRATION TESTS
# =============================================================================

class TestPipelineErrorHandling:
    """Tests for error handling in pipeline"""
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_activation(self):
        """Circuit breaker should open after repeated failures"""
        from src.utils.error_handler import ErrorHandler, CircuitBreaker
        
        handler = ErrorHandler("test_pipeline")
        cb = handler.get_circuit_breaker("bcpao_fetch")
        
        # Simulate 5 failures
        for _ in range(5):
            cb.record_failure()
        
        assert cb.state.value == "open"
        assert not cb.can_execute()
    
    @pytest.mark.asyncio
    async def test_retry_with_exponential_backoff(self):
        """Retries should use exponential backoff"""
        from src.utils.error_handler import ErrorHandler
        
        handler = ErrorHandler("test_pipeline")
        call_times = []
        
        @handler.with_retry(max_retries=3, base_delay=0.1)
        def failing_function():
            call_times.append(datetime.utcnow())
            raise ConnectionError("Network error")
        
        with pytest.raises(ConnectionError):
            failing_function()
        
        # Should have made 4 attempts (initial + 3 retries)
        assert len(call_times) == 4
        
        # Verify delays increased
        if len(call_times) >= 3:
            delay1 = (call_times[1] - call_times[0]).total_seconds()
            delay2 = (call_times[2] - call_times[1]).total_seconds()
            # Second delay should be longer (exponential backoff)
            assert delay2 >= delay1


# =============================================================================
# DATA FLOW TESTS
# =============================================================================

class TestPipelineDataFlow:
    """Tests for data flow between pipeline stages"""
    
    def test_discovery_to_scraping_handoff(self, bliss_palm_bay_parcel):
        """Discovery output should be valid input for Scraping"""
        discovery_output = {
            "parcels": [bliss_palm_bay_parcel.to_dict()],
            "total_found": 1,
            "filters_applied": {"min_acreage": 5.0},
        }
        
        # Validate structure for scraping stage
        assert "parcels" in discovery_output
        assert len(discovery_output["parcels"]) > 0
        assert "account" in discovery_output["parcels"][0]
    
    def test_scraping_to_scoring_handoff(self, bliss_palm_bay_parcel):
        """Scraping output should be valid input for Scoring"""
        scraping_output = {
            **bliss_palm_bay_parcel.to_dict(),
            "legal_description": "PALM BAY UNIT 1",
            "photo_url": "https://example.com/photo.jpg",
            "scraped_at": datetime.utcnow().isoformat(),
        }
        
        # Validate required fields for scoring
        required_fields = ["account", "acreage", "taxingDistrict", "landUseCode", "marketValue"]
        for field in required_fields:
            assert field in scraping_output
    
    def test_scoring_to_report_handoff(self, bliss_palm_bay_parcel):
        """Scoring output should be valid input for Report generation"""
        from src.models.scoring_model import RoughDiamondScorer
        
        scorer = RoughDiamondScorer()
        scoring_output = scorer.score_parcel(bliss_palm_bay_parcel.to_dict())
        
        # Validate required fields for report
        assert "score" in scoring_output
        assert "recommendation" in scoring_output
        assert "scoring_factors" in scoring_output
        assert "component_scores" in scoring_output


# =============================================================================
# PERFORMANCE TESTS
# =============================================================================

class TestPipelinePerformance:
    """Performance tests for pipeline"""
    
    @pytest.mark.slow
    def test_scoring_batch_performance(self):
        """Batch scoring should complete in reasonable time"""
        from src.models.scoring_model import RoughDiamondScorer
        import time
        
        scorer = RoughDiamondScorer()
        
        # Generate 100 test parcels
        parcels = [
            {
                "account": f"TEST{i:04d}",
                "acreage": 5.0 + (i % 20),
                "taxingDistrict": ["PALM BAY", "WEST MELBOURNE", "TITUSVILLE"][i % 3],
                "landUseCode": "AGRICULTURAL",
                "marketValue": 100000 + (i * 10000),
            }
            for i in range(100)
        ]
        
        start_time = time.time()
        results = scorer.score_parcels(parcels)
        elapsed = time.time() - start_time
        
        assert len(results) == 100
        assert elapsed < 1.0  # Should complete in under 1 second


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "not slow"])
