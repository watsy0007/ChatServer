#! /usr/bin/env python
#coding=utf-8

from tornado.tcpserver import TCPServer
from tornado.iostream import IOStream, StreamClosedError
from tornado.ioloop  import IOLoop

from tcpstreampackage import TCPStreamPackage
from models import UserModel
from logic import Logic

######################################################################
class Connection(object):

    logic = Logic()

    def __init__(self, stream, address):
        self._stream = stream
        self._address = address
        self._stream.set_close_callback(self.on_close)
        self._stream_package = TCPStreamPackage(self.onPackageDecode)
        self.read_message()

        print "A new user has entered the chat room.", address

    ######################################################################
    def read_message(self):
        self._stream.read_until_close( self.broadcast_message , self.broadcast_streaming_message)

    def broadcast_message(self, data):
        pass

    def broadcast_streaming_message(self, data):
        # print data
        self._stream_package.add( data)


    def send_message(self, data):


        try:
            self._stream.write(data)
        except StreamClosedError as err:
            print "%s error:\n%r\ndata: %s" % (self._address, err, data)



    def close(self):
        self._stream.close()

    def on_close(self):
        print "A user has left the chat room.", self._address
        Connection.logic.closeConnection(self)

    ######################################################################

    def onPackageDecode(self , package):

        # print package
        Connection.logic.handlePackage(self , package)


######################################################################
#
######################################################################
class ChatServer(TCPServer):
    def handle_stream(self, stream, address):
        print "New connection :", address, stream
        Connection(stream, address)


if __name__ == '__main__':
    print "Server start ......"
    server = ChatServer()
    server.listen(6000)
    IOLoop.instance().start()
