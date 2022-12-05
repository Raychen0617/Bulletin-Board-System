from socket import *
from select import select
import sqlite3
import threading 
import time 
import random
import sys

# create a lock 
lock = threading.RLock()

# random_list : record used random number
global random_list
random_list=[]

# dictionary : map users to unique random numbers
global dictionary
dictionary={}

# SN : unique serial number for post
global S_N 
S_N = 1

# INDEX : unique number for board
global INDEX
INDEX = 1

# record used board names
global used_board_name
used_board_name=[]

# record used post object
global used_post
used_post=[]

# record created chatroom
global used_chatroom
used_chatroom=[]

class Board:
    def __init__(self,index, name, moderator):
        self.index = index
        self.name = name
        self.moderator = moderator
        self.post = []
    
    def get_all_info(self):
        return str(self.index) + "\t"+ str(self.name) + "\t" +str(self.moderator)
    
    def get_name(self):
        return self.name
    
    def add_post(self,post):
        self.post.append(post)

    def delete_post(self,delete_post):
        for i in range(len(self.post)):
            if str(self.post[i].serial_number) == str(delete_post.serial_number):
                del self.post[i]
                break
        return

    def get_post(self):
        return self.post


class Post:
    def __init__(self, board_name, title, content, serial_number, author):
        self.board_name = board_name
        self.title = title 
        self.content = content 
        self.serial_number = serial_number
        self.author = author
        self.comment = ""
        from datetime import date
        today = date.today()
        self.date = today.strftime("%d/%m")

    def get_list_info(self):
        return  str(self.serial_number) + "\t" + str(self.title) + "\t" +str(self.author) + "\t" + str(self.date)

    def read_post(self):
        return "Author:"+ str(self.author) +"\n" +"Title:"+ str(self.title) +"\n" + "Date:"+ str(self.date) +"\n--\n" + str(self.content) + "\n--" + str(self.comment)

    def add_comment(self,whoadd,comment):
        self.comment = self.comment + "\n" + str(whoadd) + ": " + str(comment) 
    
    def get_serial_number(self):
        return self.serial_number
    
    def update_title(self,title):
        self.title = title 
    
    def update_content(self,content):
        self.content = content 


class Chatroom:
    def __init__(self, name, status, port, ip):
        self.name = name
        self.status = status
        self.port = port
        self.history_list=[]
        self.conn = None
        self.ip = ip
    
    def add_history_list(self,history_list):
        self.history_list = history_list
    
    def add_owner_conn(self,conn):
        self.conn = conn

    def change_status(self,status):
        self.status = status
    

# search for used name in class list
def search(list, platform):
    for i in range(len(list)):
        if list[i].get_name() == platform:
            return True
    return False

# search for used post serial number in class list
def search_post(list, platform):
    for i in range(len(list)):
        if str(list[i].get_serial_number()) == str(platform):
            return True
    return False

# search for used name
def search_chatroom_name(list,platform):
    for i in range(len(list)):
        if str(list[i].name) == str(platform):
            return True
    return False    


def read_tcp(client,addr,lock):
 
    username = None
    loginornot = False

    while True :
        
        data = client.recv(8000)
        data = data.decode('utf-8')
        

        if data[0:16] == "restart-chatroom":
        
            if loginornot is False:
                client.send(b'Please login first.')
                continue

            if search_chatroom_name(used_chatroom,username) is False:
                client.send(b'Please create-chatroom first.')
                continue
                
            for i in range(len(used_chatroom)):
                if str(used_chatroom[i].name) == str(username):
                    if used_chatroom[i].status is True:
                        client.send(b'Your chatroom is still running.')
                        break
                    else:
                        message = "start to create chatroom...:" + used_chatroom[i].port + ":" + username
                        used_chatroom[i].status = True
                        client.send(message.encode('utf-8'))
                        break
            continue

        
        if data[0:13] == "leavechatroom":
            for i in range(len(used_chatroom)):
                if used_chatroom[i].name == str(username):
                    used_chatroom[i].change_status(False)
                    break
        
        if data[0:15] == "create-chatroom":

            if loginornot is False:
                client.send(b'Please login first.')
                continue
            
            if search_chatroom_name(used_chatroom,username) is True:
                client.send(b'User has already created the chatroom.')
                continue
            
            message = "start to create chatroom..." + ":" + username
            client.send(message.encode('utf-8'))
            chatroom = Chatroom(username,True,data.split(" ")[1],data.split(" ")[2])
            used_chatroom.append(chatroom)
            continue

        if data[0:13] == "join-chatroom":
            
            if loginornot is False:
                client.send(b'Please login first.')
                continue           
            
            if search_chatroom_name(used_chatroom,data.split(" ")[1]) is False:
                client.send(b'The chatroom does not exist or the chatroom is close.')
                continue

            for i in range(len(used_chatroom)):
                if str(used_chatroom[i].name) == str(data.split(" ")[1]):
                    if used_chatroom[i].status is False:
                        client.send(b'The chatroom does not exist or the chatroom is close.')
                        break
                    else:
                        message = "Success:" + used_chatroom[i].port + ":" + username + ":" + used_chatroom[i].ip + ":"
                        client.send(message.encode('utf-8'))
                        break
            continue
            

        if data[0:12] == "create-board":
            
            lock.acquire()

            if loginornot is False :
                client.send(b'Please login first.')
                lock.release()
                continue
            
            board_name = data.split(" ")[1]
            if search(used_board_name,board_name) is True:
                client.send(b'Board already exists.')
                lock.release()
                continue
            else :
                client.send(b'Create board successfully')
                global INDEX
                board_name = Board(INDEX, board_name, username)
                INDEX+=1
                used_board_name.append(board_name)
                lock.release()
                continue

        if data[0:10] == "list-board":
            message = "Index\tName\tModerator"
            for name in used_board_name:
                message = message + "\n"
                message = message + name.get_all_info()
            client.send(message.encode('utf-8'))

        if data[0:11] == "create-post":

            if loginornot is False :
                client.send(b'Please login first.')
                continue

            board_name = data.split("--")[0][12:-1]
            title = data.split("--")[1][6:-1]
            content = data.split("--")[2][8: ].replace("<br>","\n")

            if search(used_board_name,board_name) is False:
                client.send(b'Board does not exist')
                continue
            
            lock.acquire()

            # create a Class Post object whoose name is same as it's serial number
            global S_N
            serial_number_post = S_N
            serial_number_post = Post(board_name, title,content,S_N,username)
            used_post.append(serial_number_post)
            S_N += 1
            '''
            for name in used_board_name:
                if name.get_name() == board_name:
                    name.add_post(serial_number_post)
            '''
            client.send(b'Create post successfully')
            
            lock.release()

        if data[0:9] == "list-post":
            
            if len(data.split(" ")) < 2:
                client.send(b'wrong format')
                continue
            
            board_name = data.split(" ")[1]

            if search(used_board_name,board_name) is False:
                client.send(b'Board does not exist.')
                continue
            
            message = "S/N\tTitle\tAuthor\tDate"
            for post in used_post:
                if post.board_name == board_name:
                    message += "\n"
                    message += post.get_list_info()
            client.send(message.encode('utf-8'))         

        if data[0:4] == "read":
            serial_number = data.split(" ")[1]
            if search_post(used_post,serial_number) is False :
                client.send(b'Post does not exist.')
                continue
            
            message=""
            for post in used_post:
                if str(post.get_serial_number())==str(serial_number):
                    message = post.read_post()
                    break
            client.send(message.encode('utf-8'))

        if data[0:11] == "delete-post":

            serial_number = data.split(" ")[1]

            if loginornot is False :
                client.send(b'Please login first.')
                continue

            lock.acquire()
            
            if search_post(used_post,serial_number) is False:
                client.send(b'Post does not exist.')
                lock.release()
                continue
            
            for post in used_post:
                if str(post.get_serial_number()) == str(serial_number):  #  find post to delete
                    
                    if str(post.author) != str(username) :    #  not the owner
                        client.send(b'Not the post owner.')
                        #print((username,post.author))
                        break 
                    
                    used_post.remove(post)  # remove from used_port
                    client.send(b'Delete successfully.')                    
            lock.release()

        if data[0:11] == "update-post":

            #lock.acquire()
            
            serial_number = data.split(" ")[1]

            if loginornot is False :
                client.send(b'Please login first.')
                continue
            
            if search_post(used_post,serial_number) is False:
                client.send(b'Post does not exist.')
                continue
            
            for post in used_post:
                if str(post.get_serial_number()) == str(serial_number):  #  find post to delete
                    
                    if str(post.author) != username:    #  not the owner
                        client.send(b'Not the post owner.')
                        break

                    if str(data.split(" ")[2]) == "--title":
                        post.update_title(data.split(" ",3)[3])
                    elif str(data.split(" ")[2]) == "--content":
                        post.update_content(data.split(" ",3)[3].replace("<br>","\n"))
                    client.send(b'Update successfully.')
                    break

        if data[0:7] == "comment":

            if len(data.split(" ")) < 3:
                client.send(b'comment <post-S/N> <comment>')
                continue

            if loginornot is False :
                client.send(b'Please login first.')
                continue
            
            # data.split(" ")[1] == serial number
            # data.split(" ")[2] == content

            if search_post(used_post,data.split(" ")[1]) is False :
                client.send(b'Post does not exist.')
                continue
            
            for post in used_post:
                if str(post.serial_number) == str(data.split(" ")[1]):
                    post.add_comment( username ,data.split(" ",2)[2])
                    client.send(b'Comment successfully')
                    break
            
            continue

        if data[0:4] == "exit" :
            client.close()
            break
        
        if data[0:5] == "login" :
            login_list = data.split(" ")
            if len(login_list) != 3:
                client.send(b'Usage: login <username> <password>')        
            
            else :
                if loginornot is True :
                    client.send(b'Please logout first.')
                    continue

                c.execute("SELECT Password from USER WHERE Username = ?",(login_list[1],))
                password = c.fetchone()
                if password is None :
                    client.send(b'Login failed.')
                    continue

                if list(password)[0] == login_list[2] : # Success login
                 
                    while True:
                        # random_list : record used random number
                        global random_list
                        identity = random.randint(11,99)
                        if identity not in random_list: 
                            random_list.append(identity)
                            break

                    global dictionary
                    dictionary[identity] = [str(login_list[1]).strip('[\']')]

                    username = data.split(" ")[1]
                    loginornot = True
                    client.send(b'Welcome, %s.%d'%(str(login_list[1]).strip('[]').encode("utf-8"),identity))
                    
                    
                else :
                    client.send(b'Login failed.')
            continue

        if data[0:6] == "logout":
            
            if username is not None:

                if search_chatroom_name(used_chatroom,username) is True:
                    for i in range(len(used_chatroom)):
                        if used_chatroom[i].name == username:
                            if used_chatroom[i].status == True:
                                client.send(b'Please do "attach" and "leave-chatroom" first.')
                                break
                            else :                                               
                                loginornot = False
                                random_list.remove(identity)
                                dictionary.pop(identity)
                                client.send(b'Bye, %s.'%(username.encode('utf-8'),))
                                username = None
                                break
                else:
                    loginornot = False
                    random_list.remove(identity)
                    dictionary.pop(identity)
                    client.send(b'Bye, %s.'%(username.encode('utf-8'),))
                    username = None
            else : 
                client.send(b'Please login first.')
            
            continue

        if data[0:9] == "list-user":

            Message = "NAME\tEMAIL"

            c.execute("SELECT Username,Email from USER ")
            user_list = c.fetchall()
            #print(user_list)
            if user_list is None :
                #print("No user yet")
                pass
            
            else:
                for i in user_list:
                    Message += "\n\r"
                    for j in i:
                        Message += str(j).strip('[()]').strip('\'')
                        Message +=  "\t"
                    
            client.send(b'%s'%(Message.encode('utf-8'),))
            continue


def read_udp(s):

    whoaminame = None
    while True :
        data,addr = s.recvfrom(8000)
        data = data.decode('utf-8')
        #print ("Recv UDP:'%s'" % data)

        if(data[0:6] == "whoami"):

            if data[-2:]=="10":
                serverMessage = 'Please login first.'
            else:
                #c.execute("SELECT NAME from USER WHERE LOGIN = ?",(data[-2: ],))
                for i in dictionary.keys() :
                    if str(i) == str(data[-2: ]):
                        whoaminame = dictionary[int(i)]
                
                if whoaminame is None :
                   # print('Unexpected error!!!')
                   pass
                
                else:
                    #print(whoaminame)
                    #print(data[-2: ])
                    serverMessage = str(whoaminame).strip('[]')[1:-1]
            
            s.sendto(serverMessage.encode(),addr)

        if data[0:13] == "list-chatroom":

            if data[-2:]=="10":
                serverMessage = 'Please login first.'
            
            else :
                serverMessage = "Chatroom_name\tStatus"    
                for i in range(len(used_chatroom)):
                    serverMessage += "\n"
                    serverMessage += str(used_chatroom[i].name) + "\t"
                    if used_chatroom[i].status is True:
                        serverMessage += "open"
                    else:
                        serverMessage += "close"

                s.sendto(serverMessage.encode(),addr)
                continue

        if(data[0:8] == "register"):

            user_list = data.split(" ")
            #print(len(user_list))

            if len(user_list) < 4 :         # register
                serverMessage = 'Usage: register <username> <email> <password>'
                s.sendto(serverMessage.encode(),addr)
            

            else:
                c.execute("SELECT * from USER WHERE Username = ?",(user_list[1],))
                row = c.fetchone()

                if row is not None:
                    serverMessage = 'Username is already used.'
                    s.sendto(serverMessage.encode(),addr)
                else:
                    c.execute("INSERT INTO USER (Username,Email,Password) \
                    VALUES (?, ?,?)",(user_list[1],user_list[2],user_list[3]))
                    serverMessage = 'Register successfully.'
                    s.sendto(serverMessage.encode(),addr)

        
        else:
            serverMessage = 'Command not found'
            s.sendto(serverMessage.encode(),addr)

def run():
    host = "127.0.0.1"
    port = sys.argv[1]
    port = int(port)
    size = 8000
    backlog = 10

    # create tcp socket and bind
    tcp = socket(AF_INET, SOCK_STREAM)
    tcp.bind((host,port))
    tcp.listen(backlog)
    #tcp.setblocking(0)

    # create udp socket and bind
    udp = socket(AF_INET, SOCK_DGRAM)
    udp.bind(('',port))

    udp_thread = threading.Thread(target=read_udp, args=(udp,))
    udp_thread.start()
    
    while True:
        client, addr = tcp.accept()
        client.send(b'''
        ********************************
        ** Welcome to the BBS server. **
        ********************************'''
                    )
        print('New Connection.')
        t = threading.Thread(target=read_tcp, args=(client, addr,lock))
        t.start()

if __name__ == '__main__':

    conn = sqlite3.connect('user.db',check_same_thread = False)
    #print('Open user database successfully')
    c = conn.cursor()
    c.execute('drop table if exists USER')
    c.execute(
        '''
        CREATE TABLE USER
        (
        UID INTEGER PRIMARY KEY AUTOINCREMENT,
        Username TEXT NOT NULL UNIQUE,
        Email TEXT NOT NULL,
        Password TEXT NOT NULL
        )
        '''
    )
    run()


