FROM python:3.12-slim

# Avoid writing .pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Collect static files for Whitenoise
RUN python manage.py collectstatic --noinput

# Set executable permissions on entrypoint
RUN chmod +x /app/entrypoint.sh

# Create a non-privileged user and switch to it
RUN useradd -U -d /app django && chown -R django:django /app

USER django

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]

CMD ["gunicorn", "grainlab.wsgi:application", "--bind", "0.0.0.0:8000", "--timeout", "605"]
