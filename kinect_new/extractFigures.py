import argparse
import os, sys
import tarfile
from os.path import expanduser
import numpy as np
from StringIO import StringIO
import Image
import shutil

MODULE_FILE = os.path.abspath(__file__)
MODULE_DIRECTORY = os.path.dirname(MODULE_FILE)

KEY_FILE = os.path.join(MODULE_DIRECTORY, "key.bin")
KEY = np.fromfile(KEY_FILE, dtype=np.int8)


def main():
    # Handle command-line arguments
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("rgb_folder", help="This is the folder holding RGB files")
    parser.add_argument("-r", "--remove", help="Remove extracted images within the directory", action="store_true", default=False)
    parser.add_argument("-v", "--verbose", help="Show verbose information", action="store_true", default=False)
    parser.add_argument("-d", "--directory", help="Assign the directory for images")
    parser.add_argument("-s", "--sampling", help="sampling method, e.g., default is minute")
    parser.add_argument("-u", "--update", help="update mode, i.e., do not remove existing files", action="store_true", default=False)
    args = parser.parse_args()

    if not args.rgb_folder:
        parser.print_help()

    sampling = "minute"
    if args.sampling:
        sampling = args.sampling

    for root, dirs, files in os.walk(args.rgb_folder):
        for file in files:
            if file.endswith("tar"):
                print root
                print file
                if args.directory:
                    outdir = args.directory
                else:
                    outdir = root.replace("edata/WICU_DATASET_2014/incoming","edata/WICU_DATASET_2014_SAMPLE_" + sampling)
                tar = tarfile.open(os.path.join(root, file))
                depth_dir = os.path.join(outdir, "depth")
                rgb_dir = os.path.join(outdir, "rgb")
                if args.remove:
                    if os.path.isdir(depth_dir):
                        shutil.rmtree(depth_dir)
                    if os.path.isdir(rgb_dir):
                        shutil.rmtree(rgb_dir)
                else:
                    if not os.path.isdir(depth_dir):
                        os.makedirs(depth_dir)
                    if not os.path.isdir(rgb_dir):
                        os.makedirs(rgb_dir)
                    depthReady = False
                    imageReady = False
                    depthFiles = os.listdir(depth_dir)
                    imageFiles = os.listdir(rgb_dir)
                    if len(depthFiles) > 0:
                        for f in depthFiles:
                            if f.startswith(file[:-4]) and f.endswith("depth.png"):
                                depthReady = True
                                break
                    if len(imageFiles) > 0:
                        for f in imageFiles:
                            if f.startswith(file[:-4]) and f.endswith("image.jpg"):
                                imageReady = True
                                break
                    if args.update and (imageReady or depthReady):
                        print "File exists."
                    else:
                        for member in tar.getmembers():
                            member.name = os.path.basename(member.name)
                            if args.verbose:
                                print member.name
                            if member.name.endswith("depth.png") and not depthReady:
                                tar.extract(member, path=depth_dir)
                                depthReady = True
                            elif member.name.endswith("image.jpg") and not imageReady:
                                tar.extract(member, path=rgb_dir)
                                # try:
                                #     rgbFile = os.path.join(rgb_dir, member.name)
                                #     rgbData = loadRGB(rgbFile, True)
                                #     saveRGB(rgbFile, rgbData, False)
                                imageReady = True
                                # except IOError:
                                #     print "ignore truncated file:", rgb_dir, member.name
                            if sampling == "minute":
                                if depthReady and imageReady:
                                    break;

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
