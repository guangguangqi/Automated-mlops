#!/usr/bin/env bash
#SBATCH --job-name=snakemake_master
#SBATCH --partition=compute
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G
#SBATCH --time=12:00:00
#SBATCH --output=logs/orchestrator-%j.out

set -euo pipefail

echo "========================================="
echo "Launching Slurm-Native Snakemake Orchestrator"
echo "Target Sample: ${SAMPLE_ID}"
echo "========================================="

# Establish local scratch work paths inside the shared network workspace
mkdir -p workspace/logs
cd workspace

# Dynamic ECR Target Path Resolution
ECR_IMAGE="docker://YOUR_AWS_ACCOUNT_://amazonaws.com"

# Relay S3 Credentials through container context
export APPTAINERENV_AWS_ACCESS_KEY_ID="${AWS_ACCESS_KEY_ID}"
export APPTAINERENV_AWS_SECRET_ACCESS_KEY="${AWS_SECRET_ACCESS_KEY}"

# Fire Orchestrator Engine using explicit daemon bind mounts (-B)
apptainer exec \
    -B /var/run/munge \
    -B /usr/bin/sbatch \
    -B /usr/bin/squeue \
    -B /etc/slurm \
    ${ECR_IMAGE} snakemake \
        --snakefile /pipeline/Snakefile \
        --executor slurm \
        --jobs 10 \
        --verbose \
        --config \
            sample_id="${SAMPLE_ID}" \
            bucket="${S3_BUCKET}" \
            r1_key="${S3_KEY_R1}" \
            r2_key="${S3_KEY_R2}" \
            out_dir="${S3_OUTPUT_DIR}"
