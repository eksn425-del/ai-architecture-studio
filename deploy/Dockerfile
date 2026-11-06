FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /srv/kstudio
COPY requirements-cloud.txt .
RUN pip install --no-cache-dir -r requirements-cloud.txt && useradd --uid 10001 --create-home kstudio
COPY cloud/ cloud/
COPY website/ website/
USER 10001:10001
EXPOSE 8920
CMD ["uvicorn","cloud.main:create_app","--factory","--host","0.0.0.0","--port","8920","--workers","1","--proxy-headers","--forwarded-allow-ips","172.31.91.3","--no-access-log"]
