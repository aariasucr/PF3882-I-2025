FROM python:3.11-slim

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

# Flask port
EXPOSE 5000

# Env
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_ENV=production


CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
