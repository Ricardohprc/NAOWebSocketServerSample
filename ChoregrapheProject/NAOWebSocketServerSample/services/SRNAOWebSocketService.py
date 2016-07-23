#!/usr/bin/python

import tornado.ioloop
import tornado.web
import tornado.websocket
import tornado.template
import threading
import sys
import qi

service = None
clients = set()
PORT = 9091

class WSHandler(tornado.websocket.WebSocketHandler):

    def open(self):
        print 'connection opened...'
        clients.add(self)

    def on_message(self, message):
        if service != None:
            service._fromClient(message)

    def on_close(self):
        clients.remove(self)
        print 'connection closed...'

    def sendMessage(self, message):
        self.write_message(message)

class NotFoundHandler(tornado.web.RequestHandler):
    def prepare(self):
        self.set_status(404)
    def get(self):
        self.write("Not Found.")
    def post(self):
        self.write("Not Found.")

class WSThread(threading.Thread):

    def __init__(self):
        super(WSThread, self).__init__()

    def run(self):
        print("Websocket thread running..")
        application = tornado.web.Application([(r'/ws', WSHandler)], default_handler_class=NotFoundHandler)
        application.listen(PORT)
        tornado.ioloop.IOLoop.instance().start()
        print("Websocket thread finished..")

    def stop(self):
        tornado.ioloop.IOLoop.instance().stop()

class SRNAOWebSocketService:
    def __init__(self, session):
        self.session = session
        self.memory = self.session.service("ALMemory")
        self.subscriber = self.memory.subscriber("SRNAOWebSocket/to")
        self.subscriber.signal.connect(self.postMessage)

    def postMessage(self, message):
        [c.write_message(message) for c in clients]

    def _fromClient(self, message):
        if self.memory:
            self.memory.raiseEvent("SRNAOWebSocket/from", message)

if __name__ == "__main__":
    webSocketThread = WSThread()
    webSocketThread.start()

    try:
        app = qi.Application(sys.argv)
        app.start()
        service = SRNAOWebSocketService(app.session)
        app.session.registerService("SRNAOWebSocketService", service)
        app.run()   # will exit when the connection is over
    except Exception as e:
        print '\nException:' + e.message

    webSocketThread.stop()
