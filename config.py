import os

class Config:
    # ---------------------------------------------------
    # Secret key for session management
    # ---------------------------------------------------
    SECRET_KEY = os.environ.get('SECRET_KEY', 'change-this-in-production')

    # ---------------------------------------------------
    # Oracle 19c Connection
    # Format: oracle+oracledb://user:pass@host:port/?service_name=SERVICE
    # Update with your actual credentials
    # ---------------------------------------------------
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'oracle+oracledb://gl:gl123@194.1.1.2:1521/?service_name=ORCL'
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }
