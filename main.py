#!/usr/bin/env python3
"""
SPD Rough Diamond Pipeline - Main Entry Point
BCPAO parcel scraping, scoring, and storage for annexation arbitrage

Usage:
    python main.py                    # Run full pipeline
    python main.py --scrape-only      # Just scrape BCPAO
    python main.py --score-only FILE  # Score existing JSON file
    python main.py --help             # Show help

Author: BidDeed.AI / Everest Capital USA
"""

import argparse
import json
import sys
import os
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))


def run_scraper(output_file: str = None) -> dict:
    """Run BCPAO scraper and return results"""
    from scrapers.bcpao_scraper import BCPAOScraper
    
    print("=" * 60)
    print("BCPAO ROUGH DIAMOND SCRAPER")
    print("=" * 60)
    
    scraper = BCPAOScraper()
    parcels = scraper.run_full_search()
    
    if output_file:
        scraper.export_results(output_file)
        print(f"\n✅ Results saved to: {output_file}")
    
    return {"parcels": parcels, "count": len(parcels)}


def run_scorer(input_file: str, output_file: str = None) -> dict:
    """Score parcels from JSON file"""
    from models.scoring_model import RoughDiamondScorer
    
    print("=" * 60)
    print("ROUGH DIAMOND SCORING")
    print("=" * 60)
    
    with open(input_file) as f:
        data = json.load(f)
    
    parcels = data.get('parcels', data) if isinstance(data, dict) else data
    
    scorer = RoughDiamondScorer()
    scored = scorer.score_parcels(parcels)
    
    bid_count = len(scorer.get_bid_candidates(scored))
    review_count = len(scorer.get_review_candidates(scored))
    
    print(f"\nScored: {len(scored)} parcels")
    print(f"🟢 BID: {bid_count}")
    print(f"🟡 REVIEW: {review_count}")
    
    if output_file:
        scorer.export_results(scored, output_file)
        print(f"\n✅ Scored results saved to: {output_file}")
    
    return {"scored": scored, "bid_count": bid_count, "review_count": review_count}


def run_full_pipeline(supabase_key: str = None) -> dict:
    """Run complete pipeline: scrape -> score -> store"""
    from agents.pipeline_orchestrator import RoughDiamondPipeline
    
    print("=" * 60)
    print("SPD ROUGH DIAMOND PIPELINE - Full Execution")
    print("=" * 60)
    
    pipeline = RoughDiamondPipeline(supabase_key=supabase_key)
    state = pipeline.run({"mode": "full", "timestamp": datetime.now().isoformat()})
    
    return state


def main():
    parser = argparse.ArgumentParser(
        description="SPD Rough Diamond Pipeline - BCPAO Parcel Analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                              # Full pipeline
  python main.py --scrape-only -o data.json   # Scrape to file
  python main.py --score-only data.json       # Score existing file
        """
    )
    
    parser.add_argument('--scrape-only', action='store_true', help='Only run BCPAO scraper')
    parser.add_argument('--score-only', type=str, metavar='FILE', help='Score parcels from JSON file')
    parser.add_argument('-o', '--output', type=str, help='Output file path')
    parser.add_argument('--supabase-key', type=str, help='Supabase service key')
    parser.add_argument('--dry-run', action='store_true', help='Skip database storage')
    
    args = parser.parse_args()
    
    # Get Supabase key from args or environment
    supabase_key = args.supabase_key or os.environ.get('SUPABASE_SERVICE_KEY', '')
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    try:
        if args.scrape_only:
            output = args.output or f"data/bcpao_raw_{timestamp}.json"
            os.makedirs(os.path.dirname(output) or '.', exist_ok=True)
            result = run_scraper(output)
            print(f"\n✅ Scraping complete: {result['count']} parcels")
            
        elif args.score_only:
            if not os.path.exists(args.score_only):
                print(f"❌ File not found: {args.score_only}")
                sys.exit(1)
            output = args.output or f"data/scored_{timestamp}.json"
            os.makedirs(os.path.dirname(output) or '.', exist_ok=True)
            result = run_scorer(args.score_only, output)
            print(f"\n✅ Scoring complete: {result['bid_count']} BID candidates")
            
        else:
            # Full pipeline
            if args.dry_run:
                supabase_key = None
            result = run_full_pipeline(supabase_key)
            print(f"\n✅ Pipeline complete: {result.get('status', 'unknown')}")
            
    except KeyboardInterrupt:
        print("\n⚠️ Interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
