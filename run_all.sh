#!/bin/bash

/Library/Developer/CommandLineTools/usr/bin/python3 /Users/j/hg/MC6Pro/print_grammar.py
/Library/Developer/CommandLineTools/usr/bin/python3 /Users/j/hg/MC6Pro/footsmart.py Configs/Config.yaml tmp/Config.json
/Library/Developer/CommandLineTools/usr/bin/python3 /Users/j/hg/MC6Pro/footsmart.py Configs/Empty.yaml tmp/Empty.json
/Library/Developer/CommandLineTools/usr/bin/python3 /Users/j/hg/MC6Pro/footsmart.py -I Configs/Config.yaml tmp/Config.yaml
/Library/Developer/CommandLineTools/usr/bin/python3 /Users/j/hg/MC6Pro/footsmart.py Configs/Example.yaml tmp/Example.json
/Library/Developer/CommandLineTools/usr/bin/python3 /Users/j/hg/MC6Pro/footsmart.py -b Configs/Test/MIDIClock.json tmp/MIDIClock_Intuitive_Script.yaml
/Library/Developer/CommandLineTools/usr/bin/python3 /Users/j/hg/MC6Pro/footsmart.py -b /Users/j/Downloads/DelaySetlist.json tmp/DelaySetlist.yaml
/Library/Developer/CommandLineTools/usr/bin/python3 /Users/j/hg/MC6Pro/footsmart.py -b Configs/Test/PCNumberScroll.json tmp/PCNumber_Intuitive_Script.yaml
/Library/Developer/CommandLineTools/usr/bin/python3 /Users/j/hg/MC6Pro/footsmart.py -b Configs/Test/SetToggle.json tmp/SetToggle_Intuitive_Script.yaml
/Library/Developer/CommandLineTools/usr/bin/python3 /Users/j/hg/MC6Pro/footsmart.py -b Configs/Test/WaveformSequence.json tmp/WaveformSequence_Intuitive_Script.yaml
/Library/Developer/CommandLineTools/usr/bin/python3 /Users/j/hg/MC6Pro/footsmart.py -s Configs/Test/Demo.yaml tmp/Demo.json
/Library/Developer/CommandLineTools/usr/bin/python3 /Users/j/hg/MC6Pro/footsmart.py -s tmp/DelaySetlistGood.yaml tmp/DelaySetlistGood.json
/Library/Developer/CommandLineTools/usr/bin/python3 /Users/j/hg/MC6Pro/footsmart.py -b Configs/Test/Empty.json tmp/Empty_Intuitive_Script.json
/Library/Developer/CommandLineTools/usr/bin/python3 /Users/j/hg/MC6Pro/footsmart.py -b Configs/Test/Features.json tmp/Features_Intuitive_Script.json
