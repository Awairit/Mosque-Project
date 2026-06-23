FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update \
  && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gdal-bin \
    libgdal-dev \
    netcat-openbsd \
  && rm -rf /var/lib/apt/lists/*

COPY requirements/production.txt requirements/production.txt
RUN pip install --upgrade pip \
  && pip install -r requirements/production.txt

COPY . .
RUN chmod +x /app/entrypoint.sh

RUN addgroup --system django \
  && adduser --system --ingroup django django \
  && chown -R django:django /app

USER django

EXPOSE 8000
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "60", "--access-logfile", "-", "--error-logfile", "-"]
