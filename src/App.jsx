import React, { useState, useEffect, useCallback, useRef } from 'react';

// ============================================================================
// SPD.AI V3.2 - Site Planning & Development AI Platform
// ============================================================================
// V1 UI/UX + Real LLM via Smart Router V7.4 (90% FREE tier)
// © 2026 BidDeed.AI / Everest Capital USA - All Rights Reserved
// ============================================================================

// API Configuration
const API_BASE = window.location.hostname === 'localhost' 
  ? 'http://localhost:8788' 
  : '';  // Same origin in production

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

// Storage unit mix for calculations
const STORAGE_UNIT_MIX = {
  '5x5': { sf: 25, pct: 10, rentPerSF: 2.00 },
  '5x10': { sf: 50, pct: 25, rentPerSF: 1.75 },
  '10x10': { sf: 100, pct: 30, rentPerSF: 1.50 },
  '10x15': { sf: 150, pct: 15, rentPerSF: 1.35 },
  '10x20': { sf: 200, pct: 12, rentPerSF: 1.25 },
  '10x30': { sf: 300, pct: 8, rentPerSF: 1.15 },
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
  const [inputMode, setInputMode] = useState('chat');
  
  // Chat state
  const [messages, setMessages] = useState([
    {
      id: 1,
      role: 'assistant',
      content: "Hi! I'm SPD.AI, your site planning assistant powered by Smart Router V7.4.\n\nI can help you with:\n• Feasibility analysis for 8 development types\n• Zoning requirements lookup\n• Pro forma calculations\n• Site comparison and recommendations\n\nTell me about your site - for example:\n• \"I have 5 acres in Titusville, zoned C-2\"\n• \"What can I build on 10 acres with R-3 zoning?\"\n• \"Compare self-storage vs industrial for my 8-acre site\"",
      timestamp: new Date(),
      metadata: { tier: 'SYSTEM', model: 'welcome' }
    }
  ]);
  const [chatInput, setChatInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [apiStatus, setApiStatus] = useState('unknown'); // 'unknown', 'connected', 'error'
  const chatEndRef = useRef(null);
  const [conversationHistory, setConversationHistory] = useState([]);

  // Auto-scroll chat
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Check API health on mount
  useEffect(() => {
    checkApiHealth();
  }, []);

  const checkApiHealth = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/chat/health`);
      if (res.ok) {
        setApiStatus('connected');
      } else {
        setApiStatus('error');
      }
    } catch {
      setApiStatus('error');
    }
  };

  // ============================================================================
  // CHAT API CALL
  // ============================================================================

  const sendToAPI = useCallback(async (message) => {
    try {
      const response = await fetch(`${API_BASE}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message,
          messages: conversationHistory,
          siteContext: {
            acreage: siteAcreage,
            zoning,
            typology: selectedTypology,
          },
        }),
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('API call failed:', error);
      return {
        response: `I'm having trouble connecting to the AI service. Please try again or switch to Form Mode.\n\n_Error: ${error.message}_`,
        metadata: { tier: 'ERROR', error: error.message },
      };
    }
  }, [conversationHistory, siteAcreage, zoning, selectedTypology]);

  // ============================================================================
  // HANDLE CHAT SUBMIT
  // ============================================================================

  const handleChatSubmit = useCallback(async () => {
    if (!chatInput.trim()) return;

    const userMessage = {
      id: messages.length + 1,
      role: 'user',
      content: chatInput.trim(),
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setConversationHistory(prev => [...prev, { role: 'user', content: chatInput.trim() }]);
    setChatInput('');
    setIsTyping(true);

    // Call the real API
    const apiResponse = await sendToAPI(chatInput.trim());

    const assistantMessage = {
      id: messages.length + 2,
      role: 'assistant',
      content: apiResponse.response,
      timestamp: new Date(),
      metadata: apiResponse.metadata,
    };

    setMessages(prev => [...prev, assistantMessage]);
    setConversationHistory(prev => [...prev, { role: 'assistant', content: apiResponse.response }]);
    setIsTyping(false);

    // Try to extract site parameters from the conversation
    extractSiteParams(chatInput.trim(), apiResponse.response);
  }, [chatInput, messages, sendToAPI]);

  // Extract site parameters from conversation
  const extractSiteParams = (userMsg, aiResponse) => {
    const lower = userMsg.toLowerCase();
    
    // Extract acreage
    const acreMatch = lower.match(/(\d+(?:\.\d+)?)\s*(?:acre|ac)/);
    if (acreMatch) {
      setSiteAcreage(parseFloat(acreMatch[1]));
    }
    
    // Extract zoning
    const zoneMatch = lower.match(/([rcib]u?-?\d|pud)/i);
    if (zoneMatch) {
      const zoneCode = zoneMatch[1].toUpperCase().replace('-', '-');
      if (BREVARD_ZONING_DATA[zoneCode]) {
        setZoning(zoneCode);
      }
    }
    
    // Extract typology
    const typologyMap = {
      'apartment': 'multifamily', 'multifamily': 'multifamily', 'multi-family': 'multifamily',
      'storage': 'selfStorage', 'self-storage': 'selfStorage',
      'industrial': 'industrial', 'warehouse': 'industrial',
      'single-family': 'singleFamily', 'subdivision': 'singleFamily',
      'senior': 'seniorLiving', 'assisted': 'seniorLiving',
      'medical': 'medical', 'mob': 'medical',
      'retail': 'retail', 'shopping': 'retail',
      'hotel': 'hotel', 'hospitality': 'hotel',
    };
    
    for (const [keyword, typology] of Object.entries(typologyMap)) {
      if (lower.includes(keyword)) {
        setSelectedTypology(typology);
        break;
      }
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleChatSubmit();
    }
  };

  // ============================================================================
  // FORM-BASED FEASIBILITY
  // ============================================================================

  const generateFeasibility = useCallback(() => {
    setIsGenerating(true);
    
    setTimeout(() => {
      const siteSquareFeet = siteAcreage * 43560;
      const zoningData = BREVARD_ZONING_DATA[zoning] || BREVARD_ZONING_DATA['C-2'];
      const typology = TYPOLOGY_CONFIGS[selectedTypology];
      
      let results = {
        typology: typology.name,
        typologyKey: selectedTypology,
        icon: typology.icon,
        color: typology.color,
        acreage: siteAcreage,
        siteSquareFeet,
        zoning,
      };

      // Calculate based on typology (same logic as before)
      if (selectedTypology === 'multifamily') {
        const maxUnits = Math.floor(siteAcreage * (zoningData.maxDensity || 10));
        const grossSF = Math.round(maxUnits * 875 * 1.15);
        const floors = Math.min(Math.ceil(grossSF / (siteSquareFeet * 0.65)), Math.floor((zoningData.maxHeight || 45) / 10));
        results = { ...results, units: maxUnits, grossSF, floors, parkingSpaces: Math.ceil(maxUnits * params.parkingRatio), density: (maxUnits / siteAcreage).toFixed(1), far: (grossSF / siteSquareFeet).toFixed(2) };
        results.proForma = { landCost: siteAcreage * 150000, hardCosts: grossSF * 185, softCosts: grossSF * 185 * 0.25, totalCost: siteAcreage * 150000 + grossSF * 185 * 1.25, annualRevenue: maxUnits * 1650 * 12, noi: maxUnits * 1650 * 12 * 0.55, capRate: '5.5%' };
      } else if (selectedTypology === 'selfStorage') {
        const stories = params.stories || 1;
        const grossBuildingSF = siteSquareFeet * (stories === 1 ? 0.40 : 0.35) * stories;
        const netRentableSF = Math.round(grossBuildingSF * 0.85);
        let totalUnits = 0, monthlyRevenue = 0;
        const unitBreakdown = {};
        for (const [size, data] of Object.entries(STORAGE_UNIT_MIX)) {
          const count = Math.round((netRentableSF * data.pct / 100) / data.sf);
          unitBreakdown[size] = count;
          totalUnits += count;
          monthlyRevenue += count * data.sf * data.rentPerSF;
        }
        results = { ...results, stories, grossBuildingSF: Math.round(grossBuildingSF), netRentableSF, totalUnits, unitBreakdown, climateControlledPct: params.climateControlled, monthlyRevenue: Math.round(monthlyRevenue), avgRentPerSF: (monthlyRevenue / netRentableSF).toFixed(2) };
        const hardCostPerSF = stories === 1 ? 55 : 85;
        results.proForma = { landCost: siteAcreage * 125000, hardCosts: grossBuildingSF * hardCostPerSF, softCosts: grossBuildingSF * hardCostPerSF * 0.18, totalCost: siteAcreage * 125000 + grossBuildingSF * hardCostPerSF * 1.18, monthlyRevenue: Math.round(monthlyRevenue), annualRevenue: Math.round(monthlyRevenue * 12), noi: Math.round(monthlyRevenue * 12 * 0.88 * 0.60), capRate: '6.5%' };
      } else if (selectedTypology === 'industrial') {
        const warehouseSF = Math.round(siteSquareFeet * 0.55);
        results = { ...results, warehouseSF, clearHeight: params.clearHeight, dockDoors: Math.ceil(warehouseSF / 10000), trailerSpaces: Math.ceil(warehouseSF / 10000) * 2, carParking: Math.ceil(warehouseSF / 2000), far: (warehouseSF / siteSquareFeet).toFixed(2) };
        results.proForma = { landCost: siteAcreage * 100000, hardCosts: warehouseSF * 95, softCosts: warehouseSF * 95 * 0.20, totalCost: siteAcreage * 100000 + warehouseSF * 95 * 1.20, annualRevenue: warehouseSF * 9.50, noi: warehouseSF * 9.50 * 0.92, capRate: '6.5%' };
      } else if (selectedTypology === 'singleFamily') {
        const totalLots = Math.floor(siteSquareFeet * 0.70 / 7500);
        results = { ...results, totalLots, avgLotSize: 7500, avgHomeSize: 2200, density: (totalLots / siteAcreage).toFixed(1) };
        results.proForma = { landCost: siteAcreage * 125000, hardCosts: totalLots * 2200 * 165, softCosts: totalLots * 2200 * 165 * 0.15, totalCost: siteAcreage * 125000 + totalLots * 2200 * 165 * 1.15, totalRevenue: totalLots * 425000, capRate: 'N/A' };
      } else if (selectedTypology === 'seniorLiving') {
        const beds = Math.floor(siteAcreage * 25);
        const grossSF = Math.round(beds * 450 / 0.65);
        results = { ...results, beds, grossSF, floors: Math.min(Math.ceil(grossSF / (siteSquareFeet * 0.40)), 4), parkingSpaces: Math.ceil(beds * 0.5), monthlyRate: params.monthlyRate };
        results.proForma = { landCost: siteAcreage * 175000, hardCosts: grossSF * 225, softCosts: grossSF * 225 * 0.28, totalCost: siteAcreage * 175000 + grossSF * 225 * 1.28, monthlyRevenue: Math.round(beds * params.monthlyRate * 0.90), annualRevenue: Math.round(beds * params.monthlyRate * 12 * 0.90), noi: Math.round(beds * params.monthlyRate * 12 * 0.90 * 0.35), capRate: '7.0%' };
      } else if (selectedTypology === 'medical') {
        const stories = params.stories || 2;
        const grossSF = Math.round(siteSquareFeet * 0.35 * stories);
        results = { ...results, grossSF, floors: stories, parkingSpaces: Math.ceil(grossSF / 250), rentPerSF: params.rentPerSF, far: (grossSF / siteSquareFeet).toFixed(2) };
        results.proForma = { landCost: siteAcreage * 200000, hardCosts: grossSF * 275, softCosts: grossSF * 275 * 0.22, totalCost: siteAcreage * 200000 + grossSF * 275 * 1.22, annualRevenue: grossSF * params.rentPerSF, noi: grossSF * params.rentPerSF * 0.88, capRate: '6.25%' };
      } else if (selectedTypology === 'retail') {
        const grossSF = Math.round(siteSquareFeet * 0.25);
        results = { ...results, grossSF, parkingSpaces: Math.ceil(grossSF / 200), padSites: Math.floor(siteAcreage / 1.5), anchorSF: Math.round(grossSF * 0.4), shopSF: Math.round(grossSF * 0.6) };
        results.proForma = { landCost: siteAcreage * 175000, hardCosts: grossSF * 165, softCosts: grossSF * 165 * 0.18, totalCost: siteAcreage * 175000 + grossSF * 165 * 1.18, annualRevenue: grossSF * 22, noi: grossSF * 22 * 0.85, capRate: '6.75%' };
      } else if (selectedTypology === 'hotel') {
        const rooms = Math.floor(siteAcreage * 60);
        const grossSF = Math.round(rooms * 375 * 1.35);
        const revPAR = params.adr * 0.68;
        results = { ...results, rooms, grossSF, floors: Math.min(Math.ceil(grossSF / (siteSquareFeet * 0.35)), 5), parkingSpaces: Math.ceil(rooms * 0.8), adr: params.adr, occupancy: '68%', revPAR: revPAR.toFixed(2) };
        results.proForma = { landCost: siteAcreage * 200000, hardCosts: grossSF * 195, softCosts: grossSF * 195 * 0.25, totalCost: siteAcreage * 200000 + grossSF * 195 * 1.25, annualRevenue: Math.round(rooms * revPAR * 365), noi: Math.round(rooms * revPAR * 365 * 0.35), capRate: '8.0%' };
      }

      // Calculate profit metrics
      if (results.proForma) {
        if (results.proForma.noi) {
          results.proForma.yieldOnCost = ((results.proForma.noi / results.proForma.totalCost) * 100).toFixed(2);
          const capRateNum = parseFloat(results.proForma.capRate) / 100;
          results.proForma.estimatedValue = results.proForma.noi / capRateNum;
          results.proForma.profit = results.proForma.estimatedValue - results.proForma.totalCost;
        } else if (results.proForma.totalRevenue) {
          results.proForma.profit = results.proForma.totalRevenue - results.proForma.totalCost;
        }
        results.proForma.margin = ((results.proForma.profit / results.proForma.totalCost) * 100).toFixed(1);
      }

      setResults(results);
      setIsGenerating(false);
    }, 800);
  }, [siteAcreage, zoning, selectedTypology, params]);

  // Quick prompts
  const quickPrompts = [
    { label: '📦 5ac storage', prompt: 'I have 5 acres and want to build self-storage. What are my options?' },
    { label: '🏢 10ac apts', prompt: 'Analyze a 10-acre site for multifamily development with R-3 zoning' },
    { label: '🏭 8ac industrial', prompt: '8 acres zoned I-1 for industrial development. What can I build?' },
    { label: '📊 Compare', prompt: 'Compare self-storage vs industrial for a 5-acre C-2 site' },
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
            <button style={{...styles.modeBtn, ...(inputMode === 'chat' ? styles.modeBtnActive : {})}} onClick={() => setInputMode('chat')}>
              💬 Chat
            </button>
            <button style={{...styles.modeBtn, ...(inputMode === 'form' ? styles.modeBtnActive : {})}} onClick={() => setInputMode('form')}>
              📝 Form
            </button>
          </div>
        </div>
        <div style={styles.headerRight}>
          <div style={styles.apiStatus}>
            <span style={{...styles.statusDot, backgroundColor: apiStatus === 'connected' ? COLORS.success : apiStatus === 'error' ? COLORS.danger : COLORS.warning}}></span>
            <span style={styles.statusText}>{apiStatus === 'connected' ? 'AI Connected' : apiStatus === 'error' ? 'Offline' : 'Checking...'}</span>
          </div>
          <div style={styles.userBadge}>
            <span style={styles.poweredBy}>Powered by</span>
            <span style={styles.biddeedBrand}>Smart Router V7.4</span>
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
                    <div style={styles.messageBubbleWrapper}>
                      <div style={{...styles.messageBubble, ...(msg.role === 'user' ? styles.userBubble : styles.aiBubble)}}>
                        <MessageContent content={msg.content} />
                      </div>
                      {msg.metadata && msg.metadata.tier && msg.metadata.tier !== 'SYSTEM' && (
                        <div style={styles.metadataTag}>
                          {msg.metadata.tier === 'FREE' ? '🆓' : msg.metadata.tier === 'ERROR' ? '⚠️' : '⚡'} {msg.metadata.tier}
                          {msg.metadata.model && ` • ${msg.metadata.model.split('-').slice(0,2).join('-')}`}
                        </div>
                      )}
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
                    <button key={i} style={styles.quickPromptBtn} onClick={() => setChatInput(qp.prompt)}>
                      {qp.label}
                    </button>
                  ))}
                </div>
              )}
              
              {/* Chat Input */}
              <div style={styles.chatInputArea}>
                <textarea
                  style={styles.chatInput}
                  placeholder="Ask about your site..."
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  onKeyPress={handleKeyPress}
                  rows={2}
                />
                <button style={styles.sendBtn} onClick={handleChatSubmit} disabled={!chatInput.trim() || isTyping}>
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
                <h3 style={styles.sectionTitle}><span style={styles.sectionIcon}>📍</span> Site</h3>
                <div style={styles.inputRow}>
                  <div style={styles.inputGroup}>
                    <label style={styles.label}>Acreage</label>
                    <input type="number" style={styles.input} value={siteAcreage} onChange={(e) => setSiteAcreage(parseFloat(e.target.value) || 0)} step="0.1" />
                  </div>
                  <div style={styles.inputGroup}>
                    <label style={styles.label}>Zoning</label>
                    <select style={styles.select} value={zoning} onChange={(e) => setZoning(e.target.value)}>
                      {Object.entries(BREVARD_ZONING_DATA).map(([code]) => (
                        <option key={code} value={code}>{code}</option>
                      ))}
                    </select>
                  </div>
                </div>
              </div>

              <div style={styles.section}>
                <h3 style={styles.sectionTitle}><span style={styles.sectionIcon}>🏗️</span> Type</h3>
                <div style={styles.typologyGrid}>
                  {Object.entries(TYPOLOGY_CONFIGS).map(([key, config]) => (
                    <button key={key} style={{...styles.typologyBtn, ...(selectedTypology === key ? {...styles.typologyBtnActive, borderColor: config.color, backgroundColor: `${config.color}15`} : {})}} onClick={() => setSelectedTypology(key)}>
                      <span style={styles.typologyIcon}>{config.icon}</span>
                      <span style={styles.typologyName}>{config.name}</span>
                    </button>
                  ))}
                </div>
              </div>

              <div style={styles.section}>
                <h3 style={styles.sectionTitle}><span style={styles.sectionIcon}>⚙️</span> Params</h3>
                {selectedTypology === 'selfStorage' && (
                  <div style={styles.paramGrid}>
                    <div style={styles.paramGroup}>
                      <label style={styles.paramLabel}>Stories</label>
                      <select style={styles.paramSelect} value={params.stories} onChange={(e) => setParams({...params, stories: parseInt(e.target.value)})}>
                        {[1,2,3,4].map(n => <option key={n} value={n}>{n}-Story</option>)}
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
                    <label style={styles.paramLabel}>Parking/Unit</label>
                    <input type="number" style={styles.paramInput} value={params.parkingRatio} onChange={(e) => setParams({...params, parkingRatio: parseFloat(e.target.value)})} step="0.1" />
                  </div>
                )}
              </div>

              <button style={{...styles.generateBtn, ...(isGenerating ? styles.generateBtnLoading : {})}} onClick={generateFeasibility} disabled={isGenerating}>
                {isGenerating ? 'Generating...' : '⚡ Generate'}
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
                    <span style={styles.resultsSubtitle}>{results.acreage} ac • {results.zoning}</span>
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
              </div>

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
                    <div style={{...styles.proFormaItem, gridColumn: 'span 2', ...styles.proFormaTotal}}><span style={styles.proFormaLabel}>Total Cost</span><span style={styles.proFormaValue}>${(results.proForma.totalCost / 1000000).toFixed(2)}M</span></div>
                  </div>
                  <div style={styles.profitBanner}>
                    <span style={styles.profitLabel}>Profit</span>
                    <span style={styles.profitValue}>${(results.proForma.profit / 1000000).toFixed(2)}M</span>
                    <span style={styles.profitMargin}>{results.proForma.margin}%</span>
                  </div>
                </div>
              )}
            </>
          ) : (
            <div style={styles.emptyResults}>
              <div style={styles.emptyIcon}>📊</div>
              <h3 style={styles.emptyTitle}>No Analysis Yet</h3>
              <p style={styles.emptyText}>Use Chat or Form to analyze a site</p>
            </div>
          )}
        </aside>
      </div>

      {/* Footer */}
      <footer style={styles.footer}>
        <span>© 2026 BidDeed.AI</span>
        <span>•</span>
        <span>SPD.AI v3.2</span>
        <span>•</span>
        <span>Smart Router V7.4 (90% FREE)</span>
      </footer>
    </div>
  );
}

// Message Content Component
function MessageContent({ content }) {
  const lines = content.split('\n');
  return (
    <div>
      {lines.map((line, i) => {
        if (line.startsWith('•')) return <div key={i} style={{paddingLeft: '8px', margin: '2px 0'}}>{line}</div>;
        if (line.startsWith('**') && line.endsWith('**')) return <strong key={i} style={{display: 'block', margin: '4px 0'}}>{line.replace(/\*\*/g, '')}</strong>;
        if (line.startsWith('_') && line.endsWith('_')) return <em key={i} style={{display: 'block', color: '#64748B', fontSize: '12px'}}>{line.replace(/_/g, '')}</em>;
        if (line === '') return <br key={i} />;
        return <p key={i} style={{margin: '4px 0'}}>{line}</p>;
      })}
    </div>
  );
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
// STYLES (condensed)
// ============================================================================

const styles = {
  container: { display: 'flex', flexDirection: 'column', height: '100vh', backgroundColor: '#F1F5F9', fontFamily: "'Inter', sans-serif", color: COLORS.textPrimary },
  header: { display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '12px 24px', backgroundColor: COLORS.primary, zIndex: 100 },
  headerLeft: { display: 'flex', alignItems: 'center', gap: '16px' },
  logo: { display: 'flex', alignItems: 'center', gap: '8px' },
  logoIcon: { fontSize: '24px', color: COLORS.accent },
  logoText: { fontSize: '20px', fontWeight: '700', color: '#fff' },
  tagline: { fontSize: '12px', color: '#94A3B8', borderLeft: '1px solid #334155', paddingLeft: '16px' },
  headerCenter: { flex: 1, display: 'flex', justifyContent: 'center' },
  modeToggle: { display: 'flex', backgroundColor: COLORS.secondary, borderRadius: '8px', padding: '4px' },
  modeBtn: { padding: '8px 20px', border: 'none', background: 'transparent', color: '#94A3B8', fontSize: '13px', fontWeight: '500', cursor: 'pointer', borderRadius: '6px' },
  modeBtnActive: { backgroundColor: COLORS.accent, color: '#fff' },
  headerRight: { display: 'flex', alignItems: 'center', gap: '16px' },
  apiStatus: { display: 'flex', alignItems: 'center', gap: '6px' },
  statusDot: { width: '8px', height: '8px', borderRadius: '50%' },
  statusText: { fontSize: '11px', color: '#94A3B8' },
  userBadge: { display: 'flex', flexDirection: 'column', alignItems: 'flex-end' },
  poweredBy: { fontSize: '9px', color: '#64748B', textTransform: 'uppercase' },
  biddeedBrand: { fontSize: '12px', fontWeight: '600', color: COLORS.accent },
  mainContent: { display: 'flex', flex: 1, overflow: 'hidden' },
  sidebar: { width: '340px', backgroundColor: '#fff', borderRight: `1px solid ${COLORS.border}`, display: 'flex', flexDirection: 'column', overflow: 'hidden' },
  chatContainer: { display: 'flex', flexDirection: 'column', height: '100%' },
  chatMessages: { flex: 1, overflow: 'auto', padding: '16px', display: 'flex', flexDirection: 'column', gap: '12px' },
  messageWrapper: { display: 'flex', alignItems: 'flex-start', gap: '10px' },
  avatarAI: { width: '28px', height: '28px', display: 'flex', alignItems: 'center', justifyContent: 'center', background: `linear-gradient(135deg, ${COLORS.accent}, #8B5CF6)`, borderRadius: '6px', fontSize: '12px', fontWeight: '700', color: '#fff', flexShrink: 0 },
  messageBubbleWrapper: { display: 'flex', flexDirection: 'column', gap: '4px', maxWidth: '85%' },
  messageBubble: { padding: '10px 14px', borderRadius: '14px', fontSize: '13px', lineHeight: 1.5 },
  aiBubble: { backgroundColor: COLORS.surface, border: `1px solid ${COLORS.border}`, borderBottomLeftRadius: '4px' },
  userBubble: { backgroundColor: COLORS.accent, color: '#fff', borderBottomRightRadius: '4px', marginLeft: 'auto' },
  metadataTag: { fontSize: '10px', color: '#94A3B8', paddingLeft: '4px' },
  typingIndicator: { display: 'flex', gap: '4px', padding: '4px 0' },
  typingDot: { width: '6px', height: '6px', backgroundColor: COLORS.textSecondary, borderRadius: '50%', animation: 'typingPulse 1s infinite' },
  quickPrompts: { display: 'flex', gap: '6px', padding: '8px 16px', flexWrap: 'wrap', borderTop: `1px solid ${COLORS.border}` },
  quickPromptBtn: { padding: '6px 12px', backgroundColor: COLORS.surface, border: `1px solid ${COLORS.border}`, borderRadius: '20px', color: COLORS.textSecondary, fontSize: '11px', cursor: 'pointer' },
  chatInputArea: { display: 'flex', gap: '10px', padding: '12px 16px', borderTop: `1px solid ${COLORS.border}`, backgroundColor: COLORS.surface },
  chatInput: { flex: 1, padding: '10px 14px', border: `1px solid ${COLORS.border}`, borderRadius: '12px', fontSize: '13px', resize: 'none', fontFamily: 'inherit', outline: 'none' },
  sendBtn: { width: '40px', height: '40px', display: 'flex', alignItems: 'center', justifyContent: 'center', backgroundColor: COLORS.accent, border: 'none', borderRadius: '10px', color: '#fff', cursor: 'pointer', flexShrink: 0 },
  section: { padding: '16px 20px', borderBottom: `1px solid ${COLORS.border}` },
  sectionTitle: { display: 'flex', alignItems: 'center', gap: '8px', fontSize: '12px', fontWeight: '600', marginBottom: '12px', textTransform: 'uppercase' },
  sectionIcon: { fontSize: '14px' },
  inputRow: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' },
  inputGroup: { marginBottom: '10px' },
  label: { display: 'block', fontSize: '11px', fontWeight: '500', color: COLORS.textSecondary, marginBottom: '4px' },
  input: { width: '100%', padding: '10px 12px', border: `1px solid ${COLORS.border}`, borderRadius: '8px', fontSize: '14px', boxSizing: 'border-box' },
  select: { width: '100%', padding: '10px 12px', border: `1px solid ${COLORS.border}`, borderRadius: '8px', fontSize: '14px', boxSizing: 'border-box' },
  typologyGrid: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px' },
  typologyBtn: { display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '10px 6px', border: `2px solid ${COLORS.border}`, borderRadius: '10px', backgroundColor: '#fff', cursor: 'pointer' },
  typologyBtnActive: { borderWidth: '2px' },
  typologyIcon: { fontSize: '18px', marginBottom: '2px' },
  typologyName: { fontSize: '9px', fontWeight: '500', color: COLORS.textSecondary },
  paramGrid: { display: 'flex', flexDirection: 'column', gap: '10px' },
  paramGroup: { display: 'flex', alignItems: 'center', gap: '8px' },
  paramLabel: { flex: 1, fontSize: '12px', color: COLORS.textSecondary },
  paramInput: { width: '60px', padding: '8px', border: `1px solid ${COLORS.border}`, borderRadius: '6px', fontSize: '13px', textAlign: 'center' },
  paramSelect: { width: '120px', padding: '8px', border: `1px solid ${COLORS.border}`, borderRadius: '6px', fontSize: '12px' },
  generateBtn: { display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', margin: '16px 20px', padding: '14px', backgroundColor: COLORS.accent, color: '#fff', border: 'none', borderRadius: '10px', fontSize: '14px', fontWeight: '600', cursor: 'pointer' },
  generateBtnLoading: { backgroundColor: '#64748B' },
  mapArea: { flex: 1, display: 'flex', overflow: 'hidden' },
  mapContainer: { flex: 1, position: 'relative', backgroundColor: '#E2E8F0' },
  mapPlaceholder: { width: '100%', height: '100%', position: 'relative', overflow: 'hidden' },
  gridPattern: { position: 'absolute', top: 0, left: 0, width: '100%', height: '100%' },
  mapOverlay: { position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, display: 'flex', flexDirection: 'column', zIndex: 10 },
  mapCenter: { flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' },
  sitePolygon: { width: '280px', height: '180px', border: '3px dashed', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center' },
  siteLabel: { fontSize: '22px', fontWeight: '700', textAlign: 'center' },
  mapInfo: { position: 'absolute', bottom: '16px', left: '16px', display: 'flex', gap: '16px', backgroundColor: 'rgba(255,255,255,0.95)', padding: '8px 16px', borderRadius: '8px', fontSize: '13px', color: COLORS.textSecondary },
  resultsSidebar: { width: '320px', backgroundColor: '#fff', borderLeft: `1px solid ${COLORS.border}`, display: 'flex', flexDirection: 'column', overflow: 'auto' },
  resultsHeader: { padding: '16px', borderBottom: `1px solid ${COLORS.border}` },
  resultsTitle: { display: 'flex', alignItems: 'center', gap: '12px' },
  resultsTitleText: { fontSize: '16px', fontWeight: '600', margin: 0 },
  resultsSubtitle: { fontSize: '11px', color: COLORS.textSecondary },
  metricsGrid: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', padding: '12px' },
  metricCard: { display: 'flex', alignItems: 'center', gap: '8px', padding: '10px', backgroundColor: COLORS.surface, borderRadius: '8px' },
  metricIcon: { fontSize: '18px' },
  metricContent: { display: 'flex', flexDirection: 'column' },
  metricValue: { fontSize: '14px', fontWeight: '600' },
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
  proFormaTotal: { backgroundColor: COLORS.surface, padding: '8px', borderRadius: '6px' },
  proFormaLabel: { fontSize: '10px', color: COLORS.textSecondary },
  proFormaValue: { fontSize: '14px', fontWeight: '600' },
  profitBanner: { display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '14px', backgroundColor: '#DCFCE7', borderRadius: '10px', marginTop: '12px' },
  profitLabel: { fontSize: '10px', color: '#166534', textTransform: 'uppercase' },
  profitValue: { fontSize: '24px', fontWeight: '700', color: '#166534' },
  profitMargin: { fontSize: '12px', color: '#166534' },
  emptyResults: { flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '40px', textAlign: 'center' },
  emptyIcon: { fontSize: '40px', marginBottom: '12px', opacity: 0.5 },
  emptyTitle: { fontSize: '14px', fontWeight: '600', marginBottom: '8px' },
  emptyText: { fontSize: '12px', color: COLORS.textSecondary },
  footer: { display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', padding: '10px', backgroundColor: COLORS.primary, color: '#64748B', fontSize: '11px' },
};

const styleSheet = document.createElement('style');
styleSheet.textContent = `@keyframes typingPulse { 0%, 100% { opacity: 0.3; } 50% { opacity: 1; } }`;
document.head.appendChild(styleSheet);
