import argparse
import json
import sys
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description="Automated Genomic Quality Gate Validation Engine")
    parser.add_pget = parser.add_argument
    
    # Standard Arguments
    parser.add_argument("--json", required=True, help="Path to input fastp JSON summary report")
    parser.add_argument("--output", required=True, help="Target path for writing the QC verdict report")
    parser.add_argument("--min_q30", type=float, default=85.0, help="Minimum acceptable Q30 percentage")
    parser.add_argument("--min_reads", type=int, default=5000000, help="Minimum required total read count")
    
    # 💡 Your Enterprise Flag: Support soft-failing on biological thresholds
    parser.add_argument(
        "--soft-fail", 
        action="store_true", 
        help="Write FAIL verdict to file but return exit code 0 when thresholds are missed."
    )
    
    args = parser.parse_args()

    # 1. Parse data from fastp JSON report
    try:
        with open(args.json, 'r') as f:
            data = json.load(f)
    except Exception as e:
        print(f"[CRITICAL ERROR] Failed to parse fastp json report: {str(e)}", file=sys.stderr)
        sys.exit(2) # Infrastructure Fault (Exit code 2 ensures the pipeline crashes!)

    # Extract metrics safely from fastp schema
    total_reads = data["summary"]["before_filtering"]["total_reads"]
    q30_rate = data["summary"]["before_filtering"]["q30_rate"] * 100.0 # convert to percentage

    failures = []
    if total_reads < args.min_reads:
        failures.append(f"Low Yield: Total reads count is {total_reads} (Threshold: >={args.min_reads})")
    if q30_rate < args.min_q30:
        failures.append(f"Low Quality: Q30 rate is {q30_rate:.2f}% (Threshold: >={args.min_q30}%)")

    # 2. Defensive Directory Creation (Native Python handling of shadow directories)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # 3. Process the Quality Gate Verdict
    with open(output_path, 'w') as out:
        if failures:
            verdict_msg = f"[QC FAIL] Automatically Quarantined Sample due to: {failures}\n"
            print(verdict_msg)
            out.write(verdict_msg)
            
            # If soft-fail is active, exit with 0 so Snakemake uploads the failure report
            if args.soft_fail:
                sys.exit(0)
            sys.exit(1) # Otherwise hard-fail
            
        else:
            verdict_msg = f"[QC PASS] Sample passed all structural validation parameters (Reads: {total_reads}, Q30: {q30_rate:.2f}%).\n"
            print(verdict_msg)
            out.write(verdict_msg)
            sys.exit(0)

if __name__ == "__main__":
    main()

