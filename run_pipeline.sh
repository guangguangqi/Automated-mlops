#!/usr/bin/env bash
#SBATCH --job-name=snakemake_orchestrator
#SBATCH --partition=compute
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G
#SBATCH --time=12:00:00
#SBATCH --output=logs/orchestrator-%j.out

set -euo pipefail

# Accept S3 file parameters from Lambda trigger
S3_INPUT_PATH="${1}"

# 1. Automatically refresh the 12-hour AWS ECR secure credential token lease
aws ecr get-login-password --region us-east-1 | apptainer registry login --username AWS --password-stdin docker://://amazonaws.com

# 2. Point directly to your new MLOps Container Repository
ECR_IMAGE="docker://://amazonaws.com/snakemake-qc-mlops:latest"

# 3. Relay environment credentials down into the running container context
export APPTAINERENV_AWS_ACCESS_KEY_ID="${AWS_ACCESS_KEY_ID:-}"
export APPTAINERENV_AWS_SECRET_ACCESS_KEY="${AWS_SECRET_ACCESS_KEY:-}"

# 4. Fire the Orchestrator with host cluster daemon mappings (-B)
apptainer exec \
    -B /var/run/munge \
    -B /usr/bin/sbatch \
    -B /usr/bin/squeue \
    -B /etc/slurm \
    ${ECR_IMAGE} snakemake \
        --snakefile /pipeline/Snakefile \
        --executor slurm \
        --jobs 10 \
        --config input_file="${S3_INPUT_PATH}"
