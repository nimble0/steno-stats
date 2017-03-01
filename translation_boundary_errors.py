#!/usr/bin/python

from __future__ import print_function
import sys
from argparse import ArgumentParser
try:
    import simplejson as json
except ImportError:
    import json
import re


def strokes_to_string(strokes):
    strokes_str = ""
    for stroke in strokes:
        if len(stroke) > 0:
            strokes_str += stroke + "/"
    strokes_str = strokes_str[:-1]

    return strokes_str


arg_parser = ArgumentParser(description="Find word boundary errors in dictionaries.")
arg_parser.add_argument("dictionaries", nargs="+", help="dictionary file paths")
args = arg_parser.parse_args()

dictionary_entries = {}
for dictionary_file in args.dictionaries:
    with open(dictionary_file) as data_file:
        dictionary_entries.update(json.load(data_file))

dictionary_entries_list = [strokes.split("/")
    for strokes, translation in dictionary_entries.items()]

def match_strokes(dictionary_entries, strokes, ignore_equal_or_larger = False):
    matches = []
    for strokes2 in [x for x in dictionary_entries
        if x[:len(strokes)] == strokes[:len(x)]
            and (not ignore_equal_or_larger or len(x) < len(strokes))]:

        strokes2_str = strokes_to_string(strokes2)
        if len(strokes2) >= len(strokes):
            matches.append([strokes2_str])
        else:
            matches += [[strokes2_str] + match
                for match in match_strokes(
                    dictionary_entries,
                    strokes[len(strokes2):])]

    return matches

boundary_errors = {}
entry_i = 0
for strokes in dictionary_entries_list:
    entry_boundary_errors = []

    entry_boundary_errors = match_strokes(dictionary_entries_list, strokes, True)
    if len(entry_boundary_errors) > 0:
        boundary_errors[strokes_to_string(strokes)] = entry_boundary_errors

    pre_progress_percent = (100*entry_i)/len(dictionary_entries_list)
    entry_i += 1
    post_progress_percent = (100*entry_i)/len(dictionary_entries_list)
    if post_progress_percent > pre_progress_percent:
        print(str(post_progress_percent) + "%", file=sys.stderr)


print(json.dumps(boundary_errors,
    ensure_ascii = False,
    indent = 2,
    separators = (',', ': ')))
