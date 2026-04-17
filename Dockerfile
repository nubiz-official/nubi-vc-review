FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends fonts-noto-cjk && rm -rf /var/lib/apt/lists/*
COPY services/nubi-vc-review/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY services/nubi-vc-review/backend ./backend/
COPY services/nubi-vc-review/streamlit_app ./streamlit_app/
COPY services/nubi-vc-review/.streamlit ./.streamlit/
EXPOSE 8080
CMD streamlit run streamlit_app/app.py \
    --server.port=8080 \
    --server.address=0.0.0.0 \
    --server.headless=true \
    --server.enableWebsocketCompression=false
