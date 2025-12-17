#!/usr/bin/env python3
"""
BCPAO Property Scraper for Rough Diamond Detection
Target: County AU/GU parcels near West Melbourne/Palm Bay city limits

Part of SPD Site Plan Development Pipeline
Author: BidDeed.AI / Everest Capital USA
"""

import json
import urllib.request
import urllib.parse
import ssl
import time
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE


class BCPAOConfig:
    BASE_URL = "https://www.bcpao.us/api/v1/search"
    MAX_RETRIES = 3
    TIMEOUT = 45
    RATE_LIMIT_DELAY = 1.0
    
    TARGET_ZIPS = {
        "32904": {"name": "West Melbourne", "priority": 1},
        "32934": {"name": "West Melbourne/Viera", "priority": 1},
        "32940": {"name": "Melbourne/Viera", "priority": 2},
        "32905": {"name": "Palm Bay North", "priority": 1},
        "32907": {"name": "Palm Bay Central", "priority": 1},
        "32908": {"name": "Palm Bay West", "priority": 2},
        "32909": {"name": "Palm Bay South", "priority": 2},
    }
    
    UNINCORP_KEYWORDS = ["UNINCORP", "UNINC", "COUNTY"]
    
    TARGET_LAND_USES = {
        "AG": ["AGRICULTURAL", "TIMBER", "GRAZING", "PASTURE", "GROVE", "FARM"],
        "VACANT": ["VACANT", "UNDEVELOPED", "RAW LAND"],
    }


class BCPAOScraper:
    def __init__(self, config: BCPAOConfig = None):
        self.config = config or BCPAOConfig()
        self.session_results = []
        
    def _make_request(self, params: Dict[str, str], max_results: int = 500) -> List[Dict]:
        query_parts = [f"{k}={urllib.parse.quote(str(v))}" for k, v in params.items()]
        url = f"{self.config.BASE_URL}?{'&'.join(query_parts)}"
        
        for attempt in range(self.config.MAX_RETRIES):
            try:
                req = urllib.request.Request(url, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept': 'application/json'
                })
                
                with urllib.request.urlopen(req, context=ssl_context, timeout=self.config.TIMEOUT) as response:
                    data = json.loads(response.read().decode())
                    rows = data.get('Rows', []) if isinstance(data, dict) else []
                    logger.info(f"Retrieved {len(rows)} parcels")
                    return rows[:max_results]
                    
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                if attempt < self.config.MAX_RETRIES - 1:
                    time.sleep(2 ** attempt)
                    
        return []
    
    def search_unincorporated_parcels(self, min_acres: float = 2, max_acres: float = 100) -> List[Dict]:
        all_results = []
        for district_num in range(1, 6):
            district_name = f"UNINCORP DISTRICT {district_num}"
            logger.info(f"Searching {district_name}")
            results = self._make_request({
                "type": "activeaccount",
                "taxingDistrict": district_name,
                "acres": f"{min_acres}-{max_acres}"
            })
            all_results.extend(results)
            time.sleep(self.config.RATE_LIMIT_DELAY)
        return all_results
    
    def search_by_zip(self, zip_code: str, land_use: str = "6", min_acres: float = 2) -> List[Dict]:
        return self._make_request({
            "type": "activeaccount",
            "zip": zip_code,
            "landuse": land_use,
            "acres": f"{min_acres}-200"
        })
    
    def is_unincorporated(self, parcel: Dict) -> bool:
        district = str(parcel.get('taxingDistrict', '')).upper()
        return any(kw in district for kw in self.config.UNINCORP_KEYWORDS)
    
    def is_target_land_use(self, parcel: Dict) -> bool:
        land_use = str(parcel.get('landUseCode', '')).upper()
        for keywords in self.config.TARGET_LAND_USES.values():
            if any(kw in land_use for kw in keywords):
                return True
        return False
    
    def run_full_search(self) -> List[Dict]:
        logger.info("BCPAO ROUGH DIAMOND SEARCH - Starting")
        all_parcels = []
        seen_accounts = set()
        
        # Strategy 1: Unincorporated large parcels
        uninc_results = self.search_unincorporated_parcels(5, 100)
        for p in uninc_results:
            if self.is_target_land_use(p):
                account = p.get('account')
                if account and account not in seen_accounts:
                    seen_accounts.add(account)
                    all_parcels.append(p)
        
        # Strategy 2: AG by zip
        for zip_code, info in self.config.TARGET_ZIPS.items():
            if info['priority'] == 1:
                results = self.search_by_zip(zip_code, "6", 2)
                for p in results:
                    account = p.get('account')
                    if account and account not in seen_accounts:
                        seen_accounts.add(account)
                        all_parcels.append(p)
                time.sleep(self.config.RATE_LIMIT_DELAY)
        
        logger.info(f"Total unique parcels: {len(all_parcels)}")
        self.session_results = all_parcels
        return all_parcels
    
    def export_results(self, filepath: str) -> None:
        output = {
            "generated": datetime.now().isoformat(),
            "total_parcels": len(self.session_results),
            "parcels": self.session_results
        }
        with open(filepath, 'w') as f:
            json.dump(output, f, indent=2, default=str)
        logger.info(f"Exported to {filepath}")


if __name__ == "__main__":
    scraper = BCPAOScraper()
    scraper.run_full_search()
    scraper.export_results("bcpao_results.json")
