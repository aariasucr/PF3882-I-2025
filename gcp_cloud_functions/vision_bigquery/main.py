from google.cloud import vision
from google.cloud import bigquery
import datetime


BQ_DATASET = "vision_data"
BQ_TABLE = "etiquetas_imagen"


def etiquetas_imagen_vision(event, context):
    file_name = event['name']
    bucket_name = event['bucket']
    gcs_uri = f"gs://{bucket_name}/{file_name}"

    print(f"📸 Analizando imagen: {gcs_uri}")

    # Vision AI
    vision_client = vision.ImageAnnotatorClient()
    image = vision.Image(source=vision.ImageSource(image_uri=gcs_uri))
    response = vision_client.label_detection(image=image)
    labels = response.label_annotations

    if not labels:
        print("❗ No se detectaron etiquetas.")
        return

    # BigQuery
    bq_client = bigquery.Client()
    table_ref = bq_client.dataset(BQ_DATASET).table(BQ_TABLE)

    rows = []
    timestamp = datetime.datetime.utcnow().isoformat()

    for label in labels:
        row = {
            "file_name": file_name,
            "bucket": bucket_name,
            "label": label.description,
            "score": label.score,
            "timestamp": timestamp,
        }
        rows.append(row)

    errors = bq_client.insert_rows_json(table_ref, rows)

    if errors:
        print("❌ Errores al insertar en BigQuery:", errors)
    else:
        print(f"✅ {len(rows)} etiquetas guardadas en BigQuery.")
