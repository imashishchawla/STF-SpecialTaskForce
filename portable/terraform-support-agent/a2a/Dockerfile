# Terraform Support Agent — A2A server container image
#
# Base image: Red Hat UBI 9 minimal Python 3.11 (IBM security policy)
# Non-root user required (IBM security policy)
#
# Build:
#   git submodule update --init --recursive
#   docker build -t terraform-support-agent:latest .
#
# Run:
#   docker run --env-file .env -p 8080:8080 terraform-support-agent:latest

FROM registry.redhat.io/ubi9/python-311-minimal:latest

# ── System packages ────────────────────────────────────────────────────────────
# git is required to initialise the aicoe-agent-utils submodule inside the image
USER root
RUN microdnf install -y git && microdnf clean all

# ── Create non-root user ───────────────────────────────────────────────────────
RUN useradd -m -u 1001 agentuser

# ── Working directory ──────────────────────────────────────────────────────────
WORKDIR /app

# ── Copy submodule first so the editable install resolves correctly ────────────
COPY lib/aicoe-agent-utils ./lib/aicoe-agent-utils

# ── Install dependencies ───────────────────────────────────────────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Copy application source ────────────────────────────────────────────────────
COPY --chown=agentuser:agentuser config.py terraform_agent.py a2a_factory.py main.py ./

# Copy the coordinator prompt (needed at runtime by terraform_agent.py)
COPY --chown=agentuser:agentuser ../export/agents/coordinator.md /app/export/agents/coordinator.md

# ── Drop to non-root ───────────────────────────────────────────────────────────
USER 1001

# ── Expose port ────────────────────────────────────────────────────────────────
EXPOSE 8080

# ── Start server ───────────────────────────────────────────────────────────────
CMD ["python", "main.py"]
