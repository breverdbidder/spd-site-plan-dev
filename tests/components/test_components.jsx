/**
 * Unit Tests for SPD.AI React Components
 * P2 Codebase Requirement: Additional unit tests
 * 
 * Tests cover:
 * - ChatInterface: Message handling, API calls, state management
 * - FormInterface: Input validation, typology selection
 * - Results: Display logic, pro forma rendering
 * - MapView: Site visualization
 * 
 * @author BidDeed.AI / Everest Capital USA
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

// Mock fetch globally
global.fetch = jest.fn();

// =============================================================================
// CHAT INTERFACE TESTS
// =============================================================================

describe('ChatInterface', () => {
  const ChatInterface = require('../src/components/ChatInterface').default;
  
  beforeEach(() => {
    fetch.mockClear();
  });
  
  const defaultProps = {
    siteContext: { acreage: 5.0, zoning: 'R-2', typology: 'multifamily' },
    onSiteParamsExtracted: jest.fn(),
    apiBase: '',
  };
  
  test('renders welcome message on mount', () => {
    render(<ChatInterface {...defaultProps} />);
    expect(screen.getByText(/SPD.AI/i)).toBeInTheDocument();
    expect(screen.getByText(/site planning assistant/i)).toBeInTheDocument();
  });
  
  test('displays chat input field', () => {
    render(<ChatInterface {...defaultProps} />);
    expect(screen.getByPlaceholderText(/describe your site/i)).toBeInTheDocument();
  });
  
  test('disables send button when input is empty', () => {
    render(<ChatInterface {...defaultProps} />);
    const sendButton = screen.getByRole('button', { name: /send/i });
    expect(sendButton).toBeDisabled();
  });
  
  test('enables send button when input has text', async () => {
    render(<ChatInterface {...defaultProps} />);
    const input = screen.getByPlaceholderText(/describe your site/i);
    await userEvent.type(input, 'Hello');
    const sendButton = screen.getByRole('button', { name: /send/i });
    expect(sendButton).not.toBeDisabled();
  });
  
  test('sends message on button click', async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ response: 'AI response', metadata: { tier: 'FREE' } }),
    });
    
    render(<ChatInterface {...defaultProps} />);
    const input = screen.getByPlaceholderText(/describe your site/i);
    await userEvent.type(input, 'Test message');
    fireEvent.click(screen.getByRole('button', { name: /send/i }));
    
    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/chat'),
        expect.objectContaining({ method: 'POST' })
      );
    });
  });
  
  test('sends message on Enter key', async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ response: 'Response', metadata: {} }),
    });
    
    render(<ChatInterface {...defaultProps} />);
    const input = screen.getByPlaceholderText(/describe your site/i);
    await userEvent.type(input, 'Test{enter}');
    
    await waitFor(() => {
      expect(fetch).toHaveBeenCalled();
    });
  });
  
  test('displays user message after sending', async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ response: 'AI response', metadata: {} }),
    });
    
    render(<ChatInterface {...defaultProps} />);
    const input = screen.getByPlaceholderText(/describe your site/i);
    await userEvent.type(input, 'My test message');
    fireEvent.click(screen.getByRole('button', { name: /send/i }));
    
    await waitFor(() => {
      expect(screen.getByText('My test message')).toBeInTheDocument();
    });
  });
  
  test('displays AI response after API call', async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ response: 'AI generated response', metadata: {} }),
    });
    
    render(<ChatInterface {...defaultProps} />);
    const input = screen.getByPlaceholderText(/describe your site/i);
    await userEvent.type(input, 'Query');
    fireEvent.click(screen.getByRole('button', { name: /send/i }));
    
    await waitFor(() => {
      expect(screen.getByText('AI generated response')).toBeInTheDocument();
    });
  });
  
  test('handles API error gracefully', async () => {
    fetch.mockRejectedValueOnce(new Error('Network error'));
    
    render(<ChatInterface {...defaultProps} />);
    const input = screen.getByPlaceholderText(/describe your site/i);
    await userEvent.type(input, 'Query');
    fireEvent.click(screen.getByRole('button', { name: /send/i }));
    
    await waitFor(() => {
      expect(screen.getByText(/trouble connecting/i)).toBeInTheDocument();
    });
  });
  
  test('extracts acreage from user message', async () => {
    const onExtract = jest.fn();
    fetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ response: 'OK', metadata: {} }),
    });
    
    render(<ChatInterface {...defaultProps} onSiteParamsExtracted={onExtract} />);
    const input = screen.getByPlaceholderText(/describe your site/i);
    await userEvent.type(input, 'I have 10 acres');
    fireEvent.click(screen.getByRole('button', { name: /send/i }));
    
    await waitFor(() => {
      expect(onExtract).toHaveBeenCalledWith(expect.objectContaining({ acreage: 10 }));
    });
  });
  
  test('clears chat on clear button click', async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ response: 'Response', metadata: {} }),
    });
    
    render(<ChatInterface {...defaultProps} />);
    
    // Send a message
    const input = screen.getByPlaceholderText(/describe your site/i);
    await userEvent.type(input, 'Test');
    fireEvent.click(screen.getByRole('button', { name: /send/i }));
    
    await waitFor(() => {
      expect(screen.getByText('Test')).toBeInTheDocument();
    });
    
    // Clear chat
    fireEvent.click(screen.getByRole('button', { name: /clear/i }));
    
    // User message should be gone, welcome message should remain
    expect(screen.queryByText('Test')).not.toBeInTheDocument();
    expect(screen.getByText(/SPD.AI/i)).toBeInTheDocument();
  });
});


// =============================================================================
// FORM INTERFACE TESTS
// =============================================================================

describe('FormInterface', () => {
  const FormInterface = require('../src/components/FormInterface').default;
  
  const defaultProps = {
    siteAcreage: 5.0,
    setSiteAcreage: jest.fn(),
    zoning: 'R-2',
    setZoning: jest.fn(),
    selectedTypology: 'multifamily',
    setSelectedTypology: jest.fn(),
    params: { parkingRatio: 1.5, stories: 1 },
    setParams: jest.fn(),
    onGenerate: jest.fn(),
    isGenerating: false,
  };
  
  test('renders site details section', () => {
    render(<FormInterface {...defaultProps} />);
    expect(screen.getByText(/site details/i)).toBeInTheDocument();
  });
  
  test('renders acreage input with initial value', () => {
    render(<FormInterface {...defaultProps} />);
    const input = screen.getByDisplayValue('5');
    expect(input).toBeInTheDocument();
  });
  
  test('renders all typology options', () => {
    render(<FormInterface {...defaultProps} />);
    expect(screen.getByText(/multi-family/i)).toBeInTheDocument();
    expect(screen.getByText(/self-storage/i)).toBeInTheDocument();
    expect(screen.getByText(/industrial/i)).toBeInTheDocument();
  });
  
  test('highlights selected typology', () => {
    render(<FormInterface {...defaultProps} />);
    const multifamilyBtn = screen.getByText(/multi-family/i).closest('button');
    expect(multifamilyBtn).toHaveStyle({ borderColor: expect.any(String) });
  });
  
  test('calls setSelectedTypology on typology click', async () => {
    render(<FormInterface {...defaultProps} />);
    const industrialBtn = screen.getByText(/industrial/i).closest('button');
    fireEvent.click(industrialBtn);
    expect(defaultProps.setSelectedTypology).toHaveBeenCalledWith('industrial');
  });
  
  test('calls setSiteAcreage on acreage change', async () => {
    render(<FormInterface {...defaultProps} />);
    const input = screen.getByDisplayValue('5');
    fireEvent.change(input, { target: { value: '10' } });
    expect(defaultProps.setSiteAcreage).toHaveBeenCalled();
  });
  
  test('renders generate button', () => {
    render(<FormInterface {...defaultProps} />);
    expect(screen.getByRole('button', { name: /generate/i })).toBeInTheDocument();
  });
  
  test('disables generate button when generating', () => {
    render(<FormInterface {...defaultProps} isGenerating={true} />);
    const btn = screen.getByRole('button', { name: /generating/i });
    expect(btn).toBeDisabled();
  });
  
  test('calls onGenerate when button clicked', () => {
    render(<FormInterface {...defaultProps} />);
    fireEvent.click(screen.getByRole('button', { name: /generate/i }));
    expect(defaultProps.onGenerate).toHaveBeenCalled();
  });
  
  test('shows typology-specific params for selfStorage', () => {
    render(<FormInterface {...defaultProps} selectedTypology="selfStorage" />);
    expect(screen.getByText(/stories/i)).toBeInTheDocument();
    expect(screen.getByText(/climate/i)).toBeInTheDocument();
  });
  
  test('shows typology-specific params for multifamily', () => {
    render(<FormInterface {...defaultProps} selectedTypology="multifamily" />);
    expect(screen.getByText(/parking/i)).toBeInTheDocument();
  });
});


// =============================================================================
// RESULTS TESTS
// =============================================================================

describe('Results', () => {
  const Results = require('../src/components/Results').default;
  
  const mockResults = {
    typology: 'Multi-Family',
    icon: '🏢',
    color: '#3B82F6',
    acreage: 5.0,
    zoning: 'R-2',
    units: 42,
    grossSF: 75000,
    floors: 3,
    parkingSpaces: 63,
    proForma: {
      landCost: 750000,
      hardCosts: 13125000,
      softCosts: 1968750,
      totalCost: 15843750,
      profit: 2500000,
      margin: 18,
    },
  };
  
  test('renders empty state when no results', () => {
    render(<Results results={null} />);
    expect(screen.getByText(/no analysis yet/i)).toBeInTheDocument();
  });
  
  test('renders typology name and icon', () => {
    render(<Results results={mockResults} />);
    expect(screen.getByText('Multi-Family')).toBeInTheDocument();
    expect(screen.getByText('🏢')).toBeInTheDocument();
  });
  
  test('renders acreage and zoning', () => {
    render(<Results results={mockResults} />);
    expect(screen.getByText(/5 acres/i)).toBeInTheDocument();
    expect(screen.getByText(/R-2/i)).toBeInTheDocument();
  });
  
  test('renders unit count', () => {
    render(<Results results={mockResults} />);
    expect(screen.getByText('42')).toBeInTheDocument();
  });
  
  test('renders pro forma toggle', () => {
    render(<Results results={mockResults} />);
    expect(screen.getByText(/pro forma/i)).toBeInTheDocument();
  });
  
  test('expands pro forma on click', async () => {
    render(<Results results={mockResults} />);
    fireEvent.click(screen.getByText(/pro forma/i));
    await waitFor(() => {
      expect(screen.getByText(/land cost/i)).toBeInTheDocument();
      expect(screen.getByText(/profit/i)).toBeInTheDocument();
    });
  });
  
  test('renders unit mix for self-storage', () => {
    const storageResults = {
      ...mockResults,
      typology: 'Self-Storage',
      unitBreakdown: { '5x5': 50, '5x10': 100, '10x10': 150 },
    };
    render(<Results results={storageResults} />);
    expect(screen.getByText(/unit mix/i)).toBeInTheDocument();
    expect(screen.getByText('5x5')).toBeInTheDocument();
  });
});


// =============================================================================
// MAP VIEW TESTS
// =============================================================================

describe('MapView', () => {
  const MapView = require('../src/components/MapView').default;
  
  const defaultProps = {
    siteAcreage: 5.0,
    zoning: 'R-2',
    results: null,
    location: 'Brevard County, FL',
    viewMode: '2d',
    setViewMode: jest.fn(),
  };
  
  test('renders location label', () => {
    render(<MapView {...defaultProps} />);
    expect(screen.getByText(/brevard county/i)).toBeInTheDocument();
  });
  
  test('renders zoning label', () => {
    render(<MapView {...defaultProps} />);
    expect(screen.getByText('R-2')).toBeInTheDocument();
  });
  
  test('renders acreage in site polygon', () => {
    render(<MapView {...defaultProps} />);
    expect(screen.getByText(/5 AC/i)).toBeInTheDocument();
  });
  
  test('renders square footage calculation', () => {
    render(<MapView {...defaultProps} />);
    // 5 acres * 43560 = 217,800 SF
    expect(screen.getByText(/217,800 SF/i)).toBeInTheDocument();
  });
  
  test('renders view mode toggle', () => {
    render(<MapView {...defaultProps} />);
    expect(screen.getByText('2D')).toBeInTheDocument();
    expect(screen.getByText('3D')).toBeInTheDocument();
  });
  
  test('calls setViewMode on toggle click', () => {
    render(<MapView {...defaultProps} />);
    fireEvent.click(screen.getByText('3D'));
    expect(defaultProps.setViewMode).toHaveBeenCalledWith('3d');
  });
  
  test('renders typology info when results present', () => {
    const results = { icon: '🏢', typology: 'Multi-Family', color: '#3B82F6' };
    render(<MapView {...defaultProps} results={results} />);
    expect(screen.getByText('🏢')).toBeInTheDocument();
    expect(screen.getByText('Multi-Family')).toBeInTheDocument();
  });
  
  test('renders compass indicator', () => {
    render(<MapView {...defaultProps} />);
    expect(screen.getByText('🧭')).toBeInTheDocument();
  });
});


// =============================================================================
// CONSTANTS TESTS
// =============================================================================

describe('Constants', () => {
  const { COLORS, BREVARD_ZONING_DATA, TYPOLOGY_CONFIGS } = require('../src/components/constants');
  
  test('COLORS contains required color keys', () => {
    expect(COLORS.primary).toBeDefined();
    expect(COLORS.accent).toBeDefined();
    expect(COLORS.success).toBeDefined();
    expect(COLORS.danger).toBeDefined();
  });
  
  test('BREVARD_ZONING_DATA contains R-1 through R-3', () => {
    expect(BREVARD_ZONING_DATA['R-1']).toBeDefined();
    expect(BREVARD_ZONING_DATA['R-2']).toBeDefined();
    expect(BREVARD_ZONING_DATA['R-3']).toBeDefined();
  });
  
  test('TYPOLOGY_CONFIGS contains all 8 typologies', () => {
    const typologies = Object.keys(TYPOLOGY_CONFIGS);
    expect(typologies).toContain('multifamily');
    expect(typologies).toContain('selfStorage');
    expect(typologies).toContain('industrial');
    expect(typologies).toContain('singleFamily');
    expect(typologies).toContain('seniorLiving');
    expect(typologies).toContain('medical');
    expect(typologies).toContain('retail');
    expect(typologies).toContain('hotel');
  });
  
  test('each typology has name, icon, and color', () => {
    Object.values(TYPOLOGY_CONFIGS).forEach(config => {
      expect(config.name).toBeDefined();
      expect(config.icon).toBeDefined();
      expect(config.color).toBeDefined();
    });
  });
});
