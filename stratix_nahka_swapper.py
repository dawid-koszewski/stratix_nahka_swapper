#!/usr/bin/python

#-----------------------------------------------------------------
# author:   dawid.koszewski@nokia.com
# date:     2019.10.30
#
# written in Notepad++
#
#
#-----------------------------------------------------------------

# when you are having problems running this script:
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


#===============================================================================
# functions to get paths to latest Nahka and Stratix files
#===============================================================================

def createNewIniFile(pathToFile):
    with open(pathToFile, 'w') as f:
        f.write("\n\
The script will search this file line by line looking for the last occurrence of Nahka or Stratix image files.\n\n\
\
In the list below for example:\n\n\
i:\\some_user\\stratix10-aaib\\tmp-glibc\\deploy\\images\\stratix-aaib\n\
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
If the script will not be able to find Nahka or Stratix files in any location it will try searching in the current working directory by default.\n\
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
    print("\n%s initialization file not found..." % (pathToFile))
    print("creating new file in which you will be able to specify location of Nahka and Stratix files")
    print("by default searching for Nahka and Stratix is done in current directory (%s)\n\n" % (os.path.dirname(os.path.realpath(sys.argv[0]))))
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
    # if still can't find Nahka or Stratix file - try searching in current directory
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
    if not os.path.isfile(fileName):
        print("copying to current working directory...\n")
        try:
            shutil.copy2(pathToFile, '.')#, *, follow_symlinks = True)
        except (shutil.Error, OSError, IOError) as e:
            print("File copy ERROR: %s - %s.\n" % (e.filename, e.strerror))
            time.sleep(5)
            sys.exit()
    else:
        print("already present in current working directory!\n")


def getFileFromArtifactory(fileName, pathToFile):
    if not os.path.isfile(fileName):
        print("downloading to current working directory...\n")
        try:
            wget.download(pathToFile, '.')
        except Exception as e:
            print("File download ERROR: %s.\n" % (e))
            time.sleep(5)
            sys.exit()
    else:
        print("already present in current working directory!\n")


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
    for tempFile in listDirTemp:
        tempFilePath = os.path.join(pathToDirTemp, tempFile)
        if os.path.isfile(tempFilePath):
            if re.search(fileMatcherInstaller, tempFile):
                with open(tempFilePath, 'r') as f:
                    file_content = f.read()
                    file_content = re.sub(fileMatcherNahka, fileNameNahka, file_content)
                with open(tempFilePath, 'w') as f:
                    f.write(file_content)
                print("%s updated with current Nahka file %s" % (tempFilePath, fileNameNahka))


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


def getChecksumUsingZutil(fileNameStratixTemp, path_to_zutil):
    fileNameStratixNew = ""
    if os.path.isfile(fileNameStratixTemp):
        zutilOutput = subprocess.check_output('%s adler32 %s' % (path_to_zutil, fileNameStratixTemp)).decode(sys.stdout.encoding).strip()
        #print('\nzutil output:\n%s\n' % (zutilOutput))

        filenamePrepend = re.sub(r'(.*)(0x)([a-fA-F0-9]{8})(.*)', r'\1', fileNameStratixTemp)
        filenameAppend = re.sub(r'(.*)(0x)([a-fA-F0-9]{8})(.*)', r'\4', fileNameStratixTemp)
        checksumNew = re.sub(r'.*(\()(0x)([a-fA-F0-9]{8})(\))', r'\3', zutilOutput).upper()
        fileNameStratixNew = filenamePrepend + '0x' + checksumNew + filenameAppend
    else:
        print('\nERROR: Could not find new stratix image file to calculate checksum\n')
    return fileNameStratixNew


def getChecksum(fileNameStratixTemp):
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

        filenamePrepend = re.sub(r'(.*)(0x)([a-fA-F0-9]{8})(.*)', r'\1', fileNameStratixTemp)
        filenameAppend = re.sub(r'(.*)(0x)([a-fA-F0-9]{8})(.*)', r'\4', fileNameStratixTemp)
        checksumNew = re.sub(r'.*(0x)([a-fA-F0-9]{8}).*', r'\2', hex(checksum)).upper()
        fileNameStratixNew = filenamePrepend + '0x' + checksumNew + filenameAppend
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

    pathToFileIni = r'.\tp_generator_stratix_nahka.ini'
    pathToDirTemp = r'.\SRM_temp'
    pathToDirTempArtifacts = r'.\SRM_temp\artifacts'
    fileNameStratixTemp = r'.\SRM-rfsw-image-install_z-uber-0x00000000.tar'


    fileMatcherNahka = r'.*(FRM-rfsw-image-install_)([0-9]{14})(-multi.tar).*'
    fileMatcherStratix = r'.*(SRM-rfsw-image-install_z-uber-0x)([a-fA-F0-9]{8})(.tar).*'
    fileMatcherInstaller = r'.*-installer.sh.*'


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
    #fileNameStratixNew = getChecksumUsingZutil(fileNameStratixTemp, path_to_zutil)
    fileNameStratixNew = getChecksum(fileNameStratixTemp)

    renameFile(fileNameStratixTemp, fileNameStratixNew)




if __name__ == '__main__':
    main()
    time.sleep(3)
    sys.exit()
