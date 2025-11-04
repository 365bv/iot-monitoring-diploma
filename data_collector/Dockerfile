# Stage 1: The "Builder"
FROM python:3.12-slim as builder
WORKDIR /app
COPY requirements.txt .

RUN python -m venv /opt/venv && \
    . /opt/venv/bin/activate && \
    pip install --no-cache-dir -r requirements.txt

# ---

# Stage 2: The "Final" Image
FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /opt/venv /opt/venv

COPY data_collector/data_collector.py .

ENV PATH="/opt/venv/bin:$PATH"
CMD ["python", "data_collector.py"]