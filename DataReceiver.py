import socket

class DataReceiver:
    """
    Listens on a UDP port, receives sonde packets from radiosonde_auto_rx,
    and outputs to the callback function.
    """

    def __init__(self, host='0.0.0.0', port=8080, buffer_size=4096, callback=None):
        self.host = host
        self.port = port
        self.buffer_size = buffer_size
        self.callback = callback
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.host, self.port))
        # print(f"Listening on UDP {self.host}:{self.port}")

    def listen(self):
        """
        Main loop: listen for UDP packets and execute callback.
        """
        try:
            while True:
                data, addr = self.sock.recvfrom(self.buffer_size)
                self.callback(data)

        except KeyboardInterrupt:
            print("\nStopping receiver.")
        finally:
            self.sock.close()


if __name__ == "__main__":
    def my_callback(data):
        print(data)
    
    receiver = DataReceiver(host="0.0.0.0", port=8080, callback=my_callback)
    receiver.listen()
