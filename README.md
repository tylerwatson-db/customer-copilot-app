# 🤖 Customer Copilot App

A clean, modern web application for querying a customer copilot AI agent deployed on Databricks model serving.

## What is this?

This is a streamlined customer copilot application that provides:
- 📝 **Clean web interface** for querying the customer copilot model
- 🔐 **Secure OAuth authentication** through Databricks Apps
- 🚀 **Instant deployment** to Databricks Apps
- ⚡ **Real-time model queries** to the customer copilot agent

## Features

### Customer Copilot Query Interface
- Clean, minimalist web UI
- Real-time query processing
- Response time tracking
- Copy-to-clipboard functionality
- Error handling and display

### Model Serving Integration
- Connects to Databricks model serving endpoint
- OAuth authentication via Databricks SDK
- Automatic token refresh
- Timeout handling and retry logic

## Quick Start

### Deploy to Databricks

```bash
# Clone the repository
git clone https://github.com/tylerwatson-db/customer-copilot-app.git
cd customer-copilot-app

# Run the interactive setup
./setup.sh

# Deploy to Databricks Apps
./deploy.sh
```

### Local Development

```bash
# Install dependencies
uv sync

# Start the development server
./run_app_local.sh
```

## Architecture

```
┌─────────────┐    HTTP/JSON    ┌──────────────────┐    OAuth    ┌─────────────────┐
│   Web UI    │ ◄─────────────► │  FastAPI Server  │ ◄─────────► │ Databricks App  │
│ (React/TS)  │                 │   (Python)       │             │ (Model Serving) │
└─────────────┘                 └──────────────────┘             └─────────────────┘
```

### Components

1. **Frontend** (`client/`): React TypeScript application with:
   - QueryInterface component for user interaction
   - Modern UI with Tailwind CSS
   - Real-time query processing

2. **Backend** (`server/`): FastAPI application with:
   - `/api/query` endpoint for model queries
   - OAuth authentication via Databricks SDK
   - Static file serving for the React app

3. **Model Integration**: Connects to customer copilot model serving endpoint

## Configuration

The app is configured via:
- **`.env.local`**: Databricks authentication and app settings
- **`config.yaml`**: App configuration
- **`app.yaml`**: Databricks App deployment configuration

## Deployment

The app is deployed to Databricks Apps and accessible at:
- **App URL**: `https://customer-copilot-app-475848639457152.aws.databricksapps.com`
- **Workspace URL**: `https://fe-vm-team-nasty-hackathon-ws.cloud.databricks.com/apps/customer-copilot-app`

## API Usage

### Query the Customer Copilot

```bash
POST /api/query
Content-Type: application/json

{
  "query": "Your customer question here"
}
```

### Response Format

```json
{
  "response": "AI response from the customer copilot",
  "metadata": {
    "responseTime": 1.23,
    "timestamp": "2025-08-29T13:18:21Z",
    "endpoint": "https://..."
  },
  "toolsUsed": ["sql", "search", "databricks"],
  "error": null
}
```

## Development

### Project Structure

```
├── client/                 # React TypeScript frontend
│   ├── src/
│   │   ├── components/     # UI components
│   │   │   └── QueryInterface.tsx  # Main query interface
│   │   └── App.tsx         # Main app component
│   └── build/              # Production build
├── server/                 # FastAPI backend
│   ├── routers/            # API routes
│   │   ├── query.py        # Query endpoint
│   │   └── user.py         # User info endpoint
│   └── app.py              # Main FastAPI app
├── deploy.sh               # Deployment script
├── setup.sh                # Setup script
└── app.yaml                # Databricks App config
```

### Available Scripts

- `./setup.sh` - Interactive setup and configuration
- `./deploy.sh` - Deploy to Databricks Apps
- `./run_app_local.sh` - Run locally for development
- `./app_status.sh` - Check app status and get URLs

## License

See LICENSE.md