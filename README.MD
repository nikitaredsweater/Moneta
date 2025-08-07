docker-compose up -d mc
docker-compose exec mc mc alias set localminio http://minio:9000 minioadmin minioadmin
docker-compose exec mc mc admin config set localminio notify_redis:1 \
  enable="on" \
  address="redis:6379" \
  key="bucketevents" \
  format="namespace"
docker-compose exec mc mc admin service restart localminio
docker-compose exec mc mc mb localminio/documents
docker-compose exec mc mc event add localminio/documents \
  arn:minio:sqs::1:redis \
  --event put


<!-- New -->
docker-compose exec mc sh -c "\
  mc alias set localminio http://minio:9000 minioadmin minioadmin && \
  mc admin config set localminio notify_amqp:1 \
    enable=\"on\" \
    url=\"amqp://rabbitmq:5672\" \
    exchange=\"minio-events\" \
    routingKey=\"document_tasks\" \
    format=\"json\" && \
  mc admin service restart localminio && \
  (mc mb localminio/documents || true) && \
  mc event add localminio/documents \
    arn:minio:sqs::1:amqp \
    --event put"

<!-- New v.2 -->
docker-compose exec mc sh -c ' \
  mc alias set localminio http://minio:9000 minioadmin minioadmin && \
  mc admin config set localminio notify_amqp:1 \
    enable="on" \
    url="amqp://rabbitmq:5672" \
    exchange="minio-events" \
    exchangeType="direct" \
    routingKey="document_tasks" \
    format="json" && \
  mc admin service restart localminio && \
  (mc mb localminio/documents || true) && \
  mc event add localminio/documents arn:minio:sqs::1:amqp --event put \
'

<!-- New v/3 -->
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

docker-compose exec mc sh -c '\
  mc alias set localminio http://minio:9000 minioadmin minioadmin && \
  mc admin config set localminio notify_amqp:1 \
    enable=on \
    url=amqp://rabbitmq:5672 \
    exchange=minio-events \
    exchangeType=direct \
    routingKey=document_tasks \
    format=json && \
  mc admin service restart localminio \
'
  
docker-compose exec mc mc event list localminio/documents
docker-compose exec mc mc event remove localminio/documents --force


docker-compose exec mc mc event add localminio/documents arn:minio:sqs::1:amqp --event put
docker-compose exec mc mc admin config get localminio notify_amqp:1

docker-compose exec mc mc admin config get notify_amqp


<!-- ADDITIONAL COMMANDS THAT YOU MIGHT NEED TO RUN -->
docker-compose exec mc mc alias set localminio http://minio:9000 minioadmin minioadmin
docker-compose exec mc mc event add localminio/documents \
  arn:minio:sqs::PRIMARY:amqp --event put

docker-compose exec mc mc admin service restart localminio