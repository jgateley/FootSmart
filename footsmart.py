# The script for handling config/backup files
# There are two modes
#
# Intuitive Mode (the default):
# This mode is used to convert an intuitive config file into a backup file, suitable for restoring to the controller.
# It can optionally generate the simple config file as an intermediary
#
# Backup/Simple mode:
# This mode is bidirectional, allowing converting backup files to simple files and vice versa
# It is useful for examining a controller backup file to see what is in it, or if the features of intuitive
# are not required

import argparse
import grammar as jg
import backup_grammar
import intuitive_grammar
import simple_grammar
import simple_model
from IntuitiveException import IntuitiveException

# Operations:
# Convert an intuitive file to a backup file --intuitive-to-backup -i
# Convert an intuitive file to a simple file --intuitive-to-simple -I
# Convert a simple file to a backup file     --simple-to-backup    -s
# Convert a backup file to a simple file     --backup-to-simple    -b
if __name__ == '__main__':
    desc = "Morningstar Configuration Management. Convert various file formats"
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('--backup-to-simple', '-b', action='store_true',
                        help='Convert a backup file to a simple file')
    parser.add_argument('--simple-to-backup', '-s', action='store_true',
                        help='Convert a simple config to a backup config')
    parser.add_argument('--intuitive-to-backup', '-i', action='store_true',
                        help='Convert a config file to an backup file')
    parser.add_argument('--intuitive-to-simple', '-I', action='store_true',
                        help='Convert a config file to an backup file')
    parser.add_argument('source', help='The source config')
    parser.add_argument('dest', help='The destination config')
    args = parser.parse_args()

    flags = 0
    if args.backup_to_simple:
        flags += 1
    if args.simple_to_backup:
        flags += 1
    if args.intuitive_to_backup:
        flags += 1
    if args.intuitive_to_simple:
        flags += 1
    if flags > 1:
        print("Error: At most one of -b, -i, or -c must be specified")
        exit(1)

    backup_grammar_obj = jg.Grammar(backup_grammar.backup_schema)
    simple_grammar_obj = jg.Grammar(simple_grammar.simple_schema, minimal=True)
    intuitive_grammar_obj = jg.Grammar(intuitive_grammar.intuitive_schema, minimal=True)

    source_file = jg.GrammarFile(args.source)
    dest_file = jg.GrammarFile(args.dest)

    try:
        if args.backup_to_simple:
            backup_model = backup_grammar_obj.parse_config(source_file.load())

            simple_model_obj = simple_model.Simple()
            simple_model_obj.from_backup(backup_model)

            dest_file.save(simple_grammar_obj.gen_config(simple_model_obj))
        elif args.simple_to_backup:
            simple_model_obj = simple_grammar_obj.parse_config(source_file.load())

            backup_model = simple_model_obj.to_backup()

            dest_file.save(backup_grammar_obj.gen_config(backup_model))
        else:  # args.intuitive_to_backup or args.intuitive_to_simple:
            intuitive_model_obj = intuitive_grammar_obj.parse_config(source_file.load())
            simple_model = intuitive_model_obj.to_simple()
            if args.intuitive_to_simple:
                dest_file.save(simple_grammar_obj.gen_config(simple_model))
            else:
                backup_model = simple_model.to_backup()
                dest_file.save(backup_grammar_obj.gen_config(backup_model))
    except jg.GrammarException as e:
        print("ERROR\n")
        print(e.args[1])
        exit(1)
    except IntuitiveException as e:
        print("ERROR\n")
        print(e.args[1])
        exit(1)
