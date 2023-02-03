#!/usr/bin/python3

import rpmfile
import io
import json
import os
import fnmatch
import tempfile
import operator
import sh
import sys
import logging
import argparse
from unidiff import PatchSet
from unidiff.errors import UnidiffParseError
from multiprocessing import Pool


debug = False
flag = 0
sources = {}
wdir = "."
processes = 4
glob_tmpdir = ""
items = {}

if not debug:
    logging.disable(logging.CRITICAL)   # FIXME mute unicode warnings for the time being

FD = 0
NAME = 1

patches_pat = ['*.patch', '*.diff', '*.dif']
tarballs_pat = ['*.tar.gz', '*.tar.bz2', '*.tar.xz', '*.tgz', '*.zip']
package_list = {}
global_lines = 0
global_adds = 0


def process_patch(filename):
    """Counts additions and deletions in one patch"""

    diff = (0, 0)
    try:
        fh = open(filename)
        patch = PatchSet(fh)
    except (LookupError, OSError, UnicodeError, UnidiffParseError, UnboundLocalError) as error:
        if debug:
            print(error)
        return diff
    for f in patch:
        diff = tuple(map(operator.add, diff, (f.added, f.removed)))
    fh.close()
    return diff


def process_one_code_dir(filename):
    files = []
    patches = []
    tarballs = []
    diff = (0, 0)
    counts = (0, 0, 0)

    files = os.listdir(filename)

    for pattern in patches_pat:
        patches.extend(fnmatch.filter(files, pattern))

    for pattern in tarballs_pat:
        tarballs.extend(fnmatch.filter(files, pattern))

    for patch in patches:
        if debug: print(patch)
        diff = tuple(map(operator.add, diff, process_patch(os.path.join(filename, patch))))


    counts = counts + diff
    for tarball in tarballs:
        if debug: print(tarball)
        counts = tuple(map(operator.add, counts, process_tarfile(os.path.join(filename, tarball))))

    return counts


def process_tarfile(filename):
    count, docs, empty = (0, 0, 0)
    diff = (0, 0)
    local_sources = {}
    totals = 0

    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        try: #this can fail in case of hardlink pointing to itself
            sh.bsdtar('-x', '-C', tmpdir, '--no-same-permissions', '-o', '--no-xattrs', '-n', '-f', filename)
        except sh.ErrorReturnCode_1 as error: #fail silently and skip if not debugging
            if debug:
                print(error)

        if 'patches' in filename: #if it's a tarball containing patches
            for root, dirs, files in os.walk(".", topdown=False):
               for name in files:
                   match = False
                   for pat in patches_pat: #is the file indeed a patch?
                       if fnmatch.fnmatch(name, pat):
                           match = True
                   if match:
                       diff = tuple(map(operator.add, diff, process_patch(os.path.join(root, name))))

        else:
            tokei_out = io.StringIO()
            sh.tokei('-C', '-o', 'json', tmpdir, _out=tokei_out)
            analysis = json.loads(tokei_out.getvalue())
            totals = analysis['Total']

            count += totals['code']
            docs += totals['comments']
            empty += totals['blanks']

    return (count, docs, empty) + diff


def process_one_rpm(filename):
    """Returns number of code, docs and empty lines, patch additions and deletions in one source rpm"""

    files = []
    patches = []
    tarballs = []
    diff = (0, 0)
    counts = (0, 0, 0)

    try:
        current_dir = os.getcwd()
    except FileNotFoundError as error:
        print(filename, error)
        return counts + diff

    if debug: print(filename)

    try:
        with rpmfile.open(filename) as rpm:

            for member in rpm.getmembers():
                files.append(member.name)

            for pattern in patches_pat:
                patches.extend(fnmatch.filter(files, pattern))

            for pattern in tarballs_pat:
                tarballs.extend(fnmatch.filter(files, pattern))

            for patch in patches:
                if debug: print(patch)
                fd = rpm.extractfile(patch)
                temp = tempfile.mkstemp()
                os.write(temp[FD], (fd.read()))
                os.close(temp[FD])
                diff = tuple(map(operator.add, diff, process_patch(temp[NAME])))
                os.remove(temp[NAME])


            counts = counts + diff #concatenating known number of diffs with empty list for the codelines, see also process_one_code_dir
            for tarball in tarballs:
                if debug: print(tarball)
                fd = rpm.extractfile(tarball)
                temp = tempfile.mkstemp()
                os.write(temp[FD], (fd.read()))
                os.close(temp[FD])
                counts = tuple(map(operator.add, counts, process_tarfile(temp[NAME])))
                os.remove(temp[NAME])
                os.chdir(current_dir)
    except AssertionError as error:
        if debug: print(error)

    return counts + diff


def process_one_file(filename):
    os.chdir(wdir)
    out = (0, 0, 0, 0, 0)
    if filename.endswith('.src.rpm') or filename.endswith('.spm'):
        out = process_one_rpm(os.path.join(wdir, filename))
    elif os.path.isdir(filename):
        out = process_one_code_dir(os.path.join(wdir, filename))
    os.chdir(glob_tmpdir.name)
    fh = open(filename, "a")
    fh.write(filename)
    fh.write(' ')
    fh.write(' '.join('%s' % x for x in out))

    fh.close()
    os.chdir(wdir)


parser = argparse.ArgumentParser()
parser.add_argument('-D', '--debug', help='Enable debug output', action='store_true')
parser.add_argument('-d', '--dir', help='Directory with packages')
parser.add_argument('-p', '--proc', help='Number of parallel processes')
args = parser.parse_args()
if args.debug:
    debug = 1

if args.proc:
    processes = int(args.proc)

if args.dir:
    if os.path.isabs(args.dir):
        wdir = args.dir
    else:
        wdir = os.path.join(os.getcwd(), args.dir)
else:
    wdir = os.getcwd()

savedir = os.getcwd()
os.chdir(wdir)

if __name__ == '__main__':
    glob_tmpdir = tempfile.TemporaryDirectory()
    pool = Pool(processes)
    filenames = os.listdir(os.getcwd())
    pool.map(process_one_file, filenames)
    pool.close()
    pool.join()
    for f in os.listdir(glob_tmpdir.name):
        fh = open(os.path.join(glob_tmpdir.name, f), "r")
        print(fh.read())
        fh.close()

os.chdir(savedir)
