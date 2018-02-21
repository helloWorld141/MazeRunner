import serial


class SerialClient():
    def __init__(self, port, baud_rate):
        self.port = port
        self.baud_rate = baud_rate

    def connect(self):
        self.client_conn = serial.Serial(
            self.port, self.baud_rate, timeout=None)
        print("SerialClient - Connected on {}:{}".format(self.port, self.baud_rate))

    def recv(self):
        try:
            data = self.client_conn.readline()
        except:
            return None
        if not data:
            return None
        data_s = data.decode('utf-8')
        print("SerialClient - Received data: {}".format(data_s))
        return data_s

    def send(self, data):
        try:
            self.client_conn.write(data.encode('utf-8'))
            print("SerialClient - Sent data: {}".format(data))
        except:
            print("SerialClient - Error sending data: {}".format(data))

    def close_conn(self):
        self.client_conn.close()
        print("SerialClient - Disconnected")
