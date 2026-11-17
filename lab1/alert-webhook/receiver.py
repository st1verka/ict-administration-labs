import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class AlertReceiver(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/alerts":
            self.send_error(404)
            return

        try:
            body_size = int(self.headers["Content-Length"])
            if not 0 < body_size <= 1_048_576:
                raise ValueError("Invalid request size")

            payload = json.loads(self.rfile.read(body_size))
            notification = {
                "receiver": payload["receiver"],
                "status": payload["status"],
                "alerts": [alert["labels"]["alertname"] for alert in payload["alerts"]],
            }
        except (KeyError, TypeError, ValueError):
            self.send_error(400, "Invalid alert payload")
            return

        print(json.dumps(notification), flush=True)
        self.send_response(204)
        self.end_headers()


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", 8080), AlertReceiver).serve_forever()
