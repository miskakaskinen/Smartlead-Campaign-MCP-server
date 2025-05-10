# Smartlead MCP Server

A Model Context Protocol (MCP) server implementation for interacting with the Smartlead API. This server provides tools for managing campaigns, leads, and email accounts through Smartlead's API.

## Overview

This project implements an MCP server that exposes Smartlead API endpoints as tools for AI assistants. It enables AI agents to perform operations like creating, updating, and analyzing email campaigns in Smartlead through a standardized protocol.

## Features

The server provides comprehensive tools for:

### Campaign Management
- List, create, and manage campaigns
- Update campaign schedules and settings
- Save and manage campaign sequences
- Export campaign data and analytics


## Prerequisites

- Python 3.12+
- Docker (recommended for deployment)
- Smartlead API credentials

## Installation

### Using uv

1. Install uv if you don't have it:
   ```bash
   pip install uv
   ```

2. Clone this repository:
   ```bash
   git clone https://github.com/miskakaskinen/Smartlead-Campaign-MCP-server.git
   cd Smartlead-Campaign-MCP-server
   ```

3. Install dependencies:
   ```bash
   uv pip install -e .
   ```

4. Create a `.env` file based on `.env.example`:
   ```bash
   cp .env.example .env
   ```

### Using Docker (Recommended)

1. Build the Docker image:
   ```bash
   docker build -t smartlead/mcp-campaign .
   ```

2. Create a `.env` file and configure your environment variables

## Configuration

Configure the following environment variables in your `.env` file:

| Variable | Description | Required |
|----------|-------------|----------|
| `TRANSPORT` | Transport protocol (sse) | Yes |
| `SMARTLEAD_API_KEY` | Your Smartlead API key | Yes |
| `SMARTLEAD_API_URL` | Smartlead API URL | Yes |
| `HOST` | Host to bind to (default: 0.0.0.0) | Yes |
| `PORT` | Port to listen on (default: 8050) | Yes |
| `LOG_LEVEL` | Logging level (INFO/DEBUG) | Yes |

## Running the Server

### Using uv

#### SSE Transport

```bash
# Set TRANSPORT=sse in .env then:
uv run src/main.py
```

The MCP server will essentially be run as an API endpoint that you can then connect to with config shown below.

### Using Docker with SSE Transport (Recommended)

Run the container with SSE transport:

```bash
docker run -p 8050:8050 --env-file .env smartlead/mcp-campaign
```

### Integration with MCP Clients

Add this configuration to your MCP client (e.g., Claude Desktop, Windsurf):

```json
{
  "mcpServers": {
    "smartlead": {
      "transport": "sse",
      "url": "http://localhost:8050/sse"
    }
  }
}
```

> **Note for n8n users**: Use host.docker.internal instead of localhost since n8n has to reach outside of its own container to the host machine:
> 
> So the full URL in the MCP node would be: http://host.docker.internal:8050/sse

## Available Tools

### Campaign Management
- `list_campaigns`: List all campaigns
- `get_campaign`: Get campaign by ID
- `create_campaign`: Create a new campaign
- `update_campaign_schedule`: Update campaign schedule
- `update_campaign_settings`: Update campaign settings
- `save_campaign_sequence`: Save campaign sequence
- `patch_campaign_status`: Update campaign status
- `get_campaign_analytics`: Get campaign analytics
- `get_campaign_sequence`: Get campaign sequence
- `get_campaigns_by_lead_id`: Get campaigns by lead ID
- `export_campaign_data`: Export campaign data
- `get_campaign_sequence_analytics`: Get sequence analytics

