# Configuration settings for the Café Face Recognition System
import os

# Base directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CUSTOMER_DIR = os.path.join(BASE_DIR, "customer")
DATABASE_DIR = os.path.join(BASE_DIR, "database")
MODELS_DIR = os.path.join(BASE_DIR, "models")
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

# Camera settings
CAMERA_INDEX = 0
FRAME_WIDTH = 640
FRAME_HEIGHT = 480

# Face recognition settings
FACE_DETECTION_TOLERANCE = 0.6
FACE_ENCODING_MODEL = "large"  # or "small" for faster processing
MAX_FACE_DISTANCE = 0.5

# Database settings
DATABASE_FILE = os.path.join(DATABASE_DIR, "cafe_system.db")

# Recommendation settings
MIN_ORDERS_FOR_RECOMMENDATION = 3
RECOMMENDATION_WEIGHT_FREQUENCY = 0.4
RECOMMENDATION_WEIGHT_RECENCY = 0.3
RECOMMENDATION_WEIGHT_SIMILARITY = 0.3

# Web interface settings
FLASK_HOST = "127.0.0.1"
FLASK_PORT = 5000
FLASK_DEBUG = True

# Create directories if they don't exist
os.makedirs(CUSTOMER_DIR, exist_ok=True)
os.makedirs(DATABASE_DIR, exist_ok=True)
os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(TEMPLATES_DIR, exist_ok=True)
