"""
Rezoning History Client - Query historical rezoning applications for market validation.

Analyzes:
- Recent rezoning applications in area
- Approval rates by zoning type
- Comparable developments
- Neighborhood opposition patterns
"""

import httpx
import logging
from typing import Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class RezoningHistoryClient:
    """
    Client for querying rezoning application history.
    
    Sources:
    - Municipal planning department records
    - County clerk's office
    - Building permit databases
    """
    
    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout
        self._client = httpx.AsyncClient(timeout=timeout)
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._client.aclose()
    
    async def get_nearby_rezonings(
        self,
        parcel_id: str,
        radius_miles: float = 2.0,
        years_back: int = 5
    ) -> list[dict]:
        """
        Get rezoning applications near a parcel.
        
        Args:
            parcel_id: Reference parcel ID
            radius_miles: Search radius
            years_back: How many years to look back
        
        Returns:
            List of rezoning application records
        """
        # In production, query municipal planning department
        # For now, return simulated data based on Brevard County patterns
        
        cutoff_date = datetime.now() - timedelta(days=years_back * 365)
        
        # Sample data structure
        sample_rezonings = [
            {
                "application_id": "RZ-2023-001",
                "address": "123 Sample Rd",
                "original_zoning": "RS-2",
                "target_zoning": "RM-10",
                "status": "APPROVED",
                "decision_date": "2023-06-15",
                "units_proposed": 24,
                "distance_miles": 0.8,
                "opposition_level": "LOW"
            },
            {
                "application_id": "RZ-2023-015",
                "address": "456 Test Ave",
                "original_zoning": "RS-4",
                "target_zoning": "RM-15",
                "status": "APPROVED",
                "decision_date": "2023-09-20",
                "units_proposed": 36,
                "distance_miles": 1.2,
                "opposition_level": "MEDIUM"
            },
            {
                "application_id": "RZ-2024-003",
                "address": "789 Demo Blvd",
                "original_zoning": "PUD",
                "target_zoning": "RM-20",
                "status": "DENIED",
                "decision_date": "2024-02-10",
                "units_proposed": 60,
                "distance_miles": 1.5,
                "opposition_level": "HIGH",
                "denial_reason": "Traffic impact concerns"
            }
        ]
        
        return sample_rezonings
    
    async def get_comparable_developments(
        self,
        parcel_id: str,
        development_type: str = "multifamily",
        radius_miles: float = 3.0
    ) -> list[dict]:
        """
        Get comparable developments for market analysis.
        
        Args:
            parcel_id: Reference parcel ID
            development_type: Type of development to compare
            radius_miles: Search radius
        
        Returns:
            List of comparable development records
        """
        # In production, query building permits and property records
        
        sample_comps = [
            {
                "name": "Palm Bay Apartments",
                "address": "1000 Palm Bay Rd",
                "units": 120,
                "density_du_acre": 18.5,
                "year_built": 2022,
                "occupancy_rate": 0.95,
                "avg_rent": 1450,
                "distance_miles": 1.8
            },
            {
                "name": "Brevard Gardens",
                "address": "2500 Garden Way",
                "units": 84,
                "density_du_acre": 15.2,
                "year_built": 2021,
                "occupancy_rate": 0.92,
                "avg_rent": 1380,
                "distance_miles": 2.1
            }
        ]
        
        return sample_comps
    
    async def calculate_approval_probability(
        self,
        original_zoning: str,
        target_zoning: str,
        flu_designation: str,
        parcel_acres: float,
        proposed_units: int
    ) -> dict:
        """
        Calculate probability of rezoning approval.
        
        Based on:
        - FLU consistency (most important)
        - Historical approval rates
        - Proposed density vs. FLU maximum
        - Parcel size
        
        Returns:
            Dict with probability and factors
        """
        factors = []
        base_probability = 50.0  # Start at 50%
        
        # FLU Consistency (±30%)
        # If target zoning is permitted by FLU, big boost
        flu_permitted_zoning = self._get_flu_permitted_zoning(flu_designation)
        if target_zoning in flu_permitted_zoning:
            base_probability += 30
            factors.append({
                "factor": "FLU Consistency",
                "impact": "+30%",
                "note": f"{target_zoning} is permitted by {flu_designation} FLU"
            })
        else:
            base_probability -= 20
            factors.append({
                "factor": "FLU Consistency",
                "impact": "-20%",
                "note": f"{target_zoning} requires comp plan amendment"
            })
        
        # Historical approval rate (±15%)
        historical = await self.get_nearby_rezonings(
            parcel_id="",
            radius_miles=3,
            years_back=3
        )
        similar = [r for r in historical if r.get("target_zoning") == target_zoning]
        if similar:
            approved = len([r for r in similar if r.get("status") == "APPROVED"])
            rate = approved / len(similar)
            if rate > 0.7:
                base_probability += 15
                factors.append({
                    "factor": "Historical Approval Rate",
                    "impact": "+15%",
                    "note": f"{rate*100:.0f}% of similar requests approved"
                })
            elif rate < 0.3:
                base_probability -= 15
                factors.append({
                    "factor": "Historical Approval Rate",
                    "impact": "-15%",
                    "note": f"Only {rate*100:.0f}% of similar requests approved"
                })
        
        # Density relative to FLU max (±10%)
        flu_max_density = self._get_flu_max_density(flu_designation)
        proposed_density = proposed_units / parcel_acres if parcel_acres > 0 else 0
        if proposed_density <= flu_max_density * 0.8:
            base_probability += 10
            factors.append({
                "factor": "Density Headroom",
                "impact": "+10%",
                "note": f"Proposed {proposed_density:.1f} du/ac < 80% of FLU max {flu_max_density}"
            })
        elif proposed_density > flu_max_density:
            base_probability -= 15
            factors.append({
                "factor": "Over-density",
                "impact": "-15%",
                "note": f"Proposed {proposed_density:.1f} du/ac exceeds FLU max {flu_max_density}"
            })
        
        # Cap probability
        final_probability = max(5, min(95, base_probability))
        
        return {
            "approval_probability": round(final_probability, 1),
            "factors": factors,
            "recommendation": self._get_recommendation(final_probability),
            "risk_level": self._get_risk_level(final_probability)
        }
    
    def _get_flu_permitted_zoning(self, flu_code: str) -> list[str]:
        """Get zoning districts permitted by FLU."""
        flu_zoning_map = {
            "LDR": ["RS-1", "RS-2", "RS-4"],
            "MDR": ["RS-4", "RM-6", "RM-10"],
            "HDR": ["RM-10", "RM-15", "RM-20"],
            "MXU": ["RM-15", "RM-20", "BU-1", "BU-2"],
            "NC": ["BU-1", "RM-15"]
        }
        return flu_zoning_map.get(flu_code, [])
    
    def _get_flu_max_density(self, flu_code: str) -> float:
        """Get max density for FLU designation."""
        flu_density_map = {
            "LDR": 4,
            "MDR": 10,
            "HDR": 20,
            "MXU": 25,
            "NC": 15
        }
        return flu_density_map.get(flu_code, 0)
    
    def _get_recommendation(self, probability: float) -> str:
        """Get recommendation based on probability."""
        if probability >= 75:
            return "PROCEED - Strong approval likelihood"
        elif probability >= 60:
            return "PROCEED WITH CAUTION - Moderate approval likelihood"
        elif probability >= 40:
            return "EVALUATE CAREFULLY - Approval uncertain"
        else:
            return "HIGH RISK - Consider alternative approach"
    
    def _get_risk_level(self, probability: float) -> str:
        """Get risk level classification."""
        if probability >= 75:
            return "LOW"
        elif probability >= 50:
            return "MEDIUM"
        else:
            return "HIGH"


async def create_rezoning_client() -> RezoningHistoryClient:
    """Create and return a rezoning history client."""
    return RezoningHistoryClient()
