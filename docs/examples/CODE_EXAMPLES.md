# SPD.AI Code Examples

Comprehensive code examples for integrating with the SPD Site Plan Development platform.

---

## Table of Contents

1. [Chat API Integration](#chat-api-integration)
2. [Feasibility Analysis](#feasibility-analysis)
3. [Property Discovery](#property-discovery)
4. [Pipeline Execution](#pipeline-execution)
5. [Performance Monitoring](#performance-monitoring)
6. [Security Implementation](#security-implementation)
7. [React Components](#react-components)

---

## Chat API Integration

### Basic Chat Request (Python)

```python
import httpx
import asyncio

async def send_chat_message(message: str, site_context: dict = None):
    """Send a message to SPD.AI chat"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.biddeed.ai/v1/api/chat",
            json={
                "message": message,
                "siteContext": site_context or {}
            },
            headers={"Authorization": "Bearer YOUR_API_KEY"}
        )
        return response.json()

# Usage
result = asyncio.run(send_chat_message(
    message="I have 5 acres zoned C-2. What can I build?",
    site_context={"acreage": 5.0, "zoning": "C-2", "jurisdiction": "Palm Bay"}
))

print(f"Response: {result['response']}")
print(f"Model: {result['metadata']['model']}")
print(f"Tier: {result['metadata']['tier']}")
```

### Conversation with History (Python)

```python
async def chat_with_history(messages: list, new_message: str):
    """Continue a conversation with context"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.biddeed.ai/v1/api/chat",
            json={
                "message": new_message,
                "messages": messages  # Previous conversation
            },
            headers={"Authorization": "Bearer YOUR_API_KEY"}
        )
        return response.json()

# Build conversation
conversation = [
    {"role": "user", "content": "I have a 10 acre parcel"},
    {"role": "assistant", "content": "What zoning is the parcel?"},
    {"role": "user", "content": "Industrial zoning"}
]

result = asyncio.run(chat_with_history(
    messages=conversation,
    new_message="What development types work best?"
))
```

### JavaScript/React Example

```javascript
import { useState, useCallback } from 'react';

const useChatAPI = () => {
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState([]);

  const sendMessage = useCallback(async (message, siteContext = {}) => {
    setLoading(true);
    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message, siteContext, messages })
      });
      
      const data = await response.json();
      
      setMessages(prev => [
        ...prev,
        { role: 'user', content: message },
        { role: 'assistant', content: data.response }
      ]);
      
      return data;
    } finally {
      setLoading(false);
    }
  }, [messages]);

  return { sendMessage, messages, loading };
};
```

---

## Feasibility Analysis

### Run Feasibility Analysis (Python)

```python
async def analyze_feasibility(
    acreage: float,
    zoning: str,
    typology: str,
    params: dict = None
):
    """Run feasibility analysis for a site"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.biddeed.ai/v1/api/feasibility/analyze",
            json={
                "acreage": acreage,
                "zoning": zoning,
                "typology": typology,
                "params": params or {}
            },
            headers={"Authorization": "Bearer YOUR_API_KEY"}
        )
        return response.json()

# Multi-family analysis
result = asyncio.run(analyze_feasibility(
    acreage=5.0,
    zoning="R-3",
    typology="multifamily",
    params={"parkingRatio": 1.5, "stories": 3}
))

print(f"Units: {result['units']}")
print(f"Gross SF: {result['grossSF']:,}")
print(f"Parking: {result['parkingSpaces']}")
print(f"Profit Margin: {result['proForma']['margin']}%")
```

### Compare Multiple Typologies

```python
async def compare_typologies(acreage: float, zoning: str):
    """Compare feasibility across all typologies"""
    typologies = [
        "multifamily", "selfStorage", "industrial",
        "singleFamily", "seniorLiving", "medical", "retail", "hotel"
    ]
    
    results = []
    for typology in typologies:
        result = await analyze_feasibility(acreage, zoning, typology)
        results.append({
            "typology": typology,
            "units": result.get("units", 0),
            "grossSF": result.get("grossSF", 0),
            "profit": result.get("proForma", {}).get("profit", 0),
            "margin": result.get("proForma", {}).get("margin", 0),
        })
    
    # Sort by profit margin
    return sorted(results, key=lambda x: x["margin"], reverse=True)

# Compare all typologies for a 5-acre C-2 site
comparisons = asyncio.run(compare_typologies(5.0, "C-2"))
for comp in comparisons:
    print(f"{comp['typology']}: {comp['margin']}% margin, ${comp['profit']:,.0f} profit")
```

---

## Property Discovery

### Discover Properties with Filters

```python
async def discover_properties(
    jurisdiction: str = None,
    min_acreage: float = None,
    max_acreage: float = None,
    land_use_filter: list = None,
    limit: int = 100
):
    """Discover properties matching criteria"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.biddeed.ai/v1/api/properties/discover",
            json={
                "jurisdiction": jurisdiction,
                "minAcreage": min_acreage,
                "maxAcreage": max_acreage,
                "landUseFilter": land_use_filter,
                "limit": limit
            },
            headers={"Authorization": "Bearer YOUR_API_KEY"}
        )
        return response.json()

# Find vacant land 5-20 acres in Palm Bay
properties = asyncio.run(discover_properties(
    jurisdiction="Palm Bay",
    min_acreage=5.0,
    max_acreage=20.0,
    land_use_filter=["0000", "0100"],  # Vacant land codes
    limit=50
))

print(f"Found {len(properties['parcels'])} matching properties")
for parcel in properties['parcels'][:5]:
    print(f"  {parcel['account']}: {parcel['acreage']} ac @ {parcel['siteAddress']}")
```

### Get Property Details and Score

```python
async def get_property_with_score(account_id: str):
    """Get property details and ML score"""
    async with httpx.AsyncClient() as client:
        # Get details
        details_resp = await client.get(
            f"https://api.biddeed.ai/v1/api/properties/{account_id}",
            headers={"Authorization": "Bearer YOUR_API_KEY"}
        )
        details = details_resp.json()
        
        # Get ML score
        score_resp = await client.get(
            f"https://api.biddeed.ai/v1/api/properties/{account_id}/score",
            headers={"Authorization": "Bearer YOUR_API_KEY"}
        )
        score = score_resp.json()
        
        return {**details, "scoring": score}

# Get full analysis for Bliss Palm Bay
property_data = asyncio.run(get_property_with_score("2835546"))

print(f"Property: {property_data['siteAddress']}")
print(f"Acreage: {property_data['acreage']}")
print(f"Score: {property_data['scoring']['score']}/100")
print(f"Recommendation: {property_data['scoring']['recommendation']}")
```

---

## Pipeline Execution

### Start Pipeline Run

```python
async def start_pipeline(
    jurisdiction: str = None,
    min_acreage: float = None,
    filters: dict = None
):
    """Start a pipeline execution"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.biddeed.ai/v1/api/pipeline/execute",
            json={
                "jurisdiction": jurisdiction,
                "minAcreage": min_acreage,
                "filters": filters or {}
            },
            headers={"Authorization": "Bearer YOUR_API_KEY"}
        )
        return response.json()

# Start pipeline for Palm Bay parcels
run = asyncio.run(start_pipeline(
    jurisdiction="Palm Bay",
    min_acreage=5.0
))

print(f"Pipeline started: {run['runId']}")
```

### Monitor Pipeline Progress

```python
async def monitor_pipeline(run_id: str, poll_interval: int = 5):
    """Monitor pipeline until completion"""
    async with httpx.AsyncClient() as client:
        while True:
            response = await client.get(
                f"https://api.biddeed.ai/v1/api/pipeline/{run_id}/status",
                headers={"Authorization": "Bearer YOUR_API_KEY"}
            )
            status = response.json()
            
            print(f"Stage: {status['currentStage']} ({status['stagesCompleted']}/12)")
            
            if status['status'] in ['COMPLETED', 'FAILED']:
                return status
            
            await asyncio.sleep(poll_interval)

# Monitor the pipeline
final_status = asyncio.run(monitor_pipeline(run['runId']))
print(f"Final status: {final_status['status']}")
print(f"Parcels analyzed: {final_status['parcelsAnalyzed']}")
```

---

## Performance Monitoring

### Using the Performance Monitor

```python
from src.monitoring.performance_tracker import PerformanceMonitor, PipelineMonitor

# Initialize monitor
monitor = PerformanceMonitor()

# Time a function with decorator
@monitor.timed("database_query")
def fetch_parcels():
    # Your database query here
    pass

# Manual timing with context manager
with monitor.timer("api_call", tags={"endpoint": "/api/chat"}):
    # Your API call here
    pass

# Get statistics
stats = monitor.get_stats("database_query")
print(f"Avg latency: {stats.avg}ms")
print(f"P95 latency: {stats.p95}ms")

# Pipeline-specific monitoring
pipeline_monitor = PipelineMonitor(monitor)
pipeline_monitor.start_run("run-001")

with pipeline_monitor.stage_timer("discovery"):
    # Discovery stage code
    pass

with pipeline_monitor.stage_timer("scraping"):
    # Scraping stage code
    pass

pipeline_monitor.end_run(success=True)

# Get pipeline stats
print(pipeline_monitor.get_stats())
```

---

## Security Implementation

### RLS Policy Verification

```python
from src.security.rls_verification import RLSVerifier, run_rls_verification

# Initialize verifier
verifier = RLSVerifier(
    supabase_url="https://your-project.supabase.co",
    service_key="your-service-key"
)

# Verify all tables
results = asyncio.run(verifier.verify_all_tables())

print(f"Compliance Score: {results['summary']['compliance_score']}%")
print(f"Missing Policies: {results['summary']['total_policies_missing']}")

# Generate migration SQL for missing policies
if results['summary']['total_policies_missing'] > 0:
    migration_sql = verifier.generate_migration()
    print(migration_sql)
```

### Credential Rotation

```python
from src.security.credential_rotation import (
    CredentialRotationManager, 
    RotationPolicy, 
    CredentialType
)

# Initialize manager
manager = CredentialRotationManager()

# Register credentials for rotation
manager.register_credential(RotationPolicy(
    credential_name="SUPABASE_SERVICE_KEY",
    credential_type=CredentialType.API_KEY,
    rotation_interval_days=90,
    notification_days_before=7,
    auto_rollback_on_failure=True
))

# Check what needs rotation
needs_rotation = manager.get_credentials_needing_rotation()
print(f"Credentials needing rotation: {len(needs_rotation)}")

# Run scheduled rotation
events = asyncio.run(manager.check_and_rotate_all())
print(f"Rotations performed: {len(events)}")
```

---

## React Components

### Using ChatInterface

```jsx
import { ChatInterface } from './components';

function App() {
  const [siteContext, setSiteContext] = useState({
    acreage: 5.0,
    zoning: 'C-2'
  });
  
  const handleParamsExtracted = (params) => {
    setSiteContext(prev => ({ ...prev, ...params }));
  };
  
  return (
    <ChatInterface
      siteContext={siteContext}
      onSiteParamsExtracted={handleParamsExtracted}
      apiBase=""
    />
  );
}
```

### Using FormInterface

```jsx
import { FormInterface } from './components';

function App() {
  const [acreage, setAcreage] = useState(5.0);
  const [zoning, setZoning] = useState('R-2');
  const [typology, setTypology] = useState('multifamily');
  const [params, setParams] = useState({});
  const [isGenerating, setIsGenerating] = useState(false);
  
  const handleGenerate = async () => {
    setIsGenerating(true);
    // Call feasibility API
    setIsGenerating(false);
  };
  
  return (
    <FormInterface
      siteAcreage={acreage}
      setSiteAcreage={setAcreage}
      zoning={zoning}
      setZoning={setZoning}
      selectedTypology={typology}
      setSelectedTypology={setTypology}
      params={params}
      setParams={setParams}
      onGenerate={handleGenerate}
      isGenerating={isGenerating}
    />
  );
}
```

### Full Application Layout

```jsx
import { 
  ChatInterface, 
  FormInterface, 
  Results, 
  MapView,
  COLORS,
  TYPOLOGY_CONFIGS 
} from './components';

function SPDApp() {
  // State
  const [inputMode, setInputMode] = useState('chat');
  const [siteAcreage, setSiteAcreage] = useState(5.0);
  const [zoning, setZoning] = useState('R-2');
  const [selectedTypology, setSelectedTypology] = useState('multifamily');
  const [params, setParams] = useState({});
  const [results, setResults] = useState(null);
  
  // Calculate feasibility
  const calculateFeasibility = async () => {
    const response = await fetch('/api/feasibility/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        acreage: siteAcreage,
        zoning,
        typology: selectedTypology,
        params
      })
    });
    const data = await response.json();
    setResults(data);
  };
  
  return (
    <div style={{ display: 'flex', height: '100vh' }}>
      {/* Left Sidebar - Input */}
      <div style={{ width: 400, borderRight: `1px solid ${COLORS.border}` }}>
        {inputMode === 'chat' ? (
          <ChatInterface
            siteContext={{ acreage: siteAcreage, zoning, typology: selectedTypology }}
            onSiteParamsExtracted={(p) => {
              if (p.acreage) setSiteAcreage(p.acreage);
              if (p.zoning) setZoning(p.zoning);
            }}
          />
        ) : (
          <FormInterface
            siteAcreage={siteAcreage}
            setSiteAcreage={setSiteAcreage}
            zoning={zoning}
            setZoning={setZoning}
            selectedTypology={selectedTypology}
            setSelectedTypology={setSelectedTypology}
            params={params}
            setParams={setParams}
            onGenerate={calculateFeasibility}
          />
        )}
      </div>
      
      {/* Center - Map */}
      <div style={{ flex: 1 }}>
        <MapView
          siteAcreage={siteAcreage}
          zoning={zoning}
          results={results}
          location="Brevard County, FL"
        />
      </div>
      
      {/* Right Sidebar - Results */}
      <div style={{ width: 350, borderLeft: `1px solid ${COLORS.border}` }}>
        <Results results={results} />
      </div>
    </div>
  );
}

export default SPDApp;
```

---

## Error Handling Best Practices

```python
from src.utils.error_handler import (
    ErrorHandler,
    with_retry,
    with_error_handling,
    ErrorCategory
)

# Use decorators for automatic error handling
@with_retry(max_retries=3, base_delay=1.0)
@with_error_handling
async def risky_api_call():
    # Your API call here
    pass

# Manual error handling
handler = ErrorHandler("my_module")

try:
    result = await risky_api_call()
except Exception as e:
    error = handler.handle_error(e, {"context": "api_call"})
    
    if error.category == ErrorCategory.RATE_LIMIT:
        # Wait and retry
        await asyncio.sleep(error.context.get("retry_after", 60))
    elif error.category == ErrorCategory.NETWORK:
        # Use cached data or fallback
        pass
```

---

*Generated by BidDeed.AI / Everest Capital USA*
