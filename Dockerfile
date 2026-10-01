FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install Python dependencies first so this layer is cached between builds.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the project (see .dockerignore: no .env, media, db or staticfiles).
COPY . .

# Bake compressed, hashed static files into the image at build time.
# The throwaway SECRET_KEY is needed because settings require a key whenever
# DEBUG is False; it is never a real secret and is used for this step only.
RUN SECRET_KEY=collectstatic-build-time-key python manage.py collectstatic --noinput

RUN chmod +x entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]
