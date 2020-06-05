#!/usr/bin/python

#-----------------------------------------------------------------
# author:   dawid.koszewski@nokia.com
# date:     2019.10.30
#-----------------------------------------------------------------

#-----------------------------------------------------------------
# set absolute path to your zutil or pass it as second parameter to this script
#-----------------------------------------------------------------
#path_to_zutil = 'C:\zutil\zutil.exe'

#pathToStratix = 'https://artifactory-espoo1.int.net.nokia.com/artifactory/mnprf_brft-local/mMIMO_FDD/FB1813_Z/PROD_mMIMO_FDD_FB1813_Z_release/1578/C_Element/SE_RFM/SS_mMIMO_FDD/Target/SRM-rfsw-image-install_z-uber-0x121E7D81.tar'

import sys
import re
import os
import time
import subprocess
import shutil
import wget
import tarfile

pathToNahka = ""
pathToStratix = ""

with open('.\tp_generator_stratix_nahka.ini', 'r') as f:
    for line in f:
        if re.search(r'(deploy)[\/\\](images)[\/\\](nahka)', line):
            pathToNahka = line.strip()
            print(pathToNahka)
        else:
            pathToStratix = line.strip()
            print(pathToStratix)
#----------------------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------------------


listDirNahka = os.listdir(pathToNahka)
nahkaFilesList = []

for item in listDirNahka:
    if os.path.isfile(os.path.join(pathToNahka, item)):
        if re.match(r'(FRM-rfsw-image-install_)([0-9]{14})(-multi.tar)', item):
            nahkaFilesList.append(item)

def getDateFromFilename(filename):
    return re.sub(r'(FRM-rfsw-image-install_)([0-9]{14})(-multi.tar)', r'\2', filename)

nahkaFilesList.sort(key = getDateFromFilename, reverse = False)
nahkaFileLast = nahkaFilesList[-1]
nahkaFilePath = os.path.join(pathToNahka, nahkaFileLast)
#----------------------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------------------


listDirStratix = os.listdir(pathToStratix)
stratixFileLast = ""

for item in listDirStratix:
    if os.path.isfile(os.path.join(pathToStratix, item)):
        if re.match(r'(SRM-rfsw-image-install_z-uber-0x)([a-fA-F0-9]{8})(.tar)', item):
            stratixFileLast = item

stratixFilePath = os.path.join(pathToStratix, stratixFileLast)
#----------------------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------------------


shutil.copy2(nahkaFilePath, '.')#, *, follow_symlinks = True)

# if re.search(r'https://', pathToStratix):
    # wget.download(pathToStratix, '.')
# else:
    # shutil.copy2(stratixFilePath, '.')#, *, follow_symlinks = True)

shutil.copy2(stratixFilePath, '.')#, *, follow_symlinks = True)


# dodac sprawdzanie czy plik juz istnieje lokalnie i wtedy sciagac


#----------------------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------------------

pathToTemp = r'.\SRM_temp'

with tarfile.open(stratixFileLast, 'r') as tar:
    tar.extractall(path = pathToTemp)


listDirTemp = os.listdir(pathToTemp)

for tempFile in listDirTemp:
    tempFilePath = os.path.join(pathToTemp, tempFile)
    if os.path.isfile(tempFilePath):
        if re.match(r'.*-installer.sh', tempFile):
            with open(tempFilePath, 'r') as f:
                file_content = f.read()
                file_content = re.sub(r'(FRM-rfsw-image-install_)([0-9]{14})(-multi.tar)', nahkaFileLast, file_content)
            with open(tempFilePath, 'w') as f:
                f.write(file_content)

pathToTempArtifacts = r'.\SRM_temp\artifacts'

listDirTempArtifacts = os.listdir(pathToTempArtifacts)

for tempFileArtifacts in listDirTempArtifacts:
    if re.match(r'(FRM-rfsw-image-install_)([0-9]{14})(-multi.tar)', tempFileArtifacts):
        try:
            os.remove(os.path.join(pathToTempArtifacts, tempFileArtifacts))
        except OSError:
            pass

shutil.copy(nahkaFileLast, pathToTempArtifacts)



with tarfile.open('SRM-rfsw-image-install_z-uber-0x00000000.tar', 'w') as tar:
    for item in listDirTemp:
        tar.add(os.path.join(pathToTemp, item), arcname = item)


