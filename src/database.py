'''
Created on Aug 10, 2013

@author: amitshah
'''

CONNECTION_STRING = 'mysql://sober:sobersteer@localhost/sobersteering'
ECHO = True
MAX_ROW_COUNT=5000

import sys
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from functools import wraps
import security  

webapi_engine = create_engine(CONNECTION_STRING, echo=ECHO)

class DatabaseService(object):
    def __init__(self, engine):
        self.engine = engine
    
        
class StateService(DatabaseService):
        
    def getState(self,page,page_size):
        data = []
        result = dict()
        with self.engine.begin() as connection:
            cursor = connection.execute("select * from State \
                LIMIT %s OFFSET %s",\
                page_size, page_size*page) 
            data = cursor.fetchall()
            cursor.close()   
        result = map(lambda x : dict(zip(x.keys(), x)), data)
        return result
    
    def updateState(self,state):
        session = self.session_factory() 
        try:
            session.add(state)            
            session.commit()
            session.refresh(state) #get the auto id assigned            
        except:
            session.rollback()
            print "Unexpected error:", sys.exc_info()[0]

        session.close()
        
        return True
    
    
    def getNotifications(self,page,page_size,start_timestamp,end_timestamp):
        data = []
        result = dict()
        count = 0
        with self.engine.begin() as connection:
            count = connection.scalar("select count(1) from Notifications\
                    where accountId=%s and timestamp >= %s and timestamp <=%s",\
                    start_timestamp,  end_timestamp)
            cursor = connection.execute("select count(1) from Notifications\
                    where accountId=%s and timestamp >= %s and timestamp <=%s\
                    LIMIT %s OFFSET %s",\
                    start_timestamp,  end_timestamp,page_size,page_size*page)
            data = cursor.fetchall()
            cursor.close()
        result['data'] = map(lambda x : dict(zip(x.keys(), x)), data)
        result['count'] = count
        result['page'] = page
        result['page_size'] = page_size        
        return result   

    
class ConfigurationService(DatabaseService):
    def getDevices(self,accountid):
        pass
    

from sqlalchemy import Column, BigInteger,Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
Base= declarative_base()

class User(Base):
    __tablename__ = 'user'
    id = Column(BigInteger,primary_key=True)
    accountid = Column('accountId',String)
    userid = Column('userId',String)
    salt = Column(String)
    hash = Column(String)
    is_active = Column('isActive',Boolean)
    auth_token = Column('authToken',String)
    secret_key= Column('secretKey',String)
    def to_dict(self):
        return dict(accountid=self.accountid,
                    userid = self.userid, 
                    auth_token= self.auth_token                   
                    )
        
class State(Base):
    __tablename__ = 'state'
    id = Column(BigInteger,primary_key=True)
    deviceid = Column('deviceId',String)
    state = Column('state',String)
    def to_dict(self):
        return dict(deviceId = self.deviceid, 
                    state = self.state                  
                    )
        
class RequestAudit(Base):    
    __tablename__='requestAudit'
    def __init__(self, url, accountid,userid,timestamp,http_status):
        self.accountid = accountid
        self.url = url
        self.userid = userid
        self.timestamp= timestamp
        self.http_status = http_status
        
    id = Column(BigInteger,primary_key=True)
    auth_token = Column('authToken',String)
    accountid = Column(String)
    userid = Column(String)
    url = Column(String)
    timestamp = Column(BigInteger)
    http_status = Column("httpStatus",Integer)
    content_length = Column('contentLength',BigInteger)

class AccountService(DatabaseService):
    def __init__(self, engine):
        self.session_factory = sessionmaker(bind=engine)
    
    def get_audit_request(self,auth_token,start_timestamp,end_timestamp):
        session = self.session_factory() 
        session.expire_on_commit = False
        ar = []
        try:
            
            ar = session.query(RequestAudit).\
                filter(RequestAudit.auth_token==auth_token,\
                       RequestAudit.timestamp > start_timestamp,\
                       RequestAudit.timestamp < end_timestamp).\
                all()                           
            session.commit()
          
        except:
            session.rollback()
            print "Unexpected error:", sys.exc_info()[0]
            return False
        session.close()     
                
        return ar
    
    def save_audit_request(self,audit_request):        
        session = self.session_factory() 
        try:
            session.add(audit_request)           
            session.commit()
        except:
            session.rollback()
            print "Unexpected error:", sys.exc_info()[0]
            return False
        session.close()     
        return True
    
    def getUsers(self):
        session = self.session_factory() 
        try:
            users = session.query(User).all()           
            session.expunge_all()                 
        except:            
            print "Unexpected error:", sys.exc_info()[0]
        
        session.close()             
        return users
    
    def getUserFromUserId(self,userid):
        user = None
        session = self.session_factory() 
        try:
            user = session.query(User).filter_by(userid=userid).first()           
            session.commit()
            session.refresh(user)
        except:
            session.rollback()
            print "Unexpected error:", sys.exc_info()[0]
        session.close()             
        return user
    
    def getUser(self,accountid,userid):
        user = None
        session = self.session_factory() 
        try:
            user = session.query(User).filter_by(accountid=accountid,userid=userid).first()           
            session.commit()
            session.refresh(user)
        except:
            session.rollback()
            print "Unexpected error:", sys.exc_info()[0]
        session.close()             
        return user
    
    def getUserWithPassword(self,userid,password):
        user = None
        session = self.session_factory() 
        try:
            user = session.query(User).\
            filter_by(userid=userid,is_active=True).first()           
            session.commit()
            session.refresh(user)
        except:
            session.rollback()
            print "Unexpected error:", sys.exc_info()[0]
        session.close()     
        if user is not None and \
        Security.isCorrectPassword(password, user.hash, user.salt):         
            return user
        return
     
    def getUserWithAuthToken(self,auth_token):          
        user = None
        session = self.session_factory() 
        try:
            user = session.query(User).filter_by(auth_token=auth_token).first()           
            session.commit()
            session.refresh(user)
        except:
            session.rollback()
            print "Unexpected error:", sys.exc_info()[0]

        session.close()             
        return user
    
    def createUser(self,accountid,userid,password):
        user = User()
        user.accountid=accountid
        user.userid = userid
        user.salt = Security.generateSalt() #password salt
        user.secret_key = Security.generateSecretKey()#private secret key, 64 bytes
        user.auth_token = Security.generateAuthToken()#poublic auth token, 40 bytes
        user.hash = Security.getPasswordHash(user.salt, password)
        user.is_active = True
        return user
    
    def saveUser(self,user):                  
        session = self.session_factory() 
        try:
            session.add(user)            
            session.commit()
            session.refresh(user) #get the auto id assigned            
        except:
            session.rollback()
            print "Unexpected error:", sys.exc_info()[0]

        session.close()
        
        return True
    
    def deleteUser(self,user):                  
        session = self.session_factory() 
        try:
            session.delete(user)            
            session.commit()
            session.refresh(user) #get the auto id assigned            
        except:
            session.rollback()
            print "Unexpected error:", sys.exc_info()[0]

        session.close()
        
        return True
        
    
    def resetSecret(self,accountid,userid):
        user = self.getUser(accountid, userid)
        user.secret_key = Security.generateSecretKey()
        self.saveUser(user)
        return user.secret_key
    
    
if __name__ == '__main__':
    '''with transaction(session_factory()) as session:
        test_events = session.query(EventData).\
            filter(EventData.deviceId == 'concord1').limit(10).all()
        print json.dumps( test_events)
    
    es = EventService(gts_engine)
    r = es.getEventsForAccount('concord', 0, 1310976095,0, 1000)
    print  json.dumps(r)
   
    print json.dumps(es.getEvents(0, 100))
    '''
    accs = AccountService(webapi_engine) 
    user = accs.createUser('concord','devuser','devuserpassword')
    accs.saveUser(user)
    
    print Security.isCorrectPassword('devuserpassword', user.hash,user.salt)
    pass