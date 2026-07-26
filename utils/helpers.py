"""
Helper Functions Module.
Provides template helper functions and utilities.
"""
from flask import url_for

def get_item_image_url(image_filename):
    """
    Returns public URL for an uploaded image file.
    Provides a default placeholder image if no file was uploaded.
    """
    if image_filename:
        return url_for('static', filename=f'uploads/{image_filename}')
    return url_for('static', filename='images/placeholder.svg')
