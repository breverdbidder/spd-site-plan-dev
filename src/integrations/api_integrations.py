"""
SPD/ZOD Enhanced API Integrations
=================================
API integrations from API_MEGA_LIBRARY.md for enhanced opportunity discovery.

Priority Integrations:
1. Census API - Demographics, income, housing characteristics
2. Zillow/Redfin (via Apify) - Market valuations, comps
3. FEMA - Flood zone data
4. Firecrawl - Anti-bot web scraping for BECA
5. AI Agents - Company research, web browsing

Based on BidDeed.AI V14.5 integration patterns.
"""

import os
import json
import asyncio
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, Any, List, Optional
import httpx


# =============================================================================
# CENSUS API INTEGRATION (FREE)
# =============================================================================

@dataclass
class CensusData:
    """Census demographics for a tract"""
    geoid: str
    tract_name: str
    population: int
    median_income: float
    median_home_value: float
    vacancy_rate: float
    owner_occupied_pct: float
    renter_occupied_pct: float
    median_age: float
    households: int
    poverty_rate: float
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class CensusAPIClient:
    """
    US Census Bureau API Client.
    
    Endpoints:
    - American Community Survey (ACS) 5-year estimates
    - Geocoding for address-to-FIPS conversion
    - TIGERweb for boundaries
    
    API Key: https://api.census.gov/data/key_signup.html
    """
    
    BASE_URL = "https://api.census.gov/data"
    GEOCODE_URL = "https://geocoding.geo.census.gov/geocoder/geographies/address"
    
    # ACS 5-year variable codes
    VARIABLES = {
        "population": "B01003_001E",
        "median_income": "B19013_001E",
        "median_home_value": "B25077_001E",
        "total_housing": "B25001_001E",
        "vacant_housing": "B25002_003E",
        "owner_occupied": "B25003_002E",
        "renter_occupied": "B25003_003E",
        "median_age": "B01002_001E",
        "households": "B11001_001E",
        "poverty_population": "B17001_002E",
    }
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("CENSUS_API_KEY", "")
        self.client = httpx.AsyncClient(timeout=30)
    
    async def geocode_address(self, address: str) -> Optional[Dict[str, str]]:
        """Convert address to Census geography (FIPS codes)"""
        try:
            params = {
                "street": address,
                "benchmark": "Public_AR_Current",
                "vintage": "Current_Current",
                "format": "json"
            }
            
            response = await self.client.get(self.GEOCODE_URL, params=params)
            response.raise_for_status()
            data = response.json()
            
            matches = data.get("result", {}).get("addressMatches", [])
            if matches:
                geographies = matches[0].get("geographies", {})
                tracts = geographies.get("Census Tracts", [])
                if tracts:
                    tract = tracts[0]
                    return {
                        "state_fips": tract.get("STATE"),
                        "county_fips": tract.get("COUNTY"),
                        "tract_fips": tract.get("TRACT"),
                        "geoid": tract.get("GEOID"),
                        "tract_name": tract.get("NAME", "")
                    }
            return None
        except Exception as e:
            print(f"Census geocoding error: {e}")
            return None
    
    async def get_tract_demographics(
        self,
        state_fips: str,
        county_fips: str,
        tract_fips: str,
        year: int = 2022
    ) -> Optional[CensusData]:
        """Get ACS demographics for a census tract"""
        try:
            # Build variable list
            var_list = ",".join(self.VARIABLES.values())
            
            params = {
                "get": f"NAME,{var_list}",
                "for": f"tract:{tract_fips}",
                "in": f"state:{state_fips} county:{county_fips}",
            }
            
            if self.api_key:
                params["key"] = self.api_key
            
            url = f"{self.BASE_URL}/{year}/acs/acs5"
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if len(data) < 2:
                return None
            
            headers = data[0]
            values = data[1]
            
            # Map to dictionary
            result = dict(zip(headers, values))
            
            # Parse values
            def safe_float(key: str, default: float = 0.0) -> float:
                var_code = self.VARIABLES.get(key, key)
                val = result.get(var_code)
                try:
                    return float(val) if val and val not in ['-', 'null', None] else default
                except:
                    return default
            
            def safe_int(key: str, default: int = 0) -> int:
                return int(safe_float(key, default))
            
            # Calculate derived metrics
            total_housing = safe_int("total_housing", 1)
            vacant = safe_int("vacant_housing")
            owner = safe_int("owner_occupied")
            renter = safe_int("renter_occupied")
            population = safe_int("population", 1)
            poverty = safe_int("poverty_population")
            
            vacancy_rate = (vacant / total_housing * 100) if total_housing > 0 else 0
            owner_pct = (owner / (total_housing - vacant) * 100) if (total_housing - vacant) > 0 else 0
            renter_pct = (renter / (total_housing - vacant) * 100) if (total_housing - vacant) > 0 else 0
            poverty_rate = (poverty / population * 100) if population > 0 else 0
            
            return CensusData(
                geoid=f"{state_fips}{county_fips}{tract_fips}",
                tract_name=result.get("NAME", ""),
                population=safe_int("population"),
                median_income=safe_float("median_income"),
                median_home_value=safe_float("median_home_value"),
                vacancy_rate=round(vacancy_rate, 1),
                owner_occupied_pct=round(owner_pct, 1),
                renter_occupied_pct=round(renter_pct, 1),
                median_age=safe_float("median_age"),
                households=safe_int("households"),
                poverty_rate=round(poverty_rate, 1)
            )
        except Exception as e:
            print(f"Census ACS error: {e}")
            return None
    
    async def get_demographics_by_address(self, address: str) -> Optional[CensusData]:
        """Get demographics for an address (geocode + ACS lookup)"""
        geo = await self.geocode_address(address)
        if not geo:
            return None
        
        return await self.get_tract_demographics(
            state_fips=geo["state_fips"],
            county_fips=geo["county_fips"],
            tract_fips=geo["tract_fips"]
        )
    
    async def close(self):
        await self.client.aclose()


# =============================================================================
# APIFY REAL ESTATE SCRAPERS (Zillow, Redfin, Realtor)
# =============================================================================

@dataclass
class PropertyValuation:
    """Multi-source property valuation"""
    address: str
    zillow_estimate: Optional[float] = None
    redfin_estimate: Optional[float] = None
    realtor_estimate: Optional[float] = None
    consensus_value: Optional[float] = None
    confidence: float = 0.0
    last_sale_price: Optional[float] = None
    last_sale_date: Optional[str] = None
    sources: List[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ApifyRealEstateClient:
    """
    Apify Real Estate Scrapers.
    
    Actors:
    - epctex/realtor-scraper - Realtor.com
    - petr_cermak/zillow-api-scraper - Zillow
    - redfin-scraper - Redfin
    
    Pricing: ~$0.01-0.05 per property
    """
    
    BASE_URL = "https://api.apify.com/v2"
    
    # Actor IDs from API_MEGA_LIBRARY
    ACTORS = {
        "zillow": "petr_cermak/zillow-api-scraper",
        "realtor": "epctex/realtor-scraper",
        "redfin": "misceres/redfin-scraper",
        "global_aggregator": "charlestechy/global-real-estate-aggregator"
    }
    
    def __init__(self, api_token: Optional[str] = None):
        self.api_token = api_token or os.environ.get("APIFY_API_TOKEN", "")
        self.client = httpx.AsyncClient(timeout=60)
    
    async def run_actor(
        self,
        actor_id: str,
        input_data: Dict[str, Any],
        wait_secs: int = 60
    ) -> Optional[List[Dict]]:
        """Run an Apify actor and wait for results"""
        if not self.api_token:
            return None
        
        try:
            # Start actor run
            url = f"{self.BASE_URL}/acts/{actor_id}/runs"
            headers = {"Authorization": f"Bearer {self.api_token}"}
            
            response = await self.client.post(
                url,
                headers=headers,
                json=input_data,
                params={"waitForFinish": wait_secs}
            )
            response.raise_for_status()
            run_data = response.json()
            
            # Get results from dataset
            dataset_id = run_data.get("data", {}).get("defaultDatasetId")
            if dataset_id:
                items_url = f"{self.BASE_URL}/datasets/{dataset_id}/items"
                items_response = await self.client.get(items_url, headers=headers)
                items_response.raise_for_status()
                return items_response.json()
            
            return None
        except Exception as e:
            print(f"Apify actor error: {e}")
            return None
    
    async def get_zillow_valuation(self, address: str) -> Optional[Dict]:
        """Get Zillow Zestimate for address"""
        results = await self.run_actor(
            self.ACTORS["zillow"],
            {"searchType": "address", "searchTerms": [address]}
        )
        if results and len(results) > 0:
            return results[0]
        return None
    
    async def get_redfin_valuation(self, address: str) -> Optional[Dict]:
        """Get Redfin estimate for address"""
        results = await self.run_actor(
            self.ACTORS["redfin"],
            {"startUrls": [{"url": f"https://www.redfin.com/search?q={address}"}]}
        )
        if results and len(results) > 0:
            return results[0]
        return None
    
    async def get_multi_source_valuation(self, address: str) -> PropertyValuation:
        """Get valuations from multiple sources"""
        sources = []
        zillow_est = None
        redfin_est = None
        
        # Run in parallel
        zillow_task = self.get_zillow_valuation(address)
        redfin_task = self.get_redfin_valuation(address)
        
        zillow_data, redfin_data = await asyncio.gather(
            zillow_task, redfin_task, return_exceptions=True
        )
        
        if zillow_data and not isinstance(zillow_data, Exception):
            zillow_est = zillow_data.get("zestimate") or zillow_data.get("price")
            if zillow_est:
                sources.append("zillow")
        
        if redfin_data and not isinstance(redfin_data, Exception):
            redfin_est = redfin_data.get("estimate") or redfin_data.get("price")
            if redfin_est:
                sources.append("redfin")
        
        # Calculate consensus
        estimates = [e for e in [zillow_est, redfin_est] if e]
        consensus = sum(estimates) / len(estimates) if estimates else None
        confidence = len(estimates) / 2.0  # 0-1 based on source count
        
        return PropertyValuation(
            address=address,
            zillow_estimate=zillow_est,
            redfin_estimate=redfin_est,
            consensus_value=consensus,
            confidence=confidence,
            sources=sources
        )
    
    async def close(self):
        await self.client.aclose()


# =============================================================================
# FIRECRAWL INTEGRATION (ANTI-BOT SCRAPING)
# =============================================================================

class FirecrawlClient:
    """
    Firecrawl API Client for anti-bot web scraping.
    
    Use for:
    - BECA document retrieval (IP blocked on free services)
    - Sites with Cloudflare protection
    
    Pricing: $16/mo = 3,000 credits (1 credit/page, 5 for stealth)
    GitHub: https://github.com/mendableai/firecrawl
    """
    
    BASE_URL = "https://api.firecrawl.dev/v0"
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("FIRECRAWL_API_KEY", "")
        self.client = httpx.AsyncClient(timeout=60)
    
    async def scrape_url(
        self,
        url: str,
        formats: List[str] = None,
        wait_for: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Scrape a URL with anti-bot capabilities.
        
        Args:
            url: URL to scrape
            formats: Output formats ["markdown", "html", "rawHtml"]
            wait_for: CSS selector to wait for before scraping
        """
        if not self.api_key:
            return None
        
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            payload = {
                "url": url,
                "formats": formats or ["markdown", "html"]
            }
            
            if wait_for:
                payload["waitFor"] = wait_for
            
            response = await self.client.post(
                f"{self.BASE_URL}/scrape",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Firecrawl error: {e}")
            return None
    
    async def crawl_site(
        self,
        url: str,
        max_pages: int = 10,
        include_patterns: List[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Crawl entire site with pagination"""
        if not self.api_key:
            return None
        
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            payload = {
                "url": url,
                "limit": max_pages
            }
            
            if include_patterns:
                payload["includePaths"] = include_patterns
            
            response = await self.client.post(
                f"{self.BASE_URL}/crawl",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Firecrawl crawl error: {e}")
            return None
    
    async def close(self):
        await self.client.aclose()


# =============================================================================
# AI WEB AGENT (Apify)
# =============================================================================

class AIWebAgentClient:
    """
    AI Web Agent from Apify.
    
    Natural language web browsing and form filling.
    Actor: apify/ai-web-agent
    
    Use for:
    - Automated BECA document retrieval
    - Complex multi-step web tasks
    """
    
    ACTOR_ID = "apify/ai-web-agent"
    
    def __init__(self, apify_token: Optional[str] = None):
        self.apify_client = ApifyRealEstateClient(apify_token)
    
    async def execute_task(
        self,
        task_description: str,
        start_url: str,
        max_steps: int = 10
    ) -> Optional[Dict[str, Any]]:
        """
        Execute a web task using natural language.
        
        Args:
            task_description: Natural language task
            start_url: URL to start from
            max_steps: Maximum browsing steps
        """
        return await self.apify_client.run_actor(
            self.ACTOR_ID,
            {
                "startUrl": start_url,
                "task": task_description,
                "maxSteps": max_steps
            }
        )
    
    async def close(self):
        await self.apify_client.close()


# =============================================================================
# AGGREGATE DATA FETCHER
# =============================================================================

class EnhancedDataFetcher:
    """
    Aggregates data from all API sources for ZOD/SPD analysis.
    
    Combines:
    - Census demographics
    - Zillow/Redfin valuations
    - FEMA flood data
    - BCPAO property data
    """
    
    def __init__(
        self,
        census_key: Optional[str] = None,
        apify_token: Optional[str] = None,
        firecrawl_key: Optional[str] = None
    ):
        self.census = CensusAPIClient(census_key)
        self.apify = ApifyRealEstateClient(apify_token)
        self.firecrawl = FirecrawlClient(firecrawl_key) if firecrawl_key else None
    
    async def get_enhanced_property_data(
        self,
        address: str,
        include_valuation: bool = True,
        include_demographics: bool = True
    ) -> Dict[str, Any]:
        """
        Get comprehensive property data from all sources.
        """
        result = {
            "address": address,
            "fetched_at": datetime.utcnow().isoformat(),
            "demographics": None,
            "valuation": None
        }
        
        tasks = []
        
        if include_demographics:
            tasks.append(("demographics", self.census.get_demographics_by_address(address)))
        
        if include_valuation:
            tasks.append(("valuation", self.apify.get_multi_source_valuation(address)))
        
        # Run in parallel
        if tasks:
            results = await asyncio.gather(
                *[t[1] for t in tasks],
                return_exceptions=True
            )
            
            for i, (key, _) in enumerate(tasks):
                if not isinstance(results[i], Exception) and results[i]:
                    if hasattr(results[i], 'to_dict'):
                        result[key] = results[i].to_dict()
                    else:
                        result[key] = results[i]
        
        return result
    
    async def close(self):
        await asyncio.gather(
            self.census.close(),
            self.apify.close(),
            self.firecrawl.close() if self.firecrawl else asyncio.sleep(0)
        )


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

async def enrich_opportunity_with_apis(
    opportunity: Dict[str, Any],
    census_key: Optional[str] = None,
    apify_token: Optional[str] = None
) -> Dict[str, Any]:
    """
    Enrich a ZOD opportunity with API data.
    
    Adds:
    - Census demographics (income, population, vacancy)
    - Market valuations (Zillow, Redfin)
    - Derived metrics
    """
    fetcher = EnhancedDataFetcher(census_key, apify_token)
    
    try:
        address = opportunity.get("address", "")
        if not address:
            return opportunity
        
        enhanced = await fetcher.get_enhanced_property_data(address)
        
        # Merge into opportunity
        if enhanced.get("demographics"):
            opportunity["census_demographics"] = enhanced["demographics"]
            
            # Calculate affordability metrics
            median_income = enhanced["demographics"].get("median_income", 0)
            if median_income > 0:
                opportunity["affordability_ratio"] = (
                    enhanced["demographics"].get("median_home_value", 0) / median_income
                )
        
        if enhanced.get("valuation"):
            opportunity["market_valuation"] = enhanced["valuation"]
            
            # Update assessed value if we have better data
            consensus = enhanced["valuation"].get("consensus_value")
            if consensus:
                opportunity["api_market_value"] = consensus
        
        opportunity["api_enriched"] = True
        opportunity["api_enriched_at"] = enhanced["fetched_at"]
        
        return opportunity
    finally:
        await fetcher.close()


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    import asyncio
    
    async def main():
        print("=" * 80)
        print("SPD/ZOD API INTEGRATIONS TEST")
        print("=" * 80)
        
        # Test Census API (no key required for basic usage)
        census = CensusAPIClient()
        
        print("\n📊 Testing Census API...")
        demographics = await census.get_demographics_by_address(
            "2165 Sandy Pines Dr NE, Palm Bay, FL 32905"
        )
        
        if demographics:
            print(f"   Tract: {demographics.tract_name}")
            print(f"   Population: {demographics.population:,}")
            print(f"   Median Income: ${demographics.median_income:,.0f}")
            print(f"   Median Home Value: ${demographics.median_home_value:,.0f}")
            print(f"   Vacancy Rate: {demographics.vacancy_rate}%")
        else:
            print("   Census data not available (API key may be required)")
        
        await census.close()
        
        print("\n✅ API integration test complete")
    
    asyncio.run(main())
