#!/usr/bin/python

import sys

try:
    # Plover setup
    from plover.config import CONFIG_FILE, Config
    from plover.registry import registry
    from plover import system
    from plover.dictionary.base import create_dictionary, load_dictionary

    def setup():
        config = Config()
        config.target_file = CONFIG_FILE
        with open(config.target_file, 'rb') as f:
            config.load(f)
            registry.load_plugins()
            registry.update()
            system_name = config.get_system_name()
            system.setup(system_name)

    setup()

    import plover.formatting
except ImportError:
    print("Error initialising Plover. Make sure Plover is added to PYTHONPATH.")
    sys.exit()

import re
import datetime


class Translation:
    def __init__(self, time, translation, strokes, text):
        self.time = time
        self.translation = translation
        self.strokes = strokes
        self.text = text

class LogStroke:
    def __init__(self, time, undo_translations, do_translations, stroke):
        self.time = time
        self.undo_translations = undo_translations
        self.do_translations = do_translations
        self.stroke = stroke

class TranslationsProcessor:
    def __init__(self):
        self.undos = []
        self.dos = []

    def process_translations(self):
        def count_matching_translations(strokes, translations):
            i = 0
            count = 0
            for translation in translations:
                for stroke in translation.strokes:
                    if i == len(strokes) or stroke != strokes[i]:
                        return False

                    i += 1

                count += 1
                if i == len(strokes):
                    return count

            return False

        undo_combine_i = 0
        do_combine_i = 0

        if len(self.undos) > 0 and len(self.dos) > 0:
            if len(self.undos[-1].strokes) > len(self.dos[0].strokes):
                # Some automatic redo translations
                count = count_matching_translations(
                    self.undos[-1].strokes[:-1],
                    self.dos)

                if count:
                    undo_combine_i = -1
                    do_combine_i = count

            elif len(self.undos[-1].strokes) < len(self.dos[0].strokes):
                # Some automatic undo translations
                count = count_matching_translations(
                    self.dos[0].strokes[:-1],
                    reversed(self.undos))

                if count:
                    undo_combine_i = -count
                    do_combine_i = 1


        simple_undos   = self.undos[:undo_combine_i] if undo_combine_i else self.undos
        combined_undos = self.undos[undo_combine_i:] if undo_combine_i else []
        simple_dos     = self.dos[do_combine_i:]     if do_combine_i   else self.dos
        combined_dos   = self.dos[:do_combine_i]     if do_combine_i   else []

        self.undos = []
        self.dos = []


        strokes = []

        for translation_ in simple_undos:
            strokes.append(LogStroke(translation_.time, [translation_], [], "*"))

        if undo_combine_i != 0 and do_combine_i != 0:
            stroke = None
            if len(combined_undos[-1].strokes) < len(combined_dos[0].strokes):
                stroke = combined_dos[0].strokes[-1]
            else:
                stroke = "*"

            strokes.append(LogStroke(
                combined_undos[0].time,
                combined_undos,
                combined_dos,
                stroke))

        for translation_ in simple_dos:
            strokes.append(LogStroke(translation_.time, [], [translation_], translation_.strokes[-1]))


        return strokes

def process_log(lines, resume, suspend):
    recording = resume is None

    processor = TranslationsProcessor()
    is_previous_translation_removal = False

    log_strokes = []
    actions_buffer = []

    for line in lines:
        match = re.match(r"""
            ^(?P<time>[0-9\-:, ]*)
            (?P<removal>\*?)Translation\(
            \((?P<strokes>[A-Z\-,'* ]*)\)
            \s* : \s*
            (?:(?:\"(?P<translation>(?:[^\\\"]|(?:\\\\)*\\[^\"]|(?:\\\\)*\\\")*)\")|None)
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

            actions = []
            if not match.group("translation") is None:
                actions = plover.formatting._translation_to_actions(
                    match.group("translation"),
                    actions_buffer[-1] if len(actions_buffer) > 0 else plover.formatting._Action(),
                    False)

            actions_text = ""
            for action in actions:
                actions_text += action.text

            translation = Translation(
                datetime.datetime.strptime(match.group("time").strip(), "%Y-%m-%d %H:%M:%S,%f"),
                match.group("translation"),
                strokes,
                actions_text)


            if removal:
                for action in reversed(actions):
                    if action == actions_buffer[-1]:
                        actions_buffer.pop()
                    else:
                        # Error undoing actions
                        break
            else:
                actions_buffer += actions


            if translation.translation == resume:
                recording = True

                log_strokes += processor.process_translations()

            elif translation.translation == suspend:
                recording = False

                log_strokes += processor.process_translations()

            elif recording:
                if removal:
                    if not is_previous_translation_removal:
                        log_strokes += processor.process_translations()

                    processor.undos.append(translation)
                else:
                    processor.dos.append(translation)

                is_previous_translation_removal = removal

    log_strokes += processor.process_translations()

    return log_strokes
