# Speech Flow UI - Self-Service Audio Processing

Simple Streamlit web interface for uploading audio files and downloading processed results.

## Features

- Upload audio files (wav, mp3, m4a, ogg, flac)
- Configure workflow type (full pipeline, transcribe only, lid only, translate only, summarize only)
- Specify source and target languages
- Monitor job status in real-time
- Download results in CSV or Excel format

## Architecture

This is a **stateless UI wrapper** around the Speech Flow API:
- No business logic in the UI
- All processing handled by the API
- Uses REST endpoints for job submission, status checks, and result retrieval

## Running Locally

### Prerequisites
- Python 3.11+
- Speech Flow API running (default: http://localhost:8000)

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py
```

The UI will be available at http://localhost:8502

### Configuration

Set the API endpoint via environment variable:
```bash
export API_BASE_URL=http://localhost:8000
streamlit run app.py
```

## Running with Docker

### Build the image
```bash
docker build -t speechflow-ui:latest .
```

### Run the container
```bash
docker run -p 8502:8502 \
  -e API_BASE_URL=http://localhost:8000 \
  speechflow-ui:latest
```

## Running with Docker Compose

From the project root:
```bash
docker-compose up upload-ui
```

## Usage

1. **Configure Job Settings**
   - Select workflow type
   - Choose target language
   - Specify source language (if required for workflow)

2. **Upload Audio File**
   - Click "Choose an audio file"
   - Select your audio file (wav, mp3, m4a, ogg, flac)
   - Click "Submit Job"

3. **Monitor Progress**
   - View job status and processing steps
   - Click "Refresh Status" to update

4. **Download Results**
   - When job completes, click "Fetch Results"
   - Download as CSV or Excel

## API Endpoints Used

- `POST /jobs` - Create new job and get upload URL
- `POST /jobs/{job_id}/start` - Start job processing
- `GET /jobs/{job_id}` - Get job status
- `GET /jobs/{job_id}/results` - Get job results

## Dependencies

- streamlit: Web interface framework
- pandas: Data handling and CSV export
- openpyxl: Excel export functionality
- requests: HTTP client for API calls

## Project Structure

```
speech-flow-ui/
├── app.py              # Main Streamlit application
├── requirements.txt    # Python dependencies
├── Dockerfile         # Container image definition
└── README.md          # This file
```

## Development

This UI is designed to be simple and maintainable:
- Single file application (app.py)
- No database or state management
- No business logic
- Pure presentation layer

For monitoring and analytics, see the Operations Dashboard in `speech-flow-backend/dashboard/`.
