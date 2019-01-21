import socket
from time import sleep
from threading import Lock, Thread


def threaded(fn):
    def wrapper(*args, **kwargs):
        t = Thread(target=fn, args=args, kwargs=kwargs)
        t.daemon = True
        t.start()
    return wrapper


class Client:
    def __init__(self, host: str, port: int, username=None):
        self.host = host
        self.port = port
        self.username = username
        self.lock = Lock()
        self.username = input("Username :>>> ") if not username else username

        print("[+] Creating socket...")
        self.sckt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print("[+] Connecting to the server...")
        self.sckt.connect((self.host, self.port))
        print("[?] Server said: \"%s\"" % self.sckt.recv(1024).decode())
        self.sckt.send(b"ACK")
        # Get the listening port
        self.listening_port = int(self.sckt.recv(1024).decode())
        self.sckt.send(b"ACK")
        # Get the sending port
        self.sending_port = int(self.sckt.recv(1024).decode())
        self.sckt.send(b"ACK")
        # Send username to the server
        self.sckt.send(self.username.encode())
        # Close main connection
        self.sckt.close()
        print("[-] Closing connection...")
        print("[§] Listening ", self.listening_port)
        print("[§] Sending ", self.sending_port)

        # print("[?] Server said: \"%s\"" % self.sckt.recv(1024))
        sleep(1)
        self.listening_sckt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listening_sckt.connect((self.host, self.listening_port))
        print(self.listening_sckt.recv(1024).decode())

        self.listening_thread()

        # print("[?] Server said: \"%s\"" % self.sckt.recv(1024))
        sleep(1)
        self.sending_sckt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sending_sckt.connect((self.host, self.sending_port))
        print(self.sending_sckt.recv(1024).decode())
        while True:
            try:
                data = input(">>> ")
                self.sending_sckt.send(data.encode())
                if data == "**END**":
                    break
            except KeyboardInterrupt:
                self.sending_sckt.send(b"**END**")
                break

        self.sending_sckt.close()
        self.listening_sckt.close()

    @threaded
    def listening_thread(self) -> None:
        while True:
            data = self.listening_sckt.recv(1024).decode()
            self.lock.acquire()
            print("\t", data)
            self.lock.release()





def main():
    client = Client("127.0.0.1", 5000)


if __name__ == '__main__':
    main()
