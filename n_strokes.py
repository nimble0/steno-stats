#!/usr/bin/python

import sys

from argparse import ArgumentParser

import log_reader

from collections import OrderedDict
try:
    import simplejson as json
except ImportError:
    import json


arg_parser = ArgumentParser(description="Count n-strokes in plover logs.")
arg_parser.add_argument("logs", nargs="+", help="log file paths")
arg_parser.add_argument("-r", "--resume", help="start recording after encountering this translation")
arg_parser.add_argument("-s", "--suspend", help="stop recording when encountering this translation")
arg_parser.add_argument("-n", "--range", required=True, nargs=2, type=int,
    help="range of n-strokes to track")
arg_parser.add_argument("-c", "--min-count", type=int, help="minimum count to output")
arg_parser.add_argument("-l", "--limit-output", type=int, help="maximum output entries")
args = arg_parser.parse_args()

log = []
for log_file in args.logs:
    with open(log_file) as data_file:
        log += data_file.readlines()

log_strokes = log_reader.process_log(log, args.resume, args.suspend)

class StrokeListCounts:
    counts = {}

    def ensure_count_initialised(self, stroke_list):
        if not stroke_list in self.counts:
            self.counts[stroke_list] = 0

    def add(self, stroke_list):
        self.ensure_count_initialised(stroke_list)
        self.counts[stroke_list] += 1

    def remove(self, stroke_list):
        self.ensure_count_initialised(stroke_list)
        self.counts[stroke_list] -= 1

    def clean(self, min_count = 0):
        # Remove zero count translation entries
        self.counts = {
            k: v for k, v in self.counts.iteritems() if v > min_count }

stroke_list_counts = StrokeListCounts()

strokes = []
for log_stroke in log_strokes:
    if log_stroke.stroke == "*":
        strokes.pop()
    else:
        strokes.append(log_stroke.stroke)

        for i in range(args.range[0], args.range[1]):
            if len(strokes) > i:
                stroke_list_counts.add("/".join(strokes[-i:]))

if args.min_count is None:
    stroke_list_counts.clean()
else:
    stroke_list_counts.clean(args.min_count)

# Sort dictionaries by reverse counts
sorted_stroke_list_counts_ = sorted(
    stroke_list_counts.counts.items(), key=lambda o: o[1], reverse=True)
if not args.limit_output is None:
    sorted_stroke_list_counts_ = sorted_stroke_list_counts_[:args.limit_output]

sorted_stroke_list_counts = OrderedDict(sorted_stroke_list_counts_)

print(json.dumps(sorted_stroke_list_counts,
    ensure_ascii = False,
    indent = 2,
    separators = (',', ': ')))
