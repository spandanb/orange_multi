import requests
from BaseHTTPServer import BaseHTTPRequestHandler
from StringIO import StringIO
import socket

class HTTPRequest(BaseHTTPRequestHandler):
    """
    http://stackoverflow.com/questions/2115410
    """
    def __init__(self, request_text):
        self.rfile = StringIO(request_text)
        self.raw_requestline = self.rfile.readline()
        self.error_code = self.error_message = None
        self.parse_request()

    def send_error(self, code, message):
        self.error_code = code
        self.error_message = message


def proxy(phost="", port=80):
    """
    Arguments:-
        phost: the host we are proxying
    """
    host = "0.0.0.0"
    soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    soc.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    soc.bind((host, port))
    soc.listen(5)
    while 1:
        conn, addr = soc.accept()
        data = conn.recv(1024)
        req = HTTPRequest(data)
        
        #Dispatcher
        method = getattr(requests, req.command.lower(), 'get')
        path = "http://{}/{}".format(phost, req.path)
        preq = method(path)
        conn.send(preq.text.encode('utf-8'))
        conn.close()

    soc.close()


if __name__ == "__main__":
    proxy(phost=sys.argv[1])
    #print requests.get("http://10.12.1.48").text
    
    
    
