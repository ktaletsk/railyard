import contextlib
import os

@contextlib.contextmanager
def cd(path):
    CWD = os.getcwd()
    os.chdir(path)
    try:
        yield
    except:
        print(f'Could not change path to: {path}')
    finally:
        os.chdir(CWD)