# SPD.AI Production Deployment Guide

Comprehensive guide for deploying SPD Site Plan Development to production.

---

## Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Security Configuration](#security-configuration)
3. [Environment Setup](#environment-setup)
4. [Database Deployment](#database-deployment)
5. [Application Deployment](#application-deployment)
6. [Monitoring Setup](#monitoring-setup)
7. [Performance Requirements](#performance-requirements)
8. [Rollback Procedures](#rollback-procedures)
9. [Troubleshooting](#troubleshooting)

---

## Pre-Deployment Checklist

### Security Checklist
- [ ] All service account keys rotated within last 90 days
- [ ] Encryption enabled (AES-256)
- [ ] RLS policies verified on all tables
- [ ] Threat detection system active
- [ ] Rate limiting configured
- [ ] Monitoring dashboards configured
- [ ] Security alerts connected to Slack/email
- [ ] Penetration testing completed (if applicable)
- [ ] OWASP Top 10 compliance verified
- [ ] Secrets scanned with Gitleaks/TruffleHog

### Code Quality Checklist
- [ ] All tests passing (unit, integration, e2e)
- [ ] Code coverage >= 80%
- [ ] No critical security vulnerabilities
- [ ] Dependencies up to date
- [ ] Linting passed (no errors)
- [ ] Type checking passed
- [ ] Documentation updated

### Infrastructure Checklist
- [ ] Supabase project configured
- [ ] GitHub Actions workflows tested
- [ ] Cloudflare Pages connected
- [ ] Domain DNS configured
- [ ] SSL certificates active
- [ ] CDN configured
- [ ] Backup strategy in place

---

## Security Configuration

### 1. Enable 6-Layer Defense

```bash
# Run security setup script
./scripts/setup_security.sh

# Verify security status
python -m src.security.health_check
```

### 2. Configure Service Accounts

Create separate service accounts for each agent:

```sql
-- Run in Supabase SQL Editor
\i sql/security/service_account_setup.sql
```

Service accounts:
- `spd_scraper` - Read-only access to parcels
- `spd_analysis` - Read/write for analysis results
- `spd_report` - Read/write for reports
- `spd_qa` - Read-only for verification

### 3. Deploy RLS Policies

```sql
-- Verify RLS enabled
SELECT tablename, rowsecurity 
FROM pg_tables 
WHERE schemaname = 'public';

-- Apply policies
\i sql/security/rls_policies.sql

-- Verify policies
SELECT * FROM pg_policies WHERE schemaname = 'public';
```

### 4. Configure Encryption

```python
from src.security.encryption_manager import EncryptionManager

# Initialize with production key
manager = EncryptionManager(
    master_key=os.environ["ENCRYPTION_MASTER_KEY"]
)

# Verify encryption working
test = manager.encrypt("test_data")
assert manager.decrypt(test) == "test_data"
```

### 5. Enable Threat Detection

```python
from src.security.threat_detection import ThreatDetector

detector = ThreatDetector(auto_block_critical=True)

# Verify patterns loaded
stats = detector.get_stats()
assert stats["patterns_loaded"] > 50
```

---

## Environment Setup

### Required Environment Variables

```env
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-key
SUPABASE_ANON_KEY=your-anon-key

# Service Account Keys
SPD_SCRAPER_KEY=your-scraper-key
SPD_ANALYSIS_KEY=your-analysis-key
SPD_REPORT_KEY=your-report-key
SPD_QA_KEY=your-qa-key

# Security
ENCRYPTION_MASTER_KEY=your-32-char-key
SLACK_SECURITY_WEBHOOK=https://hooks.slack.com/...
SECURITY_EMAIL=security@biddeed.ai

# AI/ML
ANTHROPIC_API_KEY=your-key
GEMINI_API_KEY=your-key
OPENAI_API_KEY=your-key

# External APIs
BCPAO_API_URL=https://www.bcpao.us/api/v1
CENSUS_API_KEY=your-census-key

# Feature Flags
SECURITY_LEVEL=MAXIMUM
ENCRYPTION_ENABLED=true
THREAT_DETECTION_ENABLED=true
RATE_LIMIT_ENABLED=true
AUDIT_LOG_LEVEL=FULL
```

### GitHub Secrets Configuration

Add these secrets in GitHub repository settings:

| Secret Name | Description |
|-------------|-------------|
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase service role key |
| `ENCRYPTION_MASTER_KEY` | 32-character encryption key |
| `SLACK_SECURITY_WEBHOOK` | Slack webhook for alerts |
| `GREPTILE_API_KEY` | Greptile code analysis key |

---

## Database Deployment

### 1. Run Migrations

```bash
# Apply all migrations
supabase db push

# Or manually apply
psql $DATABASE_URL -f migrations/001_initial_schema.sql
psql $DATABASE_URL -f migrations/002_security_tables.sql
psql $DATABASE_URL -f migrations/003_rls_policies.sql
```

### 2. Verify Tables

Required tables:
- `parcels` - Property data
- `pipeline_runs` - Pipeline execution state
- `scoring_results` - ML predictions
- `reports` - Generated reports
- `security_alerts` - Security audit log
- `performance_metrics` - Performance data

### 3. Verify RLS

```sql
-- Check RLS enabled on all tables
SELECT schemaname, tablename, rowsecurity
FROM pg_tables
WHERE schemaname = 'public'
  AND tablename IN ('parcels', 'pipeline_runs', 'scoring_results', 'reports');

-- All should show rowsecurity = true
```

---

## Application Deployment

### 1. GitHub Actions Deployment

Deployment is automated via GitHub Actions on push to `main`:

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Run tests
        run: pytest tests/ --cov=src --cov-fail-under=80
      
      - name: Security scan
        run: |
          pip install safety bandit
          safety check -r requirements.txt
          bandit -r src/
      
      - name: Deploy to Cloudflare
        uses: cloudflare/pages-action@v1
        with:
          apiToken: ${{ secrets.CLOUDFLARE_API_TOKEN }}
          accountId: ${{ secrets.CLOUDFLARE_ACCOUNT_ID }}
          projectName: spd-ai
```

### 2. Manual Deployment

```bash
# Build
npm run build

# Deploy to Cloudflare Pages
npx wrangler pages deploy dist --project-name spd-ai

# Deploy backend to Render/Railway
git push render main
```

### 3. Verify Deployment

```bash
# Health check
curl https://api.biddeed.ai/v1/api/health

# Expected response:
# {"status": "healthy", "version": "1.0.0", "timestamp": "..."}
```

---

## Monitoring Setup

### 1. Performance Monitoring

```python
from src.monitoring.performance_tracker import get_monitor

monitor = get_monitor()

# Verify metrics collection
stats = monitor.get_all_stats()
print(f"Metrics tracked: {len(stats)}")
```

### 2. Security Monitoring

Configure daily security dashboard:

```bash
# Add to crontab
0 9 * * * python -m src.security.security_dashboard --send-report
```

### 3. Alert Configuration

Severity routing:
- **INFO**: Console + Supabase only
- **WARNING**: + Slack notification
- **HIGH**: + Slack notification (priority)
- **CRITICAL**: + Slack + Email + PagerDuty

---

## Performance Requirements

### API Response Times
| Endpoint | Target | Maximum |
|----------|--------|---------|
| `/api/chat` | < 500ms | 2000ms |
| `/api/feasibility/analyze` | < 1s | 5s |
| `/api/properties/{id}` | < 200ms | 1000ms |
| `/api/pipeline/execute` | < 2s (start) | 5s |

### Pipeline Performance
| Stage | Target | Maximum |
|-------|--------|---------|
| Discovery | < 30s | 60s |
| Scraping | < 60s | 120s |
| ML Scoring | < 10s | 30s |
| Report Generation | < 30s | 60s |
| **Total Pipeline** | **< 15 min** | **30 min** |

### Capacity
- Concurrent users: 50+
- Parcels per pipeline run: 100+
- API requests/minute: 1000+
- Uptime SLA: 99.5%

---

## Rollback Procedures

### 1. Application Rollback

```bash
# Revert to previous deployment
git revert HEAD
git push origin main

# Or rollback Cloudflare Pages
npx wrangler pages deployment rollback --project-name spd-ai
```

### 2. Database Rollback

```bash
# Rollback last migration
supabase db reset --version 002

# Or restore from backup
supabase db restore --backup-id <backup-id>
```

### 3. Security Rollback

```bash
# Revert security changes
./scripts/rollback_security.sh

# Restore previous service account permissions
psql $DATABASE_URL -f rollback/restore_permissions.sql
```

### 4. Emergency Procedures

```bash
# Kill all active pipelines
curl -X POST https://api.biddeed.ai/v1/api/admin/kill-pipelines \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# Enable maintenance mode
curl -X POST https://api.biddeed.ai/v1/api/admin/maintenance \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{"enabled": true}'
```

---

## Troubleshooting

### Common Issues

#### 1. Pipeline Stuck
```bash
# Check pipeline status
curl https://api.biddeed.ai/v1/api/pipeline/{run_id}/status

# Force restart
curl -X POST https://api.biddeed.ai/v1/api/pipeline/{run_id}/restart
```

#### 2. High Error Rate
```bash
# Check recent errors
python -m src.utils.error_analysis --last-hour

# Check circuit breaker status
curl https://api.biddeed.ai/v1/api/health/circuit-breakers
```

#### 3. Security Alert Investigation
```sql
-- Recent security alerts
SELECT * FROM security_alerts
WHERE created_at > NOW() - INTERVAL '1 hour'
ORDER BY severity DESC, created_at DESC;
```

#### 4. Performance Degradation
```python
# Get performance stats
from src.monitoring.performance_tracker import get_monitor

monitor = get_monitor()
stats = monitor.get_stats("api_call")
print(f"P95 latency: {stats.p95}ms")
```

### Support Contacts
- **Technical Issues**: dev@biddeed.ai
- **Security Incidents**: security@biddeed.ai
- **Urgent Escalation**: Slack #spd-oncall

---

## Appendix

### A. Required IAM Permissions

```json
{
  "supabase": ["read", "write", "delete"],
  "github": ["repo", "workflow"],
  "cloudflare": ["pages:write", "workers:write"]
}
```

### B. Network Requirements

| Service | Port | Protocol |
|---------|------|----------|
| Supabase | 443 | HTTPS |
| BCPAO API | 443 | HTTPS |
| Census API | 443 | HTTPS |
| Slack | 443 | HTTPS |

### C. Compliance

- SOC 2 Type II
- ISO 27001
- OWASP LLM Top 10
- NIST Cybersecurity Framework

---

*Last Updated: January 2026*
*BidDeed.AI / Everest Capital USA*
