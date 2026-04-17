"""End-to-end pipeline test with Recens Medical sample."""
import json
import sys
from pathlib import Path
from .analyzer import Analyzer
from .validator import Validator
from .reporter import Reporter
from .persistence import PersistenceManager
from .schema_validator import SchemaValidator

# Handle UTF-8 encoding on Windows
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def load_json(filepath):
    """Load JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def test_full_pipeline():
    """Test complete analysis pipeline with Recens Medical sample."""
    print("=" * 60)
    print("NuBI VC Review v2 - End-to-End Pipeline Test")
    print("=" * 60)

    # Setup
    samples_dir = Path(__file__).parent.parent / "samples"
    db_manager = PersistenceManager(":memory:")  # Use in-memory DB for testing
    validator_schema = SchemaValidator()
    analyzer = Analyzer()
    validator = Validator()
    reporter = Reporter()

    # Step 1: Load and validate input
    print("\n[STEP 1] Loading Recens Medical input...")
    input_data = load_json(samples_dir / "sample_input_recens.json")
    is_valid, errors = validator_schema.validate_input(input_data)
    if not is_valid:
        print(f"  [FAIL] Input validation failed: {errors}")
        return False
    print(f"  [OK] Input validated successfully")
    print(f"    - Company: {input_data['company']['name']}")
    print(f"    - Purpose: {input_data['analysis_request']['purpose']}")
    print(f"    - Documents: {len(input_data['documents'])}")

    # Step 2: Run analyzer (Phase 1)
    print("\n[STEP 2] Running Phase 1 Analysis...")
    analysis_internal = analyzer.analyze(input_data)
    analysis_id = analysis_internal['metadata']['analysis_id']
    scores = analysis_internal['phase1_analysis']['scores']
    print(f"  [OK] Phase 1 analysis completed")
    print(f"    - Analysis ID: {analysis_id}")
    print(f"    - Stage 1 (원천기술통제): {scores['stage_1_원천기술통제']['score']}")
    print(f"    - Overall score: {scores['overall']['score']}, Grade: {scores['overall']['grade']}")

    # Validate phase1 output
    is_valid, errors = validator_schema.validate_phase1_analysis(analysis_internal)
    if not is_valid:
        print(f"  [FAIL] Phase 1 validation failed: {errors}")
        return False

    # Step 3: Run validator (Phase 2)
    print("\n[STEP 3] Running Phase 2 Validation...")
    vc_opinion = input_data.get('analysis_request', {}).get('vc_opinion', '')
    phase2_result = validator.validate(analysis_internal, vc_opinion)
    analysis_internal['phase2_validations'] = phase2_result['phase2_validations']
    analysis_internal['metadata']['status_history'].append({
        "status": "validated",
        "timestamp": __import__('datetime').datetime.utcnow().isoformat() + "Z",
        "actor": "system:validator",
        "notes": f"Phase 2 validation complete with {len(phase2_result['validator_flags'])} flags"
    })
    print(f"  [OK] Phase 2 validation completed")
    print(f"    - Claims extracted: {len(phase2_result['phase2_validations']['claims_extracted'])}")
    print(f"    - Validator flags: {len(phase2_result['validator_flags'])}")
    print(f"    - Investment decision: {phase2_result['phase2_validations']['investment_decision']}")

    # Step 4: Update status to validated
    print("\n[STEP 4] Updating status to VALIDATED...")
    analysis_internal['metadata']['status'] = "validated"
    print(f"  [OK] Status updated")

    # Step 5: Simulate human review (update status to reviewed)
    print("\n[STEP 5] Simulating human review...")
    analysis_internal['metadata']['status'] = "reviewed"
    analysis_internal['metadata']['reviewer'] = "user:analyst_001"
    analysis_internal['metadata']['review_timestamp'] = __import__('datetime').datetime.utcnow().isoformat() + "Z"
    analysis_internal['metadata']['status_history'].append({
        "status": "reviewed",
        "timestamp": __import__('datetime').datetime.utcnow().isoformat() + "Z",
        "actor": "user:analyst_001",
        "notes": "Reviewed and approved for publication"
    })
    print(f"  [OK] Status updated to reviewed")

    # Step 6: Run reporter (generate final report)
    print("\n[STEP 6] Generating Final Report...")
    report_result = reporter.generate_report(analysis_internal)
    analysis_internal['report_final'] = report_result['report_final']
    analysis_internal['metadata']['status'] = "published"
    analysis_internal['metadata']['status_history'].append({
        "status": "published",
        "timestamp": __import__('datetime').datetime.utcnow().isoformat() + "Z",
        "actor": "system:reporter",
        "notes": "Final report generated and published"
    })
    print(f"  [OK] Final report generated")
    print(f"    - Report ID: {report_result['report_final']['report_id']}")
    print(f"    - Recommendation: {report_result['report_final']['executive_summary']['key_recommendation']}")
    print(f"    - Early indicators: {len(report_result['report_final']['early_indicators']['indicators'])}")

    # Validate final report
    is_valid, errors = validator_schema.validate_report_final(analysis_internal)
    if not is_valid:
        print(f"  [FAIL] Report validation failed: {errors}")
        return False

    # Step 7: Persist to database
    print("\n[STEP 7] Persisting to Database...")
    db_manager.save_analysis(analysis_id, analysis_internal)
    db_manager.add_audit_entry(analysis_id, "pipeline_completed", "test_system", "End-to-end test completed")
    print(f"  [OK] Analysis persisted to database")

    # Step 8: Retrieve and verify
    print("\n[STEP 8] Verifying retrieval...")
    retrieved = db_manager.get_analysis(analysis_id)
    audit_trail = db_manager.get_audit_trail(analysis_id)
    print(f"  [OK] Analysis retrieved from database")
    print(f"    - Status: {retrieved['metadata']['status']}")
    print(f"    - Audit trail entries: {len(audit_trail)}")

    # Step 9: Generate stats
    print("\n[STEP 9] Database Statistics...")
    stats = db_manager.get_stats()
    print(f"  [OK] Database stats:")
    print(f"    - Total analyses: {stats['total_analyses']}")
    print(f"    - By status: {stats['by_status']}")

    # Step 10: Show markdown report
    print("\n[STEP 10] Markdown Report (excerpt):")
    print("-" * 60)
    print(report_result['markdown'][:500] + "...")
    print("-" * 60)

    print("\n" + "=" * 60)
    print("[SUCCESS] END-TO-END TEST COMPLETED SUCCESSFULLY")
    print("=" * 60)
    print(f"\nAnalysis Summary:")
    print(f"  - Company: {analysis_internal['metadata']['company_name']}")
    print(f"  - Status: {analysis_internal['metadata']['status']}")
    print(f"  - Overall Score: {analysis_internal['phase1_analysis']['scores']['overall']['score']}/10")
    print(f"  - Grade: {analysis_internal['phase1_analysis']['scores']['overall']['grade']}")
    print(f"  - Investment Decision: {analysis_internal['phase2_validations']['investment_decision']}")
    print(f"  - Recommendation: {analysis_internal['report_final']['executive_summary']['key_recommendation']}")

    return True


if __name__ == "__main__":
    import sys
    success = test_full_pipeline()
    sys.exit(0 if success else 1)
