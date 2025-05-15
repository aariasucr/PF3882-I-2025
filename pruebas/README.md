# Pasos

## 1. Levantar la base de datos

```bash
docker compose up -d
```

## 2. Levantar el API en Flask

```bash
python app.py
```

## 3. Crear datos de prueba

```bash
python crear_datos.py
```

Nota: no es necesario tener el API arriba para crear los datos de prueba, pero si es necesario regenerarlos cada vez que se levente el API.

## 4. Ejecutar pruebas

### 4.1. Ejecutar pruebas de unidad en `biz_logic.py`

```bash
PYTHONPATH=$(pwd) pytest tests/test_biz_logic.py
```

### 4.2. Ejecutar pruebas de unidad contra API de Flask

```bash
PYTHONPATH=$(pwd) pytest tests/test_api.py

```

### 4.3. Generar pruebas de contrato con Pact

```bash
PYTHONPATH=$(pwd) pytest tests/test_pact.py -W ignore::PendingDeprecationWarning

```

### 4.4. Validar contratos generados por Pact contra API real

```bash
pact-verifier --provider-base-url=http://localhost:5000 --pact-urls=./pacts/taskconsumer-taskprovider.json
```

**IMPORTANTE**: Para la Tarea # 3 pueden usar pruebas de Pact (4.3/4.4) o las pruebas de unidad contra Flask (4.2). Si usan FastAPI u otro lenguaje para sus tareas, pueden usar el equivalente a 4.2 que tenga el framework de su elección.
