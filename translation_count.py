#!/usr/bin/python

import sys

from argparse import ArgumentParser

import log_reader

from collections import OrderedDict
try:
    import simplejson as json
except ImportError:
    import json


def strokes_to_string(strokes):
    strokes_str = ""
    for stroke in strokes:
        if len(stroke) > 0:
            strokes_str += stroke + "/"
    strokes_str = strokes_str[:-1]

    return strokes_str


arg_parser = ArgumentParser(description="Count entry counts in plover logs. Outputs a JSON formatted dictionary of translations and dictionaries of stroke sequences and their counts to standard out.")
arg_parser.add_argument("logs", nargs="+", help="log file paths")
arg_parser.add_argument("-r", "--resume", help="start recording after encountering this translation")
arg_parser.add_argument("-s", "--suspend", help="stop recording when encountering this translation")
args = arg_parser.parse_args()

log = []
for log_file in args.logs:
    with open(log_file) as data_file:
        log += data_file.readlines()

log_strokes = log_reader.process_log(log, args.resume, args.suspend)


UNDO_PREFIX = "{UNDO} "
UNTRANSLATE = "{NONE}"

class TranslationCounts:
    counts = {}

    def ensure_count_initialised(self, translation, strokes):
        if not translation in self.counts:
            self.counts[translation] = {}
        if not strokes in self.counts[translation]:
            self.counts[translation][strokes] = 0

    def add(self, translation, strokes):
        self.ensure_count_initialised(translation, strokes)
        self.counts[translation][strokes] += 1

    def remove(self, translation, strokes):
        self.ensure_count_initialised(translation, strokes)
        self.counts[translation][strokes] -= 1

    def clean(self):
        # Remove zero count translation entries
        for translation in self.counts.keys():
            self.counts[translation] = {
                k: v for k, v in self.counts[translation].iteritems() if v > 0 }
        self.counts = {
            k: v for k, v in self.counts.iteritems() if len(v) > 0 }

translation_counts = TranslationCounts()

for log_stroke in log_strokes:
    for translation in log_stroke.undo_translations + log_stroke.do_translations:
        if translation.translation is None:
            translation.translation = UNTRANSLATE

    if log_stroke.stroke == "*":
        # Undo stroke can have no undo translations when
        # Plover's undo buffer is empty
        if len(log_stroke.undo_translations) != 0:
            translation_counts.add(
                UNDO_PREFIX + log_stroke.undo_translations[0].translation,
                strokes_to_string(log_stroke.undo_translations[0].strokes))
    else:
        for translation in log_stroke.undo_translations:
            translation_counts.remove(
                translation.translation,
                strokes_to_string(translation.strokes))

        for translation in log_stroke.do_translations:
            translation_counts.add(
                translation.translation,
                strokes_to_string(translation.strokes))

translation_counts.clean()

# Sort dictionaries by reverse counts
sorted_translation_counts = OrderedDict(sorted(
    translation_counts.counts.items(), key=lambda o: sum(o[1].values()), reverse=True))
for translation in sorted_translation_counts.keys():
    sorted_translation_counts[translation] = OrderedDict(sorted(
        sorted_translation_counts[translation].items(),
        key=lambda o: o[1], reverse=True))


print(json.dumps(sorted_translation_counts,
    ensure_ascii = False,
    indent = 2,
    separators = (',', ': ')))
