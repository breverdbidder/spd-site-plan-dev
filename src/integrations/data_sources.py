"""
Zoning-FLU Opportunity Discovery - Data Source Integrations
============================================================
API integrations for property data, GIS layers, and municipal records.

Data Sources:
- BCPAO (Brevard County Property Appraiser)
- Municipal GIS (Palm Bay, Melbourne, etc.)
- SJRWMD (Water Management District)
- FEMA Flood Maps
- Planning Department Records
"""

import os
import json
import asyncio
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
import httpx
from urllib.parse import urlencode


# =============================================================================
# BCPAO INTEGRATION
# =============================================================================

class BCPAOClient:
    """
    Brevard County Property Appraiser API Client.
    
    Endpoints:
    - Property search
    - Parcel details
    - Sales history
    - GIS overlay data
    """
    
    BASE_URL = "https://www.bcpao.us/api/v1"
    
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)
    
    async def search_by_address(
        self,
        address: str,
        city: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search parcels by address"""
        params = {"address": address}
        if city:
            params["city"] = city
        
        try:
            response = await self.client.get(
                f"{self.BASE_URL}/search",
                params=params
            )
            response.raise_for_status()
            return response.json().get("results", [])
        except Exception as e:
            print(f"BCPAO search error: {e}")
            return []
    
    async def get_parcel_details(
        self,
        account_number: str
    ) -> Optional[Dict[str, Any]]:
        """Get detailed parcel information"""
        try:
            response = await self.client.get(
                f"{self.BASE_URL}/parcels/{account_number}"
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"BCPAO parcel error: {e}")
            return None
    
    async def get_parcels_by_zoning(
        self,
        zoning_code: str,
        city: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get all parcels with specific zoning"""
        params = {
            "zoning": zoning_code,
            "limit": limit
        }
        if city:
            params["city"] = city
        
        try:
            response = await self.client.get(
                f"{self.BASE_URL}/parcels/by-zoning",
                params=params
            )
            response.raise_for_status()
            return response.json().get("parcels", [])
        except Exception as e:
            print(f"BCPAO zoning search error: {e}")
            return []
    
    async def get_parcels_by_flu(
        self,
        flu_code: str,
        city: Optional[str] = None,
        min_acres: float = 0.0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get all parcels with specific Future Land Use"""
        params = {
            "flu": flu_code,
            "min_acres": min_acres,
            "limit": limit
        }
        if city:
            params["city"] = city
        
        try:
            response = await self.client.get(
                f"{self.BASE_URL}/parcels/by-flu",
                params=params
            )
            response.raise_for_status()
            return response.json().get("parcels", [])
        except Exception as e:
            print(f"BCPAO FLU search error: {e}")
            return []
    
    async def close(self):
        await self.client.aclose()


# =============================================================================
# MUNICIPAL GIS INTEGRATION
# =============================================================================

class MunicipalGISClient:
    """
    Municipal GIS API Client for zoning and FLU data.
    
    Supports:
    - Palm Bay
    - Melbourne
    - Cocoa
    - Titusville
    - Brevard County (unincorporated)
    """
    
    GIS_ENDPOINTS = {
        "Palm Bay": "https://gis.palmbayflorida.org/arcgis/rest/services",
        "Melbourne": "https://gis.melbourneflorida.org/arcgis/rest/services",
        "Brevard County": "https://gis.brevardcounty.us/arcgis/rest/services"
    }
    
    def __init__(self, jurisdiction: str, timeout: int = 30):
        self.jurisdiction = jurisdiction
        self.base_url = self.GIS_ENDPOINTS.get(jurisdiction)
        self.client = httpx.AsyncClient(timeout=timeout)
    
    async def get_zoning_layer(
        self,
        parcel_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get zoning district for a parcel"""
        if not self.base_url:
            return None
        
        try:
            # Query zoning layer by parcel ID
            params = {
                "where": f"PARCEL_ID = '{parcel_id}'",
                "outFields": "*",
                "returnGeometry": "false",
                "f": "json"
            }
            
            response = await self.client.get(
                f"{self.base_url}/Zoning/MapServer/0/query",
                params=params
            )
            response.raise_for_status()
            data = response.json()
            
            features = data.get("features", [])
            if features:
                return features[0].get("attributes")
            return None
        except Exception as e:
            print(f"GIS zoning query error: {e}")
            return None
    
    async def get_flu_layer(
        self,
        parcel_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get Future Land Use designation for a parcel"""
        if not self.base_url:
            return None
        
        try:
            params = {
                "where": f"PARCEL_ID = '{parcel_id}'",
                "outFields": "*",
                "returnGeometry": "false",
                "f": "json"
            }
            
            response = await self.client.get(
                f"{self.base_url}/FutureLandUse/MapServer/0/query",
                params=params
            )
            response.raise_for_status()
            data = response.json()
            
            features = data.get("features", [])
            if features:
                return features[0].get("attributes")
            return None
        except Exception as e:
            print(f"GIS FLU query error: {e}")
            return None
    
    async def get_constraint_layers(
        self,
        parcel_id: str
    ) -> Dict[str, Any]:
        """Get all constraint overlays for a parcel"""
        constraints = {
            "wellhead_protection": None,
            "flood_zone": None,
            "wetlands": None,
            "conservation": None,
            "easements": None
        }
        
        if not self.base_url:
            return constraints
        
        # Query each constraint layer
        layer_mapping = {
            "wellhead_protection": "WellheadProtection/MapServer/0",
            "flood_zone": "FloodZones/MapServer/0",
            "wetlands": "Wetlands/MapServer/0",
            "conservation": "Conservation/MapServer/0",
            "easements": "Easements/MapServer/0"
        }
        
        for constraint_type, layer_path in layer_mapping.items():
            try:
                params = {
                    "where": f"PARCEL_ID = '{parcel_id}'",
                    "outFields": "*",
                    "returnGeometry": "true",
                    "f": "json"
                }
                
                response = await self.client.get(
                    f"{self.base_url}/{layer_path}/query",
                    params=params
                )
                
                if response.status_code == 200:
                    data = response.json()
                    features = data.get("features", [])
                    if features:
                        constraints[constraint_type] = features[0].get("attributes")
            except Exception:
                pass  # Layer may not exist for all jurisdictions
        
        return constraints
    
    async def close(self):
        await self.client.aclose()


# =============================================================================
# PLANNING DEPARTMENT RECORDS
# =============================================================================

class PlanningRecordsClient:
    """
    Client for querying municipal planning department records.
    
    Data:
    - Rezoning applications
    - Site plan approvals
    - Variance requests
    - Meeting minutes
    """
    
    def __init__(self, jurisdiction: str, timeout: int = 30):
        self.jurisdiction = jurisdiction
        self.client = httpx.AsyncClient(timeout=timeout)
    
    async def get_rezoning_history(
        self,
        years_back: int = 2,
        flu_designation: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get recent rezoning applications"""
        # In production: Scrape planning department website or query database
        # For now, return sample data
        
        sample_rezonings = [
            {
                "case_number": "REZ-2024-001",
                "address": "1500 Malabar Rd SE",
                "from_zoning": "RS",
                "to_zoning": "RM-15",
                "flu_designation": "HDR",
                "density_requested": 15.0,
                "acreage": 2.5,
                "status": "APPROVED",
                "decision_date": "2024-08-15",
                "conditions": ["Traffic study required"],
                "vote_count": "4-1"
            },
            {
                "case_number": "REZ-2024-002",
                "address": "2000 Palm Bay Rd NE",
                "from_zoning": "PUD",
                "to_zoning": "RM-20",
                "flu_designation": "HDR",
                "density_requested": 20.0,
                "acreage": 1.8,
                "status": "APPROVED",
                "decision_date": "2024-09-20",
                "conditions": ["Affordable housing commitment"],
                "vote_count": "5-0"
            }
        ]
        
        if flu_designation:
            return [r for r in sample_rezonings if r.get("flu_designation") == flu_designation]
        return sample_rezonings
    
    async def get_meeting_calendar(self) -> List[Dict[str, Any]]:
        """Get upcoming planning board and council meetings"""
        return [
            {
                "board": "Planning and Zoning Board",
                "date": "2025-01-09",
                "time": "6:00 PM",
                "location": "City Hall Council Chambers"
            },
            {
                "board": "City Council",
                "date": "2025-01-16",
                "time": "7:00 PM",
                "location": "City Hall Council Chambers"
            }
        ]
    
    async def close(self):
        await self.client.aclose()


# =============================================================================
# FEMA FLOOD MAP INTEGRATION
# =============================================================================

class FEMAFloodClient:
    """
    FEMA National Flood Hazard Layer (NFHL) API Client.
    """
    
    BASE_URL = "https://hazards.fema.gov/gis/nfhl/rest/services"
    
    def __init__(self, timeout: int = 30):
        self.client = httpx.AsyncClient(timeout=timeout)
    
    async def get_flood_zone(
        self,
        latitude: float,
        longitude: float
    ) -> Optional[Dict[str, Any]]:
        """Get flood zone at coordinates"""
        try:
            params = {
                "geometry": f"{longitude},{latitude}",
                "geometryType": "esriGeometryPoint",
                "spatialRel": "esriSpatialRelIntersects",
                "outFields": "FLD_ZONE,ZONE_SUBTY,SFHA_TF",
                "returnGeometry": "false",
                "f": "json"
            }
            
            response = await self.client.get(
                f"{self.BASE_URL}/public/NFHL/MapServer/28/query",
                params=params
            )
            response.raise_for_status()
            data = response.json()
            
            features = data.get("features", [])
            if features:
                attrs = features[0].get("attributes", {})
                return {
                    "flood_zone": attrs.get("FLD_ZONE"),
                    "zone_subtype": attrs.get("ZONE_SUBTY"),
                    "in_sfha": attrs.get("SFHA_TF") == "T",
                    "description": self._get_zone_description(attrs.get("FLD_ZONE"))
                }
            return {"flood_zone": "X", "in_sfha": False, "description": "Minimal flood hazard"}
        except Exception as e:
            print(f"FEMA flood query error: {e}")
            return None
    
    def _get_zone_description(self, zone: str) -> str:
        """Get human-readable flood zone description"""
        descriptions = {
            "A": "High risk - 1% annual flood chance",
            "AE": "High risk with base flood elevation",
            "AH": "High risk - 1-3 foot shallow flooding",
            "AO": "High risk - sheet flow flooding",
            "V": "High risk - coastal flooding with waves",
            "VE": "High risk - coastal with base flood elevation",
            "X": "Minimal flood hazard",
            "B": "Moderate flood hazard (0.2% annual chance)",
            "C": "Minimal flood hazard"
        }
        return descriptions.get(zone, "Unknown flood zone")
    
    async def close(self):
        await self.client.aclose()


# =============================================================================
# DATA AGGREGATOR
# =============================================================================

class OpportunityDataAggregator:
    """
    Aggregates data from all sources for opportunity analysis.
    """
    
    def __init__(self, jurisdiction: str):
        self.jurisdiction = jurisdiction
        self.bcpao = BCPAOClient()
        self.gis = MunicipalGISClient(jurisdiction)
        self.planning = PlanningRecordsClient(jurisdiction)
        self.fema = FEMAFloodClient()
    
    async def get_parcel_data(
        self,
        account_number: str
    ) -> Dict[str, Any]:
        """Get comprehensive parcel data from all sources"""
        # Gather data in parallel
        bcpao_data, gis_zoning, gis_flu, gis_constraints = await asyncio.gather(
            self.bcpao.get_parcel_details(account_number),
            self.gis.get_zoning_layer(account_number),
            self.gis.get_flu_layer(account_number),
            self.gis.get_constraint_layers(account_number),
            return_exceptions=True
        )
        
        # Combine results
        result = {
            "account_number": account_number,
            "bcpao": bcpao_data if not isinstance(bcpao_data, Exception) else None,
            "zoning": gis_zoning if not isinstance(gis_zoning, Exception) else None,
            "flu": gis_flu if not isinstance(gis_flu, Exception) else None,
            "constraints": gis_constraints if not isinstance(gis_constraints, Exception) else {},
            "fetched_at": datetime.utcnow().isoformat()
        }
        
        return result
    
    async def discover_opportunities(
        self,
        target_flu: List[str],
        min_acres: float = 0.5,
        max_results: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Discover rezoning opportunities by finding parcels where
        current zoning < FLU maximum density.
        """
        opportunities = []
        
        for flu_code in target_flu:
            # Get parcels with this FLU designation
            parcels = await self.bcpao.get_parcels_by_flu(
                flu_code=flu_code,
                city=self.jurisdiction,
                min_acres=min_acres,
                limit=max_results // len(target_flu)
            )
            
            for parcel in parcels:
                # Get zoning data
                zoning = await self.gis.get_zoning_layer(parcel.get("parcel_id"))
                
                if zoning:
                    current_density = self._get_zoning_density(zoning.get("ZONE_CODE"))
                    flu_density = self._get_flu_density(flu_code)
                    
                    if flu_density > current_density:
                        opportunities.append({
                            "parcel": parcel,
                            "zoning": zoning,
                            "flu_code": flu_code,
                            "current_density": current_density,
                            "flu_density": flu_density,
                            "density_gap": flu_density - current_density
                        })
        
        # Sort by density gap (highest opportunity first)
        opportunities.sort(key=lambda x: x["density_gap"], reverse=True)
        
        return opportunities[:max_results]
    
    def _get_zoning_density(self, zone_code: str) -> float:
        """Map zoning code to density"""
        density_map = {
            "RS": 4, "RM-6": 6, "RM-10": 10, "RM-15": 15, "RM-20": 20,
            "RM-25": 25, "PUD": 8, "MU": 15
        }
        return density_map.get(zone_code, 4)
    
    def _get_flu_density(self, flu_code: str) -> float:
        """Map FLU code to max density"""
        flu_map = {"LDR": 4, "MDR": 10, "HDR": 20, "MU": 20}
        return flu_map.get(flu_code, 4)
    
    async def close(self):
        await asyncio.gather(
            self.bcpao.close(),
            self.gis.close(),
            self.planning.close(),
            self.fema.close()
        )


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

async def fetch_opportunity_data(
    jurisdiction: str,
    target_flu: List[str] = None,
    min_acres: float = 0.5,
    max_results: int = 100
) -> Dict[str, Any]:
    """
    Main entry point for fetching opportunity data.
    
    Args:
        jurisdiction: Municipality name
        target_flu: List of FLU codes to target
        min_acres: Minimum lot size
        max_results: Max parcels to return
        
    Returns:
        Dict with opportunities and metadata
    """
    if target_flu is None:
        target_flu = ["HDR", "MDR"]
    
    aggregator = OpportunityDataAggregator(jurisdiction)
    
    try:
        # Get rezoning history for approval rate
        rezoning_history = await aggregator.planning.get_rezoning_history(
            years_back=2,
            flu_designation=None
        )
        
        # Discover opportunities
        opportunities = await aggregator.discover_opportunities(
            target_flu=target_flu,
            min_acres=min_acres,
            max_results=max_results
        )
        
        return {
            "jurisdiction": jurisdiction,
            "target_flu": target_flu,
            "opportunities": opportunities,
            "rezoning_history": rezoning_history,
            "fetched_at": datetime.utcnow().isoformat()
        }
    finally:
        await aggregator.close()
