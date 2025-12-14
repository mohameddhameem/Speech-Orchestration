FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY speech-flow-ui/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY speech-flow-ui/app.py ./app.py

# Expose Streamlit port
EXPOSE 8502

# Run the Streamlit app
CMD ["streamlit", "run", "app.py", "--server.port=8502", "--server.address=0.0.0.0"]
