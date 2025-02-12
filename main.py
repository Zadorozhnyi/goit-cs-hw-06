import http.server
import socketserver
import socket
import json
import multiprocessing
from datetime import datetime
from pymongo import MongoClient

# Налаштування серверів
HTTP_PORT = 3000
SOCKET_PORT = 5000
MONGO_URI = "mongodb://mongo:27017/"
DB_NAME = "messages_db"

# Ініціалізація MongoDB
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db["messages"]

# HTTP-сервер (обробка HTML та статичних файлів)
class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.path = "/index.html"
        elif self.path == "/message":
            self.path = "/message.html"
        elif self.path.startswith("/static/"):
            pass  # Обробка стилів та логотипу
        else:
            self.path = "/error.html"
        
        return http.server.SimpleHTTPRequestHandler.do_GET(self)

    def do_POST(self):
        if self.path == "/send":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            message_data = json.loads(post_data)

            # Надсилаємо повідомлення на Socket-сервер
            send_to_socket_server(message_data)

            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "Message sent"}).encode())

# Функція надсилання даних на Socket-сервер
def send_to_socket_server(data):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.sendto(json.dumps(data).encode(), ("localhost", SOCKET_PORT))

# Запуск HTTP-сервера
def start_http_server():
    with socketserver.TCPServer(("0.0.0.0", HTTP_PORT), MyHTTPRequestHandler) as httpd:
        print(f"HTTP сервер працює на порту {HTTP_PORT}")
        httpd.serve_forever()

# Socket-сервер (отримує повідомлення та записує в MongoDB)
def socket_server():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind(("0.0.0.0", SOCKET_PORT))
        print(f"Socket-сервер працює на порту {SOCKET_PORT}")

        while True:
            data, _ = sock.recvfrom(1024)
            message_data = json.loads(data.decode())
            message_data["date"] = datetime.now().isoformat()
            collection.insert_one(message_data)
            print(f"Збережено повідомлення: {message_data}")

# Запуск серверів у **паралельних процесах**
if __name__ == "__main__":
    http_process = multiprocessing.Process(target=start_http_server)
    socket_process = multiprocessing.Process(target=socket_server)

    http_process.start()
    socket_process.start()

    http_process.join()
    socket_process.join()
