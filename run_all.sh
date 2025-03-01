#!/bin/bash

python3 /Users/j/hg/MC6Pro/print_grammar.py
python3 /Users/j/hg/MC6Pro/footsmart.py Configs/Config.yaml tmp/Config.json
python3 /Users/j/hg/MC6Pro/footsmart.py Configs/Empty.yaml tmp/Empty.json
python3 /Users/j/hg/MC6Pro/footsmart.py -I Configs/Config.yaml tmp/Config.yaml
python3 /Users/j/hg/MC6Pro/footsmart.py Configs/Example.yaml tmp/Example.json
python3 /Users/j/hg/MC6Pro/footsmart.py -b Configs/Test/MIDIClock.json tmp/MIDIClock_Intuitive_Script.yaml
python3 /Users/j/hg/MC6Pro/footsmart.py -b /Users/j/Downloads/DelaySetlist.json tmp/DelaySetlist.yaml
python3 /Users/j/hg/MC6Pro/footsmart.py -b Configs/Test/PCNumberScroll.json tmp/PCNumber_Intuitive_Script.yaml
python3 /Users/j/hg/MC6Pro/footsmart.py -b Configs/Test/SetToggle.json tmp/SetToggle_Intuitive_Script.yaml
python3 /Users/j/hg/MC6Pro/footsmart.py -b Configs/Test/WaveformSequence.json tmp/WaveformSequence_Intuitive_Script.yaml
python3 /Users/j/hg/MC6Pro/footsmart.py -s Configs/Test/Demo.yaml tmp/Demo.json
python3 /Users/j/hg/MC6Pro/footsmart.py -s tmp/DelaySetlistGood.yaml tmp/DelaySetlistGood.json
python3 /Users/j/hg/MC6Pro/footsmart.py -b Configs/Test/Empty.json tmp/Empty_Intuitive_Script.json
python3 /Users/j/hg/MC6Pro/footsmart.py -b Configs/Test/Features.json tmp/Features_Intuitive_Script.json
