#!/usr/bin/env python3
"""Download all the Beancount docs from Google Drive and bake a nice PDF with it.

TODO: Convert all the documentation using Pandoc to its native format, and write
a custom filter to make the native nicer, identify the code blocks, etc. and
write it out to Markdown and others.
"""
__copyright__ = "Copyright (C) 2015-2016  Martin Blais"
__license__ = "GNU GPLv2"

import argparse
import datetime
import logging
import os
import shutil
import tempfile
import subprocess
import re
import pickle
import hashlib
import shelve
from os import path

from apiclient import discovery
import httplib2
from oauth2client import service_account

# Local imports
import docs


def main():
    logging.basicConfig(level=logging.INFO, format='%(levelname)-8s: %(message)s')
    parser = argparse.ArgumentParser(description=__doc__.strip())

    parser.add_argument('conversion', action='store',
                        default='pdf', choices=list(docs.CONVERSION_MAP.keys()),
                        help="The format of the desired output.")

    #default_path = path.abspath(datetime.date.today().strftime('beancount.%Y-%m-%d.pdf'))
    parser.add_argument('output', action='store',
                        default=None,
                        help="Where to write out the output files")

    parser.add_argument('--cache', action='store',
                        help="Service cache, to work offline.")

    args = parser.parse_args()

    # Connect, with authentication.
    def get_service():
        scopes = ['https://www.googleapis.com/auth/drive']
        _, http = docs.get_auth_via_service_account(scopes)
        service = discovery.build('drive', 'v3', http=http)
        return service.files()
    files = (_Cache(args.cache, get_service)
             if args.cache
             else get_service())

    # Get the ids of the documents listed in the index page.
    indexid = docs.find_index_document(files)
    assert indexid
    docids = docs.enumerate_linked_documents(files, indexid)

    # Figure out which format to download.
    mime_type, convert = docs.CONVERSION_MAP[args.conversion]

    # Allocate a temporary directory for the output.
    os.makedirs(args.output, exist_ok=True)

    # Download the docs.
    filenames = docs.download_docs(files, docids, args.output, mime_type)

    # Post-process the files.
    if convert is not None:
        convert(filenames, args.output)

    logging.info("Output produced in {}".format(args.output))


if __name__ == '__main__':
    main()
