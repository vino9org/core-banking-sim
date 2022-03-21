FROM python:3.9-slim-buster

RUN apt-get -qq update \
    && apt-get install -y --no-install-recommends \
        file \
        g++ \
        libffi-dev

COPY requirements.txt .
RUN pip install --root="/install" -r requirements.txt

COPY main.py core_banking/ seed.csv /

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
