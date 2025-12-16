"""
SPD Site Plan Development - Parking & Unit Configuration Calculator
====================================================================
LangGraph Node: parking_unit_analysis

This module calculates optimal unit configurations based on:
- Zoning density limits (du/acre)
- Parking requirements (spaces per dwelling unit)
- Site constraints (lot size, setbacks, easements)
- Micro-unit configurations (3 vs 4 per dwelling)
- Financial projections

Part of the 12-Stage SPD Pipeline:
1. Discovery → 2. Site Analysis → 3. Zoning Review → 4. **Parking/Unit Config** →
5. Building Design → 6. Financial Pro Forma → 7. Risk Assessment → 8. Report →
9. Decision → 10. Entitlement → 11. Construction → 12. Archive
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from enum import Enum
import math


class ZoningDistrict(Enum):
    """Palm Bay Zoning Districts with density limits"""
    RM_15 = 15  # 15 du/acre
    RM_20 = 20  # 20 du/acre
    RM_25 = 25  # 25 du/acre
    PUD = 0     # Planned Unit Development - variable


class ParkingTier(Enum):
    """Parking allocation tiers"""
    WITH_PARKING = "with_parking"
    NO_PARKING = "no_parking"


@dataclass
class SiteConstraints:
    """Site physical constraints"""
    lot_sf: float                    # Total lot square footage
    lot_width: float                 # Lot width in feet
    lot_depth: float                 # Lot depth in feet
    easement_sf: float = 0           # Easement area (not buildable)
    wellhead_sf: float = 0           # Wellhead protection zone
    front_setback: float = 25        # Front setback in feet
    rear_setback: float = 25         # Rear setback in feet
    side_setback: float = 15         # Side setback in feet (each side)
    max_lot_coverage: float = 0.60   # Maximum lot coverage (60%)
    max_height_no_variance: float = 25  # Max height without variance
    
    @property
    def lot_acres(self) -> float:
        return self.lot_sf / 43560
    
    @property
    def buildable_sf(self) -> float:
        return self.lot_sf - self.easement_sf - self.wellhead_sf
    
    @property
    def building_envelope_sf(self) -> float:
        """Calculate building envelope after setbacks"""
        usable_width = self.lot_width - (self.side_setback * 2)
        # Estimate usable depth based on buildable area
        usable_depth = (self.buildable_sf / self.lot_width) - self.front_setback - self.rear_setback
        return max(0, usable_width * usable_depth)
    
    @property
    def max_footprint_sf(self) -> float:
        """Maximum building footprint based on coverage"""
        return self.building_envelope_sf * self.max_lot_coverage


@dataclass
class MicroUnitSpec:
    """Micro-unit specifications"""
    living_sf: int = 180          # Living/sleeping area
    kitchenette_sf: int = 70      # Kitchenette with mini-fridge, 2-burner, micro
    bathroom_sf: int = 50         # Bathroom with toilet, sink, shower
    closet_sf: int = 20           # Closet space
    
    @property
    def total_sf(self) -> int:
        return self.living_sf + self.kitchenette_sf + self.bathroom_sf + self.closet_sf
    
    def __repr__(self):
        return f"MicroUnit({self.total_sf}SF)"


@dataclass 
class DwellingUnitConfig:
    """Configuration for a dwelling unit containing micro-units"""
    micro_units_per_dwelling: int
    micro_unit_spec: MicroUnitSpec
    shared_entry_sf: int = 60       # Internal hallway/entry
    parking_spaces_per_dwelling: int = 2  # Code requirement
    
    @property
    def dwelling_unit_sf(self) -> int:
        return (self.micro_units_per_dwelling * self.micro_unit_spec.total_sf) + self.shared_entry_sf
    
    @property
    def tenants_with_parking(self) -> int:
        """Tenants per dwelling that get parking"""
        return min(self.parking_spaces_per_dwelling, self.micro_units_per_dwelling)
    
    @property
    def tenants_without_parking(self) -> int:
        """Tenants per dwelling without parking"""
        return max(0, self.micro_units_per_dwelling - self.parking_spaces_per_dwelling)


@dataclass
class RentStructure:
    """Rent pricing structure"""
    rent_with_parking: int          # Monthly rent for micro-unit with parking
    rent_no_parking: int            # Monthly rent for micro-unit without parking
    parking_premium: int = 200      # Premium for parking ($200/mo)
    
    @classmethod
    def from_base_rent(cls, base_rent: int, parking_premium: int = 200):
        """Create rent structure from base rent"""
        return cls(
            rent_with_parking=base_rent,
            rent_no_parking=base_rent - parking_premium,
            parking_premium=parking_premium
        )


@dataclass
class ParkingAllocation:
    """Parking allocation results"""
    total_spaces_required: int
    total_spaces_available: int
    tenants_with_parking: int
    tenants_without_parking: int
    parking_ratio: float            # Spaces per tenant
    meets_code: bool
    
    @property
    def pct_with_parking(self) -> float:
        total = self.tenants_with_parking + self.tenants_without_parking
        return (self.tenants_with_parking / total * 100) if total > 0 else 0
    
    @property
    def pct_without_parking(self) -> float:
        return 100 - self.pct_with_parking


@dataclass
class BuildingSpec:
    """Building specifications"""
    gross_sf: float
    stories: int
    footprint_sf: float
    height_ft: float
    fits_envelope: bool
    requires_variance: bool
    units_per_floor: int
    
    @property
    def floor_plate_sf(self) -> float:
        return self.gross_sf / self.stories


@dataclass
class FinancialProjection:
    """Financial projections"""
    monthly_gross: float
    annual_gpr: float
    vacancy_rate: float
    egi: float
    opex_rate: float
    opex: float
    noi: float
    cap_rate: float
    value: float
    construction_cost: float
    
    @property
    def cash_on_cash(self) -> float:
        return (self.noi / self.construction_cost * 100) if self.construction_cost > 0 else 0


@dataclass
class UnitConfigScenario:
    """Complete unit configuration scenario"""
    name: str
    dwelling_units: int
    micro_units_per_dwelling: int
    total_tenants: int
    micro_unit_sf: int
    dwelling_unit_sf: int
    parking: ParkingAllocation
    building: BuildingSpec
    financials: FinancialProjection
    rent_structure: RentStructure
    risk_level: str                 # "LOW", "MEDIUM", "HIGH"
    recommendation: str


class ParkingUnitCalculator:
    """
    Main calculator for parking and unit configurations.
    
    Usage:
        calculator = ParkingUnitCalculator(
            site=SiteConstraints(...),
            zoning=ZoningDistrict.RM_20,
            parking_available=42
        )
        scenarios = calculator.calculate_scenarios()
    """
    
    # Construction cost per SF
    CONSTRUCTION_COST_PER_SF = 175
    
    # Common area percentage
    COMMON_AREA_PCT = 0.15
    
    # Financial assumptions
    DEFAULT_VACANCY_RATE = 0.08
    DEFAULT_OPEX_RATE = 0.42
    DEFAULT_CAP_RATE = 0.06
    
    # Floor height assumptions
    FLOOR_HEIGHT_FT = 10
    PARAPET_HEIGHT_FT = 2
    
    def __init__(
        self,
        site: SiteConstraints,
        zoning: ZoningDistrict,
        parking_available: int,
        parking_per_dwelling: int = 2
    ):
        self.site = site
        self.zoning = zoning
        self.parking_available = parking_available
        self.parking_per_dwelling = parking_per_dwelling
        
        # Calculate max dwelling units from zoning
        self.max_dwelling_units = int(self.site.lot_acres * self.zoning.value)
    
    def calculate_parking_allocation(
        self,
        dwelling_units: int,
        micro_units_per_dwelling: int
    ) -> ParkingAllocation:
        """Calculate parking allocation for a given configuration"""
        
        total_tenants = dwelling_units * micro_units_per_dwelling
        spaces_required = dwelling_units * self.parking_per_dwelling
        
        # Each dwelling gets parking_per_dwelling spaces
        # Distribute to micro-units within each dwelling
        tenants_with_parking = dwelling_units * min(self.parking_per_dwelling, micro_units_per_dwelling)
        tenants_without_parking = total_tenants - tenants_with_parking
        
        parking_ratio = self.parking_available / total_tenants if total_tenants > 0 else 0
        
        return ParkingAllocation(
            total_spaces_required=spaces_required,
            total_spaces_available=self.parking_available,
            tenants_with_parking=tenants_with_parking,
            tenants_without_parking=tenants_without_parking,
            parking_ratio=round(parking_ratio, 2),
            meets_code=self.parking_available >= spaces_required
        )
    
    def calculate_building_spec(
        self,
        dwelling_units: int,
        dwelling_unit_sf: int
    ) -> BuildingSpec:
        """Calculate building specifications"""
        
        total_living_sf = dwelling_units * dwelling_unit_sf
        gross_sf = total_living_sf / (1 - self.COMMON_AREA_PCT)
        
        # Find minimum stories that fit
        best_stories = None
        for stories in range(2, 6):
            footprint = gross_sf / stories
            if footprint <= self.site.building_envelope_sf:
                best_stories = stories
                break
        
        if best_stories is None:
            best_stories = 5  # Max out at 5 stories
        
        footprint_sf = gross_sf / best_stories
        height_ft = (best_stories * self.FLOOR_HEIGHT_FT) + self.PARAPET_HEIGHT_FT
        
        return BuildingSpec(
            gross_sf=round(gross_sf, 0),
            stories=best_stories,
            footprint_sf=round(footprint_sf, 0),
            height_ft=height_ft,
            fits_envelope=footprint_sf <= self.site.building_envelope_sf,
            requires_variance=height_ft > self.site.max_height_no_variance,
            units_per_floor=math.ceil(dwelling_units / best_stories)
        )
    
    def calculate_financials(
        self,
        parking: ParkingAllocation,
        rent_structure: RentStructure,
        building: BuildingSpec,
        vacancy_rate: float = None,
        opex_rate: float = None,
        cap_rate: float = None
    ) -> FinancialProjection:
        """Calculate financial projections"""
        
        vacancy_rate = vacancy_rate or self.DEFAULT_VACANCY_RATE
        opex_rate = opex_rate or self.DEFAULT_OPEX_RATE
        cap_rate = cap_rate or self.DEFAULT_CAP_RATE
        
        monthly_gross = (
            (parking.tenants_with_parking * rent_structure.rent_with_parking) +
            (parking.tenants_without_parking * rent_structure.rent_no_parking)
        )
        
        annual_gpr = monthly_gross * 12
        egi = annual_gpr * (1 - vacancy_rate)
        opex = egi * opex_rate
        noi = egi - opex
        value = noi / cap_rate
        
        construction_cost = building.gross_sf * self.CONSTRUCTION_COST_PER_SF
        
        return FinancialProjection(
            monthly_gross=monthly_gross,
            annual_gpr=annual_gpr,
            vacancy_rate=vacancy_rate,
            egi=egi,
            opex_rate=opex_rate,
            opex=opex,
            noi=round(noi, 0),
            cap_rate=cap_rate,
            value=round(value, 0),
            construction_cost=round(construction_cost, 0)
        )
    
    def assess_risk(self, parking: ParkingAllocation) -> str:
        """Assess market risk based on parking ratio"""
        pct_no_parking = parking.pct_without_parking
        
        if pct_no_parking <= 25:
            return "LOW"
        elif pct_no_parking <= 40:
            return "MEDIUM"
        else:
            return "HIGH"
    
    def calculate_scenario(
        self,
        name: str,
        micro_units_per_dwelling: int,
        micro_unit_sf: int,
        rent_with_parking: int,
        rent_no_parking: int,
        dwelling_units: int = None
    ) -> UnitConfigScenario:
        """Calculate a complete scenario"""
        
        dwelling_units = dwelling_units or self.max_dwelling_units
        
        # Create micro-unit spec
        micro_spec = MicroUnitSpec(
            living_sf=int(micro_unit_sf * 0.56),      # ~56% living
            kitchenette_sf=int(micro_unit_sf * 0.22), # ~22% kitchen
            bathroom_sf=int(micro_unit_sf * 0.16),    # ~16% bath
            closet_sf=int(micro_unit_sf * 0.06)       # ~6% closet
        )
        
        # Create dwelling config
        dwelling_config = DwellingUnitConfig(
            micro_units_per_dwelling=micro_units_per_dwelling,
            micro_unit_spec=micro_spec,
            shared_entry_sf=60 if micro_units_per_dwelling == 3 else 80,
            parking_spaces_per_dwelling=self.parking_per_dwelling
        )
        
        # Rent structure
        rent_structure = RentStructure(
            rent_with_parking=rent_with_parking,
            rent_no_parking=rent_no_parking
        )
        
        # Calculate all components
        parking = self.calculate_parking_allocation(
            dwelling_units, 
            micro_units_per_dwelling
        )
        
        building = self.calculate_building_spec(
            dwelling_units,
            dwelling_config.dwelling_unit_sf
        )
        
        financials = self.calculate_financials(
            parking,
            rent_structure,
            building
        )
        
        risk_level = self.assess_risk(parking)
        
        # Generate recommendation
        if risk_level == "LOW":
            recommendation = "RECOMMENDED - Low lease-up risk"
        elif risk_level == "MEDIUM":
            recommendation = "VIABLE - Moderate lease-up risk, consider e-bike infrastructure"
        else:
            recommendation = "CAUTION - High lease-up risk, 50%+ tenants need to be car-free"
        
        return UnitConfigScenario(
            name=name,
            dwelling_units=dwelling_units,
            micro_units_per_dwelling=micro_units_per_dwelling,
            total_tenants=dwelling_units * micro_units_per_dwelling,
            micro_unit_sf=micro_unit_sf,
            dwelling_unit_sf=dwelling_config.dwelling_unit_sf,
            parking=parking,
            building=building,
            financials=financials,
            rent_structure=rent_structure,
            risk_level=risk_level,
            recommendation=recommendation
        )
    
    def calculate_all_scenarios(self) -> List[UnitConfigScenario]:
        """Calculate both 3-micro and 4-micro scenarios"""
        
        scenarios = []
        
        # Scenario A: 4 micro-units per dwelling (compact 320 SF)
        scenario_a = self.calculate_scenario(
            name="Scenario A: 4 Micro-Units per Dwelling",
            micro_units_per_dwelling=4,
            micro_unit_sf=320,
            rent_with_parking=850,
            rent_no_parking=650
        )
        scenarios.append(scenario_a)
        
        # Scenario B: 3 micro-units per dwelling (comfortable 400 SF)
        scenario_b = self.calculate_scenario(
            name="Scenario B: 3 Micro-Units per Dwelling",
            micro_units_per_dwelling=3,
            micro_unit_sf=400,
            rent_with_parking=900,
            rent_no_parking=700
        )
        scenarios.append(scenario_b)
        
        return scenarios
    
    def to_dict(self, scenario: UnitConfigScenario) -> Dict:
        """Convert scenario to dictionary for JSON serialization"""
        return {
            "name": scenario.name,
            "dwelling_units": scenario.dwelling_units,
            "micro_units_per_dwelling": scenario.micro_units_per_dwelling,
            "total_tenants": scenario.total_tenants,
            "micro_unit_sf": scenario.micro_unit_sf,
            "dwelling_unit_sf": scenario.dwelling_unit_sf,
            "parking": {
                "spaces_required": scenario.parking.total_spaces_required,
                "spaces_available": scenario.parking.total_spaces_available,
                "tenants_with_parking": scenario.parking.tenants_with_parking,
                "tenants_without_parking": scenario.parking.tenants_without_parking,
                "pct_with_parking": round(scenario.parking.pct_with_parking, 1),
                "pct_without_parking": round(scenario.parking.pct_without_parking, 1),
                "parking_ratio": scenario.parking.parking_ratio,
                "meets_code": scenario.parking.meets_code
            },
            "building": {
                "gross_sf": scenario.building.gross_sf,
                "stories": scenario.building.stories,
                "footprint_sf": scenario.building.footprint_sf,
                "height_ft": scenario.building.height_ft,
                "fits_envelope": scenario.building.fits_envelope,
                "requires_variance": scenario.building.requires_variance
            },
            "financials": {
                "monthly_gross": scenario.financials.monthly_gross,
                "annual_gpr": scenario.financials.annual_gpr,
                "noi": scenario.financials.noi,
                "value_at_cap": scenario.financials.value,
                "construction_cost": scenario.financials.construction_cost,
                "cash_on_cash": round(scenario.financials.cash_on_cash, 1)
            },
            "rent": {
                "with_parking": scenario.rent_structure.rent_with_parking,
                "no_parking": scenario.rent_structure.rent_no_parking
            },
            "risk_level": scenario.risk_level,
            "recommendation": scenario.recommendation
        }


# =============================================================================
# LANGGRAPH NODE FUNCTION
# =============================================================================

def parking_unit_analysis_node(state: Dict) -> Dict:
    """
    LangGraph node for parking and unit configuration analysis.
    
    Input state keys:
        - site_constraints: Dict with lot_sf, lot_width, lot_depth, etc.
        - zoning_district: str (e.g., "RM_20")
        - parking_available: int
        
    Output state keys:
        - parking_analysis: Dict with scenario comparisons
        - recommended_scenario: str
        - unit_config_complete: bool
    """
    
    # Extract site constraints from state
    site_data = state.get("site_constraints", {})
    site = SiteConstraints(
        lot_sf=site_data.get("lot_sf", 46394),
        lot_width=site_data.get("lot_width", 167.5),
        lot_depth=site_data.get("lot_depth", 277.0),
        easement_sf=site_data.get("easement_sf", 0),
        wellhead_sf=site_data.get("wellhead_sf", 22000),
        front_setback=site_data.get("front_setback", 25),
        rear_setback=site_data.get("rear_setback", 25),
        side_setback=site_data.get("side_setback", 15),
        max_lot_coverage=site_data.get("max_lot_coverage", 0.60),
        max_height_no_variance=site_data.get("max_height_no_variance", 25)
    )
    
    # Get zoning
    zoning_str = state.get("zoning_district", "RM_20")
    zoning = ZoningDistrict[zoning_str]
    
    # Get parking
    parking_available = state.get("parking_available", 42)
    
    # Create calculator
    calculator = ParkingUnitCalculator(
        site=site,
        zoning=zoning,
        parking_available=parking_available
    )
    
    # Calculate scenarios
    scenarios = calculator.calculate_all_scenarios()
    
    # Convert to dicts
    scenario_dicts = [calculator.to_dict(s) for s in scenarios]
    
    # Determine recommendation
    # Prefer scenario with lower risk unless NOI difference is significant
    scenario_a = scenarios[0]
    scenario_b = scenarios[1]
    
    noi_diff = scenario_a.financials.noi - scenario_b.financials.noi
    noi_diff_pct = (noi_diff / scenario_b.financials.noi * 100) if scenario_b.financials.noi > 0 else 0
    
    if scenario_a.risk_level == "HIGH" and noi_diff_pct < 25:
        recommended = "Scenario B"
        reason = f"Lower risk ({scenario_b.risk_level}) with only {noi_diff_pct:.0f}% less NOI"
    elif scenario_a.risk_level == "HIGH":
        recommended = "Scenario A"
        reason = f"Higher NOI (+${noi_diff:,.0f}/yr) justifies risk"
    else:
        recommended = "Scenario A"
        reason = f"Higher NOI (+${noi_diff:,.0f}/yr) with acceptable risk"
    
    # Update state
    return {
        **state,
        "parking_analysis": {
            "scenarios": scenario_dicts,
            "comparison": {
                "noi_difference": noi_diff,
                "noi_difference_pct": round(noi_diff_pct, 1),
                "tenant_difference": scenario_a.total_tenants - scenario_b.total_tenants
            }
        },
        "recommended_scenario": recommended,
        "recommendation_reason": reason,
        "unit_config_complete": True
    }


# =============================================================================
# EXAMPLE USAGE / TEST
# =============================================================================

if __name__ == "__main__":
    # Bliss Palm Bay site constraints
    site = SiteConstraints(
        lot_sf=46394,
        lot_width=167.5,
        lot_depth=277.0,
        wellhead_sf=22000,
        front_setback=25,
        rear_setback=25,
        side_setback=15,
        max_lot_coverage=0.60,
        max_height_no_variance=25
    )
    
    # Create calculator
    calculator = ParkingUnitCalculator(
        site=site,
        zoning=ZoningDistrict.RM_20,
        parking_available=42
    )
    
    print("=" * 80)
    print("BLISS PALM BAY - PARKING & UNIT CONFIGURATION ANALYSIS")
    print("=" * 80)
    print(f"\nSite: {site.lot_acres:.3f} acres ({site.lot_sf:,} SF)")
    print(f"Zoning: RM-20 (Max {calculator.max_dwelling_units} dwelling units)")
    print(f"Parking Available: {calculator.parking_available} spaces")
    print(f"Building Envelope: {site.building_envelope_sf:,.0f} SF")
    
    # Calculate scenarios
    scenarios = calculator.calculate_all_scenarios()
    
    for scenario in scenarios:
        print(f"\n{'='*80}")
        print(f"{scenario.name}")
        print("=" * 80)
        
        print(f"\n  CONFIGURATION:")
        print(f"    Dwelling Units:        {scenario.dwelling_units}")
        print(f"    Micro-Units/Dwelling:  {scenario.micro_units_per_dwelling}")
        print(f"    Total Tenants:         {scenario.total_tenants}")
        print(f"    Micro-Unit Size:       {scenario.micro_unit_sf} SF")
        print(f"    Dwelling Unit Size:    {scenario.dwelling_unit_sf} SF")
        
        print(f"\n  PARKING:")
        print(f"    Required:              {scenario.parking.total_spaces_required}")
        print(f"    Available:             {scenario.parking.total_spaces_available}")
        print(f"    Meets Code:            {'✅ YES' if scenario.parking.meets_code else '❌ NO'}")
        print(f"    With Parking:          {scenario.parking.tenants_with_parking} ({scenario.parking.pct_with_parking:.0f}%)")
        print(f"    Without Parking:       {scenario.parking.tenants_without_parking} ({scenario.parking.pct_without_parking:.0f}%)")
        print(f"    Parking Ratio:         {scenario.parking.parking_ratio} spaces/tenant")
        
        print(f"\n  BUILDING:")
        print(f"    Gross SF:              {scenario.building.gross_sf:,.0f}")
        print(f"    Stories:               {scenario.building.stories}")
        print(f"    Footprint:             {scenario.building.footprint_sf:,.0f} SF")
        print(f"    Height:                {scenario.building.height_ft} ft")
        print(f"    Fits Envelope:         {'✅ YES' if scenario.building.fits_envelope else '❌ NO'}")
        print(f"    Requires Variance:     {'⚠️ YES' if scenario.building.requires_variance else '✅ NO'}")
        
        print(f"\n  FINANCIALS:")
        print(f"    Monthly Gross:         ${scenario.financials.monthly_gross:,}")
        print(f"    Annual NOI:            ${scenario.financials.noi:,.0f}")
        print(f"    Value @ 6%:            ${scenario.financials.value:,.0f}")
        print(f"    Construction Cost:     ${scenario.financials.construction_cost:,.0f}")
        print(f"    Cash-on-Cash:          {scenario.financials.cash_on_cash:.1f}%")
        
        print(f"\n  RISK: {scenario.risk_level}")
        print(f"  {scenario.recommendation}")
    
    # Summary comparison
    print(f"\n{'='*80}")
    print("SUMMARY COMPARISON")
    print("=" * 80)
    
    a, b = scenarios[0], scenarios[1]
    print(f"""
    ┌────────────────────────────────────────────────────────────────────┐
    │                    Scenario A          Scenario B                  │
    │                    (21 × 4 micro)      (21 × 3 micro)              │
    ├────────────────────────────────────────────────────────────────────┤
    │  Tenants           {a.total_tenants:<20} {b.total_tenants:<20} │
    │  With Parking      {a.parking.tenants_with_parking} ({a.parking.pct_with_parking:.0f}%)             {b.parking.tenants_with_parking} ({b.parking.pct_with_parking:.0f}%)             │
    │  No Parking        {a.parking.tenants_without_parking} ({a.parking.pct_without_parking:.0f}%)             {b.parking.tenants_without_parking} ({b.parking.pct_without_parking:.0f}%)             │
    │  Annual NOI        ${a.financials.noi:,.0f}           ${b.financials.noi:,.0f}           │
    │  Risk Level        {a.risk_level:<20} {b.risk_level:<20} │
    └────────────────────────────────────────────────────────────────────┘
    """)
