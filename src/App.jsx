import React, { useState, useEffect, useCallback, useRef } from 'react';

// ============================================================================
// SPD.AI V3.1 - Site Planning & Development AI Platform
// ============================================================================
// V1 UI/UX (sidebar layout) + V2 Features + NLP Chatbot Integration
// © 2026 BidDeed.AI / Everest Capital USA - All Rights Reserved
// ============================================================================

// Zoning data for Brevard County
const BREVARD_ZONING_DATA = {
  'R-1': { name: 'Single Family Residential', maxDensity: 4, maxHeight: 35 },
  'R-2': { name: 'Medium Density Residential', maxDensity: 10, maxHeight: 45 },
  'R-3': { name: 'High Density Residential', maxDensity: 20, maxHeight: 65 },
  'C-1': { name: 'Neighborhood Commercial', maxFAR: 0.5, maxHeight: 35 },
  'C-2': { name: 'General Commercial', maxFAR: 1.0, maxHeight: 50 },
  'I-1': { name: 'Light Industrial', maxFAR: 0.6, maxHeight: 45 },
  'PUD': { name: 'Planned Unit Development', maxDensity: 'Varies', maxHeight: 'Varies' }
};

// Self-Storage Unit Mix
const STORAGE_UNIT_MIX = {
  '5x5': { sf: 25, pct: 10, rentPerSF: 2.00 },
  '5x10': { sf: 50, pct: 25, rentPerSF: 1.75 },
  '10x10': { sf: 100, pct: 30, rentPerSF: 1.50 },
  '10x15': { sf: 150, pct: 15, rentPerSF: 1.35 },
  '10x20': { sf: 200, pct: 12, rentPerSF: 1.25 },
  '10x30': { sf: 300, pct: 8, rentPerSF: 1.15 },
};

// Typology Configurations
const TYPOLOGY_CONFIGS = {
  multifamily: { name: 'Multi-Family', icon: '🏢', color: '#3B82F6' },
  selfStorage: { name: 'Self-Storage', icon: '📦', color: '#F97316' },
  industrial: { name: 'Industrial', icon: '🏭', color: '#6366F1' },
  singleFamily: { name: 'Single-Family', icon: '🏠', color: '#10B981' },
  seniorLiving: { name: 'Senior Living', icon: '🏥', color: '#14B8A6' },
  medical: { name: 'Medical Office', icon: '⚕️', color: '#EF4444' },
  retail: { name: 'Retail', icon: '🛒', color: '#F59E0B' },
  hotel: { name: 'Hotel', icon: '🏨', color: '#EC4899' }
};

// NLP Intent Patterns
const INTENT_PATTERNS = {
  analyze_site: [
    /analyze\s+(?:a\s+)?(\d+(?:\.\d+)?)\s*(?:acre|ac)/i,
    /(?:i have|got|looking at)\s+(?:a\s+)?(\d+(?:\.\d+)?)\s*(?:acre|ac)/i,
    /(\d+(?:\.\d+)?)\s*(?:acre|ac)\s+(?:site|parcel|lot|property)/i,
    /site\s+(?:is\s+)?(\d+(?:\.\d+)?)\s*(?:acre|ac)/i,
    /(\d+(?:\.\d+)?)\s*acres?/i,
  ],
  set_zoning: [
    /zoning\s+(?:is\s+)?([A-Z]-?\d|PUD)/i,
    /([A-Z]-?\d|PUD)\s+zon(?:ing|ed)/i,
    /zone(?:d)?\s+(?:as\s+)?([A-Z]-?\d|PUD)/i,
  ],
  typology: [
    /(?:build|develop|want|planning|for)\s+(?:a\s+)?(?:an?\s+)?(multi-?family|apartment|industrial|warehouse|single.?family|retail|hotel|self.?storage|storage|mini.?storage|senior|assisted|memory.?care|medical|office)/i,
    /(multi-?family|apartment|industrial|warehouse|single.?family|retail|hotel|self.?storage|storage|mini.?storage|senior|assisted|memory.?care|medical|office)\s+(?:development|project|building|facility)?/i,
  ],
  units: [/(\d+)\s+units?/i],
  beds: [/(\d+)\s+beds?/i],
  rooms: [/(\d+)\s+rooms?/i],
  parking: [/(\d+(?:\.\d+)?)\s+parking/i, /parking\s+(?:ratio\s+)?(\d+(?:\.\d+)?)/i],
  stories: [/(\d+)\s*(?:-?\s*)?stor(?:y|ies)/i, /(\d+)\s+floors?/i],
  climate: [/(\d+)%?\s+climate/i, /climate.?control/i],
  proforma: [/pro\s*forma/i, /financials?|economics|numbers|costs?|revenue|profit|roi/i],
  generate: [/generate|analyze|calculate|run|show/i],
  greeting: [/^(?:hi|hello|hey|good\s+(?:morning|afternoon|evening))/i],
  help: [/help|what can you do|how does this work/i],
};

// Design system colors
const COLORS = {
  primary: '#0F172A',
  secondary: '#1E293B',
  accent: '#3B82F6',
  success: '#10B981',
  warning: '#F59E0B',
  danger: '#EF4444',
  surface: '#F8FAFC',
  border: '#E2E8F0',
  textPrimary: '#0F172A',
  textSecondary: '#64748B'
};

// ============================================================================
// MAIN APP COMPONENT
// ============================================================================

export default function SPDAIApp() {
  // Form state
  const [selectedTypology, setSelectedTypology] = useState('multifamily');
  const [siteAcreage, setSiteAcreage] = useState(5.0);
  const [zoning, setZoning] = useState('R-2');
  const [params, setParams] = useState({
    parkingRatio: 1.5,
    unitMix: { studio: 10, oneBed: 40, twoBed: 35, threeBed: 15 },
    stories: 1,
    climateControlled: 50,
    clearHeight: 32,
    bayDepth: 180,
    careLevel: 'assisted',
    monthlyRate: 4500,
    rentPerSF: 28,
    adr: 145,
    anchorRatio: 0.4,
  });
  
  // Results state
  const [results, setResults] = useState(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [showProForma, setShowProForma] = useState(false);
  const [viewMode, setViewMode] = useState('2d');
  const [inputMode, setInputMode] = useState('chat'); // 'chat' or 'form'
  
  // Chat state
  const [messages, setMessages] = useState([
    {
      id: 1,
      role: 'assistant',
      content: "Hi! I'm SPD.AI, your site planning assistant. Tell me about your site - for example:\n\n• \"5 acres for self-storage\"\n• \"10 acre industrial site, I-1 zoning\"\n• \"Build apartments on 8 acres\"\n\nOr switch to Form Mode for manual controls.",
      timestamp: new Date(),
    }
  ]);
  const [chatInput, setChatInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const chatEndRef = useRef(null);

  // Auto-scroll chat
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // ============================================================================
  // NLP PARSER
  // ============================================================================

  const parseIntent = useCallback((text) => {
    const intents = [];
    const params = {};

    for (const [intent, patterns] of Object.entries(INTENT_PATTERNS)) {
      for (const pattern of patterns) {
        const match = text.match(pattern);
        if (match) {
          intents.push(intent);
          if (match[1]) {
            params[intent] = match[1];
          }
          break;
        }
      }
    }

    return { intents, params };
  }, []);

  // ============================================================================
  // FEASIBILITY CALCULATIONS
  // ============================================================================

  const generateFeasibility = useCallback((acreage, zoningCode, typologyKey, customParams = {}) => {
    const siteSquareFeet = acreage * 43560;
    const zoningData = BREVARD_ZONING_DATA[zoningCode] || BREVARD_ZONING_DATA['C-2'];
    const typology = TYPOLOGY_CONFIGS[typologyKey];
    
    let results = {
      typology: typology.name,
      typologyKey,
      icon: typology.icon,
      color: typology.color,
      acreage,
      siteSquareFeet,
      zoning: zoningCode,
    };

    // MULTI-FAMILY
    if (typologyKey === 'multifamily') {
      const maxUnits = Math.floor(acreage * (zoningData.maxDensity || 10));
      const avgUnitSF = 875;
      const grossSF = Math.round(maxUnits * avgUnitSF * 1.15);
      const floors = Math.min(Math.ceil(grossSF / (siteSquareFeet * 0.65)), Math.floor((zoningData.maxHeight || 45) / 10));
      const parkingSpaces = Math.ceil(maxUnits * (customParams.parkingRatio || 1.5));

      results = {
        ...results,
        units: maxUnits,
        grossSF,
        floors,
        parkingSpaces,
        density: (maxUnits / acreage).toFixed(1),
        far: (grossSF / siteSquareFeet).toFixed(2),
        unitMix: {
          studio: Math.round(maxUnits * 0.10),
          oneBed: Math.round(maxUnits * 0.40),
          twoBed: Math.round(maxUnits * 0.35),
          threeBed: Math.round(maxUnits * 0.15),
        },
      };
      
      results.proForma = {
        landCost: acreage * 150000,
        hardCosts: grossSF * 185,
        softCosts: grossSF * 185 * 0.25,
        totalCost: acreage * 150000 + grossSF * 185 * 1.25,
        annualRevenue: maxUnits * 1650 * 12,
        noi: maxUnits * 1650 * 12 * 0.55,
        capRate: '5.5%',
      };
      results.proForma.yieldOnCost = ((results.proForma.noi / results.proForma.totalCost) * 100).toFixed(2);
      results.proForma.estimatedValue = results.proForma.noi / 0.055;
      results.proForma.profit = results.proForma.estimatedValue - results.proForma.totalCost;
      results.proForma.margin = ((results.proForma.profit / results.proForma.totalCost) * 100).toFixed(1);
    }

    // SELF-STORAGE
    else if (typologyKey === 'selfStorage') {
      const stories = customParams.stories || 1;
      const lotCoverage = stories === 1 ? 0.40 : 0.35;
      const grossBuildingSF = siteSquareFeet * lotCoverage * stories;
      const netRentableSF = Math.round(grossBuildingSF * 0.85);
      const climateControlledPct = customParams.climateControlled || 50;
      
      let totalUnits = 0;
      const unitBreakdown = {};
      let monthlyRevenue = 0;
      
      for (const [size, data] of Object.entries(STORAGE_UNIT_MIX)) {
        const unitCount = Math.round((netRentableSF * data.pct / 100) / data.sf);
        unitBreakdown[size] = unitCount;
        totalUnits += unitCount;
        const climateUnits = Math.round(unitCount * (climateControlledPct / 100));
        const nonClimateUnits = unitCount - climateUnits;
        monthlyRevenue += climateUnits * data.sf * data.rentPerSF * 1.30;
        monthlyRevenue += nonClimateUnits * data.sf * data.rentPerSF;
      }

      results = {
        ...results,
        stories,
        grossBuildingSF: Math.round(grossBuildingSF),
        netRentableSF,
        totalUnits,
        unitBreakdown,
        climateControlledPct,
        avgRentPerSF: (monthlyRevenue / netRentableSF).toFixed(2),
        monthlyRevenue: Math.round(monthlyRevenue),
      };
      
      const hardCostPerSF = stories === 1 ? 55 : 85;
      results.proForma = {
        landCost: acreage * 125000,
        hardCosts: grossBuildingSF * hardCostPerSF,
        softCosts: grossBuildingSF * hardCostPerSF * 0.18,
        totalCost: acreage * 125000 + grossBuildingSF * hardCostPerSF * 1.18,
        monthlyRevenue: Math.round(monthlyRevenue),
        annualRevenue: Math.round(monthlyRevenue * 12),
        effectiveRevenue: Math.round(monthlyRevenue * 12 * 0.88),
        noi: Math.round(monthlyRevenue * 12 * 0.88 * 0.60),
        capRate: '6.5%',
      };
      results.proForma.yieldOnCost = ((results.proForma.noi / results.proForma.totalCost) * 100).toFixed(2);
      results.proForma.estimatedValue = results.proForma.noi / 0.065;
      results.proForma.profit = results.proForma.estimatedValue - results.proForma.totalCost;
      results.proForma.margin = ((results.proForma.profit / results.proForma.totalCost) * 100).toFixed(1);
    }

    // INDUSTRIAL
    else if (typologyKey === 'industrial') {
      const warehouseSF = Math.round(siteSquareFeet * 0.55);
      const dockDoors = Math.ceil(warehouseSF / 10000);
      const carParking = Math.ceil(warehouseSF / 2000);

      results = {
        ...results,
        warehouseSF,
        clearHeight: customParams.clearHeight || 32,
        dockDoors,
        trailerSpaces: dockDoors * 2,
        carParking,
        far: (warehouseSF / siteSquareFeet).toFixed(2),
      };
      
      results.proForma = {
        landCost: acreage * 100000,
        hardCosts: warehouseSF * 95,
        softCosts: warehouseSF * 95 * 0.20,
        totalCost: acreage * 100000 + warehouseSF * 95 * 1.20,
        annualRevenue: warehouseSF * 9.50,
        noi: warehouseSF * 9.50 * 0.92,
        capRate: '6.5%',
      };
      results.proForma.yieldOnCost = ((results.proForma.noi / results.proForma.totalCost) * 100).toFixed(2);
      results.proForma.estimatedValue = results.proForma.noi / 0.065;
      results.proForma.profit = results.proForma.estimatedValue - results.proForma.totalCost;
      results.proForma.margin = ((results.proForma.profit / results.proForma.totalCost) * 100).toFixed(1);
    }

    // SINGLE-FAMILY
    else if (typologyKey === 'singleFamily') {
      const avgLotSize = 7500;
      const totalLots = Math.floor(siteSquareFeet * 0.70 / avgLotSize);

      results = {
        ...results,
        totalLots,
        avgLotSize,
        avgHomeSize: 2200,
        density: (totalLots / acreage).toFixed(1),
      };
      
      results.proForma = {
        landCost: acreage * 125000,
        hardCosts: totalLots * 2200 * 165,
        softCosts: totalLots * 2200 * 165 * 0.15,
        totalCost: acreage * 125000 + totalLots * 2200 * 165 * 1.15,
        totalRevenue: totalLots * 425000,
        capRate: 'N/A',
      };
      results.proForma.profit = results.proForma.totalRevenue - results.proForma.totalCost;
      results.proForma.margin = ((results.proForma.profit / results.proForma.totalCost) * 100).toFixed(1);
    }

    // SENIOR LIVING
    else if (typologyKey === 'seniorLiving') {
      const beds = Math.floor(acreage * 25);
      const grossSF = Math.round(beds * 450 / 0.65);
      const floors = Math.min(Math.ceil(grossSF / (siteSquareFeet * 0.40)), 4);
      const monthlyRate = customParams.monthlyRate || 4500;

      results = {
        ...results,
        beds,
        grossSF,
        floors,
        parkingSpaces: Math.ceil(beds * 0.5),
        density: (beds / acreage).toFixed(1),
        monthlyRate,
        careLevel: customParams.careLevel || 'assisted',
      };
      
      results.proForma = {
        landCost: acreage * 175000,
        hardCosts: grossSF * 225,
        softCosts: grossSF * 225 * 0.28,
        totalCost: acreage * 175000 + grossSF * 225 * 1.28,
        monthlyRevenue: Math.round(beds * monthlyRate * 0.90),
        annualRevenue: Math.round(beds * monthlyRate * 12 * 0.90),
        noi: Math.round(beds * monthlyRate * 12 * 0.90 * 0.35),
        capRate: '7.0%',
      };
      results.proForma.yieldOnCost = ((results.proForma.noi / results.proForma.totalCost) * 100).toFixed(2);
      results.proForma.estimatedValue = results.proForma.noi / 0.07;
      results.proForma.profit = results.proForma.estimatedValue - results.proForma.totalCost;
      results.proForma.margin = ((results.proForma.profit / results.proForma.totalCost) * 100).toFixed(1);
    }

    // MEDICAL OFFICE
    else if (typologyKey === 'medical') {
      const stories = customParams.stories || 2;
      const grossSF = Math.round(siteSquareFeet * 0.35 * stories);
      const parkingSpaces = Math.ceil(grossSF / 250);
      const rentPerSF = customParams.rentPerSF || 28;

      results = {
        ...results,
        grossSF,
        floors: stories,
        parkingSpaces,
        parkingRatio: (parkingSpaces / (grossSF / 1000)).toFixed(1),
        far: (grossSF / siteSquareFeet).toFixed(2),
        rentPerSF,
      };
      
      results.proForma = {
        landCost: acreage * 200000,
        hardCosts: grossSF * 275,
        softCosts: grossSF * 275 * 0.22,
        totalCost: acreage * 200000 + grossSF * 275 * 1.22,
        annualRevenue: grossSF * rentPerSF,
        noi: grossSF * rentPerSF * 0.88,
        capRate: '6.25%',
      };
      results.proForma.yieldOnCost = ((results.proForma.noi / results.proForma.totalCost) * 100).toFixed(2);
      results.proForma.estimatedValue = results.proForma.noi / 0.0625;
      results.proForma.profit = results.proForma.estimatedValue - results.proForma.totalCost;
      results.proForma.margin = ((results.proForma.profit / results.proForma.totalCost) * 100).toFixed(1);
    }

    // RETAIL
    else if (typologyKey === 'retail') {
      const grossSF = Math.round(siteSquareFeet * 0.25);
      const parkingSpaces = Math.ceil(grossSF / 200);

      results = {
        ...results,
        grossSF,
        parkingSpaces,
        padSites: Math.floor(acreage / 1.5),
        anchorSF: Math.round(grossSF * 0.4),
        shopSF: Math.round(grossSF * 0.6),
      };
      
      results.proForma = {
        landCost: acreage * 175000,
        hardCosts: grossSF * 165,
        softCosts: grossSF * 165 * 0.18,
        totalCost: acreage * 175000 + grossSF * 165 * 1.18,
        annualRevenue: grossSF * 22,
        noi: grossSF * 22 * 0.85,
        capRate: '6.75%',
      };
      results.proForma.yieldOnCost = ((results.proForma.noi / results.proForma.totalCost) * 100).toFixed(2);
      results.proForma.estimatedValue = results.proForma.noi / 0.0675;
      results.proForma.profit = results.proForma.estimatedValue - results.proForma.totalCost;
      results.proForma.margin = ((results.proForma.profit / results.proForma.totalCost) * 100).toFixed(1);
    }

    // HOTEL
    else if (typologyKey === 'hotel') {
      const rooms = Math.floor(acreage * 60);
      const grossSF = Math.round(rooms * 375 * 1.35);
      const floors = Math.min(Math.ceil(grossSF / (siteSquareFeet * 0.35)), 5);
      const adr = customParams.adr || 145;
      const revPAR = adr * 0.68;

      results = {
        ...results,
        rooms,
        grossSF,
        floors,
        parkingSpaces: Math.ceil(rooms * 0.8),
        adr,
        occupancy: '68%',
        revPAR: revPAR.toFixed(2),
      };
      
      results.proForma = {
        landCost: acreage * 200000,
        hardCosts: grossSF * 195,
        softCosts: grossSF * 195 * 0.25,
        totalCost: acreage * 200000 + grossSF * 195 * 1.25,
        annualRevenue: Math.round(rooms * revPAR * 365),
        noi: Math.round(rooms * revPAR * 365 * 0.35),
        capRate: '8.0%',
      };
      results.proForma.yieldOnCost = ((results.proForma.noi / results.proForma.totalCost) * 100).toFixed(2);
      results.proForma.estimatedValue = results.proForma.noi / 0.08;
      results.proForma.profit = results.proForma.estimatedValue - results.proForma.totalCost;
      results.proForma.margin = ((results.proForma.profit / results.proForma.totalCost) * 100).toFixed(1);
    }

    return results;
  }, []);

  // ============================================================================
  // CHAT RESPONSE GENERATION
  // ============================================================================

  const generateChatResponse = useCallback((text) => {
    const { intents, params: extractedParams } = parseIntent(text);
    let response = '';
    let newAcreage = siteAcreage;
    let newZoning = zoning;
    let newTypology = selectedTypology;
    let newParams = { ...params };
    let shouldGenerate = false;

    // Handle greetings
    if (intents.includes('greeting')) {
      response = "Hello! I'm ready to analyze your site. Tell me the acreage and what you'd like to build.";
      return { response };
    }

    // Handle help
    if (intents.includes('help')) {
      response = "I can help you analyze site feasibility! Try:\n\n";
      response += "• \"5 acres for apartments\"\n";
      response += "• \"10 acre self-storage, 3-story\"\n";
      response += "• \"8 acres industrial, I-1 zoning\"\n";
      response += "• \"Show pro forma\"\n\n";
      response += "I support: Multi-Family, Self-Storage, Industrial, Single-Family, Senior Living, Medical Office, Retail, and Hotel.";
      return { response };
    }

    // Extract acreage
    if (intents.includes('analyze_site') && extractedParams.analyze_site) {
      newAcreage = parseFloat(extractedParams.analyze_site);
      response += `📍 **${newAcreage} acres** - got it. `;
      shouldGenerate = true;
    }

    // Extract zoning
    if (intents.includes('set_zoning') && extractedParams.set_zoning) {
      const zoneCode = extractedParams.set_zoning.toUpperCase();
      if (BREVARD_ZONING_DATA[zoneCode]) {
        newZoning = zoneCode;
        response += `🏷️ Zoning: **${zoneCode}**. `;
      }
    }

    // Extract typology
    if (intents.includes('typology') && extractedParams.typology) {
      const typologyMap = {
        'multi-family': 'multifamily', 'multifamily': 'multifamily', 'apartment': 'multifamily', 'apartments': 'multifamily',
        'industrial': 'industrial', 'warehouse': 'industrial',
        'single-family': 'singleFamily', 'singlefamily': 'singleFamily',
        'self-storage': 'selfStorage', 'selfstorage': 'selfStorage', 'storage': 'selfStorage', 'mini-storage': 'selfStorage',
        'senior': 'seniorLiving', 'assisted': 'seniorLiving', 'memory-care': 'seniorLiving',
        'medical': 'medical', 'office': 'medical',
        'retail': 'retail',
        'hotel': 'hotel',
      };
      const rawTypology = extractedParams.typology.toLowerCase().replace(/\s+/g, '-');
      const mappedTypology = typologyMap[rawTypology];
      if (mappedTypology) {
        newTypology = mappedTypology;
        const config = TYPOLOGY_CONFIGS[mappedTypology];
        response += `${config.icon} **${config.name}**. `;
        shouldGenerate = true;
      }
    }

    // Extract stories
    if (intents.includes('stories') && extractedParams.stories) {
      newParams.stories = parseInt(extractedParams.stories);
      response += `🏗️ ${newParams.stories}-story. `;
    }

    // Extract climate control
    if (intents.includes('climate')) {
      if (extractedParams.climate) {
        newParams.climateControlled = parseInt(extractedParams.climate);
      } else {
        newParams.climateControlled = 100;
      }
      response += `❄️ ${newParams.climateControlled}% climate controlled. `;
    }

    // Handle pro forma request
    if (intents.includes('proforma')) {
      if (results) {
        setShowProForma(true);
        response = "📊 Pro forma is now visible in the results panel. ";
        response += `\n\n**Quick Summary:**\n`;
        response += `• Total Cost: $${(results.proForma.totalCost / 1000000).toFixed(2)}M\n`;
        response += `• NOI: $${(results.proForma.noi / 1000000).toFixed(2)}M\n`;
        response += `• **Profit: $${(results.proForma.profit / 1000000).toFixed(2)}M** (${results.proForma.margin}% margin)`;
        return { response };
      } else {
        response = "I need to generate a feasibility analysis first. Tell me about your site!";
        return { response };
      }
    }

    // Generate if we have enough info
    if (shouldGenerate && newAcreage && newTypology) {
      setSiteAcreage(newAcreage);
      setZoning(newZoning);
      setSelectedTypology(newTypology);
      setParams(newParams);
      
      const newResults = generateFeasibility(newAcreage, newZoning, newTypology, newParams);
      setResults(newResults);
      
      response += `\n\n---\n\n### ${newResults.icon} Feasibility Results\n\n`;
      
      // Build summary based on typology
      if (newTypology === 'multifamily') {
        response += `| Metric | Value |\n|--------|-------|\n`;
        response += `| Units | ${newResults.units} |\n`;
        response += `| Gross SF | ${newResults.grossSF.toLocaleString()} |\n`;
        response += `| Stories | ${newResults.floors} |\n`;
        response += `| Density | ${newResults.density}/acre |\n`;
      } else if (newTypology === 'selfStorage') {
        response += `| Metric | Value |\n|--------|-------|\n`;
        response += `| Net Rentable | ${newResults.netRentableSF.toLocaleString()} SF |\n`;
        response += `| Units | ${newResults.totalUnits} |\n`;
        response += `| Stories | ${newResults.stories} |\n`;
        response += `| Monthly Rev | $${newResults.monthlyRevenue.toLocaleString()} |\n`;
      } else if (newTypology === 'industrial') {
        response += `| Metric | Value |\n|--------|-------|\n`;
        response += `| Warehouse SF | ${newResults.warehouseSF.toLocaleString()} |\n`;
        response += `| Clear Height | ${newResults.clearHeight}' |\n`;
        response += `| Dock Doors | ${newResults.dockDoors} |\n`;
      } else if (newTypology === 'singleFamily') {
        response += `| Metric | Value |\n|--------|-------|\n`;
        response += `| Lots | ${newResults.totalLots} |\n`;
        response += `| Avg Lot | ${newResults.avgLotSize.toLocaleString()} SF |\n`;
        response += `| Density | ${newResults.density}/acre |\n`;
      } else if (newTypology === 'seniorLiving') {
        response += `| Metric | Value |\n|--------|-------|\n`;
        response += `| Beds | ${newResults.beds} |\n`;
        response += `| Gross SF | ${newResults.grossSF.toLocaleString()} |\n`;
        response += `| Monthly Rate | $${newResults.monthlyRate.toLocaleString()} |\n`;
      } else if (newTypology === 'medical') {
        response += `| Metric | Value |\n|--------|-------|\n`;
        response += `| Gross SF | ${newResults.grossSF.toLocaleString()} |\n`;
        response += `| Stories | ${newResults.floors} |\n`;
        response += `| Rent | $${newResults.rentPerSF}/SF NNN |\n`;
      } else if (newTypology === 'hotel') {
        response += `| Metric | Value |\n|--------|-------|\n`;
        response += `| Rooms | ${newResults.rooms} |\n`;
        response += `| ADR | $${newResults.adr} |\n`;
        response += `| RevPAR | $${newResults.revPAR} |\n`;
      } else if (newTypology === 'retail') {
        response += `| Metric | Value |\n|--------|-------|\n`;
        response += `| Gross SF | ${newResults.grossSF.toLocaleString()} |\n`;
        response += `| Pad Sites | ${newResults.padSites} |\n`;
      }
      
      response += `\n💰 **Profit: $${(newResults.proForma.profit / 1000000).toFixed(2)}M** (${newResults.proForma.margin}% margin)`;
      response += `\n\n_Say "show pro forma" for detailed financials._`;
      
      return { response, results: newResults };
    }

    // If we couldn't understand
    if (!response) {
      if (!siteAcreage || siteAcreage === 5.0) {
        response = "What's the acreage of your site? For example: \"I have a 5 acre site\"";
      } else if (!intents.length) {
        response = "I'm not sure what you're asking. Try:\n\n• \"Build apartments\" or \"self-storage\"\n• \"Show pro forma\"\n• \"Change to 3-story\"";
      }
    }

    return { response };
  }, [parseIntent, siteAcreage, zoning, selectedTypology, params, results, generateFeasibility]);

  // Handle chat submit
  const handleChatSubmit = useCallback(() => {
    if (!chatInput.trim()) return;

    const userMessage = {
      id: messages.length + 1,
      role: 'user',
      content: chatInput.trim(),
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setChatInput('');
    setIsTyping(true);

    setTimeout(() => {
      const { response } = generateChatResponse(chatInput);
      
      const assistantMessage = {
        id: messages.length + 2,
        role: 'assistant',
        content: response,
        timestamp: new Date(),
      };

      setMessages(prev => [...prev, assistantMessage]);
      setIsTyping(false);
    }, 600 + Math.random() * 400);
  }, [chatInput, messages, generateChatResponse]);

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleChatSubmit();
    }
  };

  // Handle form generate
  const handleFormGenerate = useCallback(() => {
    setIsGenerating(true);
    setTimeout(() => {
      const newResults = generateFeasibility(siteAcreage, zoning, selectedTypology, params);
      setResults(newResults);
      setIsGenerating(false);
    }, 800);
  }, [siteAcreage, zoning, selectedTypology, params, generateFeasibility]);

  // Quick prompts
  const quickPrompts = [
    { label: '📦 5ac storage', prompt: '5 acres for self-storage, 3-story' },
    { label: '🏢 10ac apts', prompt: '10 acre multifamily site, R-3 zoning' },
    { label: '🏭 8ac industrial', prompt: '8 acres industrial, I-1 zoning' },
    { label: '🏥 3ac senior', prompt: '3 acres for senior living' },
  ];

  return (
    <div style={styles.container}>
      {/* Header */}
      <header style={styles.header}>
        <div style={styles.headerLeft}>
          <div style={styles.logo}>
            <span style={styles.logoIcon}>◆</span>
            <span style={styles.logoText}>SPD.AI</span>
          </div>
          <span style={styles.tagline}>Site Planning Intelligence</span>
        </div>
        <div style={styles.headerCenter}>
          <div style={styles.modeToggle}>
            <button
              style={{...styles.modeBtn, ...(inputMode === 'chat' ? styles.modeBtnActive : {})}}
              onClick={() => setInputMode('chat')}
            >
              💬 Chat
            </button>
            <button
              style={{...styles.modeBtn, ...(inputMode === 'form' ? styles.modeBtnActive : {})}}
              onClick={() => setInputMode('form')}
            >
              📝 Form
            </button>
          </div>
        </div>
        <div style={styles.headerRight}>
          <div style={styles.viewToggle}>
            <button style={{...styles.viewBtn, ...(viewMode === '2d' ? styles.viewBtnActive : {})}} onClick={() => setViewMode('2d')}>2D</button>
            <button style={{...styles.viewBtn, ...(viewMode === '3d' ? styles.viewBtnActive : {})}} onClick={() => setViewMode('3d')}>3D</button>
          </div>
          <div style={styles.userBadge}>
            <span style={styles.poweredBy}>Powered by</span>
            <span style={styles.biddeedBrand}>BidDeed.AI</span>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div style={styles.mainContent}>
        {/* Left Sidebar */}
        <aside style={styles.sidebar}>
          {inputMode === 'chat' ? (
            /* CHAT MODE */
            <div style={styles.chatContainer}>
              <div style={styles.chatMessages}>
                {messages.map((msg) => (
                  <div key={msg.id} style={{...styles.messageWrapper, justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start'}}>
                    {msg.role === 'assistant' && <div style={styles.avatarAI}>◆</div>}
                    <div style={{...styles.messageBubble, ...(msg.role === 'user' ? styles.userBubble : styles.aiBubble)}}>
                      <MessageContent content={msg.content} />
                    </div>
                  </div>
                ))}
                {isTyping && (
                  <div style={styles.messageWrapper}>
                    <div style={styles.avatarAI}>◆</div>
                    <div style={{...styles.messageBubble, ...styles.aiBubble}}>
                      <div style={styles.typingIndicator}>
                        <span style={styles.typingDot}></span>
                        <span style={{...styles.typingDot, animationDelay: '0.2s'}}></span>
                        <span style={{...styles.typingDot, animationDelay: '0.4s'}}></span>
                      </div>
                    </div>
                  </div>
                )}
                <div ref={chatEndRef} />
              </div>
              
              {/* Quick Prompts */}
              {messages.length <= 2 && (
                <div style={styles.quickPrompts}>
                  {quickPrompts.map((qp, i) => (
                    <button key={i} style={styles.quickPromptBtn} onClick={() => { setChatInput(qp.prompt); }}>
                      {qp.label}
                    </button>
                  ))}
                </div>
              )}
              
              {/* Chat Input */}
              <div style={styles.chatInputArea}>
                <textarea
                  style={styles.chatInput}
                  placeholder="Describe your site... (e.g., '5 acres for storage')"
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  onKeyPress={handleKeyPress}
                  rows={2}
                />
                <button style={styles.sendBtn} onClick={handleChatSubmit} disabled={!chatInput.trim()}>
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M22 2L11 13M22 2L15 22L11 13L2 9L22 2Z" />
                  </svg>
                </button>
              </div>
            </div>
          ) : (
            /* FORM MODE */
            <>
              <div style={styles.section}>
                <h3 style={styles.sectionTitle}><span style={styles.sectionIcon}>📍</span> Site Definition</h3>
                <div style={styles.inputRow}>
                  <div style={styles.inputGroup}>
                    <label style={styles.label}>Acreage</label>
                    <input type="number" style={styles.input} value={siteAcreage} onChange={(e) => setSiteAcreage(parseFloat(e.target.value) || 0)} step="0.1" />
                  </div>
                  <div style={styles.inputGroup}>
                    <label style={styles.label}>Zoning</label>
                    <select style={styles.select} value={zoning} onChange={(e) => setZoning(e.target.value)}>
                      {Object.entries(BREVARD_ZONING_DATA).map(([code, data]) => (
                        <option key={code} value={code}>{code}</option>
                      ))}
                    </select>
                  </div>
                </div>
              </div>

              <div style={styles.section}>
                <h3 style={styles.sectionTitle}><span style={styles.sectionIcon}>🏗️</span> Development Type</h3>
                <div style={styles.typologyGrid}>
                  {Object.entries(TYPOLOGY_CONFIGS).map(([key, config]) => (
                    <button
                      key={key}
                      style={{...styles.typologyBtn, ...(selectedTypology === key ? {...styles.typologyBtnActive, borderColor: config.color, backgroundColor: `${config.color}15`} : {})}}
                      onClick={() => setSelectedTypology(key)}
                    >
                      <span style={styles.typologyIcon}>{config.icon}</span>
                      <span style={styles.typologyName}>{config.name}</span>
                    </button>
                  ))}
                </div>
              </div>

              <div style={styles.section}>
                <h3 style={styles.sectionTitle}><span style={styles.sectionIcon}>⚙️</span> Parameters</h3>
                {selectedTypology === 'selfStorage' && (
                  <div style={styles.paramGrid}>
                    <div style={styles.paramGroup}>
                      <label style={styles.paramLabel}>Stories</label>
                      <select style={styles.paramSelect} value={params.stories} onChange={(e) => setParams({...params, stories: parseInt(e.target.value)})}>
                        <option value={1}>1-Story</option>
                        <option value={2}>2-Story</option>
                        <option value={3}>3-Story</option>
                        <option value={4}>4-Story</option>
                      </select>
                    </div>
                    <div style={styles.paramGroup}>
                      <label style={styles.paramLabel}>Climate %</label>
                      <input type="number" style={styles.paramInput} value={params.climateControlled} onChange={(e) => setParams({...params, climateControlled: parseInt(e.target.value)})} />
                    </div>
                  </div>
                )}
                {selectedTypology === 'multifamily' && (
                  <div style={styles.paramGroup}>
                    <label style={styles.paramLabel}>Parking Ratio</label>
                    <input type="number" style={styles.paramInput} value={params.parkingRatio} onChange={(e) => setParams({...params, parkingRatio: parseFloat(e.target.value)})} step="0.1" />
                    <span style={styles.paramUnit}>/unit</span>
                  </div>
                )}
                {selectedTypology === 'seniorLiving' && (
                  <div style={styles.paramGroup}>
                    <label style={styles.paramLabel}>Monthly Rate</label>
                    <input type="number" style={styles.paramInput} value={params.monthlyRate} onChange={(e) => setParams({...params, monthlyRate: parseInt(e.target.value)})} />
                    <span style={styles.paramUnit}>$/mo</span>
                  </div>
                )}
              </div>

              <button style={{...styles.generateBtn, ...(isGenerating ? styles.generateBtnLoading : {})}} onClick={handleFormGenerate} disabled={isGenerating}>
                {isGenerating ? 'Generating...' : '⚡ Generate Feasibility'}
              </button>
            </>
          )}
        </aside>

        {/* Map Area */}
        <main style={styles.mapArea}>
          <div style={styles.mapContainer}>
            <div style={styles.mapPlaceholder}>
              <svg style={styles.gridPattern} xmlns="http://www.w3.org/2000/svg">
                <defs>
                  <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
                    <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#E2E8F0" strokeWidth="1"/>
                  </pattern>
                </defs>
                <rect width="100%" height="100%" fill="url(#grid)" />
              </svg>
              <div style={styles.mapOverlay}>
                <div style={styles.mapCenter}>
                  <div style={{...styles.sitePolygon, borderColor: results?.color || COLORS.accent, backgroundColor: `${results?.color || COLORS.accent}20`}}>
                    <div style={{...styles.siteLabel, color: results?.color || COLORS.accent}}>
                      {results?.icon || '📍'} {siteAcreage} AC
                      <br />
                      <small>{(siteAcreage * 43560).toLocaleString()} SF</small>
                    </div>
                  </div>
                </div>
                <div style={styles.mapInfo}>
                  <span>📍 Brevard County, FL</span>
                  <span>🏷️ {zoning}</span>
                  {results && <span style={{color: results.color}}>{results.icon} {results.typology}</span>}
                </div>
              </div>
            </div>
          </div>
        </main>

        {/* Right Sidebar - Results */}
        <aside style={styles.resultsSidebar}>
          {results ? (
            <>
              <div style={styles.resultsHeader}>
                <div style={styles.resultsTitle}>
                  <span style={{fontSize: '28px'}}>{results.icon}</span>
                  <div>
                    <h3 style={styles.resultsTitleText}>{results.typology}</h3>
                    <span style={styles.resultsSubtitle}>{results.acreage} acres • {results.zoning}</span>
                  </div>
                </div>
              </div>

              <div style={styles.metricsGrid}>
                {results.units && <MetricCard label="Units" value={results.units} icon="🏢" color={results.color} />}
                {results.netRentableSF && <MetricCard label="Net SF" value={results.netRentableSF.toLocaleString()} icon="📦" color={results.color} />}
                {results.warehouseSF && <MetricCard label="Warehouse" value={results.warehouseSF.toLocaleString()} icon="🏭" color={results.color} />}
                {results.totalLots && <MetricCard label="Lots" value={results.totalLots} icon="🏠" color={results.color} />}
                {results.beds && <MetricCard label="Beds" value={results.beds} icon="🏥" color={results.color} />}
                {results.rooms && <MetricCard label="Rooms" value={results.rooms} icon="🏨" color={results.color} />}
                {results.grossSF && <MetricCard label="Gross SF" value={results.grossSF.toLocaleString()} icon="📐" />}
                {results.floors && <MetricCard label="Stories" value={results.floors} icon="🏗️" />}
                {results.parkingSpaces && <MetricCard label="Parking" value={results.parkingSpaces} icon="🚗" />}
                {results.density && <MetricCard label="Density" value={`${results.density}/ac`} icon="📊" />}
                {results.totalUnits && <MetricCard label="Units" value={results.totalUnits} icon="🔢" />}
                {results.dockDoors && <MetricCard label="Docks" value={results.dockDoors} icon="🚚" />}
              </div>

              {/* Storage Unit Mix */}
              {results.unitBreakdown && (
                <div style={styles.unitMixResults}>
                  <h4 style={styles.sectionTitleSmall}>📦 Unit Mix</h4>
                  <div style={styles.storageUnitGrid}>
                    {Object.entries(results.unitBreakdown).map(([size, count]) => (
                      <div key={size} style={styles.storageUnitItem}>
                        <span style={styles.storageUnitSize}>{size}</span>
                        <span style={styles.storageUnitCount}>{count}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <button style={styles.proFormaToggle} onClick={() => setShowProForma(!showProForma)}>
                <span>💰</span>
                <span>Pro Forma</span>
                <span style={{transform: showProForma ? 'rotate(180deg)' : 'rotate(0deg)'}}>▼</span>
              </button>

              {showProForma && results.proForma && (
                <div style={styles.proFormaSection}>
                  <div style={styles.proFormaGrid}>
                    <div style={styles.proFormaItem}><span style={styles.proFormaLabel}>Land</span><span style={styles.proFormaValue}>${(results.proForma.landCost / 1000000).toFixed(2)}M</span></div>
                    <div style={styles.proFormaItem}><span style={styles.proFormaLabel}>Hard Costs</span><span style={styles.proFormaValue}>${(results.proForma.hardCosts / 1000000).toFixed(2)}M</span></div>
                    <div style={styles.proFormaItem}><span style={styles.proFormaLabel}>Soft Costs</span><span style={styles.proFormaValue}>${(results.proForma.softCosts / 1000000).toFixed(2)}M</span></div>
                    <div style={{...styles.proFormaItem, ...styles.proFormaTotal}}><span style={styles.proFormaLabel}>Total Cost</span><span style={styles.proFormaValue}>${(results.proForma.totalCost / 1000000).toFixed(2)}M</span></div>
                  </div>
                  <div style={styles.proFormaDivider} />
                  <div style={styles.proFormaGrid}>
                    <div style={styles.proFormaItem}><span style={styles.proFormaLabel}>Revenue</span><span style={styles.proFormaValue}>${((results.proForma.annualRevenue || results.proForma.totalRevenue) / 1000000).toFixed(2)}M</span></div>
                    {results.proForma.noi && <div style={styles.proFormaItem}><span style={styles.proFormaLabel}>NOI</span><span style={styles.proFormaValue}>${(results.proForma.noi / 1000000).toFixed(2)}M</span></div>}
                    {results.proForma.yieldOnCost && <div style={styles.proFormaItem}><span style={styles.proFormaLabel}>YOC</span><span style={{...styles.proFormaValue, color: COLORS.success}}>{results.proForma.yieldOnCost}%</span></div>}
                    <div style={styles.proFormaItem}><span style={styles.proFormaLabel}>Cap Rate</span><span style={styles.proFormaValue}>{results.proForma.capRate}</span></div>
                  </div>
                  <div style={styles.profitBanner}>
                    <span style={styles.profitLabel}>Profit</span>
                    <span style={styles.profitValue}>${(results.proForma.profit / 1000000).toFixed(2)}M</span>
                    <span style={styles.profitMargin}>{results.proForma.margin}% margin</span>
                  </div>
                </div>
              )}

              <div style={styles.exportActions}>
                <button style={styles.exportBtn}>📄 PDF</button>
                <button style={styles.exportBtn}>📊 Excel</button>
                <button style={{...styles.exportBtn, ...styles.exportBtnPrimary}}>🔗 Share</button>
              </div>
            </>
          ) : (
            <div style={styles.emptyResults}>
              <div style={styles.emptyIcon}>📊</div>
              <h3 style={styles.emptyTitle}>No Analysis Yet</h3>
              <p style={styles.emptyText}>Use the chat or form to describe your site and generate a feasibility analysis.</p>
            </div>
          )}
        </aside>
      </div>

      {/* Footer */}
      <footer style={styles.footer}>
        <span>© 2026 BidDeed.AI / Everest Capital USA</span>
        <span style={styles.footerDivider}>•</span>
        <span>SPD.AI v3.1</span>
      </footer>
    </div>
  );
}

// Message Content Component with Markdown
function MessageContent({ content }) {
  const renderContent = (text) => {
    const parts = text.split(/((?:\|[^\n]+\|\n)+)/g);
    
    return parts.map((part, i) => {
      if (part.includes('|') && part.includes('\n')) {
        const rows = part.trim().split('\n').filter(r => r.includes('|'));
        const isHeader = rows.length > 1 && rows[1].match(/^\|[\s-:|]+\|$/);
        
        return (
          <table key={i} style={styles.table}>
            <tbody>
              {rows.map((row, ri) => {
                if (isHeader && ri === 1) return null;
                const cells = row.split('|').filter(c => c.trim());
                return (
                  <tr key={ri}>
                    {cells.map((cell, ci) => (
                      <td key={ci} style={styles.td}>{cell.trim().replace(/\*\*/g, '')}</td>
                    ))}
                  </tr>
                );
              })}
            </tbody>
          </table>
        );
      }
      
      return (
        <span key={i}>
          {part.split('\n').map((line, li) => {
            if (line.startsWith('### ')) return <h4 key={li} style={styles.mdH4}>{line.replace('### ', '').replace(/\*\*/g, '')}</h4>;
            if (line === '---') return <hr key={li} style={styles.mdHr} />;
            if (line.startsWith('• ')) return <div key={li} style={styles.mdLi}>{line}</div>;
            const boldParts = line.split(/\*\*([^*]+)\*\*/g);
            if (boldParts.length > 1) {
              return <p key={li} style={styles.mdP}>{boldParts.map((bp, bpi) => bpi % 2 === 1 ? <strong key={bpi}>{bp}</strong> : bp)}</p>;
            }
            return line ? <p key={li} style={styles.mdP}>{line}</p> : null;
          })}
        </span>
      );
    });
  };

  return <div>{renderContent(content)}</div>;
}

function MetricCard({ label, value, icon, color }) {
  return (
    <div style={styles.metricCard}>
      <div style={{...styles.metricIcon, color: color || COLORS.accent}}>{icon}</div>
      <div style={styles.metricContent}>
        <span style={styles.metricValue}>{value}</span>
        <span style={styles.metricLabel}>{label}</span>
      </div>
    </div>
  );
}

// ============================================================================
// STYLES
// ============================================================================

const styles = {
  container: { display: 'flex', flexDirection: 'column', height: '100vh', backgroundColor: '#F1F5F9', fontFamily: "'Inter', -apple-system, sans-serif", color: COLORS.textPrimary },
  header: { display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '12px 24px', backgroundColor: COLORS.primary, borderBottom: `1px solid ${COLORS.secondary}`, zIndex: 100 },
  headerLeft: { display: 'flex', alignItems: 'center', gap: '16px' },
  logo: { display: 'flex', alignItems: 'center', gap: '8px' },
  logoIcon: { fontSize: '24px', color: COLORS.accent },
  logoText: { fontSize: '20px', fontWeight: '700', color: '#fff', letterSpacing: '-0.5px' },
  tagline: { fontSize: '12px', color: '#94A3B8', borderLeft: '1px solid #334155', paddingLeft: '16px' },
  headerCenter: { flex: 1, display: 'flex', justifyContent: 'center' },
  modeToggle: { display: 'flex', backgroundColor: COLORS.secondary, borderRadius: '8px', padding: '4px' },
  modeBtn: { padding: '8px 20px', border: 'none', background: 'transparent', color: '#94A3B8', fontSize: '13px', fontWeight: '500', cursor: 'pointer', borderRadius: '6px', transition: 'all 0.2s' },
  modeBtnActive: { backgroundColor: COLORS.accent, color: '#fff' },
  headerRight: { display: 'flex', alignItems: 'center', gap: '16px' },
  viewToggle: { display: 'flex', backgroundColor: COLORS.secondary, borderRadius: '6px', padding: '2px' },
  viewBtn: { padding: '6px 12px', border: 'none', background: 'transparent', color: '#94A3B8', fontSize: '12px', fontWeight: '600', cursor: 'pointer', borderRadius: '4px' },
  viewBtnActive: { backgroundColor: '#334155', color: '#fff' },
  userBadge: { display: 'flex', flexDirection: 'column', alignItems: 'flex-end' },
  poweredBy: { fontSize: '10px', color: '#64748B', textTransform: 'uppercase', letterSpacing: '0.5px' },
  biddeedBrand: { fontSize: '13px', fontWeight: '600', color: COLORS.accent },
  mainContent: { display: 'flex', flex: 1, overflow: 'hidden' },
  sidebar: { width: '340px', backgroundColor: '#fff', borderRight: `1px solid ${COLORS.border}`, display: 'flex', flexDirection: 'column', overflow: 'hidden' },
  
  // Chat styles
  chatContainer: { display: 'flex', flexDirection: 'column', height: '100%' },
  chatMessages: { flex: 1, overflow: 'auto', padding: '16px', display: 'flex', flexDirection: 'column', gap: '12px' },
  messageWrapper: { display: 'flex', alignItems: 'flex-start', gap: '10px' },
  avatarAI: { width: '28px', height: '28px', display: 'flex', alignItems: 'center', justifyContent: 'center', background: `linear-gradient(135deg, ${COLORS.accent}, #8B5CF6)`, borderRadius: '6px', fontSize: '12px', fontWeight: '700', color: '#fff', flexShrink: 0 },
  messageBubble: { maxWidth: '85%', padding: '10px 14px', borderRadius: '14px', fontSize: '13px', lineHeight: 1.5 },
  aiBubble: { backgroundColor: COLORS.surface, border: `1px solid ${COLORS.border}`, borderBottomLeftRadius: '4px' },
  userBubble: { backgroundColor: COLORS.accent, color: '#fff', borderBottomRightRadius: '4px', marginLeft: 'auto' },
  typingIndicator: { display: 'flex', gap: '4px', padding: '4px 0' },
  typingDot: { width: '6px', height: '6px', backgroundColor: COLORS.textSecondary, borderRadius: '50%', animation: 'typingPulse 1s infinite' },
  quickPrompts: { display: 'flex', gap: '6px', padding: '8px 16px', flexWrap: 'wrap', borderTop: `1px solid ${COLORS.border}` },
  quickPromptBtn: { padding: '6px 12px', backgroundColor: COLORS.surface, border: `1px solid ${COLORS.border}`, borderRadius: '20px', color: COLORS.textSecondary, fontSize: '11px', cursor: 'pointer' },
  chatInputArea: { display: 'flex', gap: '10px', padding: '12px 16px', borderTop: `1px solid ${COLORS.border}`, backgroundColor: COLORS.surface },
  chatInput: { flex: 1, padding: '10px 14px', border: `1px solid ${COLORS.border}`, borderRadius: '12px', fontSize: '13px', resize: 'none', fontFamily: 'inherit', outline: 'none' },
  sendBtn: { width: '40px', height: '40px', display: 'flex', alignItems: 'center', justifyContent: 'center', backgroundColor: COLORS.accent, border: 'none', borderRadius: '10px', color: '#fff', cursor: 'pointer', flexShrink: 0 },
  
  // Form styles
  section: { padding: '16px 20px', borderBottom: `1px solid ${COLORS.border}` },
  sectionTitle: { display: 'flex', alignItems: 'center', gap: '8px', fontSize: '12px', fontWeight: '600', color: COLORS.textPrimary, marginBottom: '12px', textTransform: 'uppercase', letterSpacing: '0.5px' },
  sectionIcon: { fontSize: '14px' },
  inputRow: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' },
  inputGroup: { marginBottom: '10px' },
  label: { display: 'block', fontSize: '11px', fontWeight: '500', color: COLORS.textSecondary, marginBottom: '4px' },
  input: { width: '100%', padding: '10px 12px', border: `1px solid ${COLORS.border}`, borderRadius: '8px', fontSize: '14px', boxSizing: 'border-box' },
  select: { width: '100%', padding: '10px 12px', border: `1px solid ${COLORS.border}`, borderRadius: '8px', fontSize: '14px', boxSizing: 'border-box' },
  typologyGrid: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px' },
  typologyBtn: { display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '10px 6px', border: `2px solid ${COLORS.border}`, borderRadius: '10px', backgroundColor: '#fff', cursor: 'pointer', transition: 'all 0.2s' },
  typologyBtnActive: { borderWidth: '2px' },
  typologyIcon: { fontSize: '18px', marginBottom: '2px' },
  typologyName: { fontSize: '9px', fontWeight: '500', color: COLORS.textSecondary, textAlign: 'center' },
  paramGrid: { display: 'flex', flexDirection: 'column', gap: '10px' },
  paramGroup: { display: 'flex', alignItems: 'center', gap: '8px' },
  paramLabel: { flex: 1, fontSize: '12px', color: COLORS.textSecondary },
  paramInput: { width: '60px', padding: '8px', border: `1px solid ${COLORS.border}`, borderRadius: '6px', fontSize: '13px', textAlign: 'center' },
  paramSelect: { width: '120px', padding: '8px', border: `1px solid ${COLORS.border}`, borderRadius: '6px', fontSize: '12px' },
  paramUnit: { fontSize: '11px', color: COLORS.textSecondary, width: '40px' },
  generateBtn: { display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', margin: '16px 20px', padding: '14px', backgroundColor: COLORS.accent, color: '#fff', border: 'none', borderRadius: '10px', fontSize: '14px', fontWeight: '600', cursor: 'pointer' },
  generateBtnLoading: { backgroundColor: '#64748B' },
  
  // Map styles
  mapArea: { flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' },
  mapContainer: { flex: 1, position: 'relative', backgroundColor: '#E2E8F0' },
  mapPlaceholder: { width: '100%', height: '100%', position: 'relative', overflow: 'hidden' },
  gridPattern: { position: 'absolute', top: 0, left: 0, width: '100%', height: '100%' },
  mapOverlay: { position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, display: 'flex', flexDirection: 'column', zIndex: 10 },
  mapCenter: { flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' },
  sitePolygon: { width: '280px', height: '180px', border: '3px dashed', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center' },
  siteLabel: { fontSize: '22px', fontWeight: '700', textAlign: 'center' },
  mapInfo: { position: 'absolute', bottom: '16px', left: '16px', display: 'flex', gap: '16px', backgroundColor: 'rgba(255,255,255,0.95)', padding: '8px 16px', borderRadius: '8px', fontSize: '13px', color: COLORS.textSecondary, boxShadow: '0 2px 8px rgba(0,0,0,0.1)' },
  
  // Results styles
  resultsSidebar: { width: '340px', backgroundColor: '#fff', borderLeft: `1px solid ${COLORS.border}`, display: 'flex', flexDirection: 'column', overflow: 'auto' },
  resultsHeader: { padding: '16px', borderBottom: `1px solid ${COLORS.border}`, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' },
  resultsTitle: { display: 'flex', alignItems: 'center', gap: '12px' },
  resultsTitleText: { fontSize: '16px', fontWeight: '600', margin: 0 },
  resultsSubtitle: { fontSize: '11px', color: COLORS.textSecondary },
  metricsGrid: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', padding: '12px' },
  metricCard: { display: 'flex', alignItems: 'center', gap: '8px', padding: '10px', backgroundColor: COLORS.surface, borderRadius: '8px' },
  metricIcon: { fontSize: '18px' },
  metricContent: { display: 'flex', flexDirection: 'column' },
  metricValue: { fontSize: '14px', fontWeight: '600', color: COLORS.textPrimary },
  metricLabel: { fontSize: '10px', color: COLORS.textSecondary },
  unitMixResults: { padding: '12px', borderTop: `1px solid ${COLORS.border}` },
  sectionTitleSmall: { fontSize: '11px', fontWeight: '600', color: COLORS.textSecondary, marginBottom: '10px', textTransform: 'uppercase' },
  storageUnitGrid: { display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '6px' },
  storageUnitItem: { display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '8px', backgroundColor: COLORS.surface, borderRadius: '6px' },
  storageUnitSize: { fontSize: '10px', fontWeight: '600', color: '#F97316' },
  storageUnitCount: { fontSize: '14px', fontWeight: '700' },
  proFormaToggle: { display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%', padding: '12px 16px', border: 'none', borderTop: `1px solid ${COLORS.border}`, backgroundColor: COLORS.surface, cursor: 'pointer', fontSize: '13px', fontWeight: '500' },
  proFormaSection: { padding: '12px' },
  proFormaGrid: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' },
  proFormaItem: { display: 'flex', flexDirection: 'column', gap: '2px' },
  proFormaTotal: { gridColumn: 'span 2', backgroundColor: COLORS.surface, padding: '8px', borderRadius: '6px' },
  proFormaLabel: { fontSize: '10px', color: COLORS.textSecondary },
  proFormaValue: { fontSize: '14px', fontWeight: '600' },
  proFormaDivider: { height: '1px', backgroundColor: COLORS.border, margin: '12px 0' },
  profitBanner: { display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '14px', backgroundColor: '#DCFCE7', borderRadius: '10px', marginTop: '12px' },
  profitLabel: { fontSize: '10px', color: '#166534', textTransform: 'uppercase' },
  profitValue: { fontSize: '24px', fontWeight: '700', color: '#166534' },
  profitMargin: { fontSize: '12px', color: '#166534' },
  exportActions: { display: 'flex', gap: '6px', padding: '12px', borderTop: `1px solid ${COLORS.border}`, marginTop: 'auto' },
  exportBtn: { flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '4px', padding: '10px', border: `1px solid ${COLORS.border}`, borderRadius: '8px', backgroundColor: '#fff', fontSize: '11px', fontWeight: '500', cursor: 'pointer' },
  exportBtnPrimary: { backgroundColor: COLORS.accent, borderColor: COLORS.accent, color: '#fff' },
  emptyResults: { flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '40px', textAlign: 'center' },
  emptyIcon: { fontSize: '40px', marginBottom: '12px', opacity: 0.5 },
  emptyTitle: { fontSize: '14px', fontWeight: '600', marginBottom: '8px' },
  emptyText: { fontSize: '12px', color: COLORS.textSecondary, lineHeight: 1.5 },
  footer: { display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', padding: '10px', backgroundColor: COLORS.primary, color: '#64748B', fontSize: '11px' },
  footerDivider: { opacity: 0.5 },
  
  // Markdown styles
  table: { width: '100%', borderCollapse: 'collapse', margin: '8px 0', fontSize: '12px' },
  td: { padding: '6px 10px', borderBottom: `1px solid ${COLORS.border}` },
  mdH4: { fontSize: '13px', fontWeight: '600', margin: '10px 0 6px' },
  mdHr: { border: 'none', borderTop: `1px solid ${COLORS.border}`, margin: '10px 0' },
  mdP: { margin: '4px 0', fontSize: '13px' },
  mdLi: { padding: '2px 0 2px 8px', fontSize: '13px' },
};

// Keyframes
const styleSheet = document.createElement('style');
styleSheet.textContent = `
  @keyframes typingPulse { 0%, 100% { opacity: 0.3; } 50% { opacity: 1; } }
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
`;
document.head.appendChild(styleSheet);
