#!/usr/bin/env python3
"""
Row Level Security (RLS) Verification and Deployment
P4 Security: Full RLS deployment verification (+2 points)

Validates and enforces RLS policies across all Supabase tables.

Author: BidDeed.AI / Everest Capital USA
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


class RLSAction(Enum):
    SELECT = "SELECT"
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    ALL = "ALL"


@dataclass
class RLSPolicy:
    """Definition of an RLS policy"""
    name: str
    table: str
    action: RLSAction
    using_expression: str
    with_check: Optional[str] = None
    roles: List[str] = None
    
    def __post_init__(self):
        if self.roles is None:
            self.roles = ["authenticated"]
    
    def to_sql(self) -> str:
        """Generate SQL for policy creation"""
        roles_str = ", ".join(self.roles)
        sql = f"""
CREATE POLICY "{self.name}"
ON {self.table}
FOR {self.action.value}
TO {roles_str}
USING ({self.using_expression})"""
        
        if self.with_check:
            sql += f"\nWITH CHECK ({self.with_check})"
        
        return sql + ";"


# =============================================================================
# RLS POLICY DEFINITIONS FOR SPD TABLES
# =============================================================================

SPD_RLS_POLICIES = {
    # Pipeline runs - users can only see their own runs
    "pipeline_runs": [
        RLSPolicy(
            name="pipeline_runs_select_own",
            table="pipeline_runs",
            action=RLSAction.SELECT,
            using_expression="auth.uid() = user_id"
        ),
        RLSPolicy(
            name="pipeline_runs_insert_own",
            table="pipeline_runs",
            action=RLSAction.INSERT,
            using_expression="true",
            with_check="auth.uid() = user_id"
        ),
        RLSPolicy(
            name="pipeline_runs_update_own",
            table="pipeline_runs",
            action=RLSAction.UPDATE,
            using_expression="auth.uid() = user_id"
        ),
    ],
    
    # Parcels - public read, authenticated write
    "parcels": [
        RLSPolicy(
            name="parcels_select_all",
            table="parcels",
            action=RLSAction.SELECT,
            using_expression="true",
            roles=["anon", "authenticated"]
        ),
        RLSPolicy(
            name="parcels_insert_authenticated",
            table="parcels",
            action=RLSAction.INSERT,
            using_expression="true",
            with_check="auth.role() = 'authenticated'"
        ),
        RLSPolicy(
            name="parcels_update_authenticated",
            table="parcels",
            action=RLSAction.UPDATE,
            using_expression="auth.role() = 'authenticated'"
        ),
    ],
    
    # Scoring results - users see own, admins see all
    "scoring_results": [
        RLSPolicy(
            name="scoring_select_own",
            table="scoring_results",
            action=RLSAction.SELECT,
            using_expression="auth.uid() = user_id OR auth.jwt()->>'role' = 'admin'"
        ),
        RLSPolicy(
            name="scoring_insert_own",
            table="scoring_results",
            action=RLSAction.INSERT,
            using_expression="true",
            with_check="auth.uid() = user_id"
        ),
    ],
    
    # Reports - private to owner
    "reports": [
        RLSPolicy(
            name="reports_select_own",
            table="reports",
            action=RLSAction.SELECT,
            using_expression="auth.uid() = user_id"
        ),
        RLSPolicy(
            name="reports_insert_own",
            table="reports",
            action=RLSAction.INSERT,
            using_expression="true",
            with_check="auth.uid() = user_id"
        ),
        RLSPolicy(
            name="reports_delete_own",
            table="reports",
            action=RLSAction.DELETE,
            using_expression="auth.uid() = user_id"
        ),
    ],
    
    # Feasibility analyses - private to owner
    "feasibility_analyses": [
        RLSPolicy(
            name="feasibility_select_own",
            table="feasibility_analyses",
            action=RLSAction.SELECT,
            using_expression="auth.uid() = user_id"
        ),
        RLSPolicy(
            name="feasibility_insert_own",
            table="feasibility_analyses",
            action=RLSAction.INSERT,
            using_expression="true",
            with_check="auth.uid() = user_id"
        ),
    ],
    
    # Chat sessions - private
    "chat_sessions": [
        RLSPolicy(
            name="chat_select_own",
            table="chat_sessions",
            action=RLSAction.SELECT,
            using_expression="auth.uid() = user_id"
        ),
        RLSPolicy(
            name="chat_insert_own",
            table="chat_sessions",
            action=RLSAction.INSERT,
            using_expression="true",
            with_check="auth.uid() = user_id"
        ),
        RLSPolicy(
            name="chat_delete_own",
            table="chat_sessions",
            action=RLSAction.DELETE,
            using_expression="auth.uid() = user_id"
        ),
    ],
    
    # Security audit logs - admin only
    "security_audit_logs": [
        RLSPolicy(
            name="audit_select_admin",
            table="security_audit_logs",
            action=RLSAction.SELECT,
            using_expression="auth.jwt()->>'role' = 'admin'",
            roles=["authenticated"]
        ),
        RLSPolicy(
            name="audit_insert_system",
            table="security_audit_logs",
            action=RLSAction.INSERT,
            using_expression="true",
            roles=["service_role"]
        ),
    ],
    
    # Performance metrics - admin read, system write
    "performance_metrics": [
        RLSPolicy(
            name="metrics_select_admin",
            table="performance_metrics",
            action=RLSAction.SELECT,
            using_expression="auth.jwt()->>'role' = 'admin'",
            roles=["authenticated"]
        ),
        RLSPolicy(
            name="metrics_insert_system",
            table="performance_metrics",
            action=RLSAction.INSERT,
            using_expression="true",
            roles=["service_role"]
        ),
    ],
    
    # Credential rotation logs - admin only
    "credential_rotation_logs": [
        RLSPolicy(
            name="rotation_select_admin",
            table="credential_rotation_logs",
            action=RLSAction.SELECT,
            using_expression="auth.jwt()->>'role' = 'admin'",
            roles=["authenticated"]
        ),
    ],
}


class RLSVerifier:
    """
    Verifies and deploys RLS policies to Supabase.
    
    Usage:
        verifier = RLSVerifier(supabase_url, service_key)
        
        # Check current RLS status
        status = await verifier.verify_all_tables()
        
        # Deploy missing policies
        await verifier.deploy_missing_policies()
        
        # Generate full migration
        migration = verifier.generate_migration()
    """
    
    def __init__(self, supabase_url: str = None, service_key: str = None):
        self.supabase_url = supabase_url or os.environ.get("SUPABASE_URL")
        self.service_key = service_key or os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        self._verification_results: Dict[str, Any] = {}
    
    async def _execute_sql(self, sql: str) -> Dict[str, Any]:
        """Execute SQL via Supabase REST API"""
        import urllib.request
        
        url = f"{self.supabase_url}/rest/v1/rpc/exec_sql"
        data = json.dumps({"query": sql}).encode()
        
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "apikey": self.service_key,
                "Authorization": f"Bearer {self.service_key}",
            },
            method="POST"
        )
        
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode())
        except Exception as e:
            logger.error(f"SQL execution failed: {e}")
            return {"error": str(e)}
    
    async def check_rls_enabled(self, table: str) -> bool:
        """Check if RLS is enabled on a table"""
        sql = f"""
        SELECT relrowsecurity 
        FROM pg_class 
        WHERE relname = '{table}' AND relnamespace = 'public'::regnamespace;
        """
        result = await self._execute_sql(sql)
        return result.get("relrowsecurity", False) if not result.get("error") else False
    
    async def get_existing_policies(self, table: str) -> List[str]:
        """Get list of existing policy names for a table"""
        sql = f"""
        SELECT polname 
        FROM pg_policy 
        WHERE polrelid = '{table}'::regclass;
        """
        result = await self._execute_sql(sql)
        if result.get("error"):
            return []
        return [r["polname"] for r in result] if isinstance(result, list) else []
    
    async def verify_table(self, table: str) -> Dict[str, Any]:
        """Verify RLS status for a single table"""
        rls_enabled = await self.check_rls_enabled(table)
        existing_policies = await self.get_existing_policies(table)
        expected_policies = SPD_RLS_POLICIES.get(table, [])
        
        missing_policies = [
            p.name for p in expected_policies 
            if p.name not in existing_policies
        ]
        
        status = {
            "table": table,
            "rls_enabled": rls_enabled,
            "expected_policies": len(expected_policies),
            "existing_policies": len(existing_policies),
            "missing_policies": missing_policies,
            "compliant": rls_enabled and len(missing_policies) == 0,
            "verified_at": datetime.utcnow().isoformat(),
        }
        
        self._verification_results[table] = status
        return status
    
    async def verify_all_tables(self) -> Dict[str, Any]:
        """Verify RLS for all SPD tables"""
        results = {
            "tables": {},
            "summary": {
                "total_tables": len(SPD_RLS_POLICIES),
                "compliant_tables": 0,
                "non_compliant_tables": 0,
                "total_policies_expected": 0,
                "total_policies_missing": 0,
            },
            "verified_at": datetime.utcnow().isoformat(),
        }
        
        for table in SPD_RLS_POLICIES:
            status = await self.verify_table(table)
            results["tables"][table] = status
            
            if status["compliant"]:
                results["summary"]["compliant_tables"] += 1
            else:
                results["summary"]["non_compliant_tables"] += 1
            
            results["summary"]["total_policies_expected"] += status["expected_policies"]
            results["summary"]["total_policies_missing"] += len(status["missing_policies"])
        
        # Calculate compliance score
        total = results["summary"]["total_tables"]
        compliant = results["summary"]["compliant_tables"]
        results["summary"]["compliance_score"] = round((compliant / total) * 100, 1) if total > 0 else 0
        
        return results
    
    def generate_enable_rls_sql(self, table: str) -> str:
        """Generate SQL to enable RLS on a table"""
        return f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;"
    
    def generate_policy_sql(self, policy: RLSPolicy) -> str:
        """Generate SQL for a policy"""
        return policy.to_sql()
    
    def generate_migration(self) -> str:
        """Generate complete RLS migration SQL"""
        lines = [
            "-- SPD Site Plan Development RLS Migration",
            f"-- Generated: {datetime.utcnow().isoformat()}",
            "-- Author: BidDeed.AI / Everest Capital USA",
            "",
            "BEGIN;",
            "",
        ]
        
        for table, policies in SPD_RLS_POLICIES.items():
            lines.append(f"-- ========== {table.upper()} ==========")
            lines.append(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;")
            lines.append("")
            
            for policy in policies:
                lines.append(f"-- Policy: {policy.name}")
                lines.append(policy.to_sql())
                lines.append("")
        
        lines.append("COMMIT;")
        lines.append("")
        lines.append("-- Verification query:")
        lines.append("-- SELECT schemaname, tablename, policyname, permissive, roles, cmd, qual")
        lines.append("-- FROM pg_policies WHERE schemaname = 'public';")
        
        return "\n".join(lines)
    
    async def deploy_missing_policies(self, dry_run: bool = True) -> Dict[str, Any]:
        """Deploy missing RLS policies"""
        results = {
            "deployed": [],
            "failed": [],
            "skipped": [],
            "dry_run": dry_run,
        }
        
        for table, policies in SPD_RLS_POLICIES.items():
            # First enable RLS if needed
            rls_enabled = await self.check_rls_enabled(table)
            if not rls_enabled:
                if dry_run:
                    results["skipped"].append(f"ENABLE RLS on {table}")
                else:
                    sql = self.generate_enable_rls_sql(table)
                    result = await self._execute_sql(sql)
                    if result.get("error"):
                        results["failed"].append({"table": table, "error": result["error"]})
                    else:
                        results["deployed"].append(f"ENABLE RLS on {table}")
            
            # Deploy each policy
            existing = await self.get_existing_policies(table)
            for policy in policies:
                if policy.name in existing:
                    continue
                
                if dry_run:
                    results["skipped"].append(policy.name)
                else:
                    sql = policy.to_sql()
                    result = await self._execute_sql(sql)
                    if result.get("error"):
                        results["failed"].append({"policy": policy.name, "error": result["error"]})
                    else:
                        results["deployed"].append(policy.name)
        
        return results
    
    def get_verification_report(self) -> str:
        """Generate human-readable verification report"""
        lines = [
            "=" * 60,
            "RLS VERIFICATION REPORT",
            f"Generated: {datetime.utcnow().isoformat()}",
            "=" * 60,
            "",
        ]
        
        for table, status in self._verification_results.items():
            icon = "✅" if status["compliant"] else "❌"
            lines.append(f"{icon} {table}")
            lines.append(f"   RLS Enabled: {status['rls_enabled']}")
            lines.append(f"   Policies: {status['existing_policies']}/{status['expected_policies']}")
            if status["missing_policies"]:
                lines.append(f"   Missing: {', '.join(status['missing_policies'])}")
            lines.append("")
        
        return "\n".join(lines)


# =============================================================================
# STANDALONE VERIFICATION SCRIPT
# =============================================================================

async def run_rls_verification():
    """Run full RLS verification"""
    verifier = RLSVerifier()
    
    print("=" * 60)
    print("SPD RLS VERIFICATION")
    print("=" * 60)
    
    # Verify all tables
    results = await verifier.verify_all_tables()
    
    print(f"\nCompliance Score: {results['summary']['compliance_score']}%")
    print(f"Compliant Tables: {results['summary']['compliant_tables']}/{results['summary']['total_tables']}")
    print(f"Missing Policies: {results['summary']['total_policies_missing']}")
    
    # Print detailed report
    print("\n" + verifier.get_verification_report())
    
    # Generate migration if needed
    if results['summary']['total_policies_missing'] > 0:
        print("\nGenerating migration SQL...")
        migration = verifier.generate_migration()
        
        with open("/tmp/rls_migration.sql", "w") as f:
            f.write(migration)
        print("Migration saved to /tmp/rls_migration.sql")
    
    return results


if __name__ == "__main__":
    import asyncio
    asyncio.run(run_rls_verification())
