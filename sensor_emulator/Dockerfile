# Stage 1: The "Builder"
# We use a specific, stable Python version to build our environment
FROM python:3.12-slim as builder

# Set the working directory inside the container
WORKDIR /app

# Copy *only* the requirements file to leverage Docker layer caching
COPY requirements.txt .

# Create a virtual environment and install dependencies into it
RUN python -m venv /opt/venv && \
    . /opt/venv/bin/activate && \
    pip install --no-cache-dir -r requirements.txt

# ---

# Stage 2: The "Final" Image
# Start from a clean, lightweight base image
FROM python:3.12-slim

# Set the working directory
WORKDIR /app

# Copy the virtual environment (with all packages) from the builder stage
COPY --from=builder /opt/venv /opt/venv

# Copy the application code
COPY sensor_emulator.py .

# Add the virtual environment's bin to the system PATH
# This ensures 'python' command uses the venv's python
ENV PATH="/opt/venv/bin:$PATH"

# Command to run when the container starts
CMD ["python", "sensor_emulator.py"]