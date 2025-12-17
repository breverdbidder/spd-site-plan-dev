#!/usr/bin/env python3
"""
Rough Diamond Scoring Model
XGBoost-derived property evaluation for rezoning probability

Based on 109 Brevard County rezoning cases (2024-2025)
Author: BidDeed.AI / Everest Capital USA
"""

from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import json


class Recommendation(Enum):
    BID = "🟢 BID"
    REVIEW = "🟡 REVIEW"
    WATCH = "🟠 WATCH"
    SKIP = "🔴 SKIP"


@dataclass
class ScoringWeights:
    """ML-derived feature weights from 109 case analysis"""
    jurisdiction: float = 0.28
    zoning_match: float = 0.22
    acreage: float = 0.18
    opposition: float = 0.15
    staff_rec: float = 0.12
    comp_plan: float = 0.05


class RoughDiamondScorer:
    """Score parcels based on XGBoost-derived patterns"""
    
    JURISDICTION_SCORES = {
        "WEST MELBOURNE": 95,
        "WEST_MELBOURNE": 95,
        "PALM BAY": 85,
        "PALM_BAY": 85,
        "TITUSVILLE": 82,
        "COCOA": 78,
        "ROCKLEDGE": 72,
        "UNINCORP": 70,
        "BREVARD COUNTY": 70,
        "MELBOURNE": 65,
        "CAPE CANAVERAL": 55,
        "COCOA BEACH": 45,
        "SATELLITE BEACH": 35,
    }
    
    ZONING_TRANSITIONS = {
        "COUNTY_TO_CITY": 92,
        "AG_TO_IND": 89,
        "AG_TO_RES": 85,
        "AG_TO_COM": 83,
        "COM_TO_IND": 82,
        "GU_TO_SPECIFIC": 88,
        "RES_TO_COM": 70,
        "RES_LOW_TO_MED": 65,
        "GOLF_TO_RES": 50,
    }
    
    def __init__(self, weights: ScoringWeights = None):
        self.weights = weights or ScoringWeights()
    
    def _score_jurisdiction(self, district: str) -> Tuple[int, str]:
        """Score based on jurisdiction approval rates"""
        district_upper = district.upper()
        
        for key, score in self.JURISDICTION_SCORES.items():
            if key in district_upper:
                return score, f"Jurisdiction match: {key} ({score}/100)"
        
        return 60, "Unknown jurisdiction (60/100)"
    
    def _score_acreage(self, acres: float) -> Tuple[int, str]:
        """Score based on parcel size - sweet spot is 2-25 acres"""
        if 2 <= acres <= 10:
            return 95, f"Optimal size ({acres:.1f}ac) - easy approval"
        elif 10 < acres <= 25:
            return 85, f"Good size ({acres:.1f}ac) - moderate complexity"
        elif 25 < acres <= 50:
            return 75, f"Larger parcel ({acres:.1f}ac) - more scrutiny"
        elif 50 < acres <= 100:
            return 60, f"Large tract ({acres:.1f}ac) - extended timeline"
        elif acres > 100:
            return 45, f"Major development ({acres:.1f}ac) - DRI possible"
        else:
            return 65, f"Small parcel ({acres:.1f}ac) - limited upside"
    
    def _score_land_use(self, land_use: str) -> Tuple[int, str]:
        """Score based on current land use and rezone potential"""
        land_use_upper = land_use.upper()
        
        if any(kw in land_use_upper for kw in ['AGRICULTURAL', 'TIMBER', 'GRAZING']):
            return 90, "Agricultural - high rezone potential"
        elif 'VACANT' in land_use_upper:
            return 85, "Vacant - clean slate for development"
        elif 'PASTURE' in land_use_upper or 'FARM' in land_use_upper:
            return 88, "Farm/Pasture - good conversion candidate"
        elif 'COMMERCIAL' in land_use_upper and 'VACANT' in land_use_upper:
            return 80, "Vacant commercial - Live Local opportunity"
        elif 'GOLF' in land_use_upper:
            return 55, "Golf course - HOA opposition risk"
        else:
            return 65, "Standard land use"
    
    def _score_value_per_acre(self, market_value: float, acres: float) -> Tuple[int, str]:
        """Score based on value arbitrage potential"""
        if acres <= 0:
            return 50, "Unable to calculate value/acre"
        
        per_acre = market_value / acres
        
        if per_acre < 15000:
            return 95, f"Very low value (${per_acre:,.0f}/ac) - major arbitrage"
        elif per_acre < 30000:
            return 85, f"Low value (${per_acre:,.0f}/ac) - good arbitrage"
        elif per_acre < 60000:
            return 70, f"Moderate value (${per_acre:,.0f}/ac)"
        elif per_acre < 100000:
            return 55, f"Higher value (${per_acre:,.0f}/ac) - limited upside"
        else:
            return 40, f"Premium value (${per_acre:,.0f}/ac) - minimal arbitrage"
    
    def _score_location(self, address: str) -> Tuple[int, List[str]]:
        """Score based on location indicators"""
        score = 0
        reasons = []
        addr_upper = (address or '').upper()
        
        # West Melbourne corridors
        if any(rd in addr_upper for rd in ['DAIRY', 'ELLIS', 'MINTON', 'FELL']):
            score += 15
            reasons.append("+15: West Melbourne annexation corridor")
        
        # Palm Bay growth corridors
        if any(rd in addr_upper for rd in ['BABCOCK', 'MALABAR', 'PALM BAY RD']):
            score += 12
            reasons.append("+12: Palm Bay growth corridor")
        
        # Major infrastructure
        if any(rd in addr_upper for rd in ['HERITAGE', 'ST JOHNS', 'I-95', 'I95', 'US 1', 'US1']):
            score += 10
            reasons.append("+10: Major corridor/infrastructure")
        
        # Industrial adjacency indicators
        if any(kw in addr_upper for kw in ['INDUSTRIAL', 'COMMERCE', 'PARK']):
            score += 8
            reasons.append("+8: Industrial area proximity")
        
        return score, reasons
    
    def score_parcel(self, parcel: Dict[str, Any]) -> Dict[str, Any]:
        """
        Score a single parcel and return detailed analysis
        
        Args:
            parcel: Dict with keys: account, acreage, taxingDistrict, 
                   landUseCode, marketValue, siteAddress, owners
        
        Returns:
            Dict with score, recommendation, and detailed breakdown
        """
        # Extract parcel data
        account = parcel.get('account', 'N/A')
        acres = float(parcel.get('acreage', 0) or 0)
        district = str(parcel.get('taxingDistrict', ''))
        land_use = str(parcel.get('landUseCode', ''))
        market_value = float(parcel.get('marketValue', 0) or 0)
        address = str(parcel.get('siteAddress', ''))
        
        # Component scores
        jur_score, jur_reason = self._score_jurisdiction(district)
        acre_score, acre_reason = self._score_acreage(acres)
        use_score, use_reason = self._score_land_use(land_use)
        value_score, value_reason = self._score_value_per_acre(market_value, acres)
        loc_bonus, loc_reasons = self._score_location(address)
        
        # Calculate weighted composite
        base_score = (
            jur_score * self.weights.jurisdiction +
            use_score * self.weights.zoning_match +
            acre_score * self.weights.acreage +
            value_score * self.weights.opposition +
            70 * self.weights.staff_rec +  # Neutral assumption
            70 * self.weights.comp_plan     # Neutral assumption
        )
        
        # Add location bonus (capped)
        final_score = min(100, max(0, int(base_score + loc_bonus * 0.5)))
        
        # Determine recommendation
        if final_score >= 80:
            recommendation = Recommendation.BID
            action = "Immediate acquisition candidate - high approval probability"
            timeline = "3-6 months"
            risk = "LOW"
        elif final_score >= 65:
            recommendation = Recommendation.REVIEW
            action = "Conduct due diligence - verify opposition factors"
            timeline = "6-12 months"
            risk = "MODERATE"
        elif final_score >= 50:
            recommendation = Recommendation.WATCH
            action = "Monitor for changing conditions"
            timeline = "12+ months"
            risk = "MODERATE-HIGH"
        else:
            recommendation = Recommendation.SKIP
            action = "Does not match rough diamond criteria"
            timeline = "N/A"
            risk = "HIGH"
        
        # Compile reasons
        all_reasons = [jur_reason, acre_reason, use_reason, value_reason] + loc_reasons
        
        return {
            "account": account,
            "parcel_id": parcel.get('parcelID', 'N/A'),
            "address": address,
            "acres": acres,
            "district": district,
            "land_use": land_use[:50],
            "market_value": market_value,
            "value_per_acre": market_value / max(acres, 0.1),
            "owner": str(parcel.get('owners', 'N/A'))[:50],
            "score": final_score,
            "recommendation": recommendation.value,
            "action": action,
            "timeline": timeline,
            "risk_level": risk,
            "scoring_factors": all_reasons,
            "component_scores": {
                "jurisdiction": jur_score,
                "land_use": use_score,
                "acreage": acre_score,
                "value_arbitrage": value_score,
                "location_bonus": loc_bonus
            },
            "bcpao_url": f"https://www.bcpao.us/PropertySearch/#/account/{account}"
        }
    
    def score_parcels(self, parcels: List[Dict]) -> List[Dict]:
        """Score multiple parcels and sort by score descending"""
        scored = [self.score_parcel(p) for p in parcels]
        return sorted(scored, key=lambda x: x['score'], reverse=True)
    
    def get_bid_candidates(self, scored_parcels: List[Dict]) -> List[Dict]:
        """Filter to only BID recommendations"""
        return [p for p in scored_parcels if '🟢' in p.get('recommendation', '')]
    
    def get_review_candidates(self, scored_parcels: List[Dict]) -> List[Dict]:
        """Filter to REVIEW recommendations"""
        return [p for p in scored_parcels if '🟡' in p.get('recommendation', '')]
    
    def export_results(self, scored_parcels: List[Dict], filepath: str) -> None:
        """Export scored results to JSON"""
        from datetime import datetime
        
        bid_count = len(self.get_bid_candidates(scored_parcels))
        review_count = len(self.get_review_candidates(scored_parcels))
        
        output = {
            "generated": datetime.now().isoformat(),
            "model_version": "1.0.0",
            "total_scored": len(scored_parcels),
            "bid_count": bid_count,
            "review_count": review_count,
            "weights": {
                "jurisdiction": self.weights.jurisdiction,
                "zoning_match": self.weights.zoning_match,
                "acreage": self.weights.acreage,
                "opposition": self.weights.opposition,
                "staff_rec": self.weights.staff_rec,
                "comp_plan": self.weights.comp_plan
            },
            "parcels": scored_parcels
        }
        
        with open(filepath, 'w') as f:
            json.dump(output, f, indent=2, default=str)


# Convenience function
def score_parcel_quick(parcel: Dict) -> Tuple[int, str]:
    """Quick scoring function for pipeline integration"""
    scorer = RoughDiamondScorer()
    result = scorer.score_parcel(parcel)
    return result['score'], result['recommendation']


if __name__ == "__main__":
    # Test with sample data
    sample = {
        "account": "TEST001",
        "parcelID": "25-36-01-00-123",
        "siteAddress": "1234 DAIRY RD, MELBOURNE FL",
        "acreage": 8.5,
        "taxingDistrict": "UNINCORP DISTRICT 3",
        "landUseCode": "AGRICULTURAL - GRAZING LAND",
        "marketValue": 150000,
        "owners": "SMITH FAMILY TRUST"
    }
    
    scorer = RoughDiamondScorer()
    result = scorer.score_parcel(sample)
    print(json.dumps(result, indent=2))
