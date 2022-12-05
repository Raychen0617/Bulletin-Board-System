from socket import *
from select import select
import sqlite3
import threading 
import time 
import random
import sys


global random_list
random_list=[]

global dictionary
dictionary={}

def read_tcp(client,addr):
 
    username = None
    loginornot = False

    while True :

        data = client.recv(8000)
       # print ("Recv TCP:'%s'" % (data,))

        data = data.decode('utf-8')
        if data[0:4] == "exit" :
           # print('exit')
            client.close()
            break
        
        if data =='login' or data[0:6] == 'login ' :

            login_list = data.split(" ")

            if len(login_list) != 3:
                client.send(b'Usage: login <username> <password>')        
            
            else :
                '''
                c.execute("SELECT LOGIN from USER WHERE Username = ?",(login_list[1],))
                check_login = c.fetchone()
                if check_login is None :
                    client.send(b'Login failed.')
                    continue
                '''

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
                    #print(dictionary)

                    username = str(login_list[1]).strip('[\']')
                    loginornot = True
                    client.send(b'Welcome, %s.%d'%(str(login_list[1]).strip('[]').encode("utf-8"),identity))
                    
                else :
                    client.send(b'Login failed.')


        if data[0:6] == "logout":
            
            if username is not None:

                #print(username)
                loginornot = False
                random_list.remove(identity)
                dictionary.pop(identity)
                client.send(b'Bye, %s.'%(username.encode('utf-8'),))
                username = None

            else : 
                client.send(b'Please login first.')
    
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
    #udp.setblocking(0)
    #input = [tcp,udp]

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
        t = threading.Thread(target=read_tcp, args=(client, addr))
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


# socket error solved : lsof -i :port_number
