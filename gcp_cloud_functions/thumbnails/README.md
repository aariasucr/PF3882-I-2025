# Deployar en GCP

```bash
gcloud functions deploy crear_thumbnail \
  --runtime python311 \
  --trigger-event google.storage.object.finalize \
  --trigger-resource pf3882_thumbnails \
  --entry-point crear_thumbnail \
  --region us-central1 \
  --gen2 \
  --project <id del proyecto en GCP>
```
