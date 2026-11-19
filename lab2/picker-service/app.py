import json
import logging
import os
from collections import deque
from contextlib import asynccontextmanager
from pathlib import Path
from threading import Event, Lock, Thread

from confluent_kafka import Consumer, KafkaException
from fastapi import FastAPI
from fastapi.responses import FileResponse

logger = logging.getLogger("uvicorn.error")
topic = os.getenv("KAFKA_TOPIC", "orders")
group = os.getenv("KAFKA_GROUP_ID", "pickers")
instance = os.getenv("INSTANCE_NAME", "picker-1")
processed_orders = deque(maxlen=100)
orders_lock = Lock()


def consume_orders(stop):
    consumer = Consumer(
        {
            "bootstrap.servers": os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092"),
            "group.id": group,
            "client.id": instance,
            "auto.offset.reset": "earliest",
            "allow.auto.create.topics": False,
            "enable.auto.commit": False,
            "log_level": 3,
        }
    )
    try:
        consumer.subscribe([topic])
        while not stop.is_set():
            message = consumer.poll(0.5)
            if message is None:
                continue
            if message.error():
                logger.warning("Kafka: %s", message.error())
                continue

            order = json.loads(message.value())
            if stop.wait(0.5):
                break

            result = {
                **order,
                "partition": message.partition(),
                "offset": message.offset(),
                "instance": instance,
            }
            with orders_lock:
                processed_orders.appendleft(result)
            try:
                consumer.commit(message=message, asynchronous=False)
            except KafkaException:
                logger.exception("Kafka не подтвердила offset обработанного заказа")
                # Restart from the last committed offset before consuming more orders.
                break
            logger.info("Обработан заказ %s", result)
    finally:
        consumer.close()


@asynccontextmanager
async def lifespan(app):
    stop = Event()
    worker = Thread(target=consume_orders, args=(stop,), daemon=True)
    worker.start()
    try:
        yield
    finally:
        stop.set()
        worker.join(timeout=5)


app = FastAPI(title="Picker Service", lifespan=lifespan)


@app.get("/")
def index():
    return FileResponse(Path(__file__).with_name("index.html"), media_type="text/html")


@app.get("/orders")
def list_orders():
    with orders_lock:
        return {
            "instance": instance,
            "group": group,
            "orders": list(processed_orders),
        }
