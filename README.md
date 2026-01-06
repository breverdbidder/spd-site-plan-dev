# SPD.AI V2 - Chat-Driven Site Planning Intelligence

> AI-powered site planning with conversational NLP interface

![Version](https://img.shields.io/badge/Version-2.0.0-blue)
![Interface](https://img.shields.io/badge/Interface-Chat%20%2B%20Preview-green)
![Powered by](https://img.shields.io/badge/Powered%20by-BidDeed.AI-purple)

## 🚀 What's New in V2

### Split-Screen Chat Interface

SPD.AI V2 features a **Lovable/Claude/Manus-style** split-screen design:

| Left Panel | Right Panel |
|------------|-------------|
| 💬 **Chat Interface** | 📊 **Real-time Preview** |
| Natural language input | Site visualization |
| AI-powered responses | Metrics dashboard |
| Markdown rendering | Pro forma display |

### NLP Capabilities

Talk to SPD.AI naturally:

```
"I have a 5 acre site zoned R-2"
"Build an apartment complex"
"Target 120 units"
"Show me the pro forma"
"Change parking to 2.0 per unit"
```

### Intent Recognition

| Intent | Example Phrases |
|--------|-----------------|
| **Analyze Site** | "5 acre site", "10 acre parcel" |
| **Set Zoning** | "zoned R-2", "C-1 zoning" |
| **Choose Typology** | "build apartments", "industrial warehouse" |
| **Set Units** | "150 units", "target 200 units" |
| **Parking Ratio** | "1.5 parking ratio", "2 spaces per unit" |
| **Pro Forma** | "show pro forma", "what's the profit" |
| **Export** | "export PDF", "download report" |

## 📐 Development Typologies

### Multi-Family
- Unit mix optimization (Studio/1BR/2BR/3BR)
- Parking ratio calculations
- Density analysis (units/acre)
- FAR calculations
- Gross SF estimates

### Industrial/Warehouse
- Clear height specifications
- Dock door calculations
- Trailer parking allocation
- Car parking requirements
- Building efficiency metrics

### Single-Family
- Lot count optimization
- Lot size calculations
- Infrastructure allocation (roads, open space)
- Density analysis (lots/acre)

## 💰 Pro Forma Analysis

Every feasibility includes:

| Metric | Description |
|--------|-------------|
| **Land Cost** | Based on Brevard County averages |
| **Hard Costs** | $/SF by typology |
| **Soft Costs** | % of hard costs |
| **Total Cost** | Sum of all costs |
| **Annual Revenue** | Rent or sales projections |
| **NOI** | Net Operating Income |
| **Yield on Cost** | NOI / Total Cost |
| **Estimated Value** | Based on cap rate |
| **Profit** | Value - Cost |
| **Margin** | Profit / Cost |

## 🎨 Design System

### Theme (Dark Mode)

```javascript
const THEME = {
  bg: {
    primary: '#0A0A0B',
    secondary: '#111113',
    tertiary: '#18181B',
    elevated: '#1F1F23',
  },
  accent: {
    primary: '#3B82F6',   // Blue
    success: '#10B981',   // Green
    warning: '#F59E0B',   // Orange
    danger: '#EF4444',    // Red
    purple: '#8B5CF6',    // Purple
  },
};
```

### Inspired By (Not Cloned)

| Platform | Borrowed Pattern |
|----------|------------------|
| **Lovable** | Split-screen layout |
| **Claude AI** | Chat bubble design |
| **Manus AI** | Real-time preview |
| **Cursor** | Command palette feel |

**All code is original** - patterns are industry-standard.

## 🏗️ Architecture

```
src/
├── App.jsx               # Main chat application
├── components/
│   ├── ChatPanel.jsx     # Left panel - messages
│   ├── PreviewPanel.jsx  # Right panel - visualization
│   ├── MessageContent.jsx # Markdown renderer
│   └── MetricCard.jsx    # Metric display
├── hooks/
│   ├── useNLP.js         # Intent recognition
│   ├── useFeasibility.js # Calculation engine
│   └── useChat.js        # Chat state management
└── utils/
    ├── intents.js        # NLP patterns
    ├── calculations.js   # Feasibility formulas
    └── theme.js          # Design tokens
```

## 🚀 Deployment

### Deploy to Lovable

1. Go to [lovable.dev](https://lovable.dev)
2. Create new project → Import from GitHub
3. Select `breverdbidder/spd-site-plan-dev`
4. Deploy

### Run Locally

```bash
git clone https://github.com/breverdbidder/spd-site-plan-dev.git
cd spd-site-plan-dev
npm install
npm run dev
```

## 🔧 Configuration

### Environment Variables

```env
# Optional - Mapbox for future map integration
VITE_MAPBOX_TOKEN=your_token

# Optional - BidDeed.AI backend
VITE_SUPABASE_URL=your_url
VITE_SUPABASE_KEY=your_key

# Optional - Anthropic for enhanced NLP
VITE_ANTHROPIC_KEY=your_key
```

## 📊 Brevard County Zoning

| Code | Type | Max Density | Max Height |
|------|------|-------------|------------|
| R-1 | Single Family | 4 units/ac | 35 ft |
| R-2 | Medium Density | 10 units/ac | 45 ft |
| R-3 | High Density | 20 units/ac | 65 ft |
| C-1 | Neighborhood Commercial | 0.5 FAR | 35 ft |
| C-2 | General Commercial | 1.0 FAR | 50 ft |
| I-1 | Light Industrial | 0.6 FAR | 45 ft |
| PUD | Planned Unit Development | Varies | Varies |

## 🔜 Roadmap

### V2.1 (Current Sprint)
- [ ] Mapbox GL JS integration
- [ ] Parcel drawing tools
- [ ] BCPAO API connection

### V2.2
- [ ] 3D visualization (Three.js)
- [ ] Unit mix slider controls
- [ ] Multi-scenario comparison

### V2.3
- [ ] Anthropic API for enhanced NLP
- [ ] Voice input support
- [ ] Team collaboration

### V3.0
- [ ] Multi-county expansion
- [ ] AutoCAD/Revit export
- [ ] Pro forma editor

## 📜 License

**Proprietary** - © 2026 Everest Capital USA / BidDeed.AI

This software is confidential. Unauthorized distribution prohibited.

## 👤 Author

- **Ariel Shapira** - Solo Founder
- **Company:** Everest Capital USA
- **Platform:** BidDeed.AI
- **Location:** Brevard County, FL

---

*Built with ❤️ by BidDeed.AI*
