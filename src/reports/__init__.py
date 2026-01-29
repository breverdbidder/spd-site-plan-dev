"""
SPD Site Plan Development - Reports Module
Core Component #5: 20-Phase Property Report Generator

Based on ZoneWise methodology used for:
- 800 Lane Ave Titusville case study
- Malabar POC case study
"""

from ..report_generator import (
    PropertyReportGenerator,
    PropertyReport,
    ReportPhase,
    Recommendation,
    PhaseResult,
    PropertyIdentification,
    BaseZoning,
    DimensionalStandards,
    HBUAnalysis,
    AppraisalApproach,
    get_phase_info,
    get_all_phases,
)

__all__ = [
    "PropertyReportGenerator",
    "PropertyReport",
    "ReportPhase",
    "Recommendation",
    "PhaseResult",
    "PropertyIdentification",
    "BaseZoning",
    "DimensionalStandards",
    "HBUAnalysis",
    "AppraisalApproach",
    "get_phase_info",
    "get_all_phases",
]
