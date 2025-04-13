# Use miniconda3 as base image with a specific version tag for reproducibility
FROM continuumio/miniconda3:23.10.0-1

# Set working directory
WORKDIR /app

# Copy only the environment files first to leverage caching
COPY environment.yml .

# Create conda environment
RUN conda env create -f environment.yml && \
    conda clean -afy  # Clean conda cache to reduce image size

# Make RUN commands use the new environment
SHELL ["conda", "run", "-n", "file-server", "/bin/bash", "-c"]

# Install only necessary system packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/* && \
    apt-get clean

# Copy application code
COPY . .

# Expose port (Render will override this with their own port)
EXPOSE 8000

# Health check for zero-downtime deploys
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Use exec form of CMD for better signal handling
CMD ["conda", "run", "--no-capture-output", "-n", "file-server", \
    "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"] 