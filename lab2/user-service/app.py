import json
import os
from pathlib import Path
from time import monotonic
from uuid import uuid4

from confluent_kafka import KafkaException, Producer
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

app = FastAPI(title="User Service")
topic = os.getenv("KAFKA_TOPIC", "orders")
producer = Producer(
    {
        "bootstrap.servers": os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092"),
        "client.id": os.getenv("INSTANCE_NAME", "user-service"),
        "enable.idempotence": True,
        "message.timeout.ms": 5000,
        "log_level": 3,
    }
)


@app.get("/")
def index():
    return FileResponse(Path(__file__).with_name("index.html"), media_type="text/html")


@app.post("/orders", status_code=201)
def create_order():
    order = {
        "order_id": str(uuid4()),
        "items": ["Футболка", "Рюкзак"],
    }
    delivery = []
    try:
        producer.produce(
            topic,
            key=order["order_id"],
            value=json.dumps(order, ensure_ascii=False).encode(),
            on_delivery=lambda error, message: delivery.append((error, message)),
        )
        deadline = monotonic() + 6
        while not delivery and monotonic() < deadline:
            producer.poll(0.1)
    except (BufferError, KafkaException) as error:
        raise HTTPException(503, "Kafka сейчас недоступна.") from error

    if not delivery or delivery[0][0] is not None:
        raise HTTPException(503, "Kafka не подтвердила запись заказа.")

    _, message = delivery[0]
    return {
        **order,
        "topic": message.topic(),
        "partition": message.partition(),
        "offset": message.offset(),
    }
