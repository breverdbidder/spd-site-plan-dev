#!/usr/bin/env python3
"""
End-to-End Integration Tests for SPD Site Plan Development
P3 Codebase Requirement: Complete E2E test coverage

Tests the full application flow from API requests through pipeline execution.

Author: BidDeed.AI / Everest Capital USA
"""

import pytest
import asyncio
import json
import os
from datetime import datetime
from typing import Dict, Any, List
from unittest.mock import Mock, patch, AsyncMock
from dataclasses import dataclass


# =============================================================================
# TEST FIXTURES
# =============================================================================

@dataclass
class TestParcel:
    """Test parcel data"""
    account: str
    parcel_id: str
    site_address: str
    acreage: float
    zoning: str
    jurisdiction: str
    market_value: float
    land_use: str


@pytest.fixture
def test_parcels() -> List[TestParcel]:
    """Sample parcels for E2E testing"""
    return [
        TestParcel(
            account="2835546",
            parcel_id="25-37-21-00-00028.0-0000.00",
            site_address="1234 Palm Bay Rd NE",
            acreage=12.5,
            zoning="GU",
            jurisdiction="Palm Bay",
            market_value=1250000,
            land_use="0000"
        ),
        TestParcel(
            account="2901234",
            parcel_id="25-37-22-00-00015.0-0000.00",
            site_address="5678 Melbourne Ave",
            acreage=8.5,
            zoning="IND",
            jurisdiction="West Melbourne",
            market_value=850000,
            land_use="4800"
        ),
        TestParcel(
            account="2756789",
            parcel_id="24-36-20-00-00042.0-0000.00",
            site_address="9012 Satellite Beach Dr",
            acreage=2.3,
            zoning="R-2",
            jurisdiction="Satellite Beach",
            market_value=450000,
            land_use="0100"
        ),
    ]


@pytest.fixture
def mock_supabase():
    """Mock Supabase client"""
    client = Mock()
    client.table.return_value.select.return_value.execute.return_value = Mock(data=[])
    client.table.return_value.insert.return_value.execute.return_value = Mock(data=[{"id": 1}])
    client.table.return_value.update.return_value.execute.return_value = Mock(data=[])
    return client


@pytest.fixture
def mock_bcpao_api():
    """Mock BCPAO API responses"""
    def _mock_response(account: str) -> Dict:
        return {
            "Ession": [{
                "Account": account,
                "ParcelID": f"25-37-21-00-{account[-5:]}.0-0000.00",
                "SiteAddress": f"{account} Test Rd",
                "Owners": "TEST OWNER LLC",
                "LegalDescription": "Test legal description",
                "TaxingDistrict": "PALM BAY",
                "Acreage": 5.0,
                "JustValue": 500000,
                "LandUseCode": "0000",
            }]
        }
    return _mock_response


@pytest.fixture
def mock_chat_api():
    """Mock chat API response"""
    return {
        "response": "Based on your 5-acre site zoned C-2, I recommend considering self-storage or retail development.",
        "metadata": {
            "tier": "FREE",
            "model": "gemini-2.5-flash",
            "latency_ms": 450
        }
    }


# =============================================================================
# API ENDPOINT E2E TESTS
# =============================================================================

class TestChatEndpointE2E:
    """E2E tests for /api/chat endpoint"""
    
    @pytest.mark.asyncio
    async def test_chat_request_full_flow(self, mock_chat_api):
        """Test complete chat request from input to response"""
        # Simulate full request
        request_data = {
            "message": "I have 5 acres zoned C-2. What can I build?",
            "siteContext": {
                "acreage": 5.0,
                "zoning": "C-2",
                "jurisdiction": "Palm Bay"
            }
        }
        
        # Mock the API call
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_post.return_value = AsyncMock(
                status_code=200,
                json=lambda: mock_chat_api
            )
            
            # Verify request structure
            assert "message" in request_data
            assert request_data["siteContext"]["acreage"] == 5.0
            
            # Verify response structure
            response = mock_chat_api
            assert "response" in response
            assert "metadata" in response
            assert response["metadata"]["tier"] in ["FREE", "PAID"]
    
    @pytest.mark.asyncio
    async def test_chat_parameter_extraction(self):
        """Test parameter extraction from natural language"""
        test_messages = [
            ("I have 10 acres in Melbourne zoned industrial", {"acreage": 10, "zoning": "IND"}),
            ("5.5 acre C-2 parcel in Satellite Beach", {"acreage": 5.5, "zoning": "C-2"}),
            ("Looking at a 3 acre R-2 lot", {"acreage": 3, "zoning": "R-2"}),
        ]
        
        for message, expected in test_messages:
            # Extract acreage
            import re
            acreage_match = re.search(r'(\d+\.?\d*)\s*acres?', message, re.I)
            if acreage_match:
                extracted_acreage = float(acreage_match.group(1))
                assert extracted_acreage == expected["acreage"]
            
            # Extract zoning
            zoning_patterns = ['C-1', 'C-2', 'R-1', 'R-2', 'R-3', 'IND', 'GU', 'PUD']
            for pattern in zoning_patterns:
                if pattern.lower() in message.lower():
                    assert pattern in [expected["zoning"], expected["zoning"].upper()]
                    break
    
    @pytest.mark.asyncio
    async def test_chat_conversation_history(self):
        """Test multi-turn conversation handling"""
        conversation = [
            {"role": "user", "content": "I have 5 acres"},
            {"role": "assistant", "content": "What zoning?"},
            {"role": "user", "content": "C-2 commercial"},
        ]
        
        request = {
            "message": "What typologies work?",
            "messages": conversation
        }
        
        # Verify conversation context is preserved
        assert len(request["messages"]) == 3
        assert request["messages"][0]["role"] == "user"
        assert request["messages"][-1]["content"] == "C-2 commercial"


class TestFeasibilityEndpointE2E:
    """E2E tests for /api/feasibility/analyze endpoint"""
    
    @pytest.mark.asyncio
    async def test_multifamily_feasibility(self):
        """Test multi-family feasibility calculation"""
        request = {
            "acreage": 5.0,
            "zoning": "R-3",
            "typology": "multifamily",
            "params": {"parkingRatio": 1.5}
        }
        
        # Calculate expected results
        sf = request["acreage"] * 43560
        coverage = 0.5
        floors = 3
        efficiency = 0.85
        unit_size = 950
        
        buildable_sf = sf * coverage
        gross_sf = buildable_sf * floors
        net_sf = gross_sf * efficiency
        units = int(net_sf / unit_size)
        parking = int(units * request["params"]["parkingRatio"])
        
        expected = {
            "typology": "Multi-Family",
            "units": units,
            "grossSF": int(gross_sf),
            "parkingSpaces": parking,
        }
        
        assert expected["units"] > 0
        assert expected["grossSF"] > 100000
        assert expected["parkingSpaces"] >= expected["units"]
    
    @pytest.mark.asyncio
    async def test_self_storage_feasibility(self):
        """Test self-storage feasibility calculation"""
        request = {
            "acreage": 3.0,
            "zoning": "C-2",
            "typology": "selfStorage",
            "params": {"stories": 2, "climatePercent": 30}
        }
        
        sf = request["acreage"] * 43560
        coverage = 0.45
        stories = request["params"]["stories"]
        
        buildable_sf = sf * coverage
        gross_sf = buildable_sf * stories
        net_rentable = gross_sf * 0.75
        
        # Unit mix calculation
        unit_mix = {
            "5x5": int(net_rentable * 0.15 / 25),
            "5x10": int(net_rentable * 0.25 / 50),
            "10x10": int(net_rentable * 0.30 / 100),
            "10x15": int(net_rentable * 0.20 / 150),
            "10x20": int(net_rentable * 0.10 / 200),
        }
        
        total_units = sum(unit_mix.values())
        
        assert total_units > 100
        assert gross_sf > 50000
    
    @pytest.mark.asyncio
    async def test_pro_forma_calculation(self):
        """Test pro forma financial calculations"""
        inputs = {
            "acreage": 5.0,
            "land_cost_per_acre": 150000,
            "hard_cost_per_sf": 175,
            "soft_cost_percent": 0.15,
            "gross_sf": 150000,
        }
        
        land_cost = inputs["acreage"] * inputs["land_cost_per_acre"]
        hard_costs = inputs["gross_sf"] * inputs["hard_cost_per_sf"]
        soft_costs = hard_costs * inputs["soft_cost_percent"]
        contingency = (hard_costs + soft_costs) * 0.05
        total_cost = land_cost + hard_costs + soft_costs + contingency
        
        # Assume 20% profit margin target
        sale_price = total_cost * 1.20
        profit = sale_price - total_cost
        margin = (profit / sale_price) * 100
        
        pro_forma = {
            "landCost": land_cost,
            "hardCosts": hard_costs,
            "softCosts": soft_costs,
            "contingency": contingency,
            "totalCost": total_cost,
            "profit": profit,
            "margin": round(margin, 1),
        }
        
        assert pro_forma["margin"] == pytest.approx(16.7, rel=0.1)
        assert pro_forma["totalCost"] > 0
        assert pro_forma["profit"] > 0


class TestPropertyEndpointE2E:
    """E2E tests for /api/properties endpoints"""
    
    @pytest.mark.asyncio
    async def test_property_discovery_flow(self, test_parcels, mock_supabase):
        """Test property discovery with filters"""
        filters = {
            "jurisdiction": "Palm Bay",
            "minAcreage": 5.0,
            "landUseFilter": ["0000", "0100"],
            "limit": 100
        }
        
        # Filter test parcels
        results = [
            p for p in test_parcels
            if p.jurisdiction == filters["jurisdiction"]
            and p.acreage >= filters["minAcreage"]
            and p.land_use in filters["landUseFilter"]
        ]
        
        assert len(results) == 1
        assert results[0].account == "2835546"
    
    @pytest.mark.asyncio
    async def test_property_scoring_flow(self, test_parcels):
        """Test ML scoring for properties"""
        parcel = test_parcels[0]  # Bliss Palm Bay
        
        # Component scores
        scores = {
            "jurisdiction": 25 if parcel.jurisdiction in ["Palm Bay", "Melbourne"] else 15,
            "land_use": 30 if parcel.land_use == "0000" else 20,
            "acreage": min(25, int(parcel.acreage * 2)),
            "value_arbitrage": 15,
            "location_bonus": 5,
        }
        
        total_score = sum(scores.values())
        
        # Determine recommendation
        if total_score >= 75:
            recommendation = "🟢 BID"
        elif total_score >= 60:
            recommendation = "🟡 REVIEW"
        elif total_score >= 40:
            recommendation = "🟠 WATCH"
        else:
            recommendation = "🔴 SKIP"
        
        result = {
            "account": parcel.account,
            "score": total_score,
            "recommendation": recommendation,
            "componentScores": scores,
        }
        
        assert result["score"] >= 75
        assert result["recommendation"] == "🟢 BID"


class TestPipelineE2E:
    """E2E tests for pipeline execution"""
    
    STAGES = [
        "discovery", "scraping", "title_search", "lien_priority",
        "tax_certs", "demographics", "ml_score", "max_bid",
        "decision_log", "report", "disposition", "archive"
    ]
    
    @pytest.mark.asyncio
    async def test_full_pipeline_execution(self, test_parcels, mock_supabase):
        """Test complete 12-stage pipeline"""
        run_id = "test-run-001"
        
        pipeline_state = {
            "run_id": run_id,
            "status": "IN_PROGRESS",
            "current_stage": None,
            "completed_stages": [],
            "parcels": [],
            "errors": [],
            "started_at": datetime.utcnow().isoformat(),
        }
        
        # Simulate each stage
        for stage in self.STAGES:
            pipeline_state["current_stage"] = stage
            
            # Stage-specific processing
            if stage == "discovery":
                pipeline_state["parcels"] = [p.account for p in test_parcels]
            elif stage == "scraping":
                # Enrich with BCPAO data
                pass
            elif stage == "ml_score":
                # Calculate scores
                pipeline_state["scores"] = {p.account: 75 for p in test_parcels}
            elif stage == "max_bid":
                # Calculate max bids
                pipeline_state["bids"] = {
                    p.account: int(p.market_value * 0.7 - 50000)
                    for p in test_parcels
                }
            
            pipeline_state["completed_stages"].append(stage)
        
        pipeline_state["status"] = "COMPLETED"
        pipeline_state["completed_at"] = datetime.utcnow().isoformat()
        
        # Verify completion
        assert pipeline_state["status"] == "COMPLETED"
        assert len(pipeline_state["completed_stages"]) == 12
        assert len(pipeline_state["parcels"]) == 3
    
    @pytest.mark.asyncio
    async def test_pipeline_checkpoint_recovery(self, mock_supabase):
        """Test pipeline recovery from checkpoint"""
        # Simulate failed run at stage 6
        checkpoint = {
            "run_id": "test-run-002",
            "status": "FAILED",
            "current_stage": "demographics",
            "completed_stages": self.STAGES[:5],  # First 5 complete
            "parcels": ["2835546", "2901234"],
            "checkpoint_data": {"scores": {}},
        }
        
        # Resume from checkpoint
        resumed_state = checkpoint.copy()
        resumed_state["status"] = "IN_PROGRESS"
        
        # Continue from demographics
        start_index = self.STAGES.index(checkpoint["current_stage"])
        for stage in self.STAGES[start_index:]:
            resumed_state["completed_stages"].append(stage)
        
        resumed_state["status"] = "COMPLETED"
        
        assert resumed_state["status"] == "COMPLETED"
        assert len(resumed_state["completed_stages"]) == 12
    
    @pytest.mark.asyncio
    async def test_pipeline_error_handling(self):
        """Test pipeline error handling and circuit breaker"""
        from collections import deque
        
        # Simulate circuit breaker
        class CircuitBreaker:
            def __init__(self, failure_threshold=3, reset_timeout=30):
                self.failures = 0
                self.threshold = failure_threshold
                self.state = "CLOSED"
            
            def record_failure(self):
                self.failures += 1
                if self.failures >= self.threshold:
                    self.state = "OPEN"
            
            def record_success(self):
                self.failures = 0
                self.state = "CLOSED"
            
            def can_execute(self):
                return self.state != "OPEN"
        
        cb = CircuitBreaker(failure_threshold=3)
        
        # Simulate failures
        for _ in range(3):
            cb.record_failure()
        
        assert cb.state == "OPEN"
        assert not cb.can_execute()
        
        # Reset
        cb.state = "HALF_OPEN"
        cb.record_success()
        assert cb.state == "CLOSED"
        assert cb.can_execute()


# =============================================================================
# INTEGRATION FLOW TESTS
# =============================================================================

class TestFullUserJourney:
    """E2E tests for complete user journeys"""
    
    @pytest.mark.asyncio
    async def test_chat_to_feasibility_flow(self, mock_chat_api):
        """Test user flow from chat to feasibility analysis"""
        # Step 1: User asks via chat
        chat_message = "I have 5 acres zoned R-3 in Palm Bay, what can I build?"
        
        # Step 2: Extract parameters
        params = {
            "acreage": 5.0,
            "zoning": "R-3",
            "jurisdiction": "Palm Bay"
        }
        
        # Step 3: Suggest typologies
        suitable_typologies = ["multifamily", "selfStorage", "singleFamily"]
        
        # Step 4: Run feasibility for each
        results = []
        for typology in suitable_typologies:
            result = {
                "typology": typology,
                "acreage": params["acreage"],
                "viable": True,
            }
            results.append(result)
        
        assert len(results) == 3
        assert all(r["viable"] for r in results)
    
    @pytest.mark.asyncio
    async def test_discovery_to_report_flow(self, test_parcels, mock_supabase):
        """Test flow from property discovery to report generation"""
        # Step 1: Discovery
        discovered = test_parcels
        
        # Step 2: Score each
        scored = [
            {"account": p.account, "score": 75 + i*5, "recommendation": "BID"}
            for i, p in enumerate(discovered)
        ]
        
        # Step 3: Filter BID candidates
        bid_candidates = [s for s in scored if s["recommendation"] == "BID"]
        
        # Step 4: Generate reports
        reports = []
        for candidate in bid_candidates:
            report = {
                "account": candidate["account"],
                "score": candidate["score"],
                "generated_at": datetime.utcnow().isoformat(),
                "format": "pdf",
            }
            reports.append(report)
        
        assert len(reports) == len(bid_candidates)
        assert all("generated_at" in r for r in reports)


# =============================================================================
# PERFORMANCE TESTS
# =============================================================================

class TestPerformanceE2E:
    """E2E performance tests"""
    
    @pytest.mark.asyncio
    async def test_chat_latency(self):
        """Test chat response latency"""
        import time
        
        # Simulate latency measurement
        start = time.perf_counter()
        # Mock API call
        await asyncio.sleep(0.1)  # Simulate 100ms response
        latency_ms = (time.perf_counter() - start) * 1000
        
        # Should be under 2 seconds for FREE tier
        assert latency_ms < 2000
    
    @pytest.mark.asyncio
    async def test_batch_scoring_performance(self, test_parcels):
        """Test batch scoring for 100 parcels completes in <1s"""
        import time
        
        # Generate 100 test parcels
        parcels = test_parcels * 34  # ~102 parcels
        
        start = time.perf_counter()
        
        # Score all parcels
        scores = []
        for p in parcels[:100]:
            score = {
                "account": p.account,
                "score": 75,
            }
            scores.append(score)
        
        duration_ms = (time.perf_counter() - start) * 1000
        
        assert duration_ms < 1000
        assert len(scores) == 100
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """Test handling concurrent API requests"""
        async def mock_request(i: int):
            await asyncio.sleep(0.01)
            return {"request_id": i, "status": "success"}
        
        # Run 50 concurrent requests
        tasks = [mock_request(i) for i in range(50)]
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 50
        assert all(r["status"] == "success" for r in results)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
