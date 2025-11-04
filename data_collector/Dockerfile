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

# Copy the application code for this specific service
COPY data_collector.py .

# Add the venv to the PATH
ENV PATH="/opt/venv/bin:$PATH"

# Command to run when the container starts
CMD ["python", "data_collector.py"]