# 1. Base on a solid GPU tracking layer
FROM nvcr.io/nvidia/cuda:12.2.0-base-ubuntu22.04

USER root

# 2. Install basic compiler utilities, wget, and system tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    curl \
    ca-certificates \
    bzip2 \
    bash \
    && rm -rf /var/lib/apt/lists/*

# 3. Install Micromamba via direct script injection
# 💡 FIX: This specific API endpoint delivers the raw archive stream that tar expects!
RUN curl -Ls https://mamba.pm | tar -xj -C /usr/bin/ --strip-components=1 micromamba

# 4. Use micromamba to install bioconda packages natively compiled with CUDA/C++ support
RUN micromamba install -y -n base -c conda-forge -c bioconda \
    snakemake \
    snakemake-storage-plugin-s3 \
    snakemake-executor-plugin-slurm \
    pandas \
    samtools \
    fastp \
    && micromamba clean --all --yes

# 5. Lock Environment Path formatting
ENV PATH="/opt/conda/bin:/root/.local/share/mamba/envs/base/bin:${PATH}"

WORKDIR /pipeline

# 6. Copy structural pipeline logic
COPY Snakefile /pipeline/Snakefile
COPY run_pipeline.sh /pipeline/run_pipeline.sh
COPY scripts/ /pipeline/scripts/

RUN chmod +x /pipeline/run_pipeline.sh


