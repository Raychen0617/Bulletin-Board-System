from socket import *
import time
import sys
import threading 
import os
import select 
import datetime

# *******************************           CHAT ROOM   ***************************************************************************


# create a lock 
lock = threading.RLock()

global history_message
history_message = []

global list_of_clients
list_of_clients=[]

global leavechatroom
leavechatroom = False

global chat_server_socket
chat_server_socket = None

global chatroom_ready
chatroom_ready = False

# chatroom server name
global chat_server_username
chat_server_username = None

# login or not
global login_ornot
login_ornot = False

# record all history list
global history_dict
history_dict = {}

# record the name and the history list 
class HISTORY_WITH_ID:
    def __init__(self, id ,history_list):
        self.id = id
        self.history_list = history_list
        

def create_join_chat_room(recvdata,port,username,isrestart):

    global chat_server_username, chat_server_socket,leavechatroom, chatroom_ready
    chat_server_username = username
    leavechatroom = False
    chatroom_ready = False
    t = threading.Thread(target=create_chatroom, args=(port,))
    t.start()
    chat_server_socket = socket(AF_INET,SOCK_STREAM)
    while(chatroom_ready == False):pass
    chat_server_socket.connect((sys.argv[1],int(port)))
    chatroom_client(chat_server_socket,False,chat_server_username,True,isrestart)


def join_chat_room(port,username,ip):

    chat_socket = socket(AF_INET,SOCK_STREAM)
    chat_socket.connect((str(ip),int(port)))
    attachornot = False
    chatroom_client(chat_socket,attachornot,username,False,False)


def chatroom_client(chat_socket,attachornot,username,isowner,isrestart):
    
    server = chat_socket

    if attachornot is False and isrestart is False:
        datetime_dt = datetime.datetime.today()# 獲得當地時間
        datetime_str = datetime_dt.strftime("%H:%M")  # 格式化日期
        datetime_str = " [" + datetime_str + "] "
        message = "sys"+ datetime_str + ": " + username + " join us"
        server.send(message.encode('utf-8'))
    if attachornot is True:
        #  server will not connect again
        print( "   ********************************\n   **  Welcome to the chatroom   **\n   ********************************   ")
        global history_message
        for m in history_message:
            print(m)

        sockets_list = [sys.stdin, server]
        read_sockets,write_socket, error_socket = select.select(sockets_list,[],[]) 
        for socks in read_sockets:
            if socks == server:
                message = socks.recv(2048)
                continue
        
    while True:  
        
        # maintains a list of possible input streams  
        sockets_list = [sys.stdin, server]
        read_sockets,write_socket, error_socket = select.select(sockets_list,[],[]) 
    
        for socks in read_sockets:  
            if socks == server:  
                message = socks.recv(2048)
                message = message.decode('utf-8')
                if message == "leavechatroom":
                    if isowner is True:    # if is owner
                        s.send(b'leavechatroom')    # 1. update bbs
                        global leavechatroom    
                        leavechatroom = True    # 2. close all servers
                        server.close()  # 3. close all clients
                    else:
                        server.close()
                        datetime_str = datetime_dt.strftime("%H:%M")  # 格式化日期
                        datetime_str = " [" + datetime_str + "] "
                        print("sys"+datetime_str+": the chatroom is close.")
                        print("Welcome back to BBS.")
                    get_command()
                else:
                    print (message)  
            
            else:  
                message = sys.stdin.readline().strip("\n")
          
                if message == "detach" and isowner is True:
                    bbs_message = "detach:"+ str(chat_socket)
                    s.send(bbs_message.encode('utf-8'))
                    print("Welcome back to BBS.")
                    get_command()

                elif message == "leave-chatroom" and isowner is False:
                    print("Welcome back to BBS.")
                    datetime_str = datetime_dt.strftime("%H:%M")  # 格式化日期
                    datetime_str = " [" + datetime_str + "] " 
                    message = "sys" + datetime_str + ": " + username + " leave us."
                    server.send(message.encode('utf-8'))
                    get_command()
                
                elif message == "leave-chatroom" and isowner is True:
                    broadcast("leavechatroom", None)    # broadcast to everyone
                    print("Welcome back to BBS.")
                
                else:
                    datetime_dt = datetime.datetime.today()# 獲得當地時間
                    datetime_str = datetime_dt.strftime("%H:%M")  # 格式化日期
                    datetime_str = " [" + datetime_str + "] " 
                    message = username + datetime_str + ":" + message
                    server.send(message.encode('utf-8'))
      


def chatroom_server(conn, addr):  

    conn.send(b'''
    ********************************
    **Welcome to the chatroom**
    ********************************'''
    )

    if history_message is not None:
        message = ""
        for i in range(len(history_message)):
            message += "\n" + history_message[i]
        conn.send(message.encode('utf-8')) 
  
    while True:  

        if leavechatroom is True:
            conn.close()
            global list_of_clients
            list_of_clients.remove(conn)
            break

        conn.settimeout(0.1)
        try:
            message = conn.recv(2048)  
            if message:
                # Calls broadcast function to send message to all  
                message_to_send = message.decode() 
                broadcast(message_to_send, conn)  

        except timeout:
            continue


# broad cast to everyone except the connection itself
def broadcast(message, connection):
    
    if str(message[0:3]) != "sys" and message != "leavechatroom": 
        lock.acquire()
        if len(history_message)==3:
            history_message.pop(0)
        elif len(history_message)> 3:
            print('history message problem occur')
        history_message.append(message)
        lock.release()

    global list_of_clients

    for clients in list_of_clients:
        if clients!=connection:  
            #try:
            clients.send(message.encode('utf-8'))  
            #except:  
            #    clients.close()
                # if the link is broken, we remove the client  
            #    remove(clients)

def remove(connection):
    connection.close()
    global list_of_clients
    if connection in list_of_clients:
        list_of_clients.remove(connection) 
    

def create_chatroom(port):
    
    host = sys.argv[1]
    port = int(port)
    backlog = 10

    # create tcp socket and bind   
    tcp = socket(AF_INET, SOCK_STREAM)
    tcp.setsockopt(SOL_SOCKET,SO_REUSEADDR,1)
    tcp.settimeout(1)
    tcp.bind((host,port))
    tcp.listen(backlog)
    

    global list_of_clients, history_dict,identity, history_message,chat_server_username,chatroom_ready
    if len(list_of_clients) != 0:
        print("ERROR!! some socket is not delete")
        for clients in list_of_clients:
            #print(clients)
            list_of_clients.remove(clients)

    history_message = []
    for name in history_dict:
        if str(name) == chat_server_username:
            history_message = history_dict[name]   # upadate history message 
            break 
    chatroom_ready = True

    while True:

        if leavechatroom is False:
            try:
                client, addr = tcp.accept()
                list_of_clients.append(client)
                t = threading.Thread(target=chatroom_server, args=(client, addr))
                t.start()

            except timeout:
                continue
        else :  # when leaving chatroom 
            tcp.close()
            history_dict[chat_server_username] = history_message
            break

# *******************************           CHAT ROOM  END  ***************************************************************************


def send_tcp(command):

    while True:
        
        data = command
        data = data.encode('utf-8')
        s.send(data)
        recvdata = s.recv(8000).decode("utf-8")
        # record the random number if login success
        if command[0:5] == "login" and recvdata[0:7] == "Welcome":
            print(recvdata[ :-2])
            global identity, chat_server_username
            identity = recvdata[-2:]
            chat_server_username = str(command.split(" ")[1])
            global login_ornot
            login_ornot = True
            #print(identity)

        elif command[0:6] == "logout" and recvdata[0:3] == "Bye":
            identity = "10"
            login_ornot = False
            chat_server_username = None
            print(recvdata)

        elif command[0:4] == "exit":
            s.shutdown(SHUT_RDWR)
            s.close()   # close bbs server
            global leavechatroom
            if leavechatroom is False:
                leavechatroom = True    # do leave chatroom
                broadcast("leavechatroom", None)
            sys.exit()
        
        elif command[0:15] == "create-chatroom":
            print(recvdata.split(":")[0])

            if str(recvdata.split(":")[0]) == "start to create chatroom...":
                # create_join_chat_room(recvdata,port,username):
                create_join_chat_room(recvdata.split(":")[0],command.split(" ")[1],recvdata.split(":")[1],False)
            

        elif command[0:13] == "join-chatroom":
            if str(recvdata.split(":")[0]) == "Success":
                # join_chat_room(port,username,history):
                join_chat_room(recvdata.split(":")[1],recvdata.split(":")[2],recvdata.split(":")[3])
            else:
                print(recvdata)

        elif command[0:16] == "restart-chatroom":

            if str(recvdata.split(":")[0]) == "start to create chatroom...":
                # create_join_chat_room(recvdata,port,username):
                print("start to create chatroom...")
                create_join_chat_room(recvdata.split(":")[0],recvdata.split(":")[1],recvdata.split(":")[2],True)     
            else:
                print(recvdata)
        
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
        send_udp(command)
        
    elif(command[0:8]=="register"):
        send_udp(command)
    
    elif(command[0:13]=="list-chatroom"):
        command += identity
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

    elif command[0:12] == "create-board":
        send_tcp(command)
    
    elif command[0:10] == "list-board":
        send_tcp(command)
    
    elif command[0:11] == "create-post":
        send_tcp(command)
    
    elif command[0:9] == "list-post":
        send_tcp(command)

    elif command[0:4] == "read":
        send_tcp(command)

    elif command[0:11] == "delete-post":
        send_tcp(command)
    
    elif command[0:11] == "update-post":
        send_tcp(command)

    elif command[0:7] == "comment":
        send_tcp(command)
######################################          ******************************      chatroom    **************************************************   ######################################
    elif command[0:15] == "create-chatroom":
        command = command +  " " + sys.argv[1]
        send_tcp(command)

    elif command[0:13] == "join-chatroom":
        send_tcp(command)

    elif command[0:6] == "attach":

        if chat_server_username is None:
            print('Please create-chatroom first.')
            get_command()
        
        elif login_ornot is False:
            print('Please login first.')
            get_command()

        else:
            chatroom_client(chat_server_socket,True,chat_server_username,True, False)

    elif command[0:16] == "restart-chatroom":
        send_tcp(command)

    else :
        # default
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





               
    
    
    


 
    
