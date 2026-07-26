"""
Storage Service Module.
Handles image file uploads and storage abstraction.
Supports both local disk storage and Supabase Cloud Storage.
"""
import os
import uuid
import urllib.request
import urllib.error
from werkzeug.utils import secure_filename
from flask import current_app

class StorageService:

    @staticmethod
    def allowed_file(filename):
        """Verifies if the file extension is allowed."""
        if not filename or '.' not in filename:
            return False
        ext = filename.rsplit('.', 1)[1].lower()
        return ext in current_app.config['ALLOWED_EXTENSIONS']

    @staticmethod
    def save_image(file_storage):
        """
        Saves uploaded file to local static storage or Supabase Storage.
        Returns unique filename or public URL.
        """
        if not file_storage or file_storage.filename == '':
            return None

        if not StorageService.allowed_file(file_storage.filename):
            raise ValueError("Invalid image file type. Allowed formats: PNG, JPG, JPEG, GIF, WEBP.")

        # Ensure local upload directory exists
        upload_dir = current_app.config['UPLOAD_FOLDER']
        os.makedirs(upload_dir, exist_ok=True)

        # Sanitize filename and attach unique prefix
        original_filename = secure_filename(file_storage.filename)
        ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else 'jpg'
        unique_filename = f"{uuid.uuid4().hex[:12]}_{original_filename}"
        
        target_path = os.path.join(upload_dir, unique_filename)
        file_storage.save(target_path)

        # Optional Supabase Storage Bucket Upload Hook
        supabase_url = current_app.config.get('SUPABASE_URL')
        supabase_key = current_app.config.get('SUPABASE_KEY')

        if supabase_url and supabase_key:
            try:
                # Attempt bucket upload to Supabase Storage if bucket exists
                bucket_name = 'item-images'
                upload_endpoint = f"{supabase_url}/storage/v1/object/{bucket_name}/{unique_filename}"
                
                with open(target_path, 'rb') as f:
                    file_data = f.read()

                req = urllib.request.Request(
                    upload_endpoint,
                    data=file_data,
                    headers={
                        'Authorization': f'Bearer {supabase_key}',
                        'apiKey': supabase_key,
                        'Content-Type': f'image/{ext}'
                    },
                    method='POST'
                )
                with urllib.request.urlopen(req) as resp:
                    if resp.status in (200, 201):
                        print(f"Uploaded {unique_filename} to Supabase Storage bucket '{bucket_name}'.")
            except Exception as e:
                # Log and fallback gracefully to local storage if bucket not pre-created
                print(f"Supabase Storage Upload Info: {e}. Saved locally to static/uploads.")

        return unique_filename

    @staticmethod
    def delete_image(filename):
        """Removes stored image file if exists."""
        if not filename:
            return
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError:
                pass
