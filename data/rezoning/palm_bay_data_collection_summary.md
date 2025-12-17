
# Palm Bay Rezoning Data Collection Summary

## Data Sources Explored

### PrimeGov Portal (palmbayflorida.primegov.com)
- **Status**: API accessible for meeting metadata
- **Limitation**: Document downloads require authentication
- **Data obtained**: 607 meetings (2020-2025), 64 P&Z meetings
- **API Endpoints**:
  - `/api/meeting/search?from=M/D/Y&to=M/D/Y` - Returns meeting list
  - `/Portal/MeetingPreview?compiledMeetingDocumentFileId=ID` - Requires login

### NovusAgenda (palmbayfl.novusagenda.com)
- **Status**: Legacy system, AJAX-based
- **Limitation**: JavaScript-rendered, no public API
- **Meeting Type ID 6**: Planning & Zoning Board/LPA

### civic-scraper Python Library
- **Supports**: PrimeGov, Granicus, CivicPlus, Legistar platforms
- **Issue**: Palm Bay's portal structure doesn't match expected patterns
- **Alternative**: Direct API calls work better

### Web Search Results
- thepalmbayer.com - Local news coverage
- citizenportal.ai - AI meeting summaries
- palmbayflorida.org - City announcements
- novusagenda attachments - Ordinance documents

## Cases Found: 20

| Year | Count |
|------|-------|
| 2019 | 2 |
| 2020 | 2 |
| 2021 | 3 |
| 2023 | 4 |
| 2024 | 7 |
| 2025 | 2 |

## Statistics
- Approved: 15 (75%)
- Denied: 0 (0%)
- Withdrawn: 1
- Pending: 4

## Gap Analysis
- Current: 20 cases
- Minimum for ML: 100 cases
- Gap: 80 cases

## Recommendation
Submit public records request to:
- Email: landdevelopmentweb@palmbayfl.gov
- Phone: (321) 733-3042

Florida Sunshine Law (Chapter 119) requires response within reasonable time.
