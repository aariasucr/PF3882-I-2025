from google.cloud import vision, storage
from PIL import Image, ImageFilter
import tempfile
import os


def moderar_imagen(event, context):
    file_name = event['name']
    bucket_name = event['bucket']

    if file_name.startswith("vision/"):
        print("🚫 Imagen ya procesada (vision), omitiendo.")
        return

    gcs_uri = f"gs://{bucket_name}/{file_name}"
    print(f"🔍 Revisando contenido inapropiado en: {gcs_uri}")

    vision_client = vision.ImageAnnotatorClient()
    image = vision.Image(source=vision.ImageSource(image_uri=gcs_uri))
    response = vision_client.safe_search_detection(image=image)

    if response.error.message:
        raise Exception(response.error.message)

    safe = response.safe_search_annotation

    # https://cloud.google.com/php/docs/reference/cloud-vision/latest/V1.Likelihood
    def is_inappropriate(safe):
        print(f"🔍 Resultado del API: {safe}")
        return any([
            safe.adult >= vision.Likelihood.LIKELY,
            safe.violence >= vision.Likelihood.LIKELY,
            safe.racy >= vision.Likelihood.LIKELY,
            safe.medical >= vision.Likelihood.LIKELY
        ])

    inappropriate = is_inappropriate(safe)

    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(file_name)

    with tempfile.NamedTemporaryFile() as temp_img:
        blob.download_to_filename(temp_img.name)

        with Image.open(temp_img.name) as img:
            if inappropriate:
                print("❌ Imagen inapropiada detectada. Aplicando blur.")
                blurred = img.filter(ImageFilter.GaussianBlur(10))
            else:
                print("✅ Imagen es segura. Copiando tal cual.")
                blurred = img

            with tempfile.NamedTemporaryFile(suffix=".jpg") as out_img:
                blurred.save(out_img.name)
                new_blob = bucket.blob(f"vision/{file_name}")
                new_blob.upload_from_filename(out_img.name)
                print(f"📥 Imagen guardada en: vision/{file_name}")
