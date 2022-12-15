import os
from cryptography.fernet import Fernet


# Load the encryption key
def load_key():
    current = os.getcwd()
    with open(f"{current}/app/key.key", "rb") as file:
        data = file.read()
    return data


# Encrypt data
def enc_data(data):
    key = Fernet(load_key())
    encrypted = key.encrypt(bytes(data, 'utf-8'))
    return encrypted


# Decrypt data
def dec_data(data):
    key = Fernet(load_key())
    decrypted_thing = key.decrypt(data)
    decrypted = decrypted_thing.decode('utf-8')
    return decrypted