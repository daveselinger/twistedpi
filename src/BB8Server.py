'''
Created on Mar 17, 2015

@author: selly
'''
from twisted.protocols.basic import LineReceiver
from twisted.internet.protocol import Factory
from twisted.internet.endpoints import TCP4ServerEndpoint
from twisted.internet import reactor
from twisted.web import resource, server, static

class BB8LineServer(LineReceiver):
    '''
    A basic server which when it receives a line attempts to set the PWM duty cycle for that side
    '''

    def __init__(self, factory):
        '''
        Constructor
        '''
        self.factory = factory

    def lineReceived(self, line):
        value = int(line)
        print "line received: {} = {}".format(line, value)
        self.factory.bb8.setSpeed("left", value);
        self.factory.bb8.setSpeed("right", value);
        self.factory.bb8.setServoPosition(value);
            

class BB8LineServerFactory (Factory):
    def buildProtocol(self, addr):
        return BB8LineServer(self)
    
    def __init__(self, bb8Passed):
        self.bb8 = bb8Passed

class BB8HTMLServer (resource.Resource):
    def __init__(self, bb8): 
        self.bb8 = bb8
    
    isLeaf = True
    def getChild(self, name, request):
        if (name==''):
            return self
        return resource.Resource.getChild(self, name, request)
    
    def render_GET(self, request):
        if ("tilt" in request.args):
            tilt = int(request.args["tilt"][0])
            if (tilt < -30):
                tilt = -30
            if (tilt > 30):
                tilt = 30
            # angle range should run from -30 to +30
            self.bb8.setServoPosition(tilt/30.0 * 100.0)
        else:
            left = int(request.args["leftSpeed"][0])
            right = int(request.args["rightSpeed"][0])
            
            print "Command: leftSpeed: {}; rightSpeed: {}".format(left, right)
            self.bb8.setSpeed("left", left);
            self.bb8.setSpeed("right", right);

        return "Hello %r"  % (request.prepath,)

class BB8ServerContainer (object):
    def __init__(self):
        return
    
    def startServer(self, bb8Passed):
        endpoint = TCP4ServerEndpoint(reactor, 8007)
        endpoint.listen(BB8LineServerFactory(bb8Passed))
        
        # This assumes that the "." directory from which python is executed is the one below src and below html of the project
        staticRoot = static.File("./html/")
        bb8HtmlServer = BB8HTMLServer(bb8Passed)
        staticRoot.putChild('execute', bb8HtmlServer)
        htmlSite = server.Site(staticRoot)
        reactor.listenTCP(8008, htmlSite) #@UndefinedVariable
    
        reactor.run() #@UndefinedVariable
        print "SERVER STARTED"
