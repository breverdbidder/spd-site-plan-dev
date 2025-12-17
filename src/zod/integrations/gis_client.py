"""
GIS Client - Interface to municipal GIS APIs for zoning and FLU data.

Supports:
- Brevard County GIS (gis.brevardfl.gov)
- Palm Bay GIS
- ArcGIS REST API standard endpoints
"""

import httpx
from typing import Optional
import logging
from datetime import datetime
from src.models.state_models import (
    get_jurisdiction_definitions,
    ZoningDistrict,
    FLUDesignation
)

logger = logging.getLogger(__name__)


class GISClient:
    """
    Client for querying municipal GIS systems.
    
    Handles:
    - Zoning layer queries
    - Future Land Use layer queries
    - Parcel geometry lookups
    - Constraint layer overlays
    """
    
    # Known GIS endpoints
    ENDPOINTS = {
        "brevard_county": {
            "base_url": "https://gis.brevardfl.gov/arcgis/rest/services",
            "zoning_service": "Planning/Zoning/MapServer/0",
            "flu_service": "Planning/FutureLandUse/MapServer/0",
            "parcels_service": "PropertyAppraiser/Parcels/MapServer/0"
        },
        "palm_bay": {
            "base_url": "https://gis.palmbayflorida.org/arcgis/rest/services",
            "zoning_service": "PalmBay/Zoning/MapServer/0",
            "flu_service": "PalmBay/FutureLandUse/MapServer/0",
            "parcels_service": "PalmBay/Parcels/MapServer/0"
        }
    }
    
    def __init__(self, jurisdiction: str, timeout: float = 30.0):
        """
        Initialize GIS client for a jurisdiction.
        
        Args:
            jurisdiction: Name of jurisdiction (e.g., "Palm Bay", "Brevard County")
            timeout: HTTP request timeout in seconds
        """
        self.jurisdiction = jurisdiction
        self.timeout = timeout
        self._client = httpx.AsyncClient(timeout=timeout)
        
        # Determine which endpoint config to use
        jurisdiction_lower = jurisdiction.lower()
        if "palm bay" in jurisdiction_lower:
            self.config = self.ENDPOINTS["palm_bay"]
        else:
            self.config = self.ENDPOINTS["brevard_county"]
        
        # Get jurisdiction-specific definitions as fallback
        self.zoning_defs, self.flu_defs = get_jurisdiction_definitions(jurisdiction)
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._client.aclose()
    
    async def get_zoning_districts(self) -> dict[str, dict]:
        """
        Fetch zoning district definitions from GIS or use cached definitions.
        
        Returns:
            Dict mapping zoning code to district attributes
        """
        try:
            # Try to query GIS for zoning definitions
            url = f"{self.config['base_url']}/{self.config['zoning_service']}/query"
            params = {
                "where": "1=1",
                "outFields": "*",
                "returnDistinctValues": "true",
                "f": "json"
            }
            
            response = await self._client.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                if "features" in data:
                    districts = {}
                    for feature in data["features"]:
                        attrs = feature.get("attributes", {})
                        code = attrs.get("ZONING_CODE") or attrs.get("ZONE_CODE") or attrs.get("ZONING")
                        if code:
                            districts[code] = {
                                "code": code,
                                "description": attrs.get("DESCRIPTION", ""),
                                "max_density_du_acre": float(attrs.get("MAX_DENSITY", 0) or 0),
                                "permitted_uses": [],
                                "overlays": []
                            }
                    if districts:
                        logger.info(f"Loaded {len(districts)} zoning districts from GIS")
                        return districts
        except Exception as e:
            logger.warning(f"GIS query failed, using cached definitions: {e}")
        
        # Fall back to cached definitions
        return {
            code: {
                "code": dist.code,
                "description": dist.description,
                "max_density_du_acre": dist.max_density_du_acre,
                "permitted_uses": dist.permitted_uses,
                "overlays": dist.overlays,
                "setback_front": dist.setback_front,
                "setback_side": dist.setback_side,
                "setback_rear": dist.setback_rear,
                "max_height": dist.max_height,
                "lot_coverage": dist.lot_coverage
            }
            for code, dist in self.zoning_defs.items()
        }
    
    async def get_flu_designations(self) -> dict[str, dict]:
        """
        Fetch FLU designations from GIS or use cached definitions.
        
        Returns:
            Dict mapping FLU code to designation attributes
        """
        try:
            # Try to query GIS for FLU definitions
            url = f"{self.config['base_url']}/{self.config['flu_service']}/query"
            params = {
                "where": "1=1",
                "outFields": "*",
                "returnDistinctValues": "true",
                "f": "json"
            }
            
            response = await self._client.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                if "features" in data:
                    designations = {}
                    for feature in data["features"]:
                        attrs = feature.get("attributes", {})
                        code = attrs.get("FLU_CODE") or attrs.get("FLU") or attrs.get("LANDUSE")
                        if code:
                            designations[code] = {
                                "code": code,
                                "description": attrs.get("DESCRIPTION", ""),
                                "max_density_du_acre": float(attrs.get("MAX_DENSITY", 0) or 0),
                                "min_density_du_acre": float(attrs.get("MIN_DENSITY", 0) or 0),
                                "permitted_zoning": []
                            }
                    if designations:
                        logger.info(f"Loaded {len(designations)} FLU designations from GIS")
                        return designations
        except Exception as e:
            logger.warning(f"GIS FLU query failed, using cached definitions: {e}")
        
        # Fall back to cached definitions
        return {
            code: {
                "code": flu.code,
                "description": flu.description,
                "max_density_du_acre": flu.max_density_du_acre,
                "min_density_du_acre": flu.min_density_du_acre,
                "permitted_zoning": flu.permitted_zoning,
                "intensity_max": flu.intensity_max
            }
            for code, flu in self.flu_defs.items()
        }
    
    async def query_parcels_in_flu(
        self,
        flu_category: str,
        min_acres: float = 0.5,
        limit: int = 100
    ) -> list[dict]:
        """
        Query parcels within a specific FLU category.
        
        Args:
            flu_category: FLU code (e.g., "HDR", "MDR")
            min_acres: Minimum parcel size in acres
            limit: Maximum parcels to return
        
        Returns:
            List of parcel dicts with basic attributes
        """
        try:
            url = f"{self.config['base_url']}/{self.config['parcels_service']}/query"
            
            # Build where clause
            where_clause = f"FLU = '{flu_category}' AND ACRES >= {min_acres}"
            
            params = {
                "where": where_clause,
                "outFields": "PARCEL_ID,ACCOUNT_ID,ADDRESS,ACRES,ZONING,FLU,OWNER_NAME",
                "returnGeometry": "false",
                "resultRecordCount": limit,
                "f": "json"
            }
            
            response = await self._client.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                parcels = []
                for feature in data.get("features", []):
                    attrs = feature.get("attributes", {})
                    parcels.append({
                        "parcel_id": attrs.get("PARCEL_ID") or attrs.get("ACCOUNT_ID"),
                        "account_id": attrs.get("ACCOUNT_ID"),
                        "address": attrs.get("ADDRESS", ""),
                        "acres": float(attrs.get("ACRES", 0) or 0),
                        "zoning_code": attrs.get("ZONING", ""),
                        "flu_designation": attrs.get("FLU", flu_category),
                        "owner_name": attrs.get("OWNER_NAME", "")
                    })
                logger.info(f"Found {len(parcels)} parcels in {flu_category} FLU")
                return parcels
        except Exception as e:
            logger.error(f"Parcel query failed: {e}")
        
        return []
    
    async def get_parcel_by_id(self, parcel_id: str) -> Optional[dict]:
        """
        Get detailed parcel information by ID.
        
        Args:
            parcel_id: Parcel ID or account number
        
        Returns:
            Parcel dict or None if not found
        """
        try:
            url = f"{self.config['base_url']}/{self.config['parcels_service']}/query"
            
            params = {
                "where": f"PARCEL_ID = '{parcel_id}' OR ACCOUNT_ID = '{parcel_id}'",
                "outFields": "*",
                "returnGeometry": "true",
                "f": "json"
            }
            
            response = await self._client.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                features = data.get("features", [])
                if features:
                    attrs = features[0].get("attributes", {})
                    geometry = features[0].get("geometry", {})
                    return {
                        "parcel_id": attrs.get("PARCEL_ID") or parcel_id,
                        "account_id": attrs.get("ACCOUNT_ID"),
                        "address": attrs.get("ADDRESS", ""),
                        "city": attrs.get("CITY", self.jurisdiction),
                        "state": "FL",
                        "zip_code": attrs.get("ZIP", ""),
                        "acres": float(attrs.get("ACRES", 0) or 0),
                        "zoning_code": attrs.get("ZONING", ""),
                        "flu_designation": attrs.get("FLU", ""),
                        "owner_name": attrs.get("OWNER_NAME", ""),
                        "legal_description": attrs.get("LEGAL", ""),
                        "geometry": geometry
                    }
        except Exception as e:
            logger.error(f"Parcel lookup failed for {parcel_id}: {e}")
        
        return None
    
    async def get_zoning_for_parcel(self, parcel_id: str) -> Optional[str]:
        """
        Get current zoning code for a specific parcel.
        
        Args:
            parcel_id: Parcel ID
        
        Returns:
            Zoning code string or None
        """
        parcel = await self.get_parcel_by_id(parcel_id)
        if parcel:
            return parcel.get("zoning_code")
        return None
    
    async def get_flu_for_parcel(self, parcel_id: str) -> Optional[str]:
        """
        Get FLU designation for a specific parcel.
        
        Args:
            parcel_id: Parcel ID
        
        Returns:
            FLU code string or None
        """
        parcel = await self.get_parcel_by_id(parcel_id)
        if parcel:
            return parcel.get("flu_designation")
        return None


# Convenience function for quick jurisdiction setup
async def create_gis_client(jurisdiction: str) -> GISClient:
    """Create and return a GIS client for the specified jurisdiction."""
    return GISClient(jurisdiction)
