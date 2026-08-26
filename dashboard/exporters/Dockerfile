FROM python:3.11-slim
WORKDIR /app/exporters
RUN apt-get update && apt-get install -y --no-install-recommends tshark \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV PCAP_ROOT=/pcaps
ENV TC_ID=TC-05
ENV FLOW_EXPORTER_HOST=0.0.0.0
ENV FLOW_EXPORTER_PORT=8010
EXPOSE 8010
CMD ["python", "pcap_flow_exporter.py"]
