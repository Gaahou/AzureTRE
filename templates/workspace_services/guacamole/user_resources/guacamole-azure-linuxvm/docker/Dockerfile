# Docker-based Linux VM for TRE workspace
# Uses linuxserver/webtop for browser-accessible Linux desktop

FROM lscr.io/linuxserver/webtop:ubuntu-xfce

# Labels for workspace integration
LABEL tre.workspace.id="${WORKSPACE_ID}" \
      tre.resource.type="linuxvm" \
      tre.resource.id="${VM_ID}"

# Environment variables
ENV PUID=1000 \
    PGID=1000 \
    TZ=Etc/UTC \
    TITLE="TRE Linux VM"

# Install additional tools commonly needed in research environments
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    r-base \
    git \
    curl \
    wget \
    vim \
    nano \
    htop \
    tree \
    jq \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create workspace mount point
RUN mkdir -p /workspace && \
    chown -R abc:abc /workspace

# Volume for persistent data
VOLUME ["/workspace", "/config"]

# Expose VNC and HTTP ports
EXPOSE 3000 3001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=60s \
    CMD curl -f http://localhost:3000/ || exit 1

# Use the base image's entrypoint
ENTRYPOINT ["/init"]