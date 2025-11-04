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
COPY dashboard.py .

# Add the venv to the PATH
ENV PATH="/opt/venv/bin:$PATH"

# Expose the port Streamlit runs on (good practice for documentation)
EXPOSE 8501

# Command to run Streamlit
# We MUST use --server.address=0.0.0.0 to allow Docker to expose it
CMD ["streamlit", "run", "dashboard.py", "--server.port=8501", "--server.address=0.0.0.0"]