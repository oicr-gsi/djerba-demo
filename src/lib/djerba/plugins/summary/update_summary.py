#! /usr/bin/env python3

import argparse
import json
import sys
sys.path.pop(0) # do not import from script directory

from djerba.util.validator import path_validator
import djerba.util.constants as constants
import djerba.util.ini_fields as ini

def get_parser():
    """Construct the parser for command-line arguments"""
    parser = argparse.ArgumentParser(
        description='update_summary.py: Update the results summary text in Djerba report JSON',
    )
    parser.add_argument('-i', '--in', dest='in_path', metavar='PATH', required=True, help='JSON input file, or - for STDIN')
    parser.add_argument('-o', '--out', metavar='PATH', required=True, help='JSON output file, or - for STDOUT')
    parser.add_argument('-s', '--summary', metavar='PATH', required=True, help='Text file to insert as results summary; required')
    return parser

def main(args):
    SUMMARY_TEXT = 'summary_text'
    val = path_validator()
    if args.in_path == '-':
        data = json.loads(sys.stdin.read())
    else:
        val.validate_input_file(args.in_path)
        with open(args.in_path) as in_file:
            data = json.loads(in_file.read())
    val.validate_input_file(args.summary)
    with open(args.summary) as sum_file:
        summary = sum_file.read().strip()
    data['plugins']['summary']['results'][SUMMARY_TEXT] = summary
    if args.out == '-':
        sys.stdout.write(json.dumps(data))
    else:
        val.validate_output_file(args.out)
        with open(args.out, 'w') as out_file:
            out_file.write(json.dumps(data))

if __name__ == '__main__':
    parser = get_parser()
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)
    main(parser.parse_args())