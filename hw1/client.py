from socket import *
import time
import sys

def send_tcp(command):

    while True:
        
        data = command
        data = data.encode('utf-8')
        s.send(data)
        recvdata = s.recv(8000).decode("utf-8")
        
        # record the random number if login success
        if command[0:5] == "login" and recvdata[0:7] == "Welcome":
            print(recvdata[ :-2])
            global identity
            identity = recvdata[-2:]
            #print(identity)

        elif command[0:6] == "logout" and recvdata[0:3] == "Bye":
            identity = "10"
            print(recvdata)

        elif command[0:4] == "exit":
            s.close()
            sys.exit()

        else :
            print(recvdata)

        get_command()


def send_udp(command):

    s1 = socket(AF_INET,SOCK_DGRAM)
    data = command
    data = data.encode('utf-8')
    s1.sendto(data, (localhost,port))
    serverMessage, addr = s1.recvfrom(8000)
    print(serverMessage.decode())
    s1.close()
    get_command()


def get_command():
    
    command = input('% ').strip(' ')

###################### UDP transfer ####################################

    if command=="whoami":
        command += identity
        #print(identity)
        send_udp(command)
        
    elif(command[0:8]=="register"):
        send_udp(command)

    ###################### TCP transfer ####################################

    elif(command[0:5]=="login"):
        send_tcp(command) 


    elif(command[0:6]=="logout"):
        send_tcp(command)

    elif command[0:9] == "list-user":
        send_tcp(command)

    elif command[0:4]  == "exit":
        send_tcp(command)
    
    #default
    
    else :
        print('Command not found')
        get_command()

if __name__ == '__main__':

    # connect tcp socket
    port = sys.argv[2]
    localhost = sys.argv[1]
    port = int(port)
    global s
    s = socket(AF_INET,SOCK_STREAM)
    s.connect((localhost,port))
    recvdata = s.recv(8000).decode("utf-8")
    print(recvdata)

    global identity
    identity = "10"

    get_command()



               
    
    
    


 
    
