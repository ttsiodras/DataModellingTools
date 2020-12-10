import os
import time
import fcntl

from contextlib import contextmanager

@contextmanager
def lock_filename(filename: str, verbose: bool):
    # If file is not there, make it, and close it. 
    # This should only happen once in the universe - lockfiles are not supposed to be removed.
    # https://unix.stackexchange.com/questions/368159/why-flock-doesnt-clean-the-lock-file
    try:
        open(filename, 'w').write("LOCK")
    except:
        # In case multiple instances try to create the file, only one will succeed.
        # No worries, we're good with that
        pass
    # Now keep trying to lock it with a read-only exclusive lock.
    fd = os.open(filename, os.O_RDONLY)
    if verbose:
        print("[-] Trying to lock:", filename)
    while True:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            break
        except:
            if verbose:
                print("[x] Already locked. Waiting 1 second...")
            time.sleep(1)
    if verbose:
        print("[-] Got lock!")
    yield
    fcntl.flock(fd, fcntl.LOCK_UN)
    if verbose:
        print("[-] Unlocked:", filename)
