from PIL import Image
import tempfile
import os
from google.cloud import storage

# THUMB_WIDTH = 150
THUMB_WIDTH = 300


def crear_thumbnail(event, context):
    file_name = event['name']
    bucket_name = event['bucket']

    if file_name.startswith("thumbnails/"):
        print("🛑 Archivo ya es un thumbnail, omitiendo.")
        return

    print(f"🖼️ Procesando thumbnail para: {file_name}")

    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(file_name)

    with tempfile.NamedTemporaryFile() as temp_original:
        blob.download_to_filename(temp_original.name)

        with Image.open(temp_original.name) as img:
            img.thumbnail((THUMB_WIDTH, THUMB_WIDTH))
            with tempfile.NamedTemporaryFile(suffix=".jpg") as temp_thumb:
                img.save(temp_thumb.name, "JPEG")

                thumb_blob = bucket.blob(f"thumbnails/{file_name}")
                thumb_blob.upload_from_filename(temp_thumb.name)
                print(f"✅ Thumbnail guardado como: thumbnails/{file_name}")
