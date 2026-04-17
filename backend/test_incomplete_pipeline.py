"""Test pipeline with incomplete gold sample (regulatory/commercial pathway unclear)."""
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


def test_incomplete_pipeline():
    """Test pipeline with incomplete sample (regulatory/commercial pathway unclear)."""
    print("=" * 70)
    print("NuBI VC Review v2 - Incomplete Gold Sample Test")
    print("Test: Framework validation for incomplete/unclear commercialization cases")
    print("=" * 70)

    # Setup
    samples_dir = Path(__file__).parent.parent / "samples"
    db_manager = PersistenceManager(":memory:")
    validator_schema = SchemaValidator()
    analyzer = Analyzer()
    validator = Validator()
    reporter = Reporter()

    # Step 1: Load and validate input
    print("\n[STEP 1] Loading BioMeasure (incomplete) input...")
    input_data = load_json(samples_dir / "sample_input_incomplete.json")
    is_valid, errors = validator_schema.validate_input(input_data)
    if not is_valid:
        print(f"  [FAIL] Input validation failed: {errors}")
        return False
    print(f"  [OK] Input validated successfully")
    print(f"    - Company: {input_data['company']['name']}")
    print(f"    - Missing key info: {len(input_data['quality_flags']['missing_key_info'])} items")
    print(f"    - Red flags identified: {len(input_data['quality_flags']['red_flags_already_identified'])} items")

    # Step 2: Run analyzer (Phase 1)
    print("\n[STEP 2] Running Phase 1 Analysis...")
    analysis_internal = analyzer.analyze(input_data)
    analysis_id = analysis_internal['metadata']['analysis_id']
    scores = analysis_internal['phase1_analysis']['scores']
    print(f"  [OK] Phase 1 analysis completed")
    print(f"    - Analysis ID: {analysis_id}")
    print(f"    - Stage 1 (원천기술통제): {scores['stage_1_원천기술통제']['score']}/10")
    print(f"    - Stage 2 (규제통제): {scores['stage_2_규제통제']['score']}/10 [EXPECT LOW]")
    print(f"    - Stage 4 (반복매출): {scores['stage_4_반복매출']['score']}/10 [EXPECT LOW]")
    print(f"    - Overall score: {scores['overall']['score']}/10, Grade: {scores['overall']['grade']} [EXPECT C or lower]")

    # Validate phase1 output
    is_valid, errors = validator_schema.validate_phase1_analysis(analysis_internal)
    if not is_valid:
        print(f"  [FAIL] Phase 1 validation failed: {errors}")
        return False

    # Step 3: Run validator (Phase 2)
    print("\n[STEP 3] Running Phase 2 Validation (FLAG DETECTION)...")
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
    print(f"    - Validator flags: {len(phase2_result['validator_flags'])} [EXPECT ≥5]")

    # Print flag details
    if phase2_result['validator_flags']:
        print(f"\n    Flag Details:")
        for i, flag in enumerate(phase2_result['validator_flags'][:5], 1):
            flag_type = flag.get('type', 'unknown')
            severity = flag.get('severity', 'unknown')
            description = flag.get('description', '')[:60]
            print(f"      {i}. [{flag_type}] ({severity}) {description}...")

    print(f"    - Investment decision: {phase2_result['phase2_validations']['investment_decision']} [EXPECT: conditional/pass]")

    # Step 4-6: Update status → review → report
    print("\n[STEP 4-5] Updating status to VALIDATED → REVIEWED...")
    analysis_internal['metadata']['status'] = "validated"
    analysis_internal['metadata']['status'] = "reviewed"
    analysis_internal['metadata']['reviewer'] = "user:analyst_validation"
    analysis_internal['metadata']['review_timestamp'] = __import__('datetime').datetime.utcnow().isoformat() + "Z"
    print(f"  [OK] Status updated")

    # Step 6: Run reporter (generate final report)
    print("\n[STEP 6] Generating Final Report...")
    report_result = reporter.generate_report(analysis_internal)
    analysis_internal['report_final'] = report_result['report_final']
    analysis_internal['metadata']['status'] = "published"
    print(f"  [OK] Final report generated")
    print(f"    - Recommendation: {report_result['report_final']['executive_summary']['key_recommendation']}")

    # Check Appendix for missing info
    appendix = report_result['report_final'].get('appendix', {})
    missing_info_count = len(appendix.get('missing_info_to_add', []))
    print(f"    - Missing info items in appendix: {missing_info_count} [EXPECT ≥3]")
    if missing_info_count > 0:
        print(f"      Categories: {', '.join([m.get('category', '?') for m in appendix.get('missing_info_to_add', [])[:3]])}")

    # Validate final report
    is_valid, errors = validator_schema.validate_report_final(analysis_internal)
    if not is_valid:
        print(f"  [FAIL] Report validation failed: {errors}")
        return False

    # Step 7-9: Persist and verify
    print("\n[STEP 7-9] Persisting and verifying...")
    db_manager.save_analysis(analysis_id, analysis_internal)
    retrieved = db_manager.get_analysis(analysis_id)
    print(f"  [OK] Analysis persisted and retrieved")
    print(f"    - Status: {retrieved['metadata']['status']}")

    # Summary
    print("\n" + "=" * 70)
    print("[VALIDATION SUMMARY] Incomplete Sample Test")
    print("=" * 70)
    print(f"\n✓ Framework correctly identifies regulatory/commercial gaps:")
    print(f"  - Grade: {scores['overall']['grade']} (expected C or lower)")
    print(f"  - Validator flags: {len(phase2_result['validator_flags'])} (expected ≥5)")
    print(f"  - Missing info in report: {missing_info_count} (expected ≥3)")
    print(f"  - Investment decision: {phase2_result['phase2_validations']['investment_decision']}")

    # Check if results match expectations
    grade = scores['overall']['grade']
    flag_count = len(phase2_result['validator_flags'])
    decision = phase2_result['phase2_validations']['investment_decision']

    all_checks = [
        (grade in ['C', 'D', 'F'], f"Grade {grade} is C or lower"),
        (flag_count >= 5, f"Flag count {flag_count} >= 5"),
        (missing_info_count >= 3, f"Missing info {missing_info_count} >= 3"),
        (decision in ['conditional', 'pass', 'neutral'], f"Decision '{decision}' is not 'buy'")
    ]

    passed = sum(1 for check, label in all_checks if check)
    total = len(all_checks)

    print(f"\nFramework validation checks: {passed}/{total} passed")
    for check, label in all_checks:
        status = "✓" if check else "✗"
        print(f"  {status} {label}")

    print("\n" + "=" * 70)
    if passed == total:
        print("[SUCCESS] INCOMPLETE SAMPLE TEST PASSED")
        print("Framework correctly identifies gaps and conditional risks")
    else:
        print("[PARTIAL] Some expectations not met - review needed")
    print("=" * 70)

    return passed == total


if __name__ == "__main__":
    success = test_incomplete_pipeline()
    sys.exit(0 if success else 1)
