# stratix_nahka_swapper
script to swap tarfile image included in subtree of main tarfile image

Lines 200-2360 contain patched "tarfile" library.
This was needed for older versions of Python 2 and 3
because checking integrity of a tar file caused false-positives.
