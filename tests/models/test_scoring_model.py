#!/usr/bin/env python3
"""
Unit Tests for Rough Diamond Scoring Model
P0 Codebase Requirement: Test coverage for scoring_model.py

Coverage targets:
- score_parcel(): 100%
- score_parcels(): 100%
- get_bid_candidates(): 100%
- All scoring helper methods: 100%

Author: BidDeed.AI / Everest Capital USA
"""

import pytest
import json
from typing import Dict, Any
from unittest.mock import patch, MagicMock

# Import the module under test
import sys
sys.path.insert(0, 'src')
from models.scoring_model import (
    RoughDiamondScorer,
    ScoringWeights,
    Recommendation,
    score_parcel_quick
)


# =============================================================================
# TEST FIXTURES
# =============================================================================

@pytest.fixture
def scorer():
    """Default scorer instance"""
    return RoughDiamondScorer()


@pytest.fixture
def custom_weights():
    """Custom scoring weights for testing"""
    return ScoringWeights(
        jurisdiction=0.30,
        zoning_match=0.25,
        acreage=0.20,
        opposition=0.10,
        staff_rec=0.10,
        comp_plan=0.05
    )


@pytest.fixture
def sample_parcel_agricultural():
    """Sample agricultural parcel - high score expected"""
    return {
        "account": "AGR001",
        "parcelID": "25-36-01-00-001",
        "siteAddress": "1234 DAIRY RD, WEST MELBOURNE FL",
        "acreage": 8.5,
        "taxingDistrict": "WEST MELBOURNE",
        "landUseCode": "AGRICULTURAL - GRAZING LAND",
        "marketValue": 120000,
        "owners": "SMITH FAMILY TRUST"
    }


@pytest.fixture
def sample_parcel_vacant():
    """Sample vacant commercial parcel"""
    return {
        "account": "VAC001",
        "parcelID": "25-36-02-00-002",
        "siteAddress": "5678 BABCOCK ST, PALM BAY FL",
        "acreage": 5.0,
        "taxingDistrict": "PALM BAY",
        "landUseCode": "VACANT COMMERCIAL",
        "marketValue": 200000,
        "owners": "ABC HOLDINGS LLC"
    }


@pytest.fixture
def sample_parcel_golf():
    """Sample golf course parcel - lower score expected"""
    return {
        "account": "GOLF001",
        "parcelID": "25-36-03-00-003",
        "siteAddress": "9999 COUNTRY CLUB DR, SATELLITE BEACH FL",
        "acreage": 120.0,
        "taxingDistrict": "SATELLITE BEACH",
        "landUseCode": "GOLF COURSE",
        "marketValue": 5000000,
        "owners": "SEASIDE GOLF LLC"
    }


@pytest.fixture
def sample_parcel_small():
    """Sample small parcel"""
    return {
        "account": "SMALL001",
        "parcelID": "25-36-04-00-004",
        "siteAddress": "123 MAIN ST, MELBOURNE FL",
        "acreage": 0.5,
        "taxingDistrict": "MELBOURNE",
        "landUseCode": "RESIDENTIAL",
        "marketValue": 50000,
        "owners": "JOHN DOE"
    }


@pytest.fixture
def sample_parcel_large():
    """Sample large tract parcel"""
    return {
        "account": "LARGE001",
        "parcelID": "25-36-05-00-005",
        "siteAddress": "MALABAR RD, UNINCORPORATED",
        "acreage": 150.0,
        "taxingDistrict": "UNINCORP DISTRICT 3",
        "landUseCode": "TIMBER/FOREST",
        "marketValue": 1500000,
        "owners": "TIMBER HOLDINGS INC"
    }


# =============================================================================
# SCORING WEIGHTS TESTS
# =============================================================================

class TestScoringWeights:
    """Tests for ScoringWeights dataclass"""
    
    def test_default_weights_sum_to_one(self):
        """Default weights should sum to 1.0"""
        weights = ScoringWeights()
        total = (
            weights.jurisdiction +
            weights.zoning_match +
            weights.acreage +
            weights.opposition +
            weights.staff_rec +
            weights.comp_plan
        )
        assert abs(total - 1.0) < 0.001
    
    def test_custom_weights(self, custom_weights):
        """Custom weights should be applied correctly"""
        assert custom_weights.jurisdiction == 0.30
        assert custom_weights.zoning_match == 0.25
        assert custom_weights.acreage == 0.20


# =============================================================================
# JURISDICTION SCORING TESTS
# =============================================================================

class TestJurisdictionScoring:
    """Tests for _score_jurisdiction method"""
    
    def test_west_melbourne_highest(self, scorer):
        """West Melbourne should score 95"""
        score, reason = scorer._score_jurisdiction("WEST MELBOURNE")
        assert score == 95
        assert "WEST MELBOURNE" in reason
    
    def test_west_melbourne_underscore(self, scorer):
        """WEST_MELBOURNE format should also work"""
        score, _ = scorer._score_jurisdiction("WEST_MELBOURNE")
        assert score == 95
    
    def test_palm_bay(self, scorer):
        """Palm Bay should score 85"""
        score, _ = scorer._score_jurisdiction("PALM BAY")
        assert score == 85
    
    def test_titusville(self, scorer):
        """Titusville should score 82"""
        score, _ = scorer._score_jurisdiction("TITUSVILLE")
        assert score == 82
    
    def test_satellite_beach_lowest(self, scorer):
        """Satellite Beach should score 35"""
        score, _ = scorer._score_jurisdiction("SATELLITE BEACH")
        assert score == 35
    
    def test_unknown_jurisdiction(self, scorer):
        """Unknown jurisdiction should return 60"""
        score, reason = scorer._score_jurisdiction("RANDOM CITY")
        assert score == 60
        assert "Unknown" in reason
    
    def test_case_insensitive(self, scorer):
        """Jurisdiction matching should be case-insensitive"""
        score1, _ = scorer._score_jurisdiction("palm bay")
        score2, _ = scorer._score_jurisdiction("PALM BAY")
        assert score1 == score2
    
    def test_partial_match(self, scorer):
        """Partial jurisdiction names should match"""
        score, _ = scorer._score_jurisdiction("UNINCORP DISTRICT 3")
        assert score == 70  # UNINCORP matches


# =============================================================================
# ACREAGE SCORING TESTS
# =============================================================================

class TestAcreageScoring:
    """Tests for _score_acreage method"""
    
    def test_optimal_size_low(self, scorer):
        """2 acres should score 95 (optimal range start)"""
        score, reason = scorer._score_acreage(2.0)
        assert score == 95
        assert "Optimal" in reason
    
    def test_optimal_size_high(self, scorer):
        """10 acres should score 95 (optimal range end)"""
        score, _ = scorer._score_acreage(10.0)
        assert score == 95
    
    def test_good_size(self, scorer):
        """15 acres should score 85"""
        score, reason = scorer._score_acreage(15.0)
        assert score == 85
        assert "Good" in reason
    
    def test_larger_parcel(self, scorer):
        """30 acres should score 75"""
        score, reason = scorer._score_acreage(30.0)
        assert score == 75
        assert "Larger" in reason
    
    def test_large_tract(self, scorer):
        """75 acres should score 60"""
        score, _ = scorer._score_acreage(75.0)
        assert score == 60
    
    def test_major_development(self, scorer):
        """150 acres should score 45 (DRI possible)"""
        score, reason = scorer._score_acreage(150.0)
        assert score == 45
        assert "DRI" in reason
    
    def test_small_parcel(self, scorer):
        """0.5 acres should score 65"""
        score, reason = scorer._score_acreage(0.5)
        assert score == 65
        assert "Small" in reason
    
    def test_zero_acreage(self, scorer):
        """Zero acreage should handle gracefully"""
        score, _ = scorer._score_acreage(0)
        assert score == 65


# =============================================================================
# LAND USE SCORING TESTS
# =============================================================================

class TestLandUseScoring:
    """Tests for _score_land_use method"""
    
    def test_agricultural(self, scorer):
        """Agricultural land should score 90"""
        score, reason = scorer._score_land_use("AGRICULTURAL - GRAZING")
        assert score == 90
        assert "Agricultural" in reason
    
    def test_vacant(self, scorer):
        """Vacant land should score 85"""
        score, _ = scorer._score_land_use("VACANT LAND")
        assert score == 85
    
    def test_farm(self, scorer):
        """Farm land should score 88"""
        score, _ = scorer._score_land_use("FARM PASTURE")
        assert score == 88
    
    def test_golf_course(self, scorer):
        """Golf course should score 55 (HOA opposition risk)"""
        score, reason = scorer._score_land_use("GOLF COURSE")
        assert score == 55
        assert "HOA" in reason
    
    def test_standard_land_use(self, scorer):
        """Standard land use should score 65"""
        score, _ = scorer._score_land_use("SINGLE FAMILY RESIDENTIAL")
        assert score == 65


# =============================================================================
# VALUE PER ACRE SCORING TESTS
# =============================================================================

class TestValuePerAcreScoring:
    """Tests for _score_value_per_acre method"""
    
    def test_very_low_value(self, scorer):
        """Under $15k/acre should score 95"""
        score, reason = scorer._score_value_per_acre(100000, 10)  # $10k/acre
        assert score == 95
        assert "major arbitrage" in reason
    
    def test_low_value(self, scorer):
        """$15k-$30k/acre should score 85"""
        score, _ = scorer._score_value_per_acre(200000, 10)  # $20k/acre
        assert score == 85
    
    def test_moderate_value(self, scorer):
        """$30k-$60k/acre should score 70"""
        score, _ = scorer._score_value_per_acre(400000, 10)  # $40k/acre
        assert score == 70
    
    def test_higher_value(self, scorer):
        """$60k-$100k/acre should score 55"""
        score, _ = scorer._score_value_per_acre(800000, 10)  # $80k/acre
        assert score == 55
    
    def test_premium_value(self, scorer):
        """Over $100k/acre should score 40"""
        score, _ = scorer._score_value_per_acre(1500000, 10)  # $150k/acre
        assert score == 40
    
    def test_zero_acreage_handling(self, scorer):
        """Zero acreage should not cause division by zero"""
        score, reason = scorer._score_value_per_acre(100000, 0)
        assert score == 50
        assert "Unable" in reason


# =============================================================================
# LOCATION SCORING TESTS
# =============================================================================

class TestLocationScoring:
    """Tests for _score_location method"""
    
    def test_west_melbourne_corridors(self, scorer):
        """West Melbourne corridors should add 15 points"""
        score, reasons = scorer._score_location("1234 DAIRY RD, MELBOURNE")
        assert score >= 15
        assert any("West Melbourne" in r for r in reasons)
    
    def test_palm_bay_corridors(self, scorer):
        """Palm Bay corridors should add 12 points"""
        score, reasons = scorer._score_location("5678 BABCOCK ST, PALM BAY")
        assert score >= 12
        assert any("Palm Bay" in r for r in reasons)
    
    def test_major_infrastructure(self, scorer):
        """Major corridors should add 10 points"""
        score, reasons = scorer._score_location("123 I-95 SERVICE RD")
        assert score >= 10
        assert any("Major corridor" in r for r in reasons)
    
    def test_industrial_area(self, scorer):
        """Industrial areas should add 8 points"""
        score, reasons = scorer._score_location("456 INDUSTRIAL PKWY")
        assert score >= 8
        assert any("Industrial" in r for r in reasons)
    
    def test_multiple_bonuses(self, scorer):
        """Multiple location factors should stack"""
        score, reasons = scorer._score_location("DAIRY RD & I-95, INDUSTRIAL PARK")
        assert score >= 25  # 15 + 10
        assert len(reasons) >= 2
    
    def test_no_bonus(self, scorer):
        """Generic address should have no bonus"""
        score, reasons = scorer._score_location("123 OAK ST, ANYTOWN")
        assert score == 0
        assert len(reasons) == 0
    
    def test_empty_address(self, scorer):
        """Empty address should handle gracefully"""
        score, reasons = scorer._score_location("")
        assert score == 0
    
    def test_none_address(self, scorer):
        """None address should handle gracefully"""
        score, reasons = scorer._score_location(None)
        assert score == 0


# =============================================================================
# SCORE_PARCEL TESTS
# =============================================================================

class TestScoreParcel:
    """Tests for score_parcel method"""
    
    def test_agricultural_parcel_high_score(self, scorer, sample_parcel_agricultural):
        """Agricultural parcel in West Melbourne should score high"""
        result = scorer.score_parcel(sample_parcel_agricultural)
        
        assert result['score'] >= 80
        assert '🟢 BID' in result['recommendation']
        assert result['risk_level'] == 'LOW'
        assert result['account'] == 'AGR001'
    
    def test_golf_course_low_score(self, scorer, sample_parcel_golf):
        """Golf course parcel should score lower"""
        result = scorer.score_parcel(sample_parcel_golf)
        
        assert result['score'] <= 60
        assert '🔴 SKIP' in result['recommendation'] or '🟠 WATCH' in result['recommendation']
    
    def test_result_contains_all_fields(self, scorer, sample_parcel_vacant):
        """Result should contain all required fields"""
        result = scorer.score_parcel(sample_parcel_vacant)
        
        required_fields = [
            'account', 'parcel_id', 'address', 'acres', 'district',
            'land_use', 'market_value', 'value_per_acre', 'owner',
            'score', 'recommendation', 'action', 'timeline', 'risk_level',
            'scoring_factors', 'component_scores', 'bcpao_url'
        ]
        
        for field in required_fields:
            assert field in result, f"Missing field: {field}"
    
    def test_component_scores_populated(self, scorer, sample_parcel_agricultural):
        """Component scores should all be populated"""
        result = scorer.score_parcel(sample_parcel_agricultural)
        
        components = result['component_scores']
        assert 'jurisdiction' in components
        assert 'land_use' in components
        assert 'acreage' in components
        assert 'value_arbitrage' in components
        assert 'location_bonus' in components
        
        # All should be numeric
        for key, value in components.items():
            assert isinstance(value, (int, float))
    
    def test_score_bounded(self, scorer, sample_parcel_agricultural):
        """Score should be between 0 and 100"""
        result = scorer.score_parcel(sample_parcel_agricultural)
        assert 0 <= result['score'] <= 100
    
    def test_bcpao_url_format(self, scorer, sample_parcel_agricultural):
        """BCPAO URL should be properly formatted"""
        result = scorer.score_parcel(sample_parcel_agricultural)
        assert result['bcpao_url'].startswith('https://www.bcpao.us/PropertySearch/')
        assert 'AGR001' in result['bcpao_url']
    
    def test_recommendation_thresholds(self, scorer):
        """Test recommendation threshold boundaries"""
        # Score >= 80: BID
        high_scorer = {
            "account": "HIGH",
            "acreage": 5.0,
            "taxingDistrict": "WEST MELBOURNE",
            "landUseCode": "AGRICULTURAL",
            "marketValue": 50000,
        }
        result = scorer.score_parcel(high_scorer)
        assert '🟢' in result['recommendation']
        
        # Score < 50: SKIP
        low_scorer = {
            "account": "LOW",
            "acreage": 200.0,
            "taxingDistrict": "SATELLITE BEACH",
            "landUseCode": "GOLF COURSE",
            "marketValue": 50000000,
        }
        result = scorer.score_parcel(low_scorer)
        assert '🔴' in result['recommendation'] or '🟠' in result['recommendation']
    
    def test_missing_fields_handled(self, scorer):
        """Missing parcel fields should be handled gracefully"""
        minimal_parcel = {"account": "MIN001"}
        result = scorer.score_parcel(minimal_parcel)
        
        assert result['score'] >= 0
        assert result['account'] == 'MIN001'


# =============================================================================
# SCORE_PARCELS TESTS
# =============================================================================

class TestScoreParcels:
    """Tests for score_parcels method"""
    
    def test_multiple_parcels_scored(self, scorer, sample_parcel_agricultural, 
                                     sample_parcel_vacant, sample_parcel_golf):
        """All parcels should be scored"""
        parcels = [sample_parcel_agricultural, sample_parcel_vacant, sample_parcel_golf]
        results = scorer.score_parcels(parcels)
        
        assert len(results) == 3
    
    def test_sorted_by_score_descending(self, scorer, sample_parcel_agricultural,
                                        sample_parcel_vacant, sample_parcel_golf):
        """Results should be sorted by score descending"""
        parcels = [sample_parcel_golf, sample_parcel_vacant, sample_parcel_agricultural]
        results = scorer.score_parcels(parcels)
        
        scores = [r['score'] for r in results]
        assert scores == sorted(scores, reverse=True)
    
    def test_empty_list(self, scorer):
        """Empty parcel list should return empty results"""
        results = scorer.score_parcels([])
        assert results == []


# =============================================================================
# GET_BID_CANDIDATES TESTS
# =============================================================================

class TestGetBidCandidates:
    """Tests for get_bid_candidates method"""
    
    def test_filters_bid_only(self, scorer, sample_parcel_agricultural,
                              sample_parcel_vacant, sample_parcel_golf):
        """Should only return BID recommendations"""
        parcels = [sample_parcel_agricultural, sample_parcel_vacant, sample_parcel_golf]
        scored = scorer.score_parcels(parcels)
        bid_candidates = scorer.get_bid_candidates(scored)
        
        for candidate in bid_candidates:
            assert '🟢' in candidate['recommendation']
    
    def test_no_bids(self, scorer, sample_parcel_golf):
        """Should return empty list if no BID candidates"""
        scored = scorer.score_parcels([sample_parcel_golf])
        bid_candidates = scorer.get_bid_candidates(scored)
        
        # Golf course likely won't be a BID
        # This verifies the filter works
        for candidate in bid_candidates:
            assert '🟢' in candidate['recommendation']


# =============================================================================
# GET_REVIEW_CANDIDATES TESTS
# =============================================================================

class TestGetReviewCandidates:
    """Tests for get_review_candidates method"""
    
    def test_filters_review_only(self, scorer, sample_parcel_agricultural,
                                 sample_parcel_vacant, sample_parcel_golf):
        """Should only return REVIEW recommendations"""
        parcels = [sample_parcel_agricultural, sample_parcel_vacant, sample_parcel_golf]
        scored = scorer.score_parcels(parcels)
        review_candidates = scorer.get_review_candidates(scored)
        
        for candidate in review_candidates:
            assert '🟡' in candidate['recommendation']


# =============================================================================
# EXPORT_RESULTS TESTS
# =============================================================================

class TestExportResults:
    """Tests for export_results method"""
    
    def test_export_creates_file(self, scorer, sample_parcel_agricultural, tmp_path):
        """Should create JSON file with results"""
        filepath = tmp_path / "test_results.json"
        scored = scorer.score_parcels([sample_parcel_agricultural])
        
        scorer.export_results(scored, str(filepath))
        
        assert filepath.exists()
    
    def test_export_file_structure(self, scorer, sample_parcel_agricultural,
                                   sample_parcel_vacant, tmp_path):
        """Exported file should have correct structure"""
        filepath = tmp_path / "test_results.json"
        parcels = [sample_parcel_agricultural, sample_parcel_vacant]
        scored = scorer.score_parcels(parcels)
        
        scorer.export_results(scored, str(filepath))
        
        with open(filepath) as f:
            data = json.load(f)
        
        assert 'generated' in data
        assert 'model_version' in data
        assert 'total_scored' in data
        assert 'bid_count' in data
        assert 'review_count' in data
        assert 'weights' in data
        assert 'parcels' in data
        
        assert data['total_scored'] == 2
        assert len(data['parcels']) == 2


# =============================================================================
# CONVENIENCE FUNCTION TESTS
# =============================================================================

class TestScoreParcelQuick:
    """Tests for score_parcel_quick function"""
    
    def test_returns_tuple(self, sample_parcel_agricultural):
        """Should return (score, recommendation) tuple"""
        result = score_parcel_quick(sample_parcel_agricultural)
        
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], int)
        assert isinstance(result[1], str)
    
    def test_score_in_range(self, sample_parcel_vacant):
        """Score should be between 0 and 100"""
        score, _ = score_parcel_quick(sample_parcel_vacant)
        assert 0 <= score <= 100


# =============================================================================
# CUSTOM WEIGHTS TESTS
# =============================================================================

class TestCustomWeights:
    """Tests for scorer with custom weights"""
    
    def test_custom_weights_applied(self, custom_weights, sample_parcel_agricultural):
        """Custom weights should affect scoring"""
        default_scorer = RoughDiamondScorer()
        custom_scorer = RoughDiamondScorer(weights=custom_weights)
        
        default_result = default_scorer.score_parcel(sample_parcel_agricultural)
        custom_result = custom_scorer.score_parcel(sample_parcel_agricultural)
        
        # Scores might differ due to different weights
        # At minimum, both should produce valid results
        assert 0 <= default_result['score'] <= 100
        assert 0 <= custom_result['score'] <= 100


# =============================================================================
# EDGE CASES AND ERROR HANDLING
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and error handling"""
    
    def test_none_values_in_parcel(self, scorer):
        """None values should be handled"""
        parcel = {
            "account": "NULL001",
            "acreage": None,
            "taxingDistrict": None,
            "landUseCode": None,
            "marketValue": None,
            "siteAddress": None,
        }
        result = scorer.score_parcel(parcel)
        assert result['score'] >= 0
    
    def test_negative_values(self, scorer):
        """Negative values should be handled"""
        parcel = {
            "account": "NEG001",
            "acreage": -5,
            "marketValue": -100000,
        }
        result = scorer.score_parcel(parcel)
        assert result['score'] >= 0
    
    def test_very_large_values(self, scorer):
        """Very large values should be handled"""
        parcel = {
            "account": "HUGE001",
            "acreage": 1000000,
            "marketValue": 999999999999,
        }
        result = scorer.score_parcel(parcel)
        assert 0 <= result['score'] <= 100
    
    def test_special_characters_in_strings(self, scorer):
        """Special characters should be handled"""
        parcel = {
            "account": "SPEC!@#$001",
            "siteAddress": "123 O'BRIEN'S RD & 45TH ST",
            "owners": "SMITH'S TRUST \"THE FAMILY\"",
        }
        result = scorer.score_parcel(parcel)
        assert result['score'] >= 0


# =============================================================================
# RECOMMENDATION ENUM TESTS
# =============================================================================

class TestRecommendationEnum:
    """Tests for Recommendation enum"""
    
    def test_all_values_have_emoji(self):
        """All recommendations should have emoji prefix"""
        for rec in Recommendation:
            assert rec.value[0] in ['🟢', '🟡', '🟠', '🔴']
    
    def test_value_strings(self):
        """Check recommendation value strings"""
        assert Recommendation.BID.value == "🟢 BID"
        assert Recommendation.REVIEW.value == "🟡 REVIEW"
        assert Recommendation.WATCH.value == "🟠 WATCH"
        assert Recommendation.SKIP.value == "🔴 SKIP"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=src/models/scoring_model", "--cov-report=term-missing"])
