# Stage 1: The "Builder"
FROM python:3.12-slim AS builder
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

COPY sensor_emulator/sensor_emulator.py .

ENV PATH="/opt/venv/bin:$PATH"
CMD ["python", "sensor_emulator.py"]