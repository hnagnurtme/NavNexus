"""
FastAPI Health Check Endpoint
=============================

Simple health check API for monitoring service status.
Provides endpoints to check:
- API health status
- RabbitMQ connection
- Neo4j connection
- Firebase connection
"""

import os
from datetime import datetime
from typing import Dict, Any
from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("HealthCheckAPI")

# Initialize FastAPI app
app = FastAPI(
    title="RabbitMQ Worker Health Check API",
    description="Health check endpoints for monitoring service status",
    version="1.0.0"
)


@app.get("/", tags=["Health"])
async def root():
    """Root endpoint"""
    return {
        "service": "RabbitMQ Worker Health Check API",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Basic health check endpoint
    Returns 200 OK if service is running
    """
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "status": "healthy",
            "service": "rabbitmq-worker",
            "timestamp": datetime.now().isoformat(),
            "uptime": "running"
        }
    )


@app.get("/health/detailed", tags=["Health"])
async def detailed_health_check():
    """
    Detailed health check with connection tests
    Tests connectivity to RabbitMQ, Neo4j, and Firebase
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "checks": {
            "api": {"status": "up"},
            "rabbitmq": {"status": "unknown", "message": "Not tested"},
            "neo4j": {"status": "unknown", "message": "Not tested"},
            "firebase": {"status": "unknown", "message": "Not tested"}
        }
    }

    overall_healthy = True

    # Check RabbitMQ
    try:
        from src.rabbitmq_client import RabbitMQClient

        rabbitmq_config = {
            "Host": os.getenv("RABBITMQ_HOST", "chameleon-01.lmq.cloudamqp.com"),
            "Username": os.getenv("RABBITMQ_USERNAME", "odgfvgev"),
            "Password": os.getenv("RABBITMQ_PASSWORD", "ElA8Lhgv15r8Y0IR6n0S5bMLxGRmUmgg"),
            "VirtualHost": os.getenv("RABBITMQ_VHOST", "odgfvgev")
        }

        client = RabbitMQClient(rabbitmq_config)
        client.connect()
        health_status["checks"]["rabbitmq"] = {
            "status": "up",
            "message": "Connected successfully"
        }
        client.close()
    except Exception as e:
        health_status["checks"]["rabbitmq"] = {
            "status": "down",
            "message": str(e)
        }
        overall_healthy = False

    # Check Neo4j
    try:
        from neo4j import GraphDatabase

        neo4j_url = os.getenv("NEO4J_URL", "neo4j+s://daa013e6.databases.neo4j.io")
        neo4j_user = os.getenv("NEO4J_USER", "neo4j")
        neo4j_password = os.getenv("NEO4J_PASSWORD", "DTG0IyhifivaD2GwRoyIz4VPapRF0JdjoVsMfT9ggiY")

        driver = GraphDatabase.driver(neo4j_url, auth=(neo4j_user, neo4j_password))
        driver.verify_connectivity()
        health_status["checks"]["neo4j"] = {
            "status": "up",
            "message": "Connected successfully"
        }
        driver.close()
    except Exception as e:
        health_status["checks"]["neo4j"] = {
            "status": "down",
            "message": str(e)
        }
        overall_healthy = False

    # Check Firebase
    try:
        from src.handler.firebase import FirebaseClient

        firebase_service_account = os.getenv("FIREBASE_SERVICE_ACCOUNT", "serviceAccountKey.json")
        firebase_database_url = os.getenv("FIREBASE_DATABASE_URL", "https://navnexus-default-rtdb.firebaseio.com/")

        firebase_client = FirebaseClient(firebase_service_account, firebase_database_url)
        health_status["checks"]["firebase"] = {
            "status": "up",
            "message": "Connected successfully"
        }
    except Exception as e:
        health_status["checks"]["firebase"] = {
            "status": "down",
            "message": str(e)
        }
        overall_healthy = False

    # Set overall status
    if not overall_healthy:
        health_status["status"] = "degraded"

    response_status = status.HTTP_200_OK if overall_healthy else status.HTTP_503_SERVICE_UNAVAILABLE

    return JSONResponse(
        status_code=response_status,
        content=health_status
    )


@app.get("/ping", tags=["Health"])
async def ping():
    """Simple ping endpoint"""
    return {"message": "pong", "timestamp": datetime.now().isoformat()}


@app.get("/readiness", tags=["Health"])
async def readiness_check():
    """
    Kubernetes readiness probe
    Returns 200 if service is ready to accept traffic
    """
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "ready": True,
            "timestamp": datetime.now().isoformat()
        }
    )


@app.get("/liveness", tags=["Health"])
async def liveness_check():
    """
    Kubernetes liveness probe
    Returns 200 if service is alive
    """
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "alive": True,
            "timestamp": datetime.now().isoformat()
        }
    )


if __name__ == "__main__":
    import uvicorn

    # Render provides PORT env variable, otherwise use HEALTHCHECK_PORT or default 8000
    port = int(os.getenv("PORT", os.getenv("HEALTHCHECK_PORT", "8000")))
    host = os.getenv("HEALTHCHECK_HOST", "0.0.0.0")

    logger.info(f"Starting Health Check API on {host}:{port}")

    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )
