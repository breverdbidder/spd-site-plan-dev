"""SPD Database Module - Supabase Integration"""
from .supabase_client import (
    SupabaseClient,
    get_supabase_client,
    verify_malabar_poc_data,
    Municipality,
    ZoningDistrict,
    SitePlanRequirement,
    QueryResult,
    TableName
)

__all__ = [
    "SupabaseClient",
    "get_supabase_client", 
    "verify_malabar_poc_data",
    "Municipality",
    "ZoningDistrict",
    "SitePlanRequirement",
    "QueryResult",
    "TableName"
]
