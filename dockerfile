# Use official Python image
FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive
ENV EDGE_VERSION=135.0.3179.54
ENV EDGE_DRIVER_URL="https://msedgedriver.azureedge.net/$EDGE_VERSION/edgedriver_linux64.zip"
ENV USER_DATA_DIR="/tmp/edge_profiles"
ENV DISPLAY=:99

# Create app directory and set working directory
WORKDIR /app

# Install system dependencies in one layer
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    unzip \
    tesseract-ocr \
    tesseract-ocr-eng \
    libtesseract-dev \
    g++ \
    gnupg2 \
    curl \
    iputils-ping \
    dnsutils \
    ca-certificates \
    libx11-6 \
    libxcomposite1 \
    libxdamage1 \
    libnss3 \
    libxcursor1 \
    libxss1 \
    libxrandr2 \
    libasound2 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libpangocairo-1.0-0 \
    libgtk-3-0 \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

# Install Microsoft Edge components
RUN mkdir -p /etc/apt/keyrings && \
    (wget -qO- https://packages.microsoft.com/keys/microsoft.asc || \
     wget -qO- http://packages.microsoft.com/keys/microsoft.asc || \
     sleep 2 && wget -qO- https://packages.microsoft.com/keys/microsoft.asc) | \
    gpg --dearmor > /etc/apt/keyrings/microsoft.gpg && \
    echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/microsoft.gpg] https://packages.microsoft.com/repos/edge stable main" > /etc/apt/sources.list.d/microsoft-edge.list && \
    apt-get update && \
    (apt-get install -y --no-install-recommends microsoft-edge || \
     apt-get install -y --no-install-recommends microsoft-edge-stable) && \
    rm -rf /var/lib/apt/lists/*

# Install matching EdgeDriver
RUN EDGE_VERSION=$(microsoft-edge --version | cut -d " " -f 3) && \
    echo "Edge version: $EDGE_VERSION" && \
    wget -q -O /tmp/msedgedriver.zip "https://msedgedriver.azureedge.net/$EDGE_VERSION/edgedriver_linux64.zip" && \
    unzip -o /tmp/msedgedriver.zip -d /usr/bin/ && \
    rm /tmp/msedgedriver.zip && \
    chmod +x /usr/bin/msedgedriver

# Create profile directory with proper permissions
RUN mkdir -p $USER_DATA_DIR && \
    chmod -R 777 $USER_DATA_DIR

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY config/config.yaml ./config/
COPY modules ./modules/
COPY main.py .

# Create and copy entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Cleanup
RUN apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/health', timeout=5)"

# Use the entrypoint script instead of directly running Python
ENTRYPOINT ["/entrypoint.sh"]
