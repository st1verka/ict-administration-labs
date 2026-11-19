import os

from confluent_kafka import KafkaError, KafkaException
from confluent_kafka.admin import AdminClient, NewTopic

topic = os.environ["KAFKA_TOPIC"]
partitions = int(os.environ["KAFKA_TOPIC_PARTITIONS"])
replication_factor = int(os.environ["KAFKA_TOPIC_REPLICATION_FACTOR"])

admin = AdminClient({
    "bootstrap.servers": os.environ["KAFKA_BOOTSTRAP_SERVERS"],
})

result = admin.create_topics(
    [NewTopic(topic, partitions, replication_factor)],
    operation_timeout=15,
    request_timeout=25,
)

try:
    result[topic].result()
except KafkaException as exc:
    if exc.args[0].code() != KafkaError.TOPIC_ALREADY_EXISTS:
        raise

metadata = admin.list_topics(timeout=10).topics.get(topic)
if metadata is None or metadata.error is not None:
    raise RuntimeError(f"Не удалось прочитать метаданные топика {topic}")

print(f"Топик {topic} готов. Партиций: {len(metadata.partitions)}")
