#!/usr/bin/python

#-----------------------------------------------------------------
# author:   dawid.koszewski@nokia.com
# date:     2019.10.28
#-----------------------------------------------------------------

#-----------------------------------------------------------------
# set absolute path to your zutil or pass it as second parameter to this script
#-----------------------------------------------------------------
path_to_zutil = 'C:\zutil\zutil.exe'

pathToStratix = 'https://artifactory-espoo1.int.net.nokia.com/artifactory/mnprf_brft-local/mMIMO_FDD/FB1813_Z/PROD_mMIMO_FDD_FB1813_Z_release/1578/C_Element/SE_RFM/SS_mMIMO_FDD/Target/SRM-rfsw-image-install_z-uber-0x121E7D81.tar'

import sys
import re
import os
import time
import subprocess
#import glob
import shutil

pathToNahka = 'V:\\dkoszewski\\rel5_mmimo\\nahka\\tmp\\deploy\\images\\nahka\\'
#dodac ifa ktory dodaje lub odejmuje ostatni backslash
pathToNahka2 = r'V:\dkoszewski\rel5_mmimo\nahka\tmp\deploy\images\nahka\\'

pathToNahka2norm = os.path.abspath(pathToNahka2)
pathToNahka2norm2 = os.path.dirname(pathToNahka2)

print(pathToNahka)
print(pathToNahka2)
print(pathToNahka2norm)
print(pathToNahka2norm2)


#os.path.join


# print(pathToNahka2norm)

# files = []
# for file in glob.glob(pathToNahka2norm + '\FRM-rfsw-image-install_*-multi.tar'):
    # files.append(file)
    # print(file)

    #print(files[:-1])

dirlist = os.listdir(pathToNahka2)

#print(dirlist)

#nahkaFilesDictionary = {}
nahkaFilesList = []

for item in dirlist:
    #print(os.path.dirname(item))
    if os.path.isfile(pathToNahka2norm +'\\' + item):
        #print(item)
        #if re.search(r'(FRM-rfsw-image-install_)([0-9]{14})(-multi.tar)', item):
        if re.match(r'(FRM-rfsw-image-install_)([0-9]{14})(-multi.tar)', item):
            #print(item)
            #nahkaFilesDictionary[re.sub(r'(FRM-rfsw-image-install_)([0-9]{14})(-multi.tar)', r'\2', item)] = item
            nahkaFilesList.append(item)

# nahkaFilesDictionary['20191024132842'] = 'FRM-rfsw-image-install_20191024132842-multi.tar'
# nahkaFilesDictionary['20191024132841'] = 'FRM-rfsw-image-install_20191024132841-multi.tar'
nahkaFilesList.append('FRM-rfsw-image-install_20191024132842-multi.tar')
nahkaFilesList.append('FRM-rfsw-image-install_20191024132841-multi.tar')

#print(nahkaFilesDictionary)
#print(sorted(nahkaFilesDictionary))

#nahkaFileLast = nahkaFilesDictionary.get(sorted(nahkaFilesDictionary)[-1])
#print(nahkaFileLast)


def getDateFromFilename(filename):
    return re.sub(r'(FRM-rfsw-image-install_)([0-9]{14})(-multi.tar)', r'\2', filename)

#print(nahkaFilesList)
nahkaFilesList.sort(key = getDateFromFilename, reverse = False)
#print(nahkaFilesList)


nahkaFileLast2 = nahkaFilesList[-1]
print(nahkaFileLast2)

nahkaFilePath = pathToNahka2norm +'\\' + nahkaFileLast2
print(nahkaFilePath)
#----------------------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------------------


shutil.copy2(nahkaFilePath, '.\\')#, *, follow_symlinks = True)

if re.search(r'https://', pathToStratix):
    import wget
    #wget.download(pathToStratix, './')
else:
    shutil.copy2(pathToStratix, './')#, *, follow_symlinks = True)

# dodac sprawdzanie czy plik juz istnieje lokalnie




#----------------------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------------------

import tarfile
with tarfile.open('SRM-rfsw-image-install_z-uber-0x121E7D81.tar', 'r') as tar:
    tar.extractall(path= '.\SRM_temp')


dirlist = os.listdir('.\SRM_temp')

for filename in dirlist:
    if os.path.isfile('.\SRM_temp\\' + filename):
        if re.match(r'.*-installer.sh', filename):
            with open('.\SRM_temp\\' + filename, 'r') as f:
                file_content = f.read()
                file_content = re.sub(r'(FRM-rfsw-image-install_)([0-9]{14})(-multi.tar)', nahkaFileLast2, file_content)
            with open('.\SRM_temp\\' + filename, 'w') as f:
                f.write(file_content)


dirlist2 = os.listdir(r'.\SRM_temp\artifacts\\')
for filename in dirlist2:
    print(filename)
    if re.match(r'(FRM-rfsw-image-install_)([0-9]{14})(-multi.tar)', r'.\SRM_temp\artifacts\\' + filename):
        try:
            os.remove(r'.\SRM_temp\artifacts\\' + filename)
        except OSError:
            pass


shutil.copy(nahkaFileLast2, r'.\SRM_temp\artifacts\\')


# podmienic jeszcze obraz nahki w artifacts


with tarfile.open('SRM-rfsw-image-install_z-uber-0x00000000.tar', 'w') as tar:
    for item in dirlist:
        tar.add('.\SRM_temp\\' + item, arcname = item)


