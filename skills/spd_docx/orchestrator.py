"""
SPD DOCX LangGraph Orchestrator
Property360 Real Estate | Site Plan Development Pipeline

This module integrates the SPD DOCX skill with LangGraph for automated document generation.
"""

import os
import json
import subprocess
from typing import TypedDict, Literal, Optional
from datetime import datetime

# LangGraph imports (install: pip install langgraph langchain-core)
try:
    from langgraph.graph import StateGraph, END
    from langchain_core.messages import HumanMessage, AIMessage
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    print("Warning: LangGraph not installed. Install with: pip install langgraph langchain-core")


class SPDProjectState(TypedDict):
    """State for SPD document generation workflow."""
    project_id: str
    address: str
    parcel_id: str
    current_zoning: str
    requested_zoning: str
    proposed_units: int
    total_acres: Optional[float]
    constraints: Optional[list]
    developer_name: str
    city: str
    
    # Workflow state
    stage: str
    documents_generated: list
    errors: list
    completed: bool


class SPDDocxOrchestrator:
    """
    Orchestrator for SPD DOCX document generation.
    
    Integrates with:
    - GitHub Actions for cloud execution
    - Local Node.js for development
    - Supabase for logging
    """
    
    TEMPLATES = {
        "pre_app_analysis": "skills/spd_docx/templates/pre_app_analysis.js",
        "meeting_agenda_attorney": "skills/spd_docx/templates/meeting_agenda_attorney.js",
    }
    
    def __init__(self, 
                 github_token: str = None,
                 supabase_url: str = None,
                 supabase_key: str = None,
                 local_mode: bool = False):
        """
        Initialize the orchestrator.
        
        Args:
            github_token: GitHub PAT for Actions API
            supabase_url: Supabase project URL
            supabase_key: Supabase service role key
            local_mode: If True, generate docs locally instead of via GitHub Actions
        """
        self.github_token = github_token or os.environ.get("GITHUB_TOKEN")
        self.supabase_url = supabase_url or os.environ.get("SUPABASE_URL")
        self.supabase_key = supabase_key or os.environ.get("SUPABASE_KEY")
        self.local_mode = local_mode
        self.repo = "breverdbidder/spd-site-plan-dev"
    
    def generate_documents(self, 
                          project: SPDProjectState,
                          document_types: list = None) -> dict:
        """
        Generate SPD documents for a project.
        
        Args:
            project: Project data
            document_types: List of document types to generate. 
                           Options: pre_app_analysis, meeting_agenda_attorney
                           Default: all
        
        Returns:
            dict with status and document paths
        """
        if document_types is None:
            document_types = list(self.TEMPLATES.keys())
        
        if self.local_mode:
            return self._generate_local(project, document_types)
        else:
            return self._trigger_github_action(project, document_types)
    
    def _generate_local(self, project: SPDProjectState, document_types: list) -> dict:
        """Generate documents locally using Node.js."""
        results = {"status": "success", "documents": [], "errors": []}
        
        # Create project data JSON
        project_json = json.dumps({
            "projectId": project["project_id"],
            "address": project["address"],
            "parcelId": project["parcel_id"],
            "currentZoning": project["current_zoning"],
            "requestedZoning": project["requested_zoning"],
            "proposedUnits": project["proposed_units"],
            "totalAcres": project.get("total_acres"),
            "constraints": project.get("constraints", []),
            "developer": {"name": project.get("developer_name", "Mariam Shapira")},
            "city": project.get("city", "Palm Bay")
        })
        
        for doc_type in document_types:
            if doc_type not in self.TEMPLATES:
                results["errors"].append(f"Unknown document type: {doc_type}")
                continue
            
            output_path = f"outputs/{project['project_id']}_{doc_type}.docx"
            
            try:
                # Generate document using Node.js
                node_script = f"""
                const {{ {'generatePreAppAnalysis' if doc_type == 'pre_app_analysis' else 'generateMeetingAgendaAttorney'} }} = require('./{self.TEMPLATES[doc_type]}');
                const project = {project_json};
                {'generatePreAppAnalysis' if doc_type == 'pre_app_analysis' else 'generateMeetingAgendaAttorney'}(project, '{output_path}');
                """
                
                subprocess.run(["node", "-e", node_script], check=True)
                results["documents"].append(output_path)
                
            except subprocess.CalledProcessError as e:
                results["errors"].append(f"Failed to generate {doc_type}: {str(e)}")
                results["status"] = "partial" if results["documents"] else "failed"
        
        return results
    
    def _trigger_github_action(self, project: SPDProjectState, document_types: list) -> dict:
        """Trigger GitHub Actions workflow."""
        import requests
        
        doc_type = "all" if len(document_types) > 1 else document_types[0]
        
        response = requests.post(
            f"https://api.github.com/repos/{self.repo}/actions/workflows/generate_spd_docs.yml/dispatches",
            headers={
                "Authorization": f"token {self.github_token}",
                "Accept": "application/vnd.github.v3+json"
            },
            json={
                "ref": "main",
                "inputs": {
                    "project_id": project["project_id"],
                    "address": project["address"],
                    "parcel_id": project["parcel_id"],
                    "current_zoning": project["current_zoning"],
                    "requested_zoning": project["requested_zoning"],
                    "proposed_units": str(project["proposed_units"]),
                    "document_type": doc_type
                }
            }
        )
        
        if response.status_code == 204:
            return {
                "status": "triggered",
                "message": f"GitHub Actions workflow triggered for {project['project_id']}",
                "workflow_url": f"https://github.com/{self.repo}/actions"
            }
        else:
            return {
                "status": "error",
                "message": f"Failed to trigger workflow: {response.text}"
            }
    
    def log_to_supabase(self, category: str, content: str, metadata: dict = None):
        """Log activity to Supabase insights table."""
        import requests
        
        if not self.supabase_url or not self.supabase_key:
            return {"status": "skipped", "message": "Supabase credentials not configured"}
        
        response = requests.post(
            f"{self.supabase_url}/rest/v1/insights",
            headers={
                "apikey": self.supabase_key,
                "Authorization": f"Bearer {self.supabase_key}",
                "Content-Type": "application/json"
            },
            json={
                "category": category,
                "content": content,
                "source": "spd_docx_orchestrator",
                "metadata": metadata or {}
            }
        )
        
        return {"status": "logged" if response.ok else "error", "response": response.text}


def create_spd_langgraph():
    """
    Create LangGraph workflow for SPD document generation.
    
    Returns a compiled LangGraph that can be invoked with project data.
    """
    if not LANGGRAPH_AVAILABLE:
        raise ImportError("LangGraph not available. Install with: pip install langgraph langchain-core")
    
    orchestrator = SPDDocxOrchestrator(local_mode=True)
    
    def analyze_project(state: SPDProjectState) -> SPDProjectState:
        """Stage 1: Analyze project requirements."""
        state["stage"] = "analysis"
        state["documents_generated"] = []
        state["errors"] = []
        return state
    
    def generate_pre_app(state: SPDProjectState) -> SPDProjectState:
        """Stage 2: Generate Pre-App Analysis document."""
        state["stage"] = "pre_app_generation"
        result = orchestrator.generate_documents(state, ["pre_app_analysis"])
        state["documents_generated"].extend(result.get("documents", []))
        state["errors"].extend(result.get("errors", []))
        return state
    
    def generate_meeting_agenda(state: SPDProjectState) -> SPDProjectState:
        """Stage 3: Generate Attorney Meeting Agenda."""
        state["stage"] = "meeting_agenda_generation"
        result = orchestrator.generate_documents(state, ["meeting_agenda_attorney"])
        state["documents_generated"].extend(result.get("documents", []))
        state["errors"].extend(result.get("errors", []))
        return state
    
    def finalize(state: SPDProjectState) -> SPDProjectState:
        """Stage 4: Finalize and log results."""
        state["stage"] = "complete"
        state["completed"] = True
        
        # Log to Supabase
        orchestrator.log_to_supabase(
            category="spd_documents",
            content=f"Generated {len(state['documents_generated'])} documents for {state['project_id']}",
            metadata={
                "project_id": state["project_id"],
                "documents": state["documents_generated"],
                "errors": state["errors"]
            }
        )
        
        return state
    
    # Build the graph
    workflow = StateGraph(SPDProjectState)
    
    workflow.add_node("analyze", analyze_project)
    workflow.add_node("pre_app", generate_pre_app)
    workflow.add_node("meeting_agenda", generate_meeting_agenda)
    workflow.add_node("finalize", finalize)
    
    workflow.set_entry_point("analyze")
    workflow.add_edge("analyze", "pre_app")
    workflow.add_edge("pre_app", "meeting_agenda")
    workflow.add_edge("meeting_agenda", "finalize")
    workflow.add_edge("finalize", END)
    
    return workflow.compile()


# Example usage
if __name__ == "__main__":
    # Example project data
    project = SPDProjectState(
        project_id="SPD-2025-001",
        address="2165 Sandy Pines Dr NE, Palm Bay, FL",
        parcel_id="2835546",
        current_zoning="RS-2",
        requested_zoning="RM-20",
        proposed_units=21,
        total_acres=1.065,
        constraints=[{
            "type": "wellhead_easement",
            "description": "200-foot wellhead protection easement",
            "timeline": "~10 years",
            "authority": "Palm Bay Utilities",
            "contact": "Tim Roberts"
        }],
        developer_name="Mariam Shapira",
        city="Palm Bay",
        stage="",
        documents_generated=[],
        errors=[],
        completed=False
    )
    
    # Option 1: Direct orchestrator usage
    orchestrator = SPDDocxOrchestrator(local_mode=True)
    result = orchestrator.generate_documents(project)
    print(f"Direct generation result: {result}")
    
    # Option 2: LangGraph workflow (if available)
    if LANGGRAPH_AVAILABLE:
        workflow = create_spd_langgraph()
        final_state = workflow.invoke(project)
        print(f"LangGraph result: {final_state}")
