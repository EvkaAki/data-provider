import os
from base64 import b64encode, b64decode
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend


def get_key_iv(password, salt=None, iterations=100000):
    """ Generate a key and IV from the given password. """
    if salt is None:
        salt = os.urandom(16)
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=iterations,
        backend=default_backend()
    )
    key = kdf.derive(password)
    return key, salt


def encrypt(data, password):
    """ Encrypt the data with AES CBC mode. """
    key, salt = get_key_iv(password)
    iv = os.urandom(16)
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    padded_data = data + b' ' * (16 - len(data) % 16)  # pad data to 16 bytes block size
    encrypted = encryptor.update(padded_data) + encryptor.finalize()
    return b64encode(salt + iv + encrypted).decode('utf-8')


def decrypt(encrypted_data, password):
    """ Decrypt data encrypted by the above function. """
    data = b64decode(encrypted_data)
    salt, iv, encrypted = data[:16], data[16:32], data[32:]
    key, _ = get_key_iv(password, salt)
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    decrypted = decryptor.update(encrypted) + decryptor.finalize()
    return decrypted.rstrip(b' ').decode('utf-8')  # remove padding

