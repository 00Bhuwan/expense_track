FROM python:3.14

WORKDIR /app
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt
COPY fastapi_app/ ./fastapi_app
ENV DATABASE_URL=sqlite:///./test.db

CMD ["uvicorn", "fastapi_app.main:app", "--host", "0.0.0.0", "--port", "8000"]