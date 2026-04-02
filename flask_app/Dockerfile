FROM python:3.14

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY flask_app/ ./flask_app
COPY flask_app/migrations/ ./migrations

CMD ["sh", "-c", "flask --app flask_app/app.py db upgrade && python flask_app/app.py"]