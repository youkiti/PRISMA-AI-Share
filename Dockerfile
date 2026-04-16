FROM python:3.11-slim

LABEL maintainer="Yuki Kataoka"
LABEL description="PRISMA-AI: Automated PRISMA 2020 adherence checking with LLMs"

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application code
COPY . .

ENV PYTHONPATH=/app

# Default: show help
CMD ["python", "-m", "prisma_evaluator.cli.main", "--help"]
