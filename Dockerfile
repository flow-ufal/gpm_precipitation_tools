FROM ghcr.io/osgeo/gdal:ubuntu-small-latest-amd64

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

WORKDIR /code

COPY . /code/

RUN buildDeps='build-essential python3-dev' && \
    apt-get update -y && apt-get install -y $buildDeps --no-install-recommends && \
    apt-get update && apt-get install -y --no-install-recommends python3-pip libpq-dev wait-for-it && \
    rm -rf /var/lib/apt/lists/* && \
    pip install --no-cache-dir -U pip && \
    pip install --no-cache-dir -r requirements_dev.txt && \
    apt-get purge -y --auto-remove $buildDeps
