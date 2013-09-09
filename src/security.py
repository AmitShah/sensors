'''
Created on Aug 11, 2013

@author: amitshah
'''
import hashlib
import os
import hmac
import binascii

def generateSalt ():
    #randomly generate a 16 byte salt
    return os.urandom(16).encode('base_64')[:16]

def generateSecretKey():
    #http://www.ietf.org/rfc/rfc2104.txt, sha-1 uses 64 byte length with minimum of 20 bytes
    #key should be between 64 and 20 bytes
    return os.urandom(64).encode('base_64')[:64]

def generateAuthToken():
    return os.urandom(40).encode('base_64')[:40]

def getPasswordHash(salt, password):
    return hashlib.md5(salt+password).hexdigest()

def isCorrectPassword(password, hash,salt):
    return hash == str(getPasswordHash(salt,password))
#hmac-sha1 hash the request object, should be 160 bits/ 20 BYTES
#http://stackoverflow.com/questions/8338661/implementaion-hmac-sha1-in-python
def getMessageSignature(secret_key,message):
    #http://docs.aws.amazon.com/AmazonS3/latest/dev/RESTAuthentication.html
    return binascii.b2a_base64(hmac.new(secret_key,message,hashlib.sha1).digest())[:-1] # get rid of newline
    
    
if __name__ == '__main__':    
    salt = generateSalt()
    hex = getPasswordHash(salt, "testpassword")
    print hex
    
    assert getPasswordHash(salt, "testpassword") == hex
    secret_key =  generateSecretKey()
    request_signature = getMessageSignature(secret_key ,"GET /eventstream/start_time=100&endtime=1000")
    
    print 'signature',request_signature
    print len(request_signature)
    print 'Done'
    
    message = 'GET\n\
webservices.amazon.com\n\
/onca/xml\n\
AWSAccessKeyId=00000000000000000000\
&ItemId=0679722769&Operation=ItemLookup\
&ResponseGroup=ItemAttributes%2COffers%2CImages%2C\
Reviews&Service=AWSECommerceService&Timestamp=2009-01-01T12%3A00%3A00Z&Version=2009-01-06'
    print getMessageSignature(b'1234567890' ,message)
    print 'Twitter:',getMessageSignature('kAcSOqF21Fu85e7zjz7ZN2U4ZRhfV3WpwPAoE3Z7kBw&LswwdoUaIvS8ltyTt5jkRh4J50vUPVVHtR2YPi5kE',\
                                         "POST&https%3A%2F%2Fapi.twitter.com%2F1%2Fstatuses%2Fupdate.json&include_entities%3Dtrue%26oauth_consumer_key%3Dxvz1evFS4wEEPTGEFPHBog%26oauth_nonce%3DkYjzVBB8Y0ZFabxSWbWovY3uYSQ2pTgmZeNu2VS4cg%26oauth_signature_method%3DHMAC-SHA1%26oauth_timestamp%3D1318622958%26oauth_token%3D370773112-GmHxMAgYyLbNEtIKZeRNFsMKPR9EyMZeS9weJAEb%26oauth_version%3D1.0%26status%3DHello%2520Ladies%2520%252B%2520Gentlemen%252C%2520a%2520signed%2520OAuth%2520request%2521")
    print 'Twitter expected:tnnArxj06cWHq44gCs1OSKk/jLY='
    import base64
    dig = hmac.new(b'1234567890', msg=message, digestmod=hashlib.sha256).digest()
    print base64.b64encode(dig).decode()      # py3k-mode