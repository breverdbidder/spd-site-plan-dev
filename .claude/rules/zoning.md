---
paths: src/**/*.py
---

# Zoning & Development Rules - SPD

## Brevard County Zoning Reference

### Residential Zoning

| Code | Name | Min Lot Size | Density |
|------|------|--------------|---------|
| RU-1-13 | Single Family | 13,000 sf | 3.35 du/ac |
| RU-1-11 | Single Family | 11,000 sf | 3.96 du/ac |
| RU-1-9 | Single Family | 9,000 sf | 4.84 du/ac |
| RU-1-7 | Single Family | 7,500 sf | 5.80 du/ac |
| RU-2-10 | Duplex | 10,000 sf | 8.71 du/ac |
| RU-2-6 | Multi-Family | 6,000 sf | 14.52 du/ac |

### Commercial Zoning

| Code | Name | Notes |
|------|------|-------|
| BU-1 | General Business | Most commercial uses |
| BU-1-A | Limited Business | Office, limited retail |
| BU-2 | Retail Business | Retail focused |
| IU | Industrial | Manufacturing, warehouse |
| IU-1 | Light Industrial | Light manufacturing |

## Standard Setbacks

### Residential (RU-1)
```python
SETBACKS_RU1 = {
    "front": 25,      # feet
    "rear": 20,       # feet
    "side": 7.5,      # feet
    "corner_side": 15 # feet (if corner lot)
}
```

### Commercial (BU-1)
```python
SETBACKS_BU1 = {
    "front": 25,
    "rear": 20,
    "side": 10,
    "adjacent_residential": 25  # buffer to residential
}
```

## Height Limits

| Zone | Max Height |
|------|------------|
| RU-1 | 35 feet |
| RU-2 | 45 feet |
| BU-1 | 45 feet |
| BU-2 | 35 feet |

## Impervious Surface Limits

| Zone | Max Impervious |
|------|----------------|
| RU-1 | 50% |
| RU-2 | 60% |
| BU-1 | 80% |
| IU | 85% |

## Parking Requirements

| Use | Spaces Required |
|-----|-----------------|
| Single Family | 2 per unit |
| Multi-Family | 1.5 per unit |
| Retail | 1 per 200 sf |
| Office | 1 per 300 sf |
| Restaurant | 1 per 75 sf |

## Environmental Overlays

### Flood Zones
- **Zone A**: 1% annual flood risk, BFE unknown
- **Zone AE**: 1% annual flood risk, BFE determined
- **Zone X**: Minimal flood risk

### Wetlands
- Jurisdictional wetlands require SJRWMD permit
- 25-foot upland buffer typically required
- Mitigation may be required for impacts

## Data Sources

| Data | Source | API |
|------|--------|-----|
| Parcel data | BCPAO | bcpao.us/api |
| Zoning | Brevard County | brevardfl.gov |
| Flood zones | FEMA | msc.fema.gov |
| Wetlands | NWI | fws.gov/wetlands |
