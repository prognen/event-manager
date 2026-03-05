FROM python:3.13-slim

WORKDIR /app

COPY mock_server/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY mock_server /app

EXPOSE 8090

CMD ["uvicorn", "external_service_mock:app", "--host", "0.0.0.0", "--port", "8090"]
