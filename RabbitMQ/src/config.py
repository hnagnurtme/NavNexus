"""
Configuration module for RabbitMQ worker
Loads environment variables using dotenv
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ============================
# API Keys
# ============================
CLOVA_API_KEY = os.getenv('CLOVA_API_KEY', '')
CLOVA_API_URL = os.getenv('CLOVA_API_URL', 'https://clovastudio.stream.ntruss.com/v3/chat-completions/HCX-005')
CLOVA_EMBEDDING_URL = os.getenv('CLOVA_EMBEDDING_URL', 'https://clovastudio.stream.ntruss.com/testapp/v1/api-tools/embedding/clir-emb-dolphin')

PAPAGO_CLIENT_ID = os.getenv('PAPAGO_CLIENT_ID', '')
PAPAGO_CLIENT_SECRET = os.getenv('PAPAGO_CLIENT_SECRET', '')

# ============================
# Database Configuration
# ============================
NEO4J_URI = os.getenv('NEO4J_URI', os.getenv('NEO4J_URL', 'bolt://localhost:7687'))
NEO4J_USER = os.getenv('NEO4J_USER', 'neo4j')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD', '')

QDRANT_HOST = os.getenv('QDRANT_HOST', 'localhost')
QDRANT_PORT = os.getenv('QDRANT_PORT', '6333')
QDRANT_URL = os.getenv('QDRANT_URL', f'http://{QDRANT_HOST}:{QDRANT_PORT}')
QDRANT_API_KEY = os.getenv('QDRANT_API_KEY', '')

# ============================
# RabbitMQ Configuration
# ============================
RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'chameleon-01.lmq.cloudamqp.com')
RABBITMQ_USERNAME = os.getenv('RABBITMQ_USERNAME', 'odgfvgev')
RABBITMQ_PASSWORD = os.getenv('RABBITMQ_PASSWORD', '')
RABBITMQ_VHOST = os.getenv('RABBITMQ_VHOST', 'odgfvgev')

# ============================
# Firebase Configuration
# ============================
FIREBASE_SERVICE_ACCOUNT = os.getenv('FIREBASE_SERVICE_ACCOUNT', 'serviceAccountKey.json')
FIREBASE_DATABASE_URL = os.getenv('FIREBASE_DATABASE_URL', 'https://navnexus-default-rtdb.firebaseio.com/')

# ============================
# Pipeline Optimization Variables
# ============================
# Semantic merge thresholds for cascading deduplication
SEMANTIC_MERGE_THRESHOLD_VERY_HIGH = float(os.getenv('SEMANTIC_MERGE_THRESHOLD_VERY_HIGH', '0.90'))
SEMANTIC_MERGE_THRESHOLD_HIGH = float(os.getenv('SEMANTIC_MERGE_THRESHOLD_HIGH', '0.80'))
SEMANTIC_MERGE_THRESHOLD_MEDIUM = float(os.getenv('SEMANTIC_MERGE_THRESHOLD_MEDIUM', '0.70'))

# Chunking configuration
CHUNK_SIZE = int(os.getenv('CHUNK_SIZE', '1000'))
OVERLAP = int(os.getenv('OVERLAP', '200'))
MAX_CHUNKS = int(os.getenv('MAX_CHUNKS', '100'))

# Batch processing configuration
BATCH_SIZE = int(os.getenv('BATCH_SIZE', '10'))
EMBEDDING_BATCH_SIZE = int(os.getenv('EMBEDDING_BATCH_SIZE', '50'))

# Compact synthesis configuration
MAX_SYNTHESIS_LENGTH = int(os.getenv('MAX_SYNTHESIS_LENGTH', '100'))
MAX_CHUNK_TEXT_LENGTH = int(os.getenv('MAX_CHUNK_TEXT_LENGTH', '200'))

# Search fallback thresholds
SEARCH_THRESHOLD_HIGH = float(os.getenv('SEARCH_THRESHOLD_HIGH', '0.75'))
SEARCH_THRESHOLD_MEDIUM = float(os.getenv('SEARCH_THRESHOLD_MEDIUM', '0.60'))
SEARCH_THRESHOLD_LOW = float(os.getenv('SEARCH_THRESHOLD_LOW', '0.40'))
