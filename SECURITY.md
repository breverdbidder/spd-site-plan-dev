# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take security vulnerabilities seriously. If you discover a security issue, please report it responsibly.

### How to Report

1. **DO NOT** create a public GitHub issue for security vulnerabilities
2. Email security concerns to: security@biddeed.ai
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

### Response Timeline

- **Initial Response**: Within 24 hours
- **Assessment**: Within 72 hours
- **Fix Timeline**: Depends on severity
  - Critical: 24-48 hours
  - High: 1 week
  - Medium: 2 weeks
  - Low: Next release

### What to Expect

1. Acknowledgment of your report
2. Assessment of severity and impact
3. Regular updates on fix progress
4. Credit in release notes (if desired)

## Security Measures

### Authentication & Authorization
- JWT-based authentication
- Role-based access control (RBAC)
- Session management with secure cookies

### Data Protection
- AES-256 encryption at rest
- TLS 1.3 in transit
- PII handling compliant with privacy regulations

### Infrastructure Security
- Supabase Row Level Security (RLS)
- Environment variable secrets management
- Regular credential rotation (90-day cycle)

### Code Security
- SAST scanning (Bandit, Semgrep)
- Dependency vulnerability scanning (Safety, pip-audit)
- Secret detection (Gitleaks, TruffleHog)
- Code review requirements

### Monitoring
- Security event logging
- Anomaly detection
- Performance monitoring with alerting

## Security Checklist

### For Contributors
- [ ] No hardcoded secrets
- [ ] Input validation on all endpoints
- [ ] SQL injection prevention (parameterized queries)
- [ ] XSS prevention (output encoding)
- [ ] CSRF protection
- [ ] Secure error handling (no stack traces in production)

### For Deployments
- [ ] Environment variables for secrets
- [ ] HTTPS only
- [ ] Security headers configured
- [ ] Rate limiting enabled
- [ ] Logging enabled
- [ ] Monitoring active

## Compliance

This project adheres to:
- OWASP Top 10 guidelines
- CWE/SANS Top 25 mitigations
- Industry security best practices

## Contact

- Security Team: security@biddeed.ai
- General Issues: GitHub Issues
- Documentation: https://docs.biddeed.ai

---

*Last Updated: January 2026*
*BidDeed.AI / Everest Capital USA*
