#!/usr/bin/env python3
"""
Municode Scraper - Production Zoning Data Extraction
SPD Site Plan Development - Core Component #2

Extracts zoning districts and site plan requirements from Municode library.
"Data is the Moat" - this scraper builds the competitive advantage.

Features:
- Playwright-based (headless Chrome) for reliability
- Anti-detection measures (stealth mode, random delays)
- Automatic retry with exponential backoff
- Structured data extraction with validation
- Direct integration with SupabaseClient (Core #1)

Author: BidDeed.AI / Everest Capital USA
"""

import os
import re
import json
import uuid
import random
import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from urllib.parse import urljoin, urlparse

logger = logging.getLogger(__name__)


class ScrapeStatus(Enum):
    """Scrape operation status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


@dataclass
class ScrapedZoning:
    """Scraped zoning district data"""
    code: str
    name: str
    description: Optional[str] = None
    category: Optional[str] = None  # residential, commercial, industrial, agricultural, mixed
    source_url: Optional[str] = None
    source_section: Optional[str] = None
    raw_text: Optional[str] = None


@dataclass
class ScrapedRequirement:
    """Scraped site plan requirement data"""
    requirement_type: str  # parking, setback, landscaping, stormwater, etc.
    description: str
    standard: Optional[str] = None
    zoning_code: Optional[str] = None  # None = applies to all zones
    source_section: Optional[str] = None
    source_url: Optional[str] = None


@dataclass
class ScrapeResult:
    """Result of a scrape operation"""
    municipality_name: str
    county: str
    state: str = "FL"
    status: ScrapeStatus = ScrapeStatus.PENDING
    zoning_districts: List[ScrapedZoning] = field(default_factory=list)
    requirements: List[ScrapedRequirement] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: float = 0.0
    pages_scraped: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "municipality_name": self.municipality_name,
            "county": self.county,
            "state": self.state,
            "status": self.status.value,
            "zoning_count": len(self.zoning_districts),
            "requirements_count": len(self.requirements),
            "errors": self.errors,
            "warnings": self.warnings,
            "duration_seconds": self.duration_seconds,
            "pages_scraped": self.pages_scraped
        }


# Municode URL patterns for Florida municipalities
MUNICODE_BASE = "https://library.municode.com"
FL_MUNICODE_PATTERN = "https://library.municode.com/fl/{municipality}"

# Known Florida municipalities on Municode (partial list for Brevard County focus)
BREVARD_MUNICIPALITIES = {
    "malabar": {
        "name": "Malabar",
        "county": "Brevard",
        "url": "https://library.municode.com/fl/malabar",
        "zoning_path": "/codes/code_of_ordinances?nodeId=PTIICOOR_CH22ZO"
    },
    "palm_bay": {
        "name": "Palm Bay",
        "county": "Brevard",
        "url": "https://library.municode.com/fl/palm_bay",
        "zoning_path": "/codes/code_of_ordinances?nodeId=PTIICOOR_CH114ZO"
    },
    "melbourne": {
        "name": "Melbourne",
        "county": "Brevard",
        "url": "https://library.municode.com/fl/melbourne",
        "zoning_path": "/codes/code_of_ordinances?nodeId=SPBLADORE_CH14"
    },
    "titusville": {
        "name": "Titusville",
        "county": "Brevard",
        "url": "https://library.municode.com/fl/titusville",
        "zoning_path": "/codes/code_of_ordinances?nodeId=PTIICOOR_CH28ZO"
    },
    "cocoa": {
        "name": "Cocoa",
        "county": "Brevard", 
        "url": "https://library.municode.com/fl/cocoa",
        "zoning_path": "/codes/code_of_ordinances?nodeId=PTIICOOR_CH13ZO"
    },
    "rockledge": {
        "name": "Rockledge",
        "county": "Brevard",
        "url": "https://library.municode.com/fl/rockledge",
        "zoning_path": "/codes/code_of_ordinances?nodeId=PTIICOOR_CH22ZO"
    }
}

# Zoning category detection patterns
CATEGORY_PATTERNS = {
    "residential": [
        r"\b(residential|single.?family|multi.?family|duplex|apartment|dwelling|r-\d|rs-\d|rm-\d|rr)\b",
    ],
    "commercial": [
        r"\b(commercial|retail|office|business|shopping|c-\d|cc|cn|cb|co)\b",
    ],
    "industrial": [
        r"\b(industrial|manufacturing|warehouse|i-\d|li|hi|m-\d)\b",
    ],
    "agricultural": [
        r"\b(agricultural|farming|ag|a-\d|ru)\b",
    ],
    "mixed": [
        r"\b(mixed.?use|planned.?unit|pud|mu|pmd|tnd)\b",
    ],
    "institutional": [
        r"\b(institutional|public|civic|government|church|school|hospital)\b",
    ],
    "conservation": [
        r"\b(conservation|preservation|environmental|wetland|flood)\b",
    ]
}

# Requirement type detection patterns
REQUIREMENT_PATTERNS = {
    "parking": [
        r"\bparking\s+(requirement|standard|space|ratio)",
        r"\boff.?street\s+parking",
        r"\bvehicle\s+parking",
        r"\bparking\s+lot",
    ],
    "setback": [
        r"\bsetback",
        r"\byard\s+requirement",
        r"\bfront\s+yard",
        r"\brear\s+yard",
        r"\bside\s+yard",
        r"\bbuffer",
    ],
    "landscaping": [
        r"\blandscap",
        r"\btree\s+(requirement|preservation|protection)",
        r"\bgreen\s+space",
        r"\bvegetation",
        r"\bplanting",
    ],
    "stormwater": [
        r"\bstormwater",
        r"\bdrainage",
        r"\bretention",
        r"\bdetention",
        r"\brunoff",
        r"\bflood",
    ],
    "height": [
        r"\bheight\s+(limit|restriction|maximum)",
        r"\bbuilding\s+height",
        r"\bmaximum\s+height",
    ],
    "density": [
        r"\bdensity",
        r"\bdwelling\s+unit",
        r"\bunits\s+per\s+acre",
        r"\bfloor\s+area\s+ratio",
        r"\bfar\b",
    ],
    "lot_coverage": [
        r"\blot\s+coverage",
        r"\bimpervious",
        r"\bbuild.?able\s+area",
    ],
    "signage": [
        r"\bsign",
        r"\bsignage",
        r"\bbillboard",
    ],
    "lighting": [
        r"\blighting",
        r"\billumination",
        r"\boutdoor\s+light",
    ],
    "access": [
        r"\baccess",
        r"\bdriveway",
        r"\bcurb\s+cut",
        r"\bingress",
        r"\begress",
    ]
}


class MunicodeScraper:
    """
    Production Municode scraper with anti-detection and reliability features.
    
    Usage:
        scraper = MunicodeScraper()
        result = await scraper.scrape_municipality("malabar")
        
        # With Supabase storage
        from src.db.supabase_client import get_supabase_client
        scraper = MunicodeScraper(supabase_client=get_supabase_client())
        result = await scraper.scrape_and_store("malabar")
    """
    
    def __init__(
        self,
        supabase_client=None,
        headless: bool = True,
        timeout: int = 30000,
        retry_count: int = 3,
        min_delay: float = 1.0,
        max_delay: float = 3.0
    ):
        """
        Initialize scraper.
        
        Args:
            supabase_client: Optional SupabaseClient for direct storage
            headless: Run browser in headless mode
            timeout: Page timeout in milliseconds
            retry_count: Number of retries on failure
            min_delay: Minimum delay between requests (seconds)
            max_delay: Maximum delay between requests (seconds)
        """
        self.supabase = supabase_client
        self.headless = headless
        self.timeout = timeout
        self.retry_count = retry_count
        self.min_delay = min_delay
        self.max_delay = max_delay
        
        self._browser = None
        self._context = None
        self._page = None
    
    async def _init_browser(self):
        """Initialize Playwright browser with stealth settings"""
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            raise ImportError("playwright required: pip install playwright && playwright install chromium")
        
        self._playwright = await async_playwright().start()
        
        # Launch with stealth settings
        self._browser = await self._playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-accelerated-2d-canvas',
                '--disable-gpu'
            ]
        )
        
        # Create context with realistic viewport and user agent
        self._context = await self._browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='en-US',
            timezone_id='America/New_York'
        )
        
        # Add stealth scripts
        await self._context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
        """)
        
        self._page = await self._context.new_page()
        self._page.set_default_timeout(self.timeout)
        
        logger.info("Browser initialized with stealth settings")
    
    async def _close_browser(self):
        """Close browser and cleanup"""
        if self._page:
            await self._page.close()
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
        if hasattr(self, '_playwright'):
            await self._playwright.stop()
        
        self._page = None
        self._context = None
        self._browser = None
        logger.info("Browser closed")
    
    async def _random_delay(self):
        """Add random delay to avoid detection"""
        delay = random.uniform(self.min_delay, self.max_delay)
        await asyncio.sleep(delay)
    
    async def _navigate_with_retry(self, url: str) -> bool:
        """Navigate to URL with retry logic"""
        for attempt in range(self.retry_count):
            try:
                await self._random_delay()
                response = await self._page.goto(url, wait_until='domcontentloaded')
                
                if response and response.status == 200:
                    # Wait for content to load
                    await self._page.wait_for_load_state('networkidle', timeout=10000)
                    return True
                
                logger.warning(f"Non-200 status ({response.status if response else 'None'}) for {url}")
                
            except Exception as e:
                logger.warning(f"Navigation attempt {attempt + 1} failed: {e}")
                if attempt < self.retry_count - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        return False
    
    def _detect_category(self, code: str, name: str, description: str = "") -> Optional[str]:
        """Detect zoning category from code/name/description"""
        text = f"{code} {name} {description}".lower()
        
        for category, patterns in CATEGORY_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    return category
        
        return None
    
    def _detect_requirement_type(self, text: str) -> Optional[str]:
        """Detect requirement type from text"""
        text_lower = text.lower()
        
        for req_type, patterns in REQUIREMENT_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    return req_type
        
        return None
    
    async def _extract_zoning_from_toc(self, base_url: str) -> List[ScrapedZoning]:
        """Extract zoning districts from table of contents"""
        zones = []
        
        try:
            # Find zoning-related links in TOC
            toc_links = await self._page.query_selector_all('a[href*="nodeId"]')
            
            for link in toc_links:
                try:
                    text = await link.inner_text()
                    href = await link.get_attribute('href')
                    
                    # Look for zoning district patterns
                    # Common patterns: "Sec. 22-123. - R-1 Residential", "Division 3. - Commercial Districts"
                    zoning_patterns = [
                        r'(?:Sec\.?\s*[\d\-\.]+\s*[-–]\s*)?([A-Z]{1,3}[-\s]?\d*)\s*[-–]\s*(.+)',
                        r'(?:Article|Division)\s+\d+\.\s*[-–]\s*([A-Z]{1,3}[-\s]?\d*)\s+(.+)',
                        r'([A-Z]{1,3}[-\s]?\d+)\s+(?:district|zone)\s*[-–:]\s*(.+)',
                    ]
                    
                    for pattern in zoning_patterns:
                        match = re.search(pattern, text, re.IGNORECASE)
                        if match:
                            code = match.group(1).strip().upper().replace(' ', '-')
                            name = match.group(2).strip()
                            
                            # Skip if it looks like a section reference, not a zone
                            if any(skip in name.lower() for skip in ['purpose', 'intent', 'general', 'definitions']):
                                continue
                            
                            zone = ScrapedZoning(
                                code=code,
                                name=name,
                                category=self._detect_category(code, name),
                                source_url=urljoin(base_url, href) if href else None,
                                source_section=text[:100]
                            )
                            
                            # Avoid duplicates
                            if not any(z.code == zone.code for z in zones):
                                zones.append(zone)
                                logger.debug(f"Found zone: {code} - {name}")
                            break
                
                except Exception as e:
                    logger.debug(f"Error processing link: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Error extracting zoning from TOC: {e}")
        
        return zones
    
    async def _extract_zoning_from_content(self, url: str) -> List[ScrapedZoning]:
        """Extract zoning districts from page content"""
        zones = []
        
        try:
            # Get main content
            content = await self._page.query_selector('#codebankContent, .content, main, article')
            if not content:
                content = await self._page.query_selector('body')
            
            if content:
                text = await content.inner_text()
                
                # Look for zoning district definitions
                # Pattern: "RS-1" or "R-1" followed by description
                pattern = r'\b([A-Z]{1,3}[-\s]?\d{0,2})\s*[-–:]\s*([A-Za-z][A-Za-z\s]{5,50}?)(?:district|zone|\.|\n)'
                
                matches = re.finditer(pattern, text, re.IGNORECASE)
                
                for match in matches:
                    code = match.group(1).strip().upper().replace(' ', '-')
                    name = match.group(2).strip()
                    
                    # Validate it looks like a zoning code
                    if len(code) < 2 or len(code) > 6:
                        continue
                    if len(name) < 5:
                        continue
                    
                    zone = ScrapedZoning(
                        code=code,
                        name=name,
                        category=self._detect_category(code, name),
                        source_url=url
                    )
                    
                    if not any(z.code == zone.code for z in zones):
                        zones.append(zone)
        
        except Exception as e:
            logger.error(f"Error extracting zoning from content: {e}")
        
        return zones
    
    async def _extract_requirements(self, url: str) -> List[ScrapedRequirement]:
        """Extract site plan requirements from page"""
        requirements = []
        
        try:
            content = await self._page.query_selector('#codebankContent, .content, main, article')
            if not content:
                content = await self._page.query_selector('body')
            
            if content:
                text = await content.inner_text()
                
                # Split into sections/paragraphs
                paragraphs = re.split(r'\n\s*\n', text)
                
                for para in paragraphs:
                    para = para.strip()
                    if len(para) < 20:
                        continue
                    
                    req_type = self._detect_requirement_type(para)
                    if req_type:
                        # Extract the key requirement text
                        # Look for patterns like "shall be", "must be", "required", etc.
                        requirement_match = re.search(
                            r'(.{0,200}(?:shall|must|required|minimum|maximum|at least|no more than).{0,200})',
                            para,
                            re.IGNORECASE | re.DOTALL
                        )
                        
                        description = requirement_match.group(1).strip() if requirement_match else para[:300]
                        
                        # Look for specific standards (numbers, ratios)
                        standard = None
                        standard_match = re.search(
                            r'(\d+(?:\.\d+)?\s*(?:feet|ft|inches|in|spaces|per|%|percent|units|acres?))',
                            description,
                            re.IGNORECASE
                        )
                        if standard_match:
                            standard = standard_match.group(1)
                        
                        req = ScrapedRequirement(
                            requirement_type=req_type,
                            description=description[:500],
                            standard=standard,
                            source_url=url
                        )
                        
                        # Avoid near-duplicates
                        if not any(
                            r.requirement_type == req.requirement_type and 
                            r.description[:50] == req.description[:50]
                            for r in requirements
                        ):
                            requirements.append(req)
                            logger.debug(f"Found requirement: {req_type}")
        
        except Exception as e:
            logger.error(f"Error extracting requirements: {e}")
        
        return requirements
    
    async def scrape_municipality(
        self,
        municipality_key: str,
        custom_url: Optional[str] = None
    ) -> ScrapeResult:
        """
        Scrape zoning and requirements for a municipality.
        
        Args:
            municipality_key: Key from BREVARD_MUNICIPALITIES or municipality slug
            custom_url: Optional custom Municode URL to use
        
        Returns:
            ScrapeResult with extracted data
        """
        # Get municipality info
        if municipality_key in BREVARD_MUNICIPALITIES:
            muni_info = BREVARD_MUNICIPALITIES[municipality_key]
            name = muni_info["name"]
            county = muni_info["county"]
            base_url = custom_url or muni_info["url"]
            zoning_url = base_url + muni_info.get("zoning_path", "")
        else:
            name = municipality_key.replace("_", " ").title()
            county = "Unknown"
            base_url = custom_url or f"{MUNICODE_BASE}/fl/{municipality_key}"
            zoning_url = base_url
        
        result = ScrapeResult(
            municipality_name=name,
            county=county,
            started_at=datetime.utcnow()
        )
        
        try:
            # Initialize browser
            await self._init_browser()
            result.status = ScrapeStatus.IN_PROGRESS
            
            # Navigate to zoning page
            logger.info(f"Scraping {name}: {zoning_url}")
            if not await self._navigate_with_retry(zoning_url):
                result.errors.append(f"Failed to load zoning page: {zoning_url}")
                result.status = ScrapeStatus.FAILED
                return result
            
            result.pages_scraped += 1
            
            # Extract zoning districts from TOC
            zones_toc = await self._extract_zoning_from_toc(base_url)
            result.zoning_districts.extend(zones_toc)
            
            # Extract from content
            zones_content = await self._extract_zoning_from_content(zoning_url)
            for zone in zones_content:
                if not any(z.code == zone.code for z in result.zoning_districts):
                    result.zoning_districts.append(zone)
            
            # Extract requirements
            requirements = await self._extract_requirements(zoning_url)
            result.requirements.extend(requirements)
            
            # Try to navigate to sub-pages for more data
            # Look for links to specific sections
            try:
                sub_links = await self._page.query_selector_all('a[href*="nodeId"]')
                visited_urls = {zoning_url}
                
                for link in sub_links[:10]:  # Limit to avoid too many requests
                    try:
                        href = await link.get_attribute('href')
                        text = await link.inner_text()
                        
                        if not href:
                            continue
                        
                        full_url = urljoin(base_url, href)
                        
                        if full_url in visited_urls:
                            continue
                        
                        # Only visit zoning-related pages
                        if not any(kw in text.lower() for kw in ['district', 'zone', 'parking', 'setback', 'landscap', 'site plan']):
                            continue
                        
                        visited_urls.add(full_url)
                        
                        if await self._navigate_with_retry(full_url):
                            result.pages_scraped += 1
                            
                            # Extract from this page
                            more_zones = await self._extract_zoning_from_content(full_url)
                            for zone in more_zones:
                                if not any(z.code == zone.code for z in result.zoning_districts):
                                    result.zoning_districts.append(zone)
                            
                            more_reqs = await self._extract_requirements(full_url)
                            for req in more_reqs:
                                if not any(
                                    r.requirement_type == req.requirement_type and 
                                    r.description[:50] == req.description[:50]
                                    for r in result.requirements
                                ):
                                    result.requirements.append(req)
                    
                    except Exception as e:
                        logger.debug(f"Error processing sub-link: {e}")
                        continue
            
            except Exception as e:
                result.warnings.append(f"Error processing sub-pages: {str(e)}")
            
            # Determine final status
            if result.zoning_districts or result.requirements:
                result.status = ScrapeStatus.COMPLETED if not result.errors else ScrapeStatus.PARTIAL
            else:
                result.status = ScrapeStatus.FAILED
                result.errors.append("No zoning districts or requirements found")
        
        except Exception as e:
            logger.error(f"Scrape failed: {e}")
            result.errors.append(str(e))
            result.status = ScrapeStatus.FAILED
        
        finally:
            await self._close_browser()
            result.completed_at = datetime.utcnow()
            result.duration_seconds = (result.completed_at - result.started_at).total_seconds()
        
        logger.info(
            f"Scrape completed: {name} - "
            f"{len(result.zoning_districts)} zones, "
            f"{len(result.requirements)} requirements, "
            f"{result.duration_seconds:.1f}s"
        )
        
        return result
    
    async def scrape_and_store(
        self,
        municipality_key: str,
        municipality_id: Optional[str] = None,
        custom_url: Optional[str] = None
    ) -> Tuple[ScrapeResult, Optional[str]]:
        """
        Scrape municipality and store results in Supabase.
        
        Args:
            municipality_key: Municipality identifier
            municipality_id: Existing municipality UUID (or will create new)
            custom_url: Optional custom URL
        
        Returns:
            Tuple of (ScrapeResult, pipeline_run_id)
        """
        if not self.supabase:
            raise ValueError("Supabase client required for storage")
        
        # Import data models from Core #1
        from src.db.supabase_client import Municipality, ZoningDistrict, SitePlanRequirement
        
        # Scrape the data
        result = await self.scrape_municipality(municipality_key, custom_url)
        
        if result.status == ScrapeStatus.FAILED:
            return result, None
        
        # Get or create municipality
        if not municipality_id:
            muni_info = BREVARD_MUNICIPALITIES.get(municipality_key, {})
            
            # Try to find existing
            existing = self.supabase.get_municipality_by_name(
                result.municipality_name,
                result.county
            )
            
            if existing:
                municipality_id = existing["id"]
            else:
                municipality_id = str(uuid.uuid4())
                
                muni = Municipality(
                    id=municipality_id,
                    name=result.municipality_name,
                    county=result.county,
                    state=result.state,
                    municode_url=muni_info.get("url"),
                    last_scraped=datetime.utcnow()
                )
                self.supabase.upsert_municipality(muni)
        
        # Create pipeline run
        run_id = self.supabase.create_pipeline_run(
            municipality_id=municipality_id,
            pipeline_type="municode_scrape",
            metadata={
                "source": "municode",
                "key": municipality_key,
                "started_at": result.started_at.isoformat() if result.started_at else None
            }
        )
        
        if run_id:
            self.supabase.update_pipeline_status(run_id, "in_progress", "storing_data")
        
        try:
            # Store zoning districts
            for scraped_zone in result.zoning_districts:
                zone = ZoningDistrict(
                    id=str(uuid.uuid4()),
                    municipality_id=municipality_id,
                    code=scraped_zone.code,
                    name=scraped_zone.name,
                    description=scraped_zone.description,
                    category=scraped_zone.category,
                    source_url=scraped_zone.source_url,
                    last_updated=datetime.utcnow()
                )
                self.supabase.upsert_zoning_district(zone)
            
            # Store requirements
            for scraped_req in result.requirements:
                req = SitePlanRequirement(
                    id=str(uuid.uuid4()),
                    municipality_id=municipality_id,
                    zoning_code=scraped_req.zoning_code,
                    requirement_type=scraped_req.requirement_type,
                    description=scraped_req.description,
                    standard=scraped_req.standard,
                    source_section=scraped_req.source_section,
                    source_url=scraped_req.source_url
                )
                self.supabase.upsert_site_plan_requirement(req)
            
            # Update pipeline run
            if run_id:
                self.supabase.update_pipeline_status(
                    run_id,
                    "completed",
                    results={
                        "zoning_count": len(result.zoning_districts),
                        "requirements_count": len(result.requirements),
                        "duration_seconds": result.duration_seconds
                    }
                )
            
            # Update municipality last_scraped
            muni = Municipality(
                id=municipality_id,
                name=result.municipality_name,
                county=result.county,
                state=result.state,
                last_scraped=datetime.utcnow()
            )
            self.supabase.upsert_municipality(muni)
            
            logger.info(f"Stored data for {result.municipality_name}: {municipality_id}")
        
        except Exception as e:
            logger.error(f"Error storing data: {e}")
            result.errors.append(f"Storage error: {str(e)}")
            
            if run_id:
                self.supabase.update_pipeline_status(run_id, "failed", error=str(e))
        
        return result, run_id


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

async def scrape_malabar_poc() -> ScrapeResult:
    """
    Replicate the Malabar POC scrape.
    Returns the scrape result without storage.
    """
    scraper = MunicodeScraper(headless=True)
    return await scraper.scrape_municipality("malabar")


async def scrape_and_store_municipality(
    municipality_key: str,
    supabase_client=None
) -> Tuple[ScrapeResult, Optional[str]]:
    """
    Convenience function to scrape and store a municipality.
    
    Args:
        municipality_key: Key from BREVARD_MUNICIPALITIES
        supabase_client: Optional client (will create if not provided)
    
    Returns:
        Tuple of (ScrapeResult, pipeline_run_id)
    """
    if supabase_client is None:
        from src.db.supabase_client import get_supabase_client
        supabase_client = get_supabase_client()
    
    scraper = MunicodeScraper(supabase_client=supabase_client, headless=True)
    return await scraper.scrape_and_store(municipality_key)


def get_available_municipalities() -> Dict[str, Dict]:
    """Get list of known municipalities that can be scraped"""
    return BREVARD_MUNICIPALITIES.copy()


if __name__ == "__main__":
    import sys
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    async def main():
        print("=" * 60)
        print("Municode Scraper - Test Run")
        print("=" * 60)
        
        # Default to Malabar POC
        municipality = sys.argv[1] if len(sys.argv) > 1 else "malabar"
        
        print(f"\nScraping: {municipality}")
        print("-" * 40)
        
        scraper = MunicodeScraper(headless=True)
        result = await scraper.scrape_municipality(municipality)
        
        print(f"\nStatus: {result.status.value}")
        print(f"Duration: {result.duration_seconds:.1f}s")
        print(f"Pages scraped: {result.pages_scraped}")
        print(f"\nZoning Districts: {len(result.zoning_districts)}")
        
        for zone in result.zoning_districts[:10]:
            print(f"  • {zone.code}: {zone.name} ({zone.category or 'unknown'})")
        
        if len(result.zoning_districts) > 10:
            print(f"  ... and {len(result.zoning_districts) - 10} more")
        
        print(f"\nRequirements: {len(result.requirements)}")
        for req in result.requirements[:5]:
            print(f"  • {req.requirement_type}: {req.description[:60]}...")
        
        if result.errors:
            print(f"\nErrors: {result.errors}")
        
        if result.warnings:
            print(f"\nWarnings: {result.warnings}")
    
    asyncio.run(main())
