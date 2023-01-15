
FROM python:3.10-bullseye as builder

run apt-get update && apt-get install -y \
    build-essential
    
COPY requirements.txt .
RUN pip install --root="/install" -r requirements.txt

# runtime
FROM python:3.10-slim-bullseye
LABEL org.opencontainers.image.source https://github.com/vino9org/core-banking-sim
USER 3001:3001


COPY --from=builder /install /
COPY . .

ENV NEW_RELIC_CONFIG_FILE /etc/config/newrelic.ini
CMD ["newrelic-admin", "run-program", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
EXPOSE 8000
