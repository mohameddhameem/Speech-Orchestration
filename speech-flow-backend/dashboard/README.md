# Speech Flow Dashboard

Operations Dashboard for monitoring and analytics.

## Operations Dashboard (`app.py`)

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

## Running with Docker

```bash
# Operations dashboard (port 8501)
docker-compose up dashboard
```

## Configuration

Environment variables:

- `DATABASE_URL` - PostgreSQL connection string
- `SERVICEBUS_CONNECTION_STRING` - Azure Service Bus connection

## Note

For the **self-service upload UI**, see the separate `speech-flow-ui` project in the repository root.
That UI is a stateless wrapper around the API for uploading audio files and downloading results.
