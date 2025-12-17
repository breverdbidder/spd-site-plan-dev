"""
SPD/ZOD Enhanced API Integrations
=================================
Leveraging the API Mega Library (10,498 APIs + 131 MCP servers)

Priority Integrations:
1. Real Estate APIs - Property data aggregation
2. Census API - Demographics and market data
3. AI Agents - Automated analysis
4. Government APIs - Zoning and FLU data
"""

import os
import asyncio
import httpx
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass


# =============================================================================
# APIFY REAL ESTATE SCRAPERS
# =============================================================================

class ApifyRealEstateClient:
    """
    Client for Apify real estate scrapers from API Mega Library.
    
    APIs:
    - Global Real Estate Aggregator (Zillow, Realtor, Zumper, etc.)
    - Realtor.com Scraper
    - Zillow API via Apify
    - Redfin Scraper
    """
    
    BASE_URL = "https://api.apify.com/v2"
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("APIFY_API_KEY", "")
        self.client = httpx.AsyncClient(timeout=60.0)
    
    async def search_zillow(
        self,
        address: str = None,
        zip_code: str = None,
        city: str = None,
        state: str = "FL"
    ) -> Dict[str, Any]:
        """Search Zillow for property data via Apify actor."""
        if not self.api_key:
            return {"error": "APIFY_API_KEY not configured"}
        
        actor_id = "l7auZloH1fqZw8FKa"  # Zillow scraper actor
        
        payload = {
            "searchType": "address" if address else "zipcode",
            "searchQuery": address or zip_code,
            "city": city,
            "state": state,
            "maxItems": 10
        }
        
        try:
            response = await self.client.post(
                f"{self.BASE_URL}/acts/{actor_id}/runs",
                params={"token": self.api_key},
                json=payload
            )
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    async def get_comps(
        self,
        address: str,
        radius_miles: float = 0.5,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """Get comparable sales from multiple sources."""
        # Would aggregate from Zillow, Redfin, Realtor.com
        return []
    
    async def get_zestimate(self, address: str) -> Dict[str, Any]:
        """Get Zillow Zestimate for property."""
        return await self.search_zillow(address=address)
    
    async def close(self):
        await self.client.aclose()


# =============================================================================
# CENSUS API CLIENT
# =============================================================================

class CensusAPIClient:
    """
    US Census Bureau API Client.
    
    Endpoints:
    - American Community Survey (ACS) - Demographics, income, housing
    - Population Estimates
    - TIGER/Line Geocoder
    
    FREE - Request API key at: https://api.census.gov/data/key_signup.html
    """
    
    BASE_URL = "https://api.census.gov/data"
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("CENSUS_API_KEY", "")
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def get_demographics_by_zip(self, zip_code: str, year: int = 2022) -> Dict[str, Any]:
        """
        Get demographic data for a zip code.
        
        Returns: population, median income, median home value, etc.
        """
        # ACS 5-year estimates
        endpoint = f"{self.BASE_URL}/{year}/acs/acs5"
        
        # Variables: B01003_001E (population), B19013_001E (median income),
        # B25077_001E (median home value), B25002_003E (vacancy)
        variables = "B01003_001E,B19013_001E,B25077_001E,B25002_003E,B25003_002E"
        
        params = {
            "get": variables,
            "for": f"zip code tabulation area:{zip_code}",
            "key": self.api_key
        }
        
        try:
            response = await self.client.get(endpoint, params=params)
            data = response.json()
            
            if len(data) >= 2:
                headers = data[0]
                values = data[1]
                result = dict(zip(headers, values))
                
                return {
                    "zip_code": zip_code,
                    "population": int(result.get("B01003_001E", 0) or 0),
                    "median_income": int(result.get("B19013_001E", 0) or 0),
                    "median_home_value": int(result.get("B25077_001E", 0) or 0),
                    "vacant_units": int(result.get("B25002_003E", 0) or 0),
                    "owner_occupied": int(result.get("B25003_002E", 0) or 0),
                    "year": year,
                    "source": "US Census ACS 5-Year Estimates"
                }
            return {"error": "No data found", "zip_code": zip_code}
            
        except Exception as e:
            return {"error": str(e), "zip_code": zip_code}
    
    async def get_housing_characteristics(self, fips_code: str, year: int = 2022) -> Dict[str, Any]:
        """Get housing characteristics by FIPS code (county or tract)."""
        endpoint = f"{self.BASE_URL}/{year}/acs/acs5"
        
        # Housing variables
        variables = (
            "B25001_001E,"  # Total housing units
            "B25002_002E,"  # Occupied
            "B25002_003E,"  # Vacant
            "B25003_002E,"  # Owner occupied
            "B25003_003E,"  # Renter occupied
            "B25064_001E,"  # Median gross rent
            "B25077_001E"   # Median home value
        )
        
        params = {
            "get": variables,
            "for": f"county:{fips_code[-3:]}" if len(fips_code) == 5 else f"tract:{fips_code}",
            "in": f"state:{fips_code[:2]}",
            "key": self.api_key
        }
        
        try:
            response = await self.client.get(endpoint, params=params)
            data = response.json()
            
            if len(data) >= 2:
                headers = data[0]
                values = data[1]
                result = dict(zip(headers, values))
                
                total = int(result.get("B25001_001E", 1) or 1)
                occupied = int(result.get("B25002_002E", 0) or 0)
                vacant = int(result.get("B25002_003E", 0) or 0)
                
                return {
                    "fips_code": fips_code,
                    "total_housing_units": total,
                    "occupied_units": occupied,
                    "vacant_units": vacant,
                    "vacancy_rate": round(vacant / total * 100, 2) if total > 0 else 0,
                    "owner_occupied": int(result.get("B25003_002E", 0) or 0),
                    "renter_occupied": int(result.get("B25003_003E", 0) or 0),
                    "median_rent": int(result.get("B25064_001E", 0) or 0),
                    "median_home_value": int(result.get("B25077_001E", 0) or 0),
                    "year": year
                }
            return {"error": "No data found"}
            
        except Exception as e:
            return {"error": str(e)}
    
    async def geocode_address(self, address: str) -> Dict[str, Any]:
        """Geocode address using Census Geocoder."""
        endpoint = "https://geocoding.geo.census.gov/geocoder/locations/onelineaddress"
        
        params = {
            "address": address,
            "benchmark": "Public_AR_Current",
            "format": "json"
        }
        
        try:
            response = await self.client.get(endpoint, params=params)
            data = response.json()
            
            matches = data.get("result", {}).get("addressMatches", [])
            if matches:
                match = matches[0]
                coords = match.get("coordinates", {})
                return {
                    "matched_address": match.get("matchedAddress"),
                    "latitude": coords.get("y"),
                    "longitude": coords.get("x"),
                    "tiger_line_id": match.get("tigerLine", {}).get("tigerLineId"),
                    "state_fips": match.get("geographies", {}).get("States", [{}])[0].get("STATEFP"),
                    "county_fips": match.get("geographies", {}).get("Counties", [{}])[0].get("COUNTYFP")
                }
            return {"error": "No match found", "address": address}
            
        except Exception as e:
            return {"error": str(e)}
    
    async def close(self):
        await self.client.aclose()


# =============================================================================
# AI AGENT APIS
# =============================================================================

class AIAgentClient:
    """
    AI Agent APIs from API Mega Library.
    
    Agents:
    - AI Web Agent (Apify) - Natural language web browsing
    - AI Company Researcher - Company research automation
    - AI Real Estate Agent - Property search by criteria
    """
    
    def __init__(self, apify_key: str = None, anthropic_key: str = None):
        self.apify_key = apify_key or os.getenv("APIFY_API_KEY", "")
        self.anthropic_key = anthropic_key or os.getenv("ANTHROPIC_API_KEY", "")
        self.client = httpx.AsyncClient(timeout=120.0)
    
    async def run_web_agent(
        self,
        task: str,
        start_url: str = None,
        max_steps: int = 10
    ) -> Dict[str, Any]:
        """
        Run AI Web Agent for natural language web tasks.
        
        Examples:
        - "Find the zoning ordinance for Palm Bay, FL"
        - "Get the comprehensive plan FLU map for Brevard County"
        """
        if not self.apify_key:
            return {"error": "APIFY_API_KEY not configured"}
        
        actor_id = "apify/ai-web-agent"
        
        payload = {
            "task": task,
            "startUrl": start_url,
            "maxSteps": max_steps,
            "model": "gpt-4o"
        }
        
        try:
            response = await self.client.post(
                f"https://api.apify.com/v2/acts/{actor_id}/runs",
                params={"token": self.apify_key},
                json=payload
            )
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    async def research_company(self, company_name: str) -> Dict[str, Any]:
        """
        Research a company (useful for plaintiff research in foreclosures).
        """
        if not self.apify_key:
            return {"error": "APIFY_API_KEY not configured"}
        
        actor_id = "louisdeconinck/ai-company-researcher-agent"
        
        payload = {
            "companyName": company_name,
            "includeLinkedIn": True,
            "includeNews": True
        }
        
        try:
            response = await self.client.post(
                f"https://api.apify.com/v2/acts/{actor_id}/runs",
                params={"token": self.apify_key},
                json=payload
            )
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    async def close(self):
        await self.client.aclose()


# =============================================================================
# GOVERNMENT DATA APIS
# =============================================================================

class GovernmentDataClient:
    """
    Government data APIs for zoning and land use.
    """
    
    # Florida Open Data Portal
    FL_OPEN_DATA = "https://opendata.arcgis.com/datasets"
    
    # FEMA National Flood Hazard Layer
    FEMA_NFHL = "https://hazards.fema.gov/gis/nfhl/rest/services"
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def get_flood_zone(
        self,
        latitude: float,
        longitude: float
    ) -> Dict[str, Any]:
        """Get FEMA flood zone at coordinates."""
        endpoint = f"{self.FEMA_NFHL}/public/NFHL/MapServer/28/query"
        
        params = {
            "geometry": f"{longitude},{latitude}",
            "geometryType": "esriGeometryPoint",
            "spatialRel": "esriSpatialRelIntersects",
            "outFields": "FLD_ZONE,ZONE_SUBTY,SFHA_TF",
            "returnGeometry": "false",
            "f": "json"
        }
        
        try:
            response = await self.client.get(endpoint, params=params)
            data = response.json()
            
            features = data.get("features", [])
            if features:
                attrs = features[0].get("attributes", {})
                zone = attrs.get("FLD_ZONE", "X")
                
                zone_descriptions = {
                    "A": "High Risk - 1% annual flood",
                    "AE": "High Risk with BFE",
                    "AH": "High Risk - Shallow",
                    "AO": "High Risk - Sheet Flow",
                    "V": "High Risk - Coastal",
                    "VE": "High Risk - Coastal with BFE",
                    "X": "Minimal Risk",
                    "B": "Moderate Risk (0.2%)",
                    "C": "Minimal Risk"
                }
                
                return {
                    "flood_zone": zone,
                    "zone_subtype": attrs.get("ZONE_SUBTY"),
                    "in_sfha": attrs.get("SFHA_TF") == "T",
                    "description": zone_descriptions.get(zone, "Unknown"),
                    "coordinates": {"lat": latitude, "lon": longitude}
                }
            
            return {
                "flood_zone": "X",
                "in_sfha": False,
                "description": "Minimal flood hazard"
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    async def close(self):
        await self.client.aclose()


# =============================================================================
# MCP SERVER REFERENCES
# =============================================================================

MCP_SERVERS = {
    "context7": {
        "name": "Context7 MCP Server",
        "description": "Up-to-date code documentation",
        "url": "https://apify.com/agentify/context7-mcp-server",
        "priority": "HIGH",
        "use_case": "Claude Code documentation lookup"
    },
    "gemini": {
        "name": "Gemini AI MCP Server",
        "description": "Gemini integration for Smart Router",
        "url": "https://apify.com/bhansalisoft/gemini-ai-mcp-server",
        "priority": "MEDIUM",
        "use_case": "Smart Router fallback"
    },
    "figma": {
        "name": "Figma MCP Server",
        "description": "Figma design access",
        "url": "https://apify.com/woundless_vehicle/figma-mcp-server",
        "priority": "LOW",
        "use_case": "UI/UX design integration"
    },
    "calculator": {
        "name": "Calculator MCP Server",
        "description": "Math operations",
        "url": "https://apify.com/matymar/calculator-mcp-server",
        "priority": "LOW",
        "use_case": "Financial calculations"
    }
}


# =============================================================================
# AGGREGATED API CLIENT
# =============================================================================

class SPDAPIClient:
    """
    Unified client for all SPD/ZOD API integrations.
    """
    
    def __init__(self):
        self.real_estate = ApifyRealEstateClient()
        self.census = CensusAPIClient()
        self.ai_agents = AIAgentClient()
        self.government = GovernmentDataClient()
    
    async def enrich_parcel(
        self,
        address: str,
        zip_code: str
    ) -> Dict[str, Any]:
        """
        Enrich parcel data from multiple sources.
        
        Returns combined data from:
        - Census demographics
        - Flood zone
        - Zillow estimate (if available)
        """
        results = await asyncio.gather(
            self.census.get_demographics_by_zip(zip_code),
            self.census.geocode_address(address),
            return_exceptions=True
        )
        
        demographics = results[0] if not isinstance(results[0], Exception) else {}
        geocode = results[1] if not isinstance(results[1], Exception) else {}
        
        # Get flood zone if we have coordinates
        flood_data = {}
        if geocode.get("latitude") and geocode.get("longitude"):
            flood_data = await self.government.get_flood_zone(
                geocode["latitude"],
                geocode["longitude"]
            )
        
        return {
            "address": address,
            "zip_code": zip_code,
            "geocode": geocode,
            "demographics": demographics,
            "flood_zone": flood_data,
            "enriched_at": datetime.utcnow().isoformat()
        }
    
    async def get_market_data(self, zip_code: str) -> Dict[str, Any]:
        """Get comprehensive market data for a zip code."""
        demographics = await self.census.get_demographics_by_zip(zip_code)
        
        # Add derived metrics
        if not demographics.get("error"):
            pop = demographics.get("population", 0)
            income = demographics.get("median_income", 0)
            home_value = demographics.get("median_home_value", 0)
            
            demographics["price_to_income_ratio"] = round(
                home_value / income, 2
            ) if income > 0 else 0
            
            demographics["affordability_score"] = (
                "HIGH" if demographics["price_to_income_ratio"] < 3
                else "MEDIUM" if demographics["price_to_income_ratio"] < 5
                else "LOW"
            )
        
        return demographics
    
    async def close(self):
        await asyncio.gather(
            self.real_estate.close(),
            self.census.close(),
            self.ai_agents.close(),
            self.government.close()
        )


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

async def enrich_parcel_data(address: str, zip_code: str) -> Dict[str, Any]:
    """Convenience function for parcel enrichment."""
    client = SPDAPIClient()
    try:
        return await client.enrich_parcel(address, zip_code)
    finally:
        await client.close()


async def get_market_data(zip_code: str) -> Dict[str, Any]:
    """Convenience function for market data."""
    client = CensusAPIClient()
    try:
        return await client.get_demographics_by_zip(zip_code)
    finally:
        await client.close()


async def get_flood_zone(lat: float, lon: float) -> Dict[str, Any]:
    """Convenience function for flood zone lookup."""
    client = GovernmentDataClient()
    try:
        return await client.get_flood_zone(lat, lon)
    finally:
        await client.close()
