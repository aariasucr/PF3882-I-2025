Comandos para levantar el servicio:

1. instalar dependencias: `pip install -r requirements.txt`
2. servidor de desarrollo: `python app.py`
3. servidor de producción: `gunicorn -w 4 -b 0.0.0.0:5000 app:app`
4. construir el contenedor de Docker: `docker-compose build`
5. levantar el contenedor de Docker: `docker-compose up -d`
6. pagina de Swagger --> http://localhost:8080/apidocs/
7. detener el contenedor de Docker: `docker-compose down`
8. ver los logs del contenedor de Docker: `docker-compose logs -f`
