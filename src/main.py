'''
Created on Aug 8, 2013

@author: amitshah
'''
from mailgun import *
import idatabase as database
from bluerover import Api
import ssl,socket,sys
import os,tornado
from tornado.httpserver import HTTPServer
from tornado.websocket import WebSocketHandler
import sys,functools,json
from threading import Lock
import datetime,logging

logger = logging.getLogger('sensor_main')
logger.setLevel(logging.INFO)

fh = logging.FileHandler('sensor.log')
fh.setLevel(logging.INFO)
logger.addHandler(fh)


'''helper method to handle casting of improper chars'''
def ignore_exception(IgnoreException=Exception,DefaultVal=None):
    """ Decorator for ignoring exception from a function
    e.g.   @ignore_exception(DivideByZero)
    e.g.2. ignore_exception(DivideByZero)(Divide)(2/0)
    """
    def dec(function):
        def _dec(*args, **kwargs):
            try:
                return function(*args, **kwargs)
            except IgnoreException:
                return DefaultVal
        return _dec
    return dec

sint = ignore_exception(IgnoreException=ValueError)(int)

class Observer(object):
    
    def __init__(self):
        self._observers = []

    def attach(self, observer):
        if not observer in self._observers:
            self._observers.append(observer)

    def detach(self, observer):
        try:
            self._observers.remove(observer)
        except ValueError:
            pass

    def notify(self, msg):    
        for observer in self._observers:
            observer(message=msg)

from threading import RLock

'''Look for new line characters and notify all observer per line '''
class LineObserver(Observer):
    def __init__(self):
        Observer.__init__(self)
        self.buffer = ''
        self.rlock = RLock()
    '''we need to protect buffer from async calls :('''        
    def notify(self,message):
        try:              
            #prevent multiple async calls from overriding the buffer while in processing  
            with self.rlock:                
                self.buffer= self.buffer+message                
                while "\n" in self.buffer:
                    (line, self.buffer) = self.buffer.split("\n", 1)
                    data = line.strip() #remove blank lines (when keep alive is sent from server)
                    if data:
                        logger.info(('sending buffered data:%s' % self.buffer))
                        Observer.notify(self, data)                            
        except:
            pass
        finally:
            pass
        
    
class BaseHandler(tornado.web.RequestHandler):        
    def initialize(self,event_service,account_service,configuration_service,api):
        self.event_service = event_service
        self.account_service = account_service
        self.configuration_service = configuration_service
        self.api = api
        pass
    
    def get_current_user(self):
        '''used for web api administration access'''
        #self.account_service.getUserWithPassword()
        user = self.get_secure_cookie('user')
        if user is not None:            
            user = json.loads(self.get_secure_cookie("user"))
        return user

class LoginHandler(BaseHandler):
    def get(self):
        self.render('login.html')
    def post(self):
        userid = self.get_argument('userid', True)
        password = self.get_argument('password',True)
        user = self.account_service.getUserWithPassword(userid,password)
        if user is not None:            
            self.set_secure_cookie("user",json.dumps(user.to_dict()))
            self.redirect(self.get_argument("next", u"/"))
        else:
            self.render('login.html',message='Error logging in, please try again.\
            If you continue to experience issues, please contact support')

class LogoutHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.clear_cookie("user")
        self.redirect(u"/login")
        
class UpdateHandler(WebSocketHandler):
    
    observer = LineObserver()
    
    def open(self):
        UpdateHandler.observer.attach(self)
        
    def on_message(self, message):
        cmd = json.loads(message)
        pass
    
    def on_close(self):
        UpdateHandler.observer.detach(self)
        
    def broadcast_as_json(self,message):
        self.write_message(json.encoder.encode_basestring(message))
        
    def __call__(self,message=None):
        self.broadcast_as_json(message)

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('temp.html')
  
class MetaHandler(BaseHandler):    
    def get(self):
        json_rfid= self.api.call_api("/rfid", {})
        self.write(json_rfid)          
        
if __name__ == '__main__':
    
    '''let setup tcp connection to the upstream service to get sensor data 
    and handle this data with a async socket read for distribution :) '''
    
    api = Api(token='wEjpw3abc23CNVb3DnXSvNp60iPKNRsw8TYLO9Dm',
              key='k7Z3qAYnuqW2HMXksI1MkWdkpyPEduIT1dGyyJrVm0CEQ08L5Iaph4t8e1iD/dFQ',
              base_url='https://developers.polairus.com')
    print api._key
    signature = api._generate_signature(api._key, "GET", "https://developers.polairus.com/eventstream")    
    CRLF = '\r\n'
    request = [
               'GET /eventstream HTTP/1.1',
               'User-Agent: curl/7.21.3 (i686-pc-linux-gnu) libcurl/7.21.3 OpenSSL/0.9.8o zlib/1.2.3.4 libidn/1.18',
               'Host: developers.polairus.com',
               'Accept: */*',
               'Authorization:BR wEjpw3abc23CNVb3DnXSvNp60iPKNRsw8TYLO9Dm:%s' %signature,
               '',
               '',
               ]
    sock = socket.socket()    
    s = ssl.wrap_socket(sock)
    
    def connect_to_service():        
        s.connect(('developers.polairus.com',443))    
        s.sendall(CRLF.join(request))
        pass
    
    def data_handler(sock,fd,events):
        try:                    
            data = sock.recv(4096)
            logger.info(('received data:%s' % data))
            UpdateHandler.observer.notify(data)        
        except:
            sock.close()
            tornado.ioloop.IOLoop.instance().add_timeout(datetime.timedelta(seconds=30), connect_to_service)            
        pass

    callback = functools.partial(data_handler, s)
    ioloop = tornado.ioloop.IOLoop.instance()
    ioloop.add_handler(s.fileno(), callback, ioloop.READ)    
    ioloop.add_callback(connect_to_service)
    
    #define all the services
    services = dict(
        event_service = database.StateService(database.CONNECTION_STRING),\
        configuration_service = database.ConfigurationService(database.CONNECTION_STRING),\
        account_service = database.AccountService(database.CONNECTION_STRING), \
        api = api
        )
    
    settings = dict(
        template_path=os.path.join(os.path.dirname(__file__), "template"),
        static_path=os.path.join(os.path.dirname(__file__), "static"),
        cookie_secret= 'secret_key',
        login_url='/login'
        )  
    application = tornado.web.Application([
    (r"/update", UpdateHandler),
    (r"/meta", MetaHandler, services),
    (r"/*", MainHandler),
          
    ], **settings)
    
    sockets = tornado.netutil.bind_sockets(9999)
    server = HTTPServer(application)
    server.add_sockets(sockets)
    
    #pc.start()
    ioloop.start()
    
