import socket
import threading
from threading import Condition
from time import sleep
from random import choice


def threaded(fn):
    def wrapper(*args, **kwargs):
        t = threading.Thread(target=fn, args=args, kwargs=kwargs)
        t.daemon = True
        t.start()

    return wrapper


class Client:
    def __init__(self, username, addr, listening_port, sending_port):
        self.username = username
        self.addr = addr
        self.listening_port = listening_port
        self.sending_port = sending_port


class Server:
    def __init__(self, host: str, port: str, servername: str, beg_port=5000, end_port=65535):
        self.host = host
        self.port = port
        self.servername = servername
        self.port_range = list(range(beg_port, end_port))
        # [["msg", ["u1", "u2", ... ], ... ]
        self.msgs = []
        self.condition = Condition()

        if self.port in self.port_range:
            self.port_range.remove(self.port)

        # self.clients = dict()

    def start(self, queue_length=5) -> None:
        # TODO: modify the try's system
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            print("[*] Created socket")
            self.server_socket.bind((self.host, self.port))
            print("[*] Set up socket")
            self.server_socket.listen(queue_length)
            print("[*] Start listening with %d queue length" % queue_length)

            while True:
                conn, addr = self.server_socket.accept()
                conn.send(("Hello from %s" % self.servername).encode())
                print("[+] New connection from %s from port %d" % (addr[0], addr[1]))
                self.check_ACK(conn)
                client_listening_port, client_sending_port = self.pick_ports()
                # Send client's listening port
                conn.send(client_listening_port)
                self.check_ACK(conn)
                # Send client's sending port
                conn.send(client_sending_port)
                self.check_ACK(conn)
                # Get client's username
                username = conn.recv(1024).decode()
                # Close main connection
                conn.close()
                # Create client's threads
                self.client_management(sending_port=client_sending_port, listening_port=client_listening_port, username=username)
        except (OSError, KeyboardInterrupt) as e:
            if e == OSError:
                print("Error on creation..\n\t%s" % str(e))
            else:  # if e == KeyboardInterrupt:
                print(e)
                print("\n[x]Shutting down the server...")
            self.server_socket.close()
        except (AttributeError) as e:
            print("[x]", e)
            self.server_socket.close()

    @threaded
    def client_management(self, sending_port: bytes, listening_port: bytes, username: str) -> None:
        self.create_client_listening_socket(listening_port, username)
        self.create_client_sending_socket(sending_port, username)

    @threaded
    def create_client_listening_socket(self, port: bytes, username: str) -> None:
        print("[+] Creating socket for client's sending on port ", port)
        self.listening_client_sckt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listening_client_sckt.bind((self.host, int(port.decode())))
        self.listening_client_sckt.listen(1)
        list_conn, _ = self.listening_client_sckt.accept()
        list_conn.send(b"Hi 1")
        while True:
            self.condition.acquire()
            if self.msgs:
                for i in range(len(self.msgs)):
                    if username not in self.msgs[i][1]:
                        list_conn.send(self.msgs[i][0].encode())
                        self.msgs[i][1].append(username)
            self.condition.wait()

            self.condition.release()
        list_conn.close()
        #TODO: CLOSE IT

    @threaded
    def create_client_sending_socket(self, port: bytes, username: str) -> None:
        print("[+] Creating socket for client's listening on port ", port)
        self.sending_client_sckt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sending_client_sckt.bind((self.host, int(port.decode())))
        self.sending_client_sckt.listen(1)
        list_conn, _ = self.sending_client_sckt.accept()
        list_conn.send(b"HI 2")

        while True:
            data = list_conn.recv(1024).decode()
            if data == "**END**":
                break
            self.condition.acquire()
            self.msgs.append([data, [username]])
            self.condition.notifyAll()
            print("[#] MSG from %s: %s" % (username, data))
            self.condition.release()

        list_conn.close()

    def pick_ports(self) -> list:
        # p1, p2 = self.port_range.pop(), self.port_range.pop()
        # TODO: check if picked up port is client's port or something else
        p1 = choice(self.port_range)
        self.port_range.remove(p1)
        p2 = choice(self.port_range)
        self.port_range.remove(p2)

        return map(lambda x: str(x).encode(), [p1, p2])

    def check_ACK(self, conn) -> None:
        if conn.recv(1024).decode() != "ACK":
            raise Warning("ACK not received")


def main():
    server = Server("127.0.0.1", 5000, "Chat_Server_337", beg_port=50000, end_port=60002)
    server.start()


if __name__ == '__main__':
    main()
