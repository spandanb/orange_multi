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
from utils import create_and_raise

#See: 
#http://stackoverflow.com/questions/2466401
#https://gist.github.com/jtriley/7270594
#http://stackoverflow.com/questions/6682815

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

def get_pubkey(location="~/.ssh/id_rsa.pub", strip_hostname=True):
    """
    Gets the contents of the pubkey
    Arguments:-
        location:- location of pub key
    """
    location = expanduser(location)
    with open(location, 'r') as content_file:
        pubkey = content_file.read()
    
    if strip_hostname:
        #TODO: Not sure if this will always be correct
        pubkey = " ".join(pubkey.split(" ")[:-1])

    return pubkey

def get_pubkey_fingerprint(hashtype, privkey_path="~/.ssh/id_rsa", pubkey_path="~/.ssh/id_rsa.pub"):
    """
    Gets the fingerprint of the pubkey
    Arguments:-
        hashtype:- [savi | aws] 
        privkey_path:- location of private key
        pubkey_path:- location of public key
    """
    #TODO: why are the following 2 different; both are md5 hashes
    if hashtype == "aws":
        privkey = RSA.importKey(open(expanduser(privkey_path)))
        pubkey = privkey.publickey()
        md5digest = hashlib.md5(pubkey.exportKey('DER')).hexdigest()

    elif hashtype == "savi":
        with open(expanduser(pubkey_path)) as pubkey_file:
            pubkey = pubkey_file.read()
            pubkey = base64.b64decode(pubkey.split()[1])
            #pubkey = base64.b64decode(pubkey.strip().split()[1].encode('ascii'))
            md5digest = hashlib.md5(pubkey).hexdigest()
    else:
        create_and_raise("InvalidHashTypeException", "hashtype must be 'savi' or 'aws'")
        
    return hash_to_fingerprint(md5digest)

def sync_aws_key(keyname, aws_client, clobber=False):
    """
    Synchronizes local RSA key with AWS with `keyname`.
    First, Checks whether local RSA priv key exists.
    If it does not exist locally, a new key is created. 
    If it does, but does not match with an
    AWS key, overrides AWS key info.

    Arguments:-
        keyname- the name of the key 
        aws_client- the AWS Client object
        clobber- delete existing key on AWS if name collision
    """
    #Check if local SSH key exists; if not create it
    check_and_create_privkey()
    #compare local key with remote key
    if aws_client.check_keyname(keyname):
        #get public key fingerprint
        fingerprint = get_pubkey_fingerprint("aws")
        if not aws_client.check_keyfingerprint(keyname, fingerprint):
            if clobber:
                #remove key with matching name
                aws_client.remove_keypair(keyname)
            else:
                #raise exception
                exc_msg = "local SSH key does not match key '{}' on AWS server".format(keyname)
                create_and_raise("SshKeyMismatchException", exc_msg)
    
            #Create key that corresponds with local key
            aws_client.create_keypair(keyname, get_pubkey())
    else:
        aws_client.create_keypair(keyname, get_pubkey())

def sync_savi_key(keyname, server_manager, clobber=False):
    """
    Synchronizes local RSA key with SAVI with `keyname`.
    Similar to sync_aws_key.
    Arguments:-
        keyname- the name of the key 
        server_manager- the AWS Client object
        clobber- delete existing key on SAVI if name collision
    """
    #Check if local SSH key exists; if not create it
    check_and_create_privkey()
    
    keys = server_manager.get_keypairs()
    for key in keys:
        if key["keypair"]["name"] == keyname:
            if key["keypair"]["public_key"] == get_pubkey():
                #Nothing to do here
                return 
            else:
                if clobber:
                    server_manager.remove_keypair(keyname)
                    server_manager.create_keypair(keyname, get_pubkey())
                else:
                    exc_msg = "local SSH key does not match key '{}' on SAVI server".format(keyname)
                    create_and_raise("SshKeyException", exc_msg) 
    else:
        server_manager.create_keypair(keyname, get_pubkey())
        

if __name__ == "__main__":
    #check_and_create_privkey()
    pub = get_pubkey()
    print get_pubkey_fingerprint("savi")
    print get_pubkey_fingerprint("aws")


