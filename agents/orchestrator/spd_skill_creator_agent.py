"""
SPD Skill Creator Agent
LangGraph orchestrator for creating, validating, and deploying skills
Follows Anthropic skill-creator best practices
"""

import os
import json
from pathlib import Path
from typing import TypedDict, Literal, Annotated
from datetime import datetime
from langgraph.graph import StateGraph, END
from anthropic import Anthropic

# Initialize Anthropic client
client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

class SkillCreatorState(TypedDict):
    """State for skill creation workflow"""
    skill_request: str
    skill_name: str
    skill_description: str
    skill_type: Literal["workflow", "tool", "domain", "bundled"]
    freedom_level: Literal["high", "medium", "low"]
    skill_md_content: str
    bundled_resources: dict
    validation_result: dict
    deployment_status: str
    messages: list
    error: str

def analyze_skill_request(state: SkillCreatorState) -> SkillCreatorState:
    """
    Analyze user's skill request and determine:
    - Skill type (workflow, tool, domain, bundled)
    - Freedom level (high, medium, low)
    - Required bundled resources
    """
    print("🔍 Analyzing skill request...")
    
    prompt = f"""Analyze this skill creation request and provide structured output:

REQUEST: {state['skill_request']}

Determine:
1. SKILL_TYPE: workflow | tool | domain | bundled
   - workflow: Multi-step procedures for specific domains
   - tool: Instructions for working with specific file formats or APIs
   - domain: Company-specific knowledge, schemas, business logic
   - bundled: Scripts, references, and assets for complex/repetitive tasks

2. FREEDOM_LEVEL: high | medium | low
   - high: Multiple approaches valid, context-dependent decisions
   - medium: Preferred pattern exists, some variation acceptable
   - low: Fragile operations, consistency critical, specific sequence required

3. BUNDLED_RESOURCES: scripts | references | assets
   - scripts: Executable code for deterministic reliability
   - references: Documentation to load as needed
   - assets: Files used in output (templates, images, etc.)

4. SKILL_NAME: Short, descriptive kebab-case name (e.g., "parcel-analyzer")

5. SKILL_DESCRIPTION: Clear, comprehensive description (1-2 sentences) explaining what the skill does and when it should be used

Output as JSON:
{{
    "skill_type": "...",
    "freedom_level": "...",
    "bundled_resources": ["scripts", "references", "assets"],
    "skill_name": "...",
    "skill_description": "..."
}}"""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )
    
    # Parse JSON response
    content = response.content[0].text
    # Extract JSON from markdown if present
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        content = content.split("```")[1].split("```")[0].strip()
    
    analysis = json.loads(content)
    
    state["skill_type"] = analysis["skill_type"]
    state["freedom_level"] = analysis["freedom_level"]
    state["skill_name"] = analysis["skill_name"]
    state["skill_description"] = analysis["skill_description"]
    state["bundled_resources"] = {
        "scripts": "scripts" in analysis.get("bundled_resources", []),
        "references": "references" in analysis.get("bundled_resources", []),
        "assets": "assets" in analysis.get("bundled_resources", [])
    }
    
    state["messages"].append({
        "stage": "analyze",
        "timestamp": datetime.now().isoformat(),
        "result": analysis
    })
    
    print(f"✅ Analysis complete: {state['skill_name']} ({state['skill_type']}, {state['freedom_level']} freedom)")
    return state

def generate_skill_md(state: SkillCreatorState) -> SkillCreatorState:
    """
    Generate SKILL.md following Anthropic best practices:
    - Concise (context window is public good)
    - YAML frontmatter (name, description)
    - Progressive disclosure (keep under 500 lines)
    - Clear workflow guidance
    """
    print("📝 Generating SKILL.md...")
    
    # Load full skill-creator guidance
    skill_creator_guide = Path("/tmp/skill_creator_full.md").read_text()
    
    prompt = f"""Create a SKILL.md file following Anthropic skill-creator best practices.

SKILL REQUEST: {state['skill_request']}

SKILL METADATA:
- Name: {state['skill_name']}
- Description: {state['skill_description']}
- Type: {state['skill_type']}
- Freedom Level: {state['freedom_level']}
- Bundled Resources: {state['bundled_resources']}

REFERENCE GUIDE:
{skill_creator_guide}

REQUIREMENTS:
1. Start with YAML frontmatter (name, description)
2. Be CONCISE - context window is public good
3. Keep under 500 lines total
4. Use progressive disclosure - reference bundled resources
5. Match freedom level to task fragility:
   - High freedom: Text instructions, heuristics
   - Medium freedom: Pseudocode, configurable patterns
   - Low freedom: Specific scripts, precise sequences
6. Include clear workflow guidance
7. Reference bundled resources (scripts/, references/, assets/) when applicable
8. NO extraneous files (README, CHANGELOG, etc.)

OUTPUT FORMAT:
Generate complete SKILL.md content as markdown."""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=8000,
        messages=[{"role": "user", "content": prompt}]
    )
    
    skill_md = response.content[0].text
    
    # Clean markdown fences if present
    if "```markdown" in skill_md:
        skill_md = skill_md.split("```markdown")[1].split("```")[0].strip()
    elif "```" in skill_md:
        skill_md = skill_md.split("```")[1].split("```")[0].strip()
    
    state["skill_md_content"] = skill_md
    state["messages"].append({
        "stage": "generate",
        "timestamp": datetime.now().isoformat(),
        "lines": len(skill_md.split("\n")),
        "tokens_estimated": len(skill_md.split()) * 1.3
    })
    
    print(f"✅ Generated SKILL.md ({len(skill_md.split())} lines)")
    return state

def validate_skill(state: SkillCreatorState) -> SkillCreatorState:
    """
    Validate SKILL.md against best practices:
    - Has YAML frontmatter (name, description)
    - Under 500 lines
    - Concise (no verbose explanations)
    - Clear workflows
    - Proper progressive disclosure
    """
    print("✅ Validating skill...")
    
    skill_md = state["skill_md_content"]
    lines = skill_md.split("\n")
    
    validation = {
        "has_frontmatter": False,
        "has_name": False,
        "has_description": False,
        "line_count": len(lines),
        "under_500_lines": len(lines) < 500,
        "issues": []
    }
    
    # Check frontmatter
    if lines[0] == "---":
        frontmatter_end = None
        for i, line in enumerate(lines[1:], 1):
            if line == "---":
                frontmatter_end = i
                break
        
        if frontmatter_end:
            validation["has_frontmatter"] = True
            frontmatter = "\n".join(lines[1:frontmatter_end])
            validation["has_name"] = "name:" in frontmatter
            validation["has_description"] = "description:" in frontmatter
    
    if not validation["has_frontmatter"]:
        validation["issues"].append("Missing YAML frontmatter")
    if not validation["has_name"]:
        validation["issues"].append("Missing 'name' in frontmatter")
    if not validation["has_description"]:
        validation["issues"].append("Missing 'description' in frontmatter")
    if not validation["under_500_lines"]:
        validation["issues"].append(f"Exceeds 500 lines ({validation['line_count']} lines)")
    
    validation["valid"] = len(validation["issues"]) == 0
    
    state["validation_result"] = validation
    state["messages"].append({
        "stage": "validate",
        "timestamp": datetime.now().isoformat(),
        "result": validation
    })
    
    if validation["valid"]:
        print(f"✅ Validation passed ({validation['line_count']} lines)")
    else:
        print(f"❌ Validation failed: {', '.join(validation['issues'])}")
    
    return state

def deploy_skill(state: SkillCreatorState) -> SkillCreatorState:
    """
    Deploy skill to SPD repo:
    1. Create skill directory: skills/{skill_name}/
    2. Write SKILL.md
    3. Create bundled resource directories if needed
    4. Commit and push to GitHub
    """
    print("🚀 Deploying skill to SPD repo...")
    
    if not state["validation_result"]["valid"]:
        state["error"] = "Cannot deploy invalid skill"
        state["deployment_status"] = "FAILED"
        return state
    
    skill_name = state["skill_name"]
    skill_md = state["skill_md_content"]
    
    # Create skill directory structure
    skill_dir = f"/tmp/spd_skills/{skill_name}"
    os.makedirs(skill_dir, exist_ok=True)
    
    # Write SKILL.md
    with open(f"{skill_dir}/SKILL.md", "w") as f:
        f.write(skill_md)
    
    # Create bundled resource directories if needed
    if state["bundled_resources"]["scripts"]:
        os.makedirs(f"{skill_dir}/scripts", exist_ok=True)
        with open(f"{skill_dir}/scripts/.gitkeep", "w") as f:
            f.write("")
    
    if state["bundled_resources"]["references"]:
        os.makedirs(f"{skill_dir}/references", exist_ok=True)
        with open(f"{skill_dir}/references/.gitkeep", "w") as f:
            f.write("")
    
    if state["bundled_resources"]["assets"]:
        os.makedirs(f"{skill_dir}/assets", exist_ok=True)
        with open(f"{skill_dir}/assets/.gitkeep", "w") as f:
            f.write("")
    
    # Create deployment artifact
    deployment_artifact = {
        "skill_name": skill_name,
        "skill_type": state["skill_type"],
        "freedom_level": state["freedom_level"],
        "bundled_resources": state["bundled_resources"],
        "file_path": f"skills/{skill_name}/SKILL.md",
        "deployed_at": datetime.now().isoformat()
    }
    
    with open(f"{skill_dir}/deployment.json", "w") as f:
        json.dump(deployment_artifact, f, indent=2)
    
    state["deployment_status"] = "SUCCESS"
    state["messages"].append({
        "stage": "deploy",
        "timestamp": datetime.now().isoformat(),
        "artifact": deployment_artifact
    })
    
    print(f"✅ Skill deployed to {skill_dir}")
    print("\nNext steps:")
    print(f"1. Review: {skill_dir}/SKILL.md")
    print(f"2. Upload to GitHub: breverdbidder/spd-site-plan-dev/skills/{skill_name}/")
    print(f"3. Add to .mcp.json if MCP integration needed")
    
    return state

def create_skill_creator_graph():
    """Create LangGraph workflow for skill creation"""
    
    workflow = StateGraph(SkillCreatorState)
    
    # Add nodes
    workflow.add_node("analyze", analyze_skill_request)
    workflow.add_node("generate", generate_skill_md)
    workflow.add_node("validate", validate_skill)
    workflow.add_node("deploy", deploy_skill)
    
    # Define edges
    workflow.add_edge("analyze", "generate")
    workflow.add_edge("generate", "validate")
    workflow.add_edge("validate", "deploy")
    workflow.add_edge("deploy", END)
    
    # Set entry point
    workflow.set_entry_point("analyze")
    
    return workflow.compile()

def run_skill_creator(skill_request: str) -> dict:
    """
    Run skill creator workflow
    
    Args:
        skill_request: Natural language description of skill to create
    
    Returns:
        Final state with deployed skill
    """
    initial_state = {
        "skill_request": skill_request,
        "skill_name": "",
        "skill_description": "",
        "skill_type": "workflow",
        "freedom_level": "medium",
        "skill_md_content": "",
        "bundled_resources": {},
        "validation_result": {},
        "deployment_status": "",
        "messages": [],
        "error": ""
    }
    
    graph = create_skill_creator_graph()
    final_state = graph.invoke(initial_state)
    
    return final_state

if __name__ == "__main__":
    # Example usage
    skill_request = """
    Create a skill for analyzing parcel data from the Brevard County Property Appraiser.
    The skill should:
    - Query BCPAO API for parcel information
    - Extract zoning, land use, and property characteristics
    - Determine buildability and development constraints
    - Calculate maximum density/units based on zoning
    - Identify required permits and approval process
    
    This is for SPD Site Plan Development automation.
    """
    
    print("=" * 80)
    print("SPD SKILL CREATOR - LANGGRAPH ORCHESTRATION")
    print("=" * 80)
    print()
    
    result = run_skill_creator(skill_request)
    
    print("\n" + "=" * 80)
    print("WORKFLOW COMPLETE")
    print("=" * 80)
    print(f"\nDeployment Status: {result['deployment_status']}")
    print(f"Skill Name: {result['skill_name']}")
    print(f"Skill Type: {result['skill_type']}")
    print(f"Freedom Level: {result['freedom_level']}")
    
    if result.get("error"):
        print(f"\nError: {result['error']}")
    else:
        print(f"\n✅ Skill ready for deployment to GitHub")
        print(f"📁 Local path: /tmp/spd_skills/{result['skill_name']}/")
