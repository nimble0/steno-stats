#!/usr/bin/python

import re


class Translation:
    def __init__(self, translation, strokes):
        self.translation = translation
        self.strokes = strokes

def process_log(lines, process_function, resume, suspend):
    recording = resume is None

    undo_translations = []

    for line in lines:
        match = re.match(r"""
            ^[0-9\-:, ]*
            (?P<removal>\*?)Translation\(
            \((?P<strokes>[A-Z\-,'* ]*)\)
            \s* : \s*
            \"(?P<translation>(?:[^\\\"]|(?:\\\\)*\\[^\"]|(?:\\\\)*\\\")*)\"
            \)
            """,
            line,
            re.VERBOSE)

        if match:
            removal = match.group("removal") == "*"

            strokes = match.group("strokes").split(",")
            strokes[:] = [stroke.strip()[1:-1] for stroke in strokes]
            if len(strokes) > 0 and len(strokes[-1]) == 0:
                strokes = strokes[:-1]

            translation = Translation(match.group("translation"), strokes)

            if translation.translation == resume:
                recording = True
            elif translation.translation == suspend:
                recording = False
            elif recording:
                if removal:
                    undo_translations.append(translation)
                else:
                    undo_strokes_count = 0
                    for translation_ in undo_translations:
                        undo_strokes_count += len(translation_.strokes)

                    process_function(
                        undo_translations = undo_translations,
                        translation = translation,
                        is_undo = undo_strokes_count == len(translation.strokes))
                    undo_translations = []

    process_function(
        undo_translations = undo_translations,
        translation = Translation("", []),
        is_undo = True)
