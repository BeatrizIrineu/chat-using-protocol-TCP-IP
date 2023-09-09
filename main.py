import socket
import threading
from http.server import SimpleHTTPRequestHandler, HTTPServer
import urllib.parse
import json

# Server configuration
HOST = '0.0.0.0'
TCP_PORT = 65432
HTTP_PORT = 8080

clients = []
message_log = []

def handle_client(client_socket):
    while True:
        try:
            msg = client_socket.recv(1024).decode('utf-8')
            if not msg:
                break
            for client in clients:
                if client != client_socket:
                    client.sendall(msg.encode('utf-8'))
        except:
            clients.remove(client_socket)
            client_socket.close()
            break

def chat_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, TCP_PORT))
    server.listen(5)
    print(f"[*] Chat server listening on {HOST}:{TCP_PORT}")

    while True:
        client_socket, addr = server.accept()
        print(f"[*] Accepted connection from {addr[0]}:{addr[1]}")
        clients.append(client_socket)
        client_handler = threading.Thread(target=handle_client, args=(client_socket,))
        client_handler.start()

def web_server():
    class ChatHandler(SimpleHTTPRequestHandler):
        def do_GET(self):
            if self.path == '/get_messages':
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(message_log).encode('utf-8'))
                return
            # ... (rest of the do_GET method)

            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            html = """
            <html>
            <body>
                <h1>Chat Interface</h1>
                <ul id="messages"></ul>
                <input type="text" id="messageInput" placeholder="Type a message...">
                <button onclick="sendMessage()">Send</button>

                <script>
                    function getMessages() {
                        fetch('/get_messages')
                        .then(response => response.json())
                        .then(data => {
                            var messages = document.getElementById('messages');
                            messages.innerHTML = '';  // Clear current messages
                            data.forEach(msg => {
                                var message = document.createElement('li');
                                message.textContent = msg;
                                messages.appendChild(message);
                            });
                        });
                    }

                    // Poll for new messages every 5 seconds
                    setInterval(getMessages, 1000);

                    function sendMessage() {
                        var input = document.getElementById("messageInput");
                        fetch('/send', {
                            method: 'POST',
                            body: encodeURIComponent(input.value)
                        })
                        .then(response => response.text())
                        .then(data => {
                            var messages = document.getElementById('messages');
                            var message = document.createElement('li');
                            message.textContent = data;
                            messages.appendChild(message);
                        });
                        input.value = '';
                    }

                </script>
            </body>
            </html>
            """
            self.wfile.write(html.encode('utf-8'))

        def do_POST(self):
            if self.path == '/send':
                length = int(self.headers.get('content-length'))
                message = urllib.parse.unquote(self.rfile.read(length).decode('utf-8'))
                message_log.append(message)  # Add the message to the log
                for client in clients:
                    client.sendall(message.encode('utf-8'))
                self.send_response(200)
                self.end_headers()

        


    httpd = HTTPServer((HOST, HTTP_PORT), ChatHandler)
    print(f"[*] Web server serving on {HOST}:{HTTP_PORT}")
    httpd.serve_forever()


# Start both servers in separate threads
threading.Thread(target=chat_server).start()
threading.Thread(target=web_server).start()
