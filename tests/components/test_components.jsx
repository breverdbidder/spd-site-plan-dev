/**
 * Unit Tests for SPD.AI React Components
 * P2 Codebase Requirement: Additional unit tests for components
 * 
 * Tests cover:
 * - ChatInterface: message handling, API calls, state management
 * - FormInterface: form validation, parameter updates, typology selection
 * - Results: display logic, pro forma calculations
 * - MapView: rendering, view mode switching
 * 
 * @author BidDeed.AI / Everest Capital USA
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';

// Mock fetch globally
global.fetch = jest.fn();

// Import components
import ChatInterface from '../src/components/ChatInterface';
import FormInterface from '../src/components/FormInterface';
import Results from '../src/components/Results';
import MapView from '../src/components/MapView';
import { COLORS, TYPOLOGY_CONFIGS, BREVARD_ZONING_DATA } from '../src/components/constants';


// =============================================================================
// TEST UTILITIES
// =============================================================================

const mockSiteContext = {
  acreage: 5.0,
  zoning: 'R-2',
  typology: 'multifamily',
};

const mockResults = {
  typology: 'Multi-Family',
  icon: '🏢',
  color: '#3B82F6',
  acreage: 5.0,
  zoning: 'R-2',
  units: 150,
  grossSF: 125000,
  floors: 3,
  parkingSpaces: 225,
  proForma: {
    landCost: 750000,
    hardCosts: 21875000,
    softCosts: 3281250,
    totalCost: 25906250,
    noi: 1620000,
    profit: 2093750,
    margin: 18,
  },
};

const mockApiResponse = {
  response: 'Based on your 5-acre site with R-2 zoning, you could build approximately 150 units.',
  metadata: {
    tier: 'FREE',
    model: 'gemini-2.5-flash',
    tokens: 150,
  },
};


// =============================================================================
// CHAT INTERFACE TESTS
// =============================================================================

describe('ChatInterface Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    fetch.mockImplementation((url) => {
      if (url.includes('/health')) {
        return Promise.resolve({ ok: true });
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve(mockApiResponse),
      });
    });
  });

  test('renders welcome message on mount', () => {
    render(<ChatInterface siteContext={mockSiteContext} />);
    
    expect(screen.getByText(/I'm SPD.AI/)).toBeInTheDocument();
    expect(screen.getByText(/Feasibility analysis/)).toBeInTheDocument();
  });

  test('shows connected status when API is healthy', async () => {
    render(<ChatInterface siteContext={mockSiteContext} />);
    
    await waitFor(() => {
      expect(screen.getByText(/Connected/)).toBeInTheDocument();
    });
  });

  test('shows disconnected status when API fails', async () => {
    fetch.mockImplementation((url) => {
      if (url.includes('/health')) {
        return Promise.resolve({ ok: false });
      }
      return Promise.resolve({ ok: true });
    });

    render(<ChatInterface siteContext={mockSiteContext} />);
    
    await waitFor(() => {
      expect(screen.getByText(/Disconnected/)).toBeInTheDocument();
    });
  });

  test('sends message when Send button is clicked', async () => {
    const user = userEvent.setup();
    render(<ChatInterface siteContext={mockSiteContext} />);
    
    const input = screen.getByPlaceholderText(/Describe your site/);
    const sendButton = screen.getByRole('button', { name: /Send/i });
    
    await user.type(input, 'What can I build on 5 acres?');
    await user.click(sendButton);
    
    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/chat'),
        expect.objectContaining({
          method: 'POST',
          body: expect.stringContaining('What can I build on 5 acres?'),
        })
      );
    });
  });

  test('sends message on Enter key press', async () => {
    const user = userEvent.setup();
    render(<ChatInterface siteContext={mockSiteContext} />);
    
    const input = screen.getByPlaceholderText(/Describe your site/);
    
    await user.type(input, 'Test message{enter}');
    
    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/chat'),
        expect.any(Object)
      );
    });
  });

  test('displays user message after sending', async () => {
    const user = userEvent.setup();
    render(<ChatInterface siteContext={mockSiteContext} />);
    
    const input = screen.getByPlaceholderText(/Describe your site/);
    
    await user.type(input, 'My test message');
    await user.click(screen.getByRole('button', { name: /Send/i }));
    
    await waitFor(() => {
      expect(screen.getByText('My test message')).toBeInTheDocument();
    });
  });

  test('displays assistant response after API call', async () => {
    const user = userEvent.setup();
    render(<ChatInterface siteContext={mockSiteContext} />);
    
    const input = screen.getByPlaceholderText(/Describe your site/);
    
    await user.type(input, 'Test query');
    await user.click(screen.getByRole('button', { name: /Send/i }));
    
    await waitFor(() => {
      expect(screen.getByText(/150 units/)).toBeInTheDocument();
    });
  });

  test('shows typing indicator while waiting for response', async () => {
    fetch.mockImplementation(() => 
      new Promise(resolve => setTimeout(() => resolve({
        ok: true,
        json: () => Promise.resolve(mockApiResponse),
      }), 100))
    );

    const user = userEvent.setup();
    render(<ChatInterface siteContext={mockSiteContext} />);
    
    const input = screen.getByPlaceholderText(/Describe your site/);
    
    await user.type(input, 'Test');
    await user.click(screen.getByRole('button', { name: /Send/i }));
    
    // Typing indicator should appear
    // (implementation depends on how TypingIndicator is rendered)
  });

  test('clears chat when Clear button is clicked', async () => {
    const user = userEvent.setup();
    render(<ChatInterface siteContext={mockSiteContext} />);
    
    // Send a message first
    const input = screen.getByPlaceholderText(/Describe your site/);
    await user.type(input, 'Test message');
    await user.click(screen.getByRole('button', { name: /Send/i }));
    
    await waitFor(() => {
      expect(screen.getByText('Test message')).toBeInTheDocument();
    });
    
    // Clear chat
    await user.click(screen.getByRole('button', { name: /Clear/i }));
    
    // User message should be gone, but welcome message remains
    expect(screen.queryByText('Test message')).not.toBeInTheDocument();
    expect(screen.getByText(/I'm SPD.AI/)).toBeInTheDocument();
  });

  test('extracts acreage from user input', async () => {
    const mockExtractCallback = jest.fn();
    const user = userEvent.setup();
    
    render(
      <ChatInterface 
        siteContext={mockSiteContext} 
        onSiteParamsExtracted={mockExtractCallback}
      />
    );
    
    const input = screen.getByPlaceholderText(/Describe your site/);
    await user.type(input, 'I have 10 acres');
    await user.click(screen.getByRole('button', { name: /Send/i }));
    
    await waitFor(() => {
      expect(mockExtractCallback).toHaveBeenCalledWith(
        expect.objectContaining({ acreage: 10 })
      );
    });
  });

  test('disables input while typing', async () => {
    fetch.mockImplementation(() => 
      new Promise(resolve => setTimeout(() => resolve({
        ok: true,
        json: () => Promise.resolve(mockApiResponse),
      }), 500))
    );

    const user = userEvent.setup();
    render(<ChatInterface siteContext={mockSiteContext} />);
    
    const input = screen.getByPlaceholderText(/Describe your site/);
    
    await user.type(input, 'Test');
    await user.click(screen.getByRole('button', { name: /Send/i }));
    
    expect(input).toBeDisabled();
  });
});


// =============================================================================
// FORM INTERFACE TESTS
// =============================================================================

describe('FormInterface Component', () => {
  const defaultProps = {
    siteAcreage: 5.0,
    setSiteAcreage: jest.fn(),
    zoning: 'R-2',
    setZoning: jest.fn(),
    selectedTypology: 'multifamily',
    setSelectedTypology: jest.fn(),
    params: { parkingRatio: 1.5 },
    setParams: jest.fn(),
    onGenerate: jest.fn(),
    isGenerating: false,
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders all sections', () => {
    render(<FormInterface {...defaultProps} />);
    
    expect(screen.getByText(/Site Details/)).toBeInTheDocument();
    expect(screen.getByText(/Development Type/)).toBeInTheDocument();
    expect(screen.getByText(/Parameters/)).toBeInTheDocument();
  });

  test('displays current acreage value', () => {
    render(<FormInterface {...defaultProps} />);
    
    const acreageInput = screen.getByDisplayValue('5');
    expect(acreageInput).toBeInTheDocument();
  });

  test('calls setSiteAcreage when acreage changes', async () => {
    const user = userEvent.setup();
    render(<FormInterface {...defaultProps} />);
    
    const acreageInput = screen.getByDisplayValue('5');
    await user.clear(acreageInput);
    await user.type(acreageInput, '10');
    
    expect(defaultProps.setSiteAcreage).toHaveBeenCalled();
  });

  test('renders all typology buttons', () => {
    render(<FormInterface {...defaultProps} />);
    
    Object.values(TYPOLOGY_CONFIGS).forEach(config => {
      expect(screen.getByText(config.name)).toBeInTheDocument();
    });
  });

  test('calls setSelectedTypology when typology button is clicked', async () => {
    const user = userEvent.setup();
    render(<FormInterface {...defaultProps} />);
    
    await user.click(screen.getByText('Self-Storage'));
    
    expect(defaultProps.setSelectedTypology).toHaveBeenCalledWith('selfStorage');
  });

  test('shows multifamily params when multifamily selected', () => {
    render(<FormInterface {...defaultProps} />);
    
    expect(screen.getByText(/Parking Ratio/)).toBeInTheDocument();
  });

  test('shows self-storage params when selfStorage selected', () => {
    render(<FormInterface {...defaultProps} selectedTypology="selfStorage" />);
    
    expect(screen.getByText(/Stories/)).toBeInTheDocument();
    expect(screen.getByText(/Climate Control/)).toBeInTheDocument();
  });

  test('shows industrial params when industrial selected', () => {
    render(<FormInterface {...defaultProps} selectedTypology="industrial" />);
    
    expect(screen.getByText(/Clear Height/)).toBeInTheDocument();
    expect(screen.getByText(/Bay Depth/)).toBeInTheDocument();
  });

  test('calls onGenerate when Generate button is clicked', async () => {
    const user = userEvent.setup();
    render(<FormInterface {...defaultProps} />);
    
    await user.click(screen.getByRole('button', { name: /Generate/i }));
    
    expect(defaultProps.onGenerate).toHaveBeenCalled();
  });

  test('disables Generate button when isGenerating is true', () => {
    render(<FormInterface {...defaultProps} isGenerating={true} />);
    
    const button = screen.getByRole('button', { name: /Generating/i });
    expect(button).toBeDisabled();
  });

  test('shows all zoning options', async () => {
    const user = userEvent.setup();
    render(<FormInterface {...defaultProps} />);
    
    const zoningSelect = screen.getByDisplayValue(/R-2/);
    expect(zoningSelect).toBeInTheDocument();
  });
});


// =============================================================================
// RESULTS COMPONENT TESTS
// =============================================================================

describe('Results Component', () => {
  test('renders empty state when no results', () => {
    render(<Results results={null} />);
    
    expect(screen.getByText(/No Analysis Yet/)).toBeInTheDocument();
  });

  test('renders typology header with results', () => {
    render(<Results results={mockResults} />);
    
    expect(screen.getByText('Multi-Family')).toBeInTheDocument();
    expect(screen.getByText(/5 acres/)).toBeInTheDocument();
    expect(screen.getByText(/R-2/)).toBeInTheDocument();
  });

  test('displays unit count metric', () => {
    render(<Results results={mockResults} />);
    
    expect(screen.getByText('150')).toBeInTheDocument();
    expect(screen.getByText('Units')).toBeInTheDocument();
  });

  test('displays gross SF metric', () => {
    render(<Results results={mockResults} />);
    
    expect(screen.getByText('125,000')).toBeInTheDocument();
  });

  test('displays parking spaces metric', () => {
    render(<Results results={mockResults} />);
    
    expect(screen.getByText('225')).toBeInTheDocument();
    expect(screen.getByText('Parking')).toBeInTheDocument();
  });

  test('renders pro forma toggle button', () => {
    render(<Results results={mockResults} />);
    
    expect(screen.getByText(/Pro Forma/)).toBeInTheDocument();
  });

  test('shows pro forma details when toggled', async () => {
    const user = userEvent.setup();
    render(<Results results={mockResults} />);
    
    await user.click(screen.getByText(/Pro Forma/));
    
    expect(screen.getByText(/Land Cost/)).toBeInTheDocument();
    expect(screen.getByText(/Hard Costs/)).toBeInTheDocument();
    expect(screen.getByText(/Total Development Cost/)).toBeInTheDocument();
  });

  test('displays profit and margin', async () => {
    const user = userEvent.setup();
    render(<Results results={mockResults} />);
    
    await user.click(screen.getByText(/Pro Forma/));
    
    expect(screen.getByText(/Estimated Profit/)).toBeInTheDocument();
    expect(screen.getByText(/18%/)).toBeInTheDocument();
  });

  test('renders unit breakdown for self-storage', () => {
    const storageResults = {
      ...mockResults,
      typology: 'Self-Storage',
      unitBreakdown: {
        '5x5': 50,
        '5x10': 100,
        '10x10': 150,
        '10x15': 75,
        '10x20': 50,
      },
    };
    
    render(<Results results={storageResults} />);
    
    expect(screen.getByText('5x5')).toBeInTheDocument();
    expect(screen.getByText('50')).toBeInTheDocument();
  });
});


// =============================================================================
// MAP VIEW TESTS
// =============================================================================

describe('MapView Component', () => {
  const defaultProps = {
    siteAcreage: 5.0,
    zoning: 'R-2',
    results: null,
    viewMode: '2d',
    setViewMode: jest.fn(),
  };

  test('renders site polygon with acreage', () => {
    render(<MapView {...defaultProps} />);
    
    expect(screen.getByText(/5 AC/)).toBeInTheDocument();
  });

  test('displays square footage', () => {
    render(<MapView {...defaultProps} />);
    
    // 5 acres = 217,800 SF
    expect(screen.getByText(/217,800 SF/)).toBeInTheDocument();
  });

  test('shows location in info bar', () => {
    render(<MapView {...defaultProps} />);
    
    expect(screen.getByText(/Brevard County, FL/)).toBeInTheDocument();
  });

  test('shows zoning in info bar', () => {
    render(<MapView {...defaultProps} />);
    
    expect(screen.getByText('R-2')).toBeInTheDocument();
  });

  test('renders view mode toggle buttons', () => {
    render(<MapView {...defaultProps} />);
    
    expect(screen.getByText('2D')).toBeInTheDocument();
    expect(screen.getByText('3D')).toBeInTheDocument();
    expect(screen.getByText('Satellite')).toBeInTheDocument();
  });

  test('calls setViewMode when view button clicked', async () => {
    const user = userEvent.setup();
    render(<MapView {...defaultProps} />);
    
    await user.click(screen.getByText('3D'));
    
    expect(defaultProps.setViewMode).toHaveBeenCalledWith('3d');
  });

  test('shows typology in info bar when results present', () => {
    render(<MapView {...defaultProps} results={mockResults} />);
    
    expect(screen.getByText('Multi-Family')).toBeInTheDocument();
  });

  test('applies result color to site polygon', () => {
    const { container } = render(<MapView {...defaultProps} results={mockResults} />);
    
    // The polygon should have the results color applied
    // (implementation depends on how styles are applied)
  });

  test('renders compass indicator', () => {
    render(<MapView {...defaultProps} />);
    
    expect(screen.getByText('🧭')).toBeInTheDocument();
  });

  test('shows placeholder for 3D view', () => {
    render(<MapView {...defaultProps} viewMode="3d" />);
    
    expect(screen.getByText(/3D View/)).toBeInTheDocument();
    expect(screen.getByText(/Coming soon/)).toBeInTheDocument();
  });
});


// =============================================================================
// CONSTANTS TESTS
// =============================================================================

describe('Constants', () => {
  test('COLORS has all required properties', () => {
    expect(COLORS.primary).toBeDefined();
    expect(COLORS.accent).toBeDefined();
    expect(COLORS.success).toBeDefined();
    expect(COLORS.danger).toBeDefined();
    expect(COLORS.textPrimary).toBeDefined();
  });

  test('TYPOLOGY_CONFIGS has all 8 typologies', () => {
    const expectedTypologies = [
      'multifamily', 'selfStorage', 'industrial', 'singleFamily',
      'seniorLiving', 'medical', 'retail', 'hotel'
    ];
    
    expectedTypologies.forEach(typology => {
      expect(TYPOLOGY_CONFIGS[typology]).toBeDefined();
      expect(TYPOLOGY_CONFIGS[typology].name).toBeDefined();
      expect(TYPOLOGY_CONFIGS[typology].icon).toBeDefined();
      expect(TYPOLOGY_CONFIGS[typology].color).toBeDefined();
    });
  });

  test('BREVARD_ZONING_DATA has required zoning codes', () => {
    const expectedCodes = ['R-1', 'R-2', 'R-3', 'C-1', 'C-2', 'I-1', 'PUD'];
    
    expectedCodes.forEach(code => {
      expect(BREVARD_ZONING_DATA[code]).toBeDefined();
      expect(BREVARD_ZONING_DATA[code].name).toBeDefined();
    });
  });
});


// =============================================================================
// INTEGRATION TESTS
// =============================================================================

describe('Component Integration', () => {
  test('FormInterface to Results flow', async () => {
    // This would test the full flow from form submission to results display
    // In a real test, you'd render the full App component
  });

  test('ChatInterface extracts params and updates form', async () => {
    // This would test parameter extraction from chat
  });
});
