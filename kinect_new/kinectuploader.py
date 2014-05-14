# uploader.py
from paramiko import SSHClient
import paramiko
from scp import SCPClient
import os
from datetime import datetime, date
import logging
import shutil
from scp import SCPException
import argparse
import sys
import time
import subprocess
from time import sleep
BACKUP_SIZE_IN_MINS = 60 * 24 * 5    # five days


server = "rambo.isi.jhu.edu"
port = 22
user = "zad"
password = "968397"

ROOT_DIR = os.path.expanduser("~/kinect")
DATA_DIR = os.path.join(ROOT_DIR, "edata")
BACKUP_DIR = os.path.join(ROOT_DIR, "backup")
LOG_FILE = os.path.join(ROOT_DIR, "uploader" + date.today().strftime("%Y%m%d") + ".log")

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

def createSSHClient(server, port, user, password):
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(server, port, user, password)
    return client

def getUploadFileList():
    filelist = []
    for f in os.listdir(DATA_DIR):
        if f.endswith(".tar"):
            filelist.append(f)
    return filelist

def clearOldBackupFiles():
    """ Remove all outofdate backup files """
    print "enter backup"
    for f in os.listdir(BACKUP_DIR):
        if f.endswith(".tar") and outofdate(f):
            filepath = os.path.join(BACKUP_DIR, f)
            os.remove(filepath)
            logging.info("remove outofdate file: " + f)

def outofdate(filename):
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

""" Start the client. """
if not os.path.isdir(ROOT_DIR):
    os.makedirs(ROOT_DIR)
initLog()

""" Load Client Location and ID """
# Handle command-line arguments
parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
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

files = getUploadFileList()
if len(files) > 0:
    ssh = createSSHClient(server, port, user, password)
    scp = SCPClient(ssh.get_transport())

try:
    for filename in files:
        # Example: filename = 201401012312.zip, day = 20140101, hour = 23
        day = filename[:8]
        hour = filename[8:10]
        remotePath = os.path.join('/data/WICU_DATASET_2014/incoming', args.client_location + "_" + args.client_ID, day, hour)
        filePath = os.path.join(DATA_DIR, filename)
        mkdirCmd = "mkdir -p " + remotePath
        logging.info("run cmd: " + mkdirCmd)
        stdin, stdout, stderr = ssh.exec_command(mkdirCmd)
        # print "stdin", stdin
        # print "stdout", stdout
        # print "stderr", stderr
        sleep(1)
        scp.put(filePath, remote_path=remotePath)
        logging.info("uploaded file " + filename)
        dstPath = os.path.join(BACKUP_DIR, filename)
        shutil.move(filePath, dstPath)
except (SCPException, Exception) as e:
    logging.warn("SCP Exception" + str(e))
clearOldBackupFiles()

print "finished!"
