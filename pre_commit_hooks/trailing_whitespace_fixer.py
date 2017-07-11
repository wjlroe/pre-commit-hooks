from __future__ import print_function

import argparse
import os
import sys

from pre_commit_hooks.util import cmd_output


def _fix_file(filename, is_markdown):
    with open(filename, mode='rb') as file_processed:
        lines = file_processed.readlines()
    newlines = [_process_line(line, is_markdown) for line in lines]
    if newlines != lines:
        with open(filename, mode='wb') as file_processed:
            for line in newlines:
                file_processed.write(line)
        return True
    else:
        return False


def _process_line(line, is_markdown):
    # preserve trailing two-space for non-blank lines in markdown files
    eol = b'\r\n' if line[-2:] == b'\r\n' else b'\n'
    if is_markdown and (not line.isspace()) and line.endswith(b'  ' + eol):
        return line.rstrip() + b'  ' + eol
    return line.rstrip() + eol


def _whitespace_before_crlf(line):
    return line[-3:-2] == b' ' or line[-3:-2] == b'\t'

def _whitespace_before_lf(line):
    return line[-2:-1] == b' ' or line[-2:-1] == b'\t'

def _has_trailing_whitespace(filename):
    trailing = False
    with open(filename, mode='rb') as fd:
        for line in fd:
            if _whitespace_before_lf(line) or _whitespace_before_crlf(line):
                trailing = True
                break
    return trailing

def fix_trailing_whitespace(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--no-markdown-linebreak-ext',
        action='store_const',
        const=[],
        default=argparse.SUPPRESS,
        dest='markdown_linebreak_ext',
        help='Do not preserve linebreak spaces in Markdown'
    )
    parser.add_argument(
        '--markdown-linebreak-ext',
        action='append',
        const='',
        default=['md,markdown'],
        metavar='*|EXT[,EXT,...]',
        nargs='?',
        help='Markdown extensions (or *) for linebreak spaces'
    )
    parser.add_argument('filenames', nargs='*', help='Filenames to fix')
    args = parser.parse_args(argv)

    if os.name == 'nt':
        bad_whitespace_files = [
            filename for filename in args.filenames
            if _has_trailing_whitespace(filename)
        ]
    else:
        bad_whitespace_files = cmd_output(
            'grep', '-l', '[[:space:]]$', *args.filenames, retcode=None
        ).strip().splitlines()

    md_args = args.markdown_linebreak_ext
    if '' in md_args:
        parser.error('--markdown-linebreak-ext requires a non-empty argument')
    all_markdown = '*' in md_args
    # normalize all extensions; split at ',', lowercase, and force 1 leading '.'
    md_exts = [
        '.' + x.lower().lstrip('.') for x in ','.join(md_args).split(',')
    ]

    # reject probable "eaten" filename as extension (skip leading '.' with [1:])
    for ext in md_exts:
        if any(c in ext[1:] for c in r'./\:'):
            parser.error(
                "bad --markdown-linebreak-ext extension '{}' (has . / \\ :)\n"
                "  (probably filename; use '--markdown-linebreak-ext=EXT')"
                .format(ext)
            )

    return_code = 0
    for bad_whitespace_file in bad_whitespace_files:
        _, extension = os.path.splitext(bad_whitespace_file.lower())
        md = all_markdown or extension in md_exts
        if _fix_file(bad_whitespace_file, md):
            print('Fixing {}'.format(bad_whitespace_file))
            return_code = 1
    return return_code


if __name__ == '__main__':
    sys.exit(fix_trailing_whitespace())
