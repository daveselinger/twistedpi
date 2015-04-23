'''
Created on Mar 17, 2015
This one just avoids the GPIO libraries which don't work on OS X

@author: selly
'''
from twisted.protocols.basic import LineReceiver
from twisted.internet.protocol import Factory
from twisted.internet.endpoints import TCP4ServerEndpoint
from twisted.internet import reactor
from twisted.web import resource, server, static

class SimpleTwistedServer (resource.Resource):
    def getChild(self, name, request):
        print "Name" + name
        
        if (name==''):
            return self
    
    def render_GET(self, request):
        if ("tilt" in request.args):
            print "Got request to tilt to: {}".format(int(request.args["tilt"][0]))
        else:
            print "Got request for left: {}; right: {}".format(int(request.args["leftSpeed"][0]), int(request.args["rightSpeed"][0]))

        return "Hello, world! I am located at %r." % (request.prepath,)

class NotHello (resource.Resource):
    isLeaf = True
    
    def render_GET(self, request):
        return "GOOD BYE"

def startServer():
    # This assumes that the "." directory from which python is executed is the one below src and below html of the project
    staticRoot = static.File("./html/")
    dynamicServer = SimpleTwistedServer()
    dynamicServer.putChild('doggy', NotHello())
 
    staticRoot.putChild('execute', dynamicServer)
    htmlSite = server.Site(staticRoot)
    reactor.listenTCP(8008, htmlSite) #@UndefinedVariable

    reactor.run() #@UndefinedVariable
    
startServer()