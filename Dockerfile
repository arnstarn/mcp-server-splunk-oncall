FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src/ src/

RUN pip install --no-cache-dir .

ENV SPLUNK_ONCALL_API_ID=""
ENV SPLUNK_ONCALL_API_KEY=""
ENV SPLUNK_ONCALL_READ_ONLY=""

EXPOSE 8000

ENTRYPOINT ["mcp-server-splunk-oncall"]
CMD ["--transport", "streamable-http", "--host", "0.0.0.0", "--port", "8000"]
