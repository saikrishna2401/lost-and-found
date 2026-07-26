"""
Database Package Initialization.
Exports the SQLAlchemy database instance used throughout the app.
"""
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
