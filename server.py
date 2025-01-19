import socket, json, struct
from _thread import *
import database

class Server():
    def main(self):
        self.send_header = {
            'Content-type': 'application/json',
            'Content-encoding': 'utf-8'
        }
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('127.0.0.1', 65432))
        s.listen()
        #Consitintly runs the 'client_handlers' function to allow for mutiple connections
        while True:
            self.client_handler(s)

    def create_header(self, msg):
        bytes_msg_len = len(bytes(msg, 'utf-8'))
        header = '{ "Content-type": "application/json", "Content-encoding": "utf-8", "Content-length":' + str(bytes_msg_len) + '}'
        header = self.create_preheader(header)
        return header

    def _header(self, body_length):
        hdr = self.send_header
        hdr['Content-length'] = body_length
        hdr_str = json.dumps(hdr)
        return bytes(hdr_str.encode('utf-8'))

    def _preheader(self, length):
        return struct.pack('>H', length)

    def create_preheader(self,header):
        length = len(bytes(header, 'utf-8'))
        pre_header = "{" + str(length) + "}"
        pre_header = pre_header + header
        return pre_header

    #Handles clients e.g when new clients attempt to connect to the server
    def client_handler(self, s):
        conn, addr = s.accept()
        #Begins a new thread to handle the current client
        start_new_thread(self.handle_messages, (s, conn, addr))
        #handle_messages(s, conn, addr)

    #Handles messages sent to the server
    def handle_messages(self, s, conn, addr):
        #Setting database up for user
        db = database.database()
        db.start_engine()
        db.create_tables()
        #Recives a message sent to the server 
        self._read_buffer = b''
        data = conn.recv(1024)
        self.loggedin = False
        self.current_user = ""
        
        #While loop to continue handling concurent messages from the same client
        while(data is not None):
            d_str = data.decode("utf-8")
            if (d_str != ""):
                if (d_str[1] == 'W'):
                    d_str = d_str[2:]
            
            if('login' in d_str):
                if(self.loggedin):
                    errorstr = '{"action": "login", "result: "error", "errors": "Already logged in"}', 'utf-8'
                    self.send(conn, errorstr)
                else:
                    user = self.login(d_str)
                    self.send(conn, '{ "action": "login","result": "ok","errors": []}')
            elif('send_messages' in d_str):
                if(self.loggedin):
                    converted_msg = self.send_message(d_str)
                    db.add_entry('message', converted_msg[0], user, converted_msg[1])
                    self.send(conn, '{ "action": "send","result": "ok","errors": []}')
                else:
                    errorstr = '{"action": "send", "result": "error", "errors": "Not logged in"}', 'utf-8'
                    self.send(conn, errorstr)
            elif('get_messages' in d_str):
                if(self.loggedin):
                    messages = db.get_entry('message', 'to', user)
                    all_msg = ""
                    for i in messages:
                        return_msg = '{"to": "' + str(i.to) + '", "from": "' + str(i.from_user) + '", "msg": "' + str(i.message) + '", "sent": "' + str(i.sent) + '"},'
                        all_msg += return_msg
                    all_msg = all_msg[:len(all_msg) -1]
                    all_msg = '{"action": "get_messages", "result": "ok", "messages": [' + all_msg + '], "errors": []}'
                    print(all_msg)
                    self.send(conn, all_msg)
            elif('logout' in d_str):
                self.loggedin = False
                self.send(conn, '{ "action": "logout","result": "ok","errors": []}')

            #conn.sendall(data)
            data = conn.recv(1024)
            #print("sent")

    def login(self, message):
        self.loggedin = True
        index = message.index('name')
        index += 7
        name = message[index:]
        name = name.strip('"}')
        return name
    
    def send_message(self, message):
        index = message.index('params') + 9
        message_params = message[index:len(message)-1]
        json_msg = json.loads(message_params)
        print(json_msg)
        content = json_msg["messages"]
        content = content[0]
        to = content["to"]
        msg = content["msg"]
        return [to, msg]


    def get_message(self, user):
        pass


    def send(self, conn, msg):
        body = bytes(msg.encode('utf-8'))
        header = self._header(len(body))
        preheader = self._preheader(len(header))
        full_msg = preheader+header+body
        conn.send(full_msg)

    def _read_header(self, length):
        hdr_bytes = self._read(length)
        hdr_str = hdr_bytes.decode('utf-8')
        return json.loads(hdr_str)

    def _read_body(self, header):
        body_len = header.get('Content-length')
        body_bytes = b''
        body_str = ''
        body = None
        if body_len:
            body_bytes = self._read(body_len)
        else:
            raise ValueError('Content-length header missing')
        body_enc = header.get('Content-encoding')
        if body_enc == 'utf-8':
            body_str = body_bytes.decode('utf-8')
        else:
            raise ValueError(f'Unsupported Content-encoding: {body_enc}')
        body_type = header.get('Content-type')
        if body_type == 'application/json':
            body = json.loads(body_str)
        return body


if __name__ == '__main__':
    server = Server()
    server.main()