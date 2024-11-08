import socketio
import time

uri = "http://192.168.1.216:5004/remote"

sio = socketio.Client(logger=True, engineio_logger=True)
start_timer = None


def send_ping():
    global start_timer
    start_timer = time.time()
    sio.emit('ping_from_client')

    #  the  "message" prefix maps to the handler on the server @socketio.on('message')
    sio.emit('message', "HOLY SHIT")


@sio.event
def connect():
    print('connected to server')
    send_ping()


@sio.event
def pong_from_server():
    global start_timer
    latency = time.time() - start_timer
    print('latency is {0:.2f} ms'.format(latency * 1000))
    sio.sleep(1)
    if sio.connected:
        send_ping()

        
#  magic sucks
# the function name is the "message" match
@sio.event
def do_ocr(file_path):
    print('OCR request received for file: {0}'.format(file_path))


if __name__ == '__main__':
    try:
        sio.connect(uri)
        sio.wait()
    except KeyboardInterrupt:
        print("Exiting...")
        sio.disconnect()
        exit(0)