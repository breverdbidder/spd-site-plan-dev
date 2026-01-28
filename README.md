# SPD Ordinance Scraper

Municipal ordinance scraper for **SPD Site Plan Development** - extracts zoning districts, site plan requirements, and land development code structure from Municode Library.

## Features

- 🏛️ **Municode Scraper** - Handles anti-bot protection using Puppeteer
- 📊 **Structured Extraction** - Zoning districts, site plan requirements, TOC
- 💾 **Supabase Storage** - Persistent storage with proper schema
- 🔄 **Batch Processing** - Scrape multiple municipalities
- 📋 **Site Plan Intelligence** - Extract applicability triggers and review process

## Quick Start

```bash
# Install dependencies
npm install

# Scrape a municipality (outputs JSON)
node src/index.js FL Malabar

# With Supabase storage
SUPABASE_URL=https://your-project.supabase.co \
SUPABASE_KEY=your-service-key \
node src/index.js FL Malabar
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_KEY` | Supabase service role key |
| `HEADLESS` | Set to `false` for visible browser |

## Database Schema

Run the migration in Supabase SQL Editor:

```bash
supabase/migrations/001_create_ordinance_tables.sql
```

### Tables

- **municipalities** - Municipality metadata and scrape status
- **zoning_districts** - Extracted zoning district codes and details
- **ordinance_sections** - TOC and content sections
- **site_plan_requirements** - Site plan triggers and requirements
- **scrape_results** - Raw scrape data for debugging

## Usage Examples

### Single Municipality

```javascript
const { scrapeMunicipality } = require('./src/index');

const results = await scrapeMunicipality('FL', 'Malabar');
console.log(results.zoningDistricts.districts);
```

### Batch Scrape

```javascript
const { batchScrape } = require('./src/index');

const results = await batchScrape([
  { state: 'FL', municipality: 'Malabar' },
  { state: 'FL', municipality: 'Palm Bay' },
  { state: 'FL', municipality: 'Melbourne' }
]);
```

### Scraper Only

```javascript
const MunicodeScraper = require('./src/scrapers/municode_scraper');

const scraper = new MunicodeScraper({ headless: true });
await scraper.init();

const toc = await scraper.scrapeTOC('FL', 'Malabar');
const districts = await scraper.scrapeZoningDistricts('FL', 'Malabar');

await scraper.close();
```

## Output Format

```json
{
  "municipality": "Malabar",
  "state": "FL",
  "scrapedAt": "2026-01-28T17:23:49.150Z",
  "status": "success",
  "toc": {
    "sections": [
      { "title": "Article I - PREAMBLE", "nodeId": "LADECO_ARTIPR" }
    ]
  },
  "zoningDistricts": {
    "districts": [
      { "code": "RR-65", "name": "Rural Residential" },
      { "code": "RS-21", "name": "Single Family LDR" }
    ]
  },
  "sitePlanReview": {
    "sections": [...],
    "applicabilityTriggers": [
      "Any land disturbance >= 1,000 sq ft"
    ]
  }
}
```

## Supported Sources

Currently supports:
- **Municode Library** (library.municode.com)

Planned:
- American Legal Publishing
- General Code
- Code Publishing Company

## Project Structure

```
spd-scraper/
├── src/
│   ├── index.js              # Main entry point
│   ├── scrapers/
│   │   └── municode_scraper.js
│   └── storage/
│       └── supabase_client.js
├── supabase/
│   └── migrations/
│       └── 001_create_ordinance_tables.sql
├── poc/
│   └── malabar_poc_results.json
└── package.json
```

## Related Projects

- **SPD Site Plan Development** - Parent project for site plan automation
- **BidDeed.AI** - Foreclosure auction intelligence platform
- **ZoneWise** - Zoning lookup desktop application

## License

MIT © Everest Capital USA
