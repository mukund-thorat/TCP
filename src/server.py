import socket
import threading


class Server:
    # Protocol Flags
    ACK_FLAG = '<ACK>'
    FILE_FLAG = '<FILE>'
    READ_FLAG = '<TEXT>'
    DISCONNECT_FLAG = '<FIN>'
    USER_FLAG = '<USER>'

    clients = []

    def __init__(self, ip, port, buffer_size=1024, decoder_format='utf-8'):
        self.ip = ip
        self.port = port
        self.format = decoder_format
        self.buffer_size = buffer_size

        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((self.ip, self.port))

    def listener(self):
        self.server.listen()
        while True:
            conn, addr = self.server.accept()
            client_thread = threading.Thread(target=self.client_handler, args=(conn, addr))
            client_thread.start()
            print(f"[Session opened]: {threading.active_count() - 1}")

    def client_handler(self, conn: socket.socket, addr):
        print(f'{addr}: Online')
        data = conn.recv(self.buffer_size).decode()
        flag, actual_data = self.flag_extractor(data)
        user_name = actual_data
        self.clients.append((conn, user_name))
        conn.sendall(self.ACK_FLAG.encode())
        print(user_name)
        while True:
            data = conn.recv(self.buffer_size)
            if data:
                try:
                    if data.decode() == self.DISCONNECT_FLAG:
                        print("Connection Closed")
                        for client in self.clients:
                            if client[0] == conn:
                                self.clients.remove(client)
                        conn.close()
                except UnicodeDecodeError:
                    print(conn.getpeername(), data)
                    for client in self.clients:
                        if client[0] == conn:
                            continue
                        client[0].sendall(data)
                print(conn.getpeername(), data)
                for client in self.clients:
                    if client[0] == conn:
                        continue
                    client[0].sendall(data)

    @staticmethod
    def flag_extractor(data: str):
        flag_end_index = data.index('>') + 1
        flag = data[0: flag_end_index]
        actual_data = data[flag_end_index:]
        return flag, actual_data


# Defined Variables
IP = '127.0.0.1'
PORT = 4747
BUFFER_SIZE = 1024
FORMAT = 'utf-8'

if __name__ == '__main__':
    instance = Server(IP, PORT)
    instance.listener()