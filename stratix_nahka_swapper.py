#!/usr/bin/python

#-------------------------------------------------------------------------------
# supports:     python 2.6, 2.7
#               python 3.4 or newer
#
# author:       dawid.koszewski@nokia.com
# date:         2019.10.30
# update:       2019.11.15
# version:      01t
#
# written in Notepad++
#
#
#-------------------------------------------------------------------------------

################# KNOWN ISSUES: ################# 
# - python 2 is not verifying CORRUPTED TAR files correctly
# - no possibility to install requests module on wrlinb, needed to download Stratix from artifactory


import errno
import os
import random
import re
import shutil
import stat
import subprocess
import sys
import tarfile
import time

#import zlib        #imported below in try except block
#import requests    #imported below in try except block


def pressEnterToExit():
#1.
    try:
        raw_input("\nPress Enter to exit...\n") #python2 only
    except (SyntaxError, Exception) as e:
        input("\nPress Enter to exit...\n") #python3 only
#2.
    # try:
        # input("\nPress Enter to exit...\n") #python3 only
    # except (SyntaxError, Exception) as e:
        # pass
    time.sleep(1)
    sys.exit()


def pressEnterToContinue():
#1.
    try:
        raw_input("\nPress Enter to continue...\n") #python2 only
    except (SyntaxError, Exception) as e:
        input("\nPress Enter to continue...\n") #python3 only
#2.
    # try:
        # input("\nPress Enter to continue...\n")  #python3 only
    # except (SyntaxError, Exception) as e:
        # pass
    time.sleep(1)


try:
    import zlib
except (ImportError, Exception) as e:
    print("\n%s\nYou can proceed but you will need to calculate checksum manually" % e)
    pressEnterToContinue()


def installRequests():
    try:
        print("If the following command will fail, script will try to access pypi.org through a proxy:")
        print("pip install requests --retries 0 --timeout 3")
        print("Please wait for up to 15 seconds...")
        subprocess.check_call("pip install requests --retries 0 --timeout 3")
    except (subprocess.CalledProcessError, Exception) as e:
        print("\n%s\n" % e)
        try:
            print("pip install requests --proxy defra1c-proxy.emea.nsn-net.net:8080 --retries 0 --timeout 3")
            print("Please wait for up to 15 seconds...")
            subprocess.check_call("pip install requests --proxy defra1c-proxy.emea.nsn-net.net:8080 --retries 0 --timeout 3")
        except (subprocess.CalledProcessError, Exception) as e:
            print("\n%s\n" % e)
            try:
                print("pip install requests --proxy fihel1d-proxy.emea.nsn-net.net:8080 --retries 0 --timeout 3")
                print("Please wait for up to 15 seconds...")
                subprocess.check_call("pip install requests --proxy fihel1d-proxy.emea.nsn-net.net:8080 --retries 0 --timeout 3")
            except (subprocess.CalledProcessError, Exception) as e:
                print("\n%s\n" % e)
                pass
    pressEnterToContinue()

#-------------------------------------------------------------------------------


################################################################################
#                                                                              #
# shutil LIBRARY functions BELOW by:                                           #
#                                                                              #
# authors:  gvanrossum, serhiy-storchaka, birkenfeld, pitrou, benjaminp,       #
#           rhettinger, merwok, loewis, tim-one, nnorwitz, doerwalter,         #
#           ronaldoussoren, ned-deily, florentx, freddrake, csernazs,          #
#           brettcannon, warsaw                                                #
#                                                                              #
# date:     24 Oct 2018                                                        #
# link:     https://github.com/python/cpython/blob/2.7/Lib/shutil.py           #
#                                                                              #
################################################################################

"""Utility functions for copying and archiving files and directory trees.

XXX The functions here don't copy the resource fork or other metadata on Mac.

"""


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


def copyfile(src, dst):
    """Copy data from src to dst"""
    if _samefile(src, dst):
        raise Error("`%s` and `%s` are the same file" % (src, dst))

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

    #modified by dawid.koszewski@nokia.com
    try:
        fsrc = open(src, 'rb')
        try:
            fdst = open(dst, 'wb')
            try:
                #copyfileobj(fsrc, fdst)
                copyfileobj(fsrc, fdst, src)
                fdst.close()
            except (OSError, IOError) as e:
                print("\nFile copy ERROR: %s - %s" % (e.filename, e.strerror))
                pressEnterToExit()
            finally:
                fdst.close()
                fsrc.close()
        except (Exception) as e:
            print("\nFile copy ERROR: %s - %s" % (e))
            pressEnterToExit()
        fsrc.close()
    except (Exception) as e:
        print("\nFile copy ERROR: %s - %s" % (e))
        pressEnterToExit()


def copystat(src, dst):
    """Copy file metadata

    Copy the permission bits, last access time, last modification time, and
    flags from `src` to `dst`. On Linux, copystat() also copies the "extended
    attributes" where possible. The file contents, owner, and group are
    unaffected. `src` and `dst` are path names given as strings.
    """
    st = os.stat(src)
    mode = stat.S_IMODE(st.st_mode)
    if hasattr(os, 'utime'):
        os.utime(dst, (st.st_atime, st.st_mtime))
    if hasattr(os, 'chmod'):
        os.chmod(dst, mode)
    if hasattr(os, 'chflags') and hasattr(st, 'st_flags'):
        try:
            os.chflags(dst, st.st_flags)
        #except OSError, why:
        except OSError as why: #modified by dawid.koszewski@nokia.com
            for err in 'EOPNOTSUPP', 'ENOTSUP':
                if hasattr(errno, err) and why.errno == getattr(errno, err):
                    break
            else:
                raise


def copy2(src, dst):
    """Copy data and metadata. Return the file's destination.

    Metadata is copied with copystat(). Please see the copystat function
    for more information.

    The destination may be a directory.

    """
    if os.path.isdir(dst):
        dst = os.path.join(dst, os.path.basename(src))
    copyfile(src, dst)
    copystat(src, dst)


################################################################################
#                                                                              #
# shutil LIBRARY functions ABOVE by:                                           #
#                                                                              #
# authors:  gvanrossum, serhiy-storchaka, birkenfeld, pitrou, benjaminp,       #
#           rhettinger, merwok, loewis, tim-one, nnorwitz, doerwalter,         #
#           ronaldoussoren, ned-deily, florentx, freddrake, csernazs,          #
#           brettcannon, warsaw                                                #
#                                                                              #
# date:     24 Oct 2018                                                        #
# link:     https://github.com/python/cpython/blob/2.7/Lib/shutil.py           #
#                                                                              #
################################################################################







#-------------------------------------------------------------------------------


#===============================================================================
# function to print random fun fact
#===============================================================================

def printFunFact():
    fun_facts_cosmos = [
    "1. Mercury & Venus are the only 2 planets in our solar system that have no moons.", 
    "2. If a star passes too close to a black hole, it can be torn apart.", 
    "3. The hottest planet in our solar system is Venus.", 
    "4. Our solar system is 4.6 billion years old.", 
    "5. Enceladus, one of Saturn's smaller moons, reflects 90% of the Sun's light.", 
    "6. The highest mountain discovered is the Olympus Mons, which is located on Mars.", 
    "7. The Whirlpool Galaxy (M51) was the first celestial object identified as being spiral.", 
    "8. A light-year is the distance covered by light in a single year.", 
    "9. The Milky Way galaxy is 105,700 light-years wide.", 
    "10. The Sun weighs about 330,000 times more than Earth.", 
    "11. Footprints left on the Moon won't disappear as there is no wind.", 
    "12. Because of lower gravity, a person who weighs 220 lbs on Earth would weigh 84 lbs on Mars.", 
    "13. There are 79 known moons orbiting Jupiter.", 
    "14. The Martian day is 24 hours 39 minutes and 35 seconds long.", 
    "15. NASA's Crater Observation and Sensing Satellite (LCROSS) found evidence of water on the Earth's Moon.", 
    "16. The Sun makes a full rotation once every 25 - 35 days.", 
    "17. Earth is the only planet not named after a God.", 
    "18. Due to the Sun and Moon's gravitational pull, we have tides.", 
    "19. Pluto is smaller than the United States.", 
    "20. According to mathematics, white holes are possible, although as of yet we have found none.", 
    "21. There are more volcanoes on Venus than any other planet in our solar system.", 
    "22. Uranus' blue glow is due to the gases in its atmosphere.", 
    "23. In our solar system that are 4 planets known as gas giants: Jupiter, Saturn, Uranus & Neptune.", 
    "24. Uranus has 27 moons that have been discovered so far.", 
    "25. Because of its unique tilt, a season on Uranus is equivalent to 21 Earth years.", 
    "26. Neptune's moon, Triton, orbits the planet backwards.", 
    "27. Triton is gradually getting closer to the planet it orbits.", 
    "28. There are more stars in space than there are grains of sand in the world.", 
    "29. Neptune takes nearly 165 Earth years to make one orbit of the Sun.", 
    "30. Pluto's largest moon, Charon, is half the size of Pluto.", 
    "31. The International Space Station is the largest manned object ever sent into space.", 
    "32. A day on Pluto is lasts for 153.6 hours long.", 
    "33. Saturn is the second largest planet in our solar system.", 
    "34. Any free-moving liquid in outer space will form itself into a sphere.", 
    "35. Mercury, Venus, Earth & Mars are known as the \"Inner Planets\".", 
    "36. We know more about Mars and our Moon than we do about our oceans.", 
    "37. The Black Arrow is the only British satellite to be launched using a British rocket.", 
    "38. Only 5% of the universe is visible from Earth.", 
    "39. Light travels from the Sun to the Earth in less than 10 minutes.", 
    "40. At any given moment, there are at least 2,000 thunderstorms happening on Earth.", 
    "41. The Earth's rotation is slowing slightly as time goes on.", 
    "42. If you were driving at 75 miles per hour, it would take 258 days to drive around Saturn's rings.", 
    "43. Outer Space is only 62 miles away.", 
    "44. The International Space Station circles Earth every 92 minutes.", 
    "45. Stars twinkle because of the way light is disrupted as it passes through Earth's atmosphere.", 
    "46. We always see the same side of the Moon, no matter where we stand on Earth.", 
    "47. There are three main types of galaxies: elliptical, spiral & irregular.", 
    "48. There are approximately 100 thousand million stars in the Milky Way.", 
    "49. Using the naked eye, you can see 3 - 7 different galaxies from Earth.", 
    "50. In 2016, scientists detected a radio signal from a source 5 billion light-years away.", 
    "51. The closest galaxy to us is the Andromeda Galaxy  its estimated at 2.5 million light-years away.", 
    "52. The first Supernovae observed outside of our own galaxy was in 1885.", 
    "53. The first ever black hole photographed is 3 million times the size of Earth.", 
    "54. The distance between the Sun & Earth is defined as an Astronomical Unit.", 
    "55. The second man on the moon was Buzz Aldrin. \"Moon\" was Aldrin's mother's maiden name.", 
    "56. Buzz Aldrin's birth name was Edwin Eugene Aldrin Jr.", 
    "57. On Venus, it snows metal and rains sulfuric acid.", 
    "58. The Mariner 10 was the first spacecraft that visited Mercury in 1974.", 
    "59. Space is completely silent.", 
    "60. Coca-Cola was the first commercial soft drink that was ever consumed in space.", 
    "61. Astronauts can grow approximately two inches (5 cm) in height when in space.", 
    "62. The Kuiper Belt is a region of the Solar System beyond the orbit of Neptune.", 
    "63. The first woman in space was a Russian called Valentina Tereshkova.", 
    "64. If Saturn's rings were 3 feet long, they would be 10,000 times thinner than a razorblade.", 
    "65. The Hubble Space Telescope is one of the most productive scientific instruments ever built.", 
    "66. The first artificial satellite in space was called \"Sputnik\".", 
    "67. Exoplanets are planets that orbit around other stars.", 
    "68. The center of the Milky Way smells like rum & tastes like raspberries.", 
    "69. Our moon is moving away from Earth at a rate of 1.6 inch (4 cm) per year!", 
    "70. Pluto is named after the Roman god of the underworld, not the Disney Dog.", 
    "71. Spacesuit helmets have a Velcro patch, to help astronauts itch.", 
    "72. The ISS is visible to more than 90% of the Earth's population.", 
    "73. Saturn is the only planet that could oat in water.", 
    "74. Asteroids are the byproducts of formations in the solar system, more than 4 billion years ago.", 
    "75. Astronauts can't burp in space.", 
    "76. Uranus was originally called \"George's Star\".", 
    "77. A sunset on Mars is blue.", 
    "78. The Earth weighs about 81 times more than the Moon.", 
    "79. The first living mammal to go into space was a dog named \"Laika\" from Russia.", 
    "80. The word \"astronaut\" means \"star sailor\" in its origins.", 
    "81. \"NASA\" stands for National Aeronautics and Space Administration.", 
    "82. Gennady Padalka has spent more time in space than anyone else.", 
    "83. Mercury has no atmosphere, which means there is no wind or weather.", 
    "84. In China, the Milky Way is known as the \"Silver River\".", 
    "85. Red Dwarf stars that are low in mass can burn continually for up to 10 trillion years!", 
    "86. Scientists once believed that the same side of Mercury always faced the Sun.", 
    "87. Jupiter's Red Spot is shrinking.", 
    "88. A large percentage of asteroids are pulled in by Jupiter's gravity.", 
    "89. A day on Mercury is equivalent to 58 Earth days.", 
    "90. As space has no gravity, pens won't work.", 
    "91. On average it takes the light only 1.3 seconds to travel from the Moon to Earth.", 
    "92. There are 88 recognized star constellations in our night sky.", 
    "93. The center of a comet is called a \"nucleus\".", 
    "94. As early as 240BC the Chinese began to document the appearance of Halley's Comet.", 
    "95. In 2006, the International Astronomical Union reclassified Pluto as a dwarf planet.", 
    "96. There are 5 Dwarf Planets recognized in our Solar System.", 
    "97. Mars is the most likely planet in our solar system to be hospitable to life.", 
    "98. Halley's Comet will pass over Earth again on 26th July 2061.", 
    "99. There is a planet half the radius of the Earth with a surface made up of diamonds.", 
    "100. Buzz Lightyear from Toy Story has actually been to outer space!"]
    print("\nDid you know?\nFun Fact: #%s" % fun_facts_cosmos[random.randint(0, 99)])

#-------------------------------------------------------------------------------







#==============================================================================#
#                                                                              #
#                                  MAIN CODE                                   #
#                                                                              #
#==============================================================================#

#-------------------------------------------------------------------------------


#===============================================================================
# utility functions
#===============================================================================

def printSelectedFile(pathToFile, name):
    nameLength = len(name)
    print('\n\n\
========' + nameLength*'=' + '\n\
=== %s ===\n\
========' % (name) + nameLength*'=' + '\n%s' % (pathToFile))


def printCustomMessage(name):
    nameLength = len(name)
    print('\n\n\
========' + nameLength*'=' + '\n\
=== %s ===\n\
========' % (name) + nameLength*'=')


def isTarfileGood(pathToFileInRes):
    try:
        tar = tarfile.open(pathToFileInRes, 'r')
        try:
            members = tar.getmembers()
            tar.close()
            return True
        except (tarfile.TarError) as e:
            #print("\nTarfile corrupted ERROR: %s in:\n%s" % (e, pathToFileInRes))
            return False
        finally:
            tar.close()
    except (Exception) as e:
        #print("\nTarfile ERROR: %s in:\n%s" % (e, pathToFileInRes))
        return False


def extractTarfile(pathToDir, pathToFileInRes):
    try:
        tar = tarfile.open(pathToFileInRes, 'r')
        try:
            tar.extractall(path = pathToDir)
            tar.close()
        except (tarfile.TarError) as e:
            print("\nTarfile extraction ERROR: %s in:\n%s" % (e, pathToFileInRes))
            pressEnterToExit()
        finally:
            tar.close()
    except (Exception) as e:
        print("\nTarfile extraction ERROR: %s in:\n%s" % (e, pathToFileInRes))
        pressEnterToExit()


def createTarfile(pathToDir, fileName):
    try:
        tar = tarfile.open(fileName, 'w')
        try:
            for item in listDirectory(pathToDir):
                tar.add(os.path.join(pathToDir, item), arcname = item)
            tar.close()
        except (tarfile.TarError) as e:
            print("\nTarfile creation ERROR: %s in:\n%s" % (e, fileName))
            pressEnterToExit()
        finally:
            tar.close()
    except (Exception) as e:
        print("\nTarfile creation ERROR: %s in:\n%s" % (e, fileName))
        pressEnterToExit()


def createDir(pathToDir):
    if not os.path.exists(pathToDir):
        try:
            os.mkdir(pathToDir)
        except (OSError) as e:
            print("\nDirectory creation ERROR: %s - %s" % (e.filename, e.strerror))
        except (Exception) as e:
            print("\nDirectory creation ERROR: %s" % (e))


def removeDir(pathToDir):
    if os.path.exists(pathToDir):
        try:
            shutil.rmtree(pathToDir)
        except (shutil.Error, OSError, IOError, Exception) as e:
            print("\nDirectory removal ERROR: %s" % (e))


def renameFile(fileNameOld, fileNameNew):
    try:
        os.rename(fileNameOld, fileNameNew)
    except (OSError) as e:
        print("\nFile rename ERROR: %s - %s" % (e.filename, e.strerror))
    except (Exception) as e:
        print("\nFile rename ERROR: %s" % (e))


def removeFile2(pathToDir, fileName):
    try:
        os.remove(os.path.join(pathToDir, fileName))
        print("\n\n%s\t deleted from:\t%s" % (fileName, pathToDir))
    except (OSError) as e:
        print("\nFile remove ERROR: %s - %s" % (e.filename, e.strerror))
    except (Exception) as e:
        print("\nFile remove ERROR: %s" % (e))


def removeFile(pathToFile):
    pathToDir = os.path.dirname(pathToFile)
    fileName = os.path.basename(pathToFile)
    try:
        os.remove(pathToFile)
        print("%s\t deleted from:\t%s" % (fileName, pathToDir))
    except (OSError) as e:
        print("\nFile remove ERROR: %s - %s" % (e.filename, e.strerror))
    except (Exception) as e:
        print("\nFile remove ERROR: %s" % (e))


def listDirectory(pathToDir):
    listDir = []
    try:
        listDir = os.listdir(pathToDir)
    except (OSError) as e:
        print("\nDirectory listing ERROR: %s - %s" % (e.filename, e.strerror))
        pressEnterToExit()
    except (Exception) as e:
        print("\nDirectory listing ERROR: %s" % (e))
        pressEnterToExit()
    return listDir

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
        print("%s\t copied to:\t%s" % (os.path.basename(pathToFileInRes), pathToDirTempArtifacts))
    except (shutil.Error, OSError, IOError, Exception) as e:
        print("\nFile copy ERROR: %s" % (e))
        pressEnterToExit()


def setNewFileNameInInstallerScripts(pathToDirTemp, pathToFileInRes, fileMatcherInstaller, fileMatcher):
    fileName = os.path.basename(pathToFileInRes)
    listDirTemp = listDirectory(pathToDirTemp)
    for tempFile in listDirTemp:
        tempFilePath = os.path.join(pathToDirTemp, tempFile)
        if os.path.isfile(tempFilePath):
            if fileMatcherInstaller.search(tempFile):
                try:
                    f = open(tempFilePath, 'r')
                    try:
                        fileContent = f.read()
                        f.close()
                        fileContent = fileMatcher.sub(fileName, fileContent)
                    except (OSError, IOError) as e:
                        print("\nInstaller script reading ERROR: %s - %s" % (e.filename, e.strerror))
                    finally:
                        f.close()
                except (Exception) as e:
                    print("\nInstaller script reading ERROR: %s" % (e))
                try:
                    f = open(tempFilePath, 'w')
                    try:
                        f.write(fileContent)
                        f.close()
                    except (OSError, IOError) as e:
                        print("\nInstaller script writing ERROR: %s - %s" % (e.filename, e.strerror))
                    finally:
                        f.close()
                except (Exception) as e:
                    print("\nInstaller script writing ERROR: %s" % (e))
                print("%s\t updated in:\t%s" % (fileName, tempFilePath))


def renameStratixFile(fileNameTemp, fileNameNew):
    renameFile(fileNameTemp, fileNameNew)
    if os.path.isfile(fileNameNew) and os.path.getsize(fileNameNew) > 0:
        printSelectedFile(fileNameNew, 'new Stratix file')
        print('modified: %s\n' % (getLastModificationTimeAsString(fileNameNew)))
    else:
        print("\nSomething went wrong. New Stratix file not generated correctly...")
        print("\nPlease manually check file: %s" % (fileNameTemp))

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


def printProgress(copied, fileSize, speedCurrent = 1048576.0, speedAverage = 1048576.0):
    percent = (copied / fileSize) * 100
    if percent > 100.0:
        percent = 100.0
    dataLeft = (fileSize - copied) #Bytes
    timeLeftSeconds = (dataLeft / speedAverage) #Seconds

    timeLeftHours = timeLeftSeconds / 3600
    timeLeftSeconds = timeLeftSeconds % 3600
    timeLeftMinutes = timeLeftSeconds / 60
    timeLeftSeconds = timeLeftSeconds % 60

    #padding = len(str(int(fileSize)))
    copied, copiedUnit = getUnit(copied)
    fileSize, fileSizeUnit = getUnit(fileSize)
    speedCurrent, speedCurrentUnit = getUnit(speedCurrent)

    symbolDone = '='
    symbolLeft = '-'
    sizeTotal = 20
    sizeDone = int((percent / 100) * sizeTotal)
    sizeLeft = sizeTotal - sizeDone
    progressBar = '[' + sizeDone*symbolDone + sizeLeft*symbolLeft + ']'
    sys.stdout.write('\r%3d%% %s [%3.1d%s/%3.1d%s]  [%6.2f%s/s] %3.1dh%2.2dm%2.2ds' % (percent, progressBar, copied, copiedUnit, fileSize, fileSizeUnit, speedCurrent, speedCurrentUnit, timeLeftHours, timeLeftMinutes, timeLeftSeconds))
    sys.stdout.flush()
    #time.sleep(0.01) #### DELETE AFTER DEVELOPMENT ##########################################################################################################

#-------------------------------------------------------------------------------


#===============================================================================
# functions to calculate checksum
#===============================================================================

def getChecksumUsingZutil(fileNameTemp, fileMatcher, path_to_zutil):
    fileNameNew = ""
    if os.path.isfile(fileNameTemp):
        try:
            zutilOutput = subprocess.check_output('%s adler32 %s' % (path_to_zutil, fileNameTemp)).decode(sys.stdout.encoding).strip()
            #print('\nzutil output:\n%s' % (zutilOutput))

            fileNamePrepend = fileMatcher.sub(r'\1', fileNameTemp)
            fileNameAppend = fileMatcher.sub(r'\4', fileNameTemp)
            checksumNew = fileMatcher.sub(r'\3', zutilOutput).upper()
            fileNameNew = fileNamePrepend + '0x' + checksumNew + filenameAppend
        except (Exception) as e:
            print ("\nCalculate checksum ERROR: %s" % (e))
    else:
        print('\nERROR: Could not find new stratix image file to calculate checksum')
    return fileNameNew


def getChecksum(fileNameTemp, fileMatcher):
    fileNameNew = ""
    if os.path.isfile(fileNameTemp):
        try:
            f = open(fileNameTemp, 'rb')
            checksum = 1
            print("\n\ncalculating checksum")

            fileSize = 1
            try:
                fileSize = os.stat(fileNameTemp).st_size
            except (OSError, IOError, Exception) as e:
                print("\nGetting file info ERROR: %s" % (e))
            if fileSize <= 0:
                fileSize = 1
            timeStarted = time.time()
            data_step = 131072
            dataMark = 0
            time_step = 1.0
            timeMark = time.time()
            timeMarkData = 0
            timeNow = 0
            timeNowData = 0
            speedCurrent = 1048576.0
            speedAverage = 1048576.0

            try:
                while 1:
                    buffer = f.read(128*1024)
                    if not buffer:
                        break
                    checksum = zlib.adler32(buffer, checksum)

                    timeNow = time.time()
                    timeNowData += len(buffer)
                #update Current Speed
                    if timeNow >= (timeMark + time_step):
                        timeDiff = timeNow - timeMark
                        if timeDiff == 0:
                            timeDiff = 0.1
                        dataDiff = timeNowData - timeMarkData
                        timeMark = timeNow
                        timeMarkData = timeNowData
                        speedCurrent = (dataDiff / timeDiff) #Bytes per second
                #update Average Speed and print progress
                    if timeNowData >= (dataMark + data_step):
                        timeDiff = timeNow - timeStarted
                        if timeDiff == 0:
                            timeDiff = 0.1
                        dataMark = timeNowData
                        speedAverage = (timeNowData / timeDiff) #Bytes per second
                #print progress
                        printProgress(timeNowData, fileSize, speedCurrent, speedAverage)
                printProgress(timeNowData, fileSize, speedCurrent, speedAverage)
                print()

                f.close()
            except (OSError, IOError) as e:
                print("\nCalculate checksum ERROR: %s - %s" % (e.filename, e.strerror))
            finally:
                f.close()
            checksum = checksum & 0xffffffff
            #print("%d %s" % (checksum, (hex(checksum))))

            fileNamePrepend = fileMatcher.sub(r'\1', fileNameTemp)
            fileNameAppend = fileMatcher.sub(r'\4', fileNameTemp)
            checksumNew = '0x' + (hex(checksum)[2:].zfill(8)).upper()
            fileNameNew = fileNamePrepend + checksumNew + fileNameAppend
        except (Exception) as e:
            print ("\nCalculate checksum ERROR: %s" % (e))
    else:
        print('\nERROR: Could not find new stratix image file to calculate checksum')
    return fileNameNew

#-------------------------------------------------------------------------------


#===============================================================================
# custom implementation of copyfileobj from shutil LIBRARY (enable displaying copy file progress)
#===============================================================================

def copyfileobj(fsrc, fdst, src, length=16*1024):
    fileSize = 1
    try:
        fileSize = os.stat(src).st_size
    except (OSError, IOError, Exception) as e:
        print("\nGetting file info ERROR: %s" % (e))
    if fileSize <= 0:
        fileSize = 1
    timeStarted = time.time()
    data_step = 131072
    dataMark = 0
    time_step = 1.0
    timeMark = time.time()
    timeMarkData = 0
    timeNow = 0
    timeNowData = 0
    speedCurrent = 1048576.0
    speedAverage = 1048576.0

    # try:
    while 1:
        buffer = fsrc.read(length)
        if not buffer:
            break
        fdst.write(buffer)

        timeNow = time.time()
        timeNowData += len(buffer)
    #update Current Speed
        if timeNow >= (timeMark + time_step):
            timeDiff = timeNow - timeMark
            if timeDiff == 0:
                timeDiff = 0.1
            dataDiff = timeNowData - timeMarkData
            timeMark = timeNow
            timeMarkData = timeNowData
            speedCurrent = (dataDiff / timeDiff) #Bytes per second
    #update Average Speed and print progress
        if timeNowData >= (dataMark + data_step):
            timeDiff = timeNow - timeStarted
            if timeDiff == 0:
                timeDiff = 0.1
            dataMark = timeNowData
            speedAverage = (timeNowData / timeDiff) #Bytes per second
    #print progress
            printProgress(timeNowData, fileSize, speedCurrent, speedAverage)
    printProgress(timeNowData, fileSize, speedCurrent, speedAverage)
    print()

    # except (OSError, IOError) as e:
        # print("\nFile copy ERROR: %s - %s" % (e.filename, e.strerror))
        # pressEnterToExit()
    # finally:
        # fdst.close()
        # fsrc.close()

#-------------------------------------------------------------------------------


#===============================================================================
# functions to copy / download Nahka and Stratix files
#===============================================================================

def getFileFromArtifactory(pathToFile, pathToFileInRes):
    import requests
    try:
        response = requests.get(pathToFile, stream = True)
        response.raise_for_status()
        print("downloading file to %s" % os.path.dirname(pathToFileInRes))
        fileSize = int(response.headers['Content-length'])
        try:
            f = open(pathToFileInRes, 'wb')

            timeStarted = time.time()
            data_step = 131072
            dataMark = 0
            time_step = 1.0
            timeMark = time.time()
            timeMarkData = 0
            timeNow = 0
            timeNowData = 0
            speedCurrent = 1048576.0
            speedAverage = 1048576.0

            try:
                while 1:
                    buffer = response.raw.read(128)
                    if not buffer:
                        break
                    f.write(buffer)

                    timeNow = time.time()
                    timeNowData += len(buffer)
                #update Current Speed
                    if timeNow >= (timeMark + time_step):
                        timeDiff = timeNow - timeMark
                        if timeDiff == 0:
                            timeDiff = 0.1
                        dataDiff = timeNowData - timeMarkData
                        timeMark = timeNow
                        timeMarkData = timeNowData
                        speedCurrent = (dataDiff / timeDiff) #Bytes per second
                #update Average Speed and print progress
                    if timeNowData >= (dataMark + data_step):
                        timeDiff = timeNow - timeStarted
                        if timeDiff == 0:
                            timeDiff = 0.1
                        dataMark = timeNowData
                        speedAverage = (timeNowData / timeDiff) #Bytes per second
                #print progress
                        printProgress(timeNowData, fileSize, speedCurrent, speedAverage)
                printProgress(timeNowData, fileSize, speedCurrent, speedAverage)
                print()

                f.close()
            except (OSError, IOError) as e:
                print("\nFile download ERROR: %s - %s" % (e.filename, e.strerror))
                pressEnterToExit()
            finally:
                f.close()
        except (Exception) as e:
            print("\nFile download ERROR: %s - %s" % (e))
            pressEnterToExit()
    except (requests.exceptions.HTTPError, requests.exceptions.RequestException, Exception) as e:
        print("\nFile download ERROR: %s" % (e))
        pressEnterToExit()



def getFileFromNetwork(pathToFile, pathToDirRes):
    print("copying file to %s" % (pathToDirRes))
    try:
        #shutil.copy2(pathToFile, pathToDirRes)
        copy2(pathToFile, pathToDirRes)
    except (shutil.Error, OSError, IOError, Exception) as e:
        print("\nFile copy ERROR: %s" % (e))
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
            import requests
        except (ImportError, Exception) as e:
            print("\n%s" % e)
            print("Script will now attempt to install required module")
            pressEnterToContinue()
            installRequests()
        try:
            import requests
        except (ImportError, Exception) as e:
            print("\n%s\nCould not get requests module from pypi.org" % e)
            print("If you need to get Stratix or Nahka file from the web you will need to manually download it to the local directory (and add path to it in the ini file)\n")
            pressEnterToContinue()
        statusCode = 404
        try:
            response = requests.head(pathToFile)
            print('modified: %s (on server)\n' % (response.headers['last-modified']))
            statusCode = response.status_code == (200 or 300 or 301 or 302 or 303 or 307 or 308) # statement must be in parentheses...
            return statusCode
        except (requests.exceptions.HTTPError, requests.exceptions.RequestException, Exception) as e:
            print("Request Header ERROR: %s[ status code: %s ]\nYou probably need authentication to download that file..." % (e, statusCode))
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
        print("\n%s\nGetting file name from URL ^^^ABOVE ERROR: %s\n(Please specify correct fileMatcher as 5th parameter in \"handleGettingFile\" function)" % (pathToFile, e))
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
    printSelectedFile(pathToFile, name)
    pathIsUrl = isPathUrl(pathToFile, urlMatcher)
    pathToFileInRes = getPathToFileInRes(pathToFile, pathIsUrl, pathToDirRes, fileMatcher)

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
            print("\nCould not find the file in the specified location, but the file is present in %s\n" % (pathToDirRes))
            pressEnterToContinue()
        else:
            print("\nCould not find file in the specified location - the file is present in %s but it is corrupted\n" % (pathToDirRes))
            pressEnterToExit()
    else:
        print("\nCould not find anything! Please specify possible file locations in the ini file...\n")
        pressEnterToExit()
    return pathToFileInRes

#-------------------------------------------------------------------------------


#===============================================================================
# functions to get paths to latest Nahka and Stratix files
#===============================================================================

def createNewIniFile(pathToFile):
    try:
        f = open(pathToFile, 'w')
        try:
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
3. but if C:\LocalDir contains Nahka and Stratix image it will copy both of them from C:\\LocalDir\n\
4. Nahka file in stratix10-aaib\\tmp-glibc\\deploy\\images\\stratix10-aaib path will be ignored because it has no use\n\n\
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
            f.close()
        except (OSError, IOError) as e:
            print("\nInifile creation ERROR: %s - %s" % (e.filename, e.strerror))
        finally:
            f.close()
    except (Exception) as e:
        print("\nInifile creation ERROR: %s" % (e))

def loadIniFileIntoList(pathToFile):
    if os.path.isfile(pathToFile):
        try:
            f = open(pathToFile, 'r')
            try:
                linesList = f.readlines()
                f.close()
                return linesList
            except (OSError, IOError) as e:
                print("\nInifile loading ERROR: %s - %s" % (e.filename, e.strerror))
                return []
            finally:
                f.close()
        except (Exception) as e:
            print("\nInifile loading ERROR: %s" % (e))
            return []
    print("\nInitialization file not found...")
    createNewIniFile(pathToFile)
    print("%s file has been created!!!\n" % (pathToFile))
    print("In the first run this script will search for Nahka and Stratix files in the current working directory (%s)" % (os.path.dirname(os.path.realpath(sys.argv[0]))))
    print("Every next time it will search for Nahka and Stratix files in locations defined by you in the ini file (%s)" % (pathToFile))
    pressEnterToContinue()
    return []


def getDateFromNahkaFile(fileMatcher):
    return lambda f : fileMatcher.sub(r'\2', f)


def getLastModificationTime(pathToFile):
    secondsSinceEpoch = 0
    try:
        secondsSinceEpoch = os.path.getmtime(pathToFile)
    except (OSError) as e:
        print("\nGetting file info ERROR: %s - %s" % (e.filename, e.strerror))
        pressEnterToExit()
    return secondsSinceEpoch


def getLastModificationTimeAsString(pathToFile):
    return time.ctime(getLastModificationTime(pathToFile))


def getPathToLatestFileInDir(pathToDir, matcher, comparator):
    filesList = []
    for item in listDirectory(pathToDir):
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
# === MAIN FUNCTION ===
#===============================================================================

def main():
    # path_to_zutil = 'C:\zutil\zutil.exe'
    # if len(sys.argv) == 2:
        # path_to_zutil = sys.argv[1]

    pathToFileIni = r'./stratix_nahka_swapper.ini'
    pathToDirRes = r'./resources'
    pathToDirTemp = r'./SRM_temp'
    pathToDirTempArtifacts = r'./SRM_temp/artifacts'
    fileNameStratixTemp = r'./SRM-rfsw-image-install_z-uber-0x00000000.tar'

    urlMatcher = re.compile(r'(https://|http://|ftp://)')
    fileMatcher = re.compile(r'(.*)(0x)([a-fA-F0-9]{1,8})(.*)')
    fileMatcherNahka = re.compile(r'(FRM-rfsw-image-install_)([0-9]{14})(-multi.tar)')
    fileMatcherStratix = re.compile(r'.*(SRM-rfsw-image-install_z-uber-0x)([a-fA-F0-9]{8})(.tar).*')
    fileMatcherInstaller = re.compile(r'.*-installer.sh')
    pathMatcherStratix = re.compile(r'.*(stratix10-aaib)([\/\\]{1,2})(tmp-glibc)([\/\\]{1,2})(deploy)([\/\\]{1,2})(images)([\/\\]{1,2})(stratix10-aaib).*')

    pathsToLatestFiles = getPathsToLatestFiles(pathToFileIni, fileMatcherNahka, fileMatcherStratix, pathMatcherStratix)
    pathToFileNahka = pathsToLatestFiles.get("pathToLatestFileNahka", "")
    pathToFileStratix = pathsToLatestFiles.get("pathToLatestFileStratix", "")

    printFunFact()

    pathToFileInResNahka = handleGettingFile(pathToFileNahka, pathToDirRes, 'selected Nahka file', urlMatcher)
    pathToFileInResStratix = handleGettingFile(pathToFileStratix, pathToDirRes, 'selected Stratix file', urlMatcher, fileMatcherStratix)


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
