FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY opencti_mcp/ ./opencti_mcp/

EXPOSE 8000

CMD ["python", "-m", "opencti_mcp.server", "--transport", "streamable-http", "--host", "0.0.0.0", "--port", "8000", "--stateless-http"]
