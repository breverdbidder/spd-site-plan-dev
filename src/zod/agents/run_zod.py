"""
ZOD Pipeline CLI Runner

Usage:
    python -m src.agents.run_zod --jurisdiction "Palm Bay" --flu-categories "HDR,MDR" --min-acres 0.5 --max-parcels 50
"""

import argparse
import asyncio
import logging
import sys
from datetime import datetime

from src.agents.zod_graph import run_zod_discovery

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f'logs/zod_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger(__name__)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='ZOD - Zoning Opportunity Discovery Pipeline',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Basic usage
    python -m src.agents.run_zod --jurisdiction "Palm Bay" --flu-categories "HDR"
    
    # Full options
    python -m src.agents.run_zod \\
        --jurisdiction "Brevard County" \\
        --flu-categories "HDR,MDR,MXU" \\
        --min-acres 1.0 \\
        --max-parcels 100 \\
        --output-dir reports/zod
        """
    )
    
    parser.add_argument(
        '--jurisdiction', '-j',
        type=str,
        required=True,
        help='Target jurisdiction (e.g., "Palm Bay", "Brevard County")'
    )
    
    parser.add_argument(
        '--flu-categories', '-f',
        type=str,
        required=True,
        help='Comma-separated FLU categories to search (e.g., "HDR,MDR,MXU")'
    )
    
    parser.add_argument(
        '--min-acres', '-a',
        type=float,
        default=0.5,
        help='Minimum parcel size in acres (default: 0.5)'
    )
    
    parser.add_argument(
        '--max-parcels', '-n',
        type=int,
        default=50,
        help='Maximum parcels to analyze (default: 50)'
    )
    
    parser.add_argument(
        '--output-dir', '-o',
        type=str,
        default='reports/zod',
        help='Output directory for reports (default: reports/zod)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    
    return parser.parse_args()


async def main():
    """Main entry point."""
    args = parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Parse FLU categories
    flu_categories = [c.strip().upper() for c in args.flu_categories.split(',')]
    
    logger.info("=" * 60)
    logger.info("ZOD - ZONING OPPORTUNITY DISCOVERY")
    logger.info("=" * 60)
    logger.info(f"Jurisdiction: {args.jurisdiction}")
    logger.info(f"FLU Categories: {flu_categories}")
    logger.info(f"Min Acres: {args.min_acres}")
    logger.info(f"Max Parcels: {args.max_parcels}")
    logger.info(f"Output Dir: {args.output_dir}")
    logger.info("=" * 60)
    
    start_time = datetime.now()
    
    try:
        # Run discovery
        results = await run_zod_discovery(
            jurisdiction=args.jurisdiction,
            target_flu_categories=flu_categories,
            min_parcel_acres=args.min_acres,
            max_parcels=args.max_parcels
        )
        
        # Log results
        opportunities = results.get('opportunities', [])
        summary = results.get('summary', {})
        
        logger.info("\n" + "=" * 60)
        logger.info("DISCOVERY COMPLETE")
        logger.info("=" * 60)
        logger.info(f"Total Opportunities: {len(opportunities)}")
        logger.info(f"Reports Generated: {len(results.get('reports_generated', []))}")
        
        if summary:
            logger.info(f"Total Unit Upside: {summary.get('total_unit_upside', 0)}")
            logger.info(f"Average Score: {summary.get('average_score', 0)}")
            logger.info(f"Grade Distribution: {summary.get('grade_distribution', {})}")
        
        # Print top opportunities
        if opportunities:
            logger.info("\nTOP OPPORTUNITIES:")
            for i, opp in enumerate(opportunities[:5], 1):
                score = opp.get('opportunity_score', {})
                logger.info(
                    f"  {i}. {opp.get('parcel_id')} - {opp.get('address', 'Unknown')}"
                    f" | Score: {score.get('total_score', 0)} | Grade: {score.get('grade', 'F')}"
                    f" | Unit Upside: {score.get('unit_analysis', {}).get('unit_upside', 0)}"
                )
        
        # Log checkpoints
        checkpoints = results.get('checkpoints', [])
        if checkpoints and args.verbose:
            logger.info("\nPIPELINE CHECKPOINTS:")
            for cp in checkpoints:
                logger.info(f"  - {cp.get('stage')}: {cp.get('timestamp')}")
        
        elapsed = datetime.now() - start_time
        logger.info(f"\nTotal Runtime: {elapsed}")
        
        # Return exit code based on success
        return 0 if opportunities else 1
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(asyncio.run(main()))
