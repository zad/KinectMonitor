import argparse
import os, sys
import tarfile
from os.path import expanduser
import numpy as np
from StringIO import StringIO
import Image
import shutil
import traceback

MODULE_FILE = os.path.abspath(__file__)
MODULE_DIRECTORY = os.path.dirname(MODULE_FILE)

KEY_FILE = os.path.join(MODULE_DIRECTORY, "key.bin")
KEY = np.fromfile(KEY_FILE, dtype=np.int8)


def main():
    # Handle command-line arguments
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("encrypted", help="Encrypted RGB file")
    parser.add_argument("plain", help="Decrypted RGB file")
    args = parser.parse_args()

    if not args.encrypted or not args.plain:
        parser.print_help()

    try:
        rgbData = loadRGB(args.encrypted, True)
        saveRGB(args.plain, rgbData, False)

    except IOError:
	traceback.print_exc(file=sys.stdout)
#        print "ignore truncated file:" , member.name

def saveRGB(filename, dataArray, obfuscate=True):
    dataImage = Image.fromarray(dataArray)

    fileInMemory = StringIO()
    dataImage.save(fileInMemory, format="JPEG")
    fileContents = fileInMemory.getvalue()

    fileAsData = np.fromstring(fileContents, np.int8)

    if obfuscate:
        bytesRemaining = fileAsData.size
        while bytesRemaining > 0:
            blockStart = fileAsData.size - bytesRemaining
            blockSize = np.minimum(bytesRemaining, KEY.size)
            fileAsData[blockStart:blockStart+blockSize] += KEY[:blockSize]
            bytesRemaining -= blockSize

    fileAsData.tofile(filename)

def loadRGB(filename, obfuscated=True):

    fileAsData = np.fromfile(filename, np.int8)

    if obfuscated:
        bytesRemaining = fileAsData.size
        while bytesRemaining > 0:
            blockStart = fileAsData.size - bytesRemaining
            blockSize = np.minimum(bytesRemaining, KEY.size)
            fileAsData[blockStart:blockStart+blockSize] -= KEY[:blockSize]
            bytesRemaining -= blockSize

    fileInMemory = StringIO(fileAsData.tostring())

    dataImage = Image.open(fileInMemory)

    # These tricks are necessary because PIL behaves differently when you use an IOString
    # object instead of an actual file object.
    dataArray = np.fromstring(str(dataImage.tostring()), dtype=np.uint8)
    dataArray = dataArray.reshape([dataImage.size[1], dataImage.size[0], 3])

    fileInMemory.close()

    return dataArray

if __name__ == "__main__":
    main()
