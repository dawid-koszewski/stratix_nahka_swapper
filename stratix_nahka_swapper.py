#!/usr/bin/python

#-----------------------------------------------------------------
# author:   dawid.koszewski@nokia.com
# date:     2019.10.30
#-----------------------------------------------------------------

import sys
import re
import os
import time
import subprocess
import shutil
import wget
import tarfile

pathToIniFile = r'.\tp_generator_stratix_nahka.ini'
pathToNahka = ""
pathToStratix = ""
pathToTemp = r'.\SRM_temp'
pathToTempArtifacts = r'.\SRM_temp\artifacts'
stratixFileNameNew = r'.\SRM-rfsw-image-install_z-uber-0x00000000.tar'

pathMatcherNahka = r'(deploy)[\/\\](images)[\/\\](nahka)'
imageMatcherNahka = r'(FRM-rfsw-image-install_)([0-9]{14})(-multi.tar)'
imageMatcherStratix = r'.*(SRM-rfsw-image-install_z-uber-0x)([a-fA-F0-9]{8})(.tar)'
installerMatcher = r'.*-installer.sh'


with open(pathToIniFile, 'r') as f:
    for line in f:
        if re.search(pathMatcherNahka, line):
            pathToNahka = line.strip()
            print(pathToNahka)
        else:
            pathToStratix = line.strip()
            print(pathToStratix)
#----------------------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------------------


def getDateFromNahkaFile(filename):
    return re.sub(imageMatcherNahka, r'\2', filename)

def getLastModificationTime(filename):
    return os.path.getmtime(filename)

def getLastFileFromDir(pathToDir, matcher, comparator):
    filesList = []
    listDir = os.listdir(pathToDir)
    for item in listDir:
        filePath = os.path.join(pathToDir, item)
        if os.path.isfile(filePath):
            if re.match(matcher, item):
                filesList.append(filePath)
    filesList.sort(key = comparator, reverse = False)
    return filesList[-1]


def getStratixFileNameFromLink(imageMatcherStratix, pathToStratix):
    return re.sub(imageMatcherStratix, r'\1\2\3', pathToStratix)


def getImageFromLinsee(fileName, filePath):
    if not os.path.isfile(fileName):
        shutil.copy2(filePath, '.')#, *, follow_symlinks = True)


def getImageFromArtifactory(fileName, filePath):
    if not os.path.isfile(fileName):
        wget.download(pathToStratix, '.')


def extractStratixImage(stratixFileName, pathToTemp):
    with tarfile.open(stratixFileName, 'r') as tar:
        tar.extractall(path = pathToTemp)


def setNewNahkaFileNameInInstallerScripts(pathToTemp, installerMatcher):
    listDirTemp = os.listdir(pathToTemp)
    for tempFile in listDirTemp:
        tempFilePath = os.path.join(pathToTemp, tempFile)
        if os.path.isfile(tempFilePath):
            if re.match(installerMatcher, tempFile):
                with open(tempFilePath, 'r') as f:
                    file_content = f.read()
                    file_content = re.sub(imageMatcherNahka, nahkaFileName, file_content)
                with open(tempFilePath, 'w') as f:
                    f.write(file_content)


def removeOldNahkaImageFile(pathToTempArtifacts, imageMatcherNahka):
    listDirTempArtifacts = os.listdir(pathToTempArtifacts)
    for tempFileArtifacts in listDirTempArtifacts:
        if re.match(imageMatcherNahka, tempFileArtifacts):
            try:
                os.remove(os.path.join(pathToTempArtifacts, tempFileArtifacts))
            except OSError as e:
                print("Error: %s - %s." % (e.filename, e.strerror))


def copyNewNahkaImageFileToArtifacts(nahkaFileName, pathToTempArtifacts):
    shutil.copy(nahkaFileName, pathToTempArtifacts)


def createNewStratixImage(pathToTemp, stratixFileNameNew):
    listDirTemp = os.listdir(pathToTemp)
    with tarfile.open(stratixFileNameNew, 'w') as tar:
        for item in listDirTemp:
            tar.add(os.path.join(pathToTemp, item), arcname = item)


def removeTempDirectory(pathToTemp):
    try:
        shutil.rmtree(pathToTemp)
    except OSError as e:
        print("Error: %s - %s." % (e.filename, e.strerror))



nahkaFilePath = getLastFileFromDir(pathToNahka, imageMatcherNahka, getLastModificationTime)
nahkaFileName = os.path.basename(nahkaFilePath)
getImageFromLinsee(nahkaFileName, nahkaFilePath)



if re.search(r'https://', pathToStratix):
    stratixFileName = getStratixFileNameFromLink(imageMatcherStratix, pathToStratix)
    getImageFromArtifactory(stratixFileName, pathToStratix)
else:
    stratixFilePath = getLastFileFromDir(pathToStratix, imageMatcherStratix, getLastModificationTime)
    stratixFileName = os.path.basename(stratixFilePath)
    getImageFromLinsee(stratixFileName, stratixFilePath)





extractStratixImage(stratixFileName, pathToTemp)

setNewNahkaFileNameInInstallerScripts(pathToTemp, installerMatcher)

removeOldNahkaImageFile(pathToTempArtifacts, imageMatcherNahka)

copyNewNahkaImageFileToArtifacts(nahkaFileName, pathToTempArtifacts)

createNewStratixImage(pathToTemp, stratixFileNameNew)

removeTempDirectory(pathToTemp)



