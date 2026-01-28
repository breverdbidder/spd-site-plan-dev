import React, { useState } from 'react';
import { COLORS } from './constants';

/**
 * Results Component
 * Displays feasibility analysis results and pro forma
 * 
 * Refactored from App.jsx as part of P1 codebase improvements
 * @author BidDeed.AI / Everest Capital USA
 */

// Metric card component
const MetricCard = ({ label, value, icon, color }) => {
  const cardStyle = {
    padding: '12px',
    backgroundColor: COLORS.surface,
    borderRadius: '10px',
    display: 'flex',
    flexDirection: 'column',
    gap: '4px',
  };

  const labelStyle = {
    fontSize: '11px',
    color: COLORS.textSecondary,
    display: 'flex',
    alignItems: 'center',
    gap: '4px',
  };

  const valueStyle = {
    fontSize: '18px',
    fontWeight: '600',
    color: color || COLORS.textPrimary,
  };

  return (
    <div style={cardStyle}>
      <span style={labelStyle}>
        {icon && <span>{icon}</span>}
        {label}
      </span>
      <span style={valueStyle}>{value}</span>
    </div>
  );
};

// Pro forma section component
const ProFormaSection = ({ proForma }) => {
  const styles = {
    container: {
      padding: '16px',
      backgroundColor: COLORS.surface,
      borderRadius: '12px',
      marginTop: '12px',
    },
    grid: {
      display: 'grid',
      gridTemplateColumns: '1fr 1fr',
      gap: '12px',
    },
    item: {
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      padding: '8px 0',
    },
    label: {
      fontSize: '13px',
      color: COLORS.textSecondary,
    },
    value: {
      fontSize: '14px',
      fontWeight: '600',
      color: COLORS.textPrimary,
    },
    total: {
      gridColumn: 'span 2',
      borderTop: `1px solid ${COLORS.border}`,
      paddingTop: '12px',
      marginTop: '4px',
    },
    profitBanner: {
      marginTop: '16px',
      padding: '16px',
      backgroundColor: COLORS.success,
      borderRadius: '10px',
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      color: 'white',
    },
    profitLabel: {
      fontSize: '13px',
      opacity: 0.9,
    },
    profitValue: {
      fontSize: '24px',
      fontWeight: '700',
    },
    profitMargin: {
      fontSize: '14px',
      fontWeight: '600',
      padding: '4px 8px',
      backgroundColor: 'rgba(255,255,255,0.2)',
      borderRadius: '6px',
    },
  };

  const formatMoney = (amount) => `$${(amount / 1000000).toFixed(2)}M`;

  return (
    <div style={styles.container}>
      <div style={styles.grid}>
        <div style={styles.item}>
          <span style={styles.label}>Land Cost</span>
          <span style={styles.value}>{formatMoney(proForma.landCost)}</span>
        </div>
        <div style={styles.item}>
          <span style={styles.label}>Hard Costs</span>
          <span style={styles.value}>{formatMoney(proForma.hardCosts)}</span>
        </div>
        <div style={styles.item}>
          <span style={styles.label}>Soft Costs</span>
          <span style={styles.value}>{formatMoney(proForma.softCosts || 0)}</span>
        </div>
        <div style={styles.item}>
          <span style={styles.label}>Contingency</span>
          <span style={styles.value}>{formatMoney(proForma.contingency || 0)}</span>
        </div>
        <div style={{ ...styles.item, ...styles.total }}>
          <span style={{ ...styles.label, fontWeight: '600', color: COLORS.textPrimary }}>
            Total Development Cost
          </span>
          <span style={{ ...styles.value, fontSize: '16px' }}>
            {formatMoney(proForma.totalCost)}
          </span>
        </div>
      </div>

      <div style={styles.profitBanner}>
        <div>
          <div style={styles.profitLabel}>Estimated Profit</div>
          <div style={styles.profitValue}>{formatMoney(proForma.profit)}</div>
        </div>
        <div style={styles.profitMargin}>{proForma.margin}% margin</div>
      </div>
    </div>
  );
};

// Unit mix display for storage
const UnitMixDisplay = ({ unitBreakdown }) => {
  const styles = {
    container: {
      marginTop: '16px',
    },
    title: {
      fontSize: '13px',
      fontWeight: '600',
      color: COLORS.textPrimary,
      marginBottom: '12px',
      display: 'flex',
      alignItems: 'center',
      gap: '8px',
    },
    grid: {
      display: 'grid',
      gridTemplateColumns: 'repeat(3, 1fr)',
      gap: '8px',
    },
    item: {
      padding: '10px',
      backgroundColor: COLORS.surface,
      borderRadius: '8px',
      textAlign: 'center',
    },
    size: {
      fontSize: '12px',
      color: COLORS.textSecondary,
    },
    count: {
      fontSize: '16px',
      fontWeight: '600',
      color: COLORS.textPrimary,
    },
  };

  return (
    <div style={styles.container}>
      <h4 style={styles.title}>
        <span>📦</span>
        Unit Mix
      </h4>
      <div style={styles.grid}>
        {Object.entries(unitBreakdown).map(([size, count]) => (
          <div key={size} style={styles.item}>
            <div style={styles.size}>{size}</div>
            <div style={styles.count}>{count}</div>
          </div>
        ))}
      </div>
    </div>
  );
};

// Empty state component
const EmptyState = () => (
  <div style={{
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    height: '100%',
    padding: '40px 20px',
    textAlign: 'center',
  }}>
    <div style={{ fontSize: '48px', marginBottom: '16px' }}>📊</div>
    <h3 style={{
      fontSize: '16px',
      fontWeight: '600',
      color: COLORS.textPrimary,
      marginBottom: '8px',
    }}>
      No Analysis Yet
    </h3>
    <p style={{
      fontSize: '14px',
      color: COLORS.textSecondary,
      maxWidth: '240px',
    }}>
      Use Chat or Form mode to analyze a site and see feasibility results here.
    </p>
  </div>
);

/**
 * Main Results component
 */
export default function Results({ results }) {
  const [showProForma, setShowProForma] = useState(false);

  // Styles
  const styles = {
    container: {
      height: '100%',
      overflowY: 'auto',
      backgroundColor: 'white',
    },
    header: {
      padding: '16px',
      borderBottom: `1px solid ${COLORS.border}`,
      display: 'flex',
      alignItems: 'center',
      gap: '12px',
    },
    icon: {
      fontSize: '32px',
    },
    titleArea: {
      flex: 1,
    },
    title: {
      fontSize: '18px',
      fontWeight: '600',
      color: COLORS.textPrimary,
      marginBottom: '2px',
    },
    subtitle: {
      fontSize: '13px',
      color: COLORS.textSecondary,
    },
    content: {
      padding: '16px',
    },
    metricsGrid: {
      display: 'grid',
      gridTemplateColumns: 'repeat(2, 1fr)',
      gap: '12px',
      marginBottom: '16px',
    },
    proFormaToggle: {
      width: '100%',
      padding: '12px 16px',
      backgroundColor: COLORS.surface,
      border: 'none',
      borderRadius: '10px',
      cursor: 'pointer',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      fontSize: '14px',
      fontWeight: '500',
      color: COLORS.textPrimary,
    },
    chevron: {
      transition: 'transform 0.2s',
    },
  };

  if (!results) {
    return (
      <div style={styles.container}>
        <EmptyState />
      </div>
    );
  }

  return (
    <div style={styles.container}>
      {/* Header */}
      <div style={styles.header}>
        <span style={{ ...styles.icon, color: results.color }}>{results.icon}</span>
        <div style={styles.titleArea}>
          <h3 style={styles.title}>{results.typology}</h3>
          <span style={styles.subtitle}>
            {results.acreage} acres • {results.zoning}
          </span>
        </div>
      </div>

      {/* Content */}
      <div style={styles.content}>
        {/* Metrics Grid */}
        <div style={styles.metricsGrid}>
          {results.units && (
            <MetricCard 
              label="Units" 
              value={results.units} 
              icon="🏢" 
              color={results.color} 
            />
          )}
          {results.netRentableSF && (
            <MetricCard 
              label="Net SF" 
              value={results.netRentableSF.toLocaleString()} 
              icon="📦" 
              color={results.color} 
            />
          )}
          {results.warehouseSF && (
            <MetricCard 
              label="Warehouse" 
              value={results.warehouseSF.toLocaleString()} 
              icon="🏭" 
              color={results.color} 
            />
          )}
          {results.totalLots && (
            <MetricCard 
              label="Lots" 
              value={results.totalLots} 
              icon="🏠" 
              color={results.color} 
            />
          )}
          {results.beds && (
            <MetricCard 
              label="Beds" 
              value={results.beds} 
              icon="🏥" 
              color={results.color} 
            />
          )}
          {results.rooms && (
            <MetricCard 
              label="Rooms" 
              value={results.rooms} 
              icon="🏨" 
              color={results.color} 
            />
          )}
          {results.grossSF && (
            <MetricCard 
              label="Gross SF" 
              value={results.grossSF.toLocaleString()} 
              icon="📐" 
            />
          )}
          {results.floors && (
            <MetricCard 
              label="Stories" 
              value={results.floors} 
              icon="🏗️" 
            />
          )}
          {results.parkingSpaces && (
            <MetricCard 
              label="Parking" 
              value={results.parkingSpaces} 
              icon="🚗" 
            />
          )}
        </div>

        {/* Unit Mix (for self-storage) */}
        {results.unitBreakdown && (
          <UnitMixDisplay unitBreakdown={results.unitBreakdown} />
        )}

        {/* Pro Forma Toggle */}
        {results.proForma && (
          <>
            <button 
              style={styles.proFormaToggle}
              onClick={() => setShowProForma(!showProForma)}
            >
              <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span>💰</span>
                Pro Forma Analysis
              </span>
              <span style={{
                ...styles.chevron,
                transform: showProForma ? 'rotate(180deg)' : 'rotate(0deg)',
              }}>
                ▼
              </span>
            </button>

            {showProForma && (
              <ProFormaSection proForma={results.proForma} />
            )}
          </>
        )}
      </div>
    </div>
  );
}
