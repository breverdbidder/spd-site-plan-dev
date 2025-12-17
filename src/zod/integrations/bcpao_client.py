"""
BCPAO Client - Brevard County Property Appraiser integration.

Queries BCPAO API for parcel data:
- Property details
- Ownership information
- Parcel boundaries
- Tax information
"""

import httpx
import logging
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class BCPAOClient:
    """
    Client for Brevard County Property Appraiser API.
    
    API Base: https://www.bcpao.us/api/v1
    """
    
    BASE_URL = "https://www.bcpao.us/api/v1"
    
    def __init__(self, timeout: float = 30.0):
        """
        Initialize BCPAO client.
        
        Args:
            timeout: HTTP request timeout in seconds
        """
        self.timeout = timeout
        self._client = httpx.AsyncClient(
            timeout=timeout,
            headers={
                "User-Agent": "SPD-ZOD/1.0 (Everest Capital)",
                "Accept": "application/json"
            }
        )
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._client.aclose()
    
    async def search_by_account(self, account_id: str) -> Optional[dict]:
        """
        Search for a parcel by account ID.
        
        Args:
            account_id: BCPAO account number (e.g., "2835546")
        
        Returns:
            Parcel dict or None if not found
        """
        try:
            url = f"{self.BASE_URL}/search"
            params = {"account": account_id}
            
            response = await self._client.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("data"):
                    parcel_data = data["data"][0] if isinstance(data["data"], list) else data["data"]
                    return self._normalize_parcel(parcel_data)
        except Exception as e:
            logger.error(f"BCPAO search failed for {account_id}: {e}")
        
        return None
    
    async def search_by_address(self, address: str) -> list[dict]:
        """
        Search for parcels by address.
        
        Args:
            address: Street address to search
        
        Returns:
            List of matching parcel dicts
        """
        try:
            url = f"{self.BASE_URL}/search"
            params = {"address": address}
            
            response = await self._client.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                parcels = []
                for item in data.get("data", []):
                    normalized = self._normalize_parcel(item)
                    if normalized:
                        parcels.append(normalized)
                return parcels
        except Exception as e:
            logger.error(f"BCPAO address search failed for {address}: {e}")
        
        return []
    
    async def query_parcels_by_flu(
        self,
        flu_category: str,
        min_acres: float = 0.5,
        limit: int = 50
    ) -> list[dict]:
        """
        Query parcels by FLU category.
        
        Note: BCPAO API doesn't directly support FLU queries.
        This method uses the GIS integration for FLU-based searches.
        
        Args:
            flu_category: FLU code (e.g., "HDR", "MDR")
            min_acres: Minimum parcel size
            limit: Maximum results
        
        Returns:
            List of parcel dicts
        """
        # For BCPAO, we typically need to query via GIS first for FLU,
        # then enrich with BCPAO data
        logger.warning("BCPAO direct FLU query not supported - use GISClient.query_parcels_in_flu")
        return []
    
    async def get_parcel_details(self, account_id: str) -> Optional[dict]:
        """
        Get detailed parcel information.
        
        Args:
            account_id: BCPAO account number
        
        Returns:
            Detailed parcel dict or None
        """
        try:
            url = f"{self.BASE_URL}/parcel/{account_id}"
            
            response = await self._client.get(url)
            
            if response.status_code == 200:
                data = response.json()
                return self._normalize_parcel_details(data)
        except Exception as e:
            logger.error(f"BCPAO detail fetch failed for {account_id}: {e}")
        
        return None
    
    async def get_parcel_photo_url(self, account_id: str) -> Optional[str]:
        """
        Get the photo URL for a parcel.
        
        Args:
            account_id: BCPAO account number
        
        Returns:
            Photo URL string or None
        """
        # BCPAO photo URL pattern
        prefix = account_id[:4] if len(account_id) >= 4 else account_id
        return f"https://www.bcpao.us/photos/{prefix}/{account_id}011.jpg"
    
    async def get_sales_history(self, account_id: str) -> list[dict]:
        """
        Get sales history for a parcel.
        
        Args:
            account_id: BCPAO account number
        
        Returns:
            List of sale records
        """
        try:
            url = f"{self.BASE_URL}/sales/{account_id}"
            
            response = await self._client.get(url)
            
            if response.status_code == 200:
                data = response.json()
                return data.get("sales", [])
        except Exception as e:
            logger.error(f"BCPAO sales history failed for {account_id}: {e}")
        
        return []
    
    def _normalize_parcel(self, raw_data: dict) -> Optional[dict]:
        """Normalize raw BCPAO parcel data to standard format."""
        if not raw_data:
            return None
        
        # Extract from various possible field names
        account = raw_data.get("account") or raw_data.get("accountId") or raw_data.get("ACCOUNT")
        
        if not account:
            return None
        
        # Calculate acres from square feet if needed
        sqft = raw_data.get("landSqFt") or raw_data.get("land_sqft") or raw_data.get("LAND_SQFT") or 0
        acres = raw_data.get("acres") or raw_data.get("ACRES") or (float(sqft) / 43560 if sqft else 0)
        
        return {
            "parcel_id": str(account),
            "account_id": str(account),
            "address": raw_data.get("address") or raw_data.get("siteAddr") or raw_data.get("SITE_ADDR") or "",
            "city": raw_data.get("city") or raw_data.get("CITY") or "",
            "state": "FL",
            "zip_code": raw_data.get("zip") or raw_data.get("ZIP") or "",
            "acres": float(acres),
            "zoning_code": raw_data.get("zoning") or raw_data.get("ZONING") or "",
            "flu_designation": raw_data.get("flu") or raw_data.get("FLU") or "",
            "owner_name": raw_data.get("owner") or raw_data.get("ownerName") or raw_data.get("OWNER") or "",
            "legal_description": raw_data.get("legal") or raw_data.get("legalDesc") or raw_data.get("LEGAL") or "",
            "just_value": float(raw_data.get("justValue") or raw_data.get("just_value") or 0),
            "assessed_value": float(raw_data.get("assessedValue") or raw_data.get("assessed_value") or 0),
            "land_value": float(raw_data.get("landValue") or raw_data.get("land_value") or 0),
            "building_value": float(raw_data.get("buildingValue") or raw_data.get("building_value") or 0)
        }
    
    def _normalize_parcel_details(self, raw_data: dict) -> Optional[dict]:
        """Normalize detailed parcel data."""
        base = self._normalize_parcel(raw_data)
        if not base:
            return None
        
        # Add detailed fields
        base.update({
            "use_code": raw_data.get("useCode") or raw_data.get("use_code") or "",
            "use_description": raw_data.get("useDesc") or raw_data.get("use_description") or "",
            "year_built": int(raw_data.get("yearBuilt") or raw_data.get("year_built") or 0),
            "building_sqft": float(raw_data.get("buildingSqFt") or raw_data.get("building_sqft") or 0),
            "bedrooms": int(raw_data.get("bedrooms") or 0),
            "bathrooms": float(raw_data.get("bathrooms") or 0),
            "stories": float(raw_data.get("stories") or 1),
            "pool": bool(raw_data.get("pool") or False),
            "homestead": bool(raw_data.get("homestead") or False)
        })
        
        return base


# Convenience function
async def create_bcpao_client() -> BCPAOClient:
    """Create and return a BCPAO client."""
    return BCPAOClient()
