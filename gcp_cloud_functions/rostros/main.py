from google.cloud import vision, storage
from PIL import Image, ImageDraw, ImageFont
import tempfile
import os


def detectar_rostros(event, context):
    file_name = event['name']
    bucket_name = event['bucket']

    if file_name.startswith("rostros/"):
        print("🚫 Imagen ya procesada (rostros), omitiendo.")
        return

    gcs_uri = f"gs://{bucket_name}/{file_name}"
    print(f"🔍 Analizando rostros en: {gcs_uri}")

    client = vision.ImageAnnotatorClient()
    image = vision.Image(source=vision.ImageSource(image_uri=gcs_uri))
    response = client.face_detection(image=image)

    if response.error.message:
        raise Exception(response.error.message)

    faces = response.face_annotations
    print(f"➡️ Rostros detectados: {len(faces)}")

    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(file_name)

    with tempfile.NamedTemporaryFile() as temp_img:
        blob.download_to_filename(temp_img.name)

        if len(faces) == 0:
            with Image.open(temp_img.name) as img:
                draw = ImageDraw.Draw(img)
                font = ImageFont.load_default()
                draw.text((10, 10), "FALTA ROSTRO",
                          fill=(255, 0, 0), font=font)

                with tempfile.NamedTemporaryFile(suffix=".jpg") as out_img:
                    img.save(out_img.name)
                    new_blob = bucket.blob(f"rostros/{file_name}")
                    new_blob.upload_from_filename(out_img.name)
                    print(
                        f"✅ Imagen modificada guardada en: rostros/{file_name}")
        else:
            print("✅ Rostros detectados, no se modifica la imagen.")
