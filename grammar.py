import copy
import inspect
import json
import yaml
import re


# JSON/YAML Grammar
#
# There are two kinds of grammars: complete and minimal.
# A complete grammar expects all elements to be present.
# A minimal grammar excludes elements that default, and shortens lists as needed
#
# For the MC6Pro, the backup file is a complete grammar. Requiring all elements ensures that as things change
# we will not miss an item
#
# The simple configuration is equivalent to the backup file, but as a minimal grammar. Only elements needed are
# specified. This is much more human-readable.
#
# The grammar provides three operations: parse, gen and print.
# Parsing creates a "model" in the theoretical computer science sense
# # it is a model of what is intended by the JSON or YAML
# It is like an abstract syntax tree, but more focused on meaning than syntax
# Generating takes a model and creates the JSON/YAML string equivalent.
# Printing prints out the grammar in human-readable form (more or less)
#
# Grammar elements are Dictionaries, Switch Dictionaries, Lists, Enums and Atoms
# Dictionaries and switch dictionaries have keys that map to elements
# For complete grammars, all keys must be present
# For minimal grammars, only non-default keys must be present
# Switch dictionaries have a switch key which must be an enum, and a set of keys for each enum value.
# This allows a choice mechanism
# Switch Dicts have an optional set of "common keys" which are common to all switches
# Lists are fixed length lists, in the minimal grammars, they can be truncated.
# Lists can also be unlimited (length == 0), only for minimal grammars
# Enums are lists of constants, used for color names (for example) or for switch keys in dictionaries
# Atoms are ints, strings, or booleans
#
# All grammar elements have var, model and cleanup bindings (optional)
# A var binding means that when that element is encountered while parsing, it is bound to that variable in the current
# model.
# A model binding means that model (python class) is used for parsing that element and all subelements
# A cleanup binding is a function that runs in the parse, after parsing an element, to clean up as needed
# It is used, for example, in a MIDI message where some of the data is present, but the type is None. It replaces
# the message with None
#
# Atoms also have optional default and value attributes. The default value is what is normally expected, and is left
# out when creating a model (only significant information is in the model, even for complete grammars).
# The value attribute requires a specific value for the atom. This is used for elements not yet covered, so that if
# a configuration file has them, an error is flagged rather than ignoring them.
# defaults and values can also be functions. These functions take 3 arguments: the value being examined, the "context",
# and the list position:
#  The value being examined is the element being parsed, if parsing, and may be a value pulled from a model if genning
# The "context" is the immediately enclosing dictionary or list element
# The list position is a list of integers, representing which position in the list this element occurred in, with the
# innermost being the last in the list
#
# Models are python classes, with variables mapping to values.
# All models must inherit from GrammarModel

class GrammarException(Exception):
    """used for exceptions raised during parsing"""
    pass


class GrammarModel:
    """Base class for models, includes the modified boolean"""
    def __init__(self, name):
        self.modified = False
        self.model_name = name

    def get_var(self, variable):
        model_vars = vars(self)
        if variable not in model_vars:
            raise GrammarException('model_missing_var', 'In ' + name + ' the model ' + self.model_name +
                                   ' is missing the variable ' + variable)
        return model_vars[variable]

    def set_var(self, variable, result, name):
        self.modified = True
        model_vars = vars(self)
        if variable not in model_vars:
            raise GrammarException('model_missing_var', 'In ' + name + ' the model ' + self.model_name +
                                   ' is missing the variable ' + variable)
        if model_vars[variable] is not None:
            raise GrammarException('multiply_assigned_var', 'In ' + name + ' with model ' + self.model_name +
                                   ' the variable ' + variable + ' is assigned multiple times')
        model_vars[variable] = result


# The base class for all grammar modes
class GrammarNode:
    def __init__(self, name, var=None, model=None, cleanup=None):
        self.name = name
        self.variable = var
        self.model = model
        self.cleanup = cleanup

    # Base methods, keeps the child method signatures correct
    def parse(self, grammar, elem, name, context, list_pos, model):
        raise GrammarException("virtual-method", "Attempted virtual method call: GrammarNode.parse")

    def gen(self, grammar, model, context, list_pos):
        raise GrammarException("virtual-method", "Attempted virtual method call: GrammarNode.gen")

    def print(self, indent):
        raise GrammarException("virtual-method", "Attempted virtual method call: GrammarNode.print")


# Base class for Dict and SwitchDict nodes
class DictBase(GrammarNode):
    def __init__(self, name, **kwargs):
        super().__init__(name, **kwargs)

    @staticmethod
    def make_key(key_name, key_schema, required=None):
        return {'name': key_name, 'schema': key_schema, 'required': required}

    @staticmethod
    def lookup_key(key_name, key_list):
        for potential_match in key_list:
            if key_name == potential_match['name']:
                return potential_match['name']
        return False

    @staticmethod
    def check_elem(elem):
        if not isinstance(elem, dict):
            raise GrammarException('type_not_dict', "parse called on non-dict")

    @staticmethod
    def parse_key(grammar, elem, name, list_pos, model, key, found_keys_name, result, seen_keys):
        found_keys = 0
        if key['name'] not in elem:
            # If 'required' is explicit, that takes precedence
            # Otherwise it is set to True for complete, false for minimal grammars
            if key['required'] is None:
                required = not grammar.minimal
            else:
                required = key['required']
            if not required:
                key_result = None
            else:
                raise GrammarException(
                    'dict_bad_keys',
                    "Parse position: " + name + ", error: parse dictionary/switch dictionary expected key: \"" +
                    key['name'] + "\" but didn't find it in " + str(elem.keys()))
        else:
            found_keys = 1
            found_keys_name.append(key['name'])
            # Note we update the context with the elem for sub-parsing
            key_result = grammar.parse(elem[key['name']], key['schema'], name + ':' + key['name'], elem, list_pos,
                                       model)
        if key['name'] in seen_keys:
            raise GrammarException('dict_duplicate_keys', 'grammar has duplicate keys')
        seen_keys[key['name']] = True
        # Only store if significant
        if key_result is not None:
            if result is None:
                msg = ('Paring SwitchDict ' + name + ' the key ' + key['name'] +
                       'returned a result instead of being stored in the switch model')
                raise GrammarException('switch_model_result', msg)
            result[key['name']] = key_result

        return found_keys

    def parse_keys(self, grammar, elem, name, list_pos, model, non_model_keys, model_keys, switch_model, result,
                   seen_keys):
        self.check_elem(elem)

        # The list of keys seen ensures we don't allow keys to appear twice
        # Found keys is the number of keys found in the elem while processing the schema
        # If this is not the total number of keys in the elem, some keys didn't match
        found_keys = len(seen_keys)
        found_keys_name = []
        for key in seen_keys:
            found_keys_name.append(key)

        # process each schema key
        for key in non_model_keys:
            found_keys += self.parse_key(grammar, elem, name, list_pos, model, key, found_keys_name, result, seen_keys)

        for key in model_keys:
            found_keys += self.parse_key(grammar, elem, name, list_pos, switch_model, key, found_keys_name, None,
                                         seen_keys)

        # Make sure all keys in the elem were processed
        if found_keys < len(elem):
            missing_keys = []
            for key in elem:
                if key not in found_keys_name:
                    missing_keys.append(key)
            message = 'While parsing ' + name + ' the following keys are undefined: '
            message += ", ".join(missing_keys)
            valid_keys = []
            for key in non_model_keys:
                valid_keys.append(key['name'])
            for key in model_keys:
                valid_keys.append(key['name'])
            message += "\nThe valid keys are: " + ", ".join(valid_keys)
            raise GrammarException('dict_bad_keys', message)
        if result == {}:
            return None
        return result

    @staticmethod
    def gen_key(grammar, model, model_is_dict, key, list_pos, result, variable_result):
        found_keys = 0
        if model_is_dict:
            # Model is a dictionary, look up the key name to get the submodel
            sub_model = None
            if key['name'] in model:
                sub_model = model[key['name']]
                found_keys = 1
        else:
            sub_model = model
        result[key['name']] = grammar.gen(sub_model, key['schema'], result, list_pos)
        if result[key['name']] is not None:
            variable_result[key['name']] = result[key['name']]
        return found_keys

    # gen the keys of a dict or a switch dict
    # found keys is the number of keys found (0 for dicts, 1 for switch dicts, since we found the switch key)
    # the model is either None, a model object, or a dictionary
    # If none or an object, we pass directly to the sub-gen
    # If a dictionary we get the key out of the model and use that
    # If an atom uses the context function, keys are added to the context in the order they appear in the schema
    @staticmethod
    def gen_keys(grammar, model, keys, model_keys, model_var, list_pos, result, variable_result, found_keys):
        model_is_dict = isinstance(model, dict)
        if model is not None and not isinstance(model, GrammarModel) and not model_is_dict:
            raise GrammarException('type_not_dict', "gen called on non dict")

        # Determine the model for genning sub elements
        # sub_model = model
        for key in keys:
            found_keys += DictBase.gen_key(grammar, model, model_is_dict, key, list_pos, result, variable_result)

        if model_var is not None:
            switched_model = model.get_var(model_var)
            for key in model_keys:
                found_keys += DictBase.gen_key(grammar, switched_model, model_is_dict, key, list_pos, result,
                                               variable_result)

        if model_is_dict and found_keys != len(model.keys()):
            raise GrammarException('dict_bad_keys', "gen_dict has unknown key in model")
        if grammar.minimal:
            if variable_result == {}:
                return None
            else:
                return variable_result
        else:
            return result

    @staticmethod
    def print_key(indent, key, prefix=None):
        result = ' ' * indent
        if prefix is not None:
            result += prefix + ' '
        result += key['name']
        if key['required'] is None:
            result += '(required defaults to grammar)'
        else:
            result += '(required)'
        result += ":\n"
        result += key['schema'].print(indent + 2)
        return result


class Dict(DictBase):
    def __init__(self, name, keys, **kwargs):
        super().__init__(name, **kwargs)
        self.keys = keys

    # parse_dict
    # elem is the dictionary element to be parsed
    # name is the debugging trail
    # list_pos and model as documented above
    #
    # The schema name is added to the debugging trail
    #
    # There are two modes, complete or minimal
    # In complete, all keys must appear to be sub-parsed
    # In minimal, keys need not appear, but we must still make sure that all appearing keys are in the grammar
    def parse(self, grammar, elem, name, context, list_pos, model):
        return super().parse_keys(grammar, elem, name, list_pos, model, self.keys, [], None, {}, {})

    # generate a dictionary element
    # returns significant keys when minimal, or the entire dict when complete
    def gen(self, grammar, model, context, list_pos):
        result = {}
        variable_result = {}
        found_keys = 0

        return super().gen_keys(grammar, model, self.keys, [], None, list_pos, result, variable_result, found_keys)

    def print(self, indent):
        result = ' ' * indent
        result += 'Dict ' + self.name + "\n"
        indent += 2
        for key in self.keys:
            result += self.print_key(indent, key)
        return result


class SwitchDict(DictBase):
    def __init__(self, name, switch_key, case_keys, common_keys=None, model_var=None, **kwargs):
        super().__init__(name, **kwargs)
        self.model_var = model_var
        self.switch_key = switch_key
        self.case_keys = copy.deepcopy(case_keys)
        self.case_models = {}
        self.common_keys = common_keys
        if self.common_keys is None:
            self.common_keys = []
        for case_key in self.case_keys:
            found_pos = None
            for pos in range(len(self.case_keys[case_key])):
                case_sub_key = self.case_keys[case_key][pos]
                if inspect.isclass(case_sub_key):
                    if issubclass(case_sub_key, GrammarModel):
                        if self.model_var is None:
                            msg = ('The SwitchDict ' + name + ' did not specify a model variable, but case key ' +
                                   case_key + ' has a model')
                            raise GrammarException('case_model_without_var', msg)
                        if found_pos is not None:
                            msg = ('The SwitchDict ' + name + ' case key ' + case_key +
                                   ' has multiple case models specified')
                            raise GrammarException('multiple_case_models', msg)
                        found_pos = pos
                        self.case_models[case_key] = case_sub_key
                    else:
                        msg = ('The SwitchDict ' + name + ' case key ' + case_key +
                               'has a class object which is not a model')
                        raise GrammarException('class_not_model', msg)
            if found_pos is None:
                if self.model_var is not None and len(self.case_keys[case_key]) > 0:
                    msg = 'The SwitchDict ' + name + ' case key ' + case_key + ' has no model'
                    raise GrammarException('case_var_without_model', msg)
            else:
                self.case_keys[case_key].pop(found_pos)
        switch_key_name = switch_key['name']
        common_match = self.lookup_key(switch_key_name, self.common_keys)
        if common_match:
            msg = ('The SwitchDict ' + name + ' switch key ' + switch_key_name + ' conflicts with a common key ' +
                   common_match)
            raise GrammarException('switch_key_conflict', msg)
        for case_key_name in self.case_keys:
            case_key_match = self.lookup_key(switch_key_name, self.case_keys[case_key_name])
            if case_key_match:
                msg = ('The SwitchDict ' + name + ' switch key ' + switch_key_name + ' conflicts with a case key ' +
                       case_key_match)
                raise GrammarException('switch_key_conflict', msg)

    # same as parse_dict except
    # we must parse the switch key into a value, even if it is the default
    def parse(self, grammar, elem, name, context, list_pos, model):
        self.check_elem(elem)
        switch_key = self.switch_key
        if switch_key['name'] not in elem:
            if switch_key['schema'].default is None:
                msg = ('While parsing ' + name + ', the switch key ' + switch_key['name'] +
                       ' does not appear in the parsed element.')
                msg += "\nElement keys are " + ', '.join(elem.keys())
                raise GrammarException('missing_switch', msg)
            switch_key_value = switch_key['schema'].default
        else:
            switch_key_value = elem[switch_key['name']]
        # Figure out what the switch value is
        switch_value = switch_key['schema'].parse(grammar, switch_key_value, name, None, [], None)
        if switch_value is None:
            switch_value = switch_key['schema'].default
        if switch_value not in self.case_keys:
            msg = 'The switch element ' + str(switch_value) + ' does not appear in the case keys: '
            msg += ','.join(self.case_keys)
            msg += "\nwhile parsing " + str(elem)
            raise GrammarException('bad_switch', msg)
        case_keys = self.case_keys[switch_value]

        if self.model_var is not None:
            if model is None:
                raise GrammarException('no_base_model', 'While parsing ' + name +
                                       ' the SwitchDict has a switch model but there is no enclosing model.')
            switched_model = None
            if switch_value in self.case_models:
                switched_model = self.case_models[switch_value]()
            model.set_var(self.model_var, switched_model, name)
            all_keys = self.common_keys
            switch_model_keys = case_keys
        else:
            all_keys = self.common_keys + case_keys
            switch_model_keys = []
            switched_model = None

        parse_value = grammar.parse(switch_value, switch_key['schema'], name, None, list_pos, model)
        result = {}
        if parse_value is not None:
            result[switch_key['name']] = parse_value
        seen_keys = {switch_key['name']: True}

        return super().parse_keys(grammar, elem, name, list_pos, model, all_keys, switch_model_keys, switched_model,
                                  result, seen_keys)

    # generate a switch key element
    # returns significant keys when minimal, or the entire dict when complete

    # Get the switch key value.
    #   It may be None, in which case get the default
    # Build the result
    # Note that the result is used as the context too, and this is not thoroughly understood
    # This affects value and default functions which try to access the switch key
    # I don't have any use cases yet
    def gen(self, grammar, model, context, list_pos):
        # Determine what the switch is
        switch_model = model
        if isinstance(model, dict):
            if self.switch_key['name'] in model:
                switch_model = model[self.switch_key['name']]
            else:
                switch_model = None
        switch_value = grammar.gen(switch_model, self.switch_key['schema'], {}, list_pos)

        defaulted_switch_value = switch_value
        if defaulted_switch_value is None:
            defaulted_switch_value = self.switch_key['schema'].default
        if defaulted_switch_value not in self.case_keys:
            msg = 'In node ' + self.name + "\n"
            msg += 'The switch value ' + defaulted_switch_value + " is not in the case keys\n"
            msg += 'Valid case keys are: ' + ', '.join(self.case_keys)
            raise GrammarException('switch_dict_bad_switch', msg)
        if self.model_var is None:
            keys = self.case_keys[defaulted_switch_value] + self.common_keys
            model_keys = []
        else:
            keys = self.common_keys
            model_keys = self.case_keys[defaulted_switch_value]

        result = {}
        variable_result = {}
        if switch_value is not None:
            result = {self.switch_key['name']: switch_value}
            variable_result = {self.switch_key['name']: switch_value}
        found_keys = 1

        return super().gen_keys(grammar, model, keys, model_keys, self.model_var, list_pos, result, variable_result,
                                found_keys)

    def print(self, indent):
        result = ' ' * indent
        result += 'SwitchDict ' + self.name + "\n"
        indent += 2
        result += self.print_key(indent, self.switch_key, prefix='Switch Key:')
        if self.common_keys is not None:
            result += ' ' * indent + 'Common Keys:' + "\n"
            for key in self.common_keys:
                result += self.print_key(indent + 2, key)
        for case_key in self.case_keys:
            result += ' ' * indent + 'Case ' + case_key + ":\n"
            for key in self.case_keys[case_key]:
                result += self.print_key(indent + 2, key)
        return result


class List(GrammarNode):
    def __init__(self, name, length, schema, **kwargs):
        super().__init__(name, **kwargs)
        self.length = length
        self.schema = schema

    # parse_list
    # for complete grammars, the list must be the exact length of the schema
    # for minimal grammars, the list can be shorter
    # If the schema list length is 0, there is no maximum length (only used with minimal grammars)
    # The significant result is a list with all significant values filled in.
    # Note that the list is not compacted, embedded insignificant values are kept with None
    # If the entire list is empty, None is returned
    def parse(self, grammar, elem, name, context, list_pos, model):
        no_max = self.length == 0
        if not isinstance(elem, list):
            raise GrammarException('type_not_list', "parse_list called on non list")
        if not grammar.minimal and no_max:
            raise GrammarException('unlimited_list_complete_grammar', 'length 0 with complete grammar')

        list_length = self.length
        if list_length == 0:
            list_length = len(elem)

        if len(elem) != list_length:
            if not (grammar.minimal and len(elem) < list_length):
                raise GrammarException('list_bad_length', "parse_list called with wrong length list")

        result = [None] * list_length
        modified = False
        for new_list_pos, list_elem in enumerate(elem):
            if list_elem is not None:
                entry_result = grammar.parse(list_elem, self.schema, name, elem, list_pos + [new_list_pos],
                                             model)
                if entry_result is not None:
                    modified = True
                    result[new_list_pos] = entry_result
        if modified:
            if grammar.minimal:
                prune_list(result)
                if len(result) == 0:
                    result = None
            return result
        else:
            return None

    # generate a list from a model
    # For a complete grammar, this is a full length list
    # For a minimal grammar, it is only up to the last non-None element
    # For zero length lists, this is only minimal grammar, and only for list models
    # For zero length lists, and non list models, the current behavior is an empty list. I don't have a use case,
    # so I am not sure that this is correct
    # The model can be None, using only defaults
    # The model can be a model, pass through to sub elements
    # The model can be a list, the list elements are used in sub-parsing
    def gen(self, grammar, model, context, list_pos):
        is_list = isinstance(model, list)
        unlimited = self.length == 0
        if model is not None and not isinstance(model, GrammarModel):
            if not is_list:
                raise GrammarException('model_schema_mismatch', "gen_list got non list")
            if not grammar.minimal and not unlimited and len(model) != self.length:
                raise GrammarException('list_bad_length', "gen_list called with wrong length list")
            if grammar.minimal and not unlimited and len(model) > self.length:
                raise GrammarException('list_bad_length', "gen_list called with wrong length list")

        list_length = self.length
        if list_length == 0 and is_list:
            list_length = len(model)

        result = [None] * list_length
        for new_list_pos in range(0, list_length):
            sub_model = model
            if is_list:
                if new_list_pos >= len(model):
                    sub_model = None
                else:
                    sub_model = model[new_list_pos]
            result[new_list_pos] = grammar.gen(sub_model, self.schema, result, list_pos + [new_list_pos])
        if grammar.minimal:
            prune_list(result)
            if len(result) == 0:
                result = None
        return result

    def print(self, indent):
        result = ' ' * indent
        result += 'List ' + self.name + '(' + str(self.length) + "):\n"
        result += self.schema.print(indent + 2)
        return result


class Enum(GrammarNode):
    def __init__(self, name, base, default=None, **kwargs):
        super().__init__(name, **kwargs)
        self.base = base
        if default is not None:
            try:
                base.index(default)
            except ValueError:
                raise GrammarException('bad_enum_value', "bad enum value")
        self.default = default

    # parse_enum parses an enum element
    # The result is significant if it is not default
    def parse(self, grammar, elem, name, context, list_pos, model):
        if not isinstance(elem, str):
            msg = "In Enum " + name + "\n"
            msg += "Enum expected a string, but received: " + str(elem)
            raise GrammarException('enum_wrong_type', msg)
        # Make sure the elem is valid
        try:
            self.base.index(elem)
        except ValueError:
            msg = 'In Enum ' + name + '\n'
            msg += 'The value ' + elem + 'is not found\n'
            msg += 'Enums are ' + ', '.join(self.base)
            raise GrammarException('bad_enum_value', msg)
        if self.default is not None and elem == self.default:
            return None
        return elem

    # generate an enum
    # This doesn't handle default/value functions
    # I don't have a use case
    def gen(self, grammar, model, context, list_pos):
        enum_value = None
        if self.default is not None:
            enum_value = self.default

        result = None
        variable_result = result
        if model is None or isinstance(model, GrammarModel):
            result = enum_value
        else:
            if model == enum_value:
                result = enum_value
            else:
                variable_result = model
                result = model

        if result is None:
            raise GrammarException('enum_no_default', 'gen_enum resulted in None')

        if grammar.minimal:
            return variable_result
        else:
            return result

    def print(self, indent):
        result = ' ' * indent + 'Enum ' + self.name + ': ['
        if len(self.base) > 2:
            result += self.base[0] + ", " + self.base[1] + ", ...]\n"
        else:
            result += ", ".join(self.base) + "]\n"
        return result


class Atom(GrammarNode):
    def __init__(self, name, atom_type, default=None, value=None, **kwargs):
        super().__init__(name, **kwargs)
        self.type = atom_type
        self.default = default
        self.value = value
        if self.default is not None and self.value is not None:
            raise GrammarException('both_value_default', 'Schema atom has more than 1 value, default set')

    # parse_atom parses a number, string, or boolean
    # It is the same for complete and minimal grammars
    # Significant values differ from the default
    # If the schema is 'value', then the value is required. This is used for portions of the MC6Pro file that are
    # not yet handled - we will throw an error when getting a config where features are used
    def parse(self, grammar, elem, name, context, list_pos, model):
        if not isinstance(elem, self.type):
            message = 'In ' + name + ' expected ' + str(self.type) + ' atom but got ' + str(elem)
            raise GrammarException('atom_wrong_type', message)
        if self.default is not None and self.value is not None:
            raise GrammarException('both_value_default', 'Schema atom has more than 1 value, skip and default')
        target = None
        value = False
        if self.default is not None:
            target = self.default
        if self.value is not None:
            target = self.value
            value = True
        if callable(target):
            target_elem = target(elem, context, list_pos)
        else:
            target_elem = target

        if elem != target_elem:
            if value:
                msg = "parse atom called with " + str(elem) + " not matching schema " + str(target_elem)
                msg += " in " + name
                raise GrammarException('atom_wrong_value', msg)
            result = elem
        else:
            result = None
        return result

    # Generate an atom
    # model is an atom, None, or model object
    # None or model object is ignored, result is the default or value
    # if atom, that is the result
    # for minimal grammars, we need to check if the atom value is default (but not value)
    def gen(self, grammar, model, context, list_pos):
        is_atom = not (model is None or isinstance(model, GrammarModel))
        if isinstance(model, GrammarModel):
            model = None

        atom_value = None
        if self.value is not None:
            atom_value = self.value
        elif self.default is not None:
            atom_value = self.default
        elif not grammar.minimal:
            raise GrammarException('no_value_default', "Missing both value and default in atom")
        if callable(atom_value):
            atom_value = atom_value(model, context, list_pos)

        variable_result = None
        if not is_atom:
            result = atom_value
            # Weird case, but if model is None we want to set the value
            if self.value is not None:
                variable_result = atom_value
        else:
            if model == atom_value:
                result = atom_value
            elif self.value is None:
                variable_result = model
                result = model
            else:
                raise GrammarException('model_schema_mismatch', "atom has wrong value in model and schema")

        if not grammar.minimal and result is None:
            raise GrammarException('programmer_error', 'gen_atom resulted in None')

        if grammar.minimal:
            return variable_result
        else:
            return result

    def print(self, indent):
        result = " " * indent
        result += "Atom " + self.name
        result += '(' + str(self.type.__name__) + '): '
        if self.value is not None:
            result += str(self.value)
        result += "\n"
        return result


# Value/Default atom functions, commonly used
# identity just returns the position in the list, zero based
def identity(_elem, _ctxt, lp):
    return lp[-1]


# returns the 1 based position in the list
def identity_plus_1(_elem, _ctxt, lp):
    return lp[-1] + 1


# returns the position in the enclosing list
def identity2(_elem, _ctxt, lp):
    return lp[-2]


false_atom = Atom('False', bool, value=False)
true_atom = Atom('True', bool, value=True)
zero_atom = Atom('Zero', int, value=0)
empty_atom = Atom('Empty', str, value='')
identity_atom = Atom('I', int, value=identity)
identity2_atom = Atom('I2', int, value=identity2)


# Helper function to remove all None elements from the end of a list
def prune_list(list_to_prune):
    while len(list_to_prune) > 0 and list_to_prune[len(list_to_prune) - 1] is None:
        list_to_prune.pop(len(list_to_prune) - 1)


def compact_list(list_to_compact):
    i = 0
    while i < len(list_to_compact):
        if list_to_compact[i] is None:
            del list_to_compact[i]
        else:
            i += 1


class Grammar:
    def __init__(self, schema, minimal=False):
        self.schema = schema
        self.minimal = minimal

    # Parsing
    # Parson a JSON/YAML subexpression can store the result in 3 ways
    # If a model is specified, all sub-subexpressions are parsed with this model
    # If a variable is specified, the result of the parse is stored in that variable in the current model
    # If neither is specified, the result is returned as the result of the parse
    # Note that if both a model and variable are specified for the same element,
    # the element is parsed with sub-elements using the specified model, and the result is stored in the variable
    # in the passed-in model.
    # At the moment, there is no way to refer to the outer model when parsing the inner model
    #
    # If a node parses to a non-default value AND there is no model/variable associated with it, the parse function
    # returns the non-default value.
    #
    # Only significant values are stored in the model. Lack of a value means it is the default etc.

    # Parsing an element
    # elem is the JSON/YAML element to be parsed
    # schema is the grammar node for the element
    # name is a debugging name indicating where in the grammar we are
    # context is the immediately enclosing dictionary or list object
    # list_pos is the list_pos documented above
    # model is the current model to be used for storing significant changes
    #
    # If a model is specified in the schema, it is used in the subparsing
    # Also, if there is a result that wasn't stored in the model, an error is raised (losing significant info)
    # Finally, the result is the new model object
    #
    # If a variable is specified in the schema for this element, the result is bound in the model (old model)
    def parse(self, elem: object, schema: object, name: object, context: object, list_pos: object,
              model: object) -> object:
        if schema is None:
            raise GrammarException('no_schema', "Schema is None")
        if not isinstance(schema, GrammarNode):
            raise GrammarException('bad_schema', "Schema should be a GrammarNode")

        new_model = False
        # This really belongs inside the 'if' where we create a new model
        # But PyCharm complains then that old_model might be reffed before assignment below
        old_model = model
        if schema.model is not None:
            model = schema.model()
            new_model = True

        if name == "":
            name = schema.name
        else:
            name = name + ":" + schema.name
        result = schema.parse(self, elem, name, context, list_pos, model)

        if new_model:
            if result is not None:
                raise GrammarException('unconsumed', "Model was used, but some result not added")
            if model.modified:
                result = model
            model = old_model

        if schema.cleanup is not None:
            result = schema.cleanup(result, context, list_pos)

        if schema.variable is not None and result is not None:
            model.set_var(schema.variable, result, name)
            result = None
        return result

    # Generate a config JSON/YAML string from a model
    # There are two modes: complete and minimal

    # generate the JSON/YAML for one element
    # The model can be a value, a schema, or a model object
    # The context is the enclosing dictionary
    # The list_pos is the same as parse
    # If there is a variable, look up the value associated with that variable in the current model and use that for
    # the sub model.
    # Otherwise, if there is a model in the schema, and the passed in model isn't the right type, the sub model is None
    # This happens when a model is defaulted/None
    # Finally if neither of the above two cases are true, the sub model is the model
    def gen(self, model, schema, context, list_pos):
        if schema is None:
            raise GrammarException('no_schema', "Schema is None")

        # If the schema specifies a model, and if the current model is not an instance of this
        # then we need to not use the current model
        # TODO: CHeck this out. If a switchdict is genned against a string (model is the string)
        # TODO: the string is replaced by None. This makes it impossible for the switchdict
        # TODO: gen code to detect an error
        if schema.model is not None and not isinstance(model, schema.model):
            sub_model = None
        else:
            sub_model = model

        if schema.variable is not None:
            # If model is None, that means the model was not populated, everything is default
            if model is not None:
                if not isinstance(model, GrammarModel):
                    raise GrammarException('variable_without_model',
                                           "In gen_elem, have a variable that isn't a model")
                model_vars = vars(model)
                if schema.variable not in model_vars.keys():
                    raise GrammarException('variable_not_in_model',
                                           'The variable ' + schema.variable + ' is not in the model ' +
                                           model.model_name)
                sub_model = model_vars[schema.variable]

        result = schema.gen(self, sub_model, context, list_pos)
        return result

    def print(self, indent=0):
        return self.schema.print(indent)

    def parse_config(self, elem):
        return self.parse(elem, self.schema, "", None, [], None)

    def gen_config(self, model):
        return self.gen(model, self.schema, None, [])


class GrammarFile:
    def __init__(self, filename=None, is_yaml=None):
        if filename is None:
            if is_yaml is None:
                raise GrammarException('must specify filename or is_yaml')
            self.is_yaml = is_yaml
            self.filename = None
        else:
            self.filename = filename
            if re.search(r'\.yaml$', filename):
                self.is_yaml = True
            elif re.search(r'\.json$', filename):
                self.is_yaml = False
            else:
                raise GrammarException('File is not json or yaml: ' + filename)

    def save(self, data):
        if self.filename is not None:
            with open(self.filename, "w") as write_file:
                if self.is_yaml:
                    yaml.dump(data, write_file)
                else:
                    json.dump(data, write_file, indent=4)
        else:
            raise GrammarException('Not implemented')

    def load(self):
        if self.filename is not None:
            with open(self.filename, "r") as read_file:
                if self.is_yaml:
                    result = yaml.safe_load(read_file)
                else:
                    result = json.load(read_file)
        else:
            raise GrammarException('Not implemented')
        if result is None:
            result = {}
        return result
