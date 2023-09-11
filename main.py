#https://docs.python.org/3/library/socket.html#
#the socket() function returns a socket object whose methods implement the various socket system calls
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

def chat_server():
    #AF_INET endereços do tipo  IPv4 e SOCK_STREAM é o protocolo TCP a ser utilizado. No caso de utilizar UDP é o SOCK_DGRAM
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    #Bind the socket to address. HOST é '0.0.0.0' ou seja, todas as interfaces de rede disponíveis no computador
    server.bind((HOST, TCP_PORT))
    #Enable a server to accept connections. Setado para 1, já que sabemos que o chat é de 1-1  
    server.listen(1)
    print(f"[*] Chat esta escutando em {HOST}:{TCP_PORT}")

    while True:
        #.accept() Accept a connection. The return value is a pair (conn, address) where:
        #conn is a new socket object usable to send and receive data on the connection, 
        #and address is the address bound to the socket on the other end of the connection.
        conn, addr = server.accept()

        #clients é a lista de clientes conectados
        clients.append(conn)

        while True:
            try:
                #lendo 1024 bytes tranmistidos atraves do socket
                msg = conn.recv(1024).decode('utf-8')
                if not msg:
                    break
                for client in clients:
                    #cliente diferente do servidor 
                    if client != conn:
                        client.sendall(msg.encode('utf-8'))
            except:
                clients.remove(conn)
                conn.close()
                break

#cria e gerencia o servidor web que lida com solicitações HTTP dos clientes. 
def web_server():
    #classe responsavel por lidar com as solicitações HTTP
    class ChatHandler(SimpleHTTPRequestHandler):
        #chamado sempre que uma solicitação do tipo get é chamada
        def do_GET(self):
            if self.path == '/get_messages':
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(message_log).encode('utf-8'))
                return
           

            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            html = """
            <html>
            <head>
                <title>Chat</title>
                <style>
                    #messages {
                        list-style-type: none; 
                    }
                </style>
            </head>
            <body>
                <h1>TCP/IP Web-Chat</h1>
                <form action="" onsubmit="sendMessage(event)">
                    <input type="text" id="messageText" autocomplete="off"/>
                    <button>Send</button>
                </form>
                
                <ul id="messages"></ul>

                <script>
                   
                    var displayMessages = []

                    function appendMessage(message) {
                        var messageElement = document.createElement('li');
                        messageElement.textContent = message;
                        messages.appendChild(messageElement);
                        
                    }
                   
                    function getMessages() {
                        fetch('/get_messages')
                        .then(response => response.json())
                        .then(data => {
                            if (data.length > 0){
                                
                                
                                data.forEach(msg => {
                                    if (msg !== '' && !displayMessages.includes(msg)){
                                        displayMessages.push(msg)
                                        appendMessage(msg)
                                    }
                                });
                            }
                        });
                    }

                    // Poll para 1 secundo
                    setInterval(getMessages, 1000);

                    function sendMessage() {
                       
                        event.preventDefault(); 
                        var input = document.getElementById("messageText");

                        var message = encodeURIComponent(input.value);
                        message = getClientIP() + ": " + message;
                       
                        
                       
                        fetch('/send', {
                            method: 'POST',
                            body: message
                        })
                        
                        input.value = '';
                    }
                    function getClientIP() {
                        return window.location.hostname; 
                    }
                </script>
            </body>
            </html>
            """
            #envia uma resposta HTTP para o cliente em formato JSON
            self.wfile.write(html.encode('utf-8'))

        #chamado sempre que uma solicitação do tipo post é chamada
        def do_POST(self):
            if self.path == '/send':

                #message = self.rfile.read().decode('utf-8')

                length = int(self.headers.get('content-length'))
                message = urllib.parse.unquote(self.rfile.read(length).decode('utf-8'))
                message_log.append(message)  # Adiconado a mensagem no historico
               
                for client in clients:
                    client.sendall(message.encode('utf-8'))

                self.send_response(200)
                self.end_headers()
                
    #criando uma instância do servidor web, e especificando como as solicitações vão ser lidadas
    httpd = HTTPServer((HOST, HTTP_PORT), ChatHandler)
    
    httpd.serve_forever()


# Inicialize o servidor web 
web_server()

# Inicialize o servidor de chat, só um cliente será aceito
chat_server()

