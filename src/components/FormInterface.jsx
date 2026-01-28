import React from 'react';
import { COLORS, BREVARD_ZONING_DATA, TYPOLOGY_CONFIGS } from './constants';

/**
 * FormInterface Component
 * Handles form-based site parameter input and configuration
 * 
 * Refactored from App.jsx as part of P1 codebase improvements
 * @author BidDeed.AI / Everest Capital USA
 */

// Parameter input field component
const ParamField = ({ label, type = 'number', value, onChange, options, step, min, max }) => {
  const fieldStyle = {
    display: 'flex',
    flexDirection: 'column',
    gap: '6px',
  };

  const labelStyle = {
    fontSize: '12px',
    fontWeight: '500',
    color: COLORS.textSecondary,
  };

  const inputStyle = {
    padding: '8px 12px',
    border: `1px solid ${COLORS.border}`,
    borderRadius: '8px',
    fontSize: '14px',
    outline: 'none',
    transition: 'border-color 0.2s',
  };

  const selectStyle = {
    ...inputStyle,
    backgroundColor: 'white',
  };

  if (options) {
    return (
      <div style={fieldStyle}>
        <label style={labelStyle}>{label}</label>
        <select style={selectStyle} value={value} onChange={(e) => onChange(e.target.value)}>
          {options.map(opt => (
            <option key={opt.value} value={opt.value}>{opt.label}</option>
          ))}
        </select>
      </div>
    );
  }

  return (
    <div style={fieldStyle}>
      <label style={labelStyle}>{label}</label>
      <input
        type={type}
        style={inputStyle}
        value={value}
        onChange={(e) => onChange(type === 'number' ? parseFloat(e.target.value) : e.target.value)}
        step={step}
        min={min}
        max={max}
      />
    </div>
  );
};

// Typology selector button
const TypologyButton = ({ config, typologyKey, isSelected, onClick }) => {
  const baseStyle = {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    padding: '12px 8px',
    border: `2px solid ${COLORS.border}`,
    borderRadius: '12px',
    cursor: 'pointer',
    transition: 'all 0.2s',
    backgroundColor: 'white',
  };

  const activeStyle = isSelected ? {
    borderColor: config.color,
    backgroundColor: `${config.color}15`,
  } : {};

  const iconStyle = {
    fontSize: '24px',
    marginBottom: '4px',
  };

  const nameStyle = {
    fontSize: '11px',
    fontWeight: '500',
    color: isSelected ? config.color : COLORS.textSecondary,
  };

  return (
    <button 
      style={{ ...baseStyle, ...activeStyle }}
      onClick={() => onClick(typologyKey)}
    >
      <span style={iconStyle}>{config.icon}</span>
      <span style={nameStyle}>{config.name}</span>
    </button>
  );
};

/**
 * Main FormInterface component
 */
export default function FormInterface({
  siteAcreage,
  setSiteAcreage,
  zoning,
  setZoning,
  selectedTypology,
  setSelectedTypology,
  params,
  setParams,
  onGenerate,
  isGenerating,
}) {
  // Styles
  const styles = {
    container: {
      display: 'flex',
      flexDirection: 'column',
      height: '100%',
      backgroundColor: 'white',
      overflowY: 'auto',
    },
    section: {
      padding: '16px',
      borderBottom: `1px solid ${COLORS.border}`,
    },
    sectionTitle: {
      fontSize: '13px',
      fontWeight: '600',
      color: COLORS.textPrimary,
      marginBottom: '12px',
      display: 'flex',
      alignItems: 'center',
      gap: '8px',
    },
    sectionIcon: {
      fontSize: '16px',
    },
    inputGrid: {
      display: 'grid',
      gridTemplateColumns: '1fr 1fr',
      gap: '12px',
    },
    typologyGrid: {
      display: 'grid',
      gridTemplateColumns: 'repeat(4, 1fr)',
      gap: '8px',
    },
    paramGrid: {
      display: 'grid',
      gridTemplateColumns: '1fr 1fr',
      gap: '12px',
    },
    generateBtn: {
      margin: '16px',
      padding: '14px 24px',
      backgroundColor: COLORS.accent,
      color: 'white',
      border: 'none',
      borderRadius: '12px',
      fontSize: '15px',
      fontWeight: '600',
      cursor: 'pointer',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      gap: '8px',
      transition: 'all 0.2s',
    },
    generateBtnDisabled: {
      backgroundColor: COLORS.border,
      cursor: 'not-allowed',
    },
  };

  // Get typology-specific parameters
  const renderTypologyParams = () => {
    switch (selectedTypology) {
      case 'selfStorage':
        return (
          <div style={styles.paramGrid}>
            <ParamField
              label="Stories"
              type="number"
              value={params.stories}
              onChange={(v) => setParams({ ...params, stories: parseInt(v) })}
              options={[1, 2, 3, 4].map(n => ({ value: n, label: `${n}-Story` }))}
            />
            <ParamField
              label="Climate Control %"
              type="number"
              value={params.climateControlled}
              onChange={(v) => setParams({ ...params, climateControlled: parseInt(v) })}
              min={0}
              max={100}
            />
          </div>
        );

      case 'multifamily':
        return (
          <ParamField
            label="Parking Ratio (per unit)"
            type="number"
            value={params.parkingRatio}
            onChange={(v) => setParams({ ...params, parkingRatio: parseFloat(v) })}
            step={0.1}
            min={0.5}
            max={3}
          />
        );

      case 'industrial':
        return (
          <div style={styles.paramGrid}>
            <ParamField
              label="Clear Height (ft)"
              type="number"
              value={params.clearHeight}
              onChange={(v) => setParams({ ...params, clearHeight: parseInt(v) })}
              min={20}
              max={60}
            />
            <ParamField
              label="Bay Depth (ft)"
              type="number"
              value={params.bayDepth}
              onChange={(v) => setParams({ ...params, bayDepth: parseInt(v) })}
              min={100}
              max={300}
            />
          </div>
        );

      case 'seniorLiving':
        return (
          <div style={styles.paramGrid}>
            <ParamField
              label="Care Level"
              value={params.careLevel}
              onChange={(v) => setParams({ ...params, careLevel: v })}
              options={[
                { value: 'independent', label: 'Independent Living' },
                { value: 'assisted', label: 'Assisted Living' },
                { value: 'memory', label: 'Memory Care' },
              ]}
            />
            <ParamField
              label="Monthly Rate ($)"
              type="number"
              value={params.monthlyRate}
              onChange={(v) => setParams({ ...params, monthlyRate: parseInt(v) })}
              step={100}
            />
          </div>
        );

      case 'medical':
        return (
          <ParamField
            label="Rent per SF ($)"
            type="number"
            value={params.rentPerSF}
            onChange={(v) => setParams({ ...params, rentPerSF: parseFloat(v) })}
            step={0.5}
          />
        );

      case 'hotel':
        return (
          <ParamField
            label="ADR ($)"
            type="number"
            value={params.adr}
            onChange={(v) => setParams({ ...params, adr: parseInt(v) })}
            step={5}
          />
        );

      case 'retail':
        return (
          <ParamField
            label="Anchor Ratio"
            type="number"
            value={params.anchorRatio}
            onChange={(v) => setParams({ ...params, anchorRatio: parseFloat(v) })}
            step={0.1}
            min={0}
            max={1}
          />
        );

      default:
        return null;
    }
  };

  return (
    <div style={styles.container}>
      {/* Site Details Section */}
      <div style={styles.section}>
        <h3 style={styles.sectionTitle}>
          <span style={styles.sectionIcon}>📍</span>
          Site Details
        </h3>
        <div style={styles.inputGrid}>
          <ParamField
            label="Acreage"
            type="number"
            value={siteAcreage}
            onChange={setSiteAcreage}
            step={0.1}
            min={0.1}
          />
          <ParamField
            label="Zoning"
            value={zoning}
            onChange={setZoning}
            options={Object.entries(BREVARD_ZONING_DATA).map(([code, data]) => ({
              value: code,
              label: `${code} - ${data.name}`,
            }))}
          />
        </div>
      </div>

      {/* Typology Selection Section */}
      <div style={styles.section}>
        <h3 style={styles.sectionTitle}>
          <span style={styles.sectionIcon}>🏗️</span>
          Development Type
        </h3>
        <div style={styles.typologyGrid}>
          {Object.entries(TYPOLOGY_CONFIGS).map(([key, config]) => (
            <TypologyButton
              key={key}
              config={config}
              typologyKey={key}
              isSelected={selectedTypology === key}
              onClick={setSelectedTypology}
            />
          ))}
        </div>
      </div>

      {/* Parameters Section */}
      <div style={styles.section}>
        <h3 style={styles.sectionTitle}>
          <span style={styles.sectionIcon}>⚙️</span>
          Parameters
        </h3>
        {renderTypologyParams()}
      </div>

      {/* Generate Button */}
      <button
        style={{
          ...styles.generateBtn,
          ...(isGenerating ? styles.generateBtnDisabled : {}),
        }}
        onClick={onGenerate}
        disabled={isGenerating}
      >
        {isGenerating ? (
          <>
            <span>⏳</span>
            <span>Generating...</span>
          </>
        ) : (
          <>
            <span>⚡</span>
            <span>Generate Feasibility</span>
          </>
        )}
      </button>
    </div>
  );
}
