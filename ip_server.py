import subprocess as sp
import re
import socket

def get_ip(interface="p1"):
    """
    Get self IP at specified interface
    """
    try:
        intf = sp.check_output(["ifconfig", interface])
        intf = re.search("(?<=inet addr:)\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", intf)
        intf_ip = intf.group()
        return intf_ip
    except sp.CalledProcessError as err:
        return ""

def run_server():
    host = '' 
    port = 5000 
    backlog = 2 
    size = 1024 
    soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
    soc.bind((host, port)) 
    soc.listen(backlog) 
    while 1: 
        client, address = soc.accept() 
        data = client.recv(size) 
        client.send(get_ip(interface="p1")) 
        client.close()

if __name__ == "__main__":
    run_server()
