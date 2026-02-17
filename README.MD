# 🚀 Moneta Backend

This is the official backend repository for backend of Moneta Financial.
This project currently follows a monolith+microservice architecture, where in monolith you have most of the tasks being performed, and microservices take on blocking tasks, optimizing the performance.

This file focuses more on the setup of the whole project. If you are looking to learn more about code's structure, and common practises of using git, please refer to files named `ONBOARDING.MD`, which can be found in every service and the root of the application.

- [Root onboarding](ONBOARDING.MD)
- [Monolith onboarding](monolith/ONBOARDING.MD)
- [Document Service onboarding](document_service/ONBOARDING.MD)

## Development Setup

Before starting the application, visit every service and read what additional setup is neceessary for correct operation:
- [Monolith setup](monolith/README.MD)
- [Document Service setup](document_service/README.MD)

And only after that was done, continue to setup through this file.
### 1. Start Services

```bash
docker-compose up --build
```

### 2. MinIO Setup

#### 2.1 Enable Versioning

```bash
# Point mc at your MinIO
docker-compose exec mc mc alias set localminio http://minio:9000 minioadmin minioadmin

# Create the bucket
docker-compose exec mc mc mb localminio/documents

# Enable versioning on the bucket
docker-compose exec mc mc version enable localminio/documents

# Verify versioning is enabled
docker-compose exec mc mc version info localminio/documents
```

#### 2.2 Enable Events

```bash
# Configure MinIO to send events to RabbitMQ
docker-compose exec mc sh -c '\
  mc alias set localminio http://minio:9000 minioadmin minioadmin && \
  mc admin config set localminio notify_amqp:1 \
    enable="on" \
    url="amqp://rabbitmq:5672" \
    exchange="minio-events" \
    exchangeType="direct" \
    routingKey="document_tasks" \
    format="json" && \
  mc admin service restart localminio && \
  sleep 2 && \
  (mc mb localminio/documents || true) && \
  mc event add localminio/documents arn:minio:sqs::1:amqp --event put \
'

# Verify events are configured
docker-compose exec mc mc event list localminio/documents
```

### 3. Database Migrations

```bash
# Run database migrations for monolith service
docker-compose exec app alembic upgrade head
```

### 4. Access Services

#### Monolith Service

- **API**: http://localhost:8080
- **Docs**: http://localhost:8080/docs
- **Health**: http://localhost:8080/health

#### Document Service

- **API**: http://localhost:8081
- **Docs**: http://localhost:8081/docs
- **Health**: http://localhost:8081/v1/health

#### Supporting Services

- **MinIO Console**: http://localhost:9001 (minioadmin/minioadmin)
- **RabbitMQ Management**: http://localhost:15672 (guest/guest)
- **PostgreSQL**: localhost:5432 (postgres/postgres)
- **MongoDB**: localhost:27017

### 5. Environment Setup

```bash
# Copy environment templates
cp monolith/environment.config.example monolith/.env
cp document_service/environment.config.example document_service/.env

# Generate JWT keys for monolith
cd monolith
mkdir -p app/keys
openssl genrsa -out app/keys/jwt_private.pem 2048
openssl rsa -in app/keys/jwt_private.pem -pubout -out app/keys/jwt_public.pem
```

### 6. Testing

```bash
# Test API endpoints
curl http://localhost:8080/health
curl http://localhost:8081/v1/health
```
