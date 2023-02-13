from .constants import constants
import io
from .mcs_pb2 import *

from google.protobuf import json_format 
from google.protobuf.internal.decoder import _DecodeVarint32

MCS_VERSION_TAG_AND_SIZE = constants["MCS_VERSION_TAG_AND_SIZE"]
MCS_TAG_AND_SIZE = constants["MCS_TAG_AND_SIZE"]
MCS_SIZE = constants["MCS_SIZE"]
MCS_PROTO_BYTES = constants["MCS_PROTO_BYTES"]

kVersionPacketLen = constants["kVersionPacketLen"]
kTagPacketLen = constants["kTagPacketLen"]
kSizePacketLenMin = constants["kSizePacketLenMin"]
kMCSVersion = constants["kMCSVersion"]

kHeartbeatPingTag = constants["kHeartbeatPingTag"]
kHeartbeatAckTag = constants["kHeartbeatAckTag"]
kLoginRequestTag = constants["kLoginRequestTag"]
kLoginResponseTag = constants["kLoginResponseTag"]
kCloseTag = constants["kCloseTag"]
kIqStanzaTag = constants["kIqStanzaTag"]
kDataMessageStanzaTag = constants["kDataMessageStanzaTag"]
kStreamErrorStanzaTag = constants["kStreamErrorStanzaTag"]

DEBUG = False

class Parser:
    def __init__(self, socket):
        self.socket = socket
        self.state = MCS_VERSION_TAG_AND_SIZE
        self.data = b""
        self.sizePacketSoFar = 0
        self.messageTag = 0
        self.messageSize = 0
        self.handshakeComplete= False
        self.isWaitingForData = True
        self.response = None
        self.minBytesNeeded = 1
    def __exit__(self):
        self.isWaitingForData = False

    async def recv(self):
        self.response = None
        while not self.response:
            self.minBytesNeeded = self.calculateMinBytesNeeded()
            if len(self.data) < self.minBytesNeeded:
                r = self.socket.recv(self.minBytesNeeded-len(self.data))
                if r:
                    self.data = self.data + r
                    if DEBUG:   
                        print("Got data", len(self.data), "need",self.minBytesNeeded)
                    if len(self.data) >= self.minBytesNeeded:
                        self.waitForData()
        return self.response
    def calculateMinBytesNeeded(self):
        minBytesNeeded = 0
        if self.state == MCS_VERSION_TAG_AND_SIZE:
            minBytesNeeded = kVersionPacketLen + kTagPacketLen + kSizePacketLenMin
        elif self.state ==  MCS_TAG_AND_SIZE:
            minBytesNeeded = kTagPacketLen + kSizePacketLenMin
        elif self.state == MCS_SIZE:
            minBytesNeeded = self.sizePacketSoFar + 1
        elif self.state == MCS_PROTO_BYTES:
            minBytesNeeded = self.messageSize
        else:
            raise ValueError("Unexpected State" + str(self.state))
        return minBytesNeeded
    def waitForData(self):
        if self.state == MCS_VERSION_TAG_AND_SIZE:
            self.gotVersion()
        elif self.state ==  MCS_TAG_AND_SIZE:
            self.gotMessageTag()
        elif self.state == MCS_SIZE:
            self.gotMessageSize()
        elif self.state == MCS_PROTO_BYTES:
            self.gotMessageBytes()
        else:
            raise ValueError("Unexpected State" + str(self.state))
            
    def gotVersion(self):
        if DEBUG:
            print("Version")
        self.state = MCS_VERSION_TAG_AND_SIZE
        if len(self.data) < 1:
            self.isWaitingForData = True
            return
        version = (self.data[0])
        self.data = self.data[1:]

        if DEBUG:
            print("VERSION IS "+ str(version))

        if version < kMCSVersion and version != 38:
            raise ValueError(f"Wrong version {version}")
        self.state = MCS_TAG_AND_SIZE
        self.gotMessageTag()

    def gotMessageTag(self):
        if DEBUG:
            print("Message Tag")
        if len(self.data) < 1:
            self.isWaitingForData = True
            return
        self.messageTag  = self.data[0]
        if DEBUG:
            print("received type", self.messageTag)
        self.data = self.data[1:]

        self.state = MCS_SIZE
        self.gotMessageSize()

    def gotMessageSize(self):
        if DEBUG:
            print("Message size ")
        incompleteSizePacket = False
        f = io.BytesIO(self.data)
        

        try:
            self.messageSize, varintLen = _DecodeVarint32(self.data, 0)
        except IndexError:
            self.sizePacketSoFar =  1+len(self.data)
            return
        # print(self.messageSize)
        # _EncodeVarint(f.write,self.messageSize) 
        self.data = self.data[varintLen:]
        # print(f.tell())

        if DEBUG:
            print(f"PROTO SIZE: {self.messageSize}")
        self.sizePacketSoFar = 0

        self.state = MCS_PROTO_BYTES
        if self.messageSize > 0:
            return
        else:
            self.gotMessageBytes()
    def gotMessageBytes(self):
        protoclass = self.protoFactory(self.messageTag)()
        if not protoclass:
            raise ValueError("Unknown Tag")
        if self.messageSize == 0:
            self.response = {'tag':self.messageTag, "object":{}}
            return self.response
        if (len(self.data) < self.messageSize):
            self.state = MCS_PROTO_BYTES
            self.isWaitingForData = True
            return

        buffer = self.data[:self.messageSize]
        self.data = self.data[self.messageSize:]

        if self.messageTag == kLoginResponseTag:
            if self.handshakeComplete:
                print("Login error?")
            else:
                self.handshakeComplete = True
                if DEBUG:
                   print("Handshake complete")
        protoclass.ParseFromString(buffer)
        self.response = {'tag':self.messageTag, 'object' : json_format.MessageToDict(protoclass) }
        self.getNextMessage()
        return self.response

    def getNextMessage(self):
        self.messageTag = 0
        self.messageSize = 0
        self.state = MCS_TAG_AND_SIZE
        return 


    def protoFactory(self, messageTag):
        if messageTag == kHeartbeatPingTag:
            return HeartbeatPing
        elif messageTag == kHeartbeatAckTag:
            return HeartbeatAck
        elif messageTag == kLoginRequestTag:
            return LoginRequest
        elif messageTag == kLoginResponseTag:
            return LoginResponse
        elif messageTag == kCloseTag:
            return Close
        elif messageTag == kIqStanzaTag:
            return IqStanza
        elif messageTag == kDataMessageStanzaTag:
            return DataMessageStanza
        elif messageTag == kStreamErrorStanzaTag:
            return StreamErrorStanza
        else:
            return None

        