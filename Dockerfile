
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (if any needed for chroma/sqlite)
# Chroma sometimes needs build tools
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
# Create data dir
RUN mkdir -p data

# Expose Streamlit port
EXPOSE 8501

# Command to run the app
CMD ["streamlit", "run", "app/main.py", "--server.address=0.0.0.0"]
