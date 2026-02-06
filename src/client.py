import os.path
import socket
import threading
import tqdm


class Client:
    # Protocol Flags
    ACK_FLAG = '<ACK>'
    FILE_FLAG = '<FILE>'
    READ_FLAG = '<TEXT>'
    DISCONNECT_FLAG = '<FIN>'
    USER_FLAG = '<USER>'
    disconnected = False
    pause = False

    def __init__(self, ip, port, buffer_size=1024, decoder_format='utf-8'):
        self.ip = ip
        self.port = port
        self.format = decoder_format
        self.buffer_size = buffer_size
        self.user = ''
        self.thread_stop = False
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect((self.ip, self.port))
        print(f'Connected to Server {self.client.getpeername()}')
        self.ack_received = False
        self.cli()  # command line interface

    def cli(self):
        user_name = str(input("Enter your name: "))
        self.client.sendall((self.USER_FLAG+user_name).encode())
        self.user = user_name
        if self.client.recv(self.buffer_size).decode() == self.ACK_FLAG:
            receiver_thread = threading.Thread(target=self.receiver, args=())
            receiver_thread.start()
            print("Register successfully, Thanks!")
            while True:
                try:
                    data_type = int(input("Message(2), File(1), Quit(0): "))

                    match data_type:
                        case 0:
                            self.send_msg("Disconnected")
                            self.disconnected = True
                            self.client.sendall(self.DISCONNECT_FLAG.encode())
                            self.client.close()
                        case 2:
                            print("Type a message | back (_)")
                            while True:
                                msg = str(input("You: "))
                                if msg == '_':
                                    break
                                self.send_msg(msg)
                        case 1:
                            while True:
                                file_path = str(input("Enter a valid file_path or go back (_): "))
                                if file_path == '_':
                                    break
                                self.file_sender(file_path)
                        case _:
                            print("Enter a valid number")

                except ValueError:
                    print("Enter a valid number")
        else:
            print("Something went wrong!")

    def receiver(self):
        while not self.pause:
            if self.disconnected:
                break
            try:
                data = self.client.recv(self.buffer_size).decode()
                if data:
                    flag, actual_data = self.flag_extractor(data)
                    match flag:
                        case self.READ_FLAG:
                            print(actual_data)
                        case self.FILE_FLAG:
                            print("start")
                            self.file_receiver(actual_data)
                            print("end")
                        case self.ACK_FLAG:
                            self.ack_received = True
            except UnicodeDecodeError:
                self.pause = True

    def send_msg(self, msg: str):
        final_msg = self.READ_FLAG + self.user + ': ' + msg
        self.client.sendall(final_msg.encode())

    def file_sender(self, file_path: str):
        file_name = os.path.basename(file_path)
        file_size = str(os.path.getsize(file_name))

        self.client.sendall((self.FILE_FLAG+file_name).encode())
        while not self.ack_received:
            if self.ack_received:
                self.ack_received = False
                self.client.sendall(file_size.encode())
                break
        with open(file_path, 'rb') as file:
            while True:
                byte_data = file.read(self.buffer_size)
                if not byte_data:
                    print("send successfully")
                    break
                self.client.sendall(byte_data)

    def file_receiver(self, actual_data: str):
        file_name = actual_data
        self.client.sendall(self.ACK_FLAG.encode())
        file_size = int(self.client.recv(self.buffer_size).decode())
        progress_bar = tqdm.tqdm(unit='B', unit_scale=True, unit_divisor=1000, total=file_size)
        self.client.sendall(self.ACK_FLAG.encode())
        with open(f'storage/{file_name}', 'wb') as file:
            data_received = 0
            while data_received < file_size:
                data = self.client.recv(self.buffer_size)
                progress_bar.update(len(data))
                print(len(data))
                data_received += len(data)
                file.write(data)
            else:
                print("File received successfully")

    @staticmethod
    def flag_extractor(data: str):
        flag_end_index = data.index('>') + 1
        flag = data[0: flag_end_index]
        actual_data = data[flag_end_index:]
        return flag, actual_data


# Defined Variables
IP = 'localhost'
PORT = 4747
BUFFER_SIZE = 1024
FORMAT = 'utf-8'

if __name__ == '__main__':
    instance = Client(IP, PORT)