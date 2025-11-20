"""
Configuration module for Knowledge Graph System
Centralized configuration management with validation and documentation
"""

import os
from dotenv import load_dotenv
from typing import Dict, Any, Optional

# Load environment variables from .env file
load_dotenv()

class ConfigValidationError(Exception):
    """Custom exception for configuration validation errors"""
    pass

def validate_required_config() -> Dict[str, Any]:
    """
    Validate all required configuration variables
    
    Returns:
        Dict with validation results and missing variables
    """
    required_configs = {
        'API_KEYS': {
            'CLOVA_API_KEY': os.getenv('CLOVA_API_KEY'),
            'CLOVA_API_URL': os.getenv('CLOVA_API_URL'),
        },
        'DATABASE': {
            'NEO4J_URI': os.getenv('NEO4J_URI'),
            'NEO4J_USER': os.getenv('NEO4J_USER'),
            'NEO4J_PASSWORD': os.getenv('NEO4J_PASSWORD'),
            'QDRANT_HOST': os.getenv('QDRANT_HOST'),
        },
        'RABBITMQ': {
            'RABBITMQ_HOST': os.getenv('RABBITMQ_HOST'),
            'RABBITMQ_USERNAME': os.getenv('RABBITMQ_USERNAME'),
            'RABBITMQ_PASSWORD': os.getenv('RABBITMQ_PASSWORD'),
        }
    }
    
    missing_vars = []
    for category, configs in required_configs.items():
        for key, value in configs.items():
            if not value:
                missing_vars.append(f"{category}.{key}")
    
    return {
        'valid': len(missing_vars) == 0,
        'missing_vars': missing_vars,
        'has_papago': bool(os.getenv('PAPAGO_CLIENT_ID') and os.getenv('PAPAGO_CLIENT_SECRET')),
        'has_firebase': bool(os.getenv('FIREBASE_SERVICE_ACCOUNT') and os.getenv('FIREBASE_DATABASE_URL'))
    }

def get_config_summary() -> Dict[str, Any]:
    """Get configuration summary for logging (without sensitive data)"""
    validation = validate_required_config()
    
    return {
        'validation': validation,
        'api_endpoints': {
            'clova_api': '✓' if os.getenv('CLOVA_API_URL') else '✗',
            'clova_embedding': '✓' if os.getenv('CLOVA_EMBEDDING_URL') else '✗',
            'papago': '✓' if validation['has_papago'] else '✗',
        },
        'databases': {
            'neo4j': '✓' if os.getenv('NEO4J_URI') else '✗',
            'qdrant': '✓' if os.getenv('QDRANT_HOST') else '✗',
            'rabbitmq': '✓' if os.getenv('RABBITMQ_HOST') else '✗',
            'firebase': '✓' if validation['has_firebase'] else '✗',
        },
        'optimization_settings': {
            'chunk_size': CHUNK_SIZE,
            'max_chunks': MAX_CHUNKS,
            'batch_size': BATCH_SIZE,
            'embedding_batch_size': EMBEDDING_BATCH_SIZE,
        }
    }

# ============================
# API Configuration
# ============================

# CLOVA AI Configuration
CLOVA_API_KEY = os.getenv('CLOVA_API_KEY', '')
CLOVA_API_URL = os.getenv('CLOVA_API_URL', '')
CLOVA_EMBEDDING_URL = os.getenv(
    'CLOVA_EMBEDDING_URL', 
    'https://clovastudio.stream.ntruss.com/testapp/v1/api-tools/embedding/clir-emb-dolphin'
)

# Papago Translation Configuration
PAPAGO_CLIENT_ID = os.getenv('PAPAGO_CLIENT_ID', '')
PAPAGO_CLIENT_SECRET = os.getenv('PAPAGO_CLIENT_SECRET', '')

# ============================
# Database Configuration
# ============================

# Neo4j Graph Database
NEO4J_URI = os.getenv('NEO4J_URI', os.getenv('NEO4J_URL', 'bolt://localhost:7687'))
NEO4J_USER = os.getenv('NEO4J_USER', 'neo4j')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD', 'password')
NEO4J_MAX_CONNECTION_LIFETIME = int(os.getenv('NEO4J_MAX_CONNECTION_LIFETIME', '3600'))  # 1 hour

# Qdrant Vector Database
QDRANT_HOST = os.getenv('QDRANT_HOST', 'localhost')
QDRANT_PORT = int(os.getenv('QDRANT_PORT', '6333'))
QDRANT_URL = os.getenv('QDRANT_URL', f'http://{QDRANT_HOST}:{QDRANT_PORT}')
QDRANT_API_KEY = os.getenv('QDRANT_API_KEY', '')
QDRANT_TIMEOUT = int(os.getenv('QDRANT_TIMEOUT', '30'))

# ============================
# Message Queue Configuration
# ============================

# RabbitMQ Configuration
RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'localhost')
RABBITMQ_PORT = int(os.getenv('RABBITMQ_PORT', '5672'))
RABBITMQ_USERNAME = os.getenv('RABBITMQ_USERNAME', 'guest')
RABBITMQ_PASSWORD = os.getenv('RABBITMQ_PASSWORD', 'guest')
RABBITMQ_VHOST = os.getenv('RABBITMQ_VHOST', '/')
RABBITMQ_HEARTBEAT = int(os.getenv('RABBITMQ_HEARTBEAT', '600'))

# Queue Names
RABBITMQ_QUEUE_PDF_JOBS = os.getenv('RABBITMQ_QUEUE_PDF_JOBS', 'pdf_processing_jobs')
RABBITMQ_QUEUE_RESULTS = os.getenv('RABBITMQ_QUEUE_RESULTS', 'processing_results')
RABBITMQ_PREFETCH_COUNT = int(os.getenv('RABBITMQ_PREFETCH_COUNT', '1'))

# ============================
# Firebase Configuration
# ============================

FIREBASE_SERVICE_ACCOUNT = os.getenv('FIREBASE_SERVICE_ACCOUNT', '')
FIREBASE_DATABASE_URL = os.getenv('FIREBASE_DATABASE_URL', '')
FIREBASE_TIMEOUT = int(os.getenv('FIREBASE_TIMEOUT', '30'))

# ============================
# Pipeline Optimization Configuration
# ============================

# Semantic Merge Thresholds for Cascading Deduplication
SEMANTIC_MERGE_THRESHOLD_VERY_HIGH = float(os.getenv('SEMANTIC_MERGE_THRESHOLD_VERY_HIGH', '0.90'))
SEMANTIC_MERGE_THRESHOLD_HIGH = float(os.getenv('SEMANTIC_MERGE_THRESHOLD_HIGH', '0.80'))
SEMANTIC_MERGE_THRESHOLD_MEDIUM = float(os.getenv('SEMANTIC_MERGE_THRESHOLD_MEDIUM', '0.70'))
SEMANTIC_MERGE_THRESHOLD_LOW = float(os.getenv('SEMANTIC_MERGE_THRESHOLD_LOW', '0.60'))

# Chunking Configuration
CHUNK_SIZE = int(os.getenv('CHUNK_SIZE', '2000'))
OVERLAP = int(os.getenv('OVERLAP', '400'))
MAX_CHUNKS = int(os.getenv('MAX_CHUNKS', '100'))
MIN_CHUNK_SIZE = int(os.getenv('MIN_CHUNK_SIZE', '200'))

# Batch Processing Configuration
BATCH_SIZE = int(os.getenv('BATCH_SIZE', '10'))
EMBEDDING_BATCH_SIZE = int(os.getenv('EMBEDDING_BATCH_SIZE', '50'))
QDRANT_BATCH_SIZE = int(os.getenv('QDRANT_BATCH_SIZE', '100'))

# Text Processing Limits
MAX_SYNTHESIS_LENGTH = int(os.getenv('MAX_SYNTHESIS_LENGTH', '150'))
MAX_CHUNK_TEXT_LENGTH = int(os.getenv('MAX_CHUNK_TEXT_LENGTH', '300'))
MAX_PDF_TEXT_EXTRACT = int(os.getenv('MAX_PDF_TEXT_EXTRACT', '5000'))

# Search Configuration
SEARCH_THRESHOLD_HIGH = float(os.getenv('SEARCH_THRESHOLD_HIGH', '0.75'))
SEARCH_THRESHOLD_MEDIUM = float(os.getenv('SEARCH_THRESHOLD_MEDIUM', '0.60'))
SEARCH_THRESHOLD_LOW = float(os.getenv('SEARCH_THRESHOLD_LOW', '0.40'))
SEARCH_DEFAULT_LIMIT = int(os.getenv('SEARCH_DEFAULT_LIMIT', '10'))

# ============================
# Performance & Timeout Configuration
# ============================

# API Timeouts (seconds)
CLOVA_API_TIMEOUT = int(os.getenv('CLOVA_API_TIMEOUT', '60'))
PAPAGO_API_TIMEOUT = int(os.getenv('PAPAGO_API_TIMEOUT', '30'))
PDF_DOWNLOAD_TIMEOUT = int(os.getenv('PDF_DOWNLOAD_TIMEOUT', '45'))

# Retry Configuration
MAX_RETRY_ATTEMPTS = int(os.getenv('MAX_RETRY_ATTEMPTS', '3'))
RETRY_BACKOFF_FACTOR = float(os.getenv('RETRY_BACKOFF_FACTOR', '2.0'))
RETRY_INITIAL_DELAY = float(os.getenv('RETRY_INITIAL_DELAY', '1.0'))

# Processing Limits
MAX_PDF_PAGES = int(os.getenv('MAX_PDF_PAGES', '50'))
MAX_CONCEPTS_PER_NODE = int(os.getenv('MAX_CONCEPTS_PER_NODE', '5'))
MAX_EVIDENCE_PER_NODE = int(os.getenv('MAX_EVIDENCE_PER_NODE', '10'))

# ============================
# Feature Flags
# ============================

# Enable/disable features
FEATURE_TRANSLATION = os.getenv('FEATURE_TRANSLATION', 'true').lower() == 'true'
FEATURE_RESOURCE_DISCOVERY = os.getenv('FEATURE_RESOURCE_DISCOVERY', 'true').lower() == 'true'
FEATURE_SEMANTIC_DEDUPLICATION = os.getenv('FEATURE_SEMANTIC_DEDUPLICATION', 'true').lower() == 'true'
FEATURE_BATCH_PROCESSING = os.getenv('FEATURE_BATCH_PROCESSING', 'true').lower() == 'true'

# Debug and Logging
DEBUG_MODE = os.getenv('DEBUG_MODE', 'false').lower() == 'true'
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
ENABLE_METRICS = os.getenv('ENABLE_METRICS', 'true').lower() == 'true'

# ============================
# Constants
# ============================

# Embedding Dimensions
EMBEDDING_DIMENSION = 384  # Fixed for CLOVA embedding model

# Language Codes
SUPPORTED_LANGUAGES = ['en', 'ko', 'ja', 'zh-cn', 'zh-tw', 'es', 'fr', 'de', 'ru']
DEFAULT_SOURCE_LANGUAGE = 'en'
DEFAULT_TARGET_LANGUAGE = 'en'

# Node Types
NODE_TYPES = ['domain', 'category', 'concept', 'subconcept', 'detail']

# Relationship Types
RELATIONSHIP_TYPES = {
    'domain_to_category': 'HAS_SUBCATEGORY',
    'category_to_concept': 'CONTAINS_CONCEPT',
    'concept_to_subconcept': 'HAS_DETAIL'
}

# ============================
# Configuration Validation
# ============================

def validate_config() -> None:
    """
    Validate configuration and raise ConfigValidationError if invalid
    """
    validation = validate_required_config()
    
    if not validation['valid']:
        missing_str = ', '.join(validation['missing_vars'])
        raise ConfigValidationError(
            f"Missing required configuration variables: {missing_str}\n"
            f"Please check your .env file or environment variables."
        )
    
    # Validate numeric ranges
    if not (0 < CHUNK_SIZE <= 10000):
        raise ConfigValidationError(f"CHUNK_SIZE must be between 1 and 10000, got {CHUNK_SIZE}")
    
    if not (0 <= OVERLAP < CHUNK_SIZE):
        raise ConfigValidationError(f"OVERLAP must be between 0 and CHUNK_SIZE-1, got {OVERLAP}")
    
    if not (0.5 <= SEMANTIC_MERGE_THRESHOLD_VERY_HIGH <= 1.0):
        raise ConfigValidationError(f"SEMANTIC_MERGE_THRESHOLD_VERY_HIGH must be between 0.5 and 1.0, got {SEMANTIC_MERGE_THRESHOLD_VERY_HIGH}")
    
    # Validate URLs
    if CLOVA_API_URL and not CLOVA_API_URL.startswith(('http://', 'https://')):
        raise ConfigValidationError(f"CLOVA_API_URL must be a valid URL, got {CLOVA_API_URL}")

def get_connection_strings() -> Dict[str, str]:
    """
    Get connection strings for logging (without passwords)
    """
    return {
        'neo4j': f"neo4j://{NEO4J_USER}@{NEO4J_URI.split('://')[1] if '://' in NEO4J_URI else NEO4J_URI}",
        'qdrant': QDRANT_URL,
        'rabbitmq': f"amqp://{RABBITMQ_USERNAME}@{RABBITMQ_HOST}:{RABBITMQ_PORT}/{RABBITMQ_VHOST}"
    }

# Validate configuration on import
try:
    validate_config()
    CONFIG_VALID = True
    CONFIG_SUMMARY = get_config_summary()
except ConfigValidationError as e:
    CONFIG_VALID = False
    CONFIG_SUMMARY = {'error': str(e)}
    if DEBUG_MODE:
        print(f"⚠️ Configuration Warning: {e}")

# ============================
# Configuration Export
# ============================

__all__ = [
    # API Configuration
    'CLOVA_API_KEY', 'CLOVA_API_URL', 'CLOVA_EMBEDDING_URL',
    'PAPAGO_CLIENT_ID', 'PAPAGO_CLIENT_SECRET',
    
    # Database Configuration
    'NEO4J_URI', 'NEO4J_USER', 'NEO4J_PASSWORD', 'NEO4J_MAX_CONNECTION_LIFETIME',
    'QDRANT_HOST', 'QDRANT_PORT', 'QDRANT_URL', 'QDRANT_API_KEY', 'QDRANT_TIMEOUT',
    
    # Message Queue Configuration
    'RABBITMQ_HOST', 'RABBITMQ_PORT', 'RABBITMQ_USERNAME', 'RABBITMQ_PASSWORD', 
    'RABBITMQ_VHOST', 'RABBITMQ_HEARTBEAT', 'RABBITMQ_QUEUE_PDF_JOBS', 
    'RABBITMQ_QUEUE_RESULTS', 'RABBITMQ_PREFETCH_COUNT',
    
    # Firebase Configuration
    'FIREBASE_SERVICE_ACCOUNT', 'FIREBASE_DATABASE_URL', 'FIREBASE_TIMEOUT',
    
    # Pipeline Optimization
    'SEMANTIC_MERGE_THRESHOLD_VERY_HIGH', 'SEMANTIC_MERGE_THRESHOLD_HIGH',
    'SEMANTIC_MERGE_THRESHOLD_MEDIUM', 'SEMANTIC_MERGE_THRESHOLD_LOW',
    'CHUNK_SIZE', 'OVERLAP', 'MAX_CHUNKS', 'MIN_CHUNK_SIZE',
    'BATCH_SIZE', 'EMBEDDING_BATCH_SIZE', 'QDRANT_BATCH_SIZE',
    'MAX_SYNTHESIS_LENGTH', 'MAX_CHUNK_TEXT_LENGTH', 'MAX_PDF_TEXT_EXTRACT',
    'SEARCH_THRESHOLD_HIGH', 'SEARCH_THRESHOLD_MEDIUM', 'SEARCH_THRESHOLD_LOW',
    'SEARCH_DEFAULT_LIMIT',
    
    # Performance & Timeouts
    'CLOVA_API_TIMEOUT', 'PAPAGO_API_TIMEOUT', 'PDF_DOWNLOAD_TIMEOUT',
    'MAX_RETRY_ATTEMPTS', 'RETRY_BACKOFF_FACTOR', 'RETRY_INITIAL_DELAY',
    'MAX_PDF_PAGES', 'MAX_CONCEPTS_PER_NODE', 'MAX_EVIDENCE_PER_NODE',
    
    # Feature Flags
    'FEATURE_TRANSLATION', 'FEATURE_RESOURCE_DISCOVERY', 
    'FEATURE_SEMANTIC_DEDUPLICATION', 'FEATURE_BATCH_PROCESSING',
    'DEBUG_MODE', 'LOG_LEVEL', 'ENABLE_METRICS',
    
    # Constants
    'EMBEDDING_DIMENSION', 'SUPPORTED_LANGUAGES', 
    'DEFAULT_SOURCE_LANGUAGE', 'DEFAULT_TARGET_LANGUAGE',
    'NODE_TYPES', 'RELATIONSHIP_TYPES',
    
    # Validation
    'ConfigValidationError', 'validate_required_config', 'get_config_summary',
    'validate_config', 'get_connection_strings', 'CONFIG_VALID', 'CONFIG_SUMMARY'
]