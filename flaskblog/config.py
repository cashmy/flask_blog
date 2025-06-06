import os

class Config:
	# Get the secret key from environment variables
	SECRET_KEY = os.environ.get('SECRET_KEY')

	# --- DYNAMIC DATABASE CONFIGURATION ---
	# This logic checks if the POSTGRES_URL (provided by Vercel) exists.
	# If it exists, we use it. Otherwise, we fall back to a local SQLite database.

	if os.environ.get('POSTGRES_URL'):
			# We are in the Vercel (production) environment
			# Use the Vercel Postgres database and correct the scheme for SQLAlchemy
			SQLALCHEMY_DATABASE_URI = os.environ.get('POSTGRES_URL').replace("postgres://", "postgresql://", 1)
	else:
			# We are in the local environment
			# Fall back to using a local SQLite database named 'site.db'
			SQLALCHEMY_DATABASE_URI = 'sqlite:///site.db'
	
	# --- MAIL CONFIGURATION ---
	MAIL_SERVER = 'smtp.googlemail.com'
	MAIL_PORT = 587
	MAIL_USE_TLS = True
	MAIL_USE_SSL = False
	MAIL_DEFAULT_SENDER = 'cmyers880@gmail.com'
	MAIL_USERNAME = os.environ.get('EMAIL_USER')
	MAIL_PASSWORD = os.environ.get('EMAIL_PASS')