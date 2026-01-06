# SPD.AI - Site Planning & Development Intelligence

> An AI-powered site planning feasibility platform by BidDeed.AI

![SPD.AI](https://img.shields.io/badge/Version-1.0.0-blue)
![BidDeed.AI](https://img.shields.io/badge/Powered%20by-BidDeed.AI-green)
![License](https://img.shields.io/badge/License-Proprietary-red)

## Overview

SPD.AI is an **original** site planning and development feasibility platform designed for real estate developers, architects, and investors in Brevard County, Florida.

**This is NOT a clone of any existing product.** SPD.AI was built from the ground up using:
- React for the frontend
- Mapbox GL JS for mapping
- Turf.js for spatial calculations
- Original algorithms for feasibility analysis
- BidDeed.AI infrastructure for data

## Features

### 🗺️ Interactive Site Definition
- Draw parcels directly on the map
- Search by address or parcel ID
- Import GIS data
- Automatic zoning lookup for Brevard County

### ⚡ Instant Feasibility Generation
- AI-optimized unit mix
- Parking ratio calculations
- Building placement optimization
- Real-time parameter adjustments

### 📊 Pro Forma Analysis
- Land cost estimates
- Hard/soft cost projections
- NOI and yield-on-cost calculations
- Profit margin analysis

### 🏗️ Five Development Typologies
1. **Multi-Family** - Apartments, condos, student housing
2. **Single-Family** - Subdivisions, townhomes, BTR
3. **Industrial** - Warehouses, logistics, flex
4. **Retail** - Shopping centers, pad sites
5. **Hotel** - Limited & full service

## Tech Stack

| Component | Technology |
|-----------|------------|
| Frontend | React 18 |
| Mapping | Mapbox GL JS + Mapbox Draw |
| Spatial | Turf.js |
| Styling | CSS-in-JS (styled objects) |
| State | React Hooks |
| Hosting | Lovable / Cloudflare Pages |
| Backend | BidDeed.AI API (Supabase) |

## Project Structure

```
spd-ai/
├── src/
│   ├── components/
│   │   ├── App.jsx           # Main application
│   │   ├── MapView.jsx       # Mapbox integration
│   │   ├── Sidebar.jsx       # Parameter controls
│   │   ├── ResultsPanel.jsx  # Feasibility results
│   │   └── ProForma.jsx      # Financial analysis
│   ├── hooks/
│   │   ├── useMap.js         # Map state management
│   │   ├── useFeasibility.js # Calculation engine
│   │   └── useZoning.js      # Zoning data
│   ├── utils/
│   │   ├── calculations.js   # Feasibility formulas
│   │   ├── zoning.js         # Zoning lookup
│   │   └── proforma.js       # Financial calculations
│   └── data/
│       └── brevard-zoning.json
├── public/
│   └── index.html
├── package.json
└── README.md
```

## Deployment to Lovable

### Option 1: Direct Import

1. Go to [lovable.dev](https://lovable.dev)
2. Click "New Project"
3. Select "Import from GitHub"
4. Connect to `breverdbidder/spd-site-plan-dev`
5. Deploy

### Option 2: Code Paste

1. Go to Lovable
2. Create new React project
3. Paste contents of `SPD_AI_App.jsx` into App.jsx
4. Deploy

## Environment Variables

```env
# Required for map functionality
VITE_MAPBOX_TOKEN=your_mapbox_token

# Optional - BidDeed.AI integration
VITE_SUPABASE_URL=your_supabase_url
VITE_SUPABASE_KEY=your_supabase_key
```

## Brevard County Zoning Codes

| Code | Type | Max Density | Max Height |
|------|------|-------------|------------|
| R-1 | Single Family | 4 units/ac | 35 ft |
| R-2 | Medium Density | 10 units/ac | 45 ft |
| R-3 | High Density | 20 units/ac | 65 ft |
| C-1 | Neighborhood Commercial | 0.5 FAR | 35 ft |
| C-2 | General Commercial | 1.0 FAR | 50 ft |
| I-1 | Light Industrial | 0.6 FAR | 45 ft |
| PUD | Planned Unit Development | Varies | Varies |

## API Endpoints (Future)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/zoning` | GET | Lookup zoning by parcel |
| `/api/feasibility` | POST | Generate feasibility analysis |
| `/api/proforma` | POST | Calculate pro forma |
| `/api/export` | POST | Generate PDF/Excel report |

## Roadmap

### Phase 1 (Current)
- [x] Core feasibility engine
- [x] Multi-family typology
- [x] Industrial typology
- [x] Single-family typology
- [x] Basic pro forma

### Phase 2 (Q1 2026)
- [ ] Mapbox GL integration
- [ ] Polygon drawing tools
- [ ] Zoning API integration
- [ ] BCPAO parcel lookup

### Phase 3 (Q2 2026)
- [ ] 3D visualization
- [ ] PDF export
- [ ] Team collaboration
- [ ] Version history

### Phase 4 (Q3 2026)
- [ ] Multi-county expansion
- [ ] AutoCAD export
- [ ] Revit integration
- [ ] ML optimization

## Legal

**© 2026 Everest Capital USA / BidDeed.AI**

This software is proprietary and confidential. Unauthorized copying, distribution, or use is strictly prohibited.

SPD.AI is an **original work** created by Ariel Shapira and Claude AI. It is not a copy, clone, or derivative of any third-party product.

## Contact

- **Developer:** Ariel Shapira
- **Company:** Everest Capital USA
- **Platform:** BidDeed.AI
- **Location:** Brevard County, Florida

---

*Built with ❤️ by BidDeed.AI*
