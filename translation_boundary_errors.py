#!/usr/bin/python

from __future__ import print_function
import sys
from argparse import ArgumentParser
try:
    import simplejson as json
except ImportError:
    import json
from collections import OrderedDict


def match_strokes(
    dictionary_entries,
    strokes,
    cached_suffix_strokes,
    ignore_perfect = False,
    ignore_larger = False):

    strokes_str = "/".join(strokes)
    if strokes_str in cached_suffix_strokes:
        return cached_suffix_strokes[strokes_str]

    matches = {}

    if not ignore_perfect and strokes_str in dictionary_entries:
        matches[strokes_str] = 1

    direct_matches = 0
    if not ignore_larger:
        for strokes2 in [x for x in dictionary_entries
            if x[:len(strokes)] == strokes and len(x) > len(strokes)]:
            direct_matches += 1

    if direct_matches > 0:
        matches[strokes_str + "/"] = direct_matches

    for strokes2 in [x for x in dictionary_entries
        if x == strokes[:len(x)] and len(x) < len(strokes)]:

        partial_match_str = "/".join(strokes[:len(strokes2)]) + " "

        sub_matches = match_strokes(
            dictionary_entries,
            strokes[len(strokes2):],
            cached_suffix_strokes,
            ignore_perfect)

        for match, count in sub_matches.items():
            matches[partial_match_str + match] = count

    cached_suffix_strokes[strokes_str] = matches

    return matches


arg_parser = ArgumentParser(description="Find word boundary errors in dictionaries.")
arg_parser.add_argument("dictionaries", nargs="+", help="dictionary file paths")
arg_parser.add_argument("-ht", "--hide_trivial", action="store_true", help="hide trivial matches")
args = arg_parser.parse_args()

dictionary_entries = {}
for dictionary_file in args.dictionaries:
    with open(dictionary_file) as data_file:
        dictionary_entries.update(json.load(data_file))

dictionary_entries_list = [strokes.split("/")
    for strokes, translation in dictionary_entries.items()]


boundary_errors = {}

cached_suffix_strokes = {}
entry_i = 0
for strokes in dictionary_entries_list:
    if len(strokes) > 1:
        entry_boundary_errors = []

        entry_boundary_errors = match_strokes(
            dictionary_entries_list,
            strokes,
            cached_suffix_strokes,
            args.hide_trivial,
            args.hide_trivial)
        if len(entry_boundary_errors) > 0:
            boundary_errors["/".join(strokes)] = entry_boundary_errors

    pre_progress_percent = (100*entry_i)/len(dictionary_entries_list)
    entry_i += 1
    post_progress_percent = (100*entry_i)/len(dictionary_entries_list)
    if post_progress_percent > pre_progress_percent:
        print(str(post_progress_percent) + "%", file=sys.stderr)

# Sort dictionaries by reverse counts
sorted_boundary_errors = OrderedDict(sorted(
    boundary_errors.items(), key=lambda o: sum(o[1].values()), reverse=True))
for translation in sorted_boundary_errors.keys():
    sorted_boundary_errors[translation] = OrderedDict(sorted(
        sorted_boundary_errors[translation].items(),
        key=lambda o: o[1], reverse=True))

print(json.dumps(sorted_boundary_errors,
    ensure_ascii = False,
    indent = 2,
    separators = (',', ': ')))
