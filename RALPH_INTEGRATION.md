# SPD Site Plan Development - Ralph Pattern Integration

**Created by:** Ariel Shapira, Solo Founder - Everest Capital USA  
**Date:** January 10, 2026  
**Application:** SPD Site Plan Development

## Quick Start

### 1. Success Criteria Loaded

✅ `spd_success_criteria.json` - 12 stages defined with validation rules

### 2. Core Ralph Pattern Files

✅ `success_criteria_validator.py` - Validation engine  
✅ `ralph_orchestrator.py` - Autonomous loop executor

### 3. Integration Example

```python
from src.ralph_pattern.ralph_orchestrator import RalphOrchestrator

# Initialize
orchestrator = RalphOrchestrator(
    criteria_path='src/ralph_pattern/spd_success_criteria.json',
    verbose=True
)

# Execute a stage with autonomous retry
async def zoning_analysis_stage(input_data, iteration):
    """Your existing zoning analysis logic"""
    # Extract zoning requirements
    return {
        'zoning_district': 'RS-4',
        'setback_requirements': {...},
        'allowed_uses': [...],
        # ... all required outputs
    }

# Run with Ralph validation
success, output, loop_state = await orchestrator.execute_stage_loop(
    stage_name='zoning_analysis',
    stage_executor=zoning_analysis_stage,
    initial_input={'project_id': '2835546'},
    max_iterations=5
)

if success:
    print(f"✅ Stage completed in {loop_state.current_iteration} iterations")
else:
    print(f"❌ Failed: {loop_state.error_message}")
```

## Stage-Specific Criteria

### Stage 1: Discovery
**Required outputs:** project_id, parcel_id, project_address, application_date, applicant_name, jurisdiction

**Critical validations:**
- Project ID matches format: 7 digits
- Jurisdiction is one of 17 Brevard municipalities

### Stage 3: Zoning Analysis
**Required outputs:** zoning_district, allowed_uses, setback_requirements, parking_requirements, height_restrictions, lot_coverage_limits

**Critical validations:**
- Zoning code data current (within 90 days)
- All four setbacks defined (front, rear, side-left, side-right)
- Proposed use matches allowed uses

### Stage 4: Setback Verification
**Required outputs:** structure_locations, setback_measurements, compliance_status, violations_found

**Critical validations:**
- Measurements within 0.5 feet of plan dimensions
- Every structure on plan has setback verification
- Violations include specific code section reference

### Stage 11: Report Generation
**Required outputs:** docx_report, pdf_report, executive_summary, supporting_exhibits

**Critical validations:**
- DOCX and PDF files valid and readable
- SPD branding only (no BidDeed, Property360, Mariam)
- Site plan images embedded

## First Project: Bliss Palm Bay

**Project ID:** 2835546  
**Jurisdiction:** City of Palm Bay  
**Test the full pipeline on this real project**

```python
# Example: Full SPD pipeline for Bliss Palm Bay
async def run_spd_pipeline():
    project_data = {
        'project_id': '2835546',
        'project_name': 'Bliss Palm Bay',
        'jurisdiction': 'City of Palm Bay'
    }
    
    # Run all 12 stages with Ralph validation
    for stage in ['discovery', 'document_retrieval', 'zoning_analysis', 
                  'setback_verification', 'parking_analysis', 'landscape_review',
                  'stormwater_analysis', 'traffic_impact', 'utility_coordination',
                  'code_compliance_summary', 'report_generation', 'archive']:
        
        success, output, state = await orchestrator.execute_stage_loop(
            stage_name=stage,
            stage_executor=get_stage_executor(stage),
            initial_input=project_data,
            max_iterations=5
        )
        
        if not success:
            print(f"Pipeline stopped at {stage}")
            break
        
        # Pass output to next stage
        project_data.update(output)
    
    print("✅ SPD pipeline completed!")
```

## Cost Optimization

**Smart Router Tier Assignments:**
- FREE tier (Gemini 2.5 Flash): Stages 1,2,5,6,8,9,11,12
- STANDARD (Sonnet 4.5): Stages 3,4,7,10

**Target:** 85% FREE tier (lower than BidDeed.AI due to more complex analysis)

**Estimated cost per project:** $0.30-0.50

## Supabase Integration

**Migration:** Run `/migrations/ralph_pattern_schema_v1.sql` in Supabase SQL editor

**Tables created:**
- `ralph_loop_logs` - All execution logs
- `validation_results` - Detailed validation checks

**Query examples:**
```sql
-- SPD performance
SELECT * FROM ralph_loop_performance WHERE application = 'SPD';

-- Recent SPD runs
SELECT * FROM ralph_loop_logs WHERE application = 'SPD' ORDER BY created_at DESC LIMIT 10;

-- FREE tier percentage for SPD
SELECT * FROM calculate_free_tier_percentage('SPD', 7);
```

## Next Steps

1. **Run migration:** Execute SQL in Supabase
2. **Test discovery:** Run stage 1 on Project 2835546
3. **Iterate:** Refine criteria based on real results
4. **Full pipeline:** Execute all 12 stages

---

**Repo:** github.com/breverdbidder/spd-site-plan-dev  
**Created by:** Ariel Shapira, Solo Founder - Everest Capital USA
