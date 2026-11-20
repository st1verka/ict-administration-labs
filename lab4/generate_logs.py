import json
from datetime import datetime, timedelta, timezone

now = datetime.now(timezone.utc)

for number in range(1, 11):
    order_id = 1000 + number
    trace_id = f"trace-lab4-{order_id}"
    started_at = now - timedelta(minutes=60 - 5 * number)

    if number in {3, 7}:
        result = ("ERROR", "Payment gateway timeout")
    elif number in {2, 5, 9}:
        result = ("WARN", "Payment queued for retry")
    else:
        result = ("INFO", "Payment confirmed")

    events = [
        ("INFO", "orders-api", "Order received"),
        ("INFO", "order-worker", "Order validated"),
        ("INFO", "payments", "Payment requested"),
        (result[0], "payments", result[1]),
    ]

    for step, (level, service, message) in enumerate(events):
        event = {
            "timestamp": (started_at + timedelta(seconds=step)).isoformat(),
            "level": level,
            "service": service,
            "message": f"{message} for order {order_id}",
            "trace_id": trace_id,
        }
        print(json.dumps({"index": {"_id": f"{order_id}-{step}"}}))
        print(json.dumps(event))
