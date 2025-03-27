# quiero comenzar desde el contenedor con python 3.11 slim
FROM python:3.11-slim

# luego establecer el directorio de trabajo en /app
WORKDIR /app

# copiar todo al directorio de trabajo
COPY . .

# instalar dependencias
RUN pip install --no-cache-dir -r requirements.txt

# exponer el puerto 5000
EXPOSE 5000

# Env
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_ENV=production

# ejecutar la aplicación
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
