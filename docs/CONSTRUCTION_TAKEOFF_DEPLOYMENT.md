# Construction Takeoff Agent - Deployment & API Integration Guide

**Date:** December 19, 2025  
**Repository:** github.com/breverdbidder/spd-site-plan-dev  
**Stack:** LangGraph + Claude + Firecrawl + OpenPyXL + Supabase

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Prerequisites](#prerequisites)
3. [Installation](#installation)
4. [API Configuration](#api-configuration)
5. [Usage Examples](#usage-examples)
6. [API Mega Library Integration](#api-mega-library-integration)
7. [Deployment to GitHub](#deployment-to-github)
8. [Testing](#testing)
9. [Troubleshooting](#troubleshooting)
10. [Cost Optimization](#cost-optimization)

---

## Quick Start

Deploy the construction takeoff agent in 5 steps:

```bash
# 1. Clone repository
git clone https://github.com/breverdbidder/spd-site-plan-dev.git
cd spd-site-plan-dev

# 2. Set environment variables
export ANTHROPIC_API_KEY="your_claude_api_key"
export FIRECRAWL_API_KEY="your_firecrawl_api_key"
export SUPABASE_SERVICE_ROLE_KEY="your_supabase_key"

# 3. Install dependencies
pip install anthropic langgraph requests openpyxl pdfplumber

# 4. Copy agent to agents/orchestrator/
cp /path/to/construction_takeoff_agent.py agents/orchestrator/

# 5. Run a test takeoff
python agents/orchestrator/construction_takeoff_agent.py \
  test_plan.pdf \
  "Test Project" \
  "TEST-001"
```

---

## Prerequisites

### Required Services

1. **Anthropic Claude API** (claude-sonnet-4-20250514)
   - Sign up: https://console.anthropic.com
   - Pricing: $3/MTok input, $15/MTok output
   - Usage: PDF vision analysis, quantity extraction

2. **Firecrawl API** (optional but recommended)
   - Sign up: https://firecrawl.dev
   - Pricing: $0.03 per scrape
   - Usage: Competitor analysis

3. **Supabase** (existing)
   - Already configured: mocerqjnksmhcjzxrewo.supabase.co
   - Table: `insights`
   - Usage: Result logging

### System Requirements

- Python 3.11+
- 2GB RAM minimum
- 500MB disk space for reports
- Internet connection for API calls

---

## Installation

### Local Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install anthropic==0.47.1
pip install langgraph==0.2.28
pip install requests==2.31.0
pip install openpyxl==3.1.2
pip install pdfplumber==0.11.0
pip install PyPDF2==3.0.1

# Verify installation
python -c "import anthropic; import langgraph; import openpyxl; print('✅ All packages installed')"
```

### GitHub Actions (Production)

Dependencies are installed automatically via workflow. See `.github/workflows/construction_takeoff_workflow.yml`.

---

## API Configuration

### 1. Anthropic Claude API

```bash
# Get API key from: https://console.anthropic.com/settings/keys
export ANTHROPIC_API_KEY="sk-ant-api03-..."
```

**Test connection:**
```python
from anthropic import Anthropic
client = Anthropic(api_key="your_key")
message = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=100,
    messages=[{"role": "user", "content": "Hello!"}]
)
print(message.content[0].text)
```

### 2. Firecrawl API

```bash
# Get API key from: https://firecrawl.dev/app/api-keys
export FIRECRAWL_API_KEY="fc-..."
```

**Test connection:**
```bash
curl -X POST https://api.firecrawl.dev/v0/scrape \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.planswift.com"}'
```

### 3. Supabase (Already Configured)

```bash
export SUPABASE_SERVICE_ROLE_KEY="eyJ..."
```

**Test connection:**
```bash
curl -X POST "https://mocerqjnksmhcjzxrewo.supabase.co/rest/v1/insights" \
  -H "apikey: YOUR_KEY" \
  -H "Authorization: Bearer YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"category":"test","insight_type":"test","insight_data":{}}'
```

### GitHub Secrets Setup

Add secrets to repository settings:

```bash
# Navigate to: Settings → Secrets and variables → Actions → New repository secret

ANTHROPIC_API_KEY: sk-ant-api03-...
FIRECRAWL_API_KEY: fc-...
SUPABASE_SERVICE_ROLE_KEY: eyJ...
```

---

## Usage Examples

### Example 1: Basic Site Plan Takeoff

```python
from construction_takeoff_agent import run_construction_takeoff

result = run_construction_takeoff(
    pdf_path="projects/bliss_palm_bay/site_plan.pdf",
    project_name="Bliss Palm Bay - Site Development",
    project_id="SPD-2025-003"
)

print(f"Total Cost: ${result['total_estimated_cost']:,.2f}")
print(f"Report: {result['excel_path']}")
```

### Example 2: Floor Plan with Multiple Sheets

```python
# Process main floor plan
result_floor1 = run_construction_takeoff(
    pdf_path="plans/floor_plan_1.pdf",
    project_name="Multi-Family Complex - Floor 1",
    project_id="MFC-2025-F1"
)

# Combine results from multiple floors...
```

### Example 3: GitHub Actions Trigger

```bash
# Via GitHub CLI
gh workflow run construction_takeoff_workflow.yml \
  -f pdf_url="https://example.com/construction_plan.pdf" \
  -f project_name="Warehouse Development" \
  -f project_id="WH-2025-001"

# Via API
curl -X POST \
  -H "Authorization: token ghp_..." \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/breverdbidder/spd-site-plan-dev/actions/workflows/construction_takeoff_workflow.yml/dispatches \
  -d '{"ref":"main","inputs":{"pdf_url":"https://...","project_name":"Warehouse","project_id":"WH-2025-001"}}'
```

### Example 4: Batch Processing

```python
import os
from pathlib import Path

# Process all PDFs in a directory
plans_dir = Path("projects/multi_family/plans")
results = []

for pdf_file in plans_dir.glob("*.pdf"):
    result = run_construction_takeoff(
        pdf_path=str(pdf_file),
        project_name=f"Multi-Family - {pdf_file.stem}",
        project_id=f"MF-{pdf_file.stem}"
    )
    results.append(result)

# Aggregate costs
total_project_cost = sum(r['total_estimated_cost'] for r in results)
print(f"Total Project Cost: ${total_project_cost:,.2f}")
```

---

## API Mega Library Integration

### Accessing the API Mega Library

The SPD system references the comprehensive API library maintained at:

**Repository:** `breverdbidder/life-os`  
**Path:** `docs/API_MEGA_LIBRARY.md`  
**Contains:** 10,498+ APIs across all categories

### Construction-Related APIs in Mega Library

#### Estimation & Takeoff APIs

1. **PlanSwift API**
   - Type: Commercial
   - Use: Digital takeoff integration
   - Pricing: Enterprise licensing
   - Integration: REST API, COM automation

2. **Bluebeam API**
   - Type: Commercial
   - Use: PDF markup automation
   - Pricing: Per-seat licensing
   - Integration: Studio REST API

3. **STACK API**
   - Type: Cloud SaaS
   - Use: Cloud-based takeoff
   - Pricing: Subscription-based
   - Integration: REST API, webhooks

#### Document Processing APIs

4. **Adobe PDF Services API**
   - Type: Commercial
   - Use: PDF extraction, conversion
   - Pricing: Pay-per-document
   - Integration: REST API
   - **Code example:**
   ```python
   from adobe.pdfservices.operation.auth.credentials import Credentials
   from adobe.pdfservices.operation.execution_context import ExecutionContext
   from adobe.pdfservices.operation.pdfops.extract_pdf_operation import ExtractPDFOperation
   
   credentials = Credentials.service_account_credentials_builder()...
   execution_context = ExecutionContext.create(credentials)
   extract_pdf_operation = ExtractPDFOperation.create_new()
   result = extract_pdf_operation.execute(execution_context)
   ```

5. **DocParser API**
   - Type: Commercial
   - Use: Document data extraction
   - Pricing: Starts at $49/month
   - Integration: REST API, Zapier
   - **Code example:**
   ```python
   import requests
   
   response = requests.post(
       "https://api.docparser.com/v1/document/upload",
       files={"file": open("plan.pdf", "rb")},
       headers={"Authorization": f"Bearer {API_KEY}"}
   )
   ```

#### Computer Vision APIs

6. **Google Cloud Vision API**
   - Type: Cloud service
   - Use: OCR, object detection in plans
   - Pricing: $1.50 per 1000 images
   - Integration: gRPC, REST
   - **Code example:**
   ```python
   from google.cloud import vision
   
   client = vision.ImageAnnotatorClient()
   with open("plan.pdf", "rb") as image_file:
       content = image_file.read()
   image = vision.Image(content=content)
   response = client.text_detection(image=image)
   texts = response.text_annotations
   ```

7. **AWS Textract**
   - Type: Cloud service
   - Use: Extract text and tables from plans
   - Pricing: $1.50 per 1000 pages
   - Integration: boto3 SDK
   - **Code example:**
   ```python
   import boto3
   
   textract = boto3.client('textract')
   response = textract.detect_document_text(
       Document={'Bytes': pdf_bytes}
   )
   blocks = response['Blocks']
   ```

#### Cost Database APIs

8. **RSMeans Data API**
   - Type: Commercial
   - Use: Construction cost data
   - Pricing: Subscription required
   - Integration: REST API
   - **Integration point:** Replace `UNIT_COSTS` dictionary

9. **Gordian RSMeans API**
   - Type: Enterprise
   - Use: Real-time cost data
   - Pricing: Custom licensing
   - Integration: SOAP/REST

#### Project Management APIs

10. **Procore API**
    - Type: Cloud SaaS
    - Use: Project coordination, document management
    - Pricing: Per-project subscription
    - Integration: REST API, OAuth2
    - **Code example:**
    ```python
    import requests
    
    headers = {"Authorization": f"Bearer {PROCORE_TOKEN}"}
    response = requests.post(
        "https://api.procore.com/rest/v1.0/projects/{project_id}/drawings",
        headers=headers,
        files={"file": open("takeoff_report.xlsx", "rb")}
    )
    ```

### Extending the Takeoff Agent

#### Adding RSMeans Cost Integration

```python
# Add to construction_takeoff_agent.py

def fetch_rsmeans_costs(material_code: str) -> Dict[str, Any]:
    """Fetch real-time costs from RSMeans API"""
    response = requests.get(
        f"https://api.rsmeans.com/v1/costs/{material_code}",
        headers={"Authorization": f"Bearer {RSMEANS_API_KEY}"}
    )
    return response.json()

# Update calculate_costs() to use RSMeans
def calculate_costs_enhanced(state: TakeoffState) -> TakeoffState:
    for item in state["quantities"]:
        # Try RSMeans first, fallback to static UNIT_COSTS
        try:
            cost_data = fetch_rsmeans_costs(item["material_code"])
            unit_cost = cost_data["unit_price"]
        except:
            unit_cost = UNIT_COSTS.get(item["category"], {}).get("cost", 100.0)
        # ... rest of calculation
```

#### Adding Procore Document Upload

```python
def upload_to_procore(state: TakeoffState) -> TakeoffState:
    """Upload takeoff report to Procore project"""
    procore_api = "https://api.procore.com/rest/v1.0"
    project_id = os.environ.get("PROCORE_PROJECT_ID")
    
    with open(state["excel_path"], "rb") as f:
        response = requests.post(
            f"{procore_api}/projects/{project_id}/documents",
            headers={"Authorization": f"Bearer {PROCORE_TOKEN}"},
            files={"file": f},
            data={
                "document[name]": f"Takeoff_{state['project_id']}.xlsx",
                "document[description]": state["report_summary"]
            }
        )
    
    state["procore_document_id"] = response.json()["id"]
    return state

# Add to LangGraph workflow
workflow.add_node("upload_procore", upload_to_procore)
workflow.add_edge("generate_report", "upload_procore")
```

---

## Deployment to GitHub

### Step 1: Copy Files to Repository

```bash
# Copy agent
cp construction_takeoff_agent.py agents/orchestrator/

# Copy workflow
cp construction_takeoff_workflow.yml .github/workflows/

# Copy skill
mkdir -p skills/construction-takeoff
cp construction_takeoff_SKILL.md skills/construction-takeoff/SKILL.md

# Create reports directory
mkdir -p reports/takeoff_reports
touch reports/takeoff_reports/.gitkeep
```

### Step 2: Configure GitHub Secrets

```bash
# Via GitHub CLI
gh secret set ANTHROPIC_API_KEY
gh secret set FIRECRAWL_API_KEY
gh secret set SUPABASE_SERVICE_ROLE_KEY

# Or via web interface:
# Settings → Secrets and variables → Actions → New repository secret
```

### Step 3: Commit and Push

```bash
git add agents/orchestrator/construction_takeoff_agent.py
git add .github/workflows/construction_takeoff_workflow.yml
git add skills/construction-takeoff/SKILL.md
git add reports/takeoff_reports/.gitkeep

git commit -m "🏗️ Deploy construction takeoff agent

Features:
- PDF construction plan processing
- Automated quantity extraction via Claude Vision
- Competitor analysis using Firecrawl API
- Cost estimation with FL market rates
- Excel report generation (multi-sheet workbook)
- Supabase insights logging
- GitHub Actions workflow integration

Agent: agents/orchestrator/construction_takeoff_agent.py
Workflow: .github/workflows/construction_takeoff_workflow.yml
Skill: skills/construction-takeoff/SKILL.md

Stack: LangGraph + Claude + Firecrawl + OpenPyXL
Author: Claude Sonnet 4.5 (AI Architect)
Date: 2025-12-19"

git push origin main
```

### Step 4: Verify Deployment

```bash
# Check workflow exists
gh workflow list | grep takeoff

# Trigger test run
gh workflow run construction_takeoff_workflow.yml \
  -f pdf_url="https://example.com/test.pdf" \
  -f project_name="Test Deployment" \
  -f project_id="TEST-001"

# Monitor run
gh run watch
```

---

## Testing

### Unit Testing

```python
# tests/test_construction_takeoff.py

import pytest
from construction_takeoff_agent import (
    process_pdf,
    extract_quantities,
    calculate_costs,
    TakeoffState
)

def test_pdf_processing():
    state = TakeoffState(
        pdf_path="tests/fixtures/sample_plan.pdf",
        project_name="Test",
        project_id="TEST-001",
        # ... initialize other fields
    )
    result = process_pdf(state)
    assert result["status"] == "pdf_processed"
    assert result["pdf_extracted_text"] != ""

def test_cost_calculation():
    state = TakeoffState(
        quantities=[
            {"item": "Excavation", "quantity": 100, "unit": "CY", "category": "earthwork"}
        ],
        # ... other fields
    )
    result = calculate_costs(state)
    assert result["total_estimated_cost"] > 0
    assert "Excavation" in result["cost_estimates"]

# Run tests
pytest tests/test_construction_takeoff.py -v
```

### Integration Testing

```bash
# Test with sample PDF
python agents/orchestrator/construction_takeoff_agent.py \
  tests/fixtures/sample_site_plan.pdf \
  "Integration Test Project" \
  "INTEG-TEST-001"

# Verify outputs
ls -lh /tmp/spd_takeoff_reports/
```

### API Testing

```python
# Test Anthropic API
from anthropic import Anthropic
client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=100,
    messages=[{"role": "user", "content": "Test message"}]
)
assert response.content[0].text

# Test Firecrawl API
response = requests.post(
    "https://api.firecrawl.dev/v0/scrape",
    headers={"Authorization": f"Bearer {os.environ['FIRECRAWL_API_KEY']}"},
    json={"url": "https://www.planswift.com"}
)
assert response.status_code == 200
```

---

## Troubleshooting

### Issue: PDF Processing Fails

**Symptoms:** `PDF processing failed: invalid format`

**Solutions:**
1. Ensure PDF is not password-protected
2. Verify PDF is not corrupted: `pdfinfo your_plan.pdf`
3. Check file size (max 100MB for Claude API)
4. Try converting to PDF/A format

```bash
# Convert to PDF/A using Ghostscript
gs -dPDFA=2 -dBATCH -dNOPAUSE -sColorConversionStrategy=UseDeviceIndependentColor \
  -sDEVICE=pdfwrite -dPDFACompatibilityPolicy=1 \
  -sOutputFile=output_pdfa.pdf input.pdf
```

### Issue: Firecrawl Returns 401

**Symptoms:** `Competitor analysis failed: 401 Unauthorized`

**Solutions:**
1. Verify API key: `echo $FIRECRAWL_API_KEY`
2. Check API key validity on dashboard
3. Ensure key has scraping permissions
4. Check rate limits (free tier: 50 requests/month)

### Issue: Excel Report Missing Data

**Symptoms:** Excel file generated but sheets are empty

**Solutions:**
1. Check state variables before report generation
2. Verify quantity extraction succeeded
3. Add debug logging:
   ```python
   print(f"Quantities: {len(state['quantities'])}")
   print(f"Cost estimates: {len(state['cost_estimates'])}")
   ```

### Issue: Cost Estimates Seem Wrong

**Symptoms:** Costs are unrealistic (too high/low)

**Solutions:**
1. Review `UNIT_COSTS` dictionary for your market
2. Update labor rates for your region
3. Verify quantity units match cost units (SF vs SY, LF vs each)
4. Consider integrating RSMeans API for real-time pricing

### Issue: Supabase Logging Fails

**Symptoms:** `Supabase logging failed: 403 Forbidden`

**Solutions:**
1. Verify service role key (not anon key)
2. Check `insights` table exists
3. Verify table has correct columns
4. Test connection:
   ```bash
   curl -X GET "https://mocerqjnksmhcjzxrewo.supabase.co/rest/v1/insights?limit=1" \
     -H "apikey: YOUR_KEY" \
     -H "Authorization: Bearer YOUR_KEY"
   ```

---

## Cost Optimization

### API Usage Targets

| Service | Target Usage | Monthly Cost | Optimization |
|---------|-------------|--------------|--------------|
| Claude API | 100 takeoffs/month | $30-50 | Use Sonnet over Opus |
| Firecrawl | 50 scrapes/month | $1.50 | Cache competitor data |
| Supabase | Standard logging | $0 (free tier) | Archive old insights |
| GitHub Actions | 100 workflow runs | $0 (free tier) | N/A |

**Total monthly cost:** ~$32-52 for 100 takeoffs

### Optimization Strategies

#### 1. Cache Competitor Data

```python
import json
from datetime import datetime, timedelta

COMPETITOR_CACHE_FILE = "/tmp/competitor_cache.json"
CACHE_DURATION_DAYS = 7

def get_cached_competitor_features():
    if os.path.exists(COMPETITOR_CACHE_FILE):
        with open(COMPETITOR_CACHE_FILE) as f:
            cache = json.load(f)
            cache_date = datetime.fromisoformat(cache["timestamp"])
            if datetime.now() - cache_date < timedelta(days=CACHE_DURATION_DAYS):
                return cache["features"]
    return None

def cache_competitor_features(features):
    with open(COMPETITOR_CACHE_FILE, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "features": features
        }, f)
```

#### 2. Use Claude Haiku for Simple Plans

```python
def select_model(pdf_pages: int, drawing_complexity: str) -> str:
    """Select appropriate model based on complexity"""
    if pdf_pages == 1 and drawing_complexity == "simple":
        return "claude-haiku-4-20250514"  # $0.30/MTok
    else:
        return "claude-sonnet-4-20250514"  # $3/MTok
```

#### 3. Batch Process PDFs

```python
def batch_process_takeoffs(pdf_paths: List[str]) -> List[TakeoffState]:
    """Process multiple takeoffs in one session to reduce overhead"""
    results = []
    workflow = create_takeoff_workflow()
    
    for pdf_path in pdf_paths:
        state = initialize_state(pdf_path)
        result = workflow.invoke(state)
        results.append(result)
    
    return results
```

#### 4. Archive Old Reports

```python
# Archive reports older than 90 days
import shutil
from datetime import datetime, timedelta

archive_date = datetime.now() - timedelta(days=90)
reports_dir = Path("reports/takeoff_reports")
archive_dir = Path("reports/archive")

for report in reports_dir.glob("*.xlsx"):
    if datetime.fromtimestamp(report.stat().st_mtime) < archive_date:
        shutil.move(str(report), str(archive_dir / report.name))
```

---

## Next Steps

1. **Deploy to production** following the deployment steps above
2. **Run test takeoff** with a sample construction plan
3. **Integrate RSMeans API** for real-time cost data
4. **Add Procore integration** for project management
5. **Implement batch processing** for multi-plan projects
6. **Train team** on using GitHub Actions workflow
7. **Monitor costs** via API dashboards

---

## Support

**Repository:** github.com/breverdbidder/spd-site-plan-dev  
**Issues:** Create GitHub issue with [TAKEOFF] prefix  
**Documentation:** See `skills/construction-takeoff/SKILL.md`  
**API Library:** See `docs/API_MEGA_LIBRARY.md` in life-os repo

**Contact:**
- Ariel Shapira (Product Owner)
- Claude Sonnet 4.5 (AI Architect)

---

**Last Updated:** December 19, 2025  
**Version:** 1.0.0  
**Status:** Production Ready
