#!/usr/bin/python

#-------------------------------------------------------------------------------
# supports:     python 2.6, 2.7
#               python 3.4 (or newer)
#
# author:       dawid.koszewski@nokia.com
# date:         2019.10.30
# update:       2019.11.25
# version:      01x
#
# written in Notepad++
#
#
#-------------------------------------------------------------------------------


################# KNOWN ISSUES: #################
# - no possibility to install requests module on wrlinb (module is needed to download Stratix from artifactory)
# - when using in windows environment - executions permission in files are missing


# please don't be afraid of this script
# the main function is located at the very bottom - take a look at it first - everything will become clear


#===============================================================================
# import section
#===============================================================================

#from __builtin__ import open as bltn_open      #imported below in try except block
import copy
import errno
import io
import os
import random
import re
#import requests    #imported below in isFileAvailable and getFileFromArtifactory functions
import shutil
import stat
import struct
import subprocess
import sys
import tarfile
import time
#import zlib        #imported below in try except block

#-------------------------------------------------------------------------------


#===============================================================================
# helper functions needed for import handling and also used throughout the code
#===============================================================================

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

#-------------------------------------------------------------------------------


#===============================================================================
# further import handling
#===============================================================================

try:
    from __builtin__ import open as bltn_open #python2 only
except (SyntaxError, Exception) as e:
    from builtins import open as bltn_open #python3 only

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


#===============================================================================
# python version global variables
#===============================================================================

PYTHON_MAJOR = sys.version_info[0]
PYTHON_MINOR = sys.version_info[1]
PYTHON_PATCH = sys.version_info[2]

def printDetectedAndSupportedPythonVersion():
    if((PYTHON_MAJOR == 2 and PYTHON_MINOR == 6 and PYTHON_PATCH >= 6)
    or (PYTHON_MAJOR == 2 and PYTHON_MINOR == 7 and PYTHON_PATCH >= 4)
    or (PYTHON_MAJOR == 3 and PYTHON_MINOR == 3 and PYTHON_PATCH >= 5)
    or (PYTHON_MAJOR == 3 and PYTHON_MINOR == 4 and PYTHON_PATCH >= 5)
    or (PYTHON_MAJOR == 3 and PYTHON_MINOR == 5 and PYTHON_PATCH >= 2)
    or (PYTHON_MAJOR == 3 and PYTHON_MINOR >= 6)):
        print("\ndetected python version: %d.%d.%d [SUPPORTED]\n(tested in 2.6.6, 2.7.4, 3.3.5, 3.8.0)" % (PYTHON_MAJOR, PYTHON_MINOR, PYTHON_PATCH))
    elif (PYTHON_MAJOR >= 4):
        print("\ndetected python version: %d.%d.%d [PROBABLY SUPPORTED]\n(tested in 2.6.6, 2.7.4, 3.3.5, 3.8.0)" % (PYTHON_MAJOR, PYTHON_MINOR, PYTHON_PATCH))
    else:
        print("\ndetected python version: %d.%d.%d [NOT TESTED]\n(it is highly recommended to upgrade to 2.6.6, 2.7.4, 3.3.5, 3.8.0 or any newer)" % (PYTHON_MAJOR, PYTHON_MINOR, PYTHON_PATCH))

#-------------------------------------------------------------------------------


################################################################################
#                                                                              #
# This is only a part of SHUTIL LIBRARY - needed to enable progress bar.       #
#                                                                              #
# contributors: gvanrossum, serhiy-storchaka, birkenfeld, pitrou, benjaminp,   #
#               rhettinger, merwok, loewis, tim-one, nnorwitz, doerwalter,     #
#               ronaldoussoren, ned-deily, florentx, freddrake, csernazs,      #
#               brettcannon, warsaw                                            #
#                                                                              #
# date:         24 Oct 2018                                                    #
# link:         https://github.com/python/cpython/blob/2.7/Lib/shutil.py       #
#                                                                              #
################################################################################

"""Utility functions for copying and archiving files and directory trees.

XXX The functions here don't copy the resource fork or other metadata on Mac.

"""

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

#-------------------------------------------------------------------------------


################################################################################
#                                                                              #
# This is only a PART of TARFILE LIBRARY - needed to CHECK TAR file INTEGRITY. #
# It contains PATCH TO BUG present in python 2.6, 2.7, 3.4, 3.5.               #
#                                                                              #
# The bug allowed to extract corrupted tar file without raising any errors     #
# (regardless of errorlevel setting).                                          #
#                                                                              #
# There are two versions used by this script - for python 2.* and 3.0-3.5.     #
# Below you can find version used by this script for python [ 2.* ].           #
#                                                                              #
# link to discussion:       https://bugs.python.org/issue24259                 #
# link to patch:            https://hg.python.org/cpython/rev/372aa98eb72e     #
#                                                                              #
# contributors: gustaebel, loewis, birkenfeld, nnorwitz, serhiy-storchaka,     #
#               tim-one, akuchling, orsenthil, jackjansen, rhettinger,         #
#               brettcannon, vadmium, ronaldoussoren, pjenvey, gvanrossum,     #
#               ezio-melotti, mdickinson, benjaminp, asvetlov                  #
#                                                                              #
# date:         30 Oct 2016                                                    #
# link:         https://github.com/python/cpython/blob/2.7/Lib/tarfile.py      #
#                                                                              #
################################################################################

#-------------------------------------------------------------------
# tarfile.py   [[[   branch 2.7   ]]] - used in this script for python 2.*
#-------------------------------------------------------------------
# Copyright (C) 2002 Lars Gustaebel <lars@gustaebel.de>
# All rights reserved.
#
# Permission  is  hereby granted,  free  of charge,  to  any person
# obtaining a  copy of  this software  and associated documentation
# files  (the  "Software"),  to   deal  in  the  Software   without
# restriction,  including  without limitation  the  rights to  use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies  of  the  Software,  and to  permit  persons  to  whom the
# Software  is  furnished  to  do  so,  subject  to  the  following
# conditions:
#
# The above copyright  notice and this  permission notice shall  be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS  IS", WITHOUT WARRANTY OF ANY  KIND,
# EXPRESS OR IMPLIED, INCLUDING  BUT NOT LIMITED TO  THE WARRANTIES
# OF  MERCHANTABILITY,  FITNESS   FOR  A  PARTICULAR   PURPOSE  AND
# NONINFRINGEMENT.  IN  NO  EVENT SHALL  THE  AUTHORS  OR COPYRIGHT
# HOLDERS  BE LIABLE  FOR ANY  CLAIM, DAMAGES  OR OTHER  LIABILITY,
# WHETHER  IN AN  ACTION OF  CONTRACT, TORT  OR OTHERWISE,  ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
#
"""Read from and write to tar format archives.
"""

__version__ = "$Revision: 85213 $"
# $Source$

version     = "0.9.0"
__author__  = "Lars Gustaebel (lars@gustaebel.de)"
__date__    = "$Date$"
__cvsid__   = "$Id$"
__credits__ = "Gustavo Niemeyer, Niels Gustaebel, Richard Townsend."

#---------------------------------------------------------
# tar constants
#---------------------------------------------------------
NUL = b"\0"                     # the null character
BLOCKSIZE = 512                 # length of processing blocks
RECORDSIZE = BLOCKSIZE * 20     # length of records
GNU_MAGIC = b"ustar  \0"        # magic gnu tar string
POSIX_MAGIC = b"ustar\x0000"    # magic posix tar string

LENGTH_NAME = 100               # maximum length of a filename
LENGTH_LINK = 100               # maximum length of a linkname
LENGTH_PREFIX = 155             # maximum length of the prefix field

REGTYPE = b"0"                  # regular file
AREGTYPE = b"\0"                # regular file
LNKTYPE = b"1"                  # link (inside TarFile)
SYMTYPE = b"2"                  # symbolic link
CHRTYPE = b"3"                  # character special device
BLKTYPE = b"4"                  # block special device
DIRTYPE = b"5"                  # directory
FIFOTYPE = b"6"                 # fifo special device
CONTTYPE = b"7"                 # contiguous file

GNUTYPE_LONGNAME = b"L"         # GNU tar longname
GNUTYPE_LONGLINK = b"K"         # GNU tar longlink
GNUTYPE_SPARSE = b"S"           # GNU tar sparse file

XHDTYPE = b"x"                  # POSIX.1-2001 extended header
XGLTYPE = b"g"                  # POSIX.1-2001 global header
SOLARIS_XHDTYPE = b"X"          # Solaris extended header

USTAR_FORMAT = 0                # POSIX.1-1988 (ustar) format
GNU_FORMAT = 1                  # GNU tar format
PAX_FORMAT = 2                  # POSIX.1-2001 (pax) format
DEFAULT_FORMAT = GNU_FORMAT

#---------------------------------------------------------
# TarFile constants
#---------------------------------------------------------
# File types that TarFile supports:
SUPPORTED_TYPES = (REGTYPE, AREGTYPE, LNKTYPE,
                   SYMTYPE, DIRTYPE, FIFOTYPE,
                   CONTTYPE, CHRTYPE, BLKTYPE,
                   GNUTYPE_LONGNAME, GNUTYPE_LONGLINK,
                   GNUTYPE_SPARSE)

# File types that will be treated as a regular file.
REGULAR_TYPES = (REGTYPE, AREGTYPE,
                 CONTTYPE, GNUTYPE_SPARSE)

# File types that are part of the GNU tar format.
GNU_TYPES = (GNUTYPE_LONGNAME, GNUTYPE_LONGLINK,
             GNUTYPE_SPARSE)

# Fields from a pax header that override a TarInfo3 attribute.
PAX_FIELDS = ("path", "linkpath", "size", "mtime",
              "uid", "gid", "uname", "gname")

# Fields from a pax header that are affected by hdrcharset.
#PAX_NAME_FIELDS = {"path", "linkpath", "uname", "gname"}
PAX_NAME_FIELDS = ("path", "linkpath", "uname", "gname")

# Fields in a pax header that are numbers, all other fields
# are treated as strings.
PAX_NUMBER_FIELDS = {
    "atime": float,
    "ctime": float,
    "mtime": float,
    "uid": int,
    "gid": int,
    "size": int
}

#---------------------------------------------------------
# initialization
#---------------------------------------------------------
# if os.name in ("nt", "ce"):
ENCODING = "utf-8"
# else:
    # ENCODING = sys.getfilesystemencoding()

#---------------------------------------------------------
# Some useful functions
#---------------------------------------------------------
def stn(s, length):
    """Convert a python string to a null-terminated string buffer.
    """
    return s[:length] + (length - len(s)) * NUL

def nts(s):
    """Convert a null-terminated string field to a python string.
    """
    # Use the string up to the first null char.
    p = s.find("\0")
    if p == -1:
        return s
    return s[:p]

def nti(s):
    """Convert a number field to a python number.
    """
    # There are two possible encodings for a number field, see
    # itn() below.
    if s[0] != chr(0o200):
        try:
            n = int(nts(s).strip() or "0", 8)
        except ValueError:
            raise InvalidHeaderError("invalid header")
    else:
        n = long(0)
        for i in xrange(len(s) - 1):
            n <<= 8
            n += ord(s[i + 1])
    return n


def uts(s, encoding, errors):
    """Convert a unicode object to a string.
    """
    if errors == "utf-8":
        # An extra error handler similar to the -o invalid=UTF-8 option
        # in POSIX.1-2001. Replace untranslatable characters with their
        # UTF-8 representation.
        try:
            return s.encode(encoding, "strict")
        except UnicodeEncodeError:
            x = []
            for c in s:
                try:
                    x.append(c.encode(encoding, "strict"))
                except UnicodeEncodeError:
                    x.append(c.encode("utf8"))
            return "".join(x)
    else:
        return s.encode(encoding, errors)

def calc_chksums(buf):
    """Calculate the checksum for a member's header by summing up all
       characters except for the chksum field which is treated as if
       it was filled with spaces. According to the GNU tar sources,
       some tars (Sun and NeXT) calculate chksum with signed char,
       which will be different if there are chars in the buffer with
       the high bit set. So we calculate two checksums, unsigned and
       signed.
    """
    unsigned_chksum = 256 + sum(struct.unpack("148B", buf[:148]) + struct.unpack("356B", buf[156:512]))
    signed_chksum = 256 + sum(struct.unpack("148b", buf[:148]) + struct.unpack("356b", buf[156:512]))
    return unsigned_chksum, signed_chksum

class TarError(Exception):
    """Base exception."""
    pass
class ExtractError(TarError):
    """General exception for extract errors."""
    pass
class ReadError(TarError):
    """Exception for unreadable tar archives."""
    pass
class CompressionError(TarError):
    """Exception for unavailable compression methods."""
    pass
class StreamError(TarError):
    """Exception for unsupported operations on stream-like TarFile2s."""
    pass
class HeaderError(TarError):
    """Base exception for header errors."""
    pass
class EmptyHeaderError(HeaderError):
    """Exception for empty headers."""
    pass
class TruncatedHeaderError(HeaderError):
    """Exception for truncated headers."""
    pass
class EOFHeaderError(HeaderError):
    """Exception for end of file headers."""
    pass
class InvalidHeaderError(HeaderError):
    """Exception for invalid headers."""
    pass
class SubsequentHeaderError(HeaderError):
    """Exception for missing and invalid extended headers."""
    pass

#------------------------
# Extraction file object
#------------------------
class _FileInFile2(object):
    """A thin wrapper around an existing file object that
       provides a part of its data as an individual file
       object.
    """

    def __init__(self, fileobj, offset, size, sparse=None):
        self.fileobj = fileobj
        self.offset = offset
        self.size = size
        self.sparse = sparse
        self.position = 0

    def tell(self):
        """Return the current file position.
        """
        return self.position

    def seek(self, position):
        """Seek to a position in the file.
        """
        self.position = position

    def read(self, size=None):
        """Read data from the file.
        """
        if size is None:
            size = self.size - self.position
        else:
            size = min(size, self.size - self.position)

        if self.sparse is None:
            return self.readnormal(size)
        else:
            return self.readsparse(size)

    def __read(self, size):
        buf = self.fileobj.read(size)
        if len(buf) != size:
            raise ReadError("unexpected end of data")
        return buf

    def readnormal(self, size):
        """Read operation for regular files.
        """
        self.fileobj.seek(self.offset + self.position)
        self.position += size
        return self.__read(size)
#class _FileInFile2

class ExFileObject2(object):
    """File-like object for reading an archive member.
       Is returned by TarFile2.extractfile().
    """
    blocksize = 1024

    def __init__(self, tarfile, tarinfo):
        self.fileobj = _FileInFile2(tarfile.fileobj,
                                   tarinfo.offset_data,
                                   tarinfo.size,
                                   getattr(tarinfo, "sparse", None))
        self.name = tarinfo.name
        self.mode = "r"
        self.closed = False
        self.size = tarinfo.size

        self.position = 0
        self.buffer = ""

    def read(self, size=None):
        """Read at most size bytes from the file. If size is not
           present or None, read all data until EOF is reached.
        """
        if self.closed:
            raise ValueError("I/O operation on closed file")

        buf = ""
        if self.buffer:
            if size is None:
                buf = self.buffer
                self.buffer = ""
            else:
                buf = self.buffer[:size]
                self.buffer = self.buffer[size:]

        if size is None:
            buf += self.fileobj.read()
        else:
            buf += self.fileobj.read(size - len(buf))

        self.position += len(buf)
        return buf

    def tell(self):
        """Return the current file position.
        """
        if self.closed:
            raise ValueError("I/O operation on closed file")

        return self.position

    def seek(self, pos, whence=os.SEEK_SET):
        """Seek to a position in the file.
        """
        if self.closed:
            raise ValueError("I/O operation on closed file")

        if whence == os.SEEK_SET:
            self.position = min(max(pos, 0), self.size)
        elif whence == os.SEEK_CUR:
            if pos < 0:
                self.position = max(self.position + pos, 0)
            else:
                self.position = min(self.position + pos, self.size)
        elif whence == os.SEEK_END:
            self.position = max(min(self.size + pos, self.size), 0)
        else:
            raise ValueError("Invalid argument")

        self.buffer = ""
        self.fileobj.seek(self.position)

    def close(self):
        """Close the file object.
        """
        self.closed = True

    def __iter__(self):
        """Get an iterator over the file's lines.
        """
        while True:
            line = self.readline()
            if not line:
                break
            yield line
#class ExFileObject2

#------------------
# Exported Classes
#------------------
class TarInfo2(object):
    """Informational class which holds the details about an
       archive member given by a tar header block.
       TarInfo2 objects are returned by TarFile2.getmember(),
       TarFile2.getmembers() and TarFile2.gettarinfo() and are
       usually created internally.
    """

    def __init__(self, name=""):
        """Construct a TarInfo2 object. name is the optional name
           of the member.
        """
        self.name = name        # member name
        self.mode = 0o644        # file permissions
        self.uid = 0            # user id
        self.gid = 0            # group id
        self.size = 0           # file size
        self.mtime = 0          # modification time
        self.chksum = 0         # header checksum
        self.type = REGTYPE     # member type
        self.linkname = ""      # link name
        self.uname = ""         # user name
        self.gname = ""         # group name
        self.devmajor = 0       # device major number
        self.devminor = 0       # device minor number

        self.offset = 0         # the tar header starts here
        self.offset_data = 0    # the file's data starts here

        self.pax_headers = {}   # pax header information

    # In pax headers the "name" and "linkname" field are called
    # "path" and "linkpath".
    def _getpath(self):
        return self.name
    def _setpath(self, name):
        self.name = name
    path = property(_getpath, _setpath)

    def _getlinkpath(self):
        return self.linkname
    def _setlinkpath(self, linkname):
        self.linkname = linkname
    linkpath = property(_getlinkpath, _setlinkpath)

    def __repr__(self):
        return "<%s %r at %#x>" % (self.__class__.__name__,self.name,id(self))

    @classmethod
    def frombuf(cls, buf):
        """Construct a TarInfo2 object from a 512 byte string buffer.
        """
        if len(buf) == 0:
            raise EmptyHeaderError("empty header")
        if len(buf) != BLOCKSIZE:
            raise TruncatedHeaderError("truncated header")
        if buf.count(NUL) == BLOCKSIZE:
            raise EOFHeaderError("end of file header")

        chksum = nti(buf[148:156])
        if chksum not in calc_chksums(buf):
            raise InvalidHeaderError("bad checksum")

        obj = cls()
        obj.buf = buf
        obj.name = nts(buf[0:100])
        obj.mode = nti(buf[100:108])
        obj.uid = nti(buf[108:116])
        obj.gid = nti(buf[116:124])
        obj.size = nti(buf[124:136])
        obj.mtime = nti(buf[136:148])
        obj.chksum = chksum
        obj.type = buf[156:157]
        obj.linkname = nts(buf[157:257])
        obj.uname = nts(buf[265:297])
        obj.gname = nts(buf[297:329])
        obj.devmajor = nti(buf[329:337])
        obj.devminor = nti(buf[337:345])
        prefix = nts(buf[345:500])

        # Old V7 tar format represents a directory as a regular
        # file with a trailing slash.
        if obj.type == AREGTYPE and obj.name.endswith("/"):
            obj.type = DIRTYPE

        # Remove redundant slashes from directories.
        if obj.isdir():
            obj.name = obj.name.rstrip("/")

        # Reconstruct a ustar longname.
        if prefix and obj.type not in GNU_TYPES:
            obj.name = prefix + "/" + obj.name
        return obj

    @classmethod
    def fromtarfile(cls, tarfile):
        """Return the next TarInfo2 object from TarFile2 object
           tarfile.
        """
        buf = tarfile.fileobj.read(BLOCKSIZE)
        obj = cls.frombuf(buf)
        obj.offset = tarfile.fileobj.tell() - BLOCKSIZE
        return obj._proc_member(tarfile)

    def _proc_member(self, tarfile):
        """Choose the right processing method depending on
           the type and call it.
        """
        if self.type in (GNUTYPE_LONGNAME, GNUTYPE_LONGLINK):
            return self._proc_gnulong(tarfile)
        elif self.type == GNUTYPE_SPARSE:
            return self._proc_sparse(tarfile)
        elif self.type in (XHDTYPE, XGLTYPE, SOLARIS_XHDTYPE):
            return self._proc_pax(tarfile)
        else:
            return self._proc_builtin(tarfile)

    def _proc_builtin(self, tarfile):
        """Process a builtin type or an unknown type which
           will be treated as a regular file.
        """
        self.offset_data = tarfile.fileobj.tell()
        offset = self.offset_data
        if self.isreg() or self.type not in SUPPORTED_TYPES:
            # Skip the following data blocks.
            offset += self._block(self.size)
        tarfile.offset = offset

        # Patch the TarInfo2 object with saved global
        # header information.
        self._apply_pax_info(tarfile.pax_headers, tarfile.encoding, tarfile.errors)

        return self

    def _apply_pax_info(self, pax_headers, encoding, errors):
        """Replace fields with supplemental information from a previous
           pax extended or global header.
        """
        for keyword, value in pax_headers.iteritems():
            if keyword not in PAX_FIELDS:
                continue

            if keyword == "path":
                value = value.rstrip("/")

            if keyword in PAX_NUMBER_FIELDS:
                try:
                    value = PAX_NUMBER_FIELDS[keyword](value)
                except ValueError:
                    value = 0
            else:
                value = uts(value, encoding, errors)

            setattr(self, keyword, value)

        self.pax_headers = pax_headers.copy()

    def _block(self, count):
        """Round up a byte count by BLOCKSIZE and return it,
           e.g. _block(834) => 1024.
        """
        blocks, remainder = divmod(count, BLOCKSIZE)
        if remainder:
            blocks += 1
        return blocks * BLOCKSIZE

    def isreg(self):
        return self.type in REGULAR_TYPES
    def isfile(self):
        return self.isreg()
    def isdir(self):
        return self.type == DIRTYPE
    def issym(self):
        return self.type == SYMTYPE
    def islnk(self):
        return self.type == LNKTYPE
    def ischr(self):
        return self.type == CHRTYPE
    def isblk(self):
        return self.type == BLKTYPE
    def isfifo(self):
        return self.type == FIFOTYPE
    def issparse(self):
        return self.type == GNUTYPE_SPARSE
    def isdev(self):
        return self.type in (CHRTYPE, BLKTYPE, FIFOTYPE)
# class TarInfo2

class TarFile2(object):
    """The TarFile2 Class provides an interface to tar archives.
    """

    debug = 0                   # May be set from 0 (no msgs) to 3 (all msgs)

    dereference = False         # If true, add content of linked file to the
                                # tar file, else the link.

    ignore_zeros = False        # If true, skips empty or invalid blocks and
                                # continues processing.

    errorlevel = 1              # If 0, fatal errors only appear in debug
                                # messages (if debug >= 0). If > 0, errors
                                # are passed to the caller as exceptions.

    format = DEFAULT_FORMAT     # The format to use when creating an archive.

    encoding = ENCODING         # Encoding for 8-bit character strings.

    errors = None               # Error handler for unicode conversion.

    tarinfo = TarInfo2           # The default TarInfo2 class to use.

    fileobject = ExFileObject2   # The default ExFileObject2 class to use.

    def __init__(self, name=None, mode="r", fileobj=None, format=None,
            tarinfo=None, dereference=None, ignore_zeros=None, encoding=None,
            errors=None, pax_headers=None, debug=None, errorlevel=None):
        """Open an (uncompressed) tar archive `name'. `mode' is either 'r' to
           read from an existing archive, 'a' to append data to an existing
           file or 'w' to create a new file overwriting an existing one. `mode'
           defaults to 'r'.
           If `fileobj' is given, it is used for reading or writing data. If it
           can be determined, `mode' is overridden by `fileobj's mode.
           `fileobj' is not closed, when TarFile2 is closed.
        """
        modes = {"r": "rb", "a": "r+b", "w": "wb"}
        if mode not in modes:
            raise ValueError("mode must be 'r', 'a' or 'w'")
        self.mode = mode
        self._mode = modes[mode]

        if not fileobj:
            if self.mode == "a" and not os.path.exists(name):
                # Create nonexistent files in append mode.
                self.mode = "w"
                self._mode = "wb"
            fileobj = bltn_open(name, self._mode)
            self._extfileobj = False
        else:
            if name is None and hasattr(fileobj, "name"):
                name = fileobj.name
            if hasattr(fileobj, "mode"):
                self._mode = fileobj.mode
            self._extfileobj = True
        self.name = os.path.abspath(name) if name else None
        self.fileobj = fileobj

        # Init attributes.
        if format is not None:
            self.format = format
        if tarinfo is not None:
            self.tarinfo = tarinfo
        if dereference is not None:
            self.dereference = dereference
        if ignore_zeros is not None:
            self.ignore_zeros = ignore_zeros
        if encoding is not None:
            self.encoding = encoding

        if errors is not None:
            self.errors = errors
        elif mode == "r":
            self.errors = "utf-8"
        else:
            self.errors = "strict"

        if pax_headers is not None and self.format == PAX_FORMAT:
            self.pax_headers = pax_headers
        else:
            self.pax_headers = {}

        if debug is not None:
            self.debug = debug
        if errorlevel is not None:
            self.errorlevel = errorlevel

        # Init datastructures.
        self.closed = False
        self.members = []       # list of members as TarInfo2 objects
        self._loaded = False    # flag if all members have been read
        self.offset = self.fileobj.tell()
                                # current position in the archive file
        self.inodes = {}        # dictionary caching the inodes of
                                # archive members already added

        try:
            if self.mode == "r":
                self.firstmember = None
                self.firstmember = self.next()

            if self.mode == "a":
                # Move to the end of the archive,
                # before the first empty block.
                while True:
                    self.fileobj.seek(self.offset)
                    try:
                        tarinfo = self.tarinfo.fromtarfile(self)
                        self.members.append(tarinfo)
                    except EOFHeaderError:
                        self.fileobj.seek(self.offset)
                        break
                    except HeaderError as e:
                        raise ReadError(str(e))

            if self.mode in "aw":
                self._loaded = True

                if self.pax_headers:
                    buf = self.tarinfo.create_pax_global_header(self.pax_headers.copy())
                    self.fileobj.write(buf)
                    self.offset += len(buf)
        except:
            if not self._extfileobj:
                self.fileobj.close()
            self.closed = True
            raise

    @classmethod
    def open(cls, name=None, mode="r", fileobj=None, bufsize=RECORDSIZE, **kwargs):
        """Open a tar archive for reading, writing or appending. Return
           an appropriate TarFile2 class.

           mode:
           'r' or 'r:*' open for reading with transparent compression
           'r:'         open for reading exclusively uncompressed
           'r:gz'       open for reading with gzip compression
           'r:bz2'      open for reading with bzip2 compression
           'a' or 'a:'  open for appending, creating the file if necessary
           'w' or 'w:'  open for writing without compression
           'w:gz'       open for writing with gzip compression
           'w:bz2'      open for writing with bzip2 compression

           'r|*'        open a stream of tar blocks with transparent compression
           'r|'         open an uncompressed stream of tar blocks for reading
           'r|gz'       open a gzip compressed stream of tar blocks
           'r|bz2'      open a bzip2 compressed stream of tar blocks
           'w|'         open an uncompressed stream for writing
           'w|gz'       open a gzip compressed stream for writing
           'w|bz2'      open a bzip2 compressed stream for writing
        """

        if not name and not fileobj:
            raise ValueError("nothing to open")

        if mode in ("r", "r:*"):
            # Find out which *open() is appropriate for opening the file.
            def not_compressed(comptype):
                return cls.OPEN_METH[comptype] == 'taropen'
            for comptype in sorted(cls.OPEN_METH, key=not_compressed):
                func = getattr(cls, cls.OPEN_METH[comptype])
                if fileobj is not None:
                    saved_pos = fileobj.tell()
                try:
                    return func(name, "r", fileobj, **kwargs)
                except (ReadError, CompressionError) as e:
                    if fileobj is not None:
                        fileobj.seek(saved_pos)
                    continue
            raise ReadError("file could not be opened successfully")

        elif ":" in mode:
            filemode, comptype = mode.split(":", 1)
            filemode = filemode or "r"
            comptype = comptype or "tar"

            # Select the *open() function according to
            # given compression.
            if comptype in cls.OPEN_METH:
                func = getattr(cls, cls.OPEN_METH[comptype])
            else:
                raise CompressionError("unknown compression type %r" % comptype)
            return func(name, filemode, fileobj, **kwargs)

        elif mode in ("a", "w"):
            return cls.taropen(name, mode, fileobj, **kwargs)

        raise ValueError("undiscernible mode")

    @classmethod
    def taropen(cls, name, mode="r", fileobj=None, **kwargs):
        """Open uncompressed tar archive name for reading or writing.
        """
        if mode not in ("r", "a", "w"):
            raise ValueError("mode must be 'r', 'a' or 'w'")
        return cls(name, mode, fileobj, **kwargs)

    @classmethod
    def gzopen(cls, name, mode="r", fileobj=None, compresslevel=9, **kwargs):
        """Open gzip compressed tar archive name for reading or writing.
           Appending is not allowed.
        """
        if mode not in ("r", "w"):
            raise ValueError("mode must be 'r' or 'w'")

        try:
            import gzip
            gzip.GzipFile
        except (ImportError, AttributeError):
            raise CompressionError("gzip module is not available")

        try:
            fileobj = gzip.GzipFile(name, mode, compresslevel, fileobj)
        except OSError:
            if fileobj is not None and mode == 'r':
                raise ReadError("not a gzip file")
            raise

        try:
            t = cls.taropen(name, mode, fileobj, **kwargs)
        except IOError:
            fileobj.close()
            if mode == 'r':
                raise ReadError("not a gzip file")
            raise
        except:
            fileobj.close()
            raise
        t._extfileobj = False
        return t

    @classmethod
    def bz2open(cls, name, mode="r", fileobj=None, compresslevel=9, **kwargs):
        """Open bzip2 compressed tar archive name for reading or writing.
           Appending is not allowed.
        """
        if mode not in ("r", "w"):
            raise ValueError("mode must be 'r' or 'w'.")

        try:
            import bz2
        except ImportError:
            raise CompressionError("bz2 module is not available")

        if fileobj is not None:
            fileobj = _BZ2Proxy2(fileobj, mode)
        else:
            fileobj = bz2.BZ2File(name, mode, compresslevel=compresslevel)

        try:
            t = cls.taropen(name, mode, fileobj, **kwargs)
        except (IOError, EOFError):
            fileobj.close()
            if mode == 'r':
                raise ReadError("not a bzip2 file")
            raise
        except:
            fileobj.close()
            raise
        t._extfileobj = False
        return t

    # All *open() methods are registered here.
    OPEN_METH = {
        "tar": "taropen",   # uncompressed tar
        "gz":  "gzopen",    # gzip compressed tar
        "bz2": "bz2open"    # bzip2 compressed tar
    }

    #--------------------------------------------------------------------------
    # The public methods which TarFile2 provides:

    def close(self):
        """Close the TarFile2. In write-mode, two finishing zero blocks are
           appended to the archive.
        """
        if self.closed:
            return

        self.closed = True
        try:
            if self.mode in "aw":
                self.fileobj.write(NUL * (BLOCKSIZE * 2))
                self.offset += (BLOCKSIZE * 2)
                # fill up the end with zero-blocks
                # (like option -b20 for tar does)
                blocks, remainder = divmod(self.offset, RECORDSIZE)
                if remainder > 0:
                    self.fileobj.write(NUL * (RECORDSIZE - remainder))
        finally:
            if not self._extfileobj:
                self.fileobj.close()

    def getmember(self, name):
        """Return a TarInfo2 object for member `name'. If `name' can not be
           found in the archive, KeyError is raised. If a member occurs more
           than once in the archive, its last occurrence is assumed to be the
           most up-to-date version.
        """
        tarinfo = self._getmember(name)
        if tarinfo is None:
            raise KeyError("filename %r not found" % name)
        return tarinfo

    def getmembers(self):
        """Return the members of the archive as a list of TarInfo2 objects. The
           list has the same order as the members in the archive.
        """
        self._check()
        if not self._loaded:    # if we want to obtain a list of
            self._load()        # all members, we first have to
                                # scan the whole archive.
        return self.members

    def extractfile(self, member):
        """Extract a member from the archive as a file object. `member' may be
           a filename or a TarInfo2 object. If `member' is a regular file, a
           file-like object is returned. If `member' is a link, a file-like
           object is constructed from the link's target. If `member' is none of
           the above, None is returned.
           The file-like object is read-only and provides the following
           methods: read(), readline(), readlines(), seek() and tell()
        """
        self._check("r")

        if isinstance(member, basestring):
            tarinfo = self.getmember(member)
        else:
            tarinfo = member

        if tarinfo.isreg():
            return self.fileobject(self, tarinfo)

        elif tarinfo.type not in SUPPORTED_TYPES:
            # If a member's type is unknown, it is treated as a
            # regular file.
            return self.fileobject(self, tarinfo)

        elif tarinfo.islnk() or tarinfo.issym():
            if isinstance(self.fileobj, _Stream2):
                # A small but ugly workaround for the case that someone tries
                # to extract a (sym)link as a file-object from a non-seekable
                # stream of tar blocks.
                raise StreamError("cannot extract (sym)link as file object")
            else:
                # A (sym)link's file object is its target's file object.
                return self.extractfile(self._find_link_target(tarinfo))
        else:
            # If there's no data associated with the member (directory, chrdev,
            # blkdev, etc.), return None instead of a file object.
            return None

    #--------------------------------------------------------------------------
    def next(self):
        """Return the next member of the archive as a TarInfo2 object, when
           TarFile2 is opened for reading. Return None if there is no more
           available.
        """
        self._check("ra")
        if self.firstmember is not None:
            m = self.firstmember
            self.firstmember = None
            return m

        # Advance the file pointer.
        if self.offset != self.fileobj.tell():
            self.fileobj.seek(self.offset - 1)
            if not self.fileobj.read(1):
                raise ReadError("unexpected end of data")

        # Read the next block.
        tarinfo = None
        while True:
            try:
                tarinfo = self.tarinfo.fromtarfile(self)
            except EOFHeaderError as e:
                if self.ignore_zeros:
                    self._dbg(2, "0x%X: %s" % (self.offset, e))
                    self.offset += BLOCKSIZE
                    continue
            except InvalidHeaderError as e:
                if self.ignore_zeros:
                    self._dbg(2, "0x%X: %s" % (self.offset, e))
                    self.offset += BLOCKSIZE
                    continue
                elif self.offset == 0:
                    raise ReadError(str(e))
            except EmptyHeaderError:
                if self.offset == 0:
                    raise ReadError("empty file")
            except TruncatedHeaderError as e:
                if self.offset == 0:
                    raise ReadError(str(e))
            except SubsequentHeaderError as e:
                raise ReadError(str(e))
            break

        if tarinfo is not None:
            self.members.append(tarinfo)
        else:
            self._loaded = True

        return tarinfo

    #--------------------------------------------------------------------------
    # Little helper methods:

    def _getmember(self, name, tarinfo=None, normalize=False):
        """Find an archive member by name from bottom to top.
           If tarinfo is given, it is used as the starting point.
        """
        # Ensure that all members have been loaded.
        members = self.getmembers()

        # Limit the member search list up to tarinfo.
        if tarinfo is not None:
            members = members[:members.index(tarinfo)]

        if normalize:
            name = os.path.normpath(name)

        for member in reversed(members):
            if normalize:
                member_name = os.path.normpath(member.name)
            else:
                member_name = member.name

            if name == member_name:
                return member

    def _load(self):
        """Read through the entire archive file and look for readable
           members.
        """
        while True:
            tarinfo = self.next()
            if tarinfo is None:
                break
        self._loaded = True

    def _check(self, mode=None):
        """Check if TarFile2 is still open, and if the operation's mode
           corresponds to TarFile2's mode.
        """
        if self.closed:
            raise IOError("%s is closed" % self.__class__.__name__)
        if mode is not None and self.mode not in mode:
            raise IOError("bad operation for mode %r" % self.mode)

    def _find_link_target(self, tarinfo):
        """Find the target member of a symlink or hardlink member in the
           archive.
        """
        if tarinfo.issym():
            # Always search the entire archive.
            linkname = "/".join(filter(None, (os.path.dirname(tarinfo.name), tarinfo.linkname)))
            limit = None
        else:
            # Search the archive before the link, because a hard link is
            # just a reference to an already archived file.
            linkname = tarinfo.linkname
            limit = tarinfo

        member = self._getmember(linkname, tarinfo=limit, normalize=True)
        if member is None:
            raise KeyError("linkname %r not found" % linkname)
        return member

    def __iter__(self):
        """Provide an iterator object.
        """
        if self._loaded:
            return iter(self.members)
        else:
            return TarIter2(self)

    def _dbg(self, level, msg):
        """Write debugging output to sys.stderr.
        """
        if level <= self.debug:
            print >> sys.stderr, msg

    def __enter__(self):
        self._check()
        return self

    def __exit__(self, type, value, traceback):
        if type is None:
            self.close()
        else:
            # An exception occurred. We must not call close() because
            # it would try to write end-of-archive blocks and padding.
            if not self._extfileobj:
                self.fileobj.close()
            self.closed = True
# class TarFile2

#-------------------------------------------------------------------------------


################################################################################
#                                                                              #
# This is only a PART of TARFILE LIBRARY - needed to CHECK TAR file INTEGRITY. #
# It contains PATCH TO BUG present in python 2.6, 2.7, 3.4, 3.5.               #
#                                                                              #
# The bug allowed to extract corrupted tar file without raising any errors     #
# (regardless of errorlevel setting).                                          #
#                                                                              #
# There are two versions used by this script - for python 2.* and 3.0-3.5.     #
# Below you can find version used by this script for python [ 3.0-3.5 ].       #
#                                                                              #
# link to discussion:       https://bugs.python.org/issue24259                 #
# link to patch:            https://hg.python.org/cpython/rev/c7f4f61697b7     #
#                                                                              #
# date:         17 Jan 2017                                                    #
# link:         https://hg.python.org/cpython/file/3.4/Lib/tarfile.py          #
#                                                                              #
################################################################################

#-------------------------------------------------------------------
# tarfile.py   [[[   branch 3.4   ]]] - used in this script for python 3.0-3.5
#-------------------------------------------------------------------
# Copyright (C) 2002 Lars Gustaebel <lars@gustaebel.de>
# All rights reserved.
#
# Permission  is  hereby granted,  free  of charge,  to  any person
# obtaining a  copy of  this software  and associated documentation
# files  (the  "Software"),  to   deal  in  the  Software   without
# restriction,  including  without limitation  the  rights to  use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies  of  the  Software,  and to  permit  persons  to  whom the
# Software  is  furnished  to  do  so,  subject  to  the  following
# conditions:
#
# The above copyright  notice and this  permission notice shall  be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS  IS", WITHOUT WARRANTY OF ANY  KIND,
# EXPRESS OR IMPLIED, INCLUDING  BUT NOT LIMITED TO  THE WARRANTIES
# OF  MERCHANTABILITY,  FITNESS   FOR  A  PARTICULAR   PURPOSE  AND
# NONINFRINGEMENT.  IN  NO  EVENT SHALL  THE  AUTHORS  OR COPYRIGHT
# HOLDERS  BE LIABLE  FOR ANY  CLAIM, DAMAGES  OR OTHER  LIABILITY,
# WHETHER  IN AN  ACTION OF  CONTRACT, TORT  OR OTHERWISE,  ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
#

#---------------------------------------------------------
# Some useful functions
#---------------------------------------------------------
def stn3(s, length, encoding, errors):
    """Convert a string to a null-terminated bytes object.
    """
    s = s.encode(encoding, errors)
    return s[:length] + (length - len(s)) * NUL

def nts3(s, encoding, errors):
    """Convert a null-terminated bytes object to a string.
    """
    p = s.find(b"\0")
    if p != -1:
        s = s[:p]
    return s.decode(encoding, errors)

def nti3(s):
    """Convert a number field to a python number.
    """
    # There are two possible encodings for a number field, see
    # itn3() below.
    if s[0] in (0o200, 0o377):
        n = 0
        for i in range(len(s) - 1):
            n <<= 8
            n += s[i + 1]
        if s[0] == 0o377:
            n = -(256 ** (len(s) - 1) - n)
    else:
        try:
            s = nts3(s, "ascii", "strict")
            n = int(s.strip() or "0", 8)
        except ValueError:
            raise InvalidHeaderError("invalid header")
    return n

def itn3(n, digits=8, format=DEFAULT_FORMAT):
    """Convert a python number to a number field.
    """
    # POSIX 1003.1-1988 requires numbers to be encoded as a string of
    # octal digits followed by a null-byte, this allows values up to
    # (8**(digits-1))-1. GNU tar allows storing numbers greater than
    # that if necessary. A leading 0o200 or 0o377 byte indicate this
    # particular encoding, the following digits-1 bytes are a big-endian
    # base-256 representation. This allows values up to (256**(digits-1))-1.
    # A 0o200 byte indicates a positive number, a 0o377 byte a negative
    # number.
    if 0 <= n < 8 ** (digits - 1):
        s = bytes("%0*o" % (digits - 1, int(n)), "ascii") + NUL
    elif format == GNU_FORMAT and -256 ** (digits - 1) <= n < 256 ** (digits - 1):
        if n >= 0:
            s = bytearray([0o200])
        else:
            s = bytearray([0o377])
            n = 256 ** digits + n

        for i in range(digits - 1):
            s.insert(1, n & 0o377)
            n >>= 8
    else:
        raise ValueError("overflow in number field")

    return s

def calc_chksums3(buf):
    """Calculate the checksum for a member's header by summing up all
       characters except for the chksum field which is treated as if
       it was filled with spaces. According to the GNU tar sources,
       some tars (Sun and NeXT) calculate chksum with signed char,
       which will be different if there are chars in the buffer with
       the high bit set. So we calculate two checksums, unsigned and
       signed.
    """
    unsigned_chksum = 256 + sum(struct.unpack_from("148B8x356B", buf))
    signed_chksum = 256 + sum(struct.unpack_from("148b8x356b", buf))
    return unsigned_chksum, signed_chksum

#------------------------
# Extraction file object
#------------------------
class _FileInFile3(object):
    """A thin wrapper around an existing file object that
       provides a part of its data as an individual file
       object.
    """

    def __init__(self, fileobj, offset, size, blockinfo=None):
        self.fileobj = fileobj
        self.offset = offset
        self.size = size
        self.position = 0
        self.name = getattr(fileobj, "name", None)
        self.closed = False

        if blockinfo is None:
            blockinfo = [(0, size)]

        # Construct a map with data and zero blocks.
        self.map_index = 0
        self.map = []
        lastpos = 0
        realpos = self.offset
        for offset, size in blockinfo:
            if offset > lastpos:
                self.map.append((False, lastpos, offset, None))
            self.map.append((True, offset, offset + size, realpos))
            realpos += size
            lastpos = offset + size
        if lastpos < self.size:
            self.map.append((False, lastpos, self.size, None))

    def flush(self):
        pass

    def readable(self):
        return True

    def writable(self):
        return False

    def seekable(self):
        return self.fileobj.seekable()

    def tell(self):
        """Return the current file position.
        """
        return self.position

    #def seek(self, position, whence=io.SEEK_SET):
    def seek(self, position, whence=os.SEEK_SET):
    #def seek(self, position, whence=0):
        # SEEK_SET or 0 - start of the stream (the default); offset should be zero or positive
        # SEEK_CUR or 1 - current stream position; offset may be negative
        # SEEK_END or 2 - end of the stream; offset is usually negative
        """Seek to a position in the file.
        """
        if whence == io.SEEK_SET:
            self.position = min(max(position, 0), self.size)
        elif whence == io.SEEK_CUR:
            if position < 0:
                self.position = max(self.position + position, 0)
            else:
                self.position = min(self.position + position, self.size)
        elif whence == io.SEEK_END:
            self.position = max(min(self.size + position, self.size), 0)
        else:
            raise ValueError("Invalid argument")
        return self.position

    def read(self, size=None):
        """Read data from the file.
        """
        if size is None:
            size = self.size - self.position
        else:
            size = min(size, self.size - self.position)

        buf = b""
        while size > 0:
            while True:
                data, start, stop, offset = self.map[self.map_index]
                if start <= self.position < stop:
                    break
                else:
                    self.map_index += 1
                    if self.map_index == len(self.map):
                        self.map_index = 0
            length = min(size, stop - self.position)
            if data:
                self.fileobj.seek(offset + (self.position - start))
                b = self.fileobj.read(length)
                if len(b) != length:
                    raise ReadError("unexpected end of data")
                buf += b
            else:
                buf += NUL * length
            size -= length
            self.position += length
        return buf

    def readinto(self, b):
        buf = self.read(len(b))
        b[:len(buf)] = buf
        return len(buf)

    def close(self):
        self.closed = True
#class _FileInFile3

class ExFileObject3(io.BufferedReader):

    def __init__(self, tarfile, tarinfo):
        fileobj = _FileInFile3(tarfile.fileobj, tarinfo.offset_data,
                tarinfo.size, tarinfo.sparse)
        super().__init__(fileobj)
#class ExFileObject3

#------------------
# Exported Classes
#------------------
class TarInfo3(object):
    """Informational class which holds the details about an
       archive member given by a tar header block.
       TarInfo3 objects are returned by TarFile3.getmember(),
       TarFile3.getmembers() and TarFile3.gettarinfo() and are
       usually created internally.
    """

    __slots__ = ("name", "mode", "uid", "gid", "size", "mtime",
                 "chksum", "type", "linkname", "uname", "gname",
                 "devmajor", "devminor",
                 "offset", "offset_data", "pax_headers", "sparse",
                 "tarfile", "_sparse_structs", "_link_target")

    def __init__(self, name=""):
        """Construct a TarInfo3 object. name is the optional name
           of the member.
        """
        self.name = name        # member name
        self.mode = 0o644       # file permissions
        self.uid = 0            # user id
        self.gid = 0            # group id
        self.size = 0           # file size
        self.mtime = 0          # modification time
        self.chksum = 0         # header checksum
        self.type = REGTYPE     # member type
        self.linkname = ""      # link name
        self.uname = ""         # user name
        self.gname = ""         # group name
        self.devmajor = 0       # device major number
        self.devminor = 0       # device minor number

        self.offset = 0         # the tar header starts here
        self.offset_data = 0    # the file's data starts here

        self.sparse = None      # sparse member information
        self.pax_headers = {}   # pax header information

    # In pax headers the "name" and "linkname" field are called
    # "path" and "linkpath".
    def _getpath(self):
        return self.name
    def _setpath(self, name):
        self.name = name
    path = property(_getpath, _setpath)

    def _getlinkpath(self):
        return self.linkname
    def _setlinkpath(self, linkname):
        self.linkname = linkname
    linkpath = property(_getlinkpath, _setlinkpath)

    def __repr__(self):
        return "<%s %r at %#x>" % (self.__class__.__name__,self.name,id(self))

    @classmethod
    def frombuf(cls, buf, encoding, errors):
        """Construct a TarInfo3 object from a 512 byte bytes object.
        """
        if len(buf) == 0:
            raise EmptyHeaderError("empty header")
        if len(buf) != BLOCKSIZE:
            raise TruncatedHeaderError("truncated header")
        if buf.count(NUL) == BLOCKSIZE:
            raise EOFHeaderError("end of file header")

        chksum = nti3(buf[148:156])
        if chksum not in calc_chksums3(buf):
            raise InvalidHeaderError("bad checksum")

        obj = cls()
        obj.name = nts3(buf[0:100], encoding, errors)
        obj.mode = nti3(buf[100:108])
        obj.uid = nti3(buf[108:116])
        obj.gid = nti3(buf[116:124])
        obj.size = nti3(buf[124:136])
        obj.mtime = nti3(buf[136:148])
        obj.chksum = chksum
        obj.type = buf[156:157]
        obj.linkname = nts3(buf[157:257], encoding, errors)
        obj.uname = nts3(buf[265:297], encoding, errors)
        obj.gname = nts3(buf[297:329], encoding, errors)
        obj.devmajor = nti3(buf[329:337])
        obj.devminor = nti3(buf[337:345])
        prefix = nts3(buf[345:500], encoding, errors)

        # Old V7 tar format represents a directory as a regular
        # file with a trailing slash.
        if obj.type == AREGTYPE and obj.name.endswith("/"):
            obj.type = DIRTYPE

        # Remove redundant slashes from directories.
        if obj.isdir():
            obj.name = obj.name.rstrip("/")

        # Reconstruct a ustar longname.
        if prefix and obj.type not in GNU_TYPES:
            obj.name = prefix + "/" + obj.name
        return obj

    @classmethod
    def fromtarfile(cls, tarfile):
        """Return the next TarInfo3 object from TarFile3 object
           tarfile.
        """
        buf = tarfile.fileobj.read(BLOCKSIZE)
        obj = cls.frombuf(buf, tarfile.encoding, tarfile.errors)
        obj.offset = tarfile.fileobj.tell() - BLOCKSIZE
        return obj._proc_member(tarfile)

    def _proc_member(self, tarfile):
        """Choose the right processing method depending on
           the type and call it.
        """
        if self.type in (GNUTYPE_LONGNAME, GNUTYPE_LONGLINK):
            return self._proc_gnulong(tarfile)
        elif self.type == GNUTYPE_SPARSE:
            return self._proc_sparse(tarfile)
        elif self.type in (XHDTYPE, XGLTYPE, SOLARIS_XHDTYPE):
            return self._proc_pax(tarfile)
        else:
            return self._proc_builtin(tarfile)

    def _proc_builtin(self, tarfile):
        """Process a builtin type or an unknown type which
           will be treated as a regular file.
        """
        self.offset_data = tarfile.fileobj.tell()
        offset = self.offset_data
        if self.isreg() or self.type not in SUPPORTED_TYPES:
            # Skip the following data blocks.
            offset += self._block(self.size)
        tarfile.offset = offset

        # Patch the TarInfo3 object with saved global
        # header information.
        self._apply_pax_info(tarfile.pax_headers, tarfile.encoding, tarfile.errors)

        return self

    def _apply_pax_info(self, pax_headers, encoding, errors):
        """Replace fields with supplemental information from a previous
           pax extended or global header.
        """
        for keyword, value in pax_headers.items():
            if keyword == "GNU.sparse.name":
                setattr(self, "path", value)
            elif keyword == "GNU.sparse.size":
                setattr(self, "size", int(value))
            elif keyword == "GNU.sparse.realsize":
                setattr(self, "size", int(value))
            elif keyword in PAX_FIELDS:
                if keyword in PAX_NUMBER_FIELDS:
                    try:
                        value = PAX_NUMBER_FIELDS[keyword](value)
                    except ValueError:
                        value = 0
                if keyword == "path":
                    value = value.rstrip("/")
                setattr(self, keyword, value)

        self.pax_headers = pax_headers.copy()

    def _decode_pax_field(self, value, encoding, fallback_encoding, fallback_errors):
        """Decode a single field from a pax record.
        """
        try:
            return value.decode(encoding, "strict")
        except UnicodeDecodeError:
            return value.decode(fallback_encoding, fallback_errors)

    def _block(self, count):
        """Round up a byte count by BLOCKSIZE and return it,
           e.g. _block(834) => 1024.
        """
        blocks, remainder = divmod(count, BLOCKSIZE)
        if remainder:
            blocks += 1
        return blocks * BLOCKSIZE

    def isreg(self):
        return self.type in REGULAR_TYPES
    def isfile(self):
        return self.isreg()
    def isdir(self):
        return self.type == DIRTYPE
    def issym(self):
        return self.type == SYMTYPE
    def islnk(self):
        return self.type == LNKTYPE
    def ischr(self):
        return self.type == CHRTYPE
    def isblk(self):
        return self.type == BLKTYPE
    def isfifo(self):
        return self.type == FIFOTYPE
    def issparse(self):
        return self.sparse is not None
    def isdev(self):
        return self.type in (CHRTYPE, BLKTYPE, FIFOTYPE)
# class TarInfo3

class TarFile3(object):
    """The TarFile3 Class provides an interface to tar archives.
    """

    debug = 0                   # May be set from 0 (no msgs) to 3 (all msgs)

    dereference = False         # If true, add content of linked file to the
                                # tar file, else the link.

    ignore_zeros = False        # If true, skips empty or invalid blocks and
                                # continues processing.

    errorlevel = 1              # If 0, fatal errors only appear in debug
                                # messages (if debug >= 0). If > 0, errors
                                # are passed to the caller as exceptions.

    format = DEFAULT_FORMAT     # The format to use when creating an archive.

    encoding = ENCODING         # Encoding for 8-bit character strings.

    errors = None               # Error handler for unicode conversion.

    tarinfo = TarInfo3           # The default TarInfo3 class to use.

    fileobject = ExFileObject3   # The file-object for extractfile().

    def __init__(self, name=None, mode="r", fileobj=None, format=None,
            tarinfo=None, dereference=None, ignore_zeros=None, encoding=None,
            errors="surrogateescape", pax_headers=None, debug=None, errorlevel=None):
        """Open an (uncompressed) tar archive `name'. `mode' is either 'r' to
           read from an existing archive, 'a' to append data to an existing
           file or 'w' to create a new file overwriting an existing one. `mode'
           defaults to 'r'.
           If `fileobj' is given, it is used for reading or writing data. If it
           can be determined, `mode' is overridden by `fileobj's mode.
           `fileobj' is not closed, when TarFile3 is closed.
        """
        modes = {"r": "rb", "a": "r+b", "w": "wb"}
        if mode not in modes:
            raise ValueError("mode must be 'r', 'a' or 'w'")
        self.mode = mode
        self._mode = modes[mode]

        if not fileobj:
            if self.mode == "a" and not os.path.exists(name):
                # Create nonexistent files in append mode.
                self.mode = "w"
                self._mode = "wb"
            fileobj = bltn_open(name, self._mode)
            self._extfileobj = False
        else:
            if (name is None and hasattr(fileobj, "name") and
                isinstance(fileobj.name, (str, bytes))):
                name = fileobj.name
            if hasattr(fileobj, "mode"):
                self._mode = fileobj.mode
            self._extfileobj = True
        self.name = os.path.abspath(name) if name else None
        self.fileobj = fileobj

        # Init attributes.
        if format is not None:
            self.format = format
        if tarinfo is not None:
            self.tarinfo = tarinfo
        if dereference is not None:
            self.dereference = dereference
        if ignore_zeros is not None:
            self.ignore_zeros = ignore_zeros
        if encoding is not None:
            self.encoding = encoding
        self.errors = errors

        if pax_headers is not None and self.format == PAX_FORMAT:
            self.pax_headers = pax_headers
        else:
            self.pax_headers = {}

        if debug is not None:
            self.debug = debug
        if errorlevel is not None:
            self.errorlevel = errorlevel

        # Init datastructures.
        self.closed = False
        self.members = []       # list of members as TarInfo3 objects
        self._loaded = False    # flag if all members have been read
        self.offset = self.fileobj.tell()
                                # current position in the archive file
        self.inodes = {}        # dictionary caching the inodes of
                                # archive members already added

        try:
            if self.mode == "r":
                self.firstmember = None
                self.firstmember = self.next()

            if self.mode == "a":
                # Move to the end of the archive,
                # before the first empty block.
                while True:
                    self.fileobj.seek(self.offset)
                    try:
                        tarinfo = self.tarinfo.fromtarfile(self)
                        self.members.append(tarinfo)
                    except EOFHeaderError:
                        self.fileobj.seek(self.offset)
                        break
                    except HeaderError as e:
                        raise ReadError(str(e))

            if self.mode in "aw":
                self._loaded = True

                if self.pax_headers:
                    buf = self.tarinfo.create_pax_global_header(self.pax_headers.copy())
                    self.fileobj.write(buf)
                    self.offset += len(buf)
        except:
            if not self._extfileobj:
                self.fileobj.close()
            self.closed = True
            raise

    @classmethod
    def open(cls, name=None, mode="r", fileobj=None, bufsize=RECORDSIZE, **kwargs):
        """Open a tar archive for reading, writing or appending. Return
           an appropriate TarFile3 class.

           mode:
           'r' or 'r:*' open for reading with transparent compression
           'r:'         open for reading exclusively uncompressed
           'r:gz'       open for reading with gzip compression
           'r:bz2'      open for reading with bzip2 compression
           'r:xz'       open for reading with lzma compression
           'a' or 'a:'  open for appending, creating the file if necessary
           'w' or 'w:'  open for writing without compression
           'w:gz'       open for writing with gzip compression
           'w:bz2'      open for writing with bzip2 compression
           'w:xz'       open for writing with lzma compression

           'r|*'        open a stream of tar blocks with transparent compression
           'r|'         open an uncompressed stream of tar blocks for reading
           'r|gz'       open a gzip compressed stream of tar blocks
           'r|bz2'      open a bzip2 compressed stream of tar blocks
           'r|xz'       open an lzma compressed stream of tar blocks
           'w|'         open an uncompressed stream for writing
           'w|gz'       open a gzip compressed stream for writing
           'w|bz2'      open a bzip2 compressed stream for writing
           'w|xz'       open an lzma compressed stream for writing
        """

        if not name and not fileobj:
            raise ValueError("nothing to open")

        if mode in ("r", "r:*"):
            # Find out which *open() is appropriate for opening the file.
            for comptype in cls.OPEN_METH:
                func = getattr(cls, cls.OPEN_METH[comptype])
                if fileobj is not None:
                    saved_pos = fileobj.tell()
                try:
                    return func(name, "r", fileobj, **kwargs)
                except (ReadError, CompressionError) as e:
                    if fileobj is not None:
                        fileobj.seek(saved_pos)
                    continue
            raise ReadError("file could not be opened successfully")

        elif ":" in mode:
            filemode, comptype = mode.split(":", 1)
            filemode = filemode or "r"
            comptype = comptype or "tar"

            # Select the *open() function according to
            # given compression.
            if comptype in cls.OPEN_METH:
                func = getattr(cls, cls.OPEN_METH[comptype])
            else:
                raise CompressionError("unknown compression type %r" % comptype)
            return func(name, filemode, fileobj, **kwargs)

        elif mode in ("a", "w"):
            return cls.taropen(name, mode, fileobj, **kwargs)

        raise ValueError("undiscernible mode")

    @classmethod
    def taropen(cls, name, mode="r", fileobj=None, **kwargs):
        """Open uncompressed tar archive name for reading or writing.
        """
        if mode not in ("r", "a", "w"):
            raise ValueError("mode must be 'r', 'a' or 'w'")
        return cls(name, mode, fileobj, **kwargs)

    @classmethod
    def gzopen(cls, name, mode="r", fileobj=None, compresslevel=9, **kwargs):
        """Open gzip compressed tar archive name for reading or writing.
           Appending is not allowed.
        """
        if mode not in ("r", "w"):
            raise ValueError("mode must be 'r' or 'w'")

        try:
            import gzip
            gzip.GzipFile
        except (ImportError, AttributeError):
            raise CompressionError("gzip module is not available")

        try:
            fileobj = gzip.GzipFile(name, mode + "b", compresslevel, fileobj)
        except OSError:
            if fileobj is not None and mode == 'r':
                raise ReadError("not a gzip file")
            raise

        try:
            t = cls.taropen(name, mode, fileobj, **kwargs)
        except OSError:
            fileobj.close()
            if mode == 'r':
                raise ReadError("not a gzip file")
            raise
        except:
            fileobj.close()
            raise
        t._extfileobj = False
        return t

    @classmethod
    def bz2open(cls, name, mode="r", fileobj=None, compresslevel=9, **kwargs):
        """Open bzip2 compressed tar archive name for reading or writing.
           Appending is not allowed.
        """
        if mode not in ("r", "w"):
            raise ValueError("mode must be 'r' or 'w'.")

        try:
            import bz2
        except ImportError:
            raise CompressionError("bz2 module is not available")

        fileobj = bz2.BZ2File(fileobj or name, mode,
                              compresslevel=compresslevel)

        try:
            t = cls.taropen(name, mode, fileobj, **kwargs)
        except (OSError, EOFError):
            fileobj.close()
            if mode == 'r':
                raise ReadError("not a bzip2 file")
            raise
        except:
            fileobj.close()
            raise
        t._extfileobj = False
        return t

    @classmethod
    def xzopen(cls, name, mode="r", fileobj=None, preset=None, **kwargs):
        """Open lzma compressed tar archive name for reading or writing.
           Appending is not allowed.
        """
        if mode not in ("r", "w"):
            raise ValueError("mode must be 'r' or 'w'")

        try:
            import lzma
        except ImportError:
            raise CompressionError("lzma module is not available")

        fileobj = lzma.LZMAFile(fileobj or name, mode, preset=preset)

        try:
            t = cls.taropen(name, mode, fileobj, **kwargs)
        except (lzma.LZMAError, EOFError):
            fileobj.close()
            if mode == 'r':
                raise ReadError("not an lzma file")
            raise
        except:
            fileobj.close()
            raise
        t._extfileobj = False
        return t

    # All *open() methods are registered here.
    OPEN_METH = {
        "tar": "taropen",   # uncompressed tar
        "gz":  "gzopen",    # gzip compressed tar
        "bz2": "bz2open",   # bzip2 compressed tar
        "xz":  "xzopen"     # lzma compressed tar
    }

    #--------------------------------------------------------------------------
    # The public methods which TarFile3 provides:

    def close(self):
        """Close the TarFile3. In write-mode, two finishing zero blocks are
           appended to the archive.
        """
        if self.closed:
            return

        self.closed = True
        try:
            if self.mode in "aw":
                self.fileobj.write(NUL * (BLOCKSIZE * 2))
                self.offset += (BLOCKSIZE * 2)
                # fill up the end with zero-blocks
                # (like option -b20 for tar does)
                blocks, remainder = divmod(self.offset, RECORDSIZE)
                if remainder > 0:
                    self.fileobj.write(NUL * (RECORDSIZE - remainder))
        finally:
            if not self._extfileobj:
                self.fileobj.close()

    def getmember(self, name):
        """Return a TarInfo3 object for member `name'. If `name' can not be
           found in the archive, KeyError is raised. If a member occurs more
           than once in the archive, its last occurrence is assumed to be the
           most up-to-date version.
        """
        tarinfo = self._getmember(name)
        if tarinfo is None:
            raise KeyError("filename %r not found" % name)
        return tarinfo

    def getmembers(self):
        """Return the members of the archive as a list of TarInfo3 objects. The
           list has the same order as the members in the archive.
        """
        self._check()
        if not self._loaded:    # if we want to obtain a list of
            self._load()        # all members, we first have to
                                # scan the whole archive.
        return self.members

    def extractfile(self, member):
        """Extract a member from the archive as a file object. `member' may be
           a filename or a TarInfo3 object. If `member' is a regular file or a
           link, an io.BufferedReader object is returned. Otherwise, None is
           returned.
        """
        self._check("r")

        if isinstance(member, str):
            tarinfo = self.getmember(member)
        else:
            tarinfo = member

        if tarinfo.isreg() or tarinfo.type not in SUPPORTED_TYPES:
            # Members with unknown types are treated as regular files.
            return self.fileobject(self, tarinfo)

        elif tarinfo.islnk() or tarinfo.issym():
            if isinstance(self.fileobj, _Stream3):
                # A small but ugly workaround for the case that someone tries
                # to extract a (sym)link as a file-object from a non-seekable
                # stream of tar blocks.
                raise StreamError("cannot extract (sym)link as file object")
            else:
                # A (sym)link's file object is its target's file object.
                return self.extractfile(self._find_link_target(tarinfo))
        else:
            # If there's no data associated with the member (directory, chrdev,
            # blkdev, etc.), return None instead of a file object.
            return None

    #--------------------------------------------------------------------------
    def next(self):
        """Return the next member of the archive as a TarInfo3 object, when
           TarFile3 is opened for reading. Return None if there is no more
           available.
        """
        self._check("ra")
        if self.firstmember is not None:
            m = self.firstmember
            self.firstmember = None
            return m

        # Advance the file pointer.
        if self.offset != self.fileobj.tell():
            self.fileobj.seek(self.offset - 1)
            if not self.fileobj.read(1):
                raise ReadError("unexpected end of data")

        # Read the next block.
        tarinfo = None
        while True:
            try:
                tarinfo = self.tarinfo.fromtarfile(self)
            except EOFHeaderError as e:
                if self.ignore_zeros:
                    self._dbg(2, "0x%X: %s" % (self.offset, e))
                    self.offset += BLOCKSIZE
                    continue
            except InvalidHeaderError as e:
                if self.ignore_zeros:
                    self._dbg(2, "0x%X: %s" % (self.offset, e))
                    self.offset += BLOCKSIZE
                    continue
                elif self.offset == 0:
                    raise ReadError(str(e))
            except EmptyHeaderError:
                if self.offset == 0:
                    raise ReadError("empty file")
            except TruncatedHeaderError as e:
                if self.offset == 0:
                    raise ReadError(str(e))
            except SubsequentHeaderError as e:
                raise ReadError(str(e))
            break

        if tarinfo is not None:
            self.members.append(tarinfo)
        else:
            self._loaded = True

        return tarinfo

    #--------------------------------------------------------------------------
    # Little helper methods:

    def _getmember(self, name, tarinfo=None, normalize=False):
        """Find an archive member by name from bottom to top.
           If tarinfo is given, it is used as the starting point.
        """
        # Ensure that all members have been loaded.
        members = self.getmembers()

        # Limit the member search list up to tarinfo.
        if tarinfo is not None:
            members = members[:members.index(tarinfo)]

        if normalize:
            name = os.path.normpath(name)

        for member in reversed(members):
            if normalize:
                member_name = os.path.normpath(member.name)
            else:
                member_name = member.name

            if name == member_name:
                return member

    def _load(self):
        """Read through the entire archive file and look for readable
           members.
        """
        while True:
            tarinfo = self.next()
            if tarinfo is None:
                break
        self._loaded = True

    def _check(self, mode=None):
        """Check if TarFile3 is still open, and if the operation's mode
           corresponds to TarFile3's mode.
        """
        if self.closed:
            raise OSError("%s is closed" % self.__class__.__name__)
        if mode is not None and self.mode not in mode:
            raise OSError("bad operation for mode %r" % self.mode)

    def _find_link_target(self, tarinfo):
        """Find the target member of a symlink or hardlink member in the
           archive.
        """
        if tarinfo.issym():
            # Always search the entire archive.
            linkname = "/".join(filter(None, (os.path.dirname(tarinfo.name), tarinfo.linkname)))
            limit = None
        else:
            # Search the archive before the link, because a hard link is
            # just a reference to an already archived file.
            linkname = tarinfo.linkname
            limit = tarinfo

        member = self._getmember(linkname, tarinfo=limit, normalize=True)
        if member is None:
            raise KeyError("linkname %r not found" % linkname)
        return member

    def __iter__(self):
        """Provide an iterator object.
        """
        if self._loaded:
            return iter(self.members)
        else:
            return TarIter3(self)

    def _dbg(self, level, msg):
        """Write debugging output to sys.stderr.
        """
        if level <= self.debug:
            #print(msg, file=sys.stderr)
            print(msg >> sys.stderr) #to get python 2.7 working, not sure if correct though...

    def __enter__(self):
        self._check()
        return self

    def __exit__(self, type, value, traceback):
        if type is None:
            self.close()
        else:
            # An exception occurred. We must not call close() because
            # it would try to write end-of-archive blocks and padding.
            if not self._extfileobj:
                self.fileobj.close()
            self.closed = True
# class TarFile3

#-------------------------------------------------------------------------------


################################################################################
################################################################################
################################################################################
################################################################################
################################################################################
################################################################################
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
        if PYTHON_MAJOR == 2:
            tar = TarFile2.open(pathToFileInRes, 'r') # using local copy of tarfile library 2.7 branch
        elif PYTHON_MAJOR == 3 and PYTHON_MINOR < 6:
            tar = TarFile3.open(pathToFileInRes, 'r') # using local copy of tarfile library 3.4 branch
        else:
            tar = tarfile.open(pathToFileInRes, 'r') # using imported tarfile library
        try:
            tar.getmembers()
            tar.close()
            return True
        #except (tarfile.TarError) as e:
        except (TarError) as e: # using local copy of tarfile library
            #print("\nTarfile corrupted ERROR: %s in:\n%s" % (e, pathToFileInRes))
            return False
        finally:
            tar.close()
    except (Exception) as e:
        #print("\nTarfile ERROR: %s in:\n%s" % (e, pathToFileInRes))
        return False


def setPermissions755(tarinfo):
    if not re.search(r'(.*.(tar|tar.gz|tar.bz2|tar.xz|tgz|tbz|txz|bin|run))', tarinfo.name):
        tarinfo.mode |= 0o755
    return tarinfo


def extractTarfile(pathToDir, pathToFileInRes):
    print("\n\nextracting tarfile...")
    try:
        tar = tarfile.open(pathToFileInRes, 'r:', format = GNU_FORMAT, encoding = "utf-8")
        try:

            updatedMembers = []
            for tarinfo in tar.getmembers():
                tarinfo = setPermissions755(tarinfo)
                updatedMembers.append(tarinfo)
            tar.extractall(members = updatedMembers, path = pathToDir)

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
    print("\ncreating new tarfile...")
    try:
        tar = tarfile.open(fileName, 'w:', format = GNU_FORMAT, encoding = "utf-8")
        try:

            if((PYTHON_MAJOR == 2 and PYTHON_MINOR >= 7)
            or (PYTHON_MAJOR == 3 and PYTHON_MINOR >= 2)
            or (PYTHON_MAJOR >= 3)):
                for item in listDirectory(pathToDir):
                    tar.add(os.path.join(pathToDir, item), arcname = item, filter = setPermissions755)
            else:
                for file in listDirsRecursively(pathToDir):
                    pathToFile = os.path.join(pathToDir, file)
                    tarinfo = tar.gettarinfo(pathToFile, arcname = file)
                    tarinfo = setPermissions755(tarinfo)
                    try:
                        f = open(pathToFile, 'rb')
                        try:
                            tar.addfile(tarinfo, fileobj = f)
                            f.close()
                        except (OSError, IOError) as e:
                            print("\nTarfile creation ERROR: %s in:\n%s" % (e, fileName))
                        finally:
                            f.close()
                    except (Exception) as e:
                        print("\nTarfile creation ERROR: %s in:\n%s" % (e, fileName))

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
        print("\n%s\t deleted from:\t%s" % (fileName, pathToDir))
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


def listDirs(pathBase, pathLocal, filesList):
    pathToDir = os.path.join(pathBase, pathLocal)
    for item in listDirectory(pathToDir):
        pathToItem = os.path.join(pathToDir, item)
        pathToItemLocal = os.path.join(pathLocal, item)
        if os.path.isdir(pathToItem):
            listDirs(pathBase, pathToItemLocal, filesList)
        else:
            filesList.append(pathToItemLocal)


def listDirsRecursively(pathBase):
    filesList = []
    localPath = ''
    listDirs(pathBase, localPath, filesList)
    return filesList


def getFileSize(pathToFile):
    fileSize = 1
    try:
        fileSize = os.stat(pathToFile).st_size
    except (OSError, IOError, Exception) as e:
        print("\nGetting file info ERROR: %s" % (e))
    if fileSize <= 0:
        fileSize = 1
    return fileSize

#-------------------------------------------------------------------------------


#===============================================================================
# functions to print progress bar
#===============================================================================

def getUnit(variable):
    units = ['kB', 'MB', 'GB', 'TB'] #Decimal Prefixes - The SI standard http://wolfprojects.altervista.org/articles/binary-and-decimal-prefixes/
    variableUnit = ' B'
    for unit in units:
        if variable >= 1000:
            variable /= 1000
            variableUnit = unit
        else:
            break
    #which translates to:
    # i = 0
    # while variable >= 1000 and i < len(units):
        # variable /= 1000
        # variableUnit = units[i] #"damn I miss array[i++] style syntax" - Dawid Koszewski, AD 2019
        # i += 1
    return variable, variableUnit


def printProgressBar(copied, fileSize, speedCurrent = 1048576.0, speedAverage = 1048576.0):
    percent = (copied / (fileSize * 1.0)) # multiplication by 1.0 needed for python 2
    if percent > 1.0:
        percent = 1.0
    dataLeft = (fileSize - copied) #Bytes
    timeLeftSeconds = (dataLeft / speedAverage) #Seconds
    timeLeftHours = (timeLeftSeconds / 3600)
    timeLeftSeconds = (timeLeftSeconds % 3600)
    timeLeftMinutes = (timeLeftSeconds / 60)
    timeLeftSeconds = (timeLeftSeconds % 60)

    #padding = len(str(int(fileSize)))
    copied, copiedUnit = getUnit(copied)
    fileSize, fileSizeUnit = getUnit(fileSize)
    speedCurrent, speedCurrentUnit = getUnit(speedCurrent)

    symbolDone = '='
    symbolLeft = '-'
    sizeTotal = 20
    sizeDone = int(percent * sizeTotal)

    sizeLeft = sizeTotal - sizeDone
    progressBar = '[' + sizeDone*symbolDone + sizeLeft*symbolLeft + ']'
    sys.stdout.write('\r%3d%% %s [%3.1d%s/%3.1d%s]  [%6.2f%s/s] %3.1dh%2.2dm%2.2ds' % (percent*100, progressBar, copied, copiedUnit, fileSize, fileSizeUnit, speedCurrent, speedCurrentUnit, timeLeftHours, timeLeftMinutes, timeLeftSeconds))
    sys.stdout.flush()
    #time.sleep(0.05) #### DELETE AFTER DEVELOPMENT ##########################################################################################################


def handleProgressBarWithinLoop(vars, buffer, fileSize):
    # timeNow = time.time()
    # timeNowData += len(buffer)
# #update Current Speed
    # if timeNow >= (timeMark + time_step):
        # timeDiff = timeNow - timeMark
        # if timeDiff == 0:
            # timeDiff = 0.1
        # dataDiff = timeNowData - timeMarkData
        # timeMark = timeNow
        # timeMarkData = timeNowData
        # speedCurrent = (dataDiff / timeDiff) #Bytes per second
# #update Average Speed and print progress
    # if timeNowData >= (dataMark + data_step):
        # timeDiff = timeNow - timeStarted
        # if timeDiff == 0:
            # timeDiff = 0.1
        # dataMark = timeNowData
        # speedAverage = (timeNowData / timeDiff) #Bytes per second
# #print progress
        # printProgressBar(timeNowData, fileSize, speedCurrent, speedAverage)

# it would be more readible to unpack a list, do calculations, and pack the list again (assign data)

    vars['timeNow'] = time.time()
    vars['timeNowData'] += len(buffer)
#update Current Speed
    if vars['timeNow'] >= (vars['timeMark'] + vars['time_step']):
        vars['timeDiff'] = vars['timeNow'] - vars['timeMark']
        if vars['timeDiff'] == 0:
            vars['timeDiff'] = 0.1
        vars['dataDiff'] = vars['timeNowData'] - vars['timeMarkData']
        vars['timeMark'] = vars['timeNow']
        vars['timeMarkData'] = vars['timeNowData']
        vars['speedCurrent'] = (vars['dataDiff'] / vars['timeDiff']) #Bytes per second
#update Average Speed and print progress
    if vars['timeNowData'] >= (vars['dataMark'] + vars['data_step']):
        vars['timeDiff'] = vars['timeNow'] - vars['timeStarted']
        if vars['timeDiff'] == 0:
            vars['timeDiff'] = 0.1
        vars['dataMark'] = vars['timeNowData']
        vars['speedAverage'] = (vars['timeNowData'] / vars['timeDiff']) #Bytes per second
#print progress
        printProgressBar(vars['timeNowData'], fileSize, vars['speedCurrent'], vars['speedAverage'])


def initProgressBarVariables():
    progressBarVars = {}

    progressBarVars['timeStarted'] = time.time()
    progressBarVars['data_step'] = 131072
    progressBarVars['dataMark'] = 0

    progressBarVars['time_step'] = 1.0
    progressBarVars['timeMark'] = time.time()
    progressBarVars['timeMarkData'] = 0.0
    progressBarVars['timeNow'] = 0.0
    progressBarVars['timeNowData'] = 0.0
    progressBarVars['speedCurrent'] = 1048576.0
    progressBarVars['speedAverage'] = 1048576.0

    return progressBarVars

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
            print("\ncalculating checksum...")
            fileSize = getFileSize(fileNameTemp)

            try:
                progressBarVars = initProgressBarVariables()

                while 1:
                    buffer = f.read(1024*1024) #default 64*1024 for linux
                    if not buffer:
                        break
                    checksum = zlib.adler32(buffer, checksum)

                    handleProgressBarWithinLoop(progressBarVars, buffer, fileSize)
                printProgressBar(progressBarVars['timeNowData'], fileSize, progressBarVars['speedCurrent'], progressBarVars['speedAverage'])
                print()

                f.close()
                checksum = checksum & 0xffffffff
                fileNamePrepend = re.sub(fileMatcher, r'\1', fileNameTemp)
                fileNameAppend = re.sub(fileMatcher, r'\4', fileNameTemp)
                #checksumFormatted = '0x' + (hex(checksum)[2:].zfill(8)).upper() #in python 2.7.14 it appends letter L
                checksumHex = "%x" % checksum
                checksumFormatted = '0x' + ((checksumHex.zfill(8)).upper())
                fileNameNew = fileNamePrepend + checksumFormatted + fileNameAppend
            except (OSError, IOError) as e:
                print("\nCalculate checksum ERROR: %s - %s" % (e.filename, e.strerror))
            finally:
                f.close()
        except (Exception) as e:
            print ("\nCalculate checksum ERROR: %s" % (e))
    else:
        print('\nERROR: Could not find new stratix image file to calculate checksum')
    return fileNameNew

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
                    # if PYTHON_MAJOR >= 3:
                        # f = open(tempFilePath, 'r', newline = '')
                    # else:
                        # f = open(tempFilePath, 'rb')
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
                    if PYTHON_MAJOR >= 3:
                        f = open(tempFilePath, 'w', newline = '')
                    else:
                        f = open(tempFilePath, 'wb')
                    try:
                        f.write(fileContent)
                        f.close()
                        print("%s\t updated in:\t%s" % (fileName, tempFilePath))
                    except (OSError, IOError) as e:
                        print("\nInstaller script writing ERROR: %s - %s" % (e.filename, e.strerror))
                    finally:
                        f.close()
                except (Exception) as e:
                    print("\nInstaller script writing ERROR: %s" % (e))


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
# custom implementation of copyfileobj from shutil LIBRARY (enable displaying progress bar)
#===============================================================================

def copyfileobj(fsrc, fdst, src, length = 1024*1024): #default 64*1024 for linux
    fileSize = getFileSize(src)

    progressBarVars = initProgressBarVariables()

    while 1:
        buffer = fsrc.read(length)
        if not buffer:
            break
        fdst.write(buffer)

        handleProgressBarWithinLoop(progressBarVars, buffer, fileSize)
    printProgressBar(progressBarVars['timeNowData'], fileSize, progressBarVars['speedCurrent'], progressBarVars['speedAverage'])
    print()

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
        if fileSize <= 0:
            fileSize = 1
        try:
            f = open(pathToFileInRes, 'wb')

            try:
                progressBarVars = initProgressBarVariables()

                while 1:
                    buffer = response.raw.read(1024) #default 128
                    if not buffer:
                        break
                    f.write(buffer)

                    handleProgressBarWithinLoop(progressBarVars, buffer, fileSize)
                printProgressBar(progressBarVars['timeNowData'], fileSize, progressBarVars['speedCurrent'], progressBarVars['speedAverage'])
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
            pressEnterToExit()
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
You can find example list below:\n\n\
v:\\some_user\\nahka\\tmp\\deploy\\images\\nahka\\FRM-rfsw-image-install_20190231120000-multi.tar\n\
v:\\some_user\\nahka\\tmp\\deploy\\images\\nahka\n\
i:\\some_user\\stratix10-aaib\\tmp-glibc\\deploy\\images\\stratix10-aaib\\\n\
https://artifactory-espoo1.int.net.nokia.com/artifactory/mnprf_brft-local/mMIMO_FDD/FB1813_Z/PROD_mMIMO_FDD_FB1813_Z_release/1578/C_Element/SE_RFM/SS_mMIMO_FDD/Target/SRM-rfsw-image-install_z-uber-0xFFFFFFFF.tar\n\
C:\\LocalDir\n\n\
\
1. if C:\\LocalDir contains Nahka and Stratix file - it will copy both of them from C:\\LocalDir\n\
2. if C:\\LocalDir contains only Nahka file - it will copy it and download Stratix file from web\n\
3. if C:\\LocalDir is empty - it will copy newest Nahka file from v:\\some_user\\nahka\\tmp\\deploy\\images\\nahka directory and download Stratix file from web\n\n\
\
When you are running this script in linux console - please specify linux relative or absolute paths, for example:\n\
../nahka/tmp/deploy/images/nahka\n\
/var/fpwork2/some_user/stratix10-aaib/tmp-glibc/deploy/images/stratix10-aaib\n\n\
\
You can keep a lot of helper links in this ini file but remember to put them above the ones desired for current build.\n\
Script will always pick the last found occurrence of Nahka or Stratix file location - so place your desired paths at the very bottom!!!\n\n\
\
If you will delete this ini file - a new one will be created.\n\n\
\
You can now put your links below (you can also delete this whole message - not recommended).\n\n\
\
. - dot means current working directory (works in both linux and windows).\n\n\
\
.\n\
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
    createNewIniFile(pathToFile)
    print("\n%s file has been created!!!" % (pathToFile))
    print("The script will always search for Nahka and Stratix files in locations defined by you in %s" % (pathToFile))
    print("\nBy default it will search in the current working directory (%s)" % (os.path.dirname(os.path.realpath(sys.argv[0]))))
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


def getPathsToLatestFiles(pathToFileIni, fileMatcherNahka, fileMatcherStratix):
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

    #----------------------------
    # initial settings of dir and file names used by this script (can be changed to any)
    #----------------------------
    pathToFileIni = r'stratix_nahka_swapper.ini'
    pathToDirRes = r'stratix_nahka_swapper_resources'
    pathToDirTemp = r'SRM_temp_00000000'
    pathToDirTempArtifacts = os.path.join(pathToDirTemp, r'artifacts')
    fileNameStratixTemp = r'SRM-rfsw-image-install_z-uber-0x00000000.tar'

    #----------------------------
    # initial settings of regex patterns
    #----------------------------
    urlMatcher = re.compile(r'(https://|http://|ftp://)')
    fileMatcher = re.compile(r'(.*)(0x)([a-fA-F0-9]{1,8})(.*)')
    fileMatcherNahka = re.compile(r'(FRM-rfsw-image-install_)([0-9]{14})(-multi.tar)')
    fileMatcherStratix = re.compile(r'.*(SRM-rfsw-image-install_z-uber-0x)([a-fA-F0-9]{8})(.tar).*')
    fileMatcherInstaller = re.compile(r'.*-installer.sh')

    printDetectedAndSupportedPythonVersion()

    #----------------------------
    # paths to latest files found
    #----------------------------
    pathsToLatestFiles = getPathsToLatestFiles(pathToFileIni, fileMatcherNahka, fileMatcherStratix)
    pathToFileNahka = pathsToLatestFiles.get("pathToLatestFileNahka", "")
    pathToFileStratix = pathsToLatestFiles.get("pathToLatestFileStratix", "")

    printFunFact()

    #----------------------------
    # paths to files copied to local resources folder used by this script
    #----------------------------
    pathToFileInResNahka = handleGettingFile(pathToFileNahka, pathToDirRes, 'selected Nahka file', urlMatcher)
    pathToFileInResStratix = handleGettingFile(pathToFileStratix, pathToDirRes, 'selected Stratix file', urlMatcher, fileMatcherStratix)


    #----------------------------
    # swapping nahka file in stratix file procedure
    #----------------------------
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
