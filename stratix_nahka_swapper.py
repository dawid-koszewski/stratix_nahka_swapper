#!/usr/bin/python

#-----------------------------------------------------------------
# author:   dawid.koszewski@nokia.com
# date:     2019.10.30
# update:   2019.11.06
# version:  01h
#
# written in Notepad++
#
#
#-----------------------------------------------------------------

# when you are having problems running this script run this command:
# pip install wget

import sys
import re
import os
import time
import subprocess
import shutil
import wget
import tarfile
import zlib


#-------------------------------------------------------------------------------





################################################################################
#
# shutil LIBRARY functions BELOW by:
#
# author:   doko@ubuntu.com
# date:     Thu, 30 Apr 2015 13:44:18 +0200 (2015-04-30)
# link:     https://hg.python.org/cpython/file/eb09f737120b/Lib/shutil.py
#
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
                copyfileobj(fsrc, fdst, callback, src) # MODIFIED TO CALL USER DEFINED FUNCTION (dawid.koszewski@nokia.com)
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
#
# shutil LIBRARY functions ABOVE by:
#
# author:   doko@ubuntu.com
# date:     Thu, 30 Apr 2015 13:44:18 +0200 (2015-04-30)
# link:     https://hg.python.org/cpython/file/eb09f737120b/Lib/shutil.py
#
################################################################################







#-------------------------------------------------------------------------------


#===============================================================================
# my implementation of copyfileobj from shutil LIBRARY
#===============================================================================

def callback(copied, fileSize):
    copied = copied / 1048576
    percent = (copied / fileSize) * 100
    sys.stdout.write('\r%dMB of %dMB (%d %%)' % (copied, fileSize, percent))
    sys.stdout.flush()


def copyfileobj(fsrc, fdst, callback, src, length=16*1024):
    fileSize = os.stat(src).st_size / 1048576
    copied = 0
    tmp = 0
    while 1:
        buf = fsrc.read(length)
        if not buf:
            break
        fdst.write(buf)
        copied += len(buf)
        if copied >= (tmp + 1048576):
            tmp = copied
            callback(copied, fileSize)
    callback(copied, fileSize)
    print()

#-------------------------------------------------------------------------------


#===============================================================================
# functions to get paths to latest Nahka and Stratix files
#===============================================================================

def createNewIniFile(pathToFile):
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


def loadIniFileIntoList(pathToFile):
    if os.path.isfile(pathToFile):
        with open(pathToFile, 'r') as f:
            return f.readlines()
    print("\nInitialization file not found...\n")
    print("%s file has been created!!!" % (pathToFile))
    print("now you will be able to specify location of Nahka and Stratix files in there\n")
    print("In the first run this script will search for Nahka and Stratix files in the current working directory (%s)\n" % (os.path.dirname(os.path.realpath(sys.argv[0]))))
    print("Every next time it will search for Nahka and Stratix files in locations defined by you in the ini file...\n")
    input("\nPress Enter to continue...\n")
    createNewIniFile(pathToFile)
    return []


def getDateFromNahkaFile(fileMatcherNahka):
    return lambda f : re.sub(fileMatcherNahka, r'\2', f)


def getLastModificationTime(pathToFile):
    secondsSinceEpoch = 0
    try:
        secondsSinceEpoch = os.path.getmtime(pathToFile)
    except OSError as e:
        print("Getting file info ERROR: %s - %s.\n" % (e.filename, e.strerror))
    return secondsSinceEpoch


def getLastModificationTimeAsString(pathToFile):
    return time.ctime(getLastModificationTime(pathToFile))


def getPathToLatestFileInDir(pathToDir, matcher, comparator):
    filesList = []
    for item in os.listdir(pathToDir):
        pathToFile = os.path.join(pathToDir, item)
        if os.path.isfile(pathToFile):
            if re.search(matcher, item):
                filesList.append(pathToFile)
    filesList.sort(key = comparator, reverse = False)
    return filesList[-1] if filesList else ""


def getPathsToLatestFiles(pathToFileIni, fileMatcherNahka, fileMatcherStratix):
    pathToFileNahka = ""
    pathToFileStratix = ""
    for line in loadIniFileIntoList(pathToFileIni):
        line = line.strip()
        if re.search(fileMatcherNahka, line):
            pathToFileNahka = line
        elif re.search(fileMatcherStratix, line):
            pathToFileStratix = line
        elif os.path.isdir(line):
            pathToLatestFileInDirNahka = getPathToLatestFileInDir(line, fileMatcherNahka, getDateFromNahkaFile(fileMatcherNahka))
            if pathToLatestFileInDirNahka:
                pathToFileNahka = pathToLatestFileInDirNahka
            pathToLatestFileInDirStratix = getPathToLatestFileInDir(line, fileMatcherStratix, getLastModificationTime)
            if pathToLatestFileInDirStratix:
                pathToFileStratix = pathToLatestFileInDirStratix
    # if still can't find Nahka or Stratix file - try searching in the current working directory
    if not pathToFileNahka:
        pathToFileNahka = getPathToLatestFileInDir('.', fileMatcherNahka, getDateFromNahkaFile(fileMatcherNahka))
    if not pathToFileStratix:
        pathToFileStratix = getPathToLatestFileInDir('.', fileMatcherStratix, getLastModificationTime)
    pathsToLatestFiles = {}
    pathsToLatestFiles['pathToLatestFileNahka'] = pathToFileNahka
    pathsToLatestFiles['pathToLatestFileStratix'] = pathToFileStratix
    return pathsToLatestFiles

#-------------------------------------------------------------------------------


#===============================================================================
# functions to copy / download Nahka and Stratix files
#===============================================================================

def getStratixFileNameFromLink(pathToFileStratix, fileMatcherStratix):
    return re.sub(fileMatcherStratix, r'\1\2\3', pathToFileStratix)


def getFile(fileName, pathToFile):
    if os.path.isfile(pathToFile):
        if not os.path.isfile(fileName):
            print("copying file to the current working directory... ")#, end = '')
            try:
                #shutil.copy2(pathToFile, '.')#, *, follow_symlinks = True)
                copy2(pathToFile, '.')
            except (shutil.Error, OSError, IOError) as e:
                print("File copy ERROR: %s - %s.\n" % (e.filename, e.strerror))
                #time.sleep(5)
                input("\nPress Enter to exit...\n")
                sys.exit()
        else:
            print("file already present in the current working directory!\n")
    else:
        print("Could not find anything! Please specify possible file locations in the ini file...\n")
        #time.sleep(5)
        input("\nPress Enter to exit...\n")
        sys.exit()

def getFileFromArtifactory(fileName, pathToFile):
    if not os.path.isfile(fileName):
        print("downloading file to the current working directory...\n")
        try:
            wget.download(pathToFile, '.')
        except Exception as e:
            print("File download ERROR: %s.\n" % (e))
            #time.sleep(5)
            input("\nPress Enter to exit...\n")
            sys.exit()
    else:
        print("file already present in the current working directory!\n")


def getFileNahka(pathToFileNahka, fileMatcherNahka):
    print('\n\n\n === selected Nahka file ===\n\n%s\n' % (pathToFileNahka))
    fileNameNahka = os.path.basename(pathToFileNahka)
    getFile(fileNameNahka, pathToFileNahka)
    print(' --- file last modified: %s ---\n\n' % (getLastModificationTimeAsString(pathToFileNahka)))
    return fileNameNahka


def getFileStratix(pathToFileStratix, fileMatcherStratix):
    fileNameStratix = ""
    print('\n\n\n === selected Stratix file ===\n\n%s\n' % (pathToFileStratix))
    if re.search(r'https://', pathToFileStratix):
        fileNameStratix = getStratixFileNameFromLink(pathToFileStratix, fileMatcherStratix)
        getFileFromArtifactory(fileNameStratix, pathToFileStratix)
        print(' --- file last modified: %s ---\n' % (getLastModificationTimeAsString(fileNameStratix)))
    else:
        fileNameStratix = os.path.basename(pathToFileStratix)
        getFile(fileNameStratix, pathToFileStratix)
        print(' --- file last modified: %s ---\n' % (getLastModificationTimeAsString(pathToFileStratix)))
    return fileNameStratix

#-------------------------------------------------------------------------------


#===============================================================================
# functions to modify Stratix file with customized nahka file
#===============================================================================

def extractTarfile(pathToDir, fileName):
    try:
        with tarfile.open(fileName, 'r') as tar:
            tar.extractall(path = pathToDir)
    except (Exception) as e:
        print("Tarfile extraction ERROR: %s " % (e))


def replaceFileNahka(pathToDirTempArtifacts, fileMatcherNahka, fileNameNahka):
    listDirTempArtifacts = []
    try:
        listDirTempArtifacts = os.listdir(pathToDirTempArtifacts)
    except OSError as e:
        print("Directory listing ERROR: %s - %s.\n" % (e.filename, e.strerror))
    for tempFileArtifacts in listDirTempArtifacts:
        if re.search(fileMatcherNahka, tempFileArtifacts):
            try:
                os.remove(os.path.join(pathToDirTempArtifacts, tempFileArtifacts))
            except OSError as e:
                print("File remove ERROR: %s - %s.\n" % (e.filename, e.strerror))
    try:
        shutil.copy(fileNameNahka, pathToDirTempArtifacts)
    except OSError as e:
        print("File copy ERROR: %s - %s.\n" % (e.filename, e.strerror))


def setNewFileNameNahkaInInstallerScripts(pathToDirTemp, fileMatcherInstaller, fileMatcherNahka, fileNameNahka):
    listDirTemp = []
    try:
        listDirTemp = os.listdir(pathToDirTemp)
    except OSError as e:
        print("Directory listing ERROR: %s - %s.\n" % (e.filename, e.strerror))
    print("\n\n")
    for tempFile in listDirTemp:
        tempFilePath = os.path.join(pathToDirTemp, tempFile)
        if os.path.isfile(tempFilePath):
            if re.search(fileMatcherInstaller, tempFile):
                with open(tempFilePath, 'r') as f:
                    file_content = f.read()
                    file_content = re.sub(fileMatcherNahka, fileNameNahka, file_content)
                with open(tempFilePath, 'w') as f:
                    f.write(file_content)
                print("Success: %s has been updated in installer script: %s" % (fileNameNahka, tempFilePath))


def createTarfile(pathToDir, fileName):
    try:
        with tarfile.open(fileName, 'w') as tar:
            for item in os.listdir(pathToDir):
                tar.add(os.path.join(pathToDir, item), arcname = item)
    except (Exception) as e:
        print("Tarfile creation ERROR: %s " % (e))


def removeDir(pathToDir):
    try:
        shutil.rmtree(pathToDir)
    except OSError as e:
        print("Directory remove ERROR: %s - %s.\n" % (e.filename, e.strerror))


def getChecksumUsingZutil(fileNameStratixTemp, fileMatcher, path_to_zutil):
    fileNameStratixNew = ""
    if os.path.isfile(fileNameStratixTemp):
        zutilOutput = subprocess.check_output('%s adler32 %s' % (path_to_zutil, fileNameStratixTemp)).decode(sys.stdout.encoding).strip()
        #print('\nzutil output:\n%s\n' % (zutilOutput))

        filenamePrepend = re.sub(fileMatcher, r'\1', fileNameStratixTemp)
        filenameAppend = re.sub(fileMatcher, r'\4', fileNameStratixTemp)
        checksumNew = re.sub(fileMatcher, r'\3', zutilOutput).upper()
        fileNameStratixNew = filenamePrepend + '0x' + checksumNew + filenameAppend
    else:
        print('\nERROR: Could not find new stratix image file to calculate checksum\n')
    return fileNameStratixNew


def getChecksum(fileNameStratixTemp, fileMatcher):
    fileNameStratixNew = ""
    if os.path.isfile(fileNameStratixTemp):
        f = open(fileNameStratixTemp, 'rb')
        checksum = 1
        buffer = f.read(1024)
        while buffer: #len(buffer) > 0:
            checksum = zlib.adler32(buffer, checksum)
            buffer = f.read(1024)
        f.close()

        checksum = checksum & 0xffffffff
        #print("%d %s" % (checksum, (hex(checksum))))

        fileNamePrepend = re.sub(fileMatcher, r'\1', fileNameStratixTemp)
        fileNameAppend = re.sub(fileMatcher, r'\4', fileNameStratixTemp)
        checksumNew = re.sub(fileMatcher, r'\3', hex(checksum)).upper()
        fileNameStratixNew = fileNamePrepend + '0x' + checksumNew + fileNameAppend
    else:
        print('\nERROR: Could not find new stratix image file to calculate checksum\n')
    return fileNameStratixNew


def renameFile(fileNameStratixTemp, fileNameStratixNew):
    try:
        os.rename(fileNameStratixTemp, fileNameStratixNew)
    except OSError as e:
        print("File rename ERROR: %s - %s.\n" % (e.filename, e.strerror))

    if os.path.isfile(fileNameStratixNew) and os.path.getsize(fileNameStratixNew) > 0:
        print('\n\n\n === new Stratix file ===\n\n%s\n' % (fileNameStratixNew))
        print(' --- file last modified: %s ---\n' % (getLastModificationTimeAsString(fileNameStratixNew)))
        print('\n/============================================\\\n|                                            |\n|                                            |\n|------- FILE CREATED SUCCESSFULLY!!! -------|\n|                                            |\n|                                            |\n\\============================================/\n\n')
    else:
        print("Something went wrong. New Stratix file not generated correctly")


#-------------------------------------------------------------------------------


#===============================================================================
# === MAIN FUNCTION ===
#===============================================================================

def main():
    # path_to_zutil = 'C:\zutil\zutil.exe'
    # if len(sys.argv) == 2:
        # path_to_zutil = sys.argv[1]

    pathToFileIni = r'.\stratix_nahka_swapper.ini'
    pathToDirTemp = r'.\SRM_temp'
    pathToDirTempArtifacts = r'.\SRM_temp\artifacts'
    fileNameStratixTemp = r'.\SRM-rfsw-image-install_z-uber-0x00000000.tar'

    fileMatcher = r'(.*)(0x)([a-fA-F0-9]{8})(.*)'
    fileMatcherNahka = r'(FRM-rfsw-image-install_)([0-9]{14})(-multi.tar)'
    fileMatcherStratix = r'(SRM-rfsw-image-install_z-uber-0x)([a-fA-F0-9]{8})(.tar)'
    fileMatcherInstaller = r'.*-installer.sh'


    pathsToLatestFiles = getPathsToLatestFiles(pathToFileIni, fileMatcherNahka, fileMatcherStratix)
    pathToFileNahka = pathsToLatestFiles.get("pathToLatestFileNahka", "")
    pathToFileStratix = pathsToLatestFiles.get("pathToLatestFileStratix", "")

    fileNameNahka = getFileNahka(pathToFileNahka, fileMatcherNahka)
    fileNameStratix = getFileStratix(pathToFileStratix, fileMatcherStratix)


    extractTarfile(pathToDirTemp, fileNameStratix)
    replaceFileNahka(pathToDirTempArtifacts, fileMatcherNahka, fileNameNahka)
    setNewFileNameNahkaInInstallerScripts(pathToDirTemp, fileMatcherInstaller, fileMatcherNahka, fileNameNahka)
    createTarfile(pathToDirTemp, fileNameStratixTemp)

    removeDir(pathToDirTemp)
    # fileNameStratixNew = getChecksumUsingZutil(fileNameStratixTemp, fileMatcher, path_to_zutil)
    fileNameStratixNew = getChecksum(fileNameStratixTemp, fileMatcher)

    renameFile(fileNameStratixTemp, fileNameStratixNew)



if __name__ == '__main__':
    main()
    #time.sleep(3)
    input("\nPress Enter to exit...\n")
    sys.exit()
