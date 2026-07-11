#!/usr/bin/env bash
#SBATCH --job-name=snakemake_orchestrator
#SBATCH --partition=compute
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G
#SBATCH --time=12:00:00
#SBATCH --output=logs/orchestrator-%j.out

set -euo pipefail

S3_INPUT_PATH="${1}"

aws ecr get-login-password --region us-east-1 | apptainer registry login --username AWS --password-stdin docker://160450754194.dkr.ecr.us-east-1.amazonaws.com

ECR_IMAGE="docker://://amazonaws.com"

export APPTAINERENV_AWS_ACCESS_KEY_ID="${AWS_ACCESS_KEY_ID:-}"
export APPTAINERENV_AWS_SECRET_ACCESS_KEY="${AWS_SECRET_ACCESS_KEY:-}"

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
