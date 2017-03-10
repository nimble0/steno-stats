# Steno stats

Scripts for analyzing Plover logs and dictionaries and giving various information.


## strokes_per_word.py

Requires Plover source in the PYTHONPATH environment variable (prefix the command with PYTHONPATH=/path/to/plover).

**usage**: strokes_per_word.py [-h] [-r RESUME] [-s SUSPEND] logs [logs ...]

Calculate strokes per word in plover logs. Outputs to standard out.

**positional arguments**:
* *logs*                log file paths

**optional arguments**:
* *-h, --help*          show this help message and exit
* *-r RESUME, --resume RESUME*
                        start recording after encountering this translation
* *-s SUSPEND, --suspend SUSPEND*
                        stop recording when encountering this translation

## translation_count.py

Requires Plover source in the PYTHONPATH environment variable (prefix the command with PYTHONPATH=/path/to/plover).

**usage**: translation_count.py [-h] [-r RESUME] [-s SUSPEND] logs [logs ...]

Count entry counts in plover logs. Outputs a JSON formatted dictionary of translations and dictionaries of stroke sequences and their counts to standard out.

**positional arguments**:
* *logs*                log file paths

**optional arguments**:
* *-h, --help*          show this help message and exit
* *-r RESUME, --resume RESUME*
                        start recording after encountering this translation
* *-s SUSPEND, --suspend SUSPEND*
                        stop recording when encountering this translation

## time_statistics.py

Requires Plover source in the PYTHONPATH environment variable (prefix the command with PYTHONPATH=/path/to/plover).

**usage**: time_statistics.py [-h] [-r RESUME] [-s SUSPEND]
                          [-sa SPEED_ACTIVATION SPEED_ACTIVATION SPEED_ACTIVATION]
                          -w SAMPLE_WINDOW [--raw]
                          logs [logs ...]

Measure statistics over time in Plover logs. Outputs as CSV to standard out.

**positional arguments**:
* logs                  log file paths

**optional arguments**:
* *-h, --help*          show this help message and exit
* *-r RESUME, --resume RESUME*
                        start recording after encountering this translation
* *-s SUSPEND, --suspend SUSPEND*
                        stop recording when encountering this translation
* * -sa SPEED_ACTIVATION SPEED_ACTIVATION SPEED_ACTIVATION, --speed_activation SPEED_ACTIVATION SPEED_ACTIVATION SPEED_ACTIVATION*
                        speed to start recording on (stroke/second), speed to
                        stop recording on (stroke/second), length of window to
                        check speed in (seconds)
* *-w SAMPLE_WINDOW, --sample-window SAMPLE_WINDOW*
                        duration of time (seconds) to sample for each discrete
                        statistic
* *--raw*               raw statistics only, no derived

## n_strokes.py

Requires Plover source in the PYTHONPATH environment variable (prefix the command with PYTHONPATH=/path/to/plover).

**usage**: n_strokes.py [-h] [-r RESUME] [-s SUSPEND] -n RANGE RANGE
                    [-c MIN_COUNT] [-l LIMIT_OUTPUT]
                    logs [logs ...]

Count n-strokes in plover logs. Outputs a JSON formatted dictionary of stroke sequences and their counts to standard out.

**positional arguments**:
* *logs*                log file paths

**optional arguments**:
* *-h, --help*          show this help message and exit
* *-r RESUME, --resume RESUME*
                        start recording after encountering this translation
* *-s SUSPEND, --suspend SUSPEND*
                        stop recording when encountering this translation
* *-n RANGE RANGE, --range RANGE RANGE*
                        range of n-strokes to track
* *-c MIN_COUNT, --min-count MIN_COUNT*
                        minimum count to output
* *-l LIMIT_OUTPUT, --limit-output LIMIT_OUTPUT*
                        maximum output entries

## translation_boundary_errors.py

**usage**: translation_boundary_errors.py [-h] [-ht] [-ss STROKE_SEQUENCE] [-at]
                                      [-p]
                                      dictionaries [dictionaries ...]

Find potential translation boundary errors in dictionaries. Outputs a JSON
formatted dictionary of stroke sequences and a list of their potential
translation boundary errors to standard out.

**positional arguments**:
* *dictionaries*        dictionary file paths

**optional arguments**:
* *-h, --help*          show this help message and exit
* *-t, --trivial*       include trivial matches, these are matches where the
                        strokes match exactly (eg/ A/HED and A HED)
* *-ss STROKE_SEQUENCE, --stroke_sequence STROKE_SEQUENCE*
                        only look for boundary errors involving this stroke
                        sequence
* *-at, --add_translations*
                        add translations to stroke lists
* *-p, --progress*      output progress percentage on standard error
