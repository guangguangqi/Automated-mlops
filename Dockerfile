# 1. NVIDIA CUDA runtime base image (optimized for precompiled runtime execution)
FROM nvcr.io/nvidia/cuda:12.2.0-runtime-ubuntu22.04

USER root

# Avoid interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Micromamba root prefix definition
ENV MAMBA_ROOT_PREFIX=/opt/conda
ENV PATH="/opt/conda/bin:${PATH}"

# 2. Install basic system utilities
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    curl \
    ca-certificates \
    bzip2 \
    bash \
    && rm -rf /var/lib/apt/lists/*

# 3. Install Micromamba via robust file-download method
RUN curl --fail \
         --location \
         --retry 5 \
         --retry-delay 3 \
         --output /tmp/micromamba.tar.bz2 \
         https://micro.mamba.pm/api/micromamba/linux-64/latest \
    && tar -xjf /tmp/micromamba.tar.bz2 \
         -C /usr/local/bin \
         --strip-components=1 \
         bin/micromamba \
    && rm /tmp/micromamba.tar.bz2 \
    && micromamba --version

# 4. Install bioinformatics and workflow packages
RUN micromamba install -y \
        -n base \
        -c conda-forge \
        -c bioconda \
        --strict-channel-priority \
        python=3.11 \
        snakemake \
        snakemake-storage-plugin-s3 \
        snakemake-executor-plugin-slurm \
        pandas \
        samtools \
        fastp \
    && micromamba clean --all --yes

WORKDIR /pipeline

# 5. Copy pipeline files
COPY Snakefile /pipeline/Snakefile
COPY run_pipeline.sh /pipeline/run_pipeline.sh
COPY scripts/ /pipeline/scripts/

RUN chmod +x /pipeline/run_pipeline.sh

# 6. Validate the installed tools during the build
RUN micromamba run -n base python --version \
    && micromamba run -n base snakemake --version \
    && micromamba run -n base samtools --version | head -n 1 \
    && micromamba run -n base fastp --version

# 7. Execute the pipeline inside the Micromamba environment cleanly
ENTRYPOINT ["micromamba", "run", "--no-capture-output", "-n", "base"]
CMD ["/pipeline/run_pipeline.sh"]
