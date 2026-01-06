import React, { useState, useEffect, useCallback, useRef } from 'react';

// ============================================================================
// SPD.AI - Site Planning & Development AI Platform
// ============================================================================
// An original BidDeed.AI product for real estate feasibility analysis
// Built with: React, Mapbox GL, Turf.js
// © 2026 BidDeed.AI / Everest Capital USA - All Rights Reserved
// ============================================================================

// Mock data for demo (replace with real Zoneomics/BCPAO integration)
const BREVARD_ZONING_DATA = {
  'R-1': { name: 'Single Family Residential', maxDensity: 4, maxHeight: 35, setbacks: { front: 25, side: 7.5, rear: 20 } },
  'R-2': { name: 'Medium Density Residential', maxDensity: 10, maxHeight: 45, setbacks: { front: 25, side: 10, rear: 15 } },
  'R-3': { name: 'High Density Residential', maxDensity: 20, maxHeight: 65, setbacks: { front: 25, side: 15, rear: 15 } },
  'C-1': { name: 'Neighborhood Commercial', maxFAR: 0.5, maxHeight: 35, setbacks: { front: 20, side: 10, rear: 10 } },
  'C-2': { name: 'General Commercial', maxFAR: 1.0, maxHeight: 50, setbacks: { front: 15, side: 10, rear: 10 } },
  'I-1': { name: 'Light Industrial', maxFAR: 0.6, maxHeight: 45, setbacks: { front: 30, side: 15, rear: 15 } },
  'PUD': { name: 'Planned Unit Development', maxDensity: 'Varies', maxHeight: 'Varies', setbacks: 'Per Plan' }
};

const TYPOLOGY_CONFIGS = {
  multifamily: {
    name: 'Multi-Family',
    icon: '🏢',
    color: '#3B82F6',
    defaultParams: {
      unitMix: { studio: 10, oneBed: 40, twoBed: 35, threeBed: 15 },
      avgUnitSize: { studio: 550, oneBed: 750, twoBed: 1050, threeBed: 1350 },
      parkingRatio: 1.5,
      corridorWidth: 6,
      coreSize: 800
    }
  },
  singleFamily: {
    name: 'Single-Family',
    icon: '🏠',
    color: '#10B981',
    defaultParams: {
      lotSizes: { min: 6000, max: 12000 },
      avgHomeSize: 2200,
      garageSpaces: 2,
      setbackBuffer: 1.1
    }
  },
  industrial: {
    name: 'Industrial/Warehouse',
    icon: '🏭',
    color: '#6366F1',
    defaultParams: {
      clearHeight: 32,
      bayDepth: 180,
      dockRatio: 1, // per 10,000 SF
      parkingRatio: 0.5,
      yardDepth: 130
    }
  },
  retail: {
    name: 'Retail',
    icon: '🛒',
    color: '#F59E0B',
    defaultParams: {
      avgTenantSize: 5000,
      parkingRatio: 4.0,
      anchorRatio: 0.4,
      padSites: 2
    }
  },
  hotel: {
    name: 'Hotel',
    icon: '🏨',
    color: '#EC4899',
    defaultParams: {
      roomCount: 120,
      avgRoomSize: 350,
      amenityRatio: 0.15,
      parkingRatio: 0.8
    }
  }
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
  // State management
  const [activeTab, setActiveTab] = useState('site');
  const [siteData, setSiteData] = useState(null);
  const [selectedTypology, setSelectedTypology] = useState('multifamily');
  const [params, setParams] = useState(TYPOLOGY_CONFIGS.multifamily.defaultParams);
  const [results, setResults] = useState(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [viewMode, setViewMode] = useState('2d'); // '2d' or '3d'
  const [address, setAddress] = useState('');
  const [siteAcreage, setSiteAcreage] = useState(5.0);
  const [zoning, setZoning] = useState('R-2');
  const [showProForma, setShowProForma] = useState(false);

  // Generate feasibility analysis
  const generateFeasibility = useCallback(() => {
    setIsGenerating(true);
    
    // Simulate AI processing
    setTimeout(() => {
      const zoningData = BREVARD_ZONING_DATA[zoning];
      const typology = TYPOLOGY_CONFIGS[selectedTypology];
      const siteSquareFeet = siteAcreage * 43560;
      
      let generatedResults;
      
      if (selectedTypology === 'multifamily') {
        const maxUnits = Math.floor(siteAcreage * zoningData.maxDensity);
        const totalBedrooms = calculateBedrooms(maxUnits, params.unitMix);
        const buildableArea = siteSquareFeet * 0.65; // 65% lot coverage
        const avgUnitSF = calculateAvgUnitSize(params.unitMix, params.avgUnitSize);
        const grossBuildingSF = maxUnits * avgUnitSF * 1.15; // 15% circulation
        const floors = Math.ceil(grossBuildingSF / buildableArea);
        const parkingSpaces = Math.ceil(maxUnits * params.parkingRatio);
        const surfaceParking = Math.min(parkingSpaces * 0.4, siteSquareFeet * 0.25 / 350);
        const structuredParking = parkingSpaces - surfaceParking;
        
        generatedResults = {
          typology: 'Multi-Family',
          units: maxUnits,
          totalBedrooms,
          grossSF: Math.round(grossBuildingSF),
          floors: Math.min(floors, Math.floor(zoningData.maxHeight / 10)),
          efficiency: 0.87,
          parkingSpaces,
          surfaceParking: Math.round(surfaceParking),
          structuredParking: Math.round(structuredParking),
          unitMix: {
            studio: Math.round(maxUnits * params.unitMix.studio / 100),
            oneBed: Math.round(maxUnits * params.unitMix.oneBed / 100),
            twoBed: Math.round(maxUnits * params.unitMix.twoBed / 100),
            threeBed: Math.round(maxUnits * params.unitMix.threeBed / 100)
          },
          density: (maxUnits / siteAcreage).toFixed(1),
          lotCoverage: '65%',
          far: (grossBuildingSF / siteSquareFeet).toFixed(2),
          openSpace: Math.round(siteSquareFeet * 0.2),
          amenitySpace: Math.round(grossBuildingSF * 0.05)
        };
      } else if (selectedTypology === 'industrial') {
        const buildableArea = siteSquareFeet * 0.55;
        const warehouseSF = Math.round(buildableArea);
        const clearHeight = params.clearHeight;
        const dockDoors = Math.ceil(warehouseSF / 10000 * params.dockRatio);
        const trailerSpaces = dockDoors * 2;
        const carParking = Math.ceil(warehouseSF / 1000 * params.parkingRatio);
        
        generatedResults = {
          typology: 'Industrial',
          warehouseSF,
          clearHeight,
          dockDoors,
          trailerSpaces,
          carParking,
          lotCoverage: '55%',
          yardDepth: params.yardDepth,
          efficiency: 0.92,
          bayWidth: 50,
          bayDepth: params.bayDepth,
          totalBays: Math.floor(warehouseSF / (50 * params.bayDepth)),
          far: (warehouseSF / siteSquareFeet).toFixed(2)
        };
      } else if (selectedTypology === 'singleFamily') {
        const avgLotSize = (params.lotSizes.min + params.lotSizes.max) / 2;
        const usableLand = siteSquareFeet * 0.70; // 70% after roads/infrastructure
        const totalLots = Math.floor(usableLand / avgLotSize);
        const roadArea = siteSquareFeet * 0.20;
        const openSpaceArea = siteSquareFeet * 0.10;
        
        generatedResults = {
          typology: 'Single-Family',
          totalLots,
          avgLotSize: Math.round(avgLotSize),
          avgHomeSize: params.avgHomeSize,
          totalHomeSF: totalLots * params.avgHomeSize,
          roadArea: Math.round(roadArea),
          openSpaceArea: Math.round(openSpaceArea),
          density: (totalLots / siteAcreage).toFixed(1),
          garageSpaces: totalLots * params.garageSpaces,
          efficiency: 0.70
        };
      }
      
      // Add pro forma estimates
      generatedResults.proForma = generateProForma(generatedResults, selectedTypology, siteAcreage);
      
      setResults(generatedResults);
      setIsGenerating(false);
    }, 1500);
  }, [siteAcreage, zoning, selectedTypology, params]);

  // Helper functions
  const calculateBedrooms = (units, mix) => {
    return Math.round(
      units * (mix.studio * 0 + mix.oneBed * 1 + mix.twoBed * 2 + mix.threeBed * 3) / 100
    );
  };

  const calculateAvgUnitSize = (mix, sizes) => {
    return (
      (mix.studio / 100 * sizes.studio) +
      (mix.oneBed / 100 * sizes.oneBed) +
      (mix.twoBed / 100 * sizes.twoBed) +
      (mix.threeBed / 100 * sizes.threeBed)
    );
  };

  const generateProForma = (results, typology, acreage) => {
    const landCostPerAcre = 150000; // Brevard County avg
    const landCost = acreage * landCostPerAcre;
    
    let hardCosts, softCosts, totalRevenue, noi;
    
    if (typology === 'multifamily') {
      hardCosts = results.grossSF * 185; // $185/SF construction
      softCosts = hardCosts * 0.25;
      const avgRent = 1650;
      totalRevenue = results.units * avgRent * 12;
      noi = totalRevenue * 0.55; // 55% NOI margin
    } else if (typology === 'industrial') {
      hardCosts = results.warehouseSF * 95; // $95/SF industrial
      softCosts = hardCosts * 0.20;
      const avgRent = 9.50; // $/SF/year NNN
      totalRevenue = results.warehouseSF * avgRent;
      noi = totalRevenue * 0.92; // NNN lease
    } else if (typology === 'singleFamily') {
      hardCosts = results.totalHomeSF * 165; // $165/SF homes
      softCosts = hardCosts * 0.15;
      const avgSalePrice = 425000;
      totalRevenue = results.totalLots * avgSalePrice;
      noi = totalRevenue * 0.18; // 18% margin on for-sale
    }
    
    const totalCost = landCost + hardCosts + softCosts;
    const yieldOnCost = (noi / totalCost * 100).toFixed(2);
    const capRate = typology === 'singleFamily' ? 'N/A (For-Sale)' : '5.5%';
    const estimatedValue = typology === 'singleFamily' ? totalRevenue : noi / 0.055;
    
    return {
      landCost,
      hardCosts,
      softCosts,
      totalCost,
      totalRevenue,
      noi,
      yieldOnCost,
      capRate,
      estimatedValue,
      profit: estimatedValue - totalCost,
      margin: ((estimatedValue - totalCost) / totalCost * 100).toFixed(1)
    };
  };

  // Update params when typology changes
  useEffect(() => {
    setParams(TYPOLOGY_CONFIGS[selectedTypology].defaultParams);
    setResults(null);
  }, [selectedTypology]);

  return (
    <div style={styles.container}>
      {/* Header */}
      <header style={styles.header}>
        <div style={styles.headerLeft}>
          <div style={styles.logo}>
            <span style={styles.logoIcon}>◆</span>
            <span style={styles.logoText}>SPD.AI</span>
          </div>
          <span style={styles.tagline}>Site Planning & Development Intelligence</span>
        </div>
        <div style={styles.headerCenter}>
          <div style={styles.tabGroup}>
            {['site', 'design', 'analyze', 'export'].map(tab => (
              <button
                key={tab}
                style={{
                  ...styles.tab,
                  ...(activeTab === tab ? styles.tabActive : {})
                }}
                onClick={() => setActiveTab(tab)}
              >
                {tab.charAt(0).toUpperCase() + tab.slice(1)}
              </button>
            ))}
          </div>
        </div>
        <div style={styles.headerRight}>
          <div style={styles.viewToggle}>
            <button
              style={{
                ...styles.viewBtn,
                ...(viewMode === '2d' ? styles.viewBtnActive : {})
              }}
              onClick={() => setViewMode('2d')}
            >
              2D
            </button>
            <button
              style={{
                ...styles.viewBtn,
                ...(viewMode === '3d' ? styles.viewBtnActive : {})
              }}
              onClick={() => setViewMode('3d')}
            >
              3D
            </button>
          </div>
          <div style={styles.userBadge}>
            <span style={styles.poweredBy}>Powered by</span>
            <span style={styles.biddeedBrand}>BidDeed.AI</span>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div style={styles.mainContent}>
        {/* Left Sidebar - Controls */}
        <aside style={styles.sidebar}>
          {/* Site Input Section */}
          <div style={styles.section}>
            <h3 style={styles.sectionTitle}>
              <span style={styles.sectionIcon}>📍</span>
              Site Definition
            </h3>
            
            <div style={styles.inputGroup}>
              <label style={styles.label}>Address or Parcel ID</label>
              <input
                type="text"
                style={styles.input}
                placeholder="Enter address or draw on map..."
                value={address}
                onChange={(e) => setAddress(e.target.value)}
              />
            </div>

            <div style={styles.inputRow}>
              <div style={styles.inputGroup}>
                <label style={styles.label}>Site Acreage</label>
                <input
                  type="number"
                  style={styles.input}
                  value={siteAcreage}
                  onChange={(e) => setSiteAcreage(parseFloat(e.target.value))}
                  step="0.1"
                />
              </div>
              <div style={styles.inputGroup}>
                <label style={styles.label}>Zoning</label>
                <select
                  style={styles.select}
                  value={zoning}
                  onChange={(e) => setZoning(e.target.value)}
                >
                  {Object.entries(BREVARD_ZONING_DATA).map(([code, data]) => (
                    <option key={code} value={code}>
                      {code} - {data.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div style={styles.zoningInfo}>
              <div style={styles.zoningRow}>
                <span>Max Density:</span>
                <strong>{BREVARD_ZONING_DATA[zoning].maxDensity} units/acre</strong>
              </div>
              <div style={styles.zoningRow}>
                <span>Max Height:</span>
                <strong>{BREVARD_ZONING_DATA[zoning].maxHeight} ft</strong>
              </div>
            </div>
          </div>

          {/* Typology Selection */}
          <div style={styles.section}>
            <h3 style={styles.sectionTitle}>
              <span style={styles.sectionIcon}>🏗️</span>
              Development Type
            </h3>
            
            <div style={styles.typologyGrid}>
              {Object.entries(TYPOLOGY_CONFIGS).map(([key, config]) => (
                <button
                  key={key}
                  style={{
                    ...styles.typologyBtn,
                    ...(selectedTypology === key ? {
                      ...styles.typologyBtnActive,
                      borderColor: config.color,
                      backgroundColor: `${config.color}15`
                    } : {})
                  }}
                  onClick={() => setSelectedTypology(key)}
                >
                  <span style={styles.typologyIcon}>{config.icon}</span>
                  <span style={styles.typologyName}>{config.name}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Parameters */}
          <div style={styles.section}>
            <h3 style={styles.sectionTitle}>
              <span style={styles.sectionIcon}>⚙️</span>
              Parameters
            </h3>
            
            {selectedTypology === 'multifamily' && (
              <div style={styles.paramGrid}>
                <div style={styles.paramGroup}>
                  <label style={styles.paramLabel}>Parking Ratio</label>
                  <input
                    type="number"
                    style={styles.paramInput}
                    value={params.parkingRatio}
                    onChange={(e) => setParams({...params, parkingRatio: parseFloat(e.target.value)})}
                    step="0.1"
                  />
                  <span style={styles.paramUnit}>spaces/unit</span>
                </div>
                <div style={styles.paramGroup}>
                  <label style={styles.paramLabel}>Corridor Width</label>
                  <input
                    type="number"
                    style={styles.paramInput}
                    value={params.corridorWidth}
                    onChange={(e) => setParams({...params, corridorWidth: parseInt(e.target.value)})}
                  />
                  <span style={styles.paramUnit}>feet</span>
                </div>
                <div style={styles.unitMixSection}>
                  <label style={styles.paramLabel}>Unit Mix (%)</label>
                  <div style={styles.unitMixGrid}>
                    {['studio', 'oneBed', 'twoBed', 'threeBed'].map(type => (
                      <div key={type} style={styles.unitMixItem}>
                        <span style={styles.unitMixLabel}>
                          {type === 'studio' ? 'Studio' : 
                           type === 'oneBed' ? '1BR' :
                           type === 'twoBed' ? '2BR' : '3BR'}
                        </span>
                        <input
                          type="number"
                          style={styles.unitMixInput}
                          value={params.unitMix[type]}
                          onChange={(e) => setParams({
                            ...params,
                            unitMix: {...params.unitMix, [type]: parseInt(e.target.value)}
                          })}
                        />
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {selectedTypology === 'industrial' && (
              <div style={styles.paramGrid}>
                <div style={styles.paramGroup}>
                  <label style={styles.paramLabel}>Clear Height</label>
                  <input
                    type="number"
                    style={styles.paramInput}
                    value={params.clearHeight}
                    onChange={(e) => setParams({...params, clearHeight: parseInt(e.target.value)})}
                  />
                  <span style={styles.paramUnit}>feet</span>
                </div>
                <div style={styles.paramGroup}>
                  <label style={styles.paramLabel}>Bay Depth</label>
                  <input
                    type="number"
                    style={styles.paramInput}
                    value={params.bayDepth}
                    onChange={(e) => setParams({...params, bayDepth: parseInt(e.target.value)})}
                  />
                  <span style={styles.paramUnit}>feet</span>
                </div>
                <div style={styles.paramGroup}>
                  <label style={styles.paramLabel}>Yard Depth</label>
                  <input
                    type="number"
                    style={styles.paramInput}
                    value={params.yardDepth}
                    onChange={(e) => setParams({...params, yardDepth: parseInt(e.target.value)})}
                  />
                  <span style={styles.paramUnit}>feet</span>
                </div>
              </div>
            )}
          </div>

          {/* Generate Button */}
          <button
            style={{
              ...styles.generateBtn,
              ...(isGenerating ? styles.generateBtnLoading : {})
            }}
            onClick={generateFeasibility}
            disabled={isGenerating}
          >
            {isGenerating ? (
              <>
                <span style={styles.spinner}></span>
                Generating...
              </>
            ) : (
              <>
                <span style={styles.generateIcon}>⚡</span>
                Generate Feasibility
              </>
            )}
          </button>
        </aside>

        {/* Map Area */}
        <main style={styles.mapArea}>
          <div style={styles.mapContainer}>
            {/* Simulated Map View */}
            <div style={styles.mapPlaceholder}>
              <div style={styles.mapOverlay}>
                <div style={styles.mapTools}>
                  <button style={styles.mapTool} title="Draw Polygon">
                    <span>⬡</span>
                  </button>
                  <button style={styles.mapTool} title="Draw Rectangle">
                    <span>▢</span>
                  </button>
                  <button style={styles.mapTool} title="Select Parcel">
                    <span>◎</span>
                  </button>
                  <button style={styles.mapTool} title="Measure">
                    <span>📏</span>
                  </button>
                </div>
                
                <div style={styles.mapCenter}>
                  <div style={styles.sitePolygon}>
                    <div style={styles.siteLabel}>
                      {siteAcreage} AC
                      <br />
                      <small>{(siteAcreage * 43560).toLocaleString()} SF</small>
                    </div>
                  </div>
                </div>
                
                <div style={styles.mapInfo}>
                  <span>📍 Brevard County, FL</span>
                  <span>🏷️ Zoning: {zoning}</span>
                </div>
              </div>
              
              {/* Grid pattern background */}
              <svg style={styles.gridPattern} xmlns="http://www.w3.org/2000/svg">
                <defs>
                  <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
                    <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#E2E8F0" strokeWidth="1"/>
                  </pattern>
                </defs>
                <rect width="100%" height="100%" fill="url(#grid)" />
              </svg>
            </div>
          </div>
        </main>

        {/* Right Sidebar - Results */}
        <aside style={styles.resultsSidebar}>
          {results ? (
            <>
              {/* Results Header */}
              <div style={styles.resultsHeader}>
                <div style={styles.resultsTitle}>
                  <span style={{fontSize: '24px'}}>{TYPOLOGY_CONFIGS[selectedTypology].icon}</span>
                  <div>
                    <h3 style={styles.resultsTitleText}>{results.typology}</h3>
                    <span style={styles.resultsSubtitle}>Feasibility Analysis</span>
                  </div>
                </div>
                <div style={styles.confidenceBadge}>
                  <span style={styles.confidenceIcon}>✓</span>
                  High Confidence
                </div>
              </div>

              {/* Key Metrics */}
              <div style={styles.metricsGrid}>
                {selectedTypology === 'multifamily' && (
                  <>
                    <MetricCard label="Total Units" value={results.units} icon="🏢" />
                    <MetricCard label="Gross SF" value={results.grossSF.toLocaleString()} icon="📐" />
                    <MetricCard label="Stories" value={results.floors} icon="🏗️" />
                    <MetricCard label="Parking" value={results.parkingSpaces} icon="🚗" />
                    <MetricCard label="Density" value={`${results.density}/ac`} icon="📊" />
                    <MetricCard label="FAR" value={results.far} icon="📈" />
                  </>
                )}
                {selectedTypology === 'industrial' && (
                  <>
                    <MetricCard label="Warehouse SF" value={results.warehouseSF.toLocaleString()} icon="🏭" />
                    <MetricCard label="Clear Height" value={`${results.clearHeight}'`} icon="📏" />
                    <MetricCard label="Dock Doors" value={results.dockDoors} icon="🚚" />
                    <MetricCard label="Trailer Spaces" value={results.trailerSpaces} icon="🚛" />
                    <MetricCard label="Car Parking" value={results.carParking} icon="🚗" />
                    <MetricCard label="Total Bays" value={results.totalBays} icon="📦" />
                  </>
                )}
                {selectedTypology === 'singleFamily' && (
                  <>
                    <MetricCard label="Total Lots" value={results.totalLots} icon="🏠" />
                    <MetricCard label="Avg Lot Size" value={results.avgLotSize.toLocaleString()} icon="📐" />
                    <MetricCard label="Density" value={`${results.density}/ac`} icon="📊" />
                    <MetricCard label="Total Home SF" value={results.totalHomeSF.toLocaleString()} icon="🏗️" />
                  </>
                )}
              </div>

              {/* Unit Mix (for multifamily) */}
              {selectedTypology === 'multifamily' && (
                <div style={styles.unitMixResults}>
                  <h4 style={styles.sectionTitleSmall}>Unit Mix Breakdown</h4>
                  <div style={styles.unitMixBars}>
                    {Object.entries(results.unitMix).map(([type, count]) => (
                      <div key={type} style={styles.unitMixBar}>
                        <div style={styles.unitMixBarLabel}>
                          <span>{type === 'studio' ? 'Studio' : type === 'oneBed' ? '1BR' : type === 'twoBed' ? '2BR' : '3BR'}</span>
                          <span>{count} units</span>
                        </div>
                        <div style={styles.unitMixBarTrack}>
                          <div 
                            style={{
                              ...styles.unitMixBarFill,
                              width: `${(count / results.units) * 100}%`,
                              backgroundColor: type === 'studio' ? '#94A3B8' : 
                                              type === 'oneBed' ? '#3B82F6' :
                                              type === 'twoBed' ? '#10B981' : '#8B5CF6'
                            }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Pro Forma Toggle */}
              <button
                style={styles.proFormaToggle}
                onClick={() => setShowProForma(!showProForma)}
              >
                <span>💰</span>
                <span>Pro Forma Analysis</span>
                <span style={{transform: showProForma ? 'rotate(180deg)' : 'rotate(0deg)', transition: 'transform 0.2s'}}>▼</span>
              </button>

              {/* Pro Forma Details */}
              {showProForma && results.proForma && (
                <div style={styles.proFormaSection}>
                  <div style={styles.proFormaGrid}>
                    <div style={styles.proFormaItem}>
                      <span style={styles.proFormaLabel}>Land Cost</span>
                      <span style={styles.proFormaValue}>${(results.proForma.landCost / 1000000).toFixed(2)}M</span>
                    </div>
                    <div style={styles.proFormaItem}>
                      <span style={styles.proFormaLabel}>Hard Costs</span>
                      <span style={styles.proFormaValue}>${(results.proForma.hardCosts / 1000000).toFixed(2)}M</span>
                    </div>
                    <div style={styles.proFormaItem}>
                      <span style={styles.proFormaLabel}>Soft Costs</span>
                      <span style={styles.proFormaValue}>${(results.proForma.softCosts / 1000000).toFixed(2)}M</span>
                    </div>
                    <div style={{...styles.proFormaItem, ...styles.proFormaTotal}}>
                      <span style={styles.proFormaLabel}>Total Cost</span>
                      <span style={styles.proFormaValue}>${(results.proForma.totalCost / 1000000).toFixed(2)}M</span>
                    </div>
                  </div>
                  
                  <div style={styles.proFormaDivider} />
                  
                  <div style={styles.proFormaGrid}>
                    <div style={styles.proFormaItem}>
                      <span style={styles.proFormaLabel}>Annual Revenue</span>
                      <span style={styles.proFormaValue}>${(results.proForma.totalRevenue / 1000000).toFixed(2)}M</span>
                    </div>
                    <div style={styles.proFormaItem}>
                      <span style={styles.proFormaLabel}>NOI</span>
                      <span style={styles.proFormaValue}>${(results.proForma.noi / 1000000).toFixed(2)}M</span>
                    </div>
                    <div style={styles.proFormaItem}>
                      <span style={styles.proFormaLabel}>Yield on Cost</span>
                      <span style={{...styles.proFormaValue, color: COLORS.success}}>{results.proForma.yieldOnCost}%</span>
                    </div>
                    <div style={styles.proFormaItem}>
                      <span style={styles.proFormaLabel}>Est. Value</span>
                      <span style={{...styles.proFormaValue, color: COLORS.accent}}>${(results.proForma.estimatedValue / 1000000).toFixed(2)}M</span>
                    </div>
                  </div>

                  <div style={styles.profitBanner}>
                    <span style={styles.profitLabel}>Estimated Profit</span>
                    <span style={styles.profitValue}>${(results.proForma.profit / 1000000).toFixed(2)}M</span>
                    <span style={styles.profitMargin}>({results.proForma.margin}% margin)</span>
                  </div>
                </div>
              )}

              {/* Export Actions */}
              <div style={styles.exportActions}>
                <button style={styles.exportBtn}>
                  <span>📄</span> Export PDF
                </button>
                <button style={styles.exportBtn}>
                  <span>📊</span> Export Excel
                </button>
                <button style={{...styles.exportBtn, ...styles.exportBtnPrimary}}>
                  <span>🔗</span> Share Report
                </button>
              </div>
            </>
          ) : (
            <div style={styles.emptyResults}>
              <div style={styles.emptyIcon}>📊</div>
              <h3 style={styles.emptyTitle}>No Analysis Yet</h3>
              <p style={styles.emptyText}>
                Define your site parameters and click "Generate Feasibility" to see results.
              </p>
            </div>
          )}
        </aside>
      </div>

      {/* Footer */}
      <footer style={styles.footer}>
        <span>© 2026 BidDeed.AI / Everest Capital USA</span>
        <span style={styles.footerDivider}>•</span>
        <span>SPD.AI Site Planning Intelligence</span>
        <span style={styles.footerDivider}>•</span>
        <span>Brevard County, Florida</span>
      </footer>
    </div>
  );
}

// Metric Card Component
function MetricCard({ label, value, icon }) {
  return (
    <div style={styles.metricCard}>
      <div style={styles.metricIcon}>{icon}</div>
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
  container: {
    display: 'flex',
    flexDirection: 'column',
    height: '100vh',
    backgroundColor: '#F1F5F9',
    fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
    color: COLORS.textPrimary
  },
  
  // Header
  header: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '12px 24px',
    backgroundColor: COLORS.primary,
    borderBottom: `1px solid ${COLORS.secondary}`,
    zIndex: 100
  },
  headerLeft: {
    display: 'flex',
    alignItems: 'center',
    gap: '16px'
  },
  logo: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px'
  },
  logoIcon: {
    fontSize: '24px',
    color: COLORS.accent
  },
  logoText: {
    fontSize: '20px',
    fontWeight: '700',
    color: '#fff',
    letterSpacing: '-0.5px'
  },
  tagline: {
    fontSize: '12px',
    color: '#94A3B8',
    borderLeft: '1px solid #334155',
    paddingLeft: '16px'
  },
  headerCenter: {
    flex: 1,
    display: 'flex',
    justifyContent: 'center'
  },
  tabGroup: {
    display: 'flex',
    backgroundColor: COLORS.secondary,
    borderRadius: '8px',
    padding: '4px'
  },
  tab: {
    padding: '8px 20px',
    border: 'none',
    background: 'transparent',
    color: '#94A3B8',
    fontSize: '13px',
    fontWeight: '500',
    cursor: 'pointer',
    borderRadius: '6px',
    transition: 'all 0.2s'
  },
  tabActive: {
    backgroundColor: COLORS.accent,
    color: '#fff'
  },
  headerRight: {
    display: 'flex',
    alignItems: 'center',
    gap: '16px'
  },
  viewToggle: {
    display: 'flex',
    backgroundColor: COLORS.secondary,
    borderRadius: '6px',
    padding: '2px'
  },
  viewBtn: {
    padding: '6px 12px',
    border: 'none',
    background: 'transparent',
    color: '#94A3B8',
    fontSize: '12px',
    fontWeight: '600',
    cursor: 'pointer',
    borderRadius: '4px'
  },
  viewBtnActive: {
    backgroundColor: '#334155',
    color: '#fff'
  },
  userBadge: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'flex-end'
  },
  poweredBy: {
    fontSize: '10px',
    color: '#64748B',
    textTransform: 'uppercase',
    letterSpacing: '0.5px'
  },
  biddeedBrand: {
    fontSize: '13px',
    fontWeight: '600',
    color: COLORS.accent
  },

  // Main Content
  mainContent: {
    display: 'flex',
    flex: 1,
    overflow: 'hidden'
  },

  // Left Sidebar
  sidebar: {
    width: '320px',
    backgroundColor: '#fff',
    borderRight: `1px solid ${COLORS.border}`,
    display: 'flex',
    flexDirection: 'column',
    overflow: 'auto'
  },
  section: {
    padding: '20px',
    borderBottom: `1px solid ${COLORS.border}`
  },
  sectionTitle: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    fontSize: '13px',
    fontWeight: '600',
    color: COLORS.textPrimary,
    marginBottom: '16px',
    textTransform: 'uppercase',
    letterSpacing: '0.5px'
  },
  sectionIcon: {
    fontSize: '16px'
  },
  inputGroup: {
    marginBottom: '12px'
  },
  inputRow: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: '12px'
  },
  label: {
    display: 'block',
    fontSize: '12px',
    fontWeight: '500',
    color: COLORS.textSecondary,
    marginBottom: '6px'
  },
  input: {
    width: '100%',
    padding: '10px 12px',
    border: `1px solid ${COLORS.border}`,
    borderRadius: '8px',
    fontSize: '14px',
    color: COLORS.textPrimary,
    backgroundColor: COLORS.surface,
    outline: 'none',
    transition: 'border-color 0.2s',
    boxSizing: 'border-box'
  },
  select: {
    width: '100%',
    padding: '10px 12px',
    border: `1px solid ${COLORS.border}`,
    borderRadius: '8px',
    fontSize: '14px',
    color: COLORS.textPrimary,
    backgroundColor: COLORS.surface,
    cursor: 'pointer',
    boxSizing: 'border-box'
  },
  zoningInfo: {
    backgroundColor: COLORS.surface,
    borderRadius: '8px',
    padding: '12px',
    marginTop: '12px'
  },
  zoningRow: {
    display: 'flex',
    justifyContent: 'space-between',
    fontSize: '13px',
    color: COLORS.textSecondary,
    marginBottom: '6px'
  },
  typologyGrid: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: '8px'
  },
  typologyBtn: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    padding: '16px 12px',
    border: `2px solid ${COLORS.border}`,
    borderRadius: '12px',
    backgroundColor: '#fff',
    cursor: 'pointer',
    transition: 'all 0.2s'
  },
  typologyBtnActive: {
    borderWidth: '2px'
  },
  typologyIcon: {
    fontSize: '24px',
    marginBottom: '6px'
  },
  typologyName: {
    fontSize: '11px',
    fontWeight: '500',
    color: COLORS.textSecondary
  },
  paramGrid: {
    display: 'flex',
    flexDirection: 'column',
    gap: '12px'
  },
  paramGroup: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px'
  },
  paramLabel: {
    flex: 1,
    fontSize: '13px',
    color: COLORS.textSecondary
  },
  paramInput: {
    width: '70px',
    padding: '8px',
    border: `1px solid ${COLORS.border}`,
    borderRadius: '6px',
    fontSize: '14px',
    textAlign: 'center'
  },
  paramUnit: {
    fontSize: '11px',
    color: COLORS.textSecondary,
    width: '70px'
  },
  unitMixSection: {
    marginTop: '8px'
  },
  unitMixGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(4, 1fr)',
    gap: '8px',
    marginTop: '8px'
  },
  unitMixItem: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: '4px'
  },
  unitMixLabel: {
    fontSize: '11px',
    color: COLORS.textSecondary
  },
  unitMixInput: {
    width: '100%',
    padding: '6px',
    border: `1px solid ${COLORS.border}`,
    borderRadius: '4px',
    fontSize: '13px',
    textAlign: 'center'
  },
  generateBtn: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '8px',
    margin: '20px',
    padding: '14px 24px',
    backgroundColor: COLORS.accent,
    color: '#fff',
    border: 'none',
    borderRadius: '10px',
    fontSize: '15px',
    fontWeight: '600',
    cursor: 'pointer',
    transition: 'all 0.2s'
  },
  generateBtnLoading: {
    backgroundColor: '#64748B'
  },
  generateIcon: {
    fontSize: '18px'
  },
  spinner: {
    width: '16px',
    height: '16px',
    border: '2px solid rgba(255,255,255,0.3)',
    borderTopColor: '#fff',
    borderRadius: '50%',
    animation: 'spin 0.8s linear infinite'
  },

  // Map Area
  mapArea: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    overflow: 'hidden'
  },
  mapContainer: {
    flex: 1,
    position: 'relative',
    backgroundColor: '#E2E8F0'
  },
  mapPlaceholder: {
    width: '100%',
    height: '100%',
    position: 'relative',
    overflow: 'hidden'
  },
  gridPattern: {
    position: 'absolute',
    top: 0,
    left: 0,
    width: '100%',
    height: '100%'
  },
  mapOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    display: 'flex',
    flexDirection: 'column',
    zIndex: 10
  },
  mapTools: {
    position: 'absolute',
    top: '16px',
    left: '16px',
    display: 'flex',
    flexDirection: 'column',
    gap: '4px',
    backgroundColor: '#fff',
    borderRadius: '8px',
    padding: '4px',
    boxShadow: '0 2px 8px rgba(0,0,0,0.15)'
  },
  mapTool: {
    width: '36px',
    height: '36px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    border: 'none',
    backgroundColor: 'transparent',
    borderRadius: '6px',
    cursor: 'pointer',
    fontSize: '18px',
    transition: 'background-color 0.2s'
  },
  mapCenter: {
    flex: 1,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center'
  },
  sitePolygon: {
    width: '300px',
    height: '200px',
    backgroundColor: 'rgba(59, 130, 246, 0.2)',
    border: '3px dashed #3B82F6',
    borderRadius: '8px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center'
  },
  siteLabel: {
    fontSize: '24px',
    fontWeight: '700',
    color: COLORS.accent,
    textAlign: 'center'
  },
  mapInfo: {
    position: 'absolute',
    bottom: '16px',
    left: '16px',
    display: 'flex',
    gap: '16px',
    backgroundColor: 'rgba(255,255,255,0.95)',
    padding: '8px 16px',
    borderRadius: '8px',
    fontSize: '13px',
    color: COLORS.textSecondary,
    boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
  },

  // Results Sidebar
  resultsSidebar: {
    width: '360px',
    backgroundColor: '#fff',
    borderLeft: `1px solid ${COLORS.border}`,
    display: 'flex',
    flexDirection: 'column',
    overflow: 'auto'
  },
  resultsHeader: {
    padding: '20px',
    borderBottom: `1px solid ${COLORS.border}`,
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'flex-start'
  },
  resultsTitle: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px'
  },
  resultsTitleText: {
    fontSize: '18px',
    fontWeight: '600',
    margin: 0
  },
  resultsSubtitle: {
    fontSize: '12px',
    color: COLORS.textSecondary
  },
  confidenceBadge: {
    display: 'flex',
    alignItems: 'center',
    gap: '4px',
    padding: '4px 10px',
    backgroundColor: '#DCFCE7',
    color: '#166534',
    borderRadius: '20px',
    fontSize: '11px',
    fontWeight: '500'
  },
  confidenceIcon: {
    fontSize: '12px'
  },
  metricsGrid: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: '8px',
    padding: '16px'
  },
  metricCard: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
    padding: '12px',
    backgroundColor: COLORS.surface,
    borderRadius: '10px'
  },
  metricIcon: {
    fontSize: '20px'
  },
  metricContent: {
    display: 'flex',
    flexDirection: 'column'
  },
  metricValue: {
    fontSize: '16px',
    fontWeight: '600',
    color: COLORS.textPrimary
  },
  metricLabel: {
    fontSize: '11px',
    color: COLORS.textSecondary
  },
  unitMixResults: {
    padding: '16px',
    borderTop: `1px solid ${COLORS.border}`
  },
  sectionTitleSmall: {
    fontSize: '12px',
    fontWeight: '600',
    color: COLORS.textSecondary,
    marginBottom: '12px',
    textTransform: 'uppercase',
    letterSpacing: '0.5px'
  },
  unitMixBars: {
    display: 'flex',
    flexDirection: 'column',
    gap: '8px'
  },
  unitMixBar: {
    display: 'flex',
    flexDirection: 'column',
    gap: '4px'
  },
  unitMixBarLabel: {
    display: 'flex',
    justifyContent: 'space-between',
    fontSize: '12px',
    color: COLORS.textSecondary
  },
  unitMixBarTrack: {
    height: '8px',
    backgroundColor: COLORS.surface,
    borderRadius: '4px',
    overflow: 'hidden'
  },
  unitMixBarFill: {
    height: '100%',
    borderRadius: '4px',
    transition: 'width 0.5s ease'
  },
  proFormaToggle: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    width: '100%',
    padding: '14px 16px',
    border: 'none',
    borderTop: `1px solid ${COLORS.border}`,
    borderBottom: `1px solid ${COLORS.border}`,
    backgroundColor: COLORS.surface,
    cursor: 'pointer',
    fontSize: '14px',
    fontWeight: '500',
    color: COLORS.textPrimary
  },
  proFormaSection: {
    padding: '16px'
  },
  proFormaGrid: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: '12px'
  },
  proFormaItem: {
    display: 'flex',
    flexDirection: 'column',
    gap: '2px'
  },
  proFormaTotal: {
    gridColumn: 'span 2',
    backgroundColor: COLORS.surface,
    padding: '10px',
    borderRadius: '8px'
  },
  proFormaLabel: {
    fontSize: '11px',
    color: COLORS.textSecondary
  },
  proFormaValue: {
    fontSize: '15px',
    fontWeight: '600',
    color: COLORS.textPrimary
  },
  proFormaDivider: {
    height: '1px',
    backgroundColor: COLORS.border,
    margin: '16px 0'
  },
  profitBanner: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    padding: '16px',
    backgroundColor: '#DCFCE7',
    borderRadius: '10px',
    marginTop: '16px'
  },
  profitLabel: {
    fontSize: '11px',
    color: '#166534',
    textTransform: 'uppercase',
    letterSpacing: '0.5px'
  },
  profitValue: {
    fontSize: '28px',
    fontWeight: '700',
    color: '#166534'
  },
  profitMargin: {
    fontSize: '13px',
    color: '#166534'
  },
  exportActions: {
    display: 'flex',
    gap: '8px',
    padding: '16px',
    borderTop: `1px solid ${COLORS.border}`,
    marginTop: 'auto'
  },
  exportBtn: {
    flex: 1,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '6px',
    padding: '10px',
    border: `1px solid ${COLORS.border}`,
    borderRadius: '8px',
    backgroundColor: '#fff',
    fontSize: '12px',
    fontWeight: '500',
    cursor: 'pointer',
    transition: 'all 0.2s'
  },
  exportBtnPrimary: {
    backgroundColor: COLORS.accent,
    borderColor: COLORS.accent,
    color: '#fff'
  },
  emptyResults: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '40px',
    textAlign: 'center'
  },
  emptyIcon: {
    fontSize: '48px',
    marginBottom: '16px',
    opacity: 0.5
  },
  emptyTitle: {
    fontSize: '16px',
    fontWeight: '600',
    color: COLORS.textPrimary,
    marginBottom: '8px'
  },
  emptyText: {
    fontSize: '13px',
    color: COLORS.textSecondary,
    lineHeight: 1.5
  },

  // Footer
  footer: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '8px',
    padding: '12px',
    backgroundColor: COLORS.primary,
    color: '#64748B',
    fontSize: '12px'
  },
  footerDivider: {
    opacity: 0.5
  }
};

// Add keyframes for spinner animation
const styleSheet = document.createElement('style');
styleSheet.textContent = `
  @keyframes spin {
    to { transform: rotate(360deg); }
  }
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
`;
document.head.appendChild(styleSheet);
