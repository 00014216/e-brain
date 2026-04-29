import os
import uuid
import base64
from PIL import Image


ALLOWED = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp'}

SUPABASE_BUCKET = 'memory-images'


def save_upload(file_obj, upload_folder):
    ext = file_obj.filename.rsplit('.', 1)[-1].lower()
    if ext not in ALLOWED:
        return None, 'File type not allowed'

    filename = f'{uuid.uuid4().hex}.{ext}'
    path = os.path.join(upload_folder, filename)
    file_obj.save(path)

    try:
        img = Image.open(path)
        img.verify()
    except Exception:
        os.remove(path)
        return None, 'Invalid image file'

    return path, None


def upload_to_supabase(local_path, filename=None):
    """Upload image to Supabase Storage. Returns public URL or None on failure."""
    try:
        from config import SUPABASE_URL, SUPABASE_SERVICE_KEY
        from supabase import create_client

        if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
            return None

        db = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        ext = local_path.rsplit('.', 1)[-1].lower()
        fname = filename or f'{uuid.uuid4().hex}.{ext}'
        media_map = {
            'jpg': 'image/jpeg', 'jpeg': 'image/jpeg',
            'png': 'image/png', 'gif': 'image/gif',
            'webp': 'image/webp', 'bmp': 'image/bmp',
        }
        content_type = media_map.get(ext, 'image/jpeg')

        with open(local_path, 'rb') as f:
            data = f.read()

        db.storage.from_(SUPABASE_BUCKET).upload(
            fname, data,
            file_options={"content-type": content_type, "upsert": "true"}
        )

        public_url = f"{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_BUCKET}/{fname}"
        return public_url

    except Exception as e:
        print(f'Supabase Storage upload failed: {e}')
        return None


def get_image_base64(image_path):
    ext = image_path.rsplit('.', 1)[-1].lower()
    media_map = {
        'jpg':  'image/jpeg',
        'jpeg': 'image/jpeg',
        'png':  'image/png',
        'gif':  'image/gif',
        'webp': 'image/webp',
        'bmp':  'image/bmp',
    }
    media_type = media_map.get(ext, 'image/jpeg')
    with open(image_path, 'rb') as f:
        data = base64.b64encode(f.read()).decode()
    return data, media_type


def resize_for_storage(image_path, max_dim=1600):
    try:
        img = Image.open(image_path)
        w, h = img.size
        if max(w, h) > max_dim:
            ratio = max_dim / max(w, h)
            img = img.resize((int(w * ratio), int(h * ratio)), Image.LANCZOS)
            img.save(image_path)
    except Exception:
        pass
