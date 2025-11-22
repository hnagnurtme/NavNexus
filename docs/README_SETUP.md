# RabbitMQ Worker - Environment Setup Guide

This guide will help you configure the environment variables needed to run the RabbitMQ worker.

## Quick Start

1. **Copy the template file:**
   ```bash
   cp .env.template .env
   ```

2. **Edit the `.env` file** with your actual credentials

3. **Never commit `.env` file** - it's already in `.gitignore`

## Required Environment Variables

### 🔑 RabbitMQ Configuration

```bash
RABBITMQ_HOST=your-rabbitmq-host.cloudamqp.com
RABBITMQ_USERNAME=your-username
RABBITMQ_PASSWORD=your-password
RABBITMQ_VHOST=your-vhost
QUEUE_NAME=PDF_JOBS_QUEUE
```

**How to get these:**
- Sign up for CloudAMQP (https://www.cloudamqp.com/)
- Create a new instance
- Copy the connection details from the instance dashboard

### 🗄️ Neo4j Configuration

```bash
NEO4J_URL=neo4j+s://your-instance.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-neo4j-password
```

**How to get these:**
- Sign up for Neo4j Aura (https://neo4j.com/cloud/aura/)
- Create a free database instance
- Copy the connection URI and password

### 🤖 CLOVA AI Configuration

```bash
CLOVA_API_KEY=your-clova-api-key
CLOVA_API_URL=https://clovastudio.stream.ntruss.com/v3/chat-completions/HCX-005
```

**How to get these:**
- Sign up for NAVER Cloud Platform (https://www.ncloud.com/)
- Enable CLOVA Studio API
- Create an API key from the console

### 🔍 Qdrant Configuration

```bash
QDRANT_URL=https://your-cluster.cloud.qdrant.io
QDRANT_API_KEY=your-qdrant-api-key
```

**How to get these:**
- Sign up for Qdrant Cloud (https://cloud.qdrant.io/)
- Create a cluster
- Copy the cluster URL and API key

### 🔥 Firebase Configuration

```bash
FIREBASE_DATABASE_URL=https://your-project.firebaseio.com/
FIREBASE_SERVICE_ACCOUNT=serviceAccountKey.json
```

**How to get these:**
- Go to Firebase Console (https://console.firebase.google.com/)
- Create a project
- Enable Realtime Database
- Download service account key:
  - Go to Project Settings → Service Accounts
  - Click "Generate New Private Key"
  - Save as `serviceAccountKey.json` in the RabbitMQ folder

### 📋 Optional: Papago Translation (for Korean/Japanese/Chinese)

```bash
PAPAGO_CLIENT_ID=your-papago-client-id
PAPAGO_CLIENT_SECRET=your-papago-client-secret
```

## File Structure

```
RabbitMQ/
├── .env.template          # Template file (safe to commit)
├── .env                   # Your actual credentials (DO NOT COMMIT)
├── serviceAccountKey.json # Firebase credentials (DO NOT COMMIT)
├── worker.py             # Main worker script
├── healthcheck_api.py    # Health check API
├── seed.py               # Database seeding script
└── ...
```

## Security Best Practices

1. **Never commit sensitive files:**
   - `.env`
   - `serviceAccountKey.json`
   - Any files with real credentials

2. **Use strong passwords:**
   - Generate unique passwords for each service
   - Use a password manager

3. **Rotate credentials regularly:**
   - Change API keys and passwords periodically
   - Revoke unused API keys

4. **Limit access:**
   - Use read-only credentials where possible
   - Implement IP whitelisting if available

## Verifying Your Setup

After configuring your `.env` file, verify your setup:

```bash
# Test connections
python healthcheck_api.py
```

Then visit:
- http://localhost:8000/health/detailed

This will show the status of all service connections.

## Running the Worker

```bash
# Install dependencies first
pip install -r requirements.txt

# Run the worker
python worker.py
```

## Troubleshooting

### Missing environment variables

If you see errors like:
```
❌ Missing required environment variables: NEO4J_URL, NEO4J_PASSWORD
```

Make sure your `.env` file exists and contains all required variables.

### Connection errors

1. **RabbitMQ:** Check if your CloudAMQP instance is running
2. **Neo4j:** Verify the database is not paused (Aura pauses free tier after inactivity)
3. **Firebase:** Ensure the service account key file exists and has correct permissions

### Testing individual connections

You can test connections individually:

```python
# Test Neo4j
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()
driver = GraphDatabase.driver(
    os.getenv("NEO4J_URL"),
    auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD"))
)
driver.verify_connectivity()
print("✅ Neo4j connected!")
```

## Need Help?

- Check the main project README
- Review the example configuration in `.env.template`
- Ensure all services are properly set up and running
