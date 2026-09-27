# syntax=docker/dockerfile:1.7

FROM python:3.12-slim AS builder

ARG VERSION=0.5.0

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

RUN pip install --upgrade pip build

COPY pyproject.toml README.md LICENSE ./
COPY src/ ./src/

RUN python -m build --wheel --outdir /dist

FROM python:3.12-slim AS runtime

ARG BUILD_DATE
ARG VCS_REF
ARG VERSION=0.5.0

LABEL org.opencontainers.image.title="datasift-py" \
      org.opencontainers.image.description="Zero-dependency data format converter, query engine, and validator" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.created="${BUILD_DATE}" \
      org.opencontainers.image.revision="${VCS_REF}" \
      org.opencontainers.image.source="https://github.com/YOUR_USERNAME/datasift-py" \
      org.opencontainers.image.licenses="MIT"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN groupadd --system --gid 1000 datasift \
    && useradd --system --uid 1000 --gid datasift --create-home datasift

COPY --from=builder /dist/*.whl /tmp/

RUN pip install /tmp/*.whl && rm -f /tmp/*.whl

USER datasift
WORKDIR /home/datasift

ENTRYPOINT ["datasift"]
CMD ["--help"]