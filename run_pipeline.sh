#!/usr/bin/env bash
#SBATCH --job-name=snakemake_orchestrator
#SBATCH --partition=local             # 💡 Matches your local Slurm partition
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G
#SBATCH --time=12:00:00
#SBATCH --output=logs/orchestrator-%j.out

set -euo pipefail

S3_INPUT_PATH="${1}"

# Refresh the 12-hour AWS ECR secure credential lease
aws ecr get-login-password --region us-east-1 | apptainer registry login --username AWS --password-stdin docker://160450754194.dkr.ecr.us-east-1.amazonaws.com

ECR_IMAGE="docker://160450754194.dkr.ecr.us-east-1.amazonaws.com/snakemake-qc-mlops:latest"

export APPTAINERENV_AWS_ACCESS_KEY_ID="${AWS_ACCESS_KEY_ID:-}"
export APPTAINERENV_AWS_SECRET_ACCESS_KEY="${AWS_SECRET_ACCESS_KEY:-}"

# Fire the Orchestrator pointing to your profile
apptainer exec \
    -B /var/run/munge \
    -B /usr/bin/sbatch \
    -B /usr/bin/squeue \
    -B /etc/slurm \
    ${ECR_IMAGE} snakemake \
        --snakefile /pipeline/Snakefile \
        --profile slurm \
        --config input_file="${S3_INPUT_PATH}"
