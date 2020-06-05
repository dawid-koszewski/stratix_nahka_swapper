#!/usr/bin/python

#-------------------------------------------------------------------------------
# author:   dawid.koszewski@nokia.com
# date:     2019.10.30
# update:   2019.11.12
# version:  01o
#
# written in Notepad++
#
#
#-------------------------------------------------------------------------------


import os
import re
import shutil
import subprocess
import sys
import tarfile
import time
import zlib


try:
    import requests
except ImportError as e:
    print("%s" % e)
    print("Script will now attempt to install required module: %s" % e.name)
    pressEnterToContinue()
    subprocess.run('pip install requests')
import requests


#import urllib.request

# try:
    # import wget
# except ImportError as e:
    # print("%s" % e)
    # print("Script will now attempt to install required module: %s" % e.name)
    # pressEnterToContinue()
    # subprocess.run('pip install wget')
# import wget


#-------------------------------------------------------------------------------


################################################################################
#                                                                              #
# shutil LIBRARY functions BELOW by:                                           #
#                                                                              #
# author:   doko@ubuntu.com                                                    #
# date:     Thu, 30 Apr 2015 13:44:18 +0200 (2015-04-30)                       #
# link:     https://hg.python.org/cpython/file/eb09f737120b/Lib/shutil.py      #
#                                                                              #
################################################################################

"""Utility functions for copying and archiving files and directory trees.

XXX The functions here don't copy the resource fork or other metadata on Mac.

"""

import stat


# def copyfileobj(fsrc, fdst, length=16*1024):
    # """copy data from file-like object fsrc to file-like object fdst"""
    # while 1:
        # buf = fsrc.read(length)
        # if not buf:
            # break
        # fdst.write(buf)

def _samefile(src, dst):
    # Macintosh, Unix.
    if hasattr(os.path, 'samefile'):
        try:
            return os.path.samefile(src, dst)
        except OSError:
            return False

    # All other platforms: check for same pathname.
    return (os.path.normcase(os.path.abspath(src)) ==
            os.path.normcase(os.path.abspath(dst)))

def copyfile(src, dst, *, follow_symlinks=True):
    """Copy data from src to dst.

    If follow_symlinks is not set and src is a symbolic link, a new
    symlink will be created instead of copying the file it points to.

    """
    if _samefile(src, dst):
        raise SameFileError("{!r} and {!r} are the same file".format(src, dst))

    for fn in [src, dst]:
        try:
            st = os.stat(fn)
        except OSError:
            # File most likely does not exist
            pass
        else:
            # XXX What about other special files? (sockets, devices...)
            if stat.S_ISFIFO(st.st_mode):
                raise SpecialFileError("`%s` is a named pipe" % fn)

    if not follow_symlinks and os.path.islink(src):
        os.symlink(os.readlink(src), dst)
    else:
        with open(src, 'rb') as fsrc:
            with open(dst, 'wb') as fdst:
                #copyfileobj(fsrc, fdst)
                #copyfileobj(fsrc, fdst, printProgress, src) # MODIFIED TO CALL USER DEFINED FUNCTION (dawid.koszewski@nokia.com)
                copyfileobj(fsrc, fdst, src)
    return dst


if hasattr(os, 'listxattr'):
    def _copyxattr(src, dst, *, follow_symlinks=True):
        """Copy extended filesystem attributes from `src` to `dst`.

        Overwrite existing attributes.

        If `follow_symlinks` is false, symlinks won't be followed.

        """

        try:
            names = os.listxattr(src, follow_symlinks=follow_symlinks)
        except OSError as e:
            if e.errno not in (errno.ENOTSUP, errno.ENODATA):
                raise
            return
        for name in names:
            try:
                value = os.getxattr(src, name, follow_symlinks=follow_symlinks)
                os.setxattr(dst, name, value, follow_symlinks=follow_symlinks)
            except OSError as e:
                if e.errno not in (errno.EPERM, errno.ENOTSUP, errno.ENODATA):
                    raise
else:
    def _copyxattr(*args, **kwargs):
        pass

def copystat(src, dst, *, follow_symlinks=True):
    """Copy all stat info (mode bits, atime, mtime, flags) from src to dst.

    If the optional flag `follow_symlinks` is not set, symlinks aren't followed if and
    only if both `src` and `dst` are symlinks.

    """
    def _nop(*args, ns=None, follow_symlinks=None):
        pass

    # follow symlinks (aka don't not follow symlinks)
    follow = follow_symlinks or not (os.path.islink(src) and os.path.islink(dst))
    if follow:
        # use the real function if it exists
        def lookup(name):
            return getattr(os, name, _nop)
    else:
        # use the real function only if it exists
        # *and* it supports follow_symlinks
        def lookup(name):
            fn = getattr(os, name, _nop)
            if fn in os.supports_follow_symlinks:
                return fn
            return _nop

    st = lookup("stat")(src, follow_symlinks=follow)
    mode = stat.S_IMODE(st.st_mode)
    lookup("utime")(dst, ns=(st.st_atime_ns, st.st_mtime_ns),
        follow_symlinks=follow)
    try:
        lookup("chmod")(dst, mode, follow_symlinks=follow)
    except NotImplementedError:
        # if we got a NotImplementedError, it's because
        #   * follow_symlinks=False,
        #   * lchown() is unavailable, and
        #   * either
        #       * fchownat() is unavailable or
        #       * fchownat() doesn't implement AT_SYMLINK_NOFOLLOW.
        #         (it returned ENOSUP.)
        # therefore we're out of options--we simply cannot chown the
        # symlink.  give up, suppress the error.
        # (which is what shutil always did in this circumstance.)
        pass
    if hasattr(st, 'st_flags'):
        try:
            lookup("chflags")(dst, st.st_flags, follow_symlinks=follow)
        except OSError as why:
            for err in 'EOPNOTSUPP', 'ENOTSUP':
                if hasattr(errno, err) and why.errno == getattr(errno, err):
                    break
            else:
                raise
    _copyxattr(src, dst, follow_symlinks=follow)


def copy2(src, dst, *, follow_symlinks=True):
    if os.path.isdir(dst):
        dst = os.path.join(dst, os.path.basename(src))
    copyfile(src, dst, follow_symlinks=follow_symlinks)
    copystat(src, dst, follow_symlinks=follow_symlinks)
    return dst


################################################################################
#                                                                              #
# shutil LIBRARY functions ABOVE by:                                           #
#                                                                              #
# author:   doko@ubuntu.com                                                    #
# date:     Thu, 30 Apr 2015 13:44:18 +0200 (2015-04-30)                       #
# link:     https://hg.python.org/cpython/file/eb09f737120b/Lib/shutil.py      #
#                                                                              #
################################################################################







#==============================================================================#
#                                                                              #
#                                  MAIN CODE                                   #
#                                                                              #
#==============================================================================#

#-------------------------------------------------------------------------------


#===============================================================================
# custom implementation of copyfileobj from shutil LIBRARY (enable displaying copy file progress)
#===============================================================================

#def copyfileobj(fsrc, fdst, callback, src, length=16*1024):
def copyfileobj(fsrc, fdst, src, length=16*1024):
    fileSize = os.stat(src).st_size
    tmp = 0
    copied = 0
    step = 131072
    time0 = time.time()
    time1Tmp = time.time()
    time2 = 0
    timeStep = 1.0
    time1TmpData = 0
    speedCur = 1048576.0
    speedAvg = 1048576.0
    while 1:
        buf = fsrc.read(length)
        if not buf:
            break
        fdst.write(buf)
        copied += len(buf)
        time2 = time.time()
        if time2 >= (time1Tmp + timeStep):
            timeDiff21 = time2 - time1Tmp #can differ slightly from timeStep
            dataDiff21 = copied - time1TmpData
            time1Tmp = time2
            time1TmpData = copied
            if timeDiff21 == 0:
                timeDiff21 = 0.1
            speedCur = (dataDiff21 / timeDiff21) #Bytes per second
        if copied >= (tmp + step):
            tmp = copied
            timeDiff20 = time2 - time0
            if timeDiff20 == 0:
                timeDiff20 = 0.1
            speedAvg = (copied / timeDiff20) #Bytes per second
            printProgress(copied, fileSize, speedCur, speedAvg)
    printProgress(copied, fileSize, speedCur, speedAvg)
    print()

#-------------------------------------------------------------------------------


#===============================================================================
# functions to print progress bar
#===============================================================================

def getUnit(variable):
    units = ['kB', 'MB', 'GB', 'TB']
    variableUnit = ' B'
    for unit in units:
        if variable > 1000:
            variable /= 1024
            variableUnit = unit
        else:
            break
    return variable, variableUnit


def printProgress(copied, fileSize, speedCur = 1048576.0, speedAvg = 1048576.0):
    percent = (copied / fileSize) * 100
    dataLeft = (fileSize - copied) #Bytes
    timeLeftSeconds = (dataLeft / speedAvg) #Seconds

    timeLeftHours = timeLeftSeconds / 3600
    timeLeftSeconds = timeLeftSeconds % 3600
    timeLeftMinutes = timeLeftSeconds / 60
    timeLeftSeconds = timeLeftSeconds % 60

    #padding = len(str(int(fileSize)))
    copied, copiedUnit = getUnit(copied)
    fileSize, fileSizeUnit = getUnit(fileSize)
    speedCur, speedCurUnit = getUnit(speedCur)

    symbolDone = '='
    symbolLeft = '-'
    sizeTotal = 20
    sizeDone = int((percent / 100) * sizeTotal)
    sizeLeft = sizeTotal - sizeDone
    progressBar = '[' + sizeDone*symbolDone + sizeLeft*symbolLeft + ']'
    sys.stdout.write('\r%3d%% %s [%3.1d%s/%3.1d%s]  [%6.2f%s/s] %3.1dh%2.2dm%2.2ds' % (percent, progressBar, copied, copiedUnit, fileSize, fileSizeUnit, speedCur, speedCurUnit, timeLeftHours, timeLeftMinutes, timeLeftSeconds))
    sys.stdout.flush()
    #time.sleep(0.01) #### DELETE AFTER DEVELOPMENT ##########################################################################################################

#-------------------------------------------------------------------------------


#===============================================================================
# utility functions
#===============================================================================

def pressEnterToExit():
    input("\nPress Enter to exit...\n")
    sys.exit()


def pressEnterToContinue():
    input("\nPress Enter to continue...\n")


def printSelectedFile(pathToFile, name):
    nameLength = len(name)
    print('\n\n\
======================' + nameLength*'=' + '\n\
=== selected %s file ===\n\
======================' % (name) + nameLength*'=' + '\n\n%s\n' % (pathToFile))


def printNewFile(fileName, name):
    nameLength = len(name)
    print('\n\n\n\
=================' + nameLength*'=' + '\n\
=== new Stratix file ===\n\
=================' + nameLength*'=' + '\n\n%s\n' % (fileName))


def isTarfileGood(pathToFileInRes):
    try:
        with tarfile.open(pathToFileInRes, 'r') as tar:
            members = tar.getmembers()
        return True
    except (tarfile.TarError) as e:
        #print("\nTarfile corrupted ERROR: %s in:\n%s\n" % (e, pathToFileInRes))
        return False
    except (Exception) as e:
        #print("\nTarfile ERROR: %s in:\n%s\n" % (e, pathToFileInRes))
        return False
    return False


def extractTarfile(pathToDir, pathToFileInRes):
    try:
        with tarfile.open(pathToFileInRes, 'r') as tar:
            tar.extractall(path = pathToDir)
    except (tarfile.TarError) as e:
        print("\nTarfile extraction ERROR: %s in:\n%s\n" % (e, pathToFileInRes))
        pressEnterToExit()
    except (Exception) as e:
        print("\nTarfile extraction ERROR: %s in:\n%s\n" % (e, pathToFileInRes))
        pressEnterToExit()


def createTarfile(pathToDir, fileName):
    try:
        with tarfile.open(fileName, 'w') as tar:
            for item in os.listdir(pathToDir):
                tar.add(os.path.join(pathToDir, item), arcname = item)
    except (tarfile.TarError) as e:
        print("\nTarfile creation ERROR: %s in:\n%s\n" % (e, fileName))
        pressEnterToExit()
    except (Exception) as e:
        print("\nTarfile creation ERROR: %s in:\n%s\n" % (e, fileName))
        pressEnterToExit()


def createDir(pathToDir):
    if not os.path.exists(pathToDir):
        try:
            os.mkdir(pathToDir)
        except (OSError) as e:
            print("\nDirectory creation ERROR: %s - %s\n" % (e.filename, e.strerror))
        except (Exception) as e:
            print("\nDirectory creation ERROR: %s\n" % (e))


def removeDir(pathToDir):
    if os.path.exists(pathToDir):
        try:
            shutil.rmtree(pathToDir)
        except (shutil.Error, OSError, IOError, Exception) as e:
            print("\nDirectory removal ERROR: %s\n" % (e))


def renameFile(fileNameOld, fileNameNew):
    try:
        os.rename(fileNameOld, fileNameNew)
    except (OSError) as e:
        print("\nFile rename ERROR: %s - %s\n" % (e.filename, e.strerror))
    except (Exception) as e:
        print("\nFile rename ERROR: %s\n" % (e))


def removeFile2(pathToDir, fileName):
    try:
        os.remove(os.path.join(pathToDir, fileName))
        print("\n\n%s deleted from:\t%s" % (fileName, pathToDir))
    except (OSError) as e:
        print("\nFile remove ERROR: %s - %s\n" % (e.filename, e.strerror))
    except (Exception) as e:
        print("\nFile remove ERROR: %s\n" % (e))


def removeFile(pathToFile):
    pathToDir = os.path.dirname(pathToFile)
    fileName = os.path.basename(pathToFile)
    try:
        os.remove(pathToFile)
        print("%s deleted from:\t%s" % (fileName, pathToDir))
    except (OSError) as e:
        print("\nFile remove ERROR: %s - %s\n" % (e.filename, e.strerror))
    except (Exception) as e:
        print("\nFile remove ERROR: %s\n" % (e))


def listDirectory(pathToDir):
    listDir = []
    try:
        listDir = os.listdir(pathToDir)
    except (OSError) as e:
        print("\nDirectory listing ERROR: %s - %s\n" % (e.filename, e.strerror))
        pressEnterToExit()
    except (Exception) as e:
        print("\nDirectory listing ERROR: %s\n" % (e))
        pressEnterToExit()
    return listDir

#-------------------------------------------------------------------------------


#===============================================================================
# functions to calculate checksum
#===============================================================================

def getChecksumUsingZutil(fileNameTemp, fileMatcher, path_to_zutil):
    fileNameNew = ""
    if os.path.isfile(fileNameTemp):
        try:
            zutilOutput = subprocess.check_output('%s adler32 %s' % (path_to_zutil, fileNameTemp)).decode(sys.stdout.encoding).strip()
            #print('\nzutil output:\n%s\n' % (zutilOutput))

            fileNamePrepend = fileMatcher.sub(r'\1', fileNameTemp)
            fileNameAppend = fileMatcher.sub(r'\4', fileNameTemp)
            checksumNew = fileMatcher.sub(r'\3', zutilOutput).upper()
            fileNameNew = fileNamePrepend + '0x' + checksumNew + filenameAppend
        except (Exception) as e:
            print ("\nCalculate checksum ERROR: %s\n" % (e))
    else:
        print('\nERROR: Could not find new stratix image file to calculate checksum\n')
    return fileNameNew


def getChecksum(fileNameTemp, fileMatcher):
    fileNameNew = ""
    if os.path.isfile(fileNameTemp):
        try:
            f = open(fileNameTemp, 'rb')
            checksum = 1
            buffer = f.read(1024)
            while buffer: #len(buffer) > 0:
                checksum = zlib.adler32(buffer, checksum)
                buffer = f.read(1024)
            f.close()
            checksum = checksum & 0xffffffff
            #print("%d %s" % (checksum, (hex(checksum))))

            fileNamePrepend = fileMatcher.sub(r'\1', fileNameTemp)
            fileNameAppend = fileMatcher.sub(r'\4', fileNameTemp)
            checksumNew = fileMatcher.sub(r'\3', hex(checksum)).upper()
            fileNameNew = fileNamePrepend + '0x' + checksumNew + fileNameAppend
        except (OSError, IOError) as e:
            print ("\nCalculate checksum ERROR: %s - %s\n" % (e.filename, e.strerror))
        except (Exception) as e:
            print ("\nCalculate checksum ERROR: %s\n" % (e))
    else:
        print('\nERROR: Could not find new stratix image file to calculate checksum\n')
    return fileNameNew

#-------------------------------------------------------------------------------


#===============================================================================
# functions to get paths to latest Nahka and Stratix files
#===============================================================================

def createNewIniFile(pathToFile):
    try:
        with open(pathToFile, 'w') as f:
            f.write("\n\
The script will search this file line by line looking for the last occurrence of Nahka or Stratix image files.\n\n\
\
You can find example in the list below:\n\n\
i:\\some_user\\stratix10-aaib\\tmp-glibc\\deploy\\images\\stratix10-aaib\\\n\
v:\\some_user\\nahka\\tmp\\deploy\\images\\nahka\\FRM-rfsw-image-install_20190231120000-multi.tar\n\
v:\\some_user\\nahka\\tmp\\deploy\\images\\nahka\n\
https://artifactory-espoo1.int.net.nokia.com/artifactory/mnprf_brft-local/mMIMO_FDD/FB1813_Z/PROD_mMIMO_FDD_FB1813_Z_release/1578/C_Element/SE_RFM/SS_mMIMO_FDD/Target/SRM-rfsw-image-install_z-uber-0xFFFFFFFF.tar\n\
C:\\LocalDir\n\n\
\
1. if C:\\LocalDir contains Nahka file it will copy it and download Stratix file from artifactory\n\
2. if C:\\LocalDir is empty it will copy newest Nahka file from v:\\some_user\\nahka\\tmp\\deploy\\images\\nahka directory and download Stratix file from artifactory\n\
3. but if C:\LocalDir contains Nahka and Stratix image it will copy both of them from C:\\LocalDir\n\n\
\
You can keep a lot of helper links in this file but remember to put them above the ones desired for current build.\n\
Script will always save the last found occurrence of Nahka or Stratix file location - so place your desired links at the very bottom!!!\n\n\
\
. - if you will put only this dot at the end of this file you are explicitly telling this script to do the final search for Nahka and Stratix files in the current working directory.\n\n\
\
If you will delete this file - a new one will be created.\n\n\
\
You can now put your links below (you can also delete this whole message - not recommended).\n\n\n\
")
    except (IOError) as e:
        print("\nInifile creation ERROR: %s - %s\n" % (e.filename, e.strerror))


def loadIniFileIntoList(pathToFile):
    if os.path.isfile(pathToFile):
        try:
            with open(pathToFile, 'r') as f:
                return f.readlines()
        except (IOError) as e:
            print("\nInifile loading ERROR: %s - %s\n" % (e.filename, e.strerror))
    print("\nInitialization file not found...\n")
    print("%s file has been created!!!" % (pathToFile))
    print("now you will be able to specify location of Nahka and Stratix files in there\n")
    print("In the first run this script will search for Nahka and Stratix files in the current working directory (%s)\n" % (os.path.dirname(os.path.realpath(sys.argv[0]))))
    print("Every next time it will search for Nahka and Stratix files in locations defined by you in the ini file...\n")
    pressEnterToContinue()
    createNewIniFile(pathToFile)
    return []


def getDateFromNahkaFile(fileMatcher):
    return lambda f : fileMatcher.sub(r'\2', f)


def getLastModificationTime(pathToFile):
    secondsSinceEpoch = 0
    try:
        secondsSinceEpoch = os.path.getmtime(pathToFile)
    except (OSError) as e:
        print("\nGetting file info ERROR: %s - %s\n" % (e.filename, e.strerror))
        pressEnterToExit()
    return secondsSinceEpoch


def getLastModificationTimeAsString(pathToFile):
    return time.ctime(getLastModificationTime(pathToFile))


def getPathToLatestFileInDir(pathToDir, matcher, comparator):
    filesList = []
    for item in os.listdir(pathToDir):
        pathToFile = os.path.join(pathToDir, item)
        if os.path.isfile(pathToFile):
            if matcher.search(item):
                filesList.append(pathToFile)
    filesList.sort(key = comparator, reverse = False)
    return filesList[-1] if filesList else ""


def getPathsToLatestFiles(pathToFileIni, fileMatcherNahka, fileMatcherStratix, pathMatcherStratix):
    pathToFileNahka = ""
    pathToFileStratix = ""
    iniFileLinesList = loadIniFileIntoList(pathToFileIni)
    if iniFileLinesList:
        for line in iniFileLinesList:
            line = line.strip()
            if fileMatcherNahka.search(line):
                pathToFileNahka = line
            elif fileMatcherStratix.search(line):
                pathToFileStratix = line
            elif os.path.isdir(line):
                if not pathMatcherStratix.search(line):
                    pathToLatestFileInDirNahka = getPathToLatestFileInDir(line, fileMatcherNahka, getDateFromNahkaFile(fileMatcherNahka))
                    if pathToLatestFileInDirNahka:
                        pathToFileNahka = pathToLatestFileInDirNahka
                pathToLatestFileInDirStratix = getPathToLatestFileInDir(line, fileMatcherStratix, getLastModificationTime)
                if pathToLatestFileInDirStratix:
                    pathToFileStratix = pathToLatestFileInDirStratix
    else:
        pathToFileNahka = getPathToLatestFileInDir('.', fileMatcherNahka, getDateFromNahkaFile(fileMatcherNahka))
        pathToFileStratix = getPathToLatestFileInDir('.', fileMatcherStratix, getLastModificationTime)
    pathsToLatestFiles = {}
    pathsToLatestFiles['pathToLatestFileNahka'] = pathToFileNahka
    pathsToLatestFiles['pathToLatestFileStratix'] = pathToFileStratix
    return pathsToLatestFiles

#-------------------------------------------------------------------------------


#===============================================================================
# functions to copy / download Nahka and Stratix files
#===============================================================================

def getFileFromArtifactory(pathToFile, pathToFileInRes):
    try:
        response = requests.get(pathToFile, stream = True)
        response.raise_for_status()

        print("downloading file to %s" % os.path.dirname(pathToFileInRes))

        fileSize = int(response.headers['Content-length'])
        with open(pathToFileInRes, 'wb') as f:
            tmp = 0
            copied = 0
            step = 131072
            time0 = time.time()
            time1Tmp = time.time()
            time2 = 0
            timeStep = 1.0
            time1TmpData = 0
            speedCur = 1048576.0
            speedAvg = 1048576.0
            buffer = response.raw.read(128)
            copied += len(buffer)
            while buffer:
                f.write(buffer)
                buffer = response.raw.read(128)
                copied += len(buffer)
                time2 = time.time()
                if time2 >= (time1Tmp + timeStep):
                    timeDiff21 = time2 - time1Tmp #can differ slightly from timeStep
                    dataDiff21 = copied - time1TmpData
                    time1Tmp = time2
                    time1TmpData = copied
                    if timeDiff21 == 0:
                        timeDiff21 = 0.1
                    speedCur = (dataDiff21 / timeDiff21) #Bytes per second
                if copied >= (tmp + step):
                    tmp = copied
                    timeDiff20 = time2 - time0
                    if timeDiff20 == 0:
                        timeDiff20 = 0.1
                    speedAvg = (copied / timeDiff20) #Bytes per second
                    printProgress(copied, fileSize, speedCur, speedAvg)
            printProgress(copied, fileSize, speedCur, speedAvg)
        print()
    except (requests.exceptions.HTTPError, requests.exceptions.RequestException, Exception) as e:
        print("\nFile download ERROR: %s\n" % (e))
        pressEnterToExit()
    except (IOError) as e:
        print("\nFile download ERROR: %s - %s\n" % (e.filename, e.strerror))
        pressEnterToExit()


def getFileFromNetwork(pathToFile, pathToDirRes):
    print("copying file to %s" % (pathToDirRes))
    try:
        #shutil.copy2(pathToFile, pathToDirRes)
        copy2(pathToFile, pathToDirRes)
    except (shutil.Error, OSError, IOError, Exception) as e:
        print("\nFile copy ERROR: %s\n" % (e))
        pressEnterToExit()


def getFile(pathToFile, pathIsUrl, pathToDirRes, pathToFileInRes):
    createDir(pathToDirRes)
    if pathIsUrl:
        getFileFromArtifactory(pathToFile, pathToFileInRes)
    else:
        getFileFromNetwork(pathToFile, pathToDirRes)


def isFileInResources(pathToFileInRes):
    return os.path.isfile(pathToFileInRes)


def isFileAvailable(pathToFile, pathIsUrl):
    if pathIsUrl:
        try:
            response = requests.head(pathToFile)
            print('modified: %s (on server)\n' % (response.headers['last-modified']))
            return response.status_code == (200 or 300 or 301 or 302 or 303 or 307 or 308) # statement must be in parentheses...
        except (requests.exceptions.HTTPError, requests.exceptions.RequestException, Exception) as e:
            print("%s\n\nYou probably need authentication to download that file...\n" % (e))
            return False
    else:
        if os.path.isfile(pathToFile):
            print('modified: %s\n' % (getLastModificationTimeAsString(pathToFile)))
            return True
    return False


def getFileNameFromURL(pathToFile, fileMatcher):
    fileName = ""
    try:
        fileName = fileMatcher.sub(r'\1\2\3', pathToFile)
    except (re.error, Exception) as e:
        print("\n%s\n\nGetting file name from URL ^^^ABOVE ERROR: %s\n(Please specify correct fileMatcher as 5th parameter in \"handleGettingFile\" function)" % (pathToFile, e))
    return fileName


def getPathToFileInRes(pathToFile, pathIsUrl, pathToDirRes, fileMatcher):
    pathToFileInRes = ""
    if pathIsUrl:
        fileName = getFileNameFromURL(pathToFile, fileMatcher)
        pathToFileInRes = os.path.join(pathToDirRes, fileName)
    else:
        fileName = os.path.basename(pathToFile)
        pathToFileInRes = os.path.join(pathToDirRes, fileName)
    return pathToFileInRes


def isPathUrl(pathToFile, urlMatcher):
    return urlMatcher.search(pathToFile)


def handleGettingFile(pathToFile, pathToDirRes, name, urlMatcher, fileMatcher = None):
    pathIsUrl = isPathUrl(pathToFile, urlMatcher)
    pathToFileInRes = getPathToFileInRes(pathToFile, pathIsUrl, pathToDirRes, fileMatcher)

    printSelectedFile(pathToFile, name)

    fileIsAvailable = isFileAvailable(pathToFile, pathIsUrl)
    fileIsInResources = isFileInResources(pathToFileInRes)
    fileIsGood = isTarfileGood(pathToFileInRes)

    if fileIsAvailable:
        if fileIsInResources:
            if fileIsGood:
                print("file already present in %s\n" % (pathToDirRes))
            else:
                print("file already present in the %s but it is corrupted - attempting to get a fresh new copy\n" % (pathToDirRes))
                getFile(pathToFile, pathIsUrl, pathToDirRes, pathToFileInRes)
        else:
            getFile(pathToFile, pathIsUrl, pathToDirRes, pathToFileInRes)
    elif fileIsInResources:
        if fileIsGood:
            print("Could not find the file in the specified location, but the file is present in %s\n" % (pathToDirRes))
            pressEnterToContinue()
        else:
            print("Could not find file in the specified location - the file is present in %s but it is corrupted\n" % (pathToDirRes))
            pressEnterToExit()
    else:
        print("Could not find anything! Please specify possible file locations in the ini file...\n")
        pressEnterToExit()
    return pathToFileInRes

#-------------------------------------------------------------------------------


#===============================================================================
# functions to modify Stratix file with customized nahka file
#===============================================================================

def replaceFileInArtifacts(pathToDirTempArtifacts, pathToFileInRes, fileMatcher):
    listDirTempArtifacts = listDirectory(pathToDirTempArtifacts)
    for tempFileArtifacts in listDirTempArtifacts:
        if fileMatcher.search(tempFileArtifacts):
            removeFile2(pathToDirTempArtifacts, tempFileArtifacts)
    try:
        shutil.copy2(pathToFileInRes, pathToDirTempArtifacts)
        print("%s copied to:\t%s" % (os.path.basename(pathToFileInRes), pathToDirTempArtifacts))
    except (shutil.Error, OSError, IOError, Exception) as e:
        print("\nFile copy ERROR: %s\n" % (e))
        pressEnterToExit()


def setNewFileNameInInstallerScripts(pathToDirTemp, pathToFileInRes, fileMatcherInstaller, fileMatcher):
    fileName = os.path.basename(pathToFileInRes)
    listDirTemp = listDirectory(pathToDirTemp)
    for tempFile in listDirTemp:
        tempFilePath = os.path.join(pathToDirTemp, tempFile)
        if os.path.isfile(tempFilePath):
            if fileMatcherInstaller.search(tempFile):
                try:
                    with open(tempFilePath, 'r') as f:
                        fileContent = f.read()
                        fileContent = fileMatcher.sub(fileName, fileContent)
                except (IOError) as e:
                    print("\nInstaller script reading ERROR: %s - %s\n" % (e.filename, e.strerror))
                try:
                    with open(tempFilePath, 'w') as f:
                        f.write(fileContent)
                except (IOError) as e:
                    print("\nInstaller script writing ERROR: %s - %s\n" % (e.filename, e.strerror))
                print("%s updated in:\t%s" % (fileName, tempFilePath))


def renameStratixFile(fileNameTemp, fileNameNew):
    renameFile(fileNameTemp, fileNameNew)
    if os.path.isfile(fileNameNew) and os.path.getsize(fileNameNew) > 0:

        printNewFile(fileNameNew, 'Stratix')

        print('modified: %s\n' % (getLastModificationTimeAsString(fileNameNew)))
    else:
        print("\nSomething went wrong. New Stratix file not generated correctly\n")

#-------------------------------------------------------------------------------


#===============================================================================
# === MAIN FUNCTION ===
#===============================================================================

def main():
    # path_to_zutil = 'C:\zutil\zutil.exe'
    # if len(sys.argv) == 2:
        # path_to_zutil = sys.argv[1]

    pathToFileIni = r'.\stratix_nahka_swapper.ini'
    pathToDirRes = r'.\resources'
    pathToDirTemp = r'.\SRM_temp'
    pathToDirTempArtifacts = r'.\SRM_temp\artifacts'
    fileNameStratixTemp = r'.\SRM-rfsw-image-install_z-uber-0x00000000.tar'

    urlMatcher = re.compile(r'(https://|http://|ftp://)')
    fileMatcher = re.compile(r'(.*)(0x)([a-fA-F0-9]{8})(.*)')
    fileMatcherNahka = re.compile(r'(FRM-rfsw-image-install_)([0-9]{14})(-multi.tar)')
    fileMatcherStratix = re.compile(r'.*(SRM-rfsw-image-install_z-uber-0x)([a-fA-F0-9]{8})(.tar).*')
    fileMatcherInstaller = re.compile(r'.*-installer.sh')
    pathMatcherStratix = re.compile(r'.*(stratix10-aaib)([\/\\]{1,2})(tmp-glibc)([\/\\]{1,2})(deploy)([\/\\]{1,2})(images)([\/\\]{1,2})(stratix10-aaib).*')

    pathsToLatestFiles = getPathsToLatestFiles(pathToFileIni, fileMatcherNahka, fileMatcherStratix, pathMatcherStratix)
    pathToFileNahka = pathsToLatestFiles.get("pathToLatestFileNahka", "")
    pathToFileStratix = pathsToLatestFiles.get("pathToLatestFileStratix", "")

    pathToFileInResNahka = handleGettingFile(pathToFileNahka, pathToDirRes, 'Nahka', urlMatcher)
    pathToFileInResStratix = handleGettingFile(pathToFileStratix, pathToDirRes, 'Stratix', urlMatcher, fileMatcherStratix)


    extractTarfile(pathToDirTemp, pathToFileInResStratix)
    replaceFileInArtifacts(pathToDirTempArtifacts, pathToFileInResNahka, fileMatcherNahka)
    setNewFileNameInInstallerScripts(pathToDirTemp, pathToFileInResNahka, fileMatcherInstaller, fileMatcherNahka)
    createTarfile(pathToDirTemp, fileNameStratixTemp)

    removeDir(pathToDirTemp)
    # fileNameStratixNew = getChecksumUsingZutil(fileNameStratixTemp, fileMatcher, path_to_zutil)
    fileNameStratixNew = getChecksum(fileNameStratixTemp, fileMatcher)

    renameStratixFile(fileNameStratixTemp, fileNameStratixNew)



if __name__ == '__main__':
    main()
    pressEnterToExit()
