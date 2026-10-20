# BoxForge -- parametric 3D storage-box generator (Streamlit web UI).
# One-click image for public deployment:  docker build -t boxforge .
#
# Python 3.13: the project is verified on 3.13 and CadQuery's OCP wheels are
# available for it. OCP (OpenCASCADE) is a compiled CAD kernel, so a handful of
# shared X11/OpenGL system libraries must be present at runtime even though we
# never open a window (it links against them for its geometry stack).

FROM python:3.15-slim-bookworm AS runtime

# --- OS runtime libraries required by CadQuery / OCP (OpenCASCADE) ---
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libgl1 \
        libglu1-mesa \
        libx11-6 \
        libxext6 \
        libxrender1 \
        libsm6 \
        libice6 \
        libfontconfig1 \
        libglib2.0-0 \
        libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# --- Python runtime configuration ---
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    # Streamlit hardening (also set in .streamlit/config.toml; env wins so the
    # container is safe even if the config file is ever removed).
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=true \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false \
    STREAMLIT_CLIENT_TOOLBAR_MODE=minimal \
    STREAMLIT_CLIENT_SHOW_ERROR_DETAILS=false

WORKDIR /app

# Install Python deps first so the layer is cached across app-code changes.
COPY requirements.txt ./
RUN pip install -r requirements.txt

# App code (app.py, main.py, box_builder/, config.yaml, .streamlit/).
COPY box_generator/ ./

# Run as an unprivileged user -- never serve a public app as root.
RUN useradd --create-home --uid 10001 appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8501

# Container-native health probe hits Streamlit's built-in health endpoint.
HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8501/_stcore/health', timeout=4).read()==b'ok' else 1)"

CMD ["streamlit", "run", "app.py"]
