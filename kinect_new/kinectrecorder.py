"""
This module provides an easy-to-use PyOpenNI wrapper for recording data with the Kinect.
"""

import time
import os
from StringIO import StringIO
from datetime import datetime
from threading import Thread
import numpy as np
import Image
import openni as ni
import scipy.misc as sm
import zipfile
import shutil
import sys
import traceback
import tarfile


MODULE_FILE = os.path.abspath(__file__)
MODULE_DIRECTORY = os.path.dirname(MODULE_FILE)

KEY_FILE = os.path.join(MODULE_DIRECTORY, "key.bin")
KEY = np.fromfile(KEY_FILE, dtype=np.int8)

# [height, width]
RESOLUTION = [480, 640]

# Rates are in recorded frames per second.
ADAPTIVE_RECORD_RATE_FAST = 30.0
ADAPTIVE_RECORD_RATE_SLOW = 1.0

ADAPTIVE_RECORD_RATE_CHANGE_DELAY = 120.00 # 2 minutes
""" If we see no change for ADAPTIVE_RECORD_RATE_CHANGE_DELAY seconds, then slow the record rate. """

# Note: If needed in the future, we can save a backlog of images so that we don't miss the first
# few frames after change is detected.

# These values were determined experimentally.

ADAPTIVE_RECORD_RATE_TIME_DELTA = 1.0
""" Time between the two frames that are compared for change detection. """
ADAPTIVE_RECORD_RATE_CHANGE_THRESHOLD = 333
""" The minimum absolute depth difference to consider a single pixel changed. """
ADAPTIVE_RECORD_RATE_PERCENT_CHANGED_THRESHOLD = 1.0
""" The percentage of changed depth pixels required to label an image as changed. """

ZIP_ON = True

class Recorder(object):
    """
    Class to start and stop Kinect recording with registered depth and image views.

    Example:
        # Record for 60 seconds.
        import time
        from kinecty import Recorder
        recorder = Recorder()
        recorder.start()
        time.sleep(60)
        recorder.stop()
    """

    """ The default top-level directory for data storage. """
    recordRate = 30
    """ The (maximum) number of recorded frames per second. """
    adaptiveRecordRate = True
    """ Slow the frame rate down if no change is detected. """

    def __init__(self, ROOT_DIR, DATA_DIR):
        self.DATA_DIR = DATA_DIR
        self.ROOT_DIR = ROOT_DIR
        self.tmpDirectory = os.path.join(self.ROOT_DIR, "tmp")
        self.__recording = False
        self.__depthGenerator = None
        self.__imageGenerator = None
        self.__initOpenNI()

        # By default, obfuscate image files.
        self.obfuscateImages = True

        # Initialize images and times for change detection and for handling the record rate.
        self.__oldDepthData = np.ones(RESOLUTION, np.uint16)
        self.__oldDepthTime = 0
        self.__currentDepthData = np.ones(RESOLUTION, np.uint16)
        self.__currentDepthTime = time.time()
        self.__lastChangeTime = time.time()
        self.__lastRecordTime = 0

    def __initOpenNI(self):
        self.__initOpenNIContext()
        self.__initOpenNIDepthGenerator()
        self.__initOpenNIImageGenerator()

    def __resetOpenNI(self):
        self.__context.stop_generating_all()
        self.__context.shutdown()
        self.__initOpenNI()
        # self.__context.init()
        # self.__initOpenNIDepthGenerator()
        # self.__initOpenNIImageGenerator()

    def __initOpenNIContext(self):
        self.__context = ni.Context()
        self.__context.init()

    def __initOpenNIImageGenerator(self):
        self.__imageGenerator = ni.ImageGenerator()
        self.__imageGenerator.create(self.__context)
        self.__imageGenerator.set_resolution_preset(ni.RES_VGA)
        # If possible, register the depth and image views.
        if self.__depthGenerator:
            self.__depthGenerator.alternative_view_point_cap.set_view_point(self.__imageGenerator)

    def __initOpenNIDepthGenerator(self):
        self.__depthGenerator = ni.DepthGenerator()
        self.__depthGenerator.create(self.__context)
        self.__depthGenerator.set_resolution_preset(ni.RES_VGA)
        # If possible, register the depth and image views.
        if self.__imageGenerator:
            self.__depthGenerator.alternative_view_point_cap.set_view_point(self.__imageGenerator)

    def __startGenerating(self):
        self.__context.start_generating_all()
        # Let the Kinect stabilize before we actually capture data.
        for i in range(0, 30):
            self.__context.wait_and_update_all()

    def __updateRecordRate(self):
        """ Update the adaptive-recording rate based on image change. """

        # If we aren't adapting the record rate, do nothing.
        if not self.adaptiveRecordRate:
            return

        # If the old and current images aren't separated enough in time, do nothing.
        if self.__currentDepthTime - self.__oldDepthTime < ADAPTIVE_RECORD_RATE_TIME_DELTA:
            return

        # Check for change between the old and the current images. If change is observed, update
        # the last-change time.

        good_data_mask = (self.__currentDepthData > 0) & (self.__oldDepthData > 0)
        good_pixel_count = good_data_mask.sum()

        # If there are no good pixels then don't use these frames for change detection. (This can happen when
        # an object gets extremely close to the sensor.
        if good_pixel_count == 0:
            return

        signed_new_data = self.__currentDepthData[good_data_mask].astype(np.int16)
        signed_old_data = self.__oldDepthData[good_data_mask].astype(np.int16)
        difference = np.abs(signed_new_data - signed_old_data)

        changed_pixel_mask = difference > ADAPTIVE_RECORD_RATE_CHANGE_THRESHOLD
        changed_pixel_count = changed_pixel_mask.sum()

        if 100.0 * changed_pixel_count / good_pixel_count > ADAPTIVE_RECORD_RATE_PERCENT_CHANGED_THRESHOLD:
            self.__lastChangeTime = self.__currentDepthTime

        # If the time elapsed since we last observed change is less than a threshold, record quickly. Otherwise,
        # record slowly.
        if self.__currentDepthTime - self.__lastChangeTime < ADAPTIVE_RECORD_RATE_CHANGE_DELAY:
            if self.recordRate != ADAPTIVE_RECORD_RATE_FAST:
                self.logger.info("Recording now: fast rate")
            self.recordRate = ADAPTIVE_RECORD_RATE_FAST
            #self.logger.info(("__lastChangeTime:") + str(self.__lastChangeTime) + "\t__currDepthTime:" + str(self.__currentDepthTime))
        else:
            if self.recordRate != ADAPTIVE_RECORD_RATE_SLOW:
                self.logger.info("Recording now: slow rate")
            self.recordRate = ADAPTIVE_RECORD_RATE_SLOW


        # Replace the old image and update the old image time.
        self.__oldDepthData = self.__currentDepthData
        self.__oldDepthTime = self.__currentDepthTime

    def __start(self):
        """ Start the main, blocking recording loop. """
        self.__lastDirTimeString = ""
        previousTime = time.time()
        previousDatetime = datetime.fromtimestamp(previousTime)
        while self.__recording:

            # Wait for the device to update before we collect data.
            self.__context.wait_and_update_all()

            # Collect any new data that we want to record.

            try:
                rawDepth = self.__depthGenerator.get_raw_depth_map()
                depthData = np.fromstring(rawDepth, np.uint16).reshape(RESOLUTION)
            except ValueError:
                print "Caught ValueError while reading depth."
                traceback.print_exc(file=sys.stdout)
                self.__resetOpenNI()
                self.__startGenerating()
                continue

            try:
                rawImage = self.__imageGenerator.get_raw_image_map()
                imageData = np.fromstring(rawImage, np.uint8).reshape(RESOLUTION + [3])
            except ValueError:
                print "Caught ValueError while reading RGB."
                traceback.print_exc(file=sys.stdout)
                self.__resetOpenNI()
                self.__startGenerating()
                continue

            currentTime = time.time()
            self.__currentDepthData = depthData
            self.__currentDepthTime = currentTime


            # Only record if we're below the record rate.
            record = 1/(currentTime - self.__lastRecordTime) < self.recordRate

            if record:
                """ Do we need to append files within one second into one file? """
                # Examples: 2013-01-01_1210.raw = <file1.name><file1.bmp>...<fileN.name><fileN.bmp>
                self.__saveCurrentImages(depthData, imageData)
            self.__updateRecordRate()

    def __saveCurrentImages(self, depthData, imageData):
        """ save current depth and RGB images """
        currentTime = self.__currentDepthTime
        currentDatetime = datetime.fromtimestamp(currentTime)

        # Example: 201301011210
        directoryTimeString = currentDatetime.strftime("%Y%m%d%H%M")
        # Example: 20130101121005_003
        fileTimeString = currentDatetime.strftime("%Y%m%d%H%M%S_%f")[:-3]

        fullDirectory = os.path.join(self.tmpDirectory, directoryTimeString)
        if not os.path.exists(fullDirectory):
            os.makedirs(fullDirectory)
        else:
            pass
            # empty this folder?

        filePrefix = os.path.join(fullDirectory, fileTimeString)
        # Save depth image first
        depthImage = Image.fromarray(depthData.astype(np.int32), "I")
        depthImage.save(filePrefix + "_depth.png")

        # Then save RGB image
        saveRGB(filePrefix + "_image.jpg", imageData, self.obfuscateImages)
        # TODO when to zip files???
        # print self.__lastRecordTime, currentTime
        if ZIP_ON and self.__lastDirTimeString != "" and  self.__lastDirTimeString != directoryTimeString:
            self.currentTimeString = directoryTimeString
            Thread(target=self.__tarAndDeleteTmpExcept).start()
            # self.__zipFolderToDataDir(directoryTimeString)
            # self.__deleteAllTmpDirExcept(directoryTimeString)
        self.__lastRecordTime = currentTime
        self.__lastDirTimeString = directoryTimeString

    def start(self, logger):
        """ Start recording. """
        self.logger = logger

        if self.__recording:
            return

        # Start the OpenNI data generators.
        self.__startGenerating()

        # Make sure the Kinect has collected some data before we ask for it.
        for i in range(0, 30):
            self.__context.wait_and_update_all()

        # Start recording data in a separate thread (which will stop when _recording is False)
        self.__recording = True
        self.__recordThread = Thread(target=self.__start)
        self.__recordThread.start()

    def stop(self):
        """ Stop recording. """

        if not self.__recording:
            return

        # Stop recording and wait for our thread to terminate.
        self.__recording = False
        self.__recordThread.join()

        # Stop the OpenNI data generators.
        self.__context.stop_generating_all()


    def __tarAndDeleteTmpExcept(self):
        for folder in os.listdir(self.tmpDirectory):
            if folder != self.currentTimeString:
                srcPath = os.path.join(self.tmpDirectory, folder)
                tarPath = os.path.join(self.DATA_DIR, folder + ".tar")
                tarf = tarfile.open(tarPath, 'w')
                for image in os.listdir(srcPath):
                    tarf.add(os.path.join(srcPath, image))
                tarf.close()
                shutil.rmtree(srcPath)
                self.logger.info("create tar file: " + folder + ".tar")


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
