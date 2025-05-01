#!/bin/bash
docker stop kafka-server hazelcast-server consul-server
docker rm kafka-server hazelcast-server consul-server

docker network create microservices-network

echo "Starting hazelcast..."
docker run -d \
  --name hazelcast-server \
  --network microservices-network \
  hazelcast/hazelcast:latest


echo "Starting Kafka..."
docker run -d \
  --name kafka-server \
  --network microservices-network \
  -e KAFKA_ENABLE_KRAFT=yes \
  -e KAFKA_CFG_NODE_ID=1 \
  -e KAFKA_CFG_PROCESS_ROLES=controller,broker \
  -e KAFKA_CFG_LISTENERS=PLAINTEXT://:9092,CONTROLLER://:9093 \
  -e KAFKA_CFG_ADVERTISED_LISTENERS=PLAINTEXT://kafka-server:9092 \
  -e KAFKA_CFG_CONTROLLER_QUORUM_VOTERS=1@kafka-server:9093 \
  -e KAFKA_CFG_CONTROLLER_LISTENER_NAMES=CONTROLLER \
  -e ALLOW_PLAINTEXT_LISTENER=yes \
  bitnami/kafka:latest
echo "Kafka is now running."

sleep 10

echo "Adding Kafka topic..."
docker run -it --rm \
    --network microservices-network \
    bitnami/kafka:latest kafka-topics.sh --create \
    --bootstrap-server kafka-server:9092 \
    --replication-factor 1 \
    --partitions 3 \
    --topic messages_topic
echo "Kafka topic is now added."

echo "Starting Consul..."
docker run -d \
  --name=consul-server \
  --network microservices-network \
  -p 8500:8500 \
  -p 8600:8600/udp \
  hashicorp/consul agent \
  -server -bootstrap -ui \
  -node=consul-server \
  -client=0.0.0.0
echo "Consul is now running."

sleep 5
