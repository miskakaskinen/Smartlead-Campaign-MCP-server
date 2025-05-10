FROM python:3.12-slim

# Build arguments
ARG PORT=8050

# Set working directory
WORKDIR /app

# Install uv
RUN pip install uv

# Copy the MCP server files
COPY . .

# Install packages
RUN python -m venv .venv
RUN uv pip install -e .

# Expose port for SSE transport
EXPOSE ${PORT}

# Set command to run the MCP server
CMD ["uv", "run", "src/main.py"] 