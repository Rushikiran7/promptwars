# ==========================================
# Dockerfile
# ==========================================
# Architectural Choice: Multi-stage build
# Why: A multi-stage build separates the build environment from the runtime environment.
# This reduces the final image size significantly by discarding build tools and caches,
# which leads to faster deployments and reduced attack surface in production (e.g., Cloud Run).

# --- Stage 1: Builder ---
FROM python:3.11-slim as builder

# Set the working directory for the build stage
WORKDIR /app

# Create a virtual environment to isolate dependencies.
# Why: Isolating dependencies in a venv makes it trivial to copy the exact runtime
# environment to the final production stage without messing with system packages.
RUN python -m venv /opt/venv
# Ensure the virtual environment is used
ENV PATH="/opt/venv/bin:$PATH"

# Copy only requirements first to leverage Docker layer caching.
# If dependencies haven't changed, Docker will use the cached layer, speeding up builds.
COPY requirements.txt .

# Install dependencies into the virtual environment
RUN pip install --no-cache-dir -r requirements.txt

# --- Stage 2: Production ---
FROM python:3.11-slim

# Set the working directory for the runtime stage
WORKDIR /app

# Copy the pre-built virtual environment from the builder stage
COPY --from=builder /opt/venv /opt/venv
# Ensure the virtual environment is used in the runtime container
ENV PATH="/opt/venv/bin:$PATH"

# Copy the application code.
# We do this after dependencies are installed to maintain optimal caching.
COPY main.py .
COPY index.html .
COPY backimg ./backimg

# Expose port 8080
# Why: Cloud Run requires the container to listen on the port defined by the PORT environment variable,
# which defaults to 8080.
EXPOSE 8080

# Command to run the FastAPI application.
# Why: We use Uvicorn as the ASGI server. Binding to 0.0.0.0 ensures it's reachable from outside the container.
# --proxy-headers is recommended when running behind a reverse proxy like Google Cloud Run.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080", "--proxy-headers"]
