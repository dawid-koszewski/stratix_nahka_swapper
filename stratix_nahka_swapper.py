#!/usr/bin/python

#-----------------------------------------------------------------
# author:   dawid.koszewski@nokia.com
# date:     2019.10.30
#
# written in Notepad++
#-----------------------------------------------------------------

import sys
import re
import os
import time
import subprocess
import shutil
import wget
import tarfile

#===============================================================================


#-------------------------------------------------------------------------------
# functions to get paths to latest Nahka and Stratix files
#-------------------------------------------------------------------------------

def loadFileIntoList(pathToFile):
    if os.path.isfile(pathToFile):
        with open(pathToFile, 'r') as f:
            return f.readlines()
    print("\n%s file not found...\nsearching for Nahka and Stratix files in current directory (%s)\n" % (pathToFile, os.path.dirname(os.path.realpath(sys.argv[0]))))
    return []


def getDateFromNahkaFile(fileMatcherNahka):
    return lambda f : re.sub(fileMatcherNahka, r'\2', f)


def getLastModificationTime(filename):
    return os.path.getmtime(filename)


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
    for line in loadFileIntoList(pathToFileIni):
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

#===============================================================================


#-------------------------------------------------------------------------------
# functions to copy / download Nahka and Stratix files
#-------------------------------------------------------------------------------

def getfileNameStratixFromLink(fileMatcherStratix, pathToDirStratix):
    return re.sub(fileMatcherStratix, r'\1\2\3', pathToDirStratix)


def getImageFromLinsee(fileName, filePath):
    if not os.path.isfile(fileName):
        shutil.copy2(filePath, '.')#, *, follow_symlinks = True)


def getImageFromArtifactory(fileName, filePath):
    if not os.path.isfile(fileName):
        wget.download(pathToDirStratix, '.')


def getNahkaFile(pathToDirNahka, fileMatcherNahka):
    nahkaFilePath = getPathToLatestFileInDir(pathToDirNahka, fileMatcherNahka, getDateFromNahkaFile(fileMatcherNahka))
    fileNameNahka = os.path.basename(nahkaFilePath)
    getImageFromLinsee(fileNameNahka, nahkaFilePath)
    return fileNameNahka


def getStratixFile(pathToDirStratix, fileMatcherStratix):
    if re.search(r'https://', pathToDirStratix):
        fileNameStratix = getfileNameStratixFromLink(fileMatcherStratix, pathToDirStratix)
        getImageFromArtifactory(fileNameStratix, pathToDirStratix)
    else:
        stratixFilePath = getPathToLatestFileInDir(pathToDirStratix, fileMatcherStratix, getLastModificationTime)
        fileNameStratix = os.path.basename(stratixFilePath)
        getImageFromLinsee(fileNameStratix, stratixFilePath)
    return fileNameStratix

#===============================================================================


#-------------------------------------------------------------------------------
# functions to modify Stratix file with customized nahka file
#-------------------------------------------------------------------------------

def extractStratixImage(fileNameStratix, pathToDirTemp):
    with tarfile.open(fileNameStratix, 'r') as tar:
        tar.extractall(path = pathToDirTemp)


def copyNewNahkaImageFileToArtifacts(fileNameNahka, pathToDirTempArtifacts):
    shutil.copy(fileNameNahka, pathToDirTempArtifacts)


def removeOldNahkaImageFile(pathToDirTempArtifacts, fileMatcherNahka):
    listDirTempArtifacts = os.listdir(pathToDirTempArtifacts)
    for tempFileArtifacts in listDirTempArtifacts:
        if re.match(fileMatcherNahka, tempFileArtifacts):
            try:
                os.remove(os.path.join(pathToDirTempArtifacts, tempFileArtifacts))
            except OSError as e:
                print("Error: %s - %s." % (e.filename, e.strerror))


def setNewfileNameNahkaInInstallerScripts(pathToDirTemp, fileMatcherInstaller, fileMatcherNahka, fileNameNahka):
    listDirTemp = os.listdir(pathToDirTemp)
    for tempFile in listDirTemp:
        tempFilePath = os.path.join(pathToDirTemp, tempFile)
        if os.path.isfile(tempFilePath):
            if re.match(fileMatcherInstaller, tempFile):
                with open(tempFilePath, 'r') as f:
                    file_content = f.read()
                    file_content = re.sub(fileMatcherNahka, fileNameNahka, file_content)
                with open(tempFilePath, 'w') as f:
                    f.write(file_content)


def createNewStratixImage(pathToDirTemp, fileNameStratixNew):
    listDirTemp = os.listdir(pathToDirTemp)
    with tarfile.open(fileNameStratixNew, 'w') as tar:
        for item in listDirTemp:
            tar.add(os.path.join(pathToDirTemp, item), arcname = item)


def removeTempDirectory(pathToDirTemp):
    try:
        shutil.rmtree(pathToDirTemp)
    except OSError as e:
        print("Error: %s - %s." % (e.filename, e.strerror))


def calculateChecksum(fileNameStratixNew, path_to_zutil):
    if os.path.isfile(fileNameStratixNew):
        zutilOutput = subprocess.check_output('%s adler32 %s' % (path_to_zutil, fileNameStratixNew)).decode(sys.stdout.encoding).strip()
        print('\nzutil output:\n%s\n' % (zutilOutput))

        filenamePrepend = re.sub(r'(.*)(0x)([a-fA-F0-9]{8})(.*)', r'\1', fileNameStratixNew)
        filenameAppend = re.sub(r'(.*)(0x)([a-fA-F0-9]{8})(.*)', r'\4', fileNameStratixNew)
        checksumNew = re.sub(r'.*(\()(0x)([a-fA-F0-9]{8})(\))', r'\3', zutilOutput).upper()
        fileNameNew = filenamePrepend + '0x' + checksumNew + filenameAppend

        os.rename(fileNameStratixNew, fileNameNew)

        if os.path.isfile(fileNameNew) and os.path.getsize(fileNameNew) > 0:
            print('\nnew file:\n%s\n' % (fileNameNew))
            print ('\n\n\n/============================================\\\n|                                            |\n|                                            |\n|------- FILE CREATED SUCCESSFULLY!!! -------|\n|                                            |\n|                                            |\n\\============================================/\n\n')
        time.sleep(3)

    else:
        print('\nERROR: Could not find new stratix image file to calculate checksum\n')
        time.sleep(3)

#===============================================================================


#-------------------------------------------------------------------------------
# === MAIN FUNCTION ===
#-------------------------------------------------------------------------------

def main():
#-------------------------------------------------------------------------------
# set absolute path to your zutil or pass it as first parameter to this script
#-------------------------------------------------------------------------------
    path_to_zutil = 'C:\zutil\zutil.exe'
    if len(sys.argv) == 2:
        path_to_zutil = sys.argv[1]

    pathToFileIni = r'.\tp_generator_stratix_nahka.in'
    pathToDirTemp = r'.\SRM_temp'
    pathToDirTempArtifacts = r'.\SRM_temp\artifacts'
    fileNameStratixNew = r'.\SRM-rfsw-image-install_z-uber-0x00000000.tar'

    #pathMatcherNahka = r'(deploy)[\/\\](images)[\/\\](nahka)'
    fileMatcherNahka = r'.*(FRM-rfsw-image-install_)([0-9]{14})(-multi.tar).*'
    fileMatcherStratix = r'.*(SRM-rfsw-image-install_z-uber-0x)([a-fA-F0-9]{8})(.tar).*'
    fileMatcherInstaller = r'.*-installer.sh'

    pathToDirNahka = ""
    pathToDirStratix = ""
    fileNameNahka = ""
    fileNameStratix = ""

    pathsToLatestFiles = getPathsToLatestFiles(pathToFileIni, fileMatcherNahka, fileMatcherStratix)
    pathToFileNahka = pathsToLatestFiles.get("pathToLatestFileNahka", "")
    pathToFileStratix = pathsToLatestFiles.get("pathToLatestFileStratix", "")

    print(pathToFileNahka)
    print(pathToFileStratix)

#jesli nie bedzie pliki ini, stworz jeden (zawierajacy opis i przyklady)



    # print('Selected Nahka file:\n%s\n' % (pathToDirNahka))
    # print('Selected Stratix file:\n%s\n' % (pathToDirStratix))

    # fileNameStratix = getStratixFile(pathToDirStratix, fileMatcherStratix)
    # fileNameNahka = getNahkaFile(pathToDirNahka, fileMatcherNahka)

    # extractStratixImage(fileNameStratix, pathToDirTemp)
    # setNewfileNameNahkaInInstallerScripts(pathToDirTemp, fileMatcherInstaller, fileMatcherNahka, fileNameNahka)
    # removeOldNahkaImageFile(pathToDirTempArtifacts, fileMatcherNahka)
    # copyNewNahkaImageFileToArtifacts(fileNameNahka, pathToDirTempArtifacts)
    # createNewStratixImage(pathToDirTemp, fileNameStratixNew)
    # removeTempDirectory(pathToDirTemp)

    # calculateChecksum(fileNameStratixNew, path_to_zutil)





if __name__ == '__main__':
    main()
    sys.exit()
