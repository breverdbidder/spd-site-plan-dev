import React from 'react';
import { COLORS } from './constants';

/**
 * MapView Component
 * Displays site visualization with parcel overlay
 * 
 * Refactored from App.jsx as part of P1 codebase improvements
 * @author BidDeed.AI / Everest Capital USA
 */

// Grid pattern SVG background
const GridPattern = () => (
  <svg 
    style={{
      position: 'absolute',
      top: 0,
      left: 0,
      width: '100%',
      height: '100%',
    }} 
    xmlns="http://www.w3.org/2000/svg"
  >
    <defs>
      <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
        <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#E2E8F0" strokeWidth="1"/>
      </pattern>
    </defs>
    <rect width="100%" height="100%" fill="url(#grid)" />
  </svg>
);

// Site polygon visualization
const SitePolygon = ({ acreage, color, icon }) => {
  const styles = {
    polygon: {
      width: '200px',
      height: '150px',
      border: `3px dashed ${color || COLORS.accent}`,
      borderRadius: '12px',
      backgroundColor: `${color || COLORS.accent}20`,
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      transition: 'all 0.3s ease',
    },
    label: {
      color: color || COLORS.accent,
      textAlign: 'center',
      fontWeight: '600',
    },
    acreage: {
      fontSize: '24px',
      display: 'flex',
      alignItems: 'center',
      gap: '8px',
    },
    sqft: {
      fontSize: '12px',
      opacity: 0.8,
    },
  };

  const squareFeet = Math.round(acreage * 43560);

  return (
    <div style={styles.polygon}>
      <div style={styles.label}>
        <div style={styles.acreage}>
          {icon && <span>{icon}</span>}
          {acreage} AC
        </div>
        <small style={styles.sqft}>
          {squareFeet.toLocaleString()} SF
        </small>
      </div>
    </div>
  );
};

// Map info bar
const MapInfoBar = ({ location, zoning, results }) => {
  const styles = {
    bar: {
      position: 'absolute',
      bottom: '16px',
      left: '16px',
      right: '16px',
      padding: '12px 16px',
      backgroundColor: 'rgba(255,255,255,0.95)',
      borderRadius: '10px',
      boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
      display: 'flex',
      alignItems: 'center',
      gap: '16px',
      fontSize: '13px',
      color: COLORS.textSecondary,
    },
    item: {
      display: 'flex',
      alignItems: 'center',
      gap: '6px',
    },
    typology: {
      color: results?.color || COLORS.accent,
      fontWeight: '500',
    },
  };

  return (
    <div style={styles.bar}>
      <span style={styles.item}>
        <span>📍</span>
        {location}
      </span>
      <span style={styles.item}>
        <span>🏷️</span>
        {zoning}
      </span>
      {results && (
        <span style={{ ...styles.item, ...styles.typology }}>
          <span>{results.icon}</span>
          {results.typology}
        </span>
      )}
    </div>
  );
};

// View mode toggle
const ViewModeToggle = ({ viewMode, setViewMode }) => {
  const styles = {
    container: {
      position: 'absolute',
      top: '16px',
      right: '16px',
      display: 'flex',
      backgroundColor: 'white',
      borderRadius: '8px',
      padding: '4px',
      boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
    },
    button: {
      padding: '8px 16px',
      border: 'none',
      borderRadius: '6px',
      cursor: 'pointer',
      fontSize: '12px',
      fontWeight: '500',
      transition: 'all 0.2s',
    },
    active: {
      backgroundColor: COLORS.accent,
      color: 'white',
    },
    inactive: {
      backgroundColor: 'transparent',
      color: COLORS.textSecondary,
    },
  };

  return (
    <div style={styles.container}>
      <button
        style={{
          ...styles.button,
          ...(viewMode === '2d' ? styles.active : styles.inactive),
        }}
        onClick={() => setViewMode('2d')}
      >
        2D
      </button>
      <button
        style={{
          ...styles.button,
          ...(viewMode === '3d' ? styles.active : styles.inactive),
        }}
        onClick={() => setViewMode('3d')}
      >
        3D
      </button>
      <button
        style={{
          ...styles.button,
          ...(viewMode === 'satellite' ? styles.active : styles.inactive),
        }}
        onClick={() => setViewMode('satellite')}
      >
        Satellite
      </button>
    </div>
  );
};

// Compass indicator
const Compass = () => (
  <div style={{
    position: 'absolute',
    top: '16px',
    left: '16px',
    width: '40px',
    height: '40px',
    backgroundColor: 'white',
    borderRadius: '50%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
    fontSize: '18px',
  }}>
    🧭
  </div>
);

/**
 * Main MapView component
 */
export default function MapView({ 
  siteAcreage, 
  zoning, 
  results,
  location = 'Brevard County, FL',
  viewMode = '2d',
  setViewMode,
}) {
  const styles = {
    container: {
      position: 'relative',
      width: '100%',
      height: '100%',
      backgroundColor: '#F8FAFC',
      overflow: 'hidden',
    },
    centerArea: {
      position: 'absolute',
      top: '50%',
      left: '50%',
      transform: 'translate(-50%, -50%)',
    },
    placeholder3d: {
      position: 'absolute',
      top: '50%',
      left: '50%',
      transform: 'translate(-50%, -50%)',
      textAlign: 'center',
      color: COLORS.textSecondary,
    },
  };

  return (
    <div style={styles.container}>
      {/* Grid Pattern Background */}
      <GridPattern />

      {/* View Mode Toggle */}
      {setViewMode && (
        <ViewModeToggle viewMode={viewMode} setViewMode={setViewMode} />
      )}

      {/* Compass */}
      <Compass />

      {/* Center Content */}
      {viewMode === '2d' ? (
        <div style={styles.centerArea}>
          <SitePolygon
            acreage={siteAcreage}
            color={results?.color}
            icon={results?.icon}
          />
        </div>
      ) : (
        <div style={styles.placeholder3d}>
          <div style={{ fontSize: '48px', marginBottom: '12px' }}>🏗️</div>
          <p>{viewMode === '3d' ? '3D View' : 'Satellite View'}</p>
          <p style={{ fontSize: '12px' }}>Coming soon</p>
        </div>
      )}

      {/* Info Bar */}
      <MapInfoBar 
        location={location} 
        zoning={zoning} 
        results={results} 
      />
    </div>
  );
}
