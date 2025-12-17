"""SPD Site Plan Development - Data Source Integrations"""

# Original data sources
from .data_sources import (
    BCPAOClient,
    MunicipalGISClient,
    PlanningRecordsClient,
    FEMAFloodClient,
    OpportunityDataAggregator,
    fetch_opportunity_data
)

# Enhanced API integrations (from API_MEGA_LIBRARY)
from .api_integrations import (
    CensusAPIClient,
    CensusData,
    ApifyRealEstateClient,
    PropertyValuation,
    FirecrawlClient,
    AIWebAgentClient,
    EnhancedDataFetcher,
    enrich_opportunity_with_apis
)

__all__ = [
    # Original
    "BCPAOClient",
    "MunicipalGISClient",
    "PlanningRecordsClient",
    "FEMAFloodClient",
    "OpportunityDataAggregator",
    "fetch_opportunity_data",
    # Enhanced
    "CensusAPIClient",
    "CensusData",
    "ApifyRealEstateClient",
    "PropertyValuation",
    "FirecrawlClient",
    "AIWebAgentClient",
    "EnhancedDataFetcher",
    "enrich_opportunity_with_apis"
]
