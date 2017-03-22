#!/usr/bin/python

from __future__ import print_function
import sys
from argparse import ArgumentParser
try:
    import simplejson as json
except ImportError:
    import json
from collections import OrderedDict


class StrokeTree:
    def __init__(self, strokes_list = {}):
        self.is_leaf = False
        self.child_count = 0
        self.children = {}
        for strokes in strokes_list:
            self.add(strokes)

    def add(self, strokes):
        if not strokes[0] in self.children:
            self.children[strokes[0]] = StrokeTree()

        if len(strokes) > 1:
            self.children[strokes[0]].child_count += 1
            self.children[strokes[0]].add(strokes[1:])
        else:
            self.is_leaf = True

    def to_string(self):
        string = "StrokeTree{\n" \
            "  is_leaf=" + str(self.is_leaf) + ",\n" \
            "  child_count=" + str(self.child_count) + ",\n" \
            "  children={\n"
        for key, tree in self.children.items():
            string += "    " + key + "=" + tree.to_string().replace("\n", "\n    ") + ",\n"
        string += "  }\n}"

        return string

    def match(self, strokes):
        if not strokes[0] in self.children:
            return StrokeTree()

        if len(strokes) == 1:
            return self.children[strokes[0]]
        else:
            return self.children[strokes[0]].match(strokes[1:])


class BoundaryErrorMatcher:
    def __init__(self, dictionary_entries, include_trivial):
        self.dictionary_entries_strokes_list = [tuple(strokes.split("/"))
            for strokes, translation in dictionary_entries.items()]
        self.dictionary_entries_strokes = set(self.dictionary_entries_strokes_list)

        self.dictionary_entries_strokes_tree = StrokeTree(
            self.dictionary_entries_strokes_list)

        self.cached_suffix_strokes = {}

        self.include_trivial = include_trivial

    def matches(self, strokes):
        if len(strokes) == 1:
            return {}

        matches = self.matches_(strokes)

        if "/".join(strokes) in matches:
            del matches["/".join(strokes)]
        if "/".join(strokes) + "/" in matches:
            del matches["/".join(strokes) + "/"]

        return matches

    def matches_(self, strokes):
        strokes_str = "/".join(strokes)
        if strokes_str in self.cached_suffix_strokes:
            return self.cached_suffix_strokes[strokes_str]

        matches = {}

        if self.include_trivial and strokes in self.dictionary_entries_strokes:
            matches[strokes_str] = 1

        full_matches = self.dictionary_entries_strokes_tree.match(strokes).child_count
        if full_matches > 0:
            matches[strokes_str + "/"] = full_matches

        for n in range(0, len(strokes)):
            if strokes[:n] in self.dictionary_entries_strokes:
                sub_matches = self.matches_(strokes[n:])

                partial_match_str = "/".join(strokes[:n]) + " "

                for match, count in sub_matches.items():
                    matches[partial_match_str + match] = count

        self.cached_suffix_strokes[strokes_str] = matches

        return matches.copy()

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


arg_parser = ArgumentParser(description="Find potential translation boundary errors in dictionaries. Outputs a JSON formatted dictionary of stroke sequences and a list of their potential translation boundary errors to standard out.")
arg_parser.add_argument("dictionaries", nargs="+", help="dictionary file paths")
arg_parser.add_argument("-t", "--trivial", action="store_true", help="include trivial matches, these are matches where the strokes match exactly (eg/ A/HED and A HED)")
arg_parser.add_argument("-ss", "--stroke_sequence", help="only look for boundary errors involving this stroke sequence")
arg_parser.add_argument("-at", "--add_translations", action="store_true", help="add translations to stroke lists")
arg_parser.add_argument("-p", "--progress", action="store_true", help="output progress percentage on standard error")
args = arg_parser.parse_args()

dictionary_entries = {}
for dictionary_file in args.dictionaries:
    with open(dictionary_file) as data_file:
        dictionary_entries.update(json.load(data_file))

if not args.stroke_sequence is None and not args.stroke_sequence in dictionary_entries:
    dictionary_entries[args.stroke_sequence] = ""

boundary_error_matcher = BoundaryErrorMatcher(dictionary_entries, args.trivial)

check_entries = boundary_error_matcher.dictionary_entries_strokes
if not args.stroke_sequence is None:
    arg_stroke_sequence_parts = tuple(args.stroke_sequence.split("/"))

    check_entries = [x for x in boundary_error_matcher.dictionary_entries_strokes_list
        if contains(x, arg_stroke_sequence_parts)
        or common_prefix_suffix(x, arg_stroke_sequence_parts)]

boundary_errors = {}
entry_i = 0
for strokes in check_entries:
    entry_boundary_errors = boundary_error_matcher.matches(strokes)
    for error in [key for key, count in entry_boundary_errors.items()
        if count == 1 and key[-1] == "/"]:

        parts = error.split(" ")
        suffix = parts[-1][:-1]

        full_strokes = error[:-1]

        suffix_tree = boundary_error_matcher.dictionary_entries_strokes_tree.match(suffix.split("/"))
        while len(suffix_tree.children) == 1:
            sole_suffix = list(suffix_tree.children.items())[0]
            full_strokes += "/" + sole_suffix[0]
            suffix_tree = sole_suffix[1]

        entry_boundary_errors[full_strokes] = 1
        del entry_boundary_errors[error]

    if len(entry_boundary_errors) > 0:
        boundary_errors["/".join(strokes)] = entry_boundary_errors

    if args.progress:
        pre_progress_percent = (100*entry_i)/len(check_entries)
        entry_i += 1
        post_progress_percent = (100*entry_i)/len(check_entries)
        if post_progress_percent > pre_progress_percent:
            print(str(post_progress_percent) + "%", file=sys.stderr)

if not args.stroke_sequence is None:
    remove_boundary_errors = []
    for boundary_error, matches in boundary_errors.items():
        if boundary_error == args.stroke_sequence:
            continue

        remove_matches = []
        for match in matches:
            parts = match.split(" ")
            tail_strokes = tuple(parts[-1].split("/")[:-1])

            if not (args.stroke_sequence in parts
                or tail_strokes == arg_stroke_sequence_parts[:len(tail_strokes)]):
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
    separators = (",", ": ")))
