#!/bin/bash
echo "+++ Build images..."
docker build -t logging-service -f Dockerfile.logging .
docker build -t facade-service -f Dockerfile.facade .
docker build -t messages-service -f Dockerfile.messages .
echo "+++ Images have been successfully built"

echo "+++ Stop and remove old services..."
docker stop facade-service logging-service1 logging-service2 logging-service3 messages-service1 messages-service2
docker rm facade-service logging-service1 logging-service2 logging-service3 messages-service1 messages-service2
echo "+++ successfully stoped and removed old services"

echo "+++ Starting facade-service..."
docker run -d \
  --name facade-service \
  --network microservices-network \
  -p 8080:8080 \
  facade-service

echo "+++ Starting logging-service1..."
docker run -d \
  --name logging-service1 \
  --network microservices-network \
  -p 8081:8081 \
  logging-service \
  python3 logging_service.py --port 8081

echo "+++ Starting logging-service2..."
docker run -d \
  --name logging-service2 \
  --network microservices-network \
  -p 8082:8081 \
  logging-service \
  python3 logging_service.py --port 8082

echo "+++ Starting logging-service3..."
docker run -d \
  --name logging-service3 \
  --network microservices-network \
  -p 8083:8081 \
  logging-service \
  python3 logging_service.py --port 8083

echo "+++ Starting messages-service1..."
docker run -d \
  --name messages-service1 \
  --network microservices-network \
  -p 8084:8084 \
  messages-service \
  python3 /app/messages_service.py --port 8084

echo "+++ Starting messages-service2..."
docker run -d \
  --name messages-service2 \
  --network microservices-network \
  -p 8085:8085 \
  messages-service \
  python3 /app/messages_service.py --port 8085
