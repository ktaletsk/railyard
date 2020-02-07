"""Main module."""

import tempfile
from railyard.assembler import readStacks, assembleStack
import railyard.builder as builder
import time
import os

def assemble(base_stack, additional_stacks, path):
    s = readStacks(base_stack, additional_stacks)
    if not os.path.exists(path):
        os.mkdir(path)
    assembleStack(s, path)


def test(base_stack, additional_stack):
    s = readStacks(base_stack, additional_stack)
    tag = 'ktaletsk/polus-notebook:' + s['package_hash']

    # Create temporary folder for Dockerfile and additional files
    # Folder is securely created with `tempfile` and is destroyed afterwards
    with tempfile.TemporaryDirectory() as tmpdirname:
        assembleStack(s, tmpdirname)
        builder.build(tmpdirname, tag)