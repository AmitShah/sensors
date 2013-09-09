'''
Created on Aug 10, 2013

@author: amitshah
'''

CONNECTION_STRING = '<connectionstring>'
ECHO = True
MAX_ROW_COUNT=5000


class DatabaseService(object):
    def __init__(self, engine):
        self.engine = engine
    
        
class StateService(DatabaseService):
        
    def getState(self,page,page_size):
        pass    
    def updateState(self,state):
        pass    
    
    def getNotifications(self,page,page_size,start_timestamp,end_timestamp):
        pass
    
class ConfigurationService(DatabaseService):
    def getDevices(self,accountid):
        pass
    

class User(object):
    pass
        
class State(object):
    pass        

class RequestAudit(object):    
    pass

class AccountService(DatabaseService):
    def __init__(self, engine):
        pass
    
    def get_audit_request(self,auth_token,start_timestamp,end_timestamp):
        pass
        
    def save_audit_request(self,audit_request):        
        pass
    
    def getUsers(self):
        pass
    
    def getUserFromUserId(self,userid):
        pass
    
    def getUser(self,accountid,userid):
        pass
    
    def getUserWithPassword(self,userid,password):
        pass
     
    def getUserWithAuthToken(self,auth_token):          
        pass
    
    def createUser(self,accountid,userid,password):
        pass
    
    def saveUser(self,user):                  
        pass
    
    def deleteUser(self,user):                  
        pass
        
    
    def resetSecret(self,accountid,userid):
        pass
    
if __name__ == '__main__':
    print 'interface place holder'