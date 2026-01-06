import React, { useState, useEffect, useRef, useCallback } from 'react';

// ============================================================================
// SPD.AI V2.1 - Chat-Driven Site Planning Intelligence
// ============================================================================
// Split-screen interface with NLP chatbot + real-time visualization
// Now with: Self-Storage, Senior Living, Medical Office, Mixed-Use
// © 2026 BidDeed.AI / Everest Capital USA - All Rights Reserved
// ============================================================================

// Design tokens
const THEME = {
  bg: {
    primary: '#0A0A0B',
    secondary: '#111113',
    tertiary: '#18181B',
    elevated: '#1F1F23',
    hover: '#27272A',
  },
  accent: {
    primary: '#3B82F6',
    secondary: '#60A5FA',
    success: '#10B981',
    warning: '#F59E0B',
    danger: '#EF4444',
    purple: '#8B5CF6',
    orange: '#F97316',
    teal: '#14B8A6',
  },
  text: {
    primary: '#FAFAFA',
    secondary: '#A1A1AA',
    muted: '#71717A',
    inverse: '#09090B',
  },
  border: {
    subtle: '#27272A',
    default: '#3F3F46',
    strong: '#52525B',
  },
  gradient: {
    brand: 'linear-gradient(135deg, #3B82F6 0%, #8B5CF6 50%, #EC4899 100%)',
    subtle: 'linear-gradient(180deg, rgba(59,130,246,0.1) 0%, transparent 100%)',
  }
};

// Zoning data
const BREVARD_ZONING = {
  'R-1': { name: 'Single Family Residential', maxDensity: 4, maxHeight: 35 },
  'R-2': { name: 'Medium Density Residential', maxDensity: 10, maxHeight: 45 },
  'R-3': { name: 'High Density Residential', maxDensity: 20, maxHeight: 65 },
  'C-1': { name: 'Neighborhood Commercial', maxFAR: 0.5, maxHeight: 35 },
  'C-2': { name: 'General Commercial', maxFAR: 1.0, maxHeight: 50 },
  'I-1': { name: 'Light Industrial', maxFAR: 0.6, maxHeight: 45 },
  'PUD': { name: 'Planned Unit Development', maxDensity: 'Varies', maxHeight: 'Varies' }
};

// Self-Storage Unit Mix (industry standard)
const STORAGE_UNIT_MIX = {
  '5x5': { sf: 25, pct: 10, rentPerSF: 2.00 },
  '5x10': { sf: 50, pct: 25, rentPerSF: 1.75 },
  '10x10': { sf: 100, pct: 30, rentPerSF: 1.50 },
  '10x15': { sf: 150, pct: 15, rentPerSF: 1.35 },
  '10x20': { sf: 200, pct: 12, rentPerSF: 1.25 },
  '10x30': { sf: 300, pct: 8, rentPerSF: 1.15 },
};

// NLP Intent patterns - EXPANDED
const INTENT_PATTERNS = {
  analyze_site: [
    /analyze\s+(?:a\s+)?(\d+(?:\.\d+)?)\s*(?:acre|ac)/i,
    /(?:i have|got|looking at)\s+(?:a\s+)?(\d+(?:\.\d+)?)\s*(?:acre|ac)/i,
    /(\d+(?:\.\d+)?)\s*(?:acre|ac)\s+(?:site|parcel|lot|property)/i,
    /site\s+(?:is\s+)?(\d+(?:\.\d+)?)\s*(?:acre|ac)/i,
  ],
  set_zoning: [
    /zoning\s+(?:is\s+)?([A-Z]-?\d|PUD)/i,
    /([A-Z]-?\d|PUD)\s+zon(?:ing|ed)/i,
    /zone(?:d)?\s+(?:as\s+)?([A-Z]-?\d|PUD)/i,
  ],
  typology: [
    /(?:build|develop|want|planning)\s+(?:a\s+)?(?:an?\s+)?(multi-?family|apartment|industrial|warehouse|single.?family|retail|hotel|self.?storage|storage|mini.?storage|senior|assisted|memory.?care|medical|office|mixed.?use|flex)/i,
    /(multi-?family|apartment|industrial|warehouse|single.?family|retail|hotel|self.?storage|storage|mini.?storage|senior|assisted|memory.?care|medical|office|mixed.?use|flex)\s+(?:development|project|building|facility|center)/i,
  ],
  units: [
    /(\d+)\s+units?/i,
    /(?:want|need|target(?:ing)?)\s+(\d+)\s+units?/i,
  ],
  beds: [
    /(\d+)\s+beds?/i,
    /(?:want|need|target(?:ing)?)\s+(\d+)\s+beds?/i,
  ],
  parking: [
    /(\d+(?:\.\d+)?)\s+parking\s+(?:spaces?\s+)?(?:per\s+unit|ratio)/i,
    /parking\s+(?:ratio\s+(?:of\s+)?)?(\d+(?:\.\d+)?)/i,
  ],
  stories: [
    /(\d+)\s+(?:story|stories|floors?)/i,
    /(?:multi.?story|two.?story|three.?story|single.?story)/i,
  ],
  climate: [
    /climate.?control(?:led)?/i,
    /(\d+)%?\s+climate/i,
  ],
  proforma: [
    /pro\s*forma/i,
    /financial|economics|numbers|costs?|revenue/i,
    /(?:what(?:'s| is) the|show me|calculate)\s+(?:profit|roi|return|yield|noi)/i,
  ],
  greeting: [
    /^(?:hi|hello|hey|good\s+(?:morning|afternoon|evening))/i,
    /^(?:what can you do|help|how does this work)/i,
  ],
  export: [
    /export|download|pdf|report|save/i,
  ]
};

// Sample responses
const GREETINGS = [
  "Hey! I'm SPD.AI, your site planning assistant. Tell me about your site - acreage, zoning, and what you want to build. I'll generate a feasibility analysis in seconds.",
  "Hello! Ready to analyze a site? Just tell me the basics: **acreage**, **zoning**, and **development type** (apartments, self-storage, industrial, senior living, etc.)",
  "Hi there! I help developers analyze site feasibility instantly. What's your site look like? Give me acreage and zoning to start.",
];

// Typology configurations
const TYPOLOGY_INFO = {
  multifamily: { label: 'Multi-Family', icon: '🏢', color: '#3B82F6' },
  industrial: { label: 'Industrial/Warehouse', icon: '🏭', color: '#6366F1' },
  'single-family': { label: 'Single-Family', icon: '🏠', color: '#10B981' },
  retail: { label: 'Retail', icon: '🛒', color: '#F59E0B' },
  hotel: { label: 'Hotel', icon: '🏨', color: '#EC4899' },
  'self-storage': { label: 'Self-Storage', icon: '📦', color: '#F97316' },
  senior: { label: 'Senior Living', icon: '🏥', color: '#14B8A6' },
  medical: { label: 'Medical Office', icon: '⚕️', color: '#EF4444' },
  'mixed-use': { label: 'Mixed-Use', icon: '🏙️', color: '#8B5CF6' },
};

// ============================================================================
// MAIN APP COMPONENT
// ============================================================================

export default function SPDAIChatApp() {
  // Chat state
  const [messages, setMessages] = useState([
    {
      id: 1,
      role: 'assistant',
      content: GREETINGS[Math.floor(Math.random() * GREETINGS.length)],
      timestamp: new Date(),
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  
  // Site state
  const [siteConfig, setSiteConfig] = useState({
    acreage: null,
    zoning: null,
    typology: null,
    units: null,
    beds: null,
    parkingRatio: 1.5,
    stories: null,
    climateControlled: 50, // percentage for self-storage
  });
  const [feasibility, setFeasibility] = useState(null);
  const [activeTab, setActiveTab] = useState('preview');
  
  const chatEndRef = useRef(null);
  const inputRef = useRef(null);

  // Auto-scroll chat
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // NLP Parser
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

  const generateFeasibility = useCallback((config) => {
    if (!config.acreage || !config.typology) return null;

    const acreage = parseFloat(config.acreage);
    const siteSquareFeet = acreage * 43560;
    const zoning = BREVARD_ZONING[config.zoning] || BREVARD_ZONING['C-2'];
    
    let results = {
      acreage,
      siteSquareFeet,
      zoning: config.zoning || 'C-2',
      typology: config.typology,
    };

    // =========================================
    // SELF-STORAGE CALCULATIONS
    // =========================================
    if (config.typology === 'self-storage' || config.typology === 'storage') {
      const stories = config.stories || 1;
      const lotCoverage = stories === 1 ? 0.40 : 0.35; // Single-story spreads out more
      const buildingFootprint = siteSquareFeet * lotCoverage;
      const grossBuildingSF = buildingFootprint * stories;
      const netRentableSF = Math.round(grossBuildingSF * 0.85); // 85% efficiency
      const climateControlledPct = config.climateControlled || 50;
      const climateSF = Math.round(netRentableSF * (climateControlledPct / 100));
      const nonClimateSF = netRentableSF - climateSF;
      
      // Calculate unit count and mix
      let totalUnits = 0;
      const unitBreakdown = {};
      for (const [size, data] of Object.entries(STORAGE_UNIT_MIX)) {
        const unitCount = Math.round((netRentableSF * data.pct / 100) / data.sf);
        unitBreakdown[size] = unitCount;
        totalUnits += unitCount;
      }

      // Calculate monthly revenue
      let monthlyRevenue = 0;
      for (const [size, data] of Object.entries(STORAGE_UNIT_MIX)) {
        const climateUnits = Math.round(unitBreakdown[size] * (climateControlledPct / 100));
        const nonClimateUnits = unitBreakdown[size] - climateUnits;
        // Climate controlled gets 30% premium
        monthlyRevenue += climateUnits * data.sf * data.rentPerSF * 1.30;
        monthlyRevenue += nonClimateUnits * data.sf * data.rentPerSF;
      }
      const annualRevenue = monthlyRevenue * 12;
      const occupancy = 0.88; // Industry average 88%
      const effectiveRevenue = annualRevenue * occupancy;
      
      // Pro forma
      const landCost = acreage * 125000;
      const hardCostPerSF = stories === 1 ? 55 : 85; // Multi-story costs more
      const hardCosts = grossBuildingSF * hardCostPerSF;
      const softCosts = hardCosts * 0.18;
      const totalCost = landCost + hardCosts + softCosts;
      const noi = effectiveRevenue * 0.60; // 60% NOI margin (self-storage is efficient)
      const capRate = 0.065;
      const estimatedValue = noi / capRate;

      results = {
        ...results,
        typologyLabel: 'Self-Storage',
        icon: '📦',
        stories,
        grossBuildingSF: Math.round(grossBuildingSF),
        netRentableSF,
        totalUnits,
        unitBreakdown,
        climateSF,
        nonClimateSF,
        climateControlledPct,
        lotCoverage: `${(lotCoverage * 100).toFixed(0)}%`,
        efficiency: '85%',
        occupancy: '88%',
        avgRentPerSF: (monthlyRevenue / netRentableSF).toFixed(2),
        // Pro forma
        landCost,
        hardCosts,
        softCosts,
        totalCost,
        monthlyRevenue: Math.round(monthlyRevenue),
        annualRevenue: Math.round(annualRevenue),
        effectiveRevenue: Math.round(effectiveRevenue),
        noi: Math.round(noi),
        yieldOnCost: ((noi / totalCost) * 100).toFixed(2),
        capRate: '6.5%',
        estimatedValue: Math.round(estimatedValue),
        profit: Math.round(estimatedValue - totalCost),
        margin: (((estimatedValue - totalCost) / totalCost) * 100).toFixed(1),
      };
    }

    // =========================================
    // MULTI-FAMILY CALCULATIONS
    // =========================================
    else if (config.typology === 'multifamily' || config.typology === 'apartment') {
      const maxUnits = config.units || Math.floor(acreage * (zoning.maxDensity || 10));
      const avgUnitSF = 875;
      const grossSF = Math.round(maxUnits * avgUnitSF * 1.15);
      const buildableArea = siteSquareFeet * 0.65;
      const floors = Math.min(Math.ceil(grossSF / buildableArea), Math.floor((zoning.maxHeight || 45) / 10));
      const parkingSpaces = Math.ceil(maxUnits * (config.parkingRatio || 1.5));

      results = {
        ...results,
        typologyLabel: 'Multi-Family',
        icon: '🏢',
        units: maxUnits,
        grossSF,
        floors,
        parkingSpaces,
        density: (maxUnits / acreage).toFixed(1),
        far: (grossSF / siteSquareFeet).toFixed(2),
        lotCoverage: '65%',
        unitMix: {
          studio: Math.round(maxUnits * 0.10),
          oneBed: Math.round(maxUnits * 0.40),
          twoBed: Math.round(maxUnits * 0.35),
          threeBed: Math.round(maxUnits * 0.15),
        },
        landCost: acreage * 150000,
        hardCosts: grossSF * 185,
        softCosts: grossSF * 185 * 0.25,
        totalCost: acreage * 150000 + grossSF * 185 * 1.25,
        annualRevenue: maxUnits * 1650 * 12,
        noi: maxUnits * 1650 * 12 * 0.55,
        yieldOnCost: ((maxUnits * 1650 * 12 * 0.55) / (acreage * 150000 + grossSF * 185 * 1.25) * 100).toFixed(2),
        estimatedValue: (maxUnits * 1650 * 12 * 0.55) / 0.055,
      };
      results.profit = results.estimatedValue - results.totalCost;
      results.margin = ((results.profit / results.totalCost) * 100).toFixed(1);
    }

    // =========================================
    // INDUSTRIAL CALCULATIONS
    // =========================================
    else if (config.typology === 'industrial' || config.typology === 'warehouse') {
      const warehouseSF = Math.round(siteSquareFeet * 0.55);
      const dockDoors = Math.ceil(warehouseSF / 10000);
      const carParking = Math.ceil(warehouseSF / 2000);

      results = {
        ...results,
        typologyLabel: 'Industrial/Warehouse',
        icon: '🏭',
        warehouseSF,
        clearHeight: 32,
        dockDoors,
        trailerSpaces: dockDoors * 2,
        carParking,
        lotCoverage: '55%',
        far: (warehouseSF / siteSquareFeet).toFixed(2),
        landCost: acreage * 100000,
        hardCosts: warehouseSF * 95,
        softCosts: warehouseSF * 95 * 0.20,
        totalCost: acreage * 100000 + warehouseSF * 95 * 1.20,
        annualRevenue: warehouseSF * 9.50,
        noi: warehouseSF * 9.50 * 0.92,
        yieldOnCost: ((warehouseSF * 9.50 * 0.92) / (acreage * 100000 + warehouseSF * 95 * 1.20) * 100).toFixed(2),
        estimatedValue: (warehouseSF * 9.50 * 0.92) / 0.065,
      };
      results.profit = results.estimatedValue - results.totalCost;
      results.margin = ((results.profit / results.totalCost) * 100).toFixed(1);
    }

    // =========================================
    // SINGLE-FAMILY CALCULATIONS
    // =========================================
    else if (config.typology === 'single-family' || config.typology === 'singlefamily') {
      const avgLotSize = 7500;
      const usableLand = siteSquareFeet * 0.70;
      const totalLots = Math.floor(usableLand / avgLotSize);

      results = {
        ...results,
        typologyLabel: 'Single-Family',
        icon: '🏠',
        totalLots,
        avgLotSize,
        avgHomeSize: 2200,
        totalHomeSF: totalLots * 2200,
        density: (totalLots / acreage).toFixed(1),
        landCost: acreage * 125000,
        hardCosts: totalLots * 2200 * 165,
        softCosts: totalLots * 2200 * 165 * 0.15,
        totalCost: acreage * 125000 + totalLots * 2200 * 165 * 1.15,
        totalRevenue: totalLots * 425000,
      };
      results.profit = results.totalRevenue - results.totalCost;
      results.margin = ((results.profit / results.totalCost) * 100).toFixed(1);
    }

    // =========================================
    // SENIOR LIVING CALCULATIONS
    // =========================================
    else if (config.typology === 'senior' || config.typology === 'assisted') {
      const beds = config.beds || Math.floor(acreage * 25); // 25 beds per acre typical
      const avgUnitSF = 450; // Smaller units for senior
      const commonAreaRatio = 0.35; // More common area
      const grossSF = Math.round(beds * avgUnitSF / (1 - commonAreaRatio));
      const buildableArea = siteSquareFeet * 0.40;
      const floors = Math.min(Math.ceil(grossSF / buildableArea), 4);
      const parkingSpaces = Math.ceil(beds * 0.5); // Lower parking for senior

      // Revenue: $4,500/month average for assisted living
      const monthlyRate = 4500;
      const occupancy = 0.90;

      results = {
        ...results,
        typologyLabel: 'Senior Living',
        icon: '🏥',
        beds,
        grossSF,
        floors,
        parkingSpaces,
        density: (beds / acreage).toFixed(1),
        lotCoverage: '40%',
        commonAreaSF: Math.round(grossSF * commonAreaRatio),
        unitSF: Math.round(grossSF * (1 - commonAreaRatio)),
        landCost: acreage * 175000,
        hardCosts: grossSF * 225, // Higher finish
        softCosts: grossSF * 225 * 0.28,
        totalCost: acreage * 175000 + grossSF * 225 * 1.28,
        monthlyRevenue: Math.round(beds * monthlyRate * occupancy),
        annualRevenue: Math.round(beds * monthlyRate * 12 * occupancy),
        noi: Math.round(beds * monthlyRate * 12 * occupancy * 0.35), // 35% NOI (labor intensive)
        yieldOnCost: ((beds * monthlyRate * 12 * occupancy * 0.35) / (acreage * 175000 + grossSF * 225 * 1.28) * 100).toFixed(2),
        capRate: '7.0%',
        estimatedValue: (beds * monthlyRate * 12 * occupancy * 0.35) / 0.07,
      };
      results.profit = results.estimatedValue - results.totalCost;
      results.margin = ((results.profit / results.totalCost) * 100).toFixed(1);
    }

    // =========================================
    // MEDICAL OFFICE CALCULATIONS
    // =========================================
    else if (config.typology === 'medical' || config.typology === 'office') {
      const grossSF = Math.round(siteSquareFeet * 0.35 * (config.stories || 2));
      const parkingSpaces = Math.ceil(grossSF / 250); // Higher parking for medical
      const rentPerSF = 28; // NNN

      results = {
        ...results,
        typologyLabel: 'Medical Office',
        icon: '⚕️',
        grossSF,
        floors: config.stories || 2,
        parkingSpaces,
        parkingRatio: (parkingSpaces / (grossSF / 1000)).toFixed(1),
        lotCoverage: '35%',
        far: (grossSF / siteSquareFeet).toFixed(2),
        landCost: acreage * 200000,
        hardCosts: grossSF * 275, // Medical TI is expensive
        softCosts: grossSF * 275 * 0.22,
        totalCost: acreage * 200000 + grossSF * 275 * 1.22,
        annualRevenue: grossSF * rentPerSF,
        noi: grossSF * rentPerSF * 0.88, // NNN leases
        yieldOnCost: ((grossSF * rentPerSF * 0.88) / (acreage * 200000 + grossSF * 275 * 1.22) * 100).toFixed(2),
        capRate: '6.25%',
        estimatedValue: (grossSF * rentPerSF * 0.88) / 0.0625,
      };
      results.profit = results.estimatedValue - results.totalCost;
      results.margin = ((results.profit / results.totalCost) * 100).toFixed(1);
    }

    // =========================================
    // RETAIL CALCULATIONS
    // =========================================
    else if (config.typology === 'retail') {
      const grossSF = Math.round(siteSquareFeet * 0.25);
      const parkingSpaces = Math.ceil(grossSF / 200);
      const rentPerSF = 22;

      results = {
        ...results,
        typologyLabel: 'Retail',
        icon: '🛒',
        grossSF,
        floors: 1,
        parkingSpaces,
        lotCoverage: '25%',
        padSites: Math.floor(acreage / 1.5),
        landCost: acreage * 175000,
        hardCosts: grossSF * 165,
        softCosts: grossSF * 165 * 0.18,
        totalCost: acreage * 175000 + grossSF * 165 * 1.18,
        annualRevenue: grossSF * rentPerSF,
        noi: grossSF * rentPerSF * 0.85,
        yieldOnCost: ((grossSF * rentPerSF * 0.85) / (acreage * 175000 + grossSF * 165 * 1.18) * 100).toFixed(2),
        capRate: '6.75%',
        estimatedValue: (grossSF * rentPerSF * 0.85) / 0.0675,
      };
      results.profit = results.estimatedValue - results.totalCost;
      results.margin = ((results.profit / results.totalCost) * 100).toFixed(1);
    }

    // =========================================
    // HOTEL CALCULATIONS
    // =========================================
    else if (config.typology === 'hotel') {
      const rooms = config.units || Math.floor(acreage * 60);
      const avgRoomSF = 375;
      const grossSF = Math.round(rooms * avgRoomSF * 1.35); // Public areas
      const floors = Math.min(Math.ceil(grossSF / (siteSquareFeet * 0.35)), 5);
      const parkingSpaces = Math.ceil(rooms * 0.8);
      const adr = 145; // Average daily rate
      const occupancy = 0.68;
      const revPAR = adr * occupancy;

      results = {
        ...results,
        typologyLabel: 'Hotel',
        icon: '🏨',
        rooms,
        grossSF,
        floors,
        parkingSpaces,
        adr,
        occupancy: '68%',
        revPAR: revPAR.toFixed(2),
        landCost: acreage * 200000,
        hardCosts: grossSF * 195,
        softCosts: grossSF * 195 * 0.25,
        totalCost: acreage * 200000 + grossSF * 195 * 1.25,
        annualRevenue: Math.round(rooms * revPAR * 365),
        noi: Math.round(rooms * revPAR * 365 * 0.35), // Hotels have thin margins
        yieldOnCost: ((rooms * revPAR * 365 * 0.35) / (acreage * 200000 + grossSF * 195 * 1.25) * 100).toFixed(2),
        capRate: '8.0%',
        estimatedValue: (rooms * revPAR * 365 * 0.35) / 0.08,
      };
      results.profit = results.estimatedValue - results.totalCost;
      results.margin = ((results.profit / results.totalCost) * 100).toFixed(1);
    }

    return results;
  }, []);

  // ============================================================================
  // RESPONSE GENERATION
  // ============================================================================

  const generateResponse = useCallback((text, currentConfig) => {
    const { intents, params } = parseIntent(text);
    let response = '';
    let updatedConfig = { ...currentConfig };

    // Handle greetings
    if (intents.includes('greeting') && intents.length === 1) {
      return {
        response: GREETINGS[Math.floor(Math.random() * GREETINGS.length)],
        config: updatedConfig,
      };
    }

    // Extract site info
    if (intents.includes('analyze_site')) {
      updatedConfig.acreage = parseFloat(params.analyze_site);
      response += `Got it - **${updatedConfig.acreage} acre** site. `;
    }

    if (intents.includes('set_zoning')) {
      const zoneCode = params.set_zoning.toUpperCase();
      if (BREVARD_ZONING[zoneCode]) {
        updatedConfig.zoning = zoneCode;
        const zone = BREVARD_ZONING[zoneCode];
        response += `Zoning set to **${zoneCode}** (${zone.name}). `;
      }
    }

    if (intents.includes('typology')) {
      const typologyMap = {
        'multi-family': 'multifamily',
        'multifamily': 'multifamily',
        'apartment': 'multifamily',
        'industrial': 'industrial',
        'warehouse': 'industrial',
        'single-family': 'single-family',
        'singlefamily': 'single-family',
        'retail': 'retail',
        'hotel': 'hotel',
        'self-storage': 'self-storage',
        'selfstorage': 'self-storage',
        'storage': 'self-storage',
        'mini-storage': 'self-storage',
        'ministorage': 'self-storage',
        'senior': 'senior',
        'assisted': 'senior',
        'memory-care': 'senior',
        'memorycare': 'senior',
        'medical': 'medical',
        'office': 'medical',
        'mixed-use': 'mixed-use',
        'mixeduse': 'mixed-use',
        'flex': 'industrial',
      };
      const rawTypology = params.typology.toLowerCase().replace(/\s+/g, '-');
      updatedConfig.typology = typologyMap[rawTypology] || rawTypology;
      const info = TYPOLOGY_INFO[updatedConfig.typology];
      response += `Development type: **${info?.label || updatedConfig.typology}** ${info?.icon || ''}. `;
    }

    if (intents.includes('units')) {
      updatedConfig.units = parseInt(params.units);
      response += `Targeting **${updatedConfig.units} units**. `;
    }

    if (intents.includes('beds')) {
      updatedConfig.beds = parseInt(params.beds);
      response += `Targeting **${updatedConfig.beds} beds**. `;
    }

    if (intents.includes('parking')) {
      updatedConfig.parkingRatio = parseFloat(params.parking);
      response += `Parking ratio: **${updatedConfig.parkingRatio}** spaces/unit. `;
    }

    if (intents.includes('stories')) {
      const storiesMatch = text.match(/(\d+)\s+(?:story|stories|floors?)/i);
      if (storiesMatch) {
        updatedConfig.stories = parseInt(storiesMatch[1]);
        response += `**${updatedConfig.stories}-story** building. `;
      } else if (text.match(/multi.?story/i)) {
        updatedConfig.stories = 3;
        response += `**Multi-story** (3 floors). `;
      } else if (text.match(/single.?story/i)) {
        updatedConfig.stories = 1;
        response += `**Single-story** building. `;
      }
    }

    if (intents.includes('climate')) {
      const climateMatch = text.match(/(\d+)%?\s+climate/i);
      if (climateMatch) {
        updatedConfig.climateControlled = parseInt(climateMatch[1]);
        response += `**${updatedConfig.climateControlled}%** climate controlled. `;
      } else {
        updatedConfig.climateControlled = 100;
        response += `**100%** climate controlled. `;
      }
    }

    // Generate feasibility if we have enough info
    if (updatedConfig.acreage && updatedConfig.typology) {
      const results = generateFeasibility(updatedConfig);
      if (results) {
        response += '\n\n---\n\n';
        response += `### ${results.icon || '📊'} ${results.typologyLabel} Feasibility\n\n`;
        
        // Build metrics table based on typology
        response += `| Metric | Value |\n|--------|-------|\n`;
        
        if (results.typologyLabel === 'Self-Storage') {
          response += `| **Net Rentable SF** | ${results.netRentableSF.toLocaleString()} |\n`;
          response += `| **Total Units** | ${results.totalUnits} |\n`;
          response += `| **Stories** | ${results.stories} |\n`;
          response += `| **Climate Controlled** | ${results.climateControlledPct}% (${results.climateSF.toLocaleString()} SF) |\n`;
          response += `| **Avg Rent/SF** | $${results.avgRentPerSF}/mo |\n`;
          response += `| **Monthly Revenue** | $${results.monthlyRevenue.toLocaleString()} |\n`;
          response += `\n**Unit Mix:**\n`;
          for (const [size, count] of Object.entries(results.unitBreakdown)) {
            response += `• ${size}: ${count} units\n`;
          }
        } else if (results.typologyLabel === 'Multi-Family') {
          response += `| **Units** | ${results.units} |\n`;
          response += `| **Gross SF** | ${results.grossSF.toLocaleString()} |\n`;
          response += `| **Stories** | ${results.floors} |\n`;
          response += `| **Parking** | ${results.parkingSpaces} spaces |\n`;
          response += `| **Density** | ${results.density} units/acre |\n`;
          response += `| **FAR** | ${results.far} |\n`;
          response += `\n**Unit Mix:** ${results.unitMix.studio} Studio, ${results.unitMix.oneBed} 1BR, ${results.unitMix.twoBed} 2BR, ${results.unitMix.threeBed} 3BR\n`;
        } else if (results.typologyLabel === 'Industrial/Warehouse') {
          response += `| **Warehouse SF** | ${results.warehouseSF.toLocaleString()} |\n`;
          response += `| **Clear Height** | ${results.clearHeight}' |\n`;
          response += `| **Dock Doors** | ${results.dockDoors} |\n`;
          response += `| **Trailer Spaces** | ${results.trailerSpaces} |\n`;
          response += `| **Car Parking** | ${results.carParking} |\n`;
        } else if (results.typologyLabel === 'Senior Living') {
          response += `| **Beds** | ${results.beds} |\n`;
          response += `| **Gross SF** | ${results.grossSF.toLocaleString()} |\n`;
          response += `| **Stories** | ${results.floors} |\n`;
          response += `| **Parking** | ${results.parkingSpaces} spaces |\n`;
          response += `| **Common Area** | ${results.commonAreaSF.toLocaleString()} SF |\n`;
          response += `| **Density** | ${results.density} beds/acre |\n`;
        } else if (results.typologyLabel === 'Medical Office') {
          response += `| **Gross SF** | ${results.grossSF.toLocaleString()} |\n`;
          response += `| **Stories** | ${results.floors} |\n`;
          response += `| **Parking** | ${results.parkingSpaces} spaces |\n`;
          response += `| **Parking Ratio** | ${results.parkingRatio}/1,000 SF |\n`;
          response += `| **FAR** | ${results.far} |\n`;
        } else if (results.typologyLabel === 'Hotel') {
          response += `| **Rooms** | ${results.rooms} |\n`;
          response += `| **Gross SF** | ${results.grossSF.toLocaleString()} |\n`;
          response += `| **Stories** | ${results.floors} |\n`;
          response += `| **ADR** | $${results.adr} |\n`;
          response += `| **Occupancy** | ${results.occupancy} |\n`;
          response += `| **RevPAR** | $${results.revPAR} |\n`;
        } else if (results.typologyLabel === 'Single-Family') {
          response += `| **Total Lots** | ${results.totalLots} |\n`;
          response += `| **Avg Lot Size** | ${results.avgLotSize.toLocaleString()} SF |\n`;
          response += `| **Avg Home Size** | ${results.avgHomeSize.toLocaleString()} SF |\n`;
          response += `| **Density** | ${results.density} lots/acre |\n`;
        } else if (results.typologyLabel === 'Retail') {
          response += `| **Gross SF** | ${results.grossSF.toLocaleString()} |\n`;
          response += `| **Parking** | ${results.parkingSpaces} spaces |\n`;
          response += `| **Pad Sites** | ${results.padSites} |\n`;
          response += `| **Lot Coverage** | ${results.lotCoverage} |\n`;
        }

        response += `\n💰 **Estimated Profit:** $${(results.profit / 1000000).toFixed(2)}M (${results.margin}% margin)`;
        response += `\n\n*View the preview panel for visualization →*`;

        return { response, config: updatedConfig, feasibility: results };
      }
    }

    // Handle pro forma request
    if (intents.includes('proforma') && currentConfig.acreage && currentConfig.typology) {
      const results = generateFeasibility(currentConfig);
      if (results) {
        response = `### 💰 Pro Forma Analysis - ${results.typologyLabel}\n\n`;
        response += `| Cost Category | Amount |\n|---------------|--------|\n`;
        response += `| Land | $${(results.landCost / 1000000).toFixed(2)}M |\n`;
        response += `| Hard Costs | $${(results.hardCosts / 1000000).toFixed(2)}M |\n`;
        response += `| Soft Costs | $${(results.softCosts / 1000000).toFixed(2)}M |\n`;
        response += `| **Total Cost** | **$${(results.totalCost / 1000000).toFixed(2)}M** |\n\n`;
        
        if (results.noi) {
          response += `| Revenue | Amount |\n|---------|--------|\n`;
          if (results.monthlyRevenue) {
            response += `| Monthly Revenue | $${(results.monthlyRevenue).toLocaleString()} |\n`;
          }
          response += `| Annual Revenue | $${(results.annualRevenue / 1000000).toFixed(2)}M |\n`;
          response += `| NOI | $${(results.noi / 1000000).toFixed(2)}M |\n`;
          response += `| Yield on Cost | ${results.yieldOnCost}% |\n`;
          response += `| Cap Rate | ${results.capRate} |\n`;
          response += `| Estimated Value | $${(results.estimatedValue / 1000000).toFixed(2)}M |\n\n`;
        }
        
        response += `### 🎯 **Profit: $${(results.profit / 1000000).toFixed(2)}M** (${results.margin}% margin)`;
        
        return { response, config: currentConfig, feasibility: results };
      }
    }

    // Handle export
    if (intents.includes('export')) {
      response = `📄 **Export Options:**\n\n`;
      response += `• **PDF Report** - Full feasibility analysis\n`;
      response += `• **Excel Pro Forma** - Editable financial model\n`;
      response += `• **Share Link** - Collaborate with team\n\n`;
      response += `*Click the export buttons in the preview panel →*`;
      return { response, config: currentConfig };
    }

    // If we couldn't understand
    if (!response) {
      if (!currentConfig.acreage) {
        response = `I need a bit more info to help. What's the **acreage** of your site? You can say something like "I have a 5 acre site" or "analyze a 10 acre parcel."`;
      } else if (!currentConfig.typology) {
        response = `Got your ${currentConfig.acreage} acre site. What do you want to build?\n\n`;
        response += `• **Multi-family** (apartments, condos)\n`;
        response += `• **Self-storage** 📦\n`;
        response += `• **Industrial** (warehouse, logistics)\n`;
        response += `• **Single-family** (subdivision, townhomes)\n`;
        response += `• **Senior Living** (assisted living, memory care)\n`;
        response += `• **Medical Office**\n`;
        response += `• **Retail** (shopping center)\n`;
        response += `• **Hotel**`;
      } else {
        response = `I'm not sure what you're asking. Try:\n\n`;
        response += `• "Show me the pro forma"\n`;
        response += `• "Change to 3-story"\n`;
        response += `• "50% climate controlled"\n`;
        response += `• "Export the report"`;
      }
    }

    return { response, config: updatedConfig };
  }, [parseIntent, generateFeasibility]);

  // Handle send message
  const handleSend = useCallback(() => {
    if (!inputValue.trim()) return;

    const userMessage = {
      id: messages.length + 1,
      role: 'user',
      content: inputValue.trim(),
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsTyping(true);

    setTimeout(() => {
      const { response, config, feasibility: newFeasibility } = generateResponse(inputValue, siteConfig);
      
      if (config) {
        setSiteConfig(config);
      }
      
      if (newFeasibility) {
        setFeasibility(newFeasibility);
      }

      const assistantMessage = {
        id: messages.length + 2,
        role: 'assistant',
        content: response,
        timestamp: new Date(),
      };

      setMessages(prev => [...prev, assistantMessage]);
      setIsTyping(false);
    }, 800 + Math.random() * 400);
  }, [inputValue, messages, siteConfig, generateResponse]);

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // Quick actions - EXPANDED
  const quickActions = [
    { label: '📦 5ac self-storage', action: 'Analyze a 5 acre site for self-storage, 3-story, 50% climate controlled' },
    { label: '🏢 5ac apartments', action: 'Analyze a 5 acre site for multifamily development, R-2 zoning' },
    { label: '🏭 10ac industrial', action: 'I have a 10 acre industrial site, I-1 zoning' },
    { label: '🏥 3ac senior living', action: 'Build senior living on 3 acres' },
  ];

  return (
    <div style={styles.container}>
      {/* Left Panel - Chat */}
      <div style={styles.chatPanel}>
        <div style={styles.chatHeader}>
          <div style={styles.logoContainer}>
            <div style={styles.logoIcon}>◆</div>
            <div style={styles.logoText}>
              <span style={styles.logoTitle}>SPD.AI</span>
              <span style={styles.logoSubtitle}>Site Planning Intelligence</span>
            </div>
          </div>
          <div style={styles.statusBadge}>
            <span style={styles.statusDot}></span>
            Online
          </div>
        </div>

        <div style={styles.messagesContainer}>
          {messages.map((msg) => (
            <div
              key={msg.id}
              style={{
                ...styles.messageWrapper,
                justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start',
              }}
            >
              {msg.role === 'assistant' && (
                <div style={styles.avatarAI}>◆</div>
              )}
              <div
                style={{
                  ...styles.messageBubble,
                  ...(msg.role === 'user' ? styles.userBubble : styles.aiBubble),
                }}
              >
                <MessageContent content={msg.content} />
              </div>
            </div>
          ))}
          
          {isTyping && (
            <div style={styles.messageWrapper}>
              <div style={styles.avatarAI}>◆</div>
              <div style={{ ...styles.messageBubble, ...styles.aiBubble }}>
                <div style={styles.typingIndicator}>
                  <span style={styles.typingDot}></span>
                  <span style={{ ...styles.typingDot, animationDelay: '0.2s' }}></span>
                  <span style={{ ...styles.typingDot, animationDelay: '0.4s' }}></span>
                </div>
              </div>
            </div>
          )}
          
          <div ref={chatEndRef} />
        </div>

        {messages.length <= 2 && (
          <div style={styles.quickActions}>
            {quickActions.map((qa, i) => (
              <button
                key={i}
                style={styles.quickActionBtn}
                onClick={() => {
                  setInputValue(qa.action);
                  setTimeout(() => handleSend(), 100);
                }}
              >
                {qa.label}
              </button>
            ))}
          </div>
        )}

        <div style={styles.inputArea}>
          <div style={styles.inputWrapper}>
            <textarea
              ref={inputRef}
              style={styles.input}
              placeholder="Describe your site... (e.g., '5 acres for self-storage')"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              rows={1}
            />
            <button
              style={{
                ...styles.sendBtn,
                opacity: inputValue.trim() ? 1 : 0.5,
              }}
              onClick={handleSend}
              disabled={!inputValue.trim()}
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M22 2L11 13M22 2L15 22L11 13L2 9L22 2Z" />
              </svg>
            </button>
          </div>
          <div style={styles.inputHint}>
            Press Enter to send • Shift+Enter for new line
          </div>
        </div>
      </div>

      <div style={styles.resizer}></div>

      {/* Right Panel - Preview */}
      <div style={styles.previewPanel}>
        <div style={styles.previewHeader}>
          <div style={styles.previewTabs}>
            {[
              { id: 'preview', label: 'Preview', icon: '📐' },
              { id: 'proforma', label: 'Pro Forma', icon: '💰' },
              { id: '3d', label: '3D View', icon: '🏗️' },
            ].map((tab) => (
              <button
                key={tab.id}
                style={{
                  ...styles.previewTab,
                  ...(activeTab === tab.id ? styles.previewTabActive : {}),
                }}
                onClick={() => setActiveTab(tab.id)}
              >
                <span>{tab.icon}</span>
                <span>{tab.label}</span>
              </button>
            ))}
          </div>
          <div style={styles.previewActions}>
            <button style={styles.actionBtn}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M21 15V19A2 2 0 0 1 19 21H5A2 2 0 0 1 3 19V15M7 10L12 15L17 10M12 15V3" />
              </svg>
              Export
            </button>
            <button style={{ ...styles.actionBtn, ...styles.actionBtnPrimary }}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M4 12V20A2 2 0 0 0 6 22H18A2 2 0 0 0 20 20V12M16 6L12 2L8 6M12 2V15" />
              </svg>
              Share
            </button>
          </div>
        </div>

        <div style={styles.previewContent}>
          {feasibility ? (
            <div style={styles.feasibilityView}>
              <div style={styles.siteCard}>
                <div style={styles.siteCardHeader}>
                  <div style={{
                    ...styles.siteIcon,
                    background: TYPOLOGY_INFO[feasibility.typology]?.color || THEME.accent.primary,
                  }}>
                    {feasibility.icon || '🏗️'}
                  </div>
                  <div>
                    <h3 style={styles.siteTitle}>{feasibility.typologyLabel} Development</h3>
                    <p style={styles.siteMeta}>
                      {feasibility.acreage} acres • {feasibility.zoning} Zoning • Brevard County, FL
                    </p>
                  </div>
                </div>
              </div>

              <div style={styles.metricsGrid}>
                {/* Self-Storage Metrics */}
                {feasibility.netRentableSF && (
                  <>
                    <MetricCard icon="📦" label="Net Rentable SF" value={feasibility.netRentableSF.toLocaleString()} />
                    <MetricCard icon="🔢" label="Total Units" value={feasibility.totalUnits} />
                    <MetricCard icon="🏗️" label="Stories" value={feasibility.stories} />
                    <MetricCard icon="❄️" label="Climate Ctrl" value={`${feasibility.climateControlledPct}%`} />
                    <MetricCard icon="💵" label="Rent/SF/Mo" value={`$${feasibility.avgRentPerSF}`} />
                    <MetricCard icon="📊" label="Occupancy" value={feasibility.occupancy} />
                  </>
                )}
                
                {/* Multi-Family Metrics */}
                {feasibility.units && !feasibility.netRentableSF && !feasibility.rooms && (
                  <>
                    <MetricCard icon="🏢" label="Total Units" value={feasibility.units} />
                    <MetricCard icon="📐" label="Gross SF" value={feasibility.grossSF?.toLocaleString()} />
                    <MetricCard icon="🏗️" label="Stories" value={feasibility.floors} />
                    <MetricCard icon="🚗" label="Parking" value={feasibility.parkingSpaces} />
                    <MetricCard icon="📊" label="Density" value={`${feasibility.density}/ac`} />
                    <MetricCard icon="📈" label="FAR" value={feasibility.far} />
                  </>
                )}

                {/* Industrial Metrics */}
                {feasibility.warehouseSF && (
                  <>
                    <MetricCard icon="🏭" label="Warehouse SF" value={feasibility.warehouseSF.toLocaleString()} />
                    <MetricCard icon="📏" label="Clear Height" value={`${feasibility.clearHeight}'`} />
                    <MetricCard icon="🚚" label="Dock Doors" value={feasibility.dockDoors} />
                    <MetricCard icon="🚛" label="Trailer Spaces" value={feasibility.trailerSpaces} />
                    <MetricCard icon="🚗" label="Car Parking" value={feasibility.carParking} />
                    <MetricCard icon="📈" label="FAR" value={feasibility.far} />
                  </>
                )}

                {/* Senior Living Metrics */}
                {feasibility.beds && (
                  <>
                    <MetricCard icon="🛏️" label="Beds" value={feasibility.beds} />
                    <MetricCard icon="📐" label="Gross SF" value={feasibility.grossSF?.toLocaleString()} />
                    <MetricCard icon="🏗️" label="Stories" value={feasibility.floors} />
                    <MetricCard icon="🚗" label="Parking" value={feasibility.parkingSpaces} />
                    <MetricCard icon="🏠" label="Common Area" value={`${Math.round(feasibility.commonAreaSF / 1000)}K SF`} />
                    <MetricCard icon="📊" label="Density" value={`${feasibility.density}/ac`} />
                  </>
                )}

                {/* Hotel Metrics */}
                {feasibility.rooms && (
                  <>
                    <MetricCard icon="🛏️" label="Rooms" value={feasibility.rooms} />
                    <MetricCard icon="📐" label="Gross SF" value={feasibility.grossSF?.toLocaleString()} />
                    <MetricCard icon="🏗️" label="Stories" value={feasibility.floors} />
                    <MetricCard icon="💵" label="ADR" value={`$${feasibility.adr}`} />
                    <MetricCard icon="📊" label="Occupancy" value={feasibility.occupancy} />
                    <MetricCard icon="📈" label="RevPAR" value={`$${feasibility.revPAR}`} />
                  </>
                )}

                {/* Single-Family Metrics */}
                {feasibility.totalLots && (
                  <>
                    <MetricCard icon="🏠" label="Total Lots" value={feasibility.totalLots} />
                    <MetricCard icon="📐" label="Avg Lot Size" value={`${feasibility.avgLotSize.toLocaleString()} SF`} />
                    <MetricCard icon="🏗️" label="Avg Home" value={`${feasibility.avgHomeSize.toLocaleString()} SF`} />
                    <MetricCard icon="📊" label="Density" value={`${feasibility.density}/ac`} />
                  </>
                )}

                {/* Retail Metrics */}
                {feasibility.padSites !== undefined && (
                  <>
                    <MetricCard icon="🛒" label="Gross SF" value={feasibility.grossSF?.toLocaleString()} />
                    <MetricCard icon="🚗" label="Parking" value={feasibility.parkingSpaces} />
                    <MetricCard icon="🏪" label="Pad Sites" value={feasibility.padSites} />
                    <MetricCard icon="📊" label="Coverage" value={feasibility.lotCoverage} />
                  </>
                )}
              </div>

              {/* Unit Mix for Self-Storage */}
              {feasibility.unitBreakdown && (
                <div style={styles.unitMixCard}>
                  <h4 style={styles.unitMixTitle}>📦 Unit Mix</h4>
                  <div style={styles.unitMixGrid}>
                    {Object.entries(feasibility.unitBreakdown).map(([size, count]) => (
                      <div key={size} style={styles.unitMixItem}>
                        <span style={styles.unitMixSize}>{size}</span>
                        <span style={styles.unitMixCount}>{count}</span>
                        <span style={styles.unitMixLabel}>units</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Site Visualization */}
              <div style={styles.siteViz}>
                <div style={styles.siteVizGrid}>
                  <div style={{
                    ...styles.buildingFootprint,
                    backgroundColor: `${TYPOLOGY_INFO[feasibility.typology]?.color || THEME.accent.primary}33`,
                    borderColor: TYPOLOGY_INFO[feasibility.typology]?.color || THEME.accent.primary,
                  }}>
                    <span style={{
                      ...styles.buildingLabel,
                      color: TYPOLOGY_INFO[feasibility.typology]?.color || THEME.accent.primary,
                    }}>
                      {feasibility.icon} {feasibility.typologyLabel}
                      <br />
                      <small>
                        {feasibility.netRentableSF ? `${feasibility.netRentableSF.toLocaleString()} SF` :
                         feasibility.units ? `${feasibility.units} Units` :
                         feasibility.warehouseSF ? `${feasibility.warehouseSF.toLocaleString()} SF` :
                         feasibility.beds ? `${feasibility.beds} Beds` :
                         feasibility.rooms ? `${feasibility.rooms} Rooms` :
                         feasibility.totalLots ? `${feasibility.totalLots} Lots` :
                         feasibility.grossSF ? `${feasibility.grossSF.toLocaleString()} SF` : ''}
                      </small>
                    </span>
                  </div>
                </div>
                <div style={styles.siteVizLegend}>
                  <span>📍 Site: {feasibility.siteSquareFeet.toLocaleString()} SF ({feasibility.acreage} ac)</span>
                </div>
              </div>

              {/* Profit Banner */}
              <div style={styles.profitBanner}>
                <div style={styles.profitLabel}>Estimated Profit</div>
                <div style={styles.profitValue}>
                  ${(feasibility.profit / 1000000).toFixed(2)}M
                </div>
                <div style={styles.profitMargin}>{feasibility.margin}% margin</div>
              </div>
            </div>
          ) : (
            <div style={styles.emptyPreview}>
              <div style={styles.emptyIcon}>📊</div>
              <h3 style={styles.emptyTitle}>No Analysis Yet</h3>
              <p style={styles.emptyText}>
                Tell me about your site in the chat to generate a feasibility analysis.
              </p>
              <div style={styles.emptyExamples}>
                <p style={styles.emptyExampleLabel}>Try saying:</p>
                <code style={styles.emptyExample}>"5 acres for self-storage, 3-story"</code>
                <code style={styles.emptyExample}>"Build apartments on 8 acres"</code>
                <code style={styles.emptyExample}>"10 acre industrial site"</code>
              </div>
            </div>
          )}
        </div>

        <div style={styles.previewFooter}>
          <span>Powered by</span>
          <span style={styles.brandLink}>BidDeed.AI</span>
          <span style={styles.footerDivider}>•</span>
          <span>© 2026 Everest Capital USA</span>
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// SUB-COMPONENTS
// ============================================================================

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
                const isHeaderRow = isHeader && ri === 0;
                return (
                  <tr key={ri}>
                    {cells.map((cell, ci) => (
                      isHeaderRow ? (
                        <th key={ci} style={styles.th}>{cell.trim().replace(/\*\*/g, '')}</th>
                      ) : (
                        <td key={ci} style={styles.td}>
                          {cell.trim().replace(/\*\*/g, '')}
                        </td>
                      )
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
            if (line.startsWith('### ')) {
              return <h4 key={li} style={styles.mdH4}>{line.replace('### ', '').replace(/\*\*/g, '')}</h4>;
            }
            if (line.startsWith('## ')) {
              return <h3 key={li} style={styles.mdH3}>{line.replace('## ', '').replace(/\*\*/g, '')}</h3>;
            }
            if (line === '---') {
              return <hr key={li} style={styles.mdHr} />;
            }
            if (line.startsWith('• ') || line.startsWith('* ')) {
              return <div key={li} style={styles.mdLi}>{line.replace(/\*\*/g, '')}</div>;
            }
            const boldParts = line.split(/\*\*([^*]+)\*\*/g);
            if (boldParts.length > 1) {
              return (
                <p key={li} style={styles.mdP}>
                  {boldParts.map((bp, bpi) => 
                    bpi % 2 === 1 ? <strong key={bpi}>{bp}</strong> : bp
                  )}
                </p>
              );
            }
            return line ? <p key={li} style={styles.mdP}>{line}</p> : null;
          })}
        </span>
      );
    });
  };

  return <div style={styles.messageContent}>{renderContent(content)}</div>;
}

function MetricCard({ icon, label, value }) {
  return (
    <div style={styles.metricCard}>
      <span style={styles.metricIcon}>{icon}</span>
      <div style={styles.metricInfo}>
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
  container: {
    display: 'flex',
    height: '100vh',
    width: '100vw',
    backgroundColor: THEME.bg.primary,
    fontFamily: "'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif",
    color: THEME.text.primary,
  },
  chatPanel: {
    width: '45%',
    minWidth: '400px',
    maxWidth: '600px',
    display: 'flex',
    flexDirection: 'column',
    backgroundColor: THEME.bg.secondary,
    borderRight: `1px solid ${THEME.border.subtle}`,
  },
  chatHeader: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '16px 20px',
    borderBottom: `1px solid ${THEME.border.subtle}`,
    backgroundColor: THEME.bg.tertiary,
  },
  logoContainer: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
  },
  logoIcon: {
    width: '36px',
    height: '36px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    background: THEME.gradient.brand,
    borderRadius: '10px',
    fontSize: '18px',
    fontWeight: '700',
  },
  logoText: {
    display: 'flex',
    flexDirection: 'column',
  },
  logoTitle: {
    fontSize: '16px',
    fontWeight: '700',
    letterSpacing: '-0.3px',
  },
  logoSubtitle: {
    fontSize: '11px',
    color: THEME.text.muted,
  },
  statusBadge: {
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
    padding: '6px 12px',
    backgroundColor: 'rgba(16, 185, 129, 0.1)',
    borderRadius: '100px',
    fontSize: '12px',
    color: THEME.accent.success,
  },
  statusDot: {
    width: '6px',
    height: '6px',
    backgroundColor: THEME.accent.success,
    borderRadius: '50%',
  },
  messagesContainer: {
    flex: 1,
    overflow: 'auto',
    padding: '20px',
    display: 'flex',
    flexDirection: 'column',
    gap: '16px',
  },
  messageWrapper: {
    display: 'flex',
    alignItems: 'flex-start',
    gap: '12px',
  },
  avatarAI: {
    width: '32px',
    height: '32px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    background: THEME.gradient.brand,
    borderRadius: '8px',
    fontSize: '14px',
    fontWeight: '700',
    flexShrink: 0,
  },
  messageBubble: {
    maxWidth: '85%',
    padding: '12px 16px',
    borderRadius: '16px',
    fontSize: '14px',
    lineHeight: 1.5,
  },
  aiBubble: {
    backgroundColor: THEME.bg.elevated,
    borderBottomLeftRadius: '4px',
  },
  userBubble: {
    backgroundColor: THEME.accent.primary,
    borderBottomRightRadius: '4px',
    marginLeft: 'auto',
  },
  messageContent: {
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
  },
  typingIndicator: {
    display: 'flex',
    gap: '4px',
    padding: '4px 0',
  },
  typingDot: {
    width: '8px',
    height: '8px',
    backgroundColor: THEME.text.muted,
    borderRadius: '50%',
    animation: 'typingPulse 1s infinite',
  },
  quickActions: {
    display: 'flex',
    gap: '8px',
    padding: '0 20px 12px',
    flexWrap: 'wrap',
  },
  quickActionBtn: {
    padding: '8px 14px',
    backgroundColor: THEME.bg.elevated,
    border: `1px solid ${THEME.border.default}`,
    borderRadius: '100px',
    color: THEME.text.secondary,
    fontSize: '13px',
    cursor: 'pointer',
    transition: 'all 0.2s',
  },
  inputArea: {
    padding: '16px 20px',
    borderTop: `1px solid ${THEME.border.subtle}`,
    backgroundColor: THEME.bg.tertiary,
  },
  inputWrapper: {
    display: 'flex',
    alignItems: 'flex-end',
    gap: '12px',
    padding: '12px 16px',
    backgroundColor: THEME.bg.elevated,
    borderRadius: '16px',
    border: `1px solid ${THEME.border.default}`,
  },
  input: {
    flex: 1,
    backgroundColor: 'transparent',
    border: 'none',
    outline: 'none',
    color: THEME.text.primary,
    fontSize: '14px',
    lineHeight: 1.5,
    resize: 'none',
    fontFamily: 'inherit',
  },
  sendBtn: {
    width: '36px',
    height: '36px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: THEME.accent.primary,
    border: 'none',
    borderRadius: '10px',
    color: '#fff',
    cursor: 'pointer',
    transition: 'all 0.2s',
    flexShrink: 0,
  },
  inputHint: {
    textAlign: 'center',
    fontSize: '11px',
    color: THEME.text.muted,
    marginTop: '8px',
  },
  resizer: {
    width: '4px',
    backgroundColor: THEME.bg.primary,
    cursor: 'col-resize',
  },
  previewPanel: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    backgroundColor: THEME.bg.primary,
  },
  previewHeader: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '12px 20px',
    borderBottom: `1px solid ${THEME.border.subtle}`,
    backgroundColor: THEME.bg.secondary,
  },
  previewTabs: {
    display: 'flex',
    gap: '4px',
    padding: '4px',
    backgroundColor: THEME.bg.elevated,
    borderRadius: '10px',
  },
  previewTab: {
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
    padding: '8px 14px',
    backgroundColor: 'transparent',
    border: 'none',
    borderRadius: '8px',
    color: THEME.text.secondary,
    fontSize: '13px',
    fontWeight: '500',
    cursor: 'pointer',
    transition: 'all 0.2s',
  },
  previewTabActive: {
    backgroundColor: THEME.accent.primary,
    color: '#fff',
  },
  previewActions: {
    display: 'flex',
    gap: '8px',
  },
  actionBtn: {
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
    padding: '8px 14px',
    backgroundColor: THEME.bg.elevated,
    border: `1px solid ${THEME.border.default}`,
    borderRadius: '8px',
    color: THEME.text.secondary,
    fontSize: '13px',
    fontWeight: '500',
    cursor: 'pointer',
    transition: 'all 0.2s',
  },
  actionBtnPrimary: {
    backgroundColor: THEME.accent.primary,
    borderColor: THEME.accent.primary,
    color: '#fff',
  },
  previewContent: {
    flex: 1,
    overflow: 'auto',
    padding: '24px',
  },
  feasibilityView: {
    display: 'flex',
    flexDirection: 'column',
    gap: '20px',
    maxWidth: '800px',
    margin: '0 auto',
  },
  siteCard: {
    padding: '20px',
    backgroundColor: THEME.bg.secondary,
    borderRadius: '16px',
    border: `1px solid ${THEME.border.subtle}`,
  },
  siteCardHeader: {
    display: 'flex',
    alignItems: 'center',
    gap: '16px',
  },
  siteIcon: {
    width: '48px',
    height: '48px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: '12px',
    fontSize: '24px',
  },
  siteTitle: {
    fontSize: '18px',
    fontWeight: '600',
    marginBottom: '4px',
  },
  siteMeta: {
    fontSize: '13px',
    color: THEME.text.muted,
  },
  metricsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))',
    gap: '12px',
  },
  metricCard: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    padding: '14px',
    backgroundColor: THEME.bg.secondary,
    borderRadius: '12px',
    border: `1px solid ${THEME.border.subtle}`,
  },
  metricIcon: {
    fontSize: '20px',
  },
  metricInfo: {
    display: 'flex',
    flexDirection: 'column',
  },
  metricValue: {
    fontSize: '16px',
    fontWeight: '600',
  },
  metricLabel: {
    fontSize: '11px',
    color: THEME.text.muted,
  },
  unitMixCard: {
    padding: '20px',
    backgroundColor: THEME.bg.secondary,
    borderRadius: '16px',
    border: `1px solid ${THEME.border.subtle}`,
  },
  unitMixTitle: {
    fontSize: '14px',
    fontWeight: '600',
    marginBottom: '16px',
    color: THEME.text.secondary,
  },
  unitMixGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(6, 1fr)',
    gap: '12px',
  },
  unitMixItem: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    padding: '12px 8px',
    backgroundColor: THEME.bg.elevated,
    borderRadius: '10px',
  },
  unitMixSize: {
    fontSize: '12px',
    fontWeight: '600',
    color: THEME.accent.orange,
    marginBottom: '4px',
  },
  unitMixCount: {
    fontSize: '18px',
    fontWeight: '700',
  },
  unitMixLabel: {
    fontSize: '10px',
    color: THEME.text.muted,
  },
  siteViz: {
    padding: '24px',
    backgroundColor: THEME.bg.secondary,
    borderRadius: '16px',
    border: `1px solid ${THEME.border.subtle}`,
  },
  siteVizGrid: {
    width: '100%',
    height: '180px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundImage: `
      linear-gradient(rgba(59,130,246,0.08) 1px, transparent 1px),
      linear-gradient(90deg, rgba(59,130,246,0.08) 1px, transparent 1px)
    `,
    backgroundSize: '20px 20px',
    borderRadius: '8px',
  },
  buildingFootprint: {
    width: '200px',
    height: '120px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    border: '2px dashed',
    borderRadius: '8px',
  },
  buildingLabel: {
    fontSize: '14px',
    fontWeight: '600',
    textAlign: 'center',
  },
  siteVizLegend: {
    display: 'flex',
    justifyContent: 'center',
    gap: '16px',
    marginTop: '16px',
    fontSize: '13px',
    color: THEME.text.muted,
  },
  profitBanner: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    padding: '24px',
    background: 'linear-gradient(135deg, rgba(16,185,129,0.2) 0%, rgba(16,185,129,0.05) 100%)',
    borderRadius: '16px',
    border: `1px solid rgba(16,185,129,0.3)`,
  },
  profitLabel: {
    fontSize: '12px',
    textTransform: 'uppercase',
    letterSpacing: '1px',
    color: THEME.accent.success,
  },
  profitValue: {
    fontSize: '36px',
    fontWeight: '700',
    color: THEME.accent.success,
    marginTop: '4px',
  },
  profitMargin: {
    fontSize: '14px',
    color: THEME.accent.success,
    opacity: 0.8,
  },
  emptyPreview: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    height: '100%',
    textAlign: 'center',
    padding: '40px',
  },
  emptyIcon: {
    fontSize: '64px',
    marginBottom: '16px',
    opacity: 0.5,
  },
  emptyTitle: {
    fontSize: '20px',
    fontWeight: '600',
    marginBottom: '8px',
  },
  emptyText: {
    fontSize: '14px',
    color: THEME.text.muted,
    marginBottom: '24px',
  },
  emptyExamples: {
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
  },
  emptyExampleLabel: {
    fontSize: '12px',
    color: THEME.text.muted,
    marginBottom: '4px',
  },
  emptyExample: {
    padding: '10px 16px',
    backgroundColor: THEME.bg.elevated,
    borderRadius: '8px',
    fontSize: '13px',
    color: THEME.text.secondary,
  },
  previewFooter: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '8px',
    padding: '12px',
    borderTop: `1px solid ${THEME.border.subtle}`,
    fontSize: '12px',
    color: THEME.text.muted,
  },
  brandLink: {
    color: THEME.accent.primary,
    fontWeight: '500',
  },
  footerDivider: {
    opacity: 0.3,
  },
  table: {
    width: '100%',
    borderCollapse: 'collapse',
    margin: '8px 0',
    fontSize: '13px',
  },
  th: {
    textAlign: 'left',
    padding: '8px 12px',
    borderBottom: `1px solid ${THEME.border.default}`,
    fontWeight: '600',
    color: THEME.text.secondary,
  },
  td: {
    padding: '8px 12px',
    borderBottom: `1px solid ${THEME.border.subtle}`,
  },
  mdH3: {
    fontSize: '16px',
    fontWeight: '600',
    margin: '12px 0 8px',
  },
  mdH4: {
    fontSize: '14px',
    fontWeight: '600',
    margin: '8px 0 6px',
    color: THEME.text.secondary,
  },
  mdHr: {
    border: 'none',
    borderTop: `1px solid ${THEME.border.subtle}`,
    margin: '12px 0',
  },
  mdP: {
    margin: '4px 0',
  },
  mdLi: {
    padding: '2px 0 2px 8px',
  },
};

// Add keyframes
const styleSheet = document.createElement('style');
styleSheet.textContent = `
  @keyframes typingPulse {
    0%, 100% { opacity: 0.3; transform: scale(1); }
    50% { opacity: 1; transform: scale(1.1); }
  }
  
  textarea::placeholder {
    color: ${THEME.text.muted};
  }
  
  ::-webkit-scrollbar {
    width: 8px;
  }
  ::-webkit-scrollbar-track {
    background: transparent;
  }
  ::-webkit-scrollbar-thumb {
    background: ${THEME.border.default};
    border-radius: 4px;
  }
  ::-webkit-scrollbar-thumb:hover {
    background: ${THEME.border.strong};
  }
`;
document.head.appendChild(styleSheet);
