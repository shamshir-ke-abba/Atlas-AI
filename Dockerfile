FROM python:3.11-slim

WORKDIR /app

COPY . .
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "-m", "uvicorn", "interfaces.web.server:app", "--host", "0.0.0.0", "--port", "8000"]
