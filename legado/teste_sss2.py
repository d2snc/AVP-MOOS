import socket
import numpy as np
import cv2


 

localIP     = "127.0.0.1"

localPort   = 3000

bufferSize  = 1024

 

msgFromServer       = "Hello UDP Client"

bytesToSend         = str.encode(msgFromServer)

 

# Create a datagram socket

UDPServerSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)

 

# Bind to address and ip

UDPServerSocket.bind((localIP, localPort))

 

print("UDP server up and listening")

 

# Listen for incoming datagrams

while(True):

    bytesAddressPair = UDPServerSocket.recvfrom(bufferSize)

    message = bytesAddressPair[0]

    address = bytesAddressPair[1]

    clientMsg = "Message from Client:{}".format(message)
    clientIP  = "Client IP Address:{}".format(address)
    
    print(clientMsg)
    print(clientIP)

    image_data = b""

    image_data += message

    image_array = np.frombuffer(image_data, dtype=np.uint8)

    image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

    cv2.imshow("Received Image", image)

    cv2.waitKey(0)
    cv2.destroyAllWindows()
   

    # Sending a reply to client

    #UDPServerSocket.sendto(bytesToSend, address)