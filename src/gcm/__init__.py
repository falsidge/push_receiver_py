import asyncio
from .. import fcm
from . import android_checkin_pb2
from . import checkin_pb2
import base64
from google.protobuf import json_format 
import aiohttp

REGISTER_URL = 'https://android.clients.google.com/c2dm/register3';
CHECKIN_URL = 'https://android.clients.google.com/checkin';
serverKey = base64.urlsafe_b64encode(bytes(fcm.server_key)).replace(b"=",b"")

async def register(session : aiohttp.client.ClientSession, appId):
    options = await checkIn(session)
    print(options)
    credentials = await doRegister(session, appId,options.android_id, options.security_token )
    return credentials

async def checkIn(session : aiohttp.client.ClientSession, androidId : int=0, securityToken=0):
    buffer = getCheckinRequest(androidId, securityToken)
    async with session.post(CHECKIN_URL, headers={"Content-Type":'application/x-protobuf'}, data = buffer) as body:
        message = checkin_pb2.AndroidCheckinResponse()
        message.ParseFromString(await body.read())
        return message

async def doRegister(session, appId, androidId = 0, securityToken=0):

    body = {
        "app": "org.chromium.linux",
        "X-subtype" : (appId),
        "device" :  str(androidId),
        "sender": serverKey.decode('utf-8')
    }
    print(body)
    response = await postRegister(session, body, androidId, securityToken)
    return {"token": response, "androidId":androidId,"securityToken":securityToken,"appId":appId}

async def postRegister(session,body, androidId=0,securityToken=0):
    async with session.post(REGISTER_URL, headers={
        "Authorization" : f"AidLogin {androidId}:{securityToken}",
        "Content-Type" : "application/x-www-form-urlencoded"
    },data=body) as response:
        j = await response.text()
        if "Error" in j:
            raise ValueError("Network error" + j)
        if "token" not in j:
            raise ValueError("token not found " + j)
        
        return j.split("=")[1]



def getCheckinRequest(androidId=0, securityToken=0):
    payload = {
        "userSerialNumber" : 0,
        "version":3,
        "id" : androidId,
        "securityToken" : securityToken ,
        "checkin":
        {
            "type":3,
            "chrome_build":
            {
                "platform":2,
                "chromeVersion":"63.0.3234.0",
                "channel" : 1
            }
        }
    }

    p = json_format.ParseDict( payload, checkin_pb2.AndroidCheckinRequest() )

    return p.SerializeToString()