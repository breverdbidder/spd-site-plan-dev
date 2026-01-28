/**
 * Constants and Configuration
 * Shared across all SPD.AI components
 * 
 * @author BidDeed.AI / Everest Capital USA
 */

// API Configuration
export const API_BASE = window.location.hostname === 'localhost' 
  ? 'http://localhost:8788' 
  : '';

// Design system colors
export const COLORS = {
  primary: '#0F172A',
  secondary: '#1E293B',
  accent: '#3B82F6',
  success: '#10B981',
  warning: '#F59E0B',
  danger: '#EF4444',
  surface: '#F8FAFC',
  border: '#E2E8F0',
  textPrimary: '#0F172A',
  textSecondary: '#64748B',
};

// Zoning data for Brevard County
export const BREVARD_ZONING_DATA = {
  'R-1': { name: 'Single Family Residential', maxDensity: 4, maxHeight: 35 },
  'R-2': { name: 'Medium Density Residential', maxDensity: 10, maxHeight: 45 },
  'R-3': { name: 'High Density Residential', maxDensity: 20, maxHeight: 65 },
  'C-1': { name: 'Neighborhood Commercial', maxFAR: 0.5, maxHeight: 35 },
  'C-2': { name: 'General Commercial', maxFAR: 1.0, maxHeight: 50 },
  'I-1': { name: 'Light Industrial', maxFAR: 0.6, maxHeight: 45 },
  'PUD': { name: 'Planned Unit Development', maxDensity: 'Varies', maxHeight: 'Varies' },
};

// Typology Configurations
export const TYPOLOGY_CONFIGS = {
  multifamily: { name: 'Multi-Family', icon: '🏢', color: '#3B82F6' },
  selfStorage: { name: 'Self-Storage', icon: '📦', color: '#F97316' },
  industrial: { name: 'Industrial', icon: '🏭', color: '#6366F1' },
  singleFamily: { name: 'Single-Family', icon: '🏠', color: '#10B981' },
  seniorLiving: { name: 'Senior Living', icon: '🏥', color: '#14B8A6' },
  medical: { name: 'Medical Office', icon: '⚕️', color: '#EF4444' },
  retail: { name: 'Retail', icon: '🛒', color: '#F59E0B' },
  hotel: { name: 'Hotel', icon: '🏨', color: '#EC4899' },
};

// Storage unit mix for calculations
export const STORAGE_UNIT_MIX = {
  '5x5': { sf: 25, pct: 10, rentPerSF: 2.00 },
  '5x10': { sf: 50, pct: 25, rentPerSF: 1.75 },
  '10x10': { sf: 100, pct: 30, rentPerSF: 1.50 },
  '10x15': { sf: 150, pct: 15, rentPerSF: 1.35 },
  '10x20': { sf: 200, pct: 12, rentPerSF: 1.25 },
  '10x30': { sf: 300, pct: 8, rentPerSF: 1.15 },
};

// Default parameters by typology
export const DEFAULT_PARAMS = {
  multifamily: {
    parkingRatio: 1.5,
    unitMix: { studio: 10, '1br': 40, '2br': 40, '3br': 10 },
  },
  selfStorage: {
    stories: 1,
    climateControlled: 50,
  },
  industrial: {
    clearHeight: 32,
    bayDepth: 180,
    dockRatio: 0.1,
  },
  singleFamily: {
    lotSize: 7500,
    homeSF: 2200,
  },
  seniorLiving: {
    careLevel: 'assisted',
    monthlyRate: 4500,
  },
  medical: {
    rentPerSF: 28,
    parkingRatio: 4,
  },
  retail: {
    anchorRatio: 0.4,
    rentPerSF: 22,
  },
  hotel: {
    adr: 145,
    roomCount: 120,
  },
};

// Cost assumptions
export const COST_ASSUMPTIONS = {
  landPerAcre: 150000,  // $150k/acre baseline
  hardCostsMultiplier: {
    multifamily: 175,    // $/SF
    selfStorage: 65,
    industrial: 85,
    singleFamily: 165,
    seniorLiving: 200,
    medical: 250,
    retail: 150,
    hotel: 180,
  },
  softCostsPct: 0.15,    // 15% of hard costs
  contingencyPct: 0.05,  // 5% contingency
};
