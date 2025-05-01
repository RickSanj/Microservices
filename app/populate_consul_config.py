import consul
import json

def main():
    consul_client = consul.Consul(host='consul-server', port=8500)

    kafka_config = {
        "address": "kafka-server:9092",
        "messages_topic": "messages_topic"
    }

    hazelcast_config = {
        "cluster_name": "hazelcast-server",
        "members": ["hazelcast-server:5701"]
    }

    consul_client.kv.put("kafka/address", kafka_config["address"])
    consul_client.kv.put("kafka/messages_topic", kafka_config["messages_topic"])

    consul_client.kv.put("hazelcast/client/config", json.dumps(hazelcast_config))

    print("Kafka and Hazelcast configurations successfully stored in Consul.")

if __name__ == '__main__':
    main()
