# SPD.AI API Reference

Complete API documentation for the SPD Site Plan Development platform.

---

## Base URL

- **Production:** `https://api.biddeed.ai/v1`
- **Development:** `http://localhost:8788`

## Authentication

All endpoints require Bearer token authentication:

```
Authorization: Bearer <your_api_key>
```

---

## Chat API

### POST /api/chat

Send a message to the AI assistant.

**Request Body:**
```json
{
  "message": "string (required)",
  "siteContext": {
    "acreage": "number (optional)",
    "zoning": "string (optional)",
    "jurisdiction": "string (optional)",
    "typology": "string (optional)"
  },
  "messages": [
    {
      "role": "user | assistant",
      "content": "string"
    }
  ]
}
```

**Response:**
```json
{
  "response": "string",
  "metadata": {
    "tier": "FREE | PAID",
    "model": "string",
    "latency_ms": "number",
    "tokens_used": "number"
  },
  "extractedParams": {
    "acreage": "number | null",
    "zoning": "string | null"
  }
}
```

**Status Codes:**
- `200` - Success
- `400` - Invalid request
- `401` - Unauthorized
- `429` - Rate limit exceeded
- `500` - Server error

---

## Feasibility API

### POST /api/feasibility/analyze

Run feasibility analysis for a site.

**Request Body:**
```json
{
  "acreage": "number (required)",
  "zoning": "string (required)",
  "typology": "string (required)",
  "params": {
    "parkingRatio": "number (optional, default: 1.5)",
    "stories": "number (optional)",
    "climatePercent": "number (optional, for selfStorage)"
  }
}
```

**Typology Values:**
- `multifamily` - Multi-family residential
- `selfStorage` - Self-storage facility
- `industrial` - Industrial/warehouse
- `singleFamily` - Single-family subdivision
- `seniorLiving` - Senior living facility
- `medical` - Medical office
- `retail` - Retail center
- `hotel` - Hotel/hospitality

**Response:**
```json
{
  "typology": "string",
  "metrics": {
    "grossSF": "number",
    "netSF": "number",
    "units": "number",
    "parkingSpaces": "number",
    "coverage": "number",
    "far": "number"
  },
  "unitMix": {
    "5x5": "number",
    "5x10": "number",
    "10x10": "number"
  },
  "proForma": {
    "landCost": "number",
    "hardCosts": "number",
    "softCosts": "number",
    "contingency": "number",
    "totalCost": "number",
    "stabilizedNOI": "number",
    "capRate": "number",
    "asStabilizedValue": "number",
    "profit": "number",
    "margin": "number"
  }
}
```

---

## Property API

### POST /api/properties/discover

Discover properties matching criteria.

**Request Body:**
```json
{
  "jurisdiction": "string (optional)",
  "minAcreage": "number (optional)",
  "maxAcreage": "number (optional)",
  "landUseFilter": ["string"] ,
  "zoningFilter": ["string"],
  "excludeFlood": "boolean (optional)",
  "limit": "number (optional, default: 100, max: 500)"
}
```

**Response:**
```json
{
  "parcels": [
    {
      "account": "string",
      "parcelId": "string",
      "siteAddress": "string",
      "owner": "string",
      "acreage": "number",
      "zoning": "string",
      "jurisdiction": "string",
      "marketValue": "number",
      "landUseCode": "string"
    }
  ],
  "total": "number",
  "hasMore": "boolean"
}
```

### GET /api/properties/{accountId}

Get property details.

**Response:**
```json
{
  "account": "string",
  "parcelId": "string",
  "siteAddress": "string",
  "legalDescription": "string",
  "owner": "string",
  "acreage": "number",
  "squareFeet": "number",
  "zoning": "string",
  "zoningDescription": "string",
  "jurisdiction": "string",
  "landUseCode": "string",
  "landUseDescription": "string",
  "marketValue": "number",
  "assessedValue": "number",
  "taxAmount": "number",
  "yearBuilt": "number | null",
  "buildingSF": "number | null",
  "floodZone": "string | null",
  "utilities": {
    "water": "boolean",
    "sewer": "boolean",
    "electric": "boolean",
    "gas": "boolean"
  },
  "photos": ["string"],
  "lastUpdated": "string (ISO date)"
}
```

### GET /api/properties/{accountId}/score

Get ML scoring for property.

**Response:**
```json
{
  "account": "string",
  "score": "number (0-100)",
  "recommendation": "BID | REVIEW | WATCH | SKIP",
  "confidence": "number (0-100)",
  "components": {
    "jurisdiction": "number",
    "landUse": "number",
    "acreage": "number",
    "valueArbitrage": "number",
    "locationBonus": "number"
  },
  "factors": {
    "positive": ["string"],
    "negative": ["string"]
  },
  "scoredAt": "string (ISO date)"
}
```

---

## Pipeline API

### POST /api/pipeline/execute

Start a pipeline execution.

**Request Body:**
```json
{
  "jurisdiction": "string (optional)",
  "minAcreage": "number (optional)",
  "filters": {
    "landUse": ["string"],
    "zoning": ["string"]
  },
  "stages": ["string"] 
}
```

**Response:**
```json
{
  "runId": "string",
  "status": "QUEUED",
  "estimatedDuration": "number (seconds)",
  "startedAt": "string (ISO date)"
}
```

### GET /api/pipeline/{runId}/status

Get pipeline run status.

**Response:**
```json
{
  "runId": "string",
  "status": "QUEUED | IN_PROGRESS | COMPLETED | FAILED",
  "currentStage": "string",
  "stagesCompleted": "number",
  "totalStages": "number",
  "parcelsAnalyzed": "number",
  "parcelsRemaining": "number",
  "errors": ["string"],
  "startedAt": "string (ISO date)",
  "completedAt": "string (ISO date) | null",
  "duration": "number (seconds) | null"
}
```

---

## Security API

### GET /api/security/alerts

Get active security alerts.

**Query Parameters:**
- `severity` - Filter by severity (CRITICAL, HIGH, MEDIUM, LOW)
- `status` - Filter by status (active, acknowledged, resolved)
- `limit` - Max results (default: 50)

**Response:**
```json
{
  "alerts": [
    {
      "alertId": "string",
      "severity": "string",
      "category": "string",
      "title": "string",
      "description": "string",
      "source": "string",
      "timestamp": "string (ISO date)",
      "acknowledged": "boolean",
      "resolved": "boolean"
    }
  ],
  "total": "number"
}
```

### POST /api/security/alerts/{alertId}/acknowledge

Acknowledge an alert.

**Request Body:**
```json
{
  "notes": "string (optional)"
}
```

### GET /api/security/hitl/pending

Get pending HITL decisions.

**Response:**
```json
{
  "decisions": [
    {
      "decisionId": "string",
      "triggerType": "HIGH_VALUE | LOW_CONFIDENCE | COMPLEX_LIENS | ANOMALY",
      "title": "string",
      "description": "string",
      "context": {},
      "createdAt": "string (ISO date)",
      "expiresAt": "string (ISO date)"
    }
  ],
  "count": "number"
}
```

### POST /api/security/hitl/{decisionId}/approve

Approve a HITL decision.

**Request Body:**
```json
{
  "notes": "string (optional)"
}
```

### POST /api/security/hitl/{decisionId}/reject

Reject a HITL decision.

**Request Body:**
```json
{
  "notes": "string (required)"
}
```

---

## Health API

### GET /api/health

Health check endpoint.

**Response:**
```json
{
  "status": "healthy | degraded | unhealthy",
  "version": "string",
  "timestamp": "string (ISO date)",
  "components": {
    "database": "healthy | unhealthy",
    "cache": "healthy | unhealthy",
    "llm": "healthy | unhealthy"
  }
}
```

### GET /api/metrics

Get system metrics.

**Response:**
```json
{
  "requests": {
    "total": "number",
    "success": "number",
    "errors": "number"
  },
  "latency": {
    "p50": "number",
    "p95": "number",
    "p99": "number"
  },
  "llm": {
    "freeRequests": "number",
    "paidRequests": "number",
    "tokensUsed": "number"
  }
}
```

---

## Error Responses

All errors follow this format:

```json
{
  "error": {
    "code": "string",
    "message": "string",
    "details": {}
  }
}
```

**Error Codes:**
- `INVALID_REQUEST` - Malformed request body
- `UNAUTHORIZED` - Invalid or missing API key
- `FORBIDDEN` - Insufficient permissions
- `NOT_FOUND` - Resource not found
- `RATE_LIMITED` - Too many requests
- `INTERNAL_ERROR` - Server error

---

## Rate Limits

| Tier | Requests/min | Requests/day |
|------|--------------|--------------|
| Free | 10 | 100 |
| Pro | 60 | 5,000 |
| Enterprise | 300 | Unlimited |

Rate limit headers:
- `X-RateLimit-Limit` - Max requests per window
- `X-RateLimit-Remaining` - Remaining requests
- `X-RateLimit-Reset` - Window reset time (Unix timestamp)

---

*BidDeed.AI / Everest Capital USA*
