FROM python:3.9-slim-buster

RUN apt-get -qq update \
    && apt-get install -y --no-install-recommends \
        file \
        g++ \
        libffi-dev

COPY requirements.txt .
RUN pip install --root="/install" -r requirements.txt

COPY *.py /

EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]

