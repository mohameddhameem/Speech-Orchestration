# Speech Flow Dashboard

This directory contains two Streamlit applications for the Speech Flow system:

## 1. Operations Dashboard (`app.py`)

**Purpose:** Monitoring and analytics for operations teams

**Features:**
- Real-time job statistics and metrics
- Queue depth monitoring
- Performance analysis by processing step
- Error tracking and breakdown
- Language distribution analytics
- Cost tracking
- Historical trends

**How to run:**
```bash
streamlit run app.py
```

Access at: http://localhost:8501

**Requirements:**
- Access to PostgreSQL database
- Access to Service Bus (for queue monitoring)

## 2. Audio Upload UI (`upload_ui.py`)

**Purpose:** Simple interface for users to upload audio files and download results

**Features:**
- Upload audio files (wav, mp3, m4a, ogg, flac)
- Configure workflow type (full pipeline, transcribe only, etc.)
- Monitor job status in real-time
- Download results in CSV or Excel format
- No business logic - purely a UI wrapper around the API

**How to run:**
```bash
# Set the API endpoint (optional, defaults to http://localhost:8000)
export API_BASE_URL=http://localhost:8000

# Run the UI
streamlit run upload_ui.py
```

Access at: http://localhost:8501

**Requirements:**
- Speech Flow API must be running
- No direct database access needed (uses API)

## Running with Docker

Both dashboards can be run using Docker Compose:

```bash
# Operations dashboard (port 8501)
docker-compose up dashboard

# Upload UI (port 8502)
docker-compose up upload-ui
```

## Configuration

Environment variables:

- `API_BASE_URL` - Base URL for Speech Flow API (default: http://localhost:8000)
- `DATABASE_URL` - PostgreSQL connection string (for Operations Dashboard)
- `SERVICEBUS_CONNECTION_STRING` - Azure Service Bus connection (for Operations Dashboard)

## Notes

- The Upload UI is completely stateless and uses the API for all operations
- The Operations Dashboard requires direct database and Service Bus access
- Both UIs can run simultaneously on different ports
