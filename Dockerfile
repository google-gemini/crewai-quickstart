FROM python:3.11-slim-bookworm

WORKDIR /app

# Install uv
RUN pip install uv

# Copy project config files.
COPY pyproject.toml .
COPY uv.lock .

# Install dependencies using uv. Speeds up runtime.
RUN uv sync --no-dev

COPY src/ .

# Cloud Run requires your application to listen on the PORT environment variable
# which it automatically injects. Default is 8080.
ENV PORT 8080
EXPOSE $PORT

# And run!
CMD ["uv", "run", "uvicorn", "api.service:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1"]
