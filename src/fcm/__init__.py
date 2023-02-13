import asyncio
import secrets
import base64
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.serialization import PublicFormat, PrivateFormat, NoEncryption, Encoding
server_key = [
  0x04,
  0x33,
  0x94,
  0xf7,
  0xdf,
  0xa1,
  0xeb,
  0xb1,
  0xdc,
  0x03,
  0xa2,
  0x5e,
  0x15,
  0x71,
  0xdb,
  0x48,
  0xd3,
  0x2e,
  0xed,
  0xed,
  0xb2,
  0x34,
  0xdb,
  0xb7,
  0x47,
  0x3a,
  0x0c,
  0x8f,
  0xc4,
  0xcc,
  0xe1,
  0x6f,
  0x3c,
  0x8c,
  0x84,
  0xdf,
  0xab,
  0xb6,
  0x66,
  0x3e,
  0xf2,
  0x0c,
  0xd4,
  0x8b,
  0xfe,
  0xe3,
  0xf9,
  0x76,
  0x2f,
  0x14,
  0x1c,
  0x63,
  0x08,
  0x6a,
  0x6f,
  0x2d,
  0xb1,
  0x1a,
  0x95,
  0xb0,
  0xce,
  0x37,
  0xc0,
  0x9c,
  0x6e,
]

FCM_SUBSCRIBE = 'https://fcm.googleapis.com/fcm/connect/subscribe'
FCM_ENDPOINT = 'https://fcm.googleapis.com/fcm/send'

async def register(session, senderId=0,token=0):
  keys = createKeys()
  print({
    "authorized_entity" : (senderId),
    "endpoint" : f"{FCM_ENDPOINT}/{token}",
    "encryption_key" : keys["publicKey"],
    "encryption_auth": keys["authSecret"]
  })
  async with session.post(FCM_SUBSCRIBE,skip_auto_headers = ["User-Agent","accept-encoding","accept"], data={
    "authorized_entity" : senderId,
    "endpoint" : f"{FCM_ENDPOINT}/{token}",
    "encryption_key" : keys["publicKey"],
    "encryption_auth": keys["authSecret"]
  }, 
  headers={"Content-Type":"application/x-www-form-urlencoded"}
  ) as response:
    return {"keys":keys, "fcm" : await response.json()}
# ecdsa library
# def createKeys():
#   ec =  ECDH(curve=NIST256p)#ecdsa.curves.curve_by_name("prime256v1")
#   ec.generate_private_key()
#   print(ec.private_key.to_string())
#   return {"privateKey": base64.urlsafe_b64encode(ec.private_key.to_string()).replace(b"=",b"").decode("utf-8"),
#           "publicKey":  base64.urlsafe_b64encode(ec.get_public_key().to_string('uncompressed')).replace(b"=",b"").decode("utf-8"),
#           "authSecret": secrets.token_urlsafe(16)

#   }
def createKeys():
  private_key =  ec.generate_private_key(ec.SECP256R1)#ecdsa.curves.curve_by_name("prime256v1")
  return {"privateKey":  private_key.private_bytes(Encoding.PEM, PrivateFormat.TraditionalOpenSSL, NoEncryption()).decode("utf-8"),
          "publicKey":  base64.urlsafe_b64encode(private_key.public_key().public_bytes(Encoding.X962, PublicFormat.UncompressedPoint)).replace(b"=",b"").decode("utf-8"),
          "authSecret": secrets.token_urlsafe(16)
         }
