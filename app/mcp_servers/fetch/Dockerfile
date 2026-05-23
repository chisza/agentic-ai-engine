FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir "mcp[cli]" httpx beautifulsoup4

COPY server.py .

EXPOSE 8001

CMD ["python", "server.py"]