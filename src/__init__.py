from . import client

from . import fcm
from . import gcm
import uuid

async def register(session, senderId):
    appId = "wp:receiver.push.com#" + str(uuid.uuid4())
    subscription = await gcm.register(session, appId)
    # print(subscription)
    result = await fcm.register(session, token=subscription["token"], senderId=senderId)
    # print(result)
    result["gcm"] = subscription
    return result

async def listen(session, credentials):
    checkCredentials(credentials)
    return await client.Client(session, credentials, credentials["persistentIds"] if "persistentIds" in credentials else []).connect()

def checkCredentials(credentials):
    if not credentials:
        raise ValueError("Missing credentials")
    if not "gcm" in credentials:
        raise ValueError("Missing credentials.gcm")
    if not "androidId" in credentials["gcm"]:
        raise ValueError("Missing credentials.gcm.androidId")
    if not "securityToken" in credentials["gcm"]:
        raise ValueError("Missing credentials.gcm.securityToken")
    if not "keys" in credentials:
        raise ValueError("Missing credentials.keys")
    if not "privateKey" in credentials["keys"]:
        raise ValueError("Missing credentials.keys.privateKey")
    if not "authSecret" in credentials["keys"]:
        raise ValueError("Missing credentials.keys.authSecret")
    return True