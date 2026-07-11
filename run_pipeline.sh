#!/usr/bin/env bash
set -e # Exit immediately if a command exits with a non-zero status

echo "========================================="
echo "Starting Cloud-Native Snakemake Container on AWS Batch"
echo "Target Sample: ${SAMPLE_ID}"
echo "========================================="

# Create a local clean execution environment inside the isolated container
mkdir -p workspace/logs
cd workspace

# Execute Snakemake programmatically, injecting runtime variables as config overrides
# We pass --cores all to utilize the full computing power provisioned by AWS Batch
snakemake \
    --snakefile /pipeline/Snakefile \
    --cores all \
    --verbose \
    --config \
        sample_id="${SAMPLE_ID}" \
        bucket="${S3_BUCKET}" \
        r1_key="${S3_KEY_R1}" \
        r2_key="${S3_KEY_R2}" \
        out_dir="${S3_OUTPUT_DIR}"

echo "========================================="
echo "Pipeline Execution Completed Successfully!"
echo "========================================="
