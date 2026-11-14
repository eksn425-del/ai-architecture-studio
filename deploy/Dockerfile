FROM python:3.12-slim
ARG KSTUDIO_BUILD_RELEASE_SHA
LABEL org.opencontainers.image.revision="${KSTUDIO_BUILD_RELEASE_SHA}"
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /srv/kstudio
COPY requirements-cloud.txt .
RUN pip install --no-cache-dir -r requirements-cloud.txt && useradd --uid 10001 --create-home kstudio
COPY cloud/ cloud/
COPY website/ website/
COPY deploy/verify_restore.py deploy/verify_restore.py
RUN printf '%s' "$KSTUDIO_BUILD_RELEASE_SHA" > /srv/kstudio/RELEASE_SHA
USER 10001:10001
EXPOSE 8920
CMD ["uvicorn","cloud.main:create_app","--factory","--host","0.0.0.0","--port","8920","--workers","1","--no-access-log"]
