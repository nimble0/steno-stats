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

    direct_match = None
    direct_matches = 0
    if not ignore_larger:
        for strokes2 in [x for x in dictionary_entries
            if x[:len(strokes)] == strokes and len(x) > len(strokes)]:
            direct_match = strokes2
            direct_matches += 1

    if direct_matches == 1:
        matches["/".join(direct_match)] = 1
    elif direct_matches > 0:
        matches[strokes_str + "/"] = direct_matches

    for n in range(0, len(strokes)):
        if strokes[:n] in dictionary_entries:
            sub_matches = match_strokes(
                dictionary_entries,
                strokes[n:],
                cached_suffix_strokes,
                ignore_perfect)

            partial_match_str = "/".join(strokes[:n]) + " "

            for match, count in sub_matches.items():
                matches[partial_match_str + match] = count

    cached_suffix_strokes[strokes_str] = matches

    return matches

def contains(list_a, list_b):
    for i in range(0, len(list_a)-len(list_b)+1):
        if list_a[i:i + len(list_b)] == list_b:
            return True

    return False

def common_prefix_suffix(list_a, list_b):
    for i in range(-len(list_b)+1, 0):
        if list_a[i:] == list_b[:-i]:
            return True

    return False


arg_parser = ArgumentParser(description="Find potential translation boundary errors in dictionaries. Outputs a JSON formatted dictionary of stroke sequences and a list of their potential translation boundary errors to standard out. This can be slow to run, consider using the --progress option.")
arg_parser.add_argument("dictionaries", nargs="+", help="dictionary file paths")
arg_parser.add_argument("-ht", "--hide_trivial", action="store_true", help="hide trivial matches")
arg_parser.add_argument("-ss", "--strokes_sequence", help="only look for boundary errors involving this stroke sequence")
arg_parser.add_argument("-at", "--add_translations", action="store_true", help="add translations to stroke lists")
arg_parser.add_argument("-p", "--progress", action="store_true", help="output progress percentage on standard error")
args = arg_parser.parse_args()

dictionary_entries = {}
for dictionary_file in args.dictionaries:
    with open(dictionary_file) as data_file:
        dictionary_entries.update(json.load(data_file))

dictionary_entries_strokes = set([tuple(strokes.split("/"))
    for strokes, translation in dictionary_entries.items()])


boundary_errors = {}

cached_suffix_strokes = {}
if args.strokes_sequence is None:
    entry_i = 0
    for strokes in dictionary_entries_strokes:
        if len(strokes) > 1:
            entry_boundary_errors = match_strokes(
                dictionary_entries_strokes,
                strokes,
                cached_suffix_strokes,
                args.hide_trivial,
                args.hide_trivial)
            if len(entry_boundary_errors) > 0:
                boundary_errors["/".join(strokes)] = entry_boundary_errors

        if args.progress:
            pre_progress_percent = (100*entry_i)/len(dictionary_entries_strokes)
            entry_i += 1
            post_progress_percent = (100*entry_i)/len(dictionary_entries_strokes)
            if post_progress_percent > pre_progress_percent:
                print(str(post_progress_percent) + "%", file=sys.stderr)
else:
    must_involve_strokes = tuple(args.strokes_sequence.split("/"))

    dictionary_entries_strokes.add(must_involve_strokes)

    for i in range(1, len(must_involve_strokes) + 1 if not args.hide_trivial else 0):
        cached_suffix_strokes["/".join(must_involve_strokes[:i])] = { args.strokes_sequence: 1 }

    relevant_dictionary_entries = [x for x in dictionary_entries_strokes
        if contains(x, must_involve_strokes)
        or common_prefix_suffix(x, must_involve_strokes)]

    entry_i = 0
    for strokes in relevant_dictionary_entries:
        if len(strokes) > 1:
            entry_boundary_errors = match_strokes(
                dictionary_entries_strokes,
                strokes,
                cached_suffix_strokes,
                args.hide_trivial,
                args.hide_trivial)
            if len(entry_boundary_errors) > 0:
                boundary_errors["/".join(strokes)] = entry_boundary_errors

        if args.progress:
            pre_progress_percent = (100*entry_i)/len(relevant_dictionary_entries)
            entry_i += 1
            post_progress_percent = (100*entry_i)/len(relevant_dictionary_entries)
            if post_progress_percent > pre_progress_percent:
                print(str(post_progress_percent) + "%", file=sys.stderr)

    remove_boundary_errors = []
    for boundary_error, matches in boundary_errors.items():
        if boundary_error == args.strokes_sequence:
            continue

        remove_matches = []
        for match in matches:
            parts = match.split(" ")

            tail_strokes = tuple(parts[-1].split("/")[:-1])

            if not (must_involve_strokes in parts
                or tail_strokes == must_involve_strokes[:len(tail_strokes)]):
                remove_matches.append(match)

        for match in remove_matches:
            del matches[match]

        if len(matches) == 0:
            remove_boundary_errors.append(boundary_error)

    for boundary_error in remove_boundary_errors:
        del boundary_errors[boundary_error]

if args.add_translations:
    boundary_errors_with_translations = {}

    for strokes, matches in boundary_errors.items():
        matches_with_translations = {}
        for match_strokes, count in matches.items():
            translations = []
            for strokes_ in match_strokes.split(" "):
                if strokes_ in dictionary_entries:
                    translations.append(dictionary_entries[strokes_])
                else:
                    translations.append(strokes_)

            matches_with_translations[match_strokes + ": " + " ".join(translations)] = count

        if strokes in dictionary_entries:
            boundary_errors_with_translations[strokes + ": " + dictionary_entries[strokes]] = \
                matches_with_translations
        else:
            boundary_errors_with_translations[strokes] = \
                matches_with_translations

    boundary_errors = boundary_errors_with_translations

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
    separators = (",", ": ")).encode("utf-8"))
