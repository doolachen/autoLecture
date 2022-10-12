"""
This function is a python implementation of school's fronted encryption with javascript
"""
import math
import random
import re
from base64 import b64encode
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

chars = 'ABCDEFGHJKMNPQRSTWXYZabcdefhijkmnprstwxyz2345678'
chars_len = len(chars)


# generate seed
def _rds(lenth):
    retStr = ''
    for _ in range(lenth):
        retStr += chars[math.floor(random.random() * chars_len)]
    return retStr


def _gas(data, key0, iv0):
    # params refer to password, salt and _rds(16)
    regex = re.compile(r'(^\s+)|(\s+$)')
    key0 = regex.sub("", key0)
    key = bytes(key0, 'utf8')
    iv = bytes(iv0, 'utf8')
    # https://pycryptodome.readthedocs.io/en/latest/src/util/util.html?highlight=padding#crypto-util-padding-module
    cipher = AES.new(key, AES.MODE_CBC, iv)
    ct = cipher.encrypt(pad(bytes(data, 'utf8'), 16, style='pkcs7'))
    return b64encode(ct).decode('utf-8')


def genEncrpty(password, salt):
    return _gas(_rds(64) + password, salt, _rds(16))


# just for test
if __name__ == '__main__':
    res = genEncrpty('abcdefgh', 'xeoSNwHeOSKAxNfD')
    print(len(res))
    print(res)
