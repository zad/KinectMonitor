"""
Client for controlling and synchronizing Kinects

Scenario: There are three computer-Kinect stations in one ICU room. The nurses hit a big green button to signify
whether it is okay to record, and if it is okay whether to start or stop the recording.

This client makes it possible to a) communicate with the button to start or stop recording, b) communicate with other
computer-Kinect stations to start or stop recording, c) interact with a remote user to let him or her control
recording state, or periodically upload recorded data to the server.

SSL is used a) to authenticate the server, b) to let the server authenticate us as a client, and c) create a secure
communication channel.
"""

import sys, signal, os
import traceback
import logging
import time
import argparse
import serial
from twisted.internet.protocol import ReconnectingClientFactory
from twisted.protocols.basic import LineReceiver, FileSender
from twisted.internet import ssl, reactor
from twisted.internet import task
import threading
from datetime import datetime, date
import shutil
from kinectrecorder import Recorder
import settings

SERVER = settings.server
PORT = settings.port

ROOT_DIR = os.path.expanduser("~/kinect")
DATA_DIR = os.path.join(ROOT_DIR, "data")
BACKUP_DIR = os.path.join(ROOT_DIR, "backup")
LOG_FILE = os.path.join(ROOT_DIR, "kinectclient" + time.strftime("%Y%m%d%H%M%S") + ".log")


CLIENT_KEY_FILE = "client.key"
CLIENT_CERT_FILE = "client.cert"
SERVER_CERT_FILE = "server.cert"

SYNC_PERIOD_IN_SECS = 20    # 10 seconds
TAR_PEROID_IN_SECS = 60     # one minute
BACKUP_SIZE_IN_MINS = 60 * 24    # 1 day

UPLOADER_ON = False

class KinectController:
    """ Sets and gets Kinect settings, and controls an attached Kinect accordingly.

    Both set and get will ignore any invalid settings. Exceptions won't be thrown.

    """

    settings = {"consent_acquired": False,
                "recording": False}

    timeRecordingStopped = 0

    #def __init__(self):
        #self.recorder = Recorder(ROOT_DIR, DATA_DIR)

    def set(self, setting, newValue):

        newValue = int(newValue)

        # For now limit new values to True or False.
        if newValue not in (True, False):
            raise ValueError("Settings must be either True or False.")

        # If we're not changing anything, don't do anything.
        if setting in self.settings.keys() and self.settings[setting] == newValue:
            return

        # When the consent status is changed, we need to reset the recording status.
        # TODO need to test and varify
        if setting == "consent_acquired":
            self.settings["consent_acquired"] = newValue
            self.set("recording", newValue)
        elif setting == "recording":
            if self.settings["consent_acquired"] and newValue == True:
                self.settings["recording"] = True
                self.logger.info("Kinect recorder start")
                self.recorder.start(self.logger)
                self.timeRecordingStopped = 0
            else:
                self.settings["recording"] = False
                self.logger.info("Kinect recorder stop")
                self.recorder.stop()
                self.timeRecordingStopped = time.time()

    def get(self, setting):
        if setting in self.settings.keys():
            return self.settings[setting]
        else:
            return None

    def toggle(self, setting):
        if setting in self.settings.keys():
            oldValue = self.get(setting)
            newValue = not oldValue
            self.set(setting, newValue)
            return self.get(setting)



class KinectClient(LineReceiver):

    """ Twisted Protocol that receives, handles, and sends commands through the network.

    Upon connecting, this client broadcasts a "get" message to every Kinect at our location. If we were for some reason
    disconnected, this lets the client sync up with current settings.

    Once sync'd, the client will listen for commands over the network and respond accordingly. For example, if this
    client receives "set location ID recording 1", and if the location matches this client's location, then this
    client will set the KinectController's recording setting to 1.

    Meanwhile, this client will also send messages if it's asked to do so by its factory. For example, if the the
    factory recognizes that an external button is pushed, then it will set the KinectController's state and ask this
    client to inform the other Kinects in the room of the change. Also, if this client is running in interactive mode,
    then the user can issue commands manually. In that case the factory will again send the message through this client.
    """

    def __init__(self, factory):
        self.factory = factory
        self.kinectController = self.factory.kinectController
        self.clientLocation = self.factory.clientLocation
        self.clientID = self.factory.clientID
        self.logger = self.factory.logger
        self.kinectController.file_sent = 0
        self.pendingFile = None
        self.lastUploadTime = 0
        # self.sender.CHUCK_SIZE = 2 ** 17



    def uptime(self):
        """ Return how long we've been connected to the server. """

        if self.connected:
            return time.time() - self.timeAtConnect
        else:
            return 0

    def synced(self):
        """ True if we're sync'd up, False otherwise. """

        # Delay in seconds until a new client is considered synchronized
        SYNC_DELAY = 5
        # If we're in interactive mode, there's nothing to sync.
        if self.factory.interactiveMode:
            return True
        else:
            return self.uptime() > SYNC_DELAY

    def matchesLocation(self, location):
        """ True if the provided location matches this client's location. """
        return location in ("*", self.clientLocation)

    def matchesID(self, ID):
        """ True if the provided ID matches this client's ID. """
        return ID in ("*", self.clientID)

    def connectionMade(self):
        """ Callback inherited from Twisted. """

        self.logger.info("connected")
        self.factory.client = self
        self.timeAtConnect = time.time()
        if not self.factory.interactiveMode:
            # When we first connect we should sync our settings with the
            # other clients in the room.
            for setting in self.kinectController.settings.keys():
                message = "get %s * %s" % (self.clientLocation, setting)
                self.sendLine(message)

    def connectionLost(self, reason):
        """ Callback inherited from Twisted. """

        self.logger.info("disconnected.")
        reason.printTraceback()



    def upload(self):
        """ Upload tar files in DATA_DIR"""
        now = time.time()
        # TODO test strict condition
        if self.lastUploadTime != 0:
        #if now - self.lastUploadTime < 60:
            self.logger.info("Skip this upload task because the last one is running")
            return
        # get the file list to upload in this turn
        self.uploadFileList = self.__getUploadFileList()
        if len(self.uploadFileList) > 0:
            self.__uploadFile(self.uploadFileList.pop(0))
        """ Manage backup files """
        self.__clearOldBackupFiles()

    def __clearOldBackupFiles(self):
        """ Remove all outofdate backup files """
        for f in os.listdir(BACKUP_DIR):
            if f.endswith(".tar") and self.__outofdate(f):
                filepath = os.path.join(BACKUP_DIR, f)
                os.remove(filepath)
                self.logger.debug("remove outofdate file: " + f)

    def __outofdate(self, filename):
        """ Return True if the file is out of date """
        currDatetime = datetime.fromtimestamp(time.time())
        try:
            fileDatetime = datetime.strptime(filename[:-4], "%Y%m%d%H%M")
        except ValueError:
            return True
        diffInSecs = (currDatetime - fileDatetime).total_seconds()
        if diffInSecs > BACKUP_SIZE_IN_MINS * 60:
            return True
        return False

    def __getUploadFileList(self):
        filelist = []
        for f in os.listdir(DATA_DIR):
            if f.endswith(".tar") and (self.pendingFile == None or f != self.pendingFile):
                filelist.append(f)
        return filelist

    def __uploadFile(self, filename):
        """ upload file in DATA_DIR """
        if filename.endswith(".tar") and len(filename) == 16:
            self.pendingFile = filename
            filepath = os.path.join(DATA_DIR, filename)
            uploadfile = open(filepath, 'rb')
            uploadsize = os.stat(filepath).st_size

            self.logger.info("upload file: " + filename)
            self.sendLine('%s %s %s %s %s' % ("upload",
                                                   self.clientLocation,
                                                   self.clientID,
                                                   filename,
                                                   uploadsize))
            try:
                self.sender = FileSender()
                self.lastUploadTime = time.time()
                d = self.sender.beginFileTransfer(uploadfile, self.transport, self.__monitor)
                d.addCallback(self.uploadCompleted, filename)
            except RuntimeError as e:
                self.logger.warn("__uploadFile|Unexcepted error:" + str(e))
                traceback.print_exc(file=sys.stdout)

        else:
            self.logger.info("invalid upload file: " + filename)

    def uploadCompleted(self, lastsent, filename):
        self.logger.info("upload done: " + filename)
        self.pendingFile = None
        # move currentUploadFile to backup folder
        srcPath = os.path.join(DATA_DIR, filename)
        dstPath = os.path.join(BACKUP_DIR, filename)
        shutil.move(srcPath, dstPath)
        if len(self.uploadFileList) > 0:
            self.__uploadFile(self.uploadFileList.pop(0))
        else:
            self.lastUploadTime = 0

    def __monitor(self, data):
        """ """
        self.kinectController.file_sent += len(data)
        self.kinectController.total_sent += len(data)

        # Check with controller to see if we've been cancelled and abort
        # if so.
        if self.kinectController.cancel:
            self.logger.warn('FileIOClient.__monitor Cancelling')

            # Need to unregister the producer with the transport or it will
            # wait for it to finish before breaking the connection
            self.transport.unregisterProducer()
            self.transport.loseConnection()

            # Indicate a user cancelled result
            self.result = TransferCancelled('User cancelled transfer')

        return data

    def lineReceived(self, line):
        """ Callback inherited from Twisted. """

        self.logger.info("received '%s'" % line)
        arguments = line.split(" ")

        while len(arguments) < 3:
            arguments.append("*")

        # Respond to pings that were sent to us, whether we're in interactive
        # mode or not.

        if self.matchesLocation(arguments[1]) and self.matchesID(arguments[2]):
            if arguments[0] == "ping":
                message = "pong %s %s uptime %d" % \
                    (self.clientLocation, self.clientID, self.uptime())
                self.sendLine(message)

        # Otherwise, only respond if we're not in interactive mode.

        if not self.factory.interactiveMode:

            # When the connection was first established, we queried every client
            # in the room. Copy them if we're not yet considered sync'd.

            if arguments[0] == "response" and len(arguments) == 5:
                sourceLocation = arguments[1]
                if self.matchesLocation(sourceLocation) and not self.synced():
                    setting = arguments[3]
                    value = arguments[4]
                    self.kinectController.set(setting, value)

            # At this point assume we're receiving a command. (Invalid commands
            # are ignored anyway.)

            command = arguments[0].lower()

            if self.matchesLocation(arguments[1]) and self.matchesID(arguments[2]):

                if command == "get":

                    if len(arguments) < 4 or arguments[3] == "*":
                        settings = self.kinectController.settings.keys()
                    else:
                        settings = [arguments[3].lower()]

                    for setting in settings:
                        value = self.kinectController.get(setting)
                        if value is not None and self.synced():
                            message = "response %s %s %s %d" % (self.clientLocation, self.clientID, setting, value)
                            self.sendLine(message)

                elif command == "set" and len(arguments) == 5:
                    setting = arguments[3].lower()
                    value = arguments[4]
                    self.kinectController.set(setting, value)

        # reactor.iterate takes care of pending socket receives and sends
        reactor.iterate()




class KinectClientFactory(ReconnectingClientFactory):
    """ Factory that creates a KinectClient for any outgoing connection.

    There's only one connection at any one time. When the connection fails or
    when a connection is terminated, the client tries to reconnect.

    This factory also stores information that should remain constant between connections. For example, if
    kinectclient.py is run with button mode on, then this factory will store the appropriate Serial object to
    talk to and response to the button. Also, if run in interactive mode, then this factory handles communication with
    the user (which should remain active even when a connection is terminated).
    """

    def __init__(self, kinectController, clientLocation, clientID, interactiveMode=False, buttonMode=False):

        # Reconnect delays in seconds. (Delays grow with the number of retries.)
        self.initialDelay = 1
        self.maxDelay = 300

        self.kinectController = kinectController
        self.clientLocation = clientLocation
        self.clientID = clientID
        self.interactiveMode = interactiveMode
        self.buttonMode = buttonMode
        self.logger = logging.getLogger("KinectClient")
        self.kinectController.logger = self.logger
        self.kinectController.total_sent = 0
        self.kinectController.cancel = False

        # init dirs
        if not os.path.isdir(BACKUP_DIR):
            os.makedirs(BACKUP_DIR)
        if not os.path.isdir(DATA_DIR):
            os.makedirs(DATA_DIR)

        if not self.interactiveMode:
            # Interactive Mode doesn't need init recorder
            self.kinectController.recorder = Recorder(ROOT_DIR, DATA_DIR)

        if self.buttonMode:

            # Try serial ports until we find one that works. (The specific port can change.)
            port_number = 0
            connected = False
            while not connected and port_number < 4:
                port = "/dev/ttyACM%d" % port_number
                try:
                    self.buttonSerial = serial.Serial(port)
                    connected = True
                except serial.SerialException:
                    port_number = port_number + 1

            # If no port was valid, we should error out.
            if not connected:
                print "Button mode specified, but the button couldn't be found."
                sys.exit(-1)

        # This will only be a valid client when connected.
        self.client = None


    def startedConnecting(self, connector):
        """ Callback inherited from Twisted. """
        pass

    def buildProtocol(self, addr):
        """ Callback inherited from Twisted. """

        # If interactive mode is on, interactWithUser is called periodically by Twisted's reactor.
        if self.interactiveMode:
            self.printHelp()
            reactor.callLater(1, self.interactWithUser)
        elif UPLOADER_ON:
            # By default, turn on sync mode with the Server
            # reactor.callLater(SYNC_PERIOD_IN_SECS, self.syncWithServer)
            self.syncTask = task.LoopingCall(self.syncWithServer)
            self.syncTask.start(SYNC_PERIOD_IN_SECS, False)


        # If button mode is on, interactWithButton is called periodically by Twisted's reactor.
        if self.buttonMode:
            reactor.callLater(1, self.interactWithButton)


        return KinectClient(self)

    def clientConnectionLost(self, connector, reason):
        """ Callback inherited from Twisted. """

        self.client = None
        ReconnectingClientFactory.clientConnectionLost(self, connector, reason)

    def clientConnectionFailed(self, connector, reason):
        """ Callback inherited from Twisted. """

        self.logger.info("connection failed")
        self.client = None
        ReconnectingClientFactory.clientConnectionFailed(self, connector, reason)

    def printHelp(self):
        print ""
        print "To exit, type exit or quit."
        print "To get help, type help."
        print "Everything else is relayed to the other clients."
        print ""
        print "commands other clients will understand"
        print "  ping [location] [ID]"
        print "  get <location> <ID> <setting>"
        print "  set <location> <ID> <setting> <new value>"
        print ""
        print "examples"
        print "  ping all clients: ping * *"
        print "  ping all clients located in JHMI-202: ping JHMI-202 *"
        print "  get every client's recording status: get * * recording"
        print "  set every client's recording status to off: set * * recording 0"
        print ""

    def syncWithServer(self):
        self.logger.info("synchronizing with server...")
        try:
            self.client.upload()
        except Exception as e:
            self.logger.warn("syncWithServer|Unexcepted error:" + str(e))
            traceback.print_exc(file=sys.stdout)
        # reactor.iterate takes care of pending socket receives and sends
        # reactor.iterate()

        # reactor.callLater(SYNC_PERIOD_IN_SECS, self.syncWithServer)

    def interactWithUser(self):
        """ Interact with a user.

        If a command is "exit" or "quit," exit. Otherwise, send the command to the server.
        """
        command = raw_input()

        if command.lower() == "exit" or command.lower() == "quit":
            reactor.stop()
            return
        elif command.lower() == "help":
            self.printHelp()
        elif self.client:
            self.client.sendLine(command)
        else:
            print "not connected; command not sent"

        # reactor.iterate takes care of pending socket receives and sends
        reactor.iterate()

        reactor.callLater(0.250, self.interactWithUser)

    def interactWithButton(self):

        # Has the button sent us anything?
        if self.buttonSerial.inWaiting() > 0:

            value = self.buttonSerial.read()

            if value == 'c':
                setting = "consent_acquired"
            elif value == 'r':
                setting = "recording"
            else:
                raise Exception("Received erroneous data from the button.")

            newValue = self.kinectController.toggle(setting)
            self.buttonSerial.write("%d" % newValue)
            self.client.sendLine("set %s * %s %d" % (self.clientLocation, setting, newValue))

            # If we have consent, we should be recording. The only exception to this is if we have been paused. If
            # 30 minutes has elapsed, we should continue recording.
            if self.kinectController.get("consent_acquired") and not self.kinectController.get("recording"):
                elapsedTimeWhileStopped = time.time() - self.kinectController.timeRecordingStopped
                if elapsedTimeWhileStopped > 30*60:
                    self.kinectController.set("recording", True)
                    self.client.sendLine("set %s * recording 1" % self.clientLocation)

        reactor.callLater(0.250, self.interactWithButton)

def signal_handler(signal, frame):
    """ Used to do nothing when we receive certain Unix signals. """
    pass

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
    """ Start the client. """
    if not os.path.isdir(ROOT_DIR):
        os.makedirs(ROOT_DIR)
    initLog()

    # Handle command-line arguments
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-i", "--interactive-mode", action="store_true", default=False,
        help="Run in interactive mode")
    parser.add_argument("-b", "--button-mode", action="store_true", default=False,
        help="Use an external button to start/stop recording")
    parser.add_argument("client_location", help="This client's location. Example: "
        "JHMI-228. If using interactive mode, use something that's informative for "
        "logging. Example: Campus.")
    parser.add_argument("client_ID", help="This client's ID. It should be unique "
        "within a single location. Example: sensor-1. If using interactive mode, "
        "use something that's informative for logging. Example: Rob.")

    if len(sys.argv) < 2:
        parser.print_help()
        sys.exit(-1)

    # Parse command-line arguments. Here we'll have args.interactive_mode, args.button_mode, etc.
    args = parser.parse_args()

    # If we're running in interactive mode, there's nothing to control. Otherwise initiate a KinectController.
    # if args.interactive_mode:
    #     kinectController = None
    # else:
    kinectController = KinectController()

    clientFactory = KinectClientFactory(kinectController, args.client_location, args.client_ID,
                                  args.interactive_mode, args.button_mode)

    # Load the server's self-signed certificate.
    serverCert = open(SERVER_CERT_FILE).read()
    serverCertObj = ssl.Certificate.loadPEM(serverCert)

    # Load the client's private key and self-signed certificate.
    clientKey = open(CLIENT_KEY_FILE).read()
    clientCert = open(CLIENT_CERT_FILE).read()
    clientPEM = clientKey + clientCert
    clientCertObj = ssl.PrivateCertificate.loadPEM(clientPEM)

    # Create an SSL context factory. Passing the server's certificate along enables server authentication.
    contextFactory = clientCertObj.options(serverCertObj)

    # Set up Twisted's reactor to handle outgoing SSL connections. A client is created by the clientFactory for each
    # outgoing connection. (There is only one outgoing connection at any given time, but if the connection is
    # terminated then another is created.) The contextFactory handles the SSL layer.
    reactor.connectSSL(SERVER, PORT, clientFactory, contextFactory)

    if args.interactive_mode:
        # Get rid of Ctrl+C so we disconnect gracefully.
        signal.signal(signal.SIGINT, signal_handler)
    else:
        # Get rid of SIGHUP so our process runs after we logout
        signal.signal(signal.SIGHUP, signal_handler)

    reactor.run()

if __name__ == "__main__":
    main()
