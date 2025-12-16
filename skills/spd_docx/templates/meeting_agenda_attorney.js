/**
 * SPD Attorney Strategy Meeting Agenda Template
 * Property360 Real Estate | Site Plan Development Pipeline
 * 
 * Generates comprehensive meeting agenda with offensive legal strategy
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
  GREEN_BG: "D5F5E3",
  PURPLE: "6C3483"
};

// Border Styles
const tableBorder = { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" };
const cellBorders = { top: tableBorder, bottom: tableBorder, left: tableBorder, right: tableBorder };
const thickBorder = { style: BorderStyle.SINGLE, size: 12, color: COLORS.PRIMARY };
const thickBorders = { top: thickBorder, bottom: thickBorder, left: thickBorder, right: thickBorder };
const purpleBorder = { style: BorderStyle.SINGLE, size: 8, color: COLORS.PURPLE };
const purpleBorders = { top: purpleBorder, bottom: purpleBorder, left: purpleBorder, right: purpleBorder };

/**
 * Generate Attorney Strategy Meeting Agenda
 * @param {Object} project - Project data object
 * @param {string} outputPath - Output file path
 */
function generateMeetingAgendaAttorney(project, outputPath) {
  const doc = new Document({
    styles: {
      default: { document: { run: { font: "Arial", size: 22 } } },
      paragraphStyles: [
        { id: "Title", name: "Title", basedOn: "Normal",
          run: { size: 44, bold: true, color: COLORS.PRIMARY, font: "Arial" },
          paragraph: { spacing: { before: 0, after: 200 }, alignment: AlignmentType.CENTER } },
        { id: "Heading1", name: "Heading 1", basedOn: "Normal", quickFormat: true,
          run: { size: 28, bold: true, color: COLORS.PRIMARY, font: "Arial" },
          paragraph: { spacing: { before: 300, after: 150 }, outlineLevel: 0 } },
        { id: "Heading2", name: "Heading 2", basedOn: "Normal", quickFormat: true,
          run: { size: 24, bold: true, color: COLORS.SECONDARY, font: "Arial" },
          paragraph: { spacing: { before: 200, after: 100 }, outlineLevel: 1 } },
        { id: "Heading3", name: "Heading 3", basedOn: "Normal", quickFormat: true,
          run: { size: 22, bold: true, color: COLORS.PURPLE, font: "Arial" },
          paragraph: { spacing: { before: 150, after: 80 }, outlineLevel: 2 } }
      ]
    },
    numbering: {
      config: [
        { reference: "bullet-list", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
        { reference: "numbered-list", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
        { reference: "strategy-list", levels: [{ level: 0, format: LevelFormat.UPPER_LETTER, text: "%1.", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
        { reference: "questions-planning", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
        { reference: "questions-utilities", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
        { reference: "questions-legal", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] }
      ]
    },
    sections: [{
      properties: { page: { margin: { top: 1080, right: 1080, bottom: 1080, left: 1080 } } },
      headers: {
        default: new Header({ children: [new Paragraph({ 
          alignment: AlignmentType.RIGHT,
          children: [new TextRun({ text: `CONFIDENTIAL - ATTORNEY WORK PRODUCT | ${project.projectId}`, size: 18, color: COLORS.DANGER, bold: true })]
        })] })
      },
      footers: {
        default: new Footer({ children: [new Paragraph({ 
          alignment: AlignmentType.CENTER,
          children: [new TextRun({ text: "Page ", size: 18 }), new TextRun({ children: [PageNumber.CURRENT], size: 18 }), new TextRun({ text: " | Property360 Real Estate | Attorney Strategy Briefing", size: 18, color: COLORS.NEUTRAL })]
        })] })
      },
      children: buildAgendaContent(project)
    }]
  });

  Packer.toBuffer(doc).then(buffer => {
    fs.writeFileSync(outputPath, buffer);
    console.log(`✅ Attorney Meeting Agenda created: ${outputPath}`);
  });
}

function buildAgendaContent(p) {
  const content = [];
  const meetingDate = p.meetingDate || new Date().toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' });
  
  // Title Section
  content.push(new Paragraph({ heading: HeadingLevel.TITLE, children: [new TextRun("PRE-APPLICATION MEETING AGENDA")] }));
  content.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 100 }, children: [new TextRun({ text: p.address, size: 26, bold: true, color: COLORS.SECONDARY })] }));
  content.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 300 }, children: [new TextRun({ text: `${meetingDate} | ${p.city || 'City'} Planning & Zoning Department`, size: 22, color: COLORS.NEUTRAL })] }));

  // Attorney Strategy Box
  content.push(new Table({
    columnWidths: [9360],
    rows: [new TableRow({
      children: [new TableCell({
        borders: purpleBorders,
        shading: { fill: "F5EEF8", type: ShadingType.CLEAR },
        children: [
          new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 150, after: 100 }, children: [new TextRun({ text: "⚖️ LAND USE ATTORNEY STRATEGY BRIEFING", size: 24, bold: true, color: COLORS.PURPLE })] }),
          new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 150 }, children: [new TextRun({ text: "Offensive Posture: Secure Maximum Entitlements While Protecting Future Rights", size: 20, italics: true })] })
        ]
      })]
    })]
  }));

  // Section 1: Meeting Participants
  content.push(new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("1. MEETING PARTICIPANTS")] }));
  
  content.push(new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("1.1 Property360 Team (Applicant)")] }));
  content.push(createParticipantTable([
    { name: p.developer?.name || "Mariam Shapira", role: "Developer & Licensed GC", focus: "Project Vision, Construction" },
    { name: p.attorney?.name || "[Land Use Attorney]", role: "Legal Counsel", focus: "Entitlements, Dev Agreement" }
  ]));

  content.push(new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("1.2 City Representatives (Expected)")] }));
  const cityContacts = p.cityContacts || [
    { department: "Planning & Zoning", name: "[Planner Name TBD]", focus: "Rezoning, Site Plan, Density" },
    { department: "Utilities Department", name: p.constraints?.[0]?.contact || "[Utilities Rep]", focus: "Wellhead, Easement, Timeline" },
    { department: "City Attorney's Office", name: "[If present]", focus: "Development Agreement" },
    { department: "Engineering/Public Works", name: "[If present]", focus: "Stormwater, Access, ROW" }
  ];
  content.push(createCityContactTable(cityContacts));

  // Section 2: Meeting Agenda Timeline
  content.push(new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("2. MEETING AGENDA")] }));
  content.push(createAgendaTable());

  // Page Break
  content.push(new Paragraph({ children: [new PageBreak()] }));

  // Section 3: Offensive Legal Strategy
  content.push(new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("3. OFFENSIVE LEGAL STRATEGY")] }));
  
  content.push(new Table({
    columnWidths: [9360],
    rows: [new TableRow({
      children: [new TableCell({
        borders: purpleBorders,
        shading: { fill: "F5EEF8", type: ShadingType.CLEAR },
        children: [
          new Paragraph({ spacing: { before: 150, after: 100 }, children: [new TextRun({ text: "CORE OBJECTIVE: ", bold: true, color: COLORS.PURPLE, size: 24 }), new TextRun({ text: `Lock in ${p.requestedZoning || 'target'} zoning and vested development rights NOW, not later`, size: 24 })] }),
          new Paragraph({ spacing: { after: 150 }, children: [new TextRun({ text: "The city cannot have it both ways - blocking development with constraints while denying entitlements that vest upon constraint removal.", size: 20, italics: true })] })
        ]
      })]
    })]
  }));

  content.push(new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("3.1 Legal Leverage Points")] }));
  
  const leveragePoints = [
    { title: "Regulatory Taking Argument", description: "If constraints render property undevelopable and city denies reasonable use, this approaches a regulatory taking under Lucas v. South Carolina Coastal Council. Use as leverage, not litigation threat." },
    { title: "Vested Rights Doctrine (Florida Statute 163.3167)", description: "Florida law provides strong vested rights protections. A Development Agreement under F.S. 163.3220-163.3243 creates binding obligations that survive zoning changes for up to 30 years." },
    { title: "City's Own Infrastructure Timeline", description: "Any documented city timeline (CIP, emails) is evidence of constraint AND solution. Request Capital Improvement Plan - it's public record." },
    { title: "Housing Element Compliance", description: "City's Comprehensive Plan includes housing goals. Multifamily development supports these goals. Frame project as helping city meet state-mandated housing requirements." },
    { title: "Equitable Estoppel", description: "If city provides favorable preliminary feedback, document everything. Written confirmations create estoppel arguments if city later reverses position." }
  ];
  
  leveragePoints.forEach((point, idx) => {
    content.push(new Paragraph({ numbering: { reference: "strategy-list", level: 0 }, spacing: { before: 150 }, children: [new TextRun({ text: point.title, bold: true })] }));
    content.push(new Paragraph({ indent: { left: 720 }, children: [new TextRun(point.description)] }));
  });

  content.push(new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("3.2 Development Agreement Strategy")] }));
  content.push(new Paragraph({ spacing: { after: 100 }, children: [new TextRun({ text: "Propose a Development Agreement with these key terms:", bold: true })] }));
  content.push(createDevAgreementTable(p));

  // Page Break
  content.push(new Paragraph({ children: [new PageBreak()] }));

  // Section 4: Comprehensive Questions
  content.push(new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("4. COMPREHENSIVE QUESTIONS BY DEPARTMENT")] }));

  // Planning Questions
  content.push(new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("4.1 Planning & Zoning Department")] }));
  const planningQuestions = [
    `What is the current zoning designation for Parcel ${p.parcelId}?`,
    `What is the process for rezoning to ${p.requestedZoning}? Timeline? Costs? Required hearings?`,
    "What is the maximum unit count achievable on the non-encumbered portion?",
    "Is a Comprehensive Plan Future Land Use Map amendment required?",
    "What setbacks apply from constraint boundaries vs. property boundaries?",
    "Can parking be located within constrained zones if properly designed?",
    "Can we get pre-approval for a phased site plan showing future development areas?",
    "What studies are required before formal application? Traffic? Environmental?"
  ];
  planningQuestions.forEach(q => {
    content.push(new Paragraph({ numbering: { reference: "questions-planning", level: 0 }, children: [new TextRun(q)] }));
  });

  // Utilities Questions
  content.push(new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("4.2 Utilities Department")] }));
  const utilitiesQuestions = [
    "What is the EXACT acreage and boundaries of any utility easements on this parcel?",
    "Can we obtain a survey-quality legal description of easement boundaries?",
    "What activities ARE permitted within protection zones? (Parking, stormwater, landscaping?)",
    "Is the constraint timeline documented in the Capital Improvement Plan?",
    "What specific milestones must occur before constraints can be removed?",
    "Is there sufficient water and sewer capacity for the proposed units?",
    "Can utility capacity be reserved under a Development Agreement?"
  ];
  utilitiesQuestions.forEach(q => {
    content.push(new Paragraph({ numbering: { reference: "questions-utilities", level: 0 }, children: [new TextRun(q)] }));
  });

  // Legal Questions
  content.push(new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("4.3 City Attorney / Development Agreement")] }));
  const legalQuestions = [
    "Does the city have a Development Agreement ordinance per F.S. 163.3220-163.3243?",
    "Would the city consider a Development Agreement for phased development?",
    "Can impact fees be locked at current rates for future phases?",
    "What is the approval process for Development Agreements? City Council vote required?",
    "Can the agreement include automatic permit issuance triggers?",
    "What is the maximum term available for a Development Agreement?",
    "Are there density transfer mechanisms that could be applied?"
  ];
  legalQuestions.forEach(q => {
    content.push(new Paragraph({ numbering: { reference: "questions-legal", level: 0 }, children: [new TextRun(q)] }));
  });

  // Section 5: Negotiation Tactics
  content.push(new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("5. NEGOTIATION TACTICS")] }));
  
  content.push(new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("5.1 What We Offer the City")] }));
  content.push(new Paragraph({ numbering: { reference: "bullet-list", level: 0 }, children: [new TextRun({ text: "Quality housing development ", bold: true }), new TextRun("supporting growth and housing element goals")] }));
  content.push(new Paragraph({ numbering: { reference: "bullet-list", level: 0 }, children: [new TextRun({ text: "Tax revenue ", bold: true }), new TextRun("- more property tax than vacant land")] }));
  content.push(new Paragraph({ numbering: { reference: "bullet-list", level: 0 }, children: [new TextRun({ text: "Professional developer ", bold: true }), new TextRun("- Licensed GC with track record")] }));
  content.push(new Paragraph({ numbering: { reference: "bullet-list", level: 0 }, children: [new TextRun({ text: "Long-term commitment ", bold: true }), new TextRun("- Development agreement shows we're serious")] }));

  content.push(new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("5.2 Red Flags to Watch For")] }));
  content.push(new Paragraph({ numbering: { reference: "bullet-list", level: 0 }, children: [new TextRun({ text: "\"We can't commit to anything\" ", color: COLORS.DANGER }), new TextRun("- Push for specifics on what they CAN commit to")] }));
  content.push(new Paragraph({ numbering: { reference: "bullet-list", level: 0 }, children: [new TextRun({ text: "\"Come back later\" ", color: COLORS.DANGER }), new TextRun("- Unacceptable; demand path forward now")] }));
  content.push(new Paragraph({ numbering: { reference: "bullet-list", level: 0 }, children: [new TextRun({ text: "\"We don't do Development Agreements\" ", color: COLORS.DANGER }), new TextRun("- Ask for statutory citation; FL law requires them")] }));

  // Section 6: Action Items
  content.push(new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("6. POST-MEETING ACTION ITEMS")] }));
  content.push(createActionItemsTable());

  // Footer
  content.push(new Paragraph({ spacing: { before: 400 }, children: [] }));
  content.push(new Paragraph({ 
    alignment: AlignmentType.CENTER, shading: { fill: "F5EEF8", type: ShadingType.CLEAR }, spacing: { before: 100, after: 50 },
    children: [new TextRun({ text: "CONFIDENTIAL - ATTORNEY WORK PRODUCT", size: 20, bold: true, color: COLORS.PURPLE })]
  }));
  content.push(new Paragraph({ 
    alignment: AlignmentType.CENTER, shading: { fill: "F5EEF8", type: ShadingType.CLEAR }, spacing: { after: 100 },
    children: [new TextRun({ text: `Prepared for Property360 Real Estate | ${p.developer?.name || 'Mariam Shapira'}, Developer | ${p.projectId}`, size: 18, color: COLORS.NEUTRAL })]
  }));

  return content;
}

function createParticipantTable(participants) {
  const rows = [
    new TableRow({ children: [
      new TableCell({ borders: cellBorders, width: { size: 3120, type: WidthType.DXA }, shading: { fill: COLORS.LIGHT, type: ShadingType.CLEAR }, children: [new Paragraph({ children: [new TextRun({ text: "Name", bold: true })] })] }),
      new TableCell({ borders: cellBorders, width: { size: 3120, type: WidthType.DXA }, shading: { fill: COLORS.LIGHT, type: ShadingType.CLEAR }, children: [new Paragraph({ children: [new TextRun({ text: "Role", bold: true })] })] }),
      new TableCell({ borders: cellBorders, width: { size: 3120, type: WidthType.DXA }, shading: { fill: COLORS.LIGHT, type: ShadingType.CLEAR }, children: [new Paragraph({ children: [new TextRun({ text: "Focus Area", bold: true })] })] })
    ]})
  ];
  
  participants.forEach(p => {
    rows.push(new TableRow({ children: [
      new TableCell({ borders: cellBorders, width: { size: 3120, type: WidthType.DXA }, children: [new Paragraph({ children: [new TextRun({ text: p.name, bold: true })] })] }),
      new TableCell({ borders: cellBorders, width: { size: 3120, type: WidthType.DXA }, children: [new Paragraph({ children: [new TextRun(p.role)] })] }),
      new TableCell({ borders: cellBorders, width: { size: 3120, type: WidthType.DXA }, children: [new Paragraph({ children: [new TextRun(p.focus)] })] })
    ]}));
  });
  
  return new Table({ columnWidths: [3120, 3120, 3120], rows });
}

function createCityContactTable(contacts) {
  const rows = [
    new TableRow({ children: [
      new TableCell({ borders: cellBorders, width: { size: 3120, type: WidthType.DXA }, shading: { fill: COLORS.LIGHT, type: ShadingType.CLEAR }, children: [new Paragraph({ children: [new TextRun({ text: "Department", bold: true })] })] }),
      new TableCell({ borders: cellBorders, width: { size: 3120, type: WidthType.DXA }, shading: { fill: COLORS.LIGHT, type: ShadingType.CLEAR }, children: [new Paragraph({ children: [new TextRun({ text: "Representative", bold: true })] })] }),
      new TableCell({ borders: cellBorders, width: { size: 3120, type: WidthType.DXA }, shading: { fill: COLORS.LIGHT, type: ShadingType.CLEAR }, children: [new Paragraph({ children: [new TextRun({ text: "Key Questions For", bold: true })] })] })
    ]})
  ];
  
  contacts.forEach(c => {
    rows.push(new TableRow({ children: [
      new TableCell({ borders: cellBorders, width: { size: 3120, type: WidthType.DXA }, children: [new Paragraph({ children: [new TextRun(c.department)] })] }),
      new TableCell({ borders: cellBorders, width: { size: 3120, type: WidthType.DXA }, children: [new Paragraph({ children: [new TextRun(c.name || "[TBD]")] })] }),
      new TableCell({ borders: cellBorders, width: { size: 3120, type: WidthType.DXA }, children: [new Paragraph({ children: [new TextRun(c.focus)] })] })
    ]}));
  });
  
  return new Table({ columnWidths: [3120, 3120, 3120], rows });
}

function createAgendaTable() {
  return new Table({
    columnWidths: [1560, 2340, 5460],
    rows: [
      new TableRow({ children: [
        new TableCell({ borders: cellBorders, width: { size: 1560, type: WidthType.DXA }, shading: { fill: COLORS.LIGHT, type: ShadingType.CLEAR }, children: [new Paragraph({ children: [new TextRun({ text: "Time", bold: true })] })] }),
        new TableCell({ borders: cellBorders, width: { size: 2340, type: WidthType.DXA }, shading: { fill: COLORS.LIGHT, type: ShadingType.CLEAR }, children: [new Paragraph({ children: [new TextRun({ text: "Topic", bold: true })] })] }),
        new TableCell({ borders: cellBorders, width: { size: 5460, type: WidthType.DXA }, shading: { fill: COLORS.LIGHT, type: ShadingType.CLEAR }, children: [new Paragraph({ children: [new TextRun({ text: "Objective", bold: true })] })] })
      ]}),
      createAgendaRow("0-5 min", "Introductions", "Establish as serious, experienced developer"),
      createAgendaRow("5-15 min", "Project Overview", "Present vision, zoning request, phased approach", false, true),
      createAgendaRow("15-25 min", "Constraint Analysis", "CRITICAL: Get exact boundaries, permitted uses, timeline", true),
      createAgendaRow("25-40 min", "Dev Agreement", "OFFENSIVE: Propose Development Agreement with vested rights", false, false, true),
      createAgendaRow("40-50 min", "Technical Review", "Stormwater, traffic, setbacks, parking"),
      createAgendaRow("50-60 min", "Next Steps", "Timeline, required studies, formal application process")
    ]
  });
}

function createAgendaRow(time, topic, objective, isWarning = false, isBold = false, isPurple = false) {
  const bgColor = isWarning ? COLORS.YELLOW_BG : (isPurple ? "F5EEF8" : undefined);
  const textColor = isPurple ? COLORS.PURPLE : undefined;
  
  return new TableRow({ children: [
    new TableCell({ borders: cellBorders, width: { size: 1560, type: WidthType.DXA }, shading: bgColor ? { fill: bgColor, type: ShadingType.CLEAR } : undefined, children: [new Paragraph({ children: [new TextRun({ text: time, bold: isWarning || isPurple })] })] }),
    new TableCell({ borders: cellBorders, width: { size: 2340, type: WidthType.DXA }, shading: bgColor ? { fill: bgColor, type: ShadingType.CLEAR } : undefined, children: [new Paragraph({ children: [new TextRun({ text: topic, bold: isBold || isWarning || isPurple, color: textColor })] })] }),
    new TableCell({ borders: cellBorders, width: { size: 5460, type: WidthType.DXA }, shading: bgColor ? { fill: bgColor, type: ShadingType.CLEAR } : undefined, children: [new Paragraph({ children: [new TextRun({ text: objective, bold: isWarning || isPurple, color: textColor })] })] })
  ]});
}

function createDevAgreementTable(p) {
  const terms = [
    { term: "Zoning Lock-In", description: `${p.requestedZoning || 'Target'} zoning approved now, vested for 20 years` },
    { term: "Phased Site Plan", description: `Phase 1: Units on buildable area NOW; Phase 2: Additional units upon constraint removal` },
    { term: "Automatic Trigger", description: "Phase 2 building permits issue automatically upon constraint vacation" },
    { term: "Impact Fee Lock", description: "Current impact fee rates apply to Phase 2" },
    { term: "Concurrency Vesting", description: `Utility capacity reserved for full ${p.proposedUnits || 'all'} units` },
    { term: "Notification Duty", description: "City must notify owner within 30 days of constraint removal decision" }
  ];
  
  const rows = terms.map(t => new TableRow({ children: [
    new TableCell({ borders: cellBorders, width: { size: 3120, type: WidthType.DXA }, shading: { fill: COLORS.GREEN_BG, type: ShadingType.CLEAR }, children: [new Paragraph({ children: [new TextRun({ text: t.term, bold: true })] })] }),
    new TableCell({ borders: cellBorders, width: { size: 6240, type: WidthType.DXA }, children: [new Paragraph({ children: [new TextRun(t.description)] })] })
  ]}));
  
  return new Table({ columnWidths: [3120, 6240], rows });
}

function createActionItemsTable() {
  const items = [
    { action: "Send follow-up email summarizing meeting outcomes within 48 hours", responsible: "Attorney" },
    { action: "Request written confirmation of constraint boundaries", responsible: "Attorney" },
    { action: "FOIA request for Capital Improvement Plan", responsible: "Attorney" },
    { action: "Obtain copy of Development Agreement ordinance", responsible: "Attorney" },
    { action: "Commission updated survey showing constraint vs. buildable area", responsible: "Developer" },
    { action: "Engage civil engineer for preliminary site plan", responsible: "Developer" },
    { action: "Draft Development Agreement term sheet for city review", responsible: "Attorney" }
  ];
  
  const rows = [
    new TableRow({ children: [
      new TableCell({ borders: cellBorders, width: { size: 780, type: WidthType.DXA }, shading: { fill: COLORS.LIGHT, type: ShadingType.CLEAR }, children: [new Paragraph({ children: [new TextRun({ text: "☐", bold: true })] })] }),
      new TableCell({ borders: cellBorders, width: { size: 5460, type: WidthType.DXA }, shading: { fill: COLORS.LIGHT, type: ShadingType.CLEAR }, children: [new Paragraph({ children: [new TextRun({ text: "Action Item", bold: true })] })] }),
      new TableCell({ borders: cellBorders, width: { size: 3120, type: WidthType.DXA }, shading: { fill: COLORS.LIGHT, type: ShadingType.CLEAR }, children: [new Paragraph({ children: [new TextRun({ text: "Responsible", bold: true })] })] })
    ]})
  ];
  
  items.forEach(item => {
    rows.push(new TableRow({ children: [
      new TableCell({ borders: cellBorders, width: { size: 780, type: WidthType.DXA }, children: [new Paragraph({ children: [new TextRun("☐")] })] }),
      new TableCell({ borders: cellBorders, width: { size: 5460, type: WidthType.DXA }, children: [new Paragraph({ children: [new TextRun(item.action)] })] }),
      new TableCell({ borders: cellBorders, width: { size: 3120, type: WidthType.DXA }, children: [new Paragraph({ children: [new TextRun(item.responsible)] })] })
    ]}));
  });
  
  return new Table({ columnWidths: [780, 5460, 3120], rows });
}

module.exports = { generateMeetingAgendaAttorney, COLORS };

// CLI execution
if (require.main === module) {
  const sampleProject = {
    projectId: "SPD-2025-001",
    address: "2165 Sandy Pines Dr NE, Palm Bay, FL",
    city: "Palm Bay",
    parcelId: "2835546",
    currentZoning: "RS-2",
    requestedZoning: "RM-20",
    proposedUnits: 21,
    developer: { name: "Mariam Shapira", title: "Developer & Licensed GC" },
    constraints: [{
      type: "wellhead_easement",
      contact: "Tim Roberts",
      authority: "Palm Bay Utilities",
      timeline: "~10 years"
    }]
  };
  
  generateMeetingAgendaAttorney(sampleProject, "/mnt/user-data/outputs/SPD_MeetingAgenda_Template_Output.docx");
}
