/**
 * SPD Pre-Application Analysis Document Template
 * Property360 Real Estate | Site Plan Development Pipeline
 * 
 * Generates comprehensive property analysis document for pre-app meetings
 */

const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, 
        AlignmentType, LevelFormat, BorderStyle, WidthType, ShadingType,
        HeadingLevel, Header, Footer, PageNumber, PageBreak } = require('docx');
const fs = require('fs');

// Property360 Brand Colors
const COLORS = {
  PRIMARY: "1B4F72",
  SECONDARY: "2E86AB",
  SUCCESS: "27AE60",
  WARNING: "E67E22",
  DANGER: "C0392B",
  NEUTRAL: "566573",
  LIGHT: "EBF5FB",
  YELLOW_BG: "FEF9E7",
  RED_BG: "FADBD8",
  GREEN_BG: "D5F5E3"
};

// Border Styles
const tableBorder = { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" };
const cellBorders = { top: tableBorder, bottom: tableBorder, left: tableBorder, right: tableBorder };
const thickBorder = { style: BorderStyle.SINGLE, size: 12, color: COLORS.PRIMARY };
const thickBorders = { top: thickBorder, bottom: thickBorder, left: thickBorder, right: thickBorder };
const warningBorder = { style: BorderStyle.SINGLE, size: 8, color: COLORS.DANGER };
const warningBorders = { top: warningBorder, bottom: warningBorder, left: warningBorder, right: warningBorder };

/**
 * Generate Pre-Application Analysis Document
 * @param {Object} project - Project data object
 * @param {string} outputPath - Output file path
 */
function generatePreAppAnalysis(project, outputPath) {
  const doc = new Document({
    styles: {
      default: { document: { run: { font: "Arial", size: 22 } } },
      paragraphStyles: [
        { id: "Title", name: "Title", basedOn: "Normal",
          run: { size: 48, bold: true, color: COLORS.PRIMARY, font: "Arial" },
          paragraph: { spacing: { before: 0, after: 200 }, alignment: AlignmentType.CENTER } },
        { id: "Heading1", name: "Heading 1", basedOn: "Normal", quickFormat: true,
          run: { size: 28, bold: true, color: COLORS.PRIMARY, font: "Arial" },
          paragraph: { spacing: { before: 300, after: 150 }, outlineLevel: 0 } },
        { id: "Heading2", name: "Heading 2", basedOn: "Normal", quickFormat: true,
          run: { size: 24, bold: true, color: COLORS.SECONDARY, font: "Arial" },
          paragraph: { spacing: { before: 200, after: 100 }, outlineLevel: 1 } }
      ]
    },
    numbering: {
      config: [
        { reference: "bullet-list",
          levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
            style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
        { reference: "numbered-list",
          levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
            style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
        { reference: "questions-list",
          levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
            style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] }
      ]
    },
    sections: [{
      properties: { page: { margin: { top: 1080, right: 1080, bottom: 1080, left: 1080 } } },
      headers: {
        default: new Header({ children: [new Paragraph({ 
          alignment: AlignmentType.RIGHT,
          children: [new TextRun({ text: `Property360 Real Estate | Pre-Application Analysis | ${project.projectId}`, size: 18, color: COLORS.NEUTRAL })]
        })] })
      },
      footers: {
        default: new Footer({ children: [new Paragraph({ 
          alignment: AlignmentType.CENTER,
          children: [new TextRun({ text: "Page ", size: 18 }), new TextRun({ children: [PageNumber.CURRENT], size: 18 }), new TextRun({ text: " | Confidential", size: 18, color: COLORS.NEUTRAL })]
        })] })
      },
      children: buildPreAppContent(project)
    }]
  });

  Packer.toBuffer(doc).then(buffer => {
    fs.writeFileSync(outputPath, buffer);
    console.log(`✅ Pre-App Analysis created: ${outputPath}`);
  });
}

function buildPreAppContent(p) {
  const content = [];
  
  // Title
  content.push(new Paragraph({ heading: HeadingLevel.TITLE, children: [new TextRun(`${p.address.split(',')[0].toUpperCase()} PRE-APP ANALYSIS`)] }));
  content.push(new Paragraph({ 
    alignment: AlignmentType.CENTER, spacing: { after: 200 },
    children: [new TextRun({ text: `${p.address} | Project ${p.projectId}`, size: 24, color: COLORS.SECONDARY })]
  }));

  // Critical Constraint Box (if constraints exist)
  if (p.constraints && p.constraints.length > 0) {
    const primaryConstraint = p.constraints[0];
    content.push(new Table({
      columnWidths: [9360],
      rows: [new TableRow({
        children: [new TableCell({
          borders: warningBorders,
          shading: { fill: COLORS.RED_BG, type: ShadingType.CLEAR },
          children: [
            new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 150, after: 100 }, children: [new TextRun({ text: "⚠️ CRITICAL CONSTRAINT DISCOVERED", size: 26, bold: true, color: COLORS.DANGER })] }),
            new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 150 }, children: [new TextRun({ text: primaryConstraint.description || `${primaryConstraint.type} affecting development`, size: 22 })] }),
            primaryConstraint.contact ? new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 100 }, children: [new TextRun({ text: `(Per ${primaryConstraint.contact}, ${primaryConstraint.authority})`, size: 18, italics: true, color: COLORS.NEUTRAL })] }) : null
          ].filter(Boolean)
        })]
      })]
    }));
  }

  // Section 1: Property Overview
  content.push(new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("1. PROPERTY OVERVIEW")] }));
  content.push(new Table({
    columnWidths: [3120, 6240],
    rows: [
      createTableRow("Address", p.address, true),
      createTableRow("Parcel ID", p.parcelId, true),
      p.legalDescription ? createTableRow("Legal Description", p.legalDescription, true) : null,
      createTableRow("Total Parcel Size", `${p.totalSqFt?.toLocaleString() || 'TBD'} SF (${p.totalAcres?.toFixed(3) || 'TBD'} acres)`, true),
      p.surveyDate ? createTableRow("Survey Date", `${p.surveyDate}${p.surveyor ? ` (${p.surveyor})` : ''}`, true) : null,
      p.constraints?.length > 0 ? createTableRow("CONSTRAINT", p.constraints[0].description || p.constraints[0].type, true, true) : null
    ].filter(Boolean)
  }));

  // Section 2: Constraint Analysis (if applicable)
  if (p.constraints && p.constraints.length > 0) {
    content.push(new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("2. CONSTRAINT ANALYSIS")] }));
    
    p.constraints.forEach((constraint, idx) => {
      content.push(new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun(`2.${idx + 1} ${constraint.type.replace(/_/g, ' ').toUpperCase()}`)] }));
      
      if (constraint.authority) {
        content.push(new Paragraph({ numbering: { reference: "bullet-list", level: 0 }, children: [new TextRun({ text: "Authority: ", bold: true }), new TextRun(constraint.authority)] }));
      }
      if (constraint.timeline) {
        content.push(new Paragraph({ numbering: { reference: "bullet-list", level: 0 }, children: [new TextRun({ text: "Timeline: ", bold: true }), new TextRun(constraint.timeline)] }));
      }
      if (constraint.affectedArea) {
        content.push(new Paragraph({ numbering: { reference: "bullet-list", level: 0 }, children: [new TextRun({ text: "Affected Area: ", bold: true }), new TextRun(`~${constraint.affectedArea.toLocaleString()} SF`)] }));
      }
      if (constraint.vacationProcess) {
        content.push(new Paragraph({ numbering: { reference: "bullet-list", level: 0 }, children: [new TextRun({ text: "Resolution Process: ", bold: true }), new TextRun(constraint.vacationProcess)] }));
      }
    });
  }

  // Section 3: Zoning Analysis
  content.push(new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("3. ZONING ANALYSIS")] }));
  content.push(new Table({
    columnWidths: [3120, 3120, 3120],
    rows: [
      new TableRow({ children: [
        new TableCell({ borders: cellBorders, width: { size: 3120, type: WidthType.DXA }, shading: { fill: COLORS.LIGHT, type: ShadingType.CLEAR }, children: [new Paragraph({ children: [new TextRun({ text: "Category", bold: true })] })] }),
        new TableCell({ borders: cellBorders, width: { size: 3120, type: WidthType.DXA }, shading: { fill: COLORS.LIGHT, type: ShadingType.CLEAR }, children: [new Paragraph({ children: [new TextRun({ text: "Current", bold: true })] })] }),
        new TableCell({ borders: cellBorders, width: { size: 3120, type: WidthType.DXA }, shading: { fill: COLORS.LIGHT, type: ShadingType.CLEAR }, children: [new Paragraph({ children: [new TextRun({ text: "Requested", bold: true })] })] })
      ]}),
      new TableRow({ children: [
        new TableCell({ borders: cellBorders, width: { size: 3120, type: WidthType.DXA }, children: [new Paragraph({ children: [new TextRun("Zoning")] })] }),
        new TableCell({ borders: cellBorders, width: { size: 3120, type: WidthType.DXA }, children: [new Paragraph({ children: [new TextRun(p.currentZoning || "TBD")] })] }),
        new TableCell({ borders: cellBorders, width: { size: 3120, type: WidthType.DXA }, shading: { fill: COLORS.YELLOW_BG, type: ShadingType.CLEAR }, children: [new Paragraph({ children: [new TextRun({ text: p.requestedZoning || "TBD", bold: true })] })] })
      ]}),
      new TableRow({ children: [
        new TableCell({ borders: cellBorders, width: { size: 3120, type: WidthType.DXA }, children: [new Paragraph({ children: [new TextRun("Proposed Units")] })] }),
        new TableCell({ borders: cellBorders, width: { size: 3120, type: WidthType.DXA }, children: [new Paragraph({ children: [new TextRun("N/A")] })] }),
        new TableCell({ borders: cellBorders, width: { size: 3120, type: WidthType.DXA }, shading: { fill: COLORS.YELLOW_BG, type: ShadingType.CLEAR }, children: [new Paragraph({ children: [new TextRun({ text: String(p.proposedUnits || "TBD"), bold: true })] })] })
      ]})
    ]
  }));

  // Section 4: Recommended Strategy
  content.push(new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("4. RECOMMENDED STRATEGY")] }));
  content.push(new Table({
    columnWidths: [9360],
    rows: [new TableRow({
      children: [new TableCell({
        borders: thickBorders,
        shading: { fill: COLORS.GREEN_BG, type: ShadingType.CLEAR },
        children: [
          new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 150, after: 150 }, children: [new TextRun({ text: p.recommendedStrategy || "PHASED DEVELOPMENT WITH FUTURE RIGHTS AGREEMENT", size: 24, bold: true, color: COLORS.SUCCESS })] })
        ]
      })]
    })]
  }));

  // Section 5: Questions for Meeting
  content.push(new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("5. QUESTIONS FOR PRE-APPLICATION MEETING")] }));
  
  const defaultQuestions = [
    "What is the exact acreage inside vs. outside any easement constraints?",
    "What uses ARE permitted within constrained areas? (Parking? Stormwater? Landscaping?)",
    "What is the maximum unit count achievable on the non-encumbered portion?",
    "What is the process for rezoning? Timeline and costs?",
    "Would the city support a Development Agreement guaranteeing future expansion rights?",
    "What setbacks apply from constraint boundaries vs. property boundaries?",
    "What studies are required before formal application?",
    "Can we get pre-approval for a phased site plan?"
  ];
  
  const questions = p.questions || defaultQuestions;
  questions.forEach(q => {
    content.push(new Paragraph({ numbering: { reference: "questions-list", level: 0 }, children: [new TextRun(q)] }));
  });

  // Footer
  content.push(new Paragraph({ spacing: { before: 400 }, children: [] }));
  content.push(new Paragraph({
    alignment: AlignmentType.CENTER,
    shading: { fill: COLORS.GREEN_BG, type: ShadingType.CLEAR },
    spacing: { before: 100, after: 100 },
    children: [
      new TextRun({ text: "Prepared by Property360 Real Estate  |  ", size: 20, color: COLORS.NEUTRAL }),
      new TextRun({ text: "Mariam Shapira, Developer & GC", size: 20, bold: true, color: COLORS.SUCCESS }),
      new TextRun({ text: `  |  ${new Date().toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}`, size: 20, color: COLORS.NEUTRAL })
    ]
  }));

  return content;
}

function createTableRow(label, value, isLabeled = false, isWarning = false) {
  const bgColor = isWarning ? COLORS.YELLOW_BG : COLORS.LIGHT;
  const textColor = isWarning ? COLORS.WARNING : undefined;
  
  return new TableRow({ children: [
    new TableCell({ borders: cellBorders, width: { size: 3120, type: WidthType.DXA }, shading: { fill: bgColor, type: ShadingType.CLEAR }, children: [new Paragraph({ children: [new TextRun({ text: label, bold: true, color: textColor })] })] }),
    new TableCell({ borders: cellBorders, width: { size: 6240, type: WidthType.DXA }, shading: isWarning ? { fill: bgColor, type: ShadingType.CLEAR } : undefined, children: [new Paragraph({ children: [new TextRun({ text: value, bold: isWarning })] })] })
  ]});
}

// Export for use in other modules
module.exports = { generatePreAppAnalysis, COLORS };

// CLI execution
if (require.main === module) {
  const sampleProject = {
    projectId: "SPD-2025-001",
    address: "2165 Sandy Pines Dr NE, Palm Bay, FL",
    parcelId: "2835546",
    legalDescription: "S½ of NE¼, Section 17, T28S, R37E, Brevard County",
    totalSqFt: 46394,
    totalAcres: 1.065,
    surveyDate: "August 26, 2024",
    surveyor: "Kevin A. Smith, PSM",
    currentZoning: "RS-2",
    requestedZoning: "RM-20",
    proposedUnits: 21,
    constraints: [{
      type: "wellhead_easement",
      description: "200-foot wellhead protection easement CANNOT be vacated for approximately 10 years",
      radius: 200,
      timeline: "~10 years",
      authority: "Palm Bay Utilities",
      contact: "Tim Roberts",
      affectedArea: 22000,
      canBeVacated: true,
      vacationProcess: "Well abandonment after RO plant completion"
    }],
    recommendedStrategy: "PHASED DEVELOPMENT WITH FUTURE RIGHTS AGREEMENT"
  };
  
  generatePreAppAnalysis(sampleProject, "/mnt/user-data/outputs/SPD_PreApp_Template_Output.docx");
}
