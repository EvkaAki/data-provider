import base64
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP

publicKey = RSA.importKey(open("keys_/public.pem").read())
privateKey = RSA.importKey(open("keys_/private.pem").read())

cipherEncrypt = PKCS1_OAEP.new(publicKey)
cipherDecrypt = PKCS1_OAEP.new(privateKey)


def encrypt(data):
    data = bytes(data, 'utf-8')
    return base64.b64encode(PKCS1_OAEP.new(publicKey).encrypt(data))


def decrypt(data):
    data = base64.b64decode(data)
    return PKCS1_OAEP.new(privateKey).decrypt(data).decode("utf-8")
