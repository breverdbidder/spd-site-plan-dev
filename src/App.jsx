import React, { useState, useCallback } from 'react';

// Import refactored components
import ChatInterface from './components/ChatInterface';
import FormInterface from './components/FormInterface';
import Results from './components/Results';
import MapView from './components/MapView';
import { COLORS, API_BASE, TYPOLOGY_CONFIGS, STORAGE_UNIT_MIX } from './components/constants';

/**
 * SPD.AI V3.3 - Site Planning & Development AI Platform
 * 
 * Refactored Architecture (P1):
 * - ChatInterface: AI chat functionality
 * - FormInterface: Form-based input
 * - Results: Feasibility analysis display
 * - MapView: Site visualization
 * 
 * @author BidDeed.AI / Everest Capital USA
 * @version 3.3.0
 */

export default function SPDAIApp() {
  // ============================================================================
  // STATE MANAGEMENT
  // ============================================================================
  
  // Site parameters
  const [siteAcreage, setSiteAcreage] = useState(5.0);
  const [zoning, setZoning] = useState('R-2');
  const [selectedTypology, setSelectedTypology] = useState('multifamily');
  
  // Typology-specific parameters
  const [params, setParams] = useState({
    parkingRatio: 1.5,
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
  
  // Results and UI state
  const [results, setResults] = useState(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [inputMode, setInputMode] = useState('chat');
  const [viewMode, setViewMode] = useState('2d');

  // ============================================================================
  // FEASIBILITY CALCULATIONS
  // ============================================================================

  const calculateFeasibility = useCallback((typology, acreage, zoningCode) => {
    const config = TYPOLOGY_CONFIGS[typology];
    const siteSF = acreage * 43560;
    
    let result = {
      typology: config.name,
      icon: config.icon,
      color: config.color,
      acreage: acreage,
      zoning: zoningCode,
    };

    switch (typology) {
      case 'multifamily': {
        const buildableSF = siteSF * 0.65;
        const floors = 3;
        const grossSF = buildableSF * floors;
        const efficiency = 0.85;
        const avgUnitSF = 900;
        const units = Math.floor((grossSF * efficiency) / avgUnitSF);
        const parking = Math.ceil(units * params.parkingRatio);
        
        result = {
          ...result,
          units,
          grossSF: Math.round(grossSF),
          floors,
          parkingSpaces: parking,
          proForma: {
            landCost: acreage * 150000,
            hardCosts: grossSF * 175,
            softCosts: grossSF * 175 * 0.15,
            totalCost: acreage * 150000 + grossSF * 175 * 1.15,
            noi: units * 1500 * 12 * 0.6,
            profit: units * 1500 * 12 * 0.6 * 5 - (acreage * 150000 + grossSF * 175 * 1.15),
            margin: 18,
          },
        };
        break;
      }

      case 'selfStorage': {
        const buildableSF = siteSF * 0.45;
        const floors = params.stories;
        const grossSF = buildableSF * floors;
        const efficiency = 0.88;
        const netRentableSF = Math.round(grossSF * efficiency);
        
        // Calculate unit breakdown
        const unitBreakdown = {};
        Object.entries(STORAGE_UNIT_MIX).forEach(([size, config]) => {
          unitBreakdown[size] = Math.round((netRentableSF * config.pct / 100) / config.sf);
        });

        result = {
          ...result,
          netRentableSF,
          grossSF: Math.round(grossSF),
          floors,
          unitBreakdown,
          proForma: {
            landCost: acreage * 120000,
            hardCosts: grossSF * 65,
            softCosts: grossSF * 65 * 0.12,
            totalCost: acreage * 120000 + grossSF * 65 * 1.12,
            noi: netRentableSF * 12 * 0.7,
            profit: netRentableSF * 12 * 0.7 * 6 - (acreage * 120000 + grossSF * 65 * 1.12),
            margin: 22,
          },
        };
        break;
      }

      case 'industrial': {
        const buildableSF = siteSF * 0.5;
        const warehouseSF = Math.round(buildableSF);
        const docks = Math.ceil(warehouseSF / 10000);

        result = {
          ...result,
          warehouseSF,
          grossSF: warehouseSF,
          clearHeight: params.clearHeight,
          docks,
          proForma: {
            landCost: acreage * 100000,
            hardCosts: warehouseSF * 85,
            softCosts: warehouseSF * 85 * 0.1,
            totalCost: acreage * 100000 + warehouseSF * 85 * 1.1,
            noi: warehouseSF * 8 * 0.75,
            profit: warehouseSF * 8 * 0.75 * 7 - (acreage * 100000 + warehouseSF * 85 * 1.1),
            margin: 20,
          },
        };
        break;
      }

      case 'singleFamily': {
        const lotSize = 7500;
        const roadAllowance = 0.2;
        const usableSF = siteSF * (1 - roadAllowance);
        const totalLots = Math.floor(usableSF / lotSize);

        result = {
          ...result,
          totalLots,
          avgLotSF: lotSize,
          proForma: {
            landCost: acreage * 80000,
            hardCosts: totalLots * 45000,
            softCosts: totalLots * 45000 * 0.08,
            totalCost: acreage * 80000 + totalLots * 45000 * 1.08,
            profit: totalLots * 75000 - (acreage * 80000 + totalLots * 45000 * 1.08),
            margin: 25,
          },
        };
        break;
      }

      case 'seniorLiving': {
        const buildableSF = siteSF * 0.35;
        const floors = 2;
        const grossSF = buildableSF * floors;
        const avgUnitSF = params.careLevel === 'memory' ? 400 : 600;
        const beds = Math.floor(grossSF * 0.7 / avgUnitSF);

        result = {
          ...result,
          beds,
          grossSF: Math.round(grossSF),
          floors,
          careLevel: params.careLevel,
          proForma: {
            landCost: acreage * 200000,
            hardCosts: grossSF * 200,
            softCosts: grossSF * 200 * 0.18,
            totalCost: acreage * 200000 + grossSF * 200 * 1.18,
            noi: beds * params.monthlyRate * 12 * 0.35,
            profit: beds * params.monthlyRate * 12 * 0.35 * 8 - (acreage * 200000 + grossSF * 200 * 1.18),
            margin: 15,
          },
        };
        break;
      }

      case 'hotel': {
        const buildableSF = siteSF * 0.4;
        const floors = 4;
        const grossSF = buildableSF * floors;
        const roomSF = 450;
        const rooms = Math.floor(grossSF * 0.65 / roomSF);

        result = {
          ...result,
          rooms,
          grossSF: Math.round(grossSF),
          floors,
          proForma: {
            landCost: acreage * 250000,
            hardCosts: grossSF * 180,
            softCosts: grossSF * 180 * 0.15,
            totalCost: acreage * 250000 + grossSF * 180 * 1.15,
            revPAR: params.adr * 0.65,
            profit: rooms * params.adr * 365 * 0.65 * 0.35 * 10 - (acreage * 250000 + grossSF * 180 * 1.15),
            margin: 16,
          },
        };
        break;
      }

      default:
        break;
    }

    return result;
  }, [params]);

  // ============================================================================
  // EVENT HANDLERS
  // ============================================================================

  const generateFeasibility = useCallback(() => {
    setIsGenerating(true);
    
    // Simulate processing time
    setTimeout(() => {
      const feasibility = calculateFeasibility(selectedTypology, siteAcreage, zoning);
      setResults(feasibility);
      setIsGenerating(false);
    }, 800);
  }, [selectedTypology, siteAcreage, zoning, calculateFeasibility]);

  const handleSiteParamsExtracted = useCallback((extractedParams) => {
    if (extractedParams.acreage) {
      setSiteAcreage(extractedParams.acreage);
    }
    if (extractedParams.zoning) {
      setZoning(extractedParams.zoning);
    }
  }, []);

  // ============================================================================
  // STYLES
  // ============================================================================

  const styles = {
    app: {
      display: 'flex',
      height: '100vh',
      backgroundColor: COLORS.surface,
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    },
    leftSidebar: {
      width: '380px',
      borderRight: `1px solid ${COLORS.border}`,
      display: 'flex',
      flexDirection: 'column',
      backgroundColor: 'white',
    },
    modeToggle: {
      display: 'flex',
      padding: '12px',
      gap: '8px',
      borderBottom: `1px solid ${COLORS.border}`,
    },
    modeBtn: {
      flex: 1,
      padding: '10px',
      border: 'none',
      borderRadius: '8px',
      cursor: 'pointer',
      fontSize: '13px',
      fontWeight: '500',
      transition: 'all 0.2s',
    },
    modeBtnActive: {
      backgroundColor: COLORS.accent,
      color: 'white',
    },
    modeBtnInactive: {
      backgroundColor: COLORS.surface,
      color: COLORS.textSecondary,
    },
    sidebarContent: {
      flex: 1,
      overflow: 'hidden',
    },
    mapArea: {
      flex: 1,
      position: 'relative',
    },
    rightSidebar: {
      width: '340px',
      borderLeft: `1px solid ${COLORS.border}`,
      backgroundColor: 'white',
    },
  };

  // ============================================================================
  // RENDER
  // ============================================================================

  return (
    <div style={styles.app}>
      {/* Left Sidebar - Input */}
      <aside style={styles.leftSidebar}>
        {/* Mode Toggle */}
        <div style={styles.modeToggle}>
          <button
            style={{
              ...styles.modeBtn,
              ...(inputMode === 'chat' ? styles.modeBtnActive : styles.modeBtnInactive),
            }}
            onClick={() => setInputMode('chat')}
          >
            💬 Chat
          </button>
          <button
            style={{
              ...styles.modeBtn,
              ...(inputMode === 'form' ? styles.modeBtnActive : styles.modeBtnInactive),
            }}
            onClick={() => setInputMode('form')}
          >
            📋 Form
          </button>
        </div>

        {/* Input Interface */}
        <div style={styles.sidebarContent}>
          {inputMode === 'chat' ? (
            <ChatInterface
              siteContext={{ acreage: siteAcreage, zoning, typology: selectedTypology }}
              onSiteParamsExtracted={handleSiteParamsExtracted}
              apiBase={API_BASE}
            />
          ) : (
            <FormInterface
              siteAcreage={siteAcreage}
              setSiteAcreage={setSiteAcreage}
              zoning={zoning}
              setZoning={setZoning}
              selectedTypology={selectedTypology}
              setSelectedTypology={setSelectedTypology}
              params={params}
              setParams={setParams}
              onGenerate={generateFeasibility}
              isGenerating={isGenerating}
            />
          )}
        </div>
      </aside>

      {/* Center - Map View */}
      <main style={styles.mapArea}>
        <MapView
          siteAcreage={siteAcreage}
          zoning={zoning}
          results={results}
          viewMode={viewMode}
          setViewMode={setViewMode}
        />
      </main>

      {/* Right Sidebar - Results */}
      <aside style={styles.rightSidebar}>
        <Results results={results} />
      </aside>
    </div>
  );
}
