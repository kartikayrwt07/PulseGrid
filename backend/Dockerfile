FROM python:3.11-slim

WORKDIR /app

# Install system dependencies needed by scientific Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Generate demo dataset and train ML artifacts at build time for fast startup
ENV SECRET_KEY=build-time-placeholder-secret-key-0000
ENV DEMO_MODE=true
RUN python ml/generate_data.py && python ml/train_and_evaluate.py

EXPOSE 7860

# Support both Hugging Face Spaces (default 7860) and Render ($PORT)
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-7860}"]
