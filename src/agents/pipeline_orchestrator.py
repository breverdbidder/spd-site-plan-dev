#!/usr/bin/env python3
"""
LangGraph Orchestration for SPD Rough Diamond Pipeline
Agentic workflow for property discovery, scoring, and storage

Author: BidDeed.AI / Everest Capital USA
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, TypedDict, Annotated
from enum import Enum

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# State definitions for LangGraph
class PipelineState(TypedDict):
    """State passed between pipeline nodes"""
    run_id: str
    stage: str
    raw_parcels: List[Dict]
    scored_parcels: List[Dict]
    bid_candidates: List[Dict]
    review_candidates: List[Dict]
    errors: List[str]
    metrics: Dict[str, Any]
    status: str


class PipelineStage(Enum):
    """Pipeline stages"""
    INIT = "init"
    SCRAPE = "scrape"
    SCORE = "score"
    FILTER = "filter"
    STORE = "store"
    REPORT = "report"
    COMPLETE = "complete"
    ERROR = "error"


class RoughDiamondPipeline:
    """
    LangGraph-style orchestration pipeline for rough diamond property discovery
    
    Pipeline stages:
    1. INIT - Initialize state and parameters
    2. SCRAPE - Fetch parcels from BCPAO
    3. SCORE - Apply XGBoost-derived scoring model
    4. FILTER - Extract BID and REVIEW candidates
    5. STORE - Save to Supabase
    6. REPORT - Generate summary report
    7. COMPLETE - Finalize and cleanup
    """
    
    def __init__(self, supabase_key: str = None):
        self.supabase_key = supabase_key or os.environ.get('SUPABASE_SERVICE_KEY', '')
        self.run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def init_state(self, params: Dict = None) -> PipelineState:
        """Initialize pipeline state"""
        return PipelineState(
            run_id=self.run_id,
            stage=PipelineStage.INIT.value,
            raw_parcels=[],
            scored_parcels=[],
            bid_candidates=[],
            review_candidates=[],
            errors=[],
            metrics={
                "started_at": datetime.now().isoformat(),
                "params": params or {}
            },
            status="running"
        )
    
    def node_scrape(self, state: PipelineState) -> PipelineState:
        """SCRAPE node - Fetch parcels from BCPAO"""
        logger.info(f"[{self.run_id}] SCRAPE: Starting BCPAO data collection")
        state["stage"] = PipelineStage.SCRAPE.value
        
        try:
            from scrapers.bcpao_scraper import BCPAOScraper
            
            scraper = BCPAOScraper()
            parcels = scraper.run_full_search()
            
            state["raw_parcels"] = parcels
            state["metrics"]["parcels_scraped"] = len(parcels)
            logger.info(f"[{self.run_id}] SCRAPE: Found {len(parcels)} parcels")
            
        except Exception as e:
            state["errors"].append(f"SCRAPE error: {str(e)}")
            logger.error(f"[{self.run_id}] SCRAPE failed: {e}")
        
        return state
    
    def node_score(self, state: PipelineState) -> PipelineState:
        """SCORE node - Apply scoring model to parcels"""
        logger.info(f"[{self.run_id}] SCORE: Applying XGBoost scoring model")
        state["stage"] = PipelineStage.SCORE.value
        
        try:
            from models.scoring_model import RoughDiamondScorer
            
            scorer = RoughDiamondScorer()
            scored = scorer.score_parcels(state["raw_parcels"])
            
            state["scored_parcels"] = scored
            state["metrics"]["parcels_scored"] = len(scored)
            
            # Calculate score distribution
            score_dist = {"80+": 0, "65-79": 0, "50-64": 0, "<50": 0}
            for p in scored:
                s = p.get("score", 0)
                if s >= 80: score_dist["80+"] += 1
                elif s >= 65: score_dist["65-79"] += 1
                elif s >= 50: score_dist["50-64"] += 1
                else: score_dist["<50"] += 1
            
            state["metrics"]["score_distribution"] = score_dist
            logger.info(f"[{self.run_id}] SCORE: Scored {len(scored)} parcels")
            
        except Exception as e:
            state["errors"].append(f"SCORE error: {str(e)}")
            logger.error(f"[{self.run_id}] SCORE failed: {e}")
        
        return state
    
    def node_filter(self, state: PipelineState) -> PipelineState:
        """FILTER node - Extract candidates by recommendation"""
        logger.info(f"[{self.run_id}] FILTER: Extracting candidates")
        state["stage"] = PipelineStage.FILTER.value
        
        try:
            bid = [p for p in state["scored_parcels"] if "🟢" in p.get("recommendation", "")]
            review = [p for p in state["scored_parcels"] if "🟡" in p.get("recommendation", "")]
            
            state["bid_candidates"] = bid
            state["review_candidates"] = review
            state["metrics"]["bid_count"] = len(bid)
            state["metrics"]["review_count"] = len(review)
            
            logger.info(f"[{self.run_id}] FILTER: {len(bid)} BID, {len(review)} REVIEW")
            
        except Exception as e:
            state["errors"].append(f"FILTER error: {str(e)}")
            logger.error(f"[{self.run_id}] FILTER failed: {e}")
        
        return state
    
    def node_store(self, state: PipelineState) -> PipelineState:
        """STORE node - Save to Supabase"""
        logger.info(f"[{self.run_id}] STORE: Saving to Supabase")
        state["stage"] = PipelineStage.STORE.value
        
        if not self.supabase_key:
            logger.warning(f"[{self.run_id}] STORE: No Supabase key - skipping database storage")
            state["metrics"]["db_stored"] = False
            return state
        
        try:
            from integrations.supabase_client import SupabaseClient, SupabaseConfig
            
            config = SupabaseConfig()
            config.service_key = self.supabase_key
            client = SupabaseClient(config)
            
            # Store raw parcels
            if state["raw_parcels"]:
                client.insert_parcels_batch(state["raw_parcels"][:100])  # Limit batch size
                logger.info(f"[{self.run_id}] STORE: Inserted parcels")
            
            # Store scores
            if state["scored_parcels"]:
                client.insert_scores_batch(state["scored_parcels"][:100])
                logger.info(f"[{self.run_id}] STORE: Inserted scores")
            
            # Log run
            client.log_search_run({
                "run_type": "rough_diamond_pipeline",
                "total_found": len(state["raw_parcels"]),
                "bid_count": len(state["bid_candidates"]),
                "review_count": len(state["review_candidates"]),
                "parameters": state["metrics"].get("params", {}),
                "status": "completed"
            })
            
            state["metrics"]["db_stored"] = True
            
        except Exception as e:
            state["errors"].append(f"STORE error: {str(e)}")
            state["metrics"]["db_stored"] = False
            logger.error(f"[{self.run_id}] STORE failed: {e}")
        
        return state
    
    def node_report(self, state: PipelineState) -> PipelineState:
        """REPORT node - Generate summary"""
        logger.info(f"[{self.run_id}] REPORT: Generating summary")
        state["stage"] = PipelineStage.REPORT.value
        
        state["metrics"]["completed_at"] = datetime.now().isoformat()
        state["metrics"]["total_errors"] = len(state["errors"])
        
        # Print summary
        print("\n" + "=" * 60)
        print(f"ROUGH DIAMOND PIPELINE - Run {self.run_id}")
        print("=" * 60)
        print(f"Parcels Scraped: {state['metrics'].get('parcels_scraped', 0)}")
        print(f"Parcels Scored: {state['metrics'].get('parcels_scored', 0)}")
        print(f"🟢 BID Candidates: {state['metrics'].get('bid_count', 0)}")
        print(f"🟡 REVIEW Candidates: {state['metrics'].get('review_count', 0)}")
        print(f"Database Stored: {state['metrics'].get('db_stored', False)}")
        print(f"Errors: {state['metrics'].get('total_errors', 0)}")
        print("=" * 60)
        
        # Top 5 BID candidates
        if state["bid_candidates"]:
            print("\nTOP BID CANDIDATES:")
            for i, p in enumerate(state["bid_candidates"][:5], 1):
                print(f"  {i}. {p.get('account')} | {p.get('score')}/100 | {p.get('acres', 0):.1f}ac | {p.get('address', 'N/A')[:40]}")
        
        return state
    
    def node_complete(self, state: PipelineState) -> PipelineState:
        """COMPLETE node - Finalize pipeline"""
        state["stage"] = PipelineStage.COMPLETE.value
        state["status"] = "completed" if not state["errors"] else "completed_with_errors"
        
        # Save state to file
        output_path = f"pipeline_run_{self.run_id}.json"
        with open(output_path, 'w') as f:
            json.dump(state, f, indent=2, default=str)
        
        logger.info(f"[{self.run_id}] COMPLETE: Pipeline finished - {output_path}")
        return state
    
    def run(self, params: Dict = None) -> PipelineState:
        """Execute full pipeline"""
        logger.info(f"Starting Rough Diamond Pipeline - Run ID: {self.run_id}")
        
        # Initialize state
        state = self.init_state(params)
        
        # Execute pipeline stages
        pipeline_nodes = [
            self.node_scrape,
            self.node_score,
            self.node_filter,
            self.node_store,
            self.node_report,
            self.node_complete
        ]
        
        for node in pipeline_nodes:
            try:
                state = node(state)
            except Exception as e:
                state["errors"].append(f"Pipeline error in {node.__name__}: {str(e)}")
                state["status"] = "failed"
                logger.error(f"Pipeline failed at {node.__name__}: {e}")
                break
        
        return state


# LangGraph-compatible graph definition (for future integration)
def create_langgraph_workflow():
    """
    Create LangGraph StateGraph for the pipeline
    Requires: pip install langgraph
    """
    try:
        from langgraph.graph import StateGraph, END
        
        pipeline = RoughDiamondPipeline()
        
        # Define the graph
        workflow = StateGraph(PipelineState)
        
        # Add nodes
        workflow.add_node("scrape", pipeline.node_scrape)
        workflow.add_node("score", pipeline.node_score)
        workflow.add_node("filter", pipeline.node_filter)
        workflow.add_node("store", pipeline.node_store)
        workflow.add_node("report", pipeline.node_report)
        
        # Add edges
        workflow.add_edge("scrape", "score")
        workflow.add_edge("score", "filter")
        workflow.add_edge("filter", "store")
        workflow.add_edge("store", "report")
        workflow.add_edge("report", END)
        
        # Set entry point
        workflow.set_entry_point("scrape")
        
        return workflow.compile()
        
    except ImportError:
        logger.warning("LangGraph not installed - using simple pipeline execution")
        return None


if __name__ == "__main__":
    # Run pipeline
    pipeline = RoughDiamondPipeline()
    final_state = pipeline.run({
        "target_zips": ["32904", "32905", "32907"],
        "min_acres": 2,
        "max_acres": 100
    })
    
    print(f"\nFinal Status: {final_state['status']}")
