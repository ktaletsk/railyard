import contextlib
import os

@contextlib.contextmanager
def cd(path):
    CWD = os.getcwd()
    os.chdir(path)
    try:
        yield
    except e:
        print(f'Could not change path to: {path}. Error log: {e}')
    finally:
        os.chdir(CWD)