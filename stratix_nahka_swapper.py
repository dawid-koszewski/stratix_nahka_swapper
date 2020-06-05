#!/usr/bin/python

#-----------------------------------------------------------------
# author:   dawid.koszewski@nokia.com
# date:     2019.10.30
#
# written in Notepad++
#-----------------------------------------------------------------

# pip install wget # when you are having problems running this script

import sys
import re
import os
import time
import subprocess
import shutil
import wget
import tarfile

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
https://artifactory-espoo1.int.net.nokia.com/artifactory/mnprf_brft-local/mMIMO_FDD/FB1813_Z/PROD_mMIMO_FDD_FB1813_Z_release/1578/C_Element/SE_RFM/SS_mMIMO_FDD/Target/SRM-rfsw-image-install_z-uber-0x00000000.tar\n\
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
You can now put your links below (you can also delete this whole message - not recommended).\n\n\
\
.\n\n\n\
\
")


def loadFileIntoList(pathToFile):
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
        print("Error: %s - %s.\n" % (e.filename, e.strerror))
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

#-------------------------------------------------------------------------------


#===============================================================================
# functions to copy / download Nahka and Stratix files
#===============================================================================

def getStratixFileNameFromLink(pathToFileStratix, fileMatcherStratix):
    return re.sub(fileMatcherStratix, r'\1\2\3', pathToFileStratix)


def getImageFromLinsee(fileName, pathToFile):
    if not os.path.isfile(fileName):
        print("copying to current working directory...\n")
        try:
            shutil.copy2(pathToFile, '.')#, *, follow_symlinks = True)
        except (shutil.Error, OSError, IOError):
            e = get_exception()
            print("Error: %s - %s.\n" % (e.filename, e.strerror))
    else:
        print("already present in current working directory!\n")


def getImageFromArtifactory(fileName, pathToFile):
    if not os.path.isfile(fileName):
        print("downloading to current working directory...\n")
        try:
            wget.download(pathToFile, '.')
        except Exception as e:
            print("Error: %s.\n" % (e))
    else:
        print("already present in current working directory!\n")


def getFileNahka(pathToFileNahka, fileMatcherNahka):
    print('\n\n === selected Nahka file ===\n\n%s\n' % (pathToFileNahka))
    fileNameNahka = os.path.basename(pathToFileNahka)
    getImageFromLinsee(fileNameNahka, pathToFileNahka)
    print(' --- file last modified: %s ---\n\n' % (getLastModificationTimeAsString(pathToFileNahka)))
    return fileNameNahka


def getFileStratix(pathToFileStratix, fileMatcherStratix):
    fileNameStratix = ""
    print('\n\n === selected Stratix file ===\n\n%s\n' % (pathToFileStratix))
    if re.search(r'https://', pathToFileStratix):
        fileNameStratix = getStratixFileNameFromLink(pathToFileStratix, fileMatcherStratix)
        getImageFromArtifactory(fileNameStratix, pathToFileStratix)
        print(' --- file last modified: %s ---\n\n' % (getLastModificationTimeAsString(fileNameStratix)))
    else:
        fileNameStratix = os.path.basename(pathToFileStratix)
        getImageFromLinsee(fileNameStratix, pathToFileStratix)
        print(' --- file last modified: %s ---\n\n' % (getLastModificationTimeAsString(pathToFileStratix)))
    return fileNameStratix

#-------------------------------------------------------------------------------


#===============================================================================
# functions to modify Stratix file with customized nahka file
#===============================================================================

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
                print("Error: %s - %s.\n" % (e.filename, e.strerror))


def setNewfileNameNahkaInInstallerScripts(pathToDirTemp, fileMatcherInstaller, fileMatcherNahka, fileNameNahka):
    for tempFile in os.listdir(pathToDirTemp):
        tempFilePath = os.path.join(pathToDirTemp, tempFile)
        if os.path.isfile(tempFilePath):
            if re.match(fileMatcherInstaller, tempFile):
                with open(tempFilePath, 'r') as f:
                    file_content = f.read()
                    file_content = re.sub(fileMatcherNahka, fileNameNahka, file_content)
                with open(tempFilePath, 'w') as f:
                    f.write(file_content)


def createNewStratixImage(pathToDirTemp, fileNameStratixNew):
    with tarfile.open(fileNameStratixNew, 'w') as tar:
        for item in os.listdir(pathToDirTemp):
            tar.add(os.path.join(pathToDirTemp, item), arcname = item)


def removeTempDirectory(pathToDirTemp):
    try:
        shutil.rmtree(pathToDirTemp)
    except OSError as e:
        print("Error: %s - %s\n." % (e.filename, e.strerror))


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

#-------------------------------------------------------------------------------


#===============================================================================
# === MAIN FUNCTION ===
#===============================================================================

def main():
#-------------------------------------------------------------------------------
# set absolute path to your zutil or pass it as first parameter to this script
#-------------------------------------------------------------------------------
    path_to_zutil = 'C:\zutil\zutil.exe'
    if len(sys.argv) == 2:
        path_to_zutil = sys.argv[1]

    pathToFileIni = r'.\tp_generator_stratix_nahka.ini'
    pathToDirTemp = r'.\SRM_temp'
    pathToDirTempArtifacts = r'.\SRM_temp\artifacts'
    fileNameStratixNew = r'.\SRM-rfsw-image-install_z-uber-0x00000000.tar'


    fileMatcherNahka = r'.*(FRM-rfsw-image-install_)([0-9]{14})(-multi.tar).*'
    fileMatcherStratix = r'.*(SRM-rfsw-image-install_z-uber-0x)([a-fA-F0-9]{8})(.tar).*'
    fileMatcherInstaller = r'.*-installer.sh.*'


    pathsToLatestFiles = getPathsToLatestFiles(pathToFileIni, fileMatcherNahka, fileMatcherStratix)
    pathToFileNahka = pathsToLatestFiles.get("pathToLatestFileNahka", "")
    pathToFileStratix = pathsToLatestFiles.get("pathToLatestFileStratix", "")

    fileNameNahka = getFileNahka(pathToFileNahka, fileMatcherNahka)
    fileNameStratix = getFileStratix(pathToFileStratix, fileMatcherStratix)


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
