"""
Server for controlling and synchronizing Kinects.

Scenario: There are three computer-Kinect stations in one ICU room. The nurses hit a big green button to signify
whether it is okay to record, and if it is okay whether to start or stop the recording.

This server lets each of the computer-Kinect stations connect so that they can communicate and synchronize. It does
this by acting as a simple relay server. For example, if clients A, C, and C are connected, and A sends the message
"get * * recording", then this server relays the message "get * * recording" to clients B and C.

SSL is used a) to authenticate the server, b) to let the server authenticate us as a client, and c) create a secure
communication channel.
"""

from binascii import crc32
import logging
import sys
import os
from twisted.protocols.basic import LineReceiver
from twisted.internet.protocol import Factory
from twisted.internet import ssl, reactor
import datetime
import settings
import time

PORT = settings.port


SERVER_KEY_FILE = "server.key"
SERVER_CERT_FILE = "server.cert"
CLIENT_CERT_FILE = "client.cert"
ROOT_DIR = os.path.expanduser("~/kinect")
DATA_DIR = os.path.join(ROOT_DIR, "incoming")
LOG_FILE = os.path.join(ROOT_DIR, "server"+datetime.date.today().strftime("%Y%m%d")+".log")
SYNC_INTERVAL = 1800 # half an hour

class KinectServer(LineReceiver):
    """ Twisted Protocol that receives and relays commands through the network. """

    def __init__(self, factory):
        self.factory = factory
        self.logger = logging.getLogger("KinectServer")
        self.outfile = None
        self.remain = 0
        self.crc = 0

        if not os.path.isdir(DATA_DIR):
            os.makedirs(DATA_DIR)


    def connectionMade(self):
        self.factory.clients.add(self)
        self.remoteHost = self.transport.getHost().host.rjust(15)
        self.logger.info("%s has connected" % self.remoteHost)

    def connectionLost(self, reason):
        self.factory.clients.remove(self)
        self.logger.info("%s has disconnected" % self.remoteHost)
        reason.printTraceback()
        if self.outfile:
            self.outfile.close()

            if self.remain != 0:
                # Problem uploading - discard
                self.logger.debug('%s connectionLost remain(%d)!=0', self.remoteHost,
                             self.remain)
                os.remove(self.outfilename)
            else:
                # Upload job object with upload status
                self.logger.debug('%s connectionLost remain==0', self.remoteHost)

    def lineReceived(self, line):
        if line.startswith("upload"):
            """ receive upload file """
            upload_cmd, clientLoc, clientID, file_key, file_size = line.split()
            self.logger.info("%s (%s %s) uploads %s file: %s, size: %s"
                             % (self.remoteHost, clientLoc, clientID, upload_cmd, file_key, file_size))
            # Example: file_key = 201401012312.zip, day = 20140101, hour = 23
            day = file_key[:8]
            hour = file_key[8:10]
            outPath = os.path.join(DATA_DIR, clientLoc + "_" + clientID, day, hour)
            if not os.path.isdir(outPath):
                os.makedirs(outPath)
            self.outfilename = os.path.join(outPath, file_key)
            try:
                self.outfile = open(self.outfilename, 'w')
            except Exception, value:
                self.logger.debug('lineReceived Unable to open file %s '
                             '(%s)', self.outfilename, value)
                self.transport.loseConnection()
                return
            self.remain = int(file_size)
            self.logger.debug('lineReceived Entering raw mode: %s %s',
                         self.outfile, self.remain)
            self.setRawMode()

        else:
            self.logger.info("%s relayed '%s'" % (self.remoteHost, line))
            for client in self.factory.clients:
                if client is not self:
                    client.sendLine(line)

    def rawDataReceived(self, data):
        # if self.remain%10000==0:
        #     self.logger.info('   & ',self.remain,'/',data.size)
        self.remain -= len(data)

        self.crc = crc32(data, self.crc)
        self.outfile.write(data)
        if self.remain == 0:
            self.setLineMode()
            self.logger.debug("%s rawDataReceived done.", self.remoteHost)

class KinectServerFactory(Factory):
    """ Twisted Factory that creates a KinectServer for each incoming connection. """

    clients = set()
    """ The set of all connected clients. """


    def __init__(self):
        pass


    def buildProtocol(self, addr):
        """ Inherited from Twisted. This is what builds a KinectServer for each incoming connection. """
	reactor.callLater(1, self.timesync)
        return KinectServer(self)

    def timesync(self):
        curtime = time.strftime('%m%d%H%M%Y.%S')
        line = "set * * time %s" % (curtime,)
        for client in self.clients:
            if client is not self:
                client.sendLine(line)
        reactor.callLater(SYNC_INTERVAL, self.timesync) 

def initLog():
    # set up logging to file - see previous section for more details
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S',
                        filename=LOG_FILE,
                        filemode='w')
    # define a Handler which writes INFO messages or higher to the sys.stderr
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    # set a format which is simpler for console use
    formatter = logging.Formatter('%(name)s %(levelname)s: %(asctime)s %(message)s', datefmt='%m-%d %H:%M:%S')
    # tell the handler to use this format
    console.setFormatter(formatter)
    # add the handler to the root logger
    logging.getLogger('').addHandler(console)

def main():
    """ Run the server. """
    # setup logger first
    initLog()

    # Load the client's self-signed certificate.
    clientCert = open(CLIENT_CERT_FILE).read()
    clientCertObj = ssl.Certificate.loadPEM(clientCert)

    # Load the server's key and the server's self-signed certificate.
    serverKey = open(SERVER_KEY_FILE).read()
    serverCert = open(SERVER_CERT_FILE).read()
    serverPEM = serverKey + serverCert
    serverCertObj = ssl.PrivateCertificate.loadPEM(serverPEM)

    # Create an SSL context factory. Passing the client's certificate along enables client authentication.
    sslContextFactory = serverCertObj.options(clientCertObj)

    kinectServerFactory = KinectServerFactory()

    # Set the Twisted reactor up to listen for connections. For each incoming connection, create a KinectServer
    # (using the KinectServerFactory) and create an SSL context (using the sslContextFactory). The SSL context is used
    # to verify clients and set up an SSL layer. The KinectServer is used to handle all messages their decrypted state;
    # messages are relayed to all other connections.
    reactor.listenSSL(PORT, kinectServerFactory, sslContextFactory)

    # Run the reactor (which enters Twisted's main loop).
    reactor.run()

if __name__ == "__main__":
    main()
