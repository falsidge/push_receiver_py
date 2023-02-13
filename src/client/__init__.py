import base64
import socket
import ssl
import io
import json

from cryptography.hazmat.primitives.asymmetric import ec
import http_ece


from google.protobuf.internal.encoder import _EncodeVarint
from  google.protobuf import json_format 

from cryptography.hazmat.primitives import serialization


from . import constants
from .mcs_pb2 import *
from .. import gcm
from . import parser

HOST = 'mtalk.google.com';
PORT = 5228;
MAX_RETRY_TIMEOUT = 15;
context = ssl.create_default_context()

def decrypt(obj, keys):
    if not "appData" in obj:
        raise ValueError("no appdata?")

    salt = ""
    cryptokey = ""
    for i in obj["appData"]:
        if "key" in i:
            if i["key"] == "encryption":
                salt = i["value"]
            if i["key"] == "crypto-key":
                cryptokey = i["value"]
    
    if not (salt and cryptokey):
        raise ValueError("salt or crpto key missing")

    private_key = serialization.load_pem_private_key(keys["privateKey"].encode("utf-8"), None)
    auth = keys["authSecret"] + ('=' * (4 - len(keys["authSecret"]) % 4)) if len(keys["authSecret"]) % 4 else "" 
    auth = base64.urlsafe_b64decode(auth)
    decrypted = http_ece.decrypt(base64.urlsafe_b64decode(obj["rawData"]), salt=base64.urlsafe_b64decode(salt[5:]),
                                            private_key=private_key,auth_secret=auth,dh=base64.urlsafe_b64decode(cryptokey[3:]),version="aesgcm")

    return decrypted

class Client:
    def __init__(self,session,credentials, persistentIds):
        self.credentials = credentials
        self.persistentIds = persistentIds
        self.socket = None
        self.ssocket = None
        self.session = session

    def __enter__ (self):
        return self
    
    async def connect(self):
        await gcm.checkIn(self.session, self.credentials["gcm"]["androidId"], self.credentials["gcm"]["securityToken"])
        self.socket = socket.create_connection((HOST, PORT))
        self.socket.setblocking(True)
        self.ssocket = context.wrap_socket(self.socket, server_hostname=HOST)
        self.ssocket.write(self.loginBuffer())
        self.parser = parser.Parser(self.ssocket)
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        if self.ssocket:
            self.ssocket.close() 
        if self.socket:
            self.socket.close() 
    
    async def recv(self):
        while True:
            message =  await self.parser.recv()
            print("test",message)
            if "tag" in message:
                if message["tag"] == constants.constants["kLoginResponseTag"]:
                    self.persistentIds = []
                    continue
                elif message["tag"] == constants.constants["kDataMessageStanzaTag"]:
                    if message["object"]["persistentId"] in self.persistentIds:
                        continue
                    
                    persist = message["object"]["persistentId"]
                    message = decrypt(message["object"], self.credentials["keys"])
                    message = json.loads(message.decode("utf-8"))

                    self.persistentIds.append(persist)
                    return message
        
    def loginBuffer(self):
        hexAndroidId = hex(self.credentials["gcm"]["androidId"])

        loginRequest = {
      "adaptiveHeartbeat"    : False,
      "authService"          : 2,
      "authToken"            : str(self.credentials["gcm"]["securityToken"]),
      "id"                   : 'chrome-63.0.3234.0',
      "domain"               : 'mcs.android.com',
      "deviceId"             : f"android-{hexAndroidId[2:]}",
      "networkType"          : 1,
      "resource"             : str(self.credentials["gcm"]["androidId"]),
      "user"                 : str(self.credentials["gcm"]["androidId"]),
      "useRmq2"              : True,
      "setting"              : [{ "name" : 'new_vc', "value" : '1' }],
      "clientEvent"          : [],
      "receivedPersistentId" : self.persistentIds,
    };
        lr = LoginRequest()
        print(lr)
        lr = json_format.ParseDict(loginRequest, lr)
        f = io.BytesIO() 
        _EncodeVarint(f.write,lr.ByteSize()) 
        sizebytes = f.getvalue()
        buf = int.to_bytes(constants.constants["kMCSVersion"]) + int.to_bytes(constants.constants["kLoginRequestTag"]) + sizebytes  + lr.SerializeToString()
        return buf


