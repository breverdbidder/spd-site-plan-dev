# SPD Document Generation Skill
## Property360 Real Estate | Site Plan Development Pipeline

---

## Overview

This skill provides standardized templates for generating professional Word documents (.docx) for the Site Plan Development (SPD) pipeline. All documents use Property360 branding and are designed for land use attorneys, developers, and planning staff interactions.

## Document Types

| Template | Use Case | Typical Length |
|----------|----------|----------------|
| `pre_app_analysis.js` | Comprehensive property analysis before pre-app meeting | 3-4 pages |
| `meeting_agenda_attorney.js` | Attorney strategy briefing with offensive legal posture | 5-6 pages |
| `executive_summary.js` | One-page project overview for stakeholders | 1 page |
| `dev_agreement_term_sheet.js` | Development Agreement negotiation terms | 2 pages |

## Quick Start

```javascript
// Import the template generator
const { generatePreAppAnalysis } = require('./templates/pre_app_analysis.js');

// Provide project data
const projectData = {
  address: "2165 Sandy Pines Dr NE, Palm Bay, FL",
  parcelId: "2835546",
  projectId: "SPD-2025-001",
  totalAcres: 1.065,
  currentZoning: "RS-2",
  requestedZoning: "RM-20",
  proposedUnits: 21,
  constraints: [{
    type: "wellhead_easement",
    radius: 200,
    timeline: "10 years",
    authority: "Palm Bay Utilities",
    contact: "Tim Roberts"
  }]
};

// Generate document
generatePreAppAnalysis(projectData, "/mnt/user-data/outputs/PreApp_Analysis.docx");
```

## Brand Colors

```javascript
const COLORS = {
  PRIMARY: "1B4F72",    // Deep Blue - Headers, titles
  SECONDARY: "2E86AB",  // Teal - Subheaders
  SUCCESS: "27AE60",    // Green - Positive/recommended
  WARNING: "E67E22",    // Orange - Caution items
  DANGER: "C0392B",     // Red - Critical constraints
  NEUTRAL: "566573",    // Gray - Secondary text
  LIGHT: "EBF5FB",      // Light Blue - Table backgrounds
  YELLOW_BG: "FEF9E7",  // Yellow - Action items
  RED_BG: "FADBD8",     // Light Red - Critical alerts
  GREEN_BG: "D5F5E3",   // Light Green - Recommendations
  PURPLE: "6C3483"      // Purple - Attorney/legal sections
};
```

## Document Structure Patterns

### Critical Alert Box
```javascript
new Table({
  columnWidths: [9360],
  rows: [new TableRow({
    children: [new TableCell({
      borders: warningBorders,
      shading: { fill: COLORS.RED_BG, type: ShadingType.CLEAR },
      children: [
        new Paragraph({ 
          alignment: AlignmentType.CENTER,
          children: [new TextRun({ text: "⚠️ CRITICAL CONSTRAINT", bold: true, color: COLORS.DANGER })]
        })
      ]
    })]
  })]
})
```

### Recommendation Box
```javascript
new Table({
  columnWidths: [9360],
  rows: [new TableRow({
    children: [new TableCell({
      borders: thickBorders,
      shading: { fill: COLORS.GREEN_BG, type: ShadingType.CLEAR },
      children: [
        new Paragraph({ 
          alignment: AlignmentType.CENTER,
          children: [new TextRun({ text: "RECOMMENDED: [Strategy Name]", bold: true, color: COLORS.SUCCESS })]
        })
      ]
    })]
  })]
})
```

### Attorney Strategy Box
```javascript
new Table({
  columnWidths: [9360],
  rows: [new TableRow({
    children: [new TableCell({
      borders: purpleBorders,
      shading: { fill: "F5EEF8", type: ShadingType.CLEAR },
      children: [
        new Paragraph({ 
          alignment: AlignmentType.CENTER,
          children: [new TextRun({ text: "⚖️ LEGAL STRATEGY", bold: true, color: COLORS.PURPLE })]
        })
      ]
    })]
  })]
})
```

## Required Data Schema

### Project Data Object
```typescript
interface SPDProject {
  // Basic Info
  projectId: string;          // "SPD-2025-001"
  address: string;            // Full street address
  city: string;               // "Palm Bay"
  state: string;              // "FL"
  parcelId: string;           // County parcel ID
  legalDescription?: string;  // Section/Township/Range
  
  // Parcel Details
  totalSqFt: number;          // Total parcel square footage
  totalAcres: number;         // Calculated from sqft
  surveyDate?: string;        // Date of most recent survey
  surveyor?: string;          // PSM name
  
  // Zoning
  currentZoning: string;      // "RS-2", "RM-10", etc.
  requestedZoning: string;    // Target zoning
  futurelandUse?: string;     // Comp plan designation
  
  // Development
  proposedUnits: number;      // Unit count
  proposedUse: string;        // "multifamily", "commercial", etc.
  buildingType?: string;      // "apartment", "townhome", etc.
  
  // Constraints
  constraints: Constraint[];
  
  // Contacts
  developer: Contact;
  attorney?: Contact;
  cityContacts: CityContact[];
}

interface Constraint {
  type: "wellhead_easement" | "wetland" | "flood_zone" | "utility_easement" | "access" | "other";
  description: string;
  affectedArea?: number;      // Square feet affected
  timeline?: string;          // Resolution timeline
  authority?: string;         // Regulating body
  contact?: string;           // Point of contact
  canBeVacated: boolean;
  vacationProcess?: string;
}

interface Contact {
  name: string;
  title: string;
  company?: string;
  email?: string;
  phone?: string;
}

interface CityContact {
  department: string;
  name?: string;
  title?: string;
  email?: string;
  phone?: string;
  focusArea: string;
}
```

## LangGraph Integration

### Stage 3: Pre-Application Analysis
```python
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph

def generate_preapp_docs(state: SPDState) -> SPDState:
    """Generate pre-application documents for Stage 3."""
    
    project_data = state["project_data"]
    
    # Generate Pre-App Analysis
    analysis_path = f"/tmp/spd/{project_data['projectId']}/PreApp_Analysis.docx"
    run_template("pre_app_analysis", project_data, analysis_path)
    
    # Generate Attorney Meeting Agenda
    agenda_path = f"/tmp/spd/{project_data['projectId']}/Meeting_Agenda_Attorney.docx"
    run_template("meeting_agenda_attorney", project_data, agenda_path)
    
    # Upload to GitHub
    upload_to_github(
        repo="breverdbidder/spd-site-plan-dev",
        path=f"projects/{project_data['projectId']}/documents/",
        files=[analysis_path, agenda_path]
    )
    
    # Log to Supabase
    insert_insight(
        category="spd_documents",
        content=f"Generated pre-app documents for {project_data['projectId']}",
        metadata={
            "project_id": project_data["projectId"],
            "documents": ["PreApp_Analysis.docx", "Meeting_Agenda_Attorney.docx"],
            "stage": 3
        }
    )
    
    return {**state, "preapp_docs_generated": True}
```

## File Naming Convention

```
{ProjectID}_{DocumentType}_{Date}.docx

Examples:
- SPD-2025-001_PreApp_Analysis_Dec16.docx
- SPD-2025-001_Meeting_Agenda_Attorney_Dec16.docx
- SPD-2025-001_Executive_Summary.docx
- SPD-2025-001_DevAgreement_TermSheet.docx
```

## Critical Rules

### DO
1. Always use Arial font for universal compatibility
2. Use proper heading hierarchy (Title > Heading1 > Heading2)
3. Apply consistent spacing (200 twips before sections)
4. Use ShadingType.CLEAR for all cell shading
5. Set column widths at BOTH table level AND cell level
6. Use separate Paragraphs for each line (never \n)
7. Output final files to /mnt/user-data/outputs/
8. Include Property360 branding in footer

### DON'T
1. Don't use PageBreak standalone (wrap in Paragraph)
2. Don't use unicode bullets (use LevelFormat.BULLET)
3. Don't use text property on Paragraph (use children with TextRun)
4. Don't forget borders on individual TableCells
5. Don't exceed 9360 DXA total width for letter size
6. Don't mix heading styles with custom styles

## Deployment

### GitHub Workflow Integration
```yaml
# .github/workflows/generate_spd_docs.yml
name: Generate SPD Documents

on:
  workflow_dispatch:
    inputs:
      project_id:
        description: 'SPD Project ID'
        required: true
      document_type:
        description: 'Document type to generate'
        required: true
        type: choice
        options:
          - pre_app_analysis
          - meeting_agenda_attorney
          - executive_summary
          - all

jobs:
  generate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - run: npm install docx
      - run: node skills/spd_docx/templates/${{ inputs.document_type }}.js
      - uses: actions/upload-artifact@v4
        with:
          name: spd-documents
          path: outputs/*.docx
```

---

**Created by Everest Capital USA | SPD Pipeline v1.0**
**Property360 Real Estate | Mariam Shapira, Developer & GC**
