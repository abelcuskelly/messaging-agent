# Use Google's Deep Learning Container as base
FROM gcr.io/deeplearning-platform-release/pytorch-gpu.2-1.py310

# Set working directory
WORKDIR /root

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy training code
COPY trainer /root/trainer

# Set Python path
ENV PYTHONPATH="${PYTHONPATH}:/root"

# Entry point for training
ENTRYPOINT ["python", "-m", "trainer.train"]


