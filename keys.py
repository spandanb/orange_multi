"""
Interface for interacting with keys on local system 
such as creating keys, checking fingerprint.
"""
from os import chmod
from os.path import expanduser, isfile
from Crypto.PublicKey import RSA
import hashlib
import base64
import pdb

#See: 
#http://stackoverflow.com/questions/2466401
#https://gist.github.com/jtriley/7270594

def hash_to_fingerprint(seq):
    """returns seq with a colon after every 2 chars
    """
    chunks = (seq[pos:pos + 2] for pos in xrange(0, len(seq), 2))
    return ":".join(chunks)

def check_and_create_privkey(location="~/.ssh/"):
    """
    Creates private key file at `location`
    if one does not exist.
    Supports path with variable expansion
    """
    location = expanduser(location)
    privkey_path= "{}id_rsa".format(location)
    pubkey_path = "{}id_rsa.pub".format(location)

    #file exists, return
    if isfile(privkey_path): return

    key = RSA.generate(2048)
    with open(privkey_path, 'w') as content_file:
        chmod(privkey_path, 0600)
        content_file.write(key.exportKey('PEM'))
    pubkey = key.publickey()
    with open(pubkey_path, 'w') as content_file:
        content_file.write(pubkey.exportKey('OpenSSH'))

def get_pubkey(location="~/.ssh/id_rsa.pub"):
    """
    Gets the contents of the pubkey
    Arguments:-
        location:- location of pub key
    """
    location = expanduser(location)
    with open(location, 'r') as content_file:
        return content_file.read()

def get_pubkey_fingerprint(privkey_path="~/.ssh/id_rsa"):
    """
    Gets the md5 fingerprint of the pubkey
    Arguments:-
        privkey_path:- location of private key
    """
    privkey = RSA.importKey(open(expanduser(privkey_path)))
    pubkey = privkey.publickey()
    md5digest = hashlib.md5(pubkey.exportKey('DER')).hexdigest()
    return hash_to_fingerprint(md5digest)


if __name__ == "__main__":
    #check_and_create_privkey()
    #pub = get_pubkey()
    print get_pubkey_fingerprint()


