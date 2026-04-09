FROM python:3.13-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        tesseract-ocr \
        poppler-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.lock requirements.txt ./
RUN python -m pip install --upgrade pip \
    && pip install -r requirements.lock

COPY . ./

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]
