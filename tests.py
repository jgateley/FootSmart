import unittest

import MC6Pro_grammar
import MC6Pro_intuitive
import json_grammar as jg
from IntuitiveException import IntuitiveException
import intuitive_message as im
import intuitive_midi_channel


# Model object used for testing
class ObjectForTests(jg.JsonGrammarModel):
    def __init__(self):
        super().__init__('ObjectForTests')
        self.x = None

    def __eq__(self, other):
        return self.x == other.x and self.modified == other.modified


# A second model object used for testing
class Object2ForTests(jg.JsonGrammarModel):
    def __init__(self):
        super().__init__('Object2ForTests')
        self.y = None

    def __eq__(self, other):
        return self.y == other.y and self.modified == other.modified


# Switch Models
class SwitchBaseModel(jg.JsonGrammarModel):
    def __init__(self):
        super().__init__('SwitchBaseModel')
        self.switch_key = None
        self.switched_model = None
        self.x = None
        self.y = None

    def __eq__(self, other):
        return (self.switch_key == other.switch_key and self.switched_model == other.switched_model and
                self.x == other.x and self.y == other.y)


class SwitchAModel(jg.JsonGrammarModel):
    def __init__(self):
        super().__init__('SwitchAModel')
        self.a1 = None
        self.a2 = None

    def __eq__(self, other):
        return self.a1 == other.a1 and self.a2 == other.a2


class SwitchBModel(jg.JsonGrammarModel):
    def __init__(self):
        super().__init__('SwitchBModel')
        self.b1 = None
        self.b2 = None

    def __eq__(self, other):
        return self.b1 == other.b1 and self.b2 == other.b2


class SwitchCModel(jg.JsonGrammarModel):
    def __init__(self):
        super().__init__('SwitchCModel')
        self.c1 = None
        self.c2 = None

    def __eq__(self, other):
        return self.c1 == other.c1 and self.c2 == other.c2


complete_conf = jg.JsonGrammar(None)
minimal_conf = jg.JsonGrammar(None, True)


# Helper function
def make_common_switch():
    switch_enum = jg.Enum('enum', ['a', 'b'], default='a')
    switch_key = jg.SwitchDict.make_key('switch', switch_enum)
    a_keys = [jg.SwitchDict.make_key('a1', jg.Atom('atom', int, 1)),
              jg.SwitchDict.make_key('a2', jg.Atom('atom', int, 2))]
    b_keys = [jg.SwitchDict.make_key('b1', jg.Atom('atom', int, 1)),
              jg.SwitchDict.make_key('b2', jg.Atom('atom', int, 2))]
    common_keys = [jg.SwitchDict.make_key('c1', jg.Atom('atom', int, 1)),
                   jg.SwitchDict.make_key('c2', jg.Atom('atom', int, 2))]
    test_switch = jg.SwitchDict('test', switch_key,
                                {'a': a_keys, 'b': b_keys}, common_keys)
    return test_switch


# Test the list pruning, compacting
# Pruning should only remove empty elements at the end, not the middle
class ListTestCases(unittest.TestCase):
    # Test:
    # Empty list
    # List with all specified
    # List with some Nones at end
    # List with some Nones at end, and in middle
    def test_prune_list(self):
        test_list = []
        jg.prune_list(test_list)
        self.assertEqual([], test_list)

        test_list = [1, 2, 3]
        jg.prune_list(test_list)
        self.assertEqual([1, 2, 3], test_list)

        test_list = [1, 2, 3, None, None]
        jg.prune_list(test_list)
        self.assertEqual([1, 2, 3], test_list)

        test_list = [1, 2, None, 3, None, None]
        jg.prune_list(test_list)
        self.assertEqual([1, 2, None, 3], test_list)

    def test_compact_list(self):
        test_list = []
        jg.compact_list(test_list)
        self.assertEqual([], test_list)

        test_list = [1, 2, 3]
        jg.compact_list(test_list)
        self.assertEqual([1, 2, 3], test_list)

        test_list = [None, 1, 2, 3]
        jg.compact_list(test_list)
        self.assertEqual([1, 2, 3], test_list)

        test_list = [None, None, 1, 2, 3]
        jg.compact_list(test_list)
        self.assertEqual([1, 2, 3], test_list)

        test_list = [1, None, 2, 3]
        jg.compact_list(test_list)
        self.assertEqual([1, 2, 3], test_list)

        test_list = [1, None, 2, None, 3]
        jg.compact_list(test_list)
        self.assertEqual([1, 2, 3], test_list)

        test_list = [1, None, None, 2, 3]
        jg.compact_list(test_list)
        self.assertEqual([1, 2, 3], test_list)

        test_list = [1, 2, 3, None]
        jg.compact_list(test_list)
        self.assertEqual([1, 2, 3], test_list)

        test_list = [None, 1, None, None, 2, None, 3, None, None, None]
        jg.compact_list(test_list)
        self.assertEqual([1, 2, 3], test_list)


class ModelTestCases(unittest.TestCase):
    def test_set_get(self):
        obj = ObjectForTests()
        self.assertFalse(obj.modified)
        self.assertEqual(obj.name, 'ObjectForTests')
        self.assertIsNone(obj.x)
        obj.set_var('x', 2, 'error message')
        self.assertTrue(obj.modified)
        self.assertEqual(obj.x, 2)
        self.assertEqual(obj.get_var('x'), 2)


# Test the structure of the various grammar elements
# These are brittle, not the best
class JsonGrammarElementStructureTestCase(unittest.TestCase):
    def validate_keywords(self, node, var, model, cleanup):
        if var is None:
            self.assertIsNone(node.variable)
        else:
            self.assertEqual(var, node.variable)
        if model is None:
            self.assertIsNone(node.model)
        else:
            self.assertEqual(model, node.model)
        if cleanup is None:
            self.assertIsNone(node.cleanup)
        else:
            self.assertEqual(cleanup, node.cleanup)

    def validate_dict(self, node, name, keys, var, model, cleanup):
        self.assertEqual(name, node.name)
        self.assertEqual(keys, node.keys)
        self.validate_keywords(node, var, model, cleanup)

    # Test dict structure, include variable, model and both and none
    def test_dict(self):
        self.validate_dict(jg.Dict('foo', [1, 2, 3]),
                           'foo', [1, 2, 3], None, None, None)
        self.validate_dict(jg.Dict('foo', [1, 2, 3], var='x'),
                           'foo', [1, 2, 3], 'x', None, None)
        self.validate_dict(jg.Dict('foo', [1, 2, 3], model=ObjectForTests),
                           'foo', [1, 2, 3], None, ObjectForTests, None)
        self.validate_dict(jg.Dict('foo', [1, 2, 3], cleanup=3),
                           'foo', [1, 2, 3], None, None, 3)
        self.validate_dict(jg.Dict('foo', [1, 2, 3], var='x', model=ObjectForTests, cleanup=3),
                           'foo', [1, 2, 3], 'x', ObjectForTests, 3)

    # Test the switch dictionary, with none, var, model, and both
    def validate_switch_dict(self, node, name, switch_key, case_keys, common_keys, var, model, cleanup):
        self.assertEqual(name, node.name)
        self.assertEqual(switch_key, node.switch_key)
        self.assertEqual(case_keys, node.case_keys)
        self.assertEqual(common_keys, node.common_keys)
        self.validate_keywords(node, var, model, cleanup)

    def test_switch_dict(self):
        switch_key = jg.SwitchDict.make_key('x', jg.Enum('enum', ['a', 'b'], 'a'))
        case_keys = {'a': []}
        self.validate_switch_dict(jg.SwitchDict('foo', switch_key, case_keys),
                                  'foo', switch_key, case_keys, [], None, None, None)
        self.validate_switch_dict(jg.SwitchDict('foo', switch_key, case_keys, var='x'),
                                  'foo', switch_key, case_keys, [], 'x', None, None)
        self.validate_switch_dict(jg.SwitchDict('foo', switch_key, case_keys, model=ObjectForTests),
                                  'foo', switch_key, case_keys, [], None, ObjectForTests, None)
        self.validate_switch_dict(jg.SwitchDict('foo', switch_key, case_keys, var='x', model=ObjectForTests),
                                  'foo', switch_key, case_keys, [], 'x', ObjectForTests, None)
        self.validate_switch_dict(jg.SwitchDict('foo', switch_key, case_keys, var='x', model=ObjectForTests, cleanup=3),
                                  'foo', switch_key, case_keys, [], 'x', ObjectForTests, 3)

    def test_switch_dict_switch_key_conflict(self):
        test_switch_enum = jg.Enum('enum', ['a', 'b'], 'a')
        test_switch_key = jg.SwitchDict.make_key('x', test_switch_enum)
        test_case_keys = {'a': [jg.SwitchDict.make_key('x', jg.Atom('atom', int, 1)),
                                jg.SwitchDict.make_key('y', jg.Atom('atom', int, 2))],
                          'b': [ListTestCases, jg.SwitchDict.make_key('b1', jg.Atom('atom', int, 1)),
                                jg.SwitchDict.make_key('b2', jg.Atom('atom', int, 2)),
                                jg.SwitchDict.make_key('b3', jg.Atom('atom', int, 3))]}
        with self.assertRaises(jg.JsonGrammarException) as context:
            jg.SwitchDict('test', test_switch_key, test_case_keys)
        self.assertEqual('class_not_model', context.exception.args[0])

    def test_switch_dict_switch_model(self):
        test_switch_enum = jg.Enum('enum', ['a', 'b', 'c'], 'a')
        test_switch_key = jg.SwitchDict.make_key('x', test_switch_enum)
        test_case_keys = {'a': [jg.SwitchDict.make_key('a1', jg.Atom('atom', int, 1)),
                                jg.SwitchDict.make_key('a2', jg.Atom('atom', int, 2)),
                                jg.SwitchDict.make_key('a3', jg.Atom('atom', int, 3))],
                          'b': [ListTestCases, jg.SwitchDict.make_key('b1', jg.Atom('atom', int, 1)),
                                jg.SwitchDict.make_key('b2', jg.Atom('atom', int, 2)),
                                jg.SwitchDict.make_key('b3', jg.Atom('atom', int, 3))],
                          'c': [jg.SwitchDict.make_key('c1', jg.Atom('atom', int, 1)),
                                jg.SwitchDict.make_key('c2', jg.Atom('atom', int, 2)),
                                jg.SwitchDict.make_key('c3', jg.Atom('atom', int, 3))]}
        with self.assertRaises(jg.JsonGrammarException) as context:
            jg.SwitchDict('test', test_switch_key, test_case_keys)
        self.assertEqual('class_not_model', context.exception.args[0])
        test_case_keys = {'a': [jg.SwitchDict.make_key('a1', jg.Atom('atom', int, 1)),
                                jg.SwitchDict.make_key('a2', jg.Atom('atom', int, 2)),
                                jg.SwitchDict.make_key('a3', jg.Atom('atom', int, 3))],
                          'b': [SwitchBModel, jg.SwitchDict.make_key('b1', jg.Atom('atom', int, 1)),
                                jg.SwitchDict.make_key('b2', jg.Atom('atom', int, 2)),
                                jg.SwitchDict.make_key('b3', jg.Atom('atom', int, 3))],
                          'c': [jg.SwitchDict.make_key('c1', jg.Atom('atom', int, 1)),
                                jg.SwitchDict.make_key('c2', jg.Atom('atom', int, 2)),
                                jg.SwitchDict.make_key('c3', jg.Atom('atom', int, 3))]}
        with self.assertRaises(jg.JsonGrammarException) as context:
            jg.SwitchDict('test', test_switch_key, test_case_keys)
        self.assertEqual('case_model_without_var', context.exception.args[0])
        test_case_keys = {'a': [SwitchAModel, jg.SwitchDict.make_key('a1', jg.Atom('atom', int, 1)),
                                jg.SwitchDict.make_key('a2', jg.Atom('atom', int, 2)),
                                jg.SwitchDict.make_key('a3', jg.Atom('atom', int, 3))],
                          'b': [SwitchBModel, jg.SwitchDict.make_key('b1', jg.Atom('atom', int, 1)),
                                SwitchAModel, jg.SwitchDict.make_key('b2', jg.Atom('atom', int, 2)),
                                jg.SwitchDict.make_key('b3', jg.Atom('atom', int, 3))],
                          'c': [SwitchCModel, jg.SwitchDict.make_key('c1', jg.Atom('atom', int, 1)),
                                jg.SwitchDict.make_key('c2', jg.Atom('atom', int, 2)),
                                jg.SwitchDict.make_key('c3', jg.Atom('atom', int, 3))]}
        with self.assertRaises(jg.JsonGrammarException) as context:
            jg.SwitchDict('test', test_switch_key, test_case_keys, model_var='x')
        self.assertEqual('multiple_case_models', context.exception.args[0])
        test_case_keys = {'a': [jg.SwitchDict.make_key('a1', jg.Atom('atom', int, 1)),
                                jg.SwitchDict.make_key('a2', jg.Atom('atom', int, 2)),
                                jg.SwitchDict.make_key('a3', jg.Atom('atom', int, 3))],
                          'b': [jg.SwitchDict.make_key('b1', jg.Atom('atom', int, 1)),
                                jg.SwitchDict.make_key('b2', jg.Atom('atom', int, 2)),
                                jg.SwitchDict.make_key('b3', jg.Atom('atom', int, 3))],
                          'c': [jg.SwitchDict.make_key('c1', jg.Atom('atom', int, 1)),
                                jg.SwitchDict.make_key('c2', jg.Atom('atom', int, 2)),
                                jg.SwitchDict.make_key('c3', jg.Atom('atom', int, 3))]}
        with self.assertRaises(jg.JsonGrammarException) as context:
            jg.SwitchDict('test', test_switch_key, test_case_keys, model_var='x')
        self.assertEqual('case_var_without_model', context.exception.args[0])
        test_case_keys = {'a': [SwitchAModel, jg.SwitchDict.make_key('a1', jg.Atom('atom', int, 1)),
                                jg.SwitchDict.make_key('a2', jg.Atom('atom', int, 2)),
                                jg.SwitchDict.make_key('a3', jg.Atom('atom', int, 3))],
                          'b': [SwitchBModel, jg.SwitchDict.make_key('b1', jg.Atom('atom', int, 1)),
                                jg.SwitchDict.make_key('b2', jg.Atom('atom', int, 2)),
                                jg.SwitchDict.make_key('b3', jg.Atom('atom', int, 3))],
                          'c': [SwitchCModel, jg.SwitchDict.make_key('c1', jg.Atom('atom', int, 1)),
                                jg.SwitchDict.make_key('c2', jg.Atom('atom', int, 2)),
                                jg.SwitchDict.make_key('c3', jg.Atom('atom', int, 3))]}
        self.assertIsNotNone(jg.SwitchDict('test', test_switch_key, test_case_keys, model_var='x'))

    def validate_list(self, node, length, schema, var, model, cleanup):
        self.assertEqual(length, node.length)
        self.assertEqual(schema, node.schema)
        self.validate_keywords(node, var, model, cleanup)

    # Test a list, with none, var, model and both
    def test_list(self):
        schema = jg.Atom('atom', int, value=1)
        self.validate_list(jg.List('list', 3, schema), 3, schema, None, None, None)
        self.validate_list(jg.List('list', 3, schema, var='x'), 3, schema, 'x', None, None)
        self.validate_list(jg.List('list', 3, schema, model=ObjectForTests),
                           3, schema, None, ObjectForTests, None)
        self.validate_list(jg.List('list', 3, schema, var='x', model=ObjectForTests),
                           3, schema, 'x', ObjectForTests, None)
        self.validate_list(jg.List('list', 3, schema, var='x', model=ObjectForTests, cleanup=3),
                           3, schema, 'x', ObjectForTests, 3)

    # Test an enum element where a default is not a member of the enum
    def test_enum(self):
        enum_base = ["one", "two", "three"]
        # Test default with incorrect value
        with self.assertRaises(jg.JsonGrammarException) as context:
            jg.Enum('enum', enum_base, "four")
        self.assertEqual('bad_enum_value', context.exception.args[0])

    # Test atom structure
    # Test that default and value both specified is an error
    def test_atom(self):
        with self.assertRaises(jg.JsonGrammarException) as context:
            jg.Atom('atom', int, 1, value=2)
        self.assertEqual(context.exception.args[0], 'both_value_default')


class JsonGrammarBaseTestCase(unittest.TestCase):
    def check_target(self, result, target):
        if target is None:
            self.assertIsNone(result)
        else:
            self.assertEqual(target, result)

    def run_grammar_parse(self, node, elem, complete_target, minimal_target):
        result = complete_conf.parse(elem, node, "foo", None, [], None)
        self.check_target(result, complete_target)
        result = minimal_conf.parse(elem, node, "foo", None, [], None)
        self.check_target(result, minimal_target)

    def run_grammar_parse_model(self, node, elem, complete_target, minimal_target, var_result):
        test_model = ObjectForTests()
        result = complete_conf.parse(elem, node, 'foo', None, [], test_model)
        self.check_target(result, complete_target)
        self.check_target(test_model.x, var_result)
        test_model = ObjectForTests()
        result = minimal_conf.parse(elem, node, 'foo', None, [], test_model)
        self.check_target(result, minimal_target)
        self.check_target(test_model.x, var_result)

    def run_grammar_parse_error(self, schema, elem, code):
        with self.assertRaises(jg.JsonGrammarException) as context:
            complete_conf.parse(elem, schema, "foo", None, [], None)
        self.assertEqual(code, context.exception.args[0])
        with self.assertRaises(jg.JsonGrammarException) as context:
            minimal_conf.parse(elem, schema, "foo", None, [], None)
        self.assertEqual(code, context.exception.args[0])

    def run_grammar_gen(self, node, elem, complete_target, minimal_target):
        result = complete_conf.gen(elem, node, None, [])
        self.check_target(result, complete_target)
        result = minimal_conf.gen(elem, node, None, [])
        self.check_target(result, minimal_target)

    def run_grammar_gen_error(self, schema, elem, code):
        with self.assertRaises(jg.JsonGrammarException) as context:
            complete_conf.gen(elem, schema, None, [])
        self.assertEqual(code, context.exception.args[0])
        with self.assertRaises(jg.JsonGrammarException) as context:
            minimal_conf.gen(elem, schema, None, [])
        self.assertEqual(code, context.exception.args[0])

    def run_node_parse(self, node, elem, complete_target, minimal_target):
        result = node.parse(complete_conf, elem, "foo", None, [], None)
        self.check_target(result, complete_target)
        result = node.parse(minimal_conf, elem, "foo", None, [], None)
        self.check_target(result, minimal_target)

    def run_node_parse_model(self, node, elem, complete_target, minimal_target, var_result):
        test_model = ObjectForTests()
        result = node.parse(complete_conf, elem, "foo", None, [], test_model)
        self.check_target(result, complete_target)
        self.assertEqual(var_result, test_model.x)
        test_model = ObjectForTests()
        result = node.parse(minimal_conf, elem, "foo", None, [], test_model)
        self.check_target(result, minimal_target)
        self.assertEqual(var_result, test_model.x)

    def run_node_parse_error(self, node, elem, code):
        with self.assertRaises(jg.JsonGrammarException) as context:
            node.parse(complete_conf, elem, "foo", None, [], None)
        self.assertEqual(code, context.exception.args[0])
        with self.assertRaises(jg.JsonGrammarException) as context:
            node.parse(minimal_conf, elem, "foo", None, [], None)
        self.assertEqual(code, context.exception.args[0])

    def run_node_parse_complete_error(self, node, elem, code, target):
        with self.assertRaises(jg.JsonGrammarException) as context:
            node.parse(complete_conf, elem, "foo", None, [], None)
        self.assertEqual(code, context.exception.args[0])
        result = node.parse(minimal_conf, elem, "foo", None, [], None)
        self.check_target(result, target)

    def run_node_gen(self, node, elem, complete_target, minimal_target, list_pos=None):
        if list_pos is None:
            list_pos = []
        result = node.gen(complete_conf, elem, None, list_pos)
        self.check_target(result, complete_target)
        result = node.gen(minimal_conf, elem, None, list_pos)
        self.check_target(result, minimal_target)

    def run_node_gen_error(self, node, elem, code, exception=jg.JsonGrammarException):
        with self.assertRaises(exception) as context:
            node.gen(complete_conf, elem, None, [])
        self.assertEqual(code, context.exception.args[0])
        with self.assertRaises(exception) as context:
            node.gen(minimal_conf, elem, None, [])
        self.assertEqual(code, context.exception.args[0])


class JsonGrammarParserTestCase(JsonGrammarBaseTestCase):

    def setUp(self):
        self.var_schema = jg.Atom('atom', int, 1, var='x')
        self.model_schema = jg.Dict('foo',
                                    [jg.Dict.make_key("a", self.var_schema),
                                     jg.Dict.make_key("b", jg.Atom('atom', int, 1))],
                                    model=ObjectForTests)

    def test_parse_errors(self):
        # Test schema is none
        self.run_grammar_parse_error(None, 1, 'no_schema')

    def test_simple_var_cases(self):
        # Test var in schema, not modified
        self.run_grammar_parse_model(self.var_schema, 1, None, None, None)

        # Test var in schema, modified
        self.run_grammar_parse_model(self.var_schema, 2, None, None, 2)

    def test_simple_model_cases(self):
        # Test model in schema, not modified
        self.run_grammar_parse(self.model_schema, {'a': 1, 'b': 1}, None, None)

        # Test model in schema, modified
        target = ObjectForTests()
        target.x = 2
        target.modified = True
        self.run_grammar_parse(self.model_schema, {'a': 2, 'b': 1}, target, target)

        # Test model in schema, modified, but some result not added to model
        self.run_grammar_parse_error(self.model_schema, {'a': 2, 'b': 2},  'unconsumed')

    # Testing an element, primarily testing vars and models
    def test_model_var_cases(self):
        # Both model and variable in schema
        inner_schema = jg.Dict('inner',
                               [jg.Dict.make_key('x', jg.Atom('atom', int, 1, var='x'))],
                               var='y', model=ObjectForTests)
        outer_schema = jg.Dict('outer',
                               [jg.Dict.make_key('y', inner_schema)], model=Object2ForTests)

        # Test model not modified
        self.run_grammar_parse(outer_schema, {'y': {'x': 1}}, None, None)
        self.assertIsNone(complete_conf.parse({'y': {'x': 1}}, outer_schema, 'outer',
                                              None, [], None))

        # Test model modified
        target = Object2ForTests()
        target.modified = True
        target.y = ObjectForTests()
        target.y.modified = True
        target.y.x = 2
        self.run_grammar_parse(outer_schema, {'y': {'x': 2}}, target, target)

    # Test that a var appearing as a list elem raises a multiply assigned error
    def test_var_in_list(self):
        list_schema = jg.List('list', 3, jg.Atom('atom', int, 1, var='x'), model=ObjectForTests)
        self.run_grammar_parse_error(list_schema, [1, 2, 3], 'multiply_assigned_var')


class JsonGrammarGenTestCase(JsonGrammarBaseTestCase):
    def test_elem(self):
        # Test schema is None
        self.run_grammar_gen_error(None, 1, 'no_schema')

        # Test dictionary
        test_schema = jg.Dict('foo',
                              [jg.Dict.make_key('a', jg.Atom('atom', int, value=1)),
                               jg.Dict.make_key('b', jg.Atom('atom', int, value=2)),
                               jg.Dict.make_key('c', jg.Atom('atom', int, value=3))])
        self.run_grammar_gen(test_schema, {'a': 1, 'b': 2, 'c': 3}, {'a': 1, 'b': 2, 'c': 3}, None)

        # Test list
        test_schema = jg.List('list', 3, jg.Atom('atom', int, value=1))
        self.run_grammar_gen(test_schema, None, [1, 1, 1], [1, 1, 1])

        # Test atom
        test_schema = jg.Atom('atom', int, value=1)
        self.run_grammar_gen(test_schema, 1, 1, None)

        # Test variable expansion
        test_model = ObjectForTests()
        test_model.x = 3
        test_schema = jg.Atom('atom', int, 1, var='x')
        self.run_grammar_gen(test_schema, test_model, 3, 3)


class JsonGrammarDictNodeParseTestCase(JsonGrammarBaseTestCase):

    # Test parsing dictionaries, error cases
    # Both complete and minimal
    def test_parse_dict_errors(self):
        test_dict = jg.Dict('foo', [])

        # Dictionary isn't a dict
        self.run_node_parse_error(test_dict, 1, 'type_not_dict')

        # Key errors
        # elem has too many keys
        test_schema = jg.Dict('foo', [jg.Dict.make_key('a', jg.Atom('atom', int, 1))])
        self.run_node_parse_error(test_schema, {'a': 1, 'b': 2}, 'dict_bad_keys')
        # elem has too few keys, and some are misnamed
        test_schema = jg.Dict('foo', [jg.Dict.make_key('b', jg.Atom('atom', int, 1)),
                                      jg.Dict.make_key('c', jg.Atom('atom', int, 2))])
        self.run_node_parse_error(test_schema, {'a': 1}, 'dict_bad_keys')
        # elem has too few keys, all correct, complete => error, minimal => parse
        test_schema = jg.Dict('foo',
                              [jg.Dict.make_key('a', jg.Atom('atom', int, 1)),
                               jg.Dict.make_key('b', jg.Atom('atom', int, 2)),
                               jg.Dict.make_key('c', jg.Atom('atom', int, 3))])
        self.run_node_parse_complete_error(test_schema, {'a': 1, 'b': 2}, 'dict_bad_keys', None)
        self.run_node_parse_complete_error(test_schema, {'a': 2}, 'dict_bad_keys', {'a': 2})
        self.run_node_parse_complete_error(test_schema, {'b': 1}, 'dict_bad_keys', {'b': 1})
        self.run_node_parse_complete_error(test_schema, {'a': 2, 'b': 1}, 'dict_bad_keys', {'a': 2, 'b': 1})
        # elem has the right number of keys, but some are named wrong
        test_schema = jg.Dict('foo', [jg.Dict.make_key('b', None)])
        self.run_node_parse_error(test_schema, {'a': 1}, 'dict_bad_keys')
        # Key appears twice in dict/schema (grammar specified incorrectly)
        test_schema = jg.Dict('foo', [jg.Dict.make_key('a', jg.Atom('atom', int, value=0)),
                                      jg.Dict.make_key('a', jg.Atom('atom', int, value=0))])
        self.run_node_parse_error(test_schema, {'a': 0, 'b': 0}, 'dict_duplicate_keys')

    # Test parsing dictionaries
    # Both complete and minimal
    def test_parse_dict(self):
        # Has right number of keys and subparsing
        test_schema = jg.Dict('foo',
                              [jg.Dict.make_key('a', jg.Atom('atom', int, 1)),
                               jg.Dict.make_key('b', jg.Atom('atom', int, 2))])
        self.run_node_parse(test_schema, {'a': 1, 'b': 2}, None, None)
        self.run_node_parse(test_schema, {'a': 2, 'b': 2}, {'a': 2}, {'a': 2})
        self.run_node_parse(test_schema, {'a': 1, 'b': 1}, {'b': 1}, {'b': 1})
        self.run_node_parse(test_schema, {'a': 2, 'b': 1}, {'a': 2, 'b': 1}, {'a': 2, 'b': 1})

    # Test parsing dictionaries context
    # Both complete and minimal
    def test_parse_dict_context(self):
        # Test that matching values work
        test_schema = jg.Dict('foo',
                              [jg.Dict.make_key('a', jg.Atom('atom', int, value=1)),
                               jg.Dict.make_key('b', jg.Atom('atom', int, value=lambda elem, ctxt, lp: ctxt['a']))])
        self.run_node_parse(test_schema, {'a': 1, 'b': 1}, None, None)

        # Test values not matching work
        self.run_node_parse_error(test_schema, {'a': 1, 'b': 2}, 'atom_wrong_value')

        # Test value works against defaults
        test_schema = jg.Dict('foo',
                              [jg.Dict.make_key('a', jg.Atom('atom', int, 1)),
                               jg.Dict.make_key('b', jg.Atom('atom', int, value=lambda elem, ctxt, lp: ctxt['a']))])
        self.run_node_parse(test_schema, {'a': 2, 'b': 2}, {'a': 2}, {'a': 2})
        self.run_node_parse_error(test_schema, {'a': 2, 'b': 3}, 'atom_wrong_value')

        # Test defaults work
        test_schema = jg.Dict('foo',
                              [jg.Dict.make_key('a', jg.Atom('atom', int, 1)),
                               jg.Dict.make_key('b', jg.Atom('atom', int, lambda elem, ctxt, lp: ctxt['a']))])
        self.run_node_parse(test_schema, {'a': 1, 'b': 1}, None, None)
        self.run_node_parse(test_schema, {'a': 1, 'b': 2}, {'b': 2}, {'b': 2})
        self.run_node_parse(test_schema, {'a': 2, 'b': 2}, {'a': 2}, {'a': 2})
        self.run_node_parse(test_schema, {'a': 2, 'b': 1}, {'a': 2, 'b': 1}, {'a': 2, 'b': 1})

    def test_dict_required_key(self):
        test_schema = jg.Dict('foo',
                              [jg.Dict.make_key('a', jg.Atom('atom', int, 1), required=True)])
        self.run_node_parse_error(test_schema, {}, 'dict_bad_keys')


class JsonGrammarSwitchDictNodeParseTestCase(JsonGrammarBaseTestCase):
    def __init__(self, *args, **kwargs):
        super(JsonGrammarSwitchDictNodeParseTestCase, self).__init__(*args, **kwargs)
        self.test_switch_enum = jg.Enum('enum', ['a', 'b', 'c'], 'a')
        self.test_switch_key = jg.SwitchDict.make_key('x', self.test_switch_enum)
        self.test_case_keys = {'a': [jg.SwitchDict.make_key('a1', jg.Atom('atom', int, 1)),
                                     jg.SwitchDict.make_key('a2', jg.Atom('atom', int, 2)),
                                     jg.SwitchDict.make_key('a3', jg.Atom('atom', int, 3))],
                               'b': [jg.SwitchDict.make_key('b1', jg.Atom('atom', int, 1)),
                                     jg.SwitchDict.make_key('b2', jg.Atom('atom', int, 2)),
                                     jg.SwitchDict.make_key('b3', jg.Atom('atom', int, 3))],
                               'c': [jg.SwitchDict.make_key('c1', jg.Atom('atom', int, 1)),
                                     jg.SwitchDict.make_key('c2', jg.Atom('atom', int, 2)),
                                     jg.SwitchDict.make_key('c3', jg.Atom('atom', int, 3))]}
        self.test_switch = jg.SwitchDict('test', self.test_switch_key, self.test_case_keys)

    # Test parsing dictionaries, error cases
    # Both complete and minimal
    def test_parse_switch_dict_errors(self):
        # Dictionary isn't a dict
        self.run_node_parse_error(self.test_switch, 1, 'type_not_dict')
        # Is a dictionary, but missing switch key
        self.run_node_parse_error(self.test_switch, {'a': 1}, 'missing_switch')
        # Dictionary is a dict, switch matches, but has wrong number of keys
        # Too few keys, all correct
        self.run_node_parse_complete_error(self.test_switch, {'x': 'a', 'a1': 1, 'a2': 2}, 'dict_bad_keys', None)
        #   Too few keys, some incorrect
        self.run_node_parse_error(self.test_switch, {'x': 'a', 'a1': 1, 'a4': 2}, 'dict_bad_keys')
        #   Too many keys, some incorrect
        self.run_node_parse_error(self.test_switch, {'x': 'a', 'a1': 1, 'a2': 2, 'a3': 3, 'a4': 4}, 'dict_bad_keys')
        # switch matches Has right number of keys, but name is wrong
        self.run_node_parse_error(self.test_switch, {'x': 'a', 'a1': 1, 'a2': 2, 'a4': 3}, 'dict_bad_keys')

        # Need to test when grammar is specified incorrectly, and a key appears twice in schema
        switch_key = jg.SwitchDict.make_key('x', jg.Enum('Enum', ['a', 'b'], None))
        case_keys = {'a': [jg.SwitchDict.make_key('x', jg.Atom('atom', str, 'z'))],
                     'b': [jg.SwitchDict.make_key('b1', jg.Atom('atom', int))]}
        with self.assertRaises(jg.JsonGrammarException) as context:
            jg.SwitchDict('foo', switch_key, case_keys)
        self.assertEqual('switch_key_conflict', context.exception.args[0])

        case_keys = {'a': [jg.SwitchDict.make_key('a1', jg.Atom('atom', int, value=0)),
                           jg.SwitchDict.make_key('a1', jg.Atom('atom', int, 1))],
                     'b': [jg.SwitchDict.make_key('b1', jg.Atom('atom', int)),
                           jg.SwitchDict.make_key('b2', jg.Atom('atom', int))]}
        test_switch = jg.SwitchDict('foo', switch_key, case_keys)
        self.run_node_parse_error(test_switch, {'x': 'a', 'a1': 0}, 'dict_duplicate_keys')

    # Test parsing dictionaries
    # Both complete and minimal
    def test_parse_switch_dict(self):
        # Has right number of keys
        self.run_node_parse(self.test_switch, {'x': 'a', 'a1': 1, 'a2': 2, 'a3': 3}, None, None)

        self.run_node_parse(self.test_switch, {'x': 'b', 'b1': 1, 'b2': 2, 'b3': 3},
                            {'x': 'b'}, {'x': 'b'})
        self.run_node_parse(self.test_switch, {'x': 'b', 'b1': 2, 'b2': 2, 'b3': 3},
                            {'x': 'b', 'b1': 2}, {'x': 'b', 'b1': 2})
        self.run_node_parse(self.test_switch, {'x': 'b', 'b1': 2, 'b2': 4, 'b3': 6},
                            {'x': 'b', 'b1': 2, 'b2': 4, 'b3': 6}, {'x': 'b', 'b1': 2, 'b2': 4, 'b3': 6})

        # Has too few keys
        self.run_node_parse_complete_error(self.test_switch, {'x': 'a', 'a1': 1, 'a2': 2},
                                           'dict_bad_keys', None)
        self.run_node_parse_complete_error(self.test_switch, {'x': 'b', 'b1': 1, 'b2': 2},
                                           'dict_bad_keys', {'x': 'b'})
        self.run_node_parse_complete_error(self.test_switch, {'x': 'b', 'b1': 2, 'b2': 2},
                                           'dict_bad_keys', {'x': 'b', 'b1': 2})

    def test_parse_switch_dict_switch_var(self):
        switch_enum = jg.Enum('enum', ['a', 'b'], None, var='x')
        switch_key = jg.SwitchDict.make_key('x', switch_enum)
        case_keys = {'a': [jg.SwitchDict.make_key('a1', jg.Atom('atom', int, value=1))],
                     'b': [jg.SwitchDict.make_key('b1', jg.Atom('atom', int, value=1))]}
        test_switch = jg.SwitchDict('test', switch_key, case_keys)
        self.run_node_parse_model(test_switch, {'x': 'a', 'a1': 1}, None, None, 'a')
        self.run_node_parse_model(test_switch, {'x': 'b', 'b1': 1}, None, None, 'b')

    def test_parse_switch_dict_context(self):
        # Test switch dict context
        # Test non switch key is a value context function, success and failure
        switch_enum = jg.Enum('enum', ['a', 'b'], 'a')
        switch_key = jg.SwitchDict.make_key('x', switch_enum)
        case_keys = {'a': [jg.SwitchDict.make_key('a1', jg.Atom('atom', int, value=1)),
                           jg.SwitchDict.make_key('a2', jg.Atom('atom', int, value=lambda elem, ctxt, lp: ctxt['a1']))],
                     'b': [jg.SwitchDict.make_key('b1', jg.Atom('atom', int, 1))]}
        test_switch = jg.SwitchDict('test', switch_key, case_keys)
        self.run_node_parse(test_switch, {'x': 'a', 'a1': 1, 'a2': 1}, None, None)
        self.run_node_parse_error(test_switch, {'x': 'a', 'a1': 1, 'a2': 2}, 'atom_wrong_value')

        # Test non switch key is a default context function, match and doesn't match
        case_keys = {'a': [jg.SwitchDict.make_key('a1', jg.Atom('atom', int, 1)),
                           jg.SwitchDict.make_key('a2', jg.Atom('atom', int, lambda elem, ctxt, lp: ctxt['a1']))],
                     'b': [jg.SwitchDict.make_key('b1', jg.Atom('atom', int, 1))]}
        test_switch = jg.SwitchDict('test', switch_key, case_keys)
        self.run_node_parse(test_switch, {'x': 'a', 'a1': 1, 'a2': 1}, None, None)
        self.run_node_parse(test_switch, {'x': 'a', 'a1': 2, 'a2': 2}, {'a1': 2}, {'a1': 2})
        self.run_node_parse(test_switch, {'x': 'a', 'a1': 1, 'a2': 2}, {'a2': 2}, {'a2': 2})
        self.run_node_parse(test_switch, {'x': 'a', 'a1': 2, 'a2': 3},
                            {'a1': 2, 'a2': 3}, {'a1': 2, 'a2': 3})

    def test_parse_switch_dict_common_keys(self):
        test_switch = make_common_switch()
        self.run_node_parse(test_switch, {'switch': 'a', 'a1': 1, 'a2': 2, 'c1': 1, 'c2': 2},
                            None, None)

    def test_switch_models(self):
        test_switch_enum = jg.Enum('enum', ['a', 'b', 'c'], 'a', var='switch_key')
        test_switch_key = jg.SwitchDict.make_key('switcher', test_switch_enum)
        test_common_keys = [jg.SwitchDict.make_key('x', jg.Atom('atom x', int, 1, var='x')),
                            jg.SwitchDict.make_key('y', jg.Atom('atom y', int, 2, var='y'))]
        test_case_keys = {'a': [SwitchAModel,
                                jg.SwitchDict.make_key('a1', jg.Atom('atom', int, 1, var='a1')),
                                jg.SwitchDict.make_key('a2', jg.Atom('atom', int, 2, var='a2'))],
                          'b': [SwitchBModel,
                                jg.SwitchDict.make_key('b1', jg.Atom('atom', int, 1, var='b1')),
                                jg.SwitchDict.make_key('b2', jg.Atom('atom', int, 2, var='b2')),
                                jg.SwitchDict.make_key('b3', jg.Atom('atom', int, 3))],
                          'c': [SwitchCModel,
                                jg.SwitchDict.make_key('c1', jg.Atom('atom', int, 1, var='c1')),
                                jg.SwitchDict.make_key('c2', jg.Atom('atom', int, 2, var='c2')),
                                jg.SwitchDict.make_key('c3', jg.Atom('atom', int, 3))]}
        test_switch = jg.SwitchDict('test', test_switch_key, test_case_keys, common_keys=test_common_keys,
                                    model_var='switched_model', model=SwitchBaseModel)
        expected = SwitchBaseModel()
        expected.x = 3
        expected.y = 4
        expected.switched_key = 'a'
        expected.switched_model = SwitchAModel()
        expected.switched_model.a1 = 3
        expected.switched_model.a2 = 4
        self.run_grammar_parse(test_switch, {'switcher': 'a', 'a1': 3, 'a2': 4, 'x': 3, 'y': 4}, expected, expected)


class JsonGrammarListNodeParseTestCase(JsonGrammarBaseTestCase):
    def test_parse_list(self):
        # list isn't a list
        test_schema = jg.List('list', 1, jg.Atom('atom', int, value=1))
        self.run_node_parse_error(test_schema, 3, 'type_not_list')

        # List is wrong length
        test_schema = jg.List('list', 2, jg.Atom('atom', int, value=1))
        # Too long
        self.run_node_parse_error(test_schema, [1, 2, 3], 'list_bad_length')
        # Too short
        self.run_node_parse_complete_error(test_schema, [1], 'list_bad_length', None)

        # List is a list and right length, check list index
        test_schema = jg.List('list', 3, jg.Atom('atom', int, value=lambda elem, ctxt, x: x[-1]))
        self.run_node_parse(test_schema, [0, 1, 2], None, None)

        # test nested lists
        test_schema = jg.List('list', 3, jg.List('list', 3,
                                                 jg.Atom('atom', int, value=lambda elem, ctxt, x: x[-1] + x[-2])))
        self.run_node_parse(test_schema, [[0, 1, 2], [1, 2, 3], [2, 3, 4]], None, None)

        # Test lists with defaults
        test_schema = jg.List('list', 3, jg.Atom('atom', int, 1))
        # test list with all matching defaults
        self.run_node_parse(test_schema, [1, 1, 1], None, None)

        self.run_node_parse(test_schema, [2, 1, 1], [2, None, None], [2])
        self.run_node_parse(test_schema, [1, 2, 1], [None, 2, None], [None, 2])
        self.run_node_parse(test_schema, [2, 2, 1], [2, 2, None], [2, 2])
        self.run_node_parse(test_schema, [1, 1, 2], [None, None, 2], [None, None, 2])
        self.run_node_parse(test_schema, [2, 1, 2], [2, None, 2], [2, None, 2])
        self.run_node_parse(test_schema, [1, 2, 2], [None, 2, 2], [None, 2, 2])
        self.run_node_parse(test_schema, [2, 2, 2], [2, 2, 2], [2, 2, 2])

    def test_parse_unlimited_list(self):
        zero_list = jg.List('list', 0, jg.Atom('atom', int, 1))
        self.run_node_parse_complete_error(zero_list, [], 'unlimited_list_complete_grammar', None)
        self.run_node_parse_complete_error(zero_list, [1], 'unlimited_list_complete_grammar', None)
        self.run_node_parse_complete_error(zero_list, [1, 1, 1], 'unlimited_list_complete_grammar', None)
        self.run_node_parse_complete_error(zero_list, [2], 'unlimited_list_complete_grammar', [2])
        self.run_node_parse_complete_error(zero_list, [1, 2, 3], 'unlimited_list_complete_grammar', [None, 2, 3])

    def test_parse_list_minimal(self):
        test_schema = jg.List('list', 10, jg.Atom('atom', int, default=1))

        # empty list
        self.run_node_parse(test_schema, [1, 1, 1, 1, 1, 1, 1, 1, 1, 1], None, None)
        # full list
        self.run_node_parse(test_schema, [2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
                            [2, 3, 4, 5, 6, 7, 8, 9, 10, 11], [2, 3, 4, 5, 6, 7, 8, 9, 10, 11])
        # List empty at beginning, one or two slots
        self.run_node_parse(test_schema, [1, 3, 4, 5, 6, 7, 8, 9, 10, 11],
                            [None, 3, 4, 5, 6, 7, 8, 9, 10, 11], [None, 3, 4, 5, 6, 7, 8, 9, 10, 11])
        self.run_node_parse(test_schema, [1, 1, 4, 5, 6, 7, 8, 9, 10, 11],
                            [None, None, 4, 5, 6, 7, 8, 9, 10, 11], [None, None, 4, 5, 6, 7, 8, 9, 10, 11])
        # List empty at end, one or two slots
        self.run_node_parse(test_schema, [2, 3, 4, 5, 6, 7, 8, 9, 10, 1],
                            [2, 3, 4, 5, 6, 7, 8, 9, 10, None], [2, 3, 4, 5, 6, 7, 8, 9, 10])
        self.run_node_parse(test_schema, [2, 3, 4, 5, 6, 7, 8, 9, 1, 1],
                            [2, 3, 4, 5, 6, 7, 8, 9, None, None], [2, 3, 4, 5, 6, 7, 8, 9])
        # List empty in middle, one or two slots
        self.run_node_parse(test_schema, [2, 3, 4, 5, 1, 7, 8, 9, 10, 11],
                            [2, 3, 4, 5, None, 7, 8, 9, 10, 11], [2, 3, 4, 5, None, 7, 8, 9, 10, 11])
        self.run_node_parse(test_schema, [2, 3, 4, 5, 1, 1, 8, 9, 10, 11],
                            [2, 3, 4, 5, None, None, 8, 9, 10, 11], [2, 3, 4, 5, None, None, 8, 9, 10, 11])
        # List empty at beginning, middle and end
        self.run_node_parse(test_schema, [1, 1, 4, 5, 1, 1, 8, 9, 1, 1],
                            [None, None, 4, 5, None, None, 8, 9, None, None], [None, None, 4, 5, None, None, 8, 9])
        # Shorter list than expected
        self.run_node_parse_complete_error(test_schema, [2, 3, 4, 5], 'list_bad_length', [2, 3, 4, 5])


class JsonGrammarEnumNodeParseTestCase(JsonGrammarBaseTestCase):
    def test_parse_enum(self):
        test_enum = jg.Enum('enum', ['foo', 'bar', 'baz'], None)
        test_enum_default = jg.Enum('enum', ['foo', 'bar', 'baz'], 'bar')

        # enum is right type, right value
        for enum_value in test_enum.base:
            self.run_node_parse(test_enum, enum_value, enum_value, enum_value)

        # enum has right type but wrong value
        self.run_node_parse_error(test_enum, 'bum', 'bad_enum_value')

        # Now test defaults
        # Atom is right type, default value
        self.run_node_parse(test_enum_default, 'bar', None, None)

        # Atom has right type not default value
        self.run_node_parse(test_enum_default, 'foo', 'foo', 'foo')


class JsonGrammarAtomNodeParseTestCase(JsonGrammarBaseTestCase):
    def test_parse_atom_errors(self):
        # Atom has both default and value
        test_schema = jg.Atom('atom', str, value='123')
        test_schema.default = '456'
        self.run_node_parse_error(test_schema, '3', 'both_value_default')

        # Atom is wrong type
        test_schema = jg.Atom('atom', str, value='blah')
        self.run_node_parse_error(test_schema, 3, 'atom_wrong_type')

    def test_parse_atom(self):
        test_schema = jg.Atom('atom', int, value=3)
        self.run_node_parse(test_schema, 3, None, None)
        self.run_node_parse_error(test_schema, 4, 'atom_wrong_value')

        test_schema = jg.Atom('atom', int, value=lambda elem, ctxt, lp: 3)
        self.run_node_parse(test_schema, 3, None, None)
        self.run_node_parse_error(test_schema, 4, 'atom_wrong_value')

        # Now test defaults
        # Atom is right type, default value
        test_schema = jg.Atom('atom', int, 3)
        self.run_node_parse(test_schema, 3, None, None)
        # Atom has right type not default value
        self.run_node_parse(test_schema, 4, 4, 4)

        # Atom is right type, default value via function
        test_schema = jg.Atom('atom', int, lambda elem, ctxt, lp: 3)
        self.run_node_parse(test_schema, 3, None, None)

        # Atom is right type but wrong value via function
        self.run_node_parse(test_schema, 4, 4, 4)


class JsonGrammarDictNodeGenTestCase(JsonGrammarBaseTestCase):
    def test_gen_dict_value(self):
        test_schema = jg.Dict('foo',
                              [jg.Dict.make_key('a', jg.Atom('atom', int, value=1)),
                               jg.Dict.make_key('b', jg.Atom('atom', int, value=2)),
                               jg.Dict.make_key('c', jg.Atom('atom', int, value=3))])
        test_result = {'a': 1, 'b': 2, 'c': 3}
        self.run_node_gen_error(test_schema, 3, 'type_not_dict')
        # Test dict is None
        self.run_node_gen(test_schema, None, test_result, test_result)
        # Test dict is model, but no need to test variable, handled by test_elem
        self.run_node_gen(test_schema, ObjectForTests(), test_result, test_result)
        # Test dict is a dict, but too few keys
        self.run_node_gen(test_schema, {'a': 1, 'b': 2}, test_result, {'c': 3})
        # Test dict is a dict, right number of keys, but key name mismatch
        self.run_node_gen_error(test_schema, {'a': 1, 'b': 2, 'd': 3}, 'dict_bad_keys')
        # Test dict is a dict
        self.run_node_gen(test_schema, test_result, test_result, None)

    def test_gen_dict_default(self):
        test_schema = jg.Dict('test',
                              [jg.Dict.make_key('a', jg.Atom('atom', int, 1)),
                               jg.Dict.make_key('b', jg.Atom('atom', int, 1)),
                               jg.Dict.make_key('c', jg.Atom('atom', int, 1)),
                               jg.Dict.make_key('d', jg.Atom('atom', int, 1))])

        # Test that None produces None
        self.run_node_gen(test_schema, None, {'a': 1, 'b': 1, 'c': 1, 'd': 1}, None)

        # Test that no keys appearing produced None
        self.run_node_gen(test_schema, {}, {'a': 1, 'b': 1, 'c': 1, 'd': 1}, None)

        # Test wrong key out of all
        self.run_node_gen_error(test_schema, {'e': 1}, 'dict_bad_keys')

        # Test one key out of all
        self.run_node_gen(test_schema, {'a': 2}, {'a': 2, 'b': 1, 'c': 1, 'd': 1}, {'a': 2})
        self.assertEqual({"a": 2}, test_schema.gen(minimal_conf, {'a': 2}, None, []))
        # Test two keys out of all
        self.run_node_gen(test_schema, {'a': 2, 'c': 3}, {'a': 2, 'b': 1, 'c': 3, 'd': 1}, {'a': 2, 'c': 3})
        self.assertEqual({"a": 2, 'c': 3}, test_schema.gen(minimal_conf, {'a': 2, 'c': 3}, None, []))
        # Test all keys out of all
        self.run_node_gen(test_schema, {'a': 2, 'b': 4, 'c': 3, 'd': 5},
                          {'a': 2, 'b': 4, 'c': 3, 'd': 5}, {'a': 2, 'b': 4, 'c': 3, 'd': 5})
        self.assertEqual({"a": 2, 'b': 4, 'c': 3, 'd': 5},
                         test_schema.gen(minimal_conf, {'a': 2, 'b': 4, 'c': 3, 'd': 5}, None, []))

    def test_gen_dict_context(self):
        # Test ordering of keys, they are added in order of appearance
        # Test value function: None as model produces appropriate value
        test_schema = jg.Dict('foo',
                              [jg.Dict.make_key('a', jg.Atom('atom', int, value=1)),
                               jg.Dict.make_key('b', jg.Atom('atom', int, value=lambda elem, ctxt, lp: ctxt['a']))])
        self.run_node_gen(test_schema, None, {'a': 1, 'b': 1}, {'a': 1, 'b': 1})

        # Test value function: None as model, improper ordering fails
        test_schema = jg.Dict('foo',
                              [jg.Dict.make_key('a', jg.Atom('atom', int, value=lambda elem, ctxt, lp: ctxt['b'])),
                               jg.Dict.make_key('b', jg.Atom('atom', int, value=1))])
        self.run_node_gen_error(test_schema, None, 'b', exception=KeyError)

        # Test default function:
        # None as model produces appropriate entry
        test_schema = jg.Dict('foo',
                              [jg.Dict.make_key('a', jg.Atom('atom', int, default=1)),
                               jg.Dict.make_key('b', jg.Atom('atom', int, default=lambda elem, ctxt, lp: ctxt['a']))])
        self.run_node_gen(test_schema, None, {'a': 1, 'b': 1}, None)

        #  Non default as model produces appropriate entry
        test_schema = jg.Dict('foo',
                              [jg.Dict.make_key('a', jg.Atom('atom', int, default=1)),
                               jg.Dict.make_key('b', jg.Atom('atom', int, default=lambda elem, ctxt, lp: ctxt['a']))])
        self.run_node_gen(test_schema, {'a': 2}, {'a': 2, 'b': 2}, {'a': 2})
        self.run_node_gen(test_schema, {'b': 2}, {'a': 1, 'b': 2}, {'b': 2})


class JsonGrammarSwitchDictNodeGenTestCase(JsonGrammarBaseTestCase):

    def test_gen_switch_dict(self):
        test_case_keys = {'a': [jg.SwitchDict.make_key('d', jg.Atom('atom', int, 1))],
                          'b': [jg.SwitchDict.make_key('e', jg.Atom('atom', int, 1))],
                          'c': [jg.SwitchDict.make_key('f', jg.Atom('atom', int, 1))]}
        test_enum = jg.Enum('enum', ["a", "b", "c"], None)
        test_enum_default = jg.Enum('enum', ["a", "b", "c"], "a")
        test_switch_dict_schema = jg.SwitchDict('test',
                                                jg.SwitchDict.make_key('switch', test_enum_default),
                                                test_case_keys)
        test_switch_dict_default_schema = jg.SwitchDict('test',
                                                        jg.SwitchDict.make_key('switch', test_enum),
                                                        test_case_keys)

        # Test switch dict model is None, enum has default
        self.run_node_gen(test_switch_dict_schema, None, {'switch': 'a', 'd': 1}, None)

        # Test switch dict model is None, enum doesn't have default
        self.run_node_gen_error(test_switch_dict_default_schema, None, 'enum_no_default')

        # Test switch dict model is a model, no variable (that test handled by test_elem), enum has default
        self.run_node_gen(test_switch_dict_schema, ObjectForTests(), {'switch': 'a', 'd': 1}, None)

        # Test switch dict model is a model, no variable (that test handled by test_elem), enum has no default
        self.run_node_gen_error(test_switch_dict_default_schema, ObjectForTests(), 'enum_no_default')

        # Test switch dict model is a dict, but wrong number of keys
        self.run_node_gen_error(test_switch_dict_schema, {'switch': 'b', 'e': 1, 'f': 1}, 'dict_bad_keys')

        # Test switch dict model is a dict, right number of keys, but wrong keys
        self.run_node_gen_error(test_switch_dict_schema, {'switch': 'b', 'd': 1}, 'dict_bad_keys')

        # Test switch dict has an invalid switch field
        self.run_node_gen_error(test_switch_dict_schema, {'switch': 'd', 'd': 1}, 'switch_dict_bad_switch')

        # Test switch dict has a valid switch field
        self.run_node_gen(test_switch_dict_schema, {'switch': 'a', 'd': 1}, {'switch': 'a', 'd': 1}, None)

        # Test switch dict has a valid switch field
        self.run_node_gen(test_switch_dict_schema, {'switch': 'b', 'e': 2},
                          {'switch': 'b', 'e': 2}, {'switch': 'b', 'e': 2})

    def test_switch_dict_context(self):
        # Functions cannot appear as switch
        # Test value function: None as model produces appropriate value
        # Test default function:
        #  None as model produces appropriate entry
        #  Non default as model produces appropriate entry
        # Must test ordering where keys added to context
        test_switch_key = jg.SwitchDict.make_key('switch', jg.Enum('enum', ["a", "b"], "a"))
        test_case_keys = {'a': [jg.SwitchDict.make_key('a1', jg.Atom('atom', int, value=1)),
                                jg.SwitchDict.make_key(
                                    'a2',
                                    jg.Atom('atom', int, value=lambda elem, ctxt, lp: ctxt['a1']))],
                          'b': [jg.SwitchDict.make_key('b1', jg.Atom('atom', int, value=1)),
                                jg.SwitchDict.make_key(
                                    'b2',
                                    jg.Atom('atom', int, value=lambda elem, ctxt, lp: ctxt['b1']))]}
        test_schema = jg.SwitchDict('test', test_switch_key, test_case_keys)
        # Test value function: None as model produces appropriate value
        self.run_node_gen(test_schema, None, {'switch': 'a', 'a1': 1, 'a2': 1}, {'a1': 1, 'a2': 1})

        # Test value function: None as model, improper ordering fails
        test_case_keys = {'a': [jg.SwitchDict.make_key('a1',
                                                       jg.Atom('atom', int, value=lambda elem, ctxt, lp: ctxt['a2'])),
                                jg.SwitchDict.make_key('a2', jg.Atom('atom', int, value=1))],
                          'b': [jg.SwitchDict.make_key('b1', jg.Atom('atom', int, value=1)),
                                jg.SwitchDict.make_key(
                                    'b2',
                                    jg.Atom('atom', int, value=lambda elem, ctxt, lp: ctxt['b1']))]}
        test_schema = jg.SwitchDict('test', test_switch_key, test_case_keys)
        self.run_node_gen_error(test_schema, None, 'a2', exception=KeyError)

        # Test default function:
        #  None as model produces appropriate entry
        test_case_keys = {'a': [jg.SwitchDict.make_key('a1', jg.Atom('atom', int, 1)),
                                jg.SwitchDict.make_key('a2', jg.Atom('atom', int, lambda elem, ctxt, lp: ctxt['a1']))],
                          'b': [jg.SwitchDict.make_key('b1', jg.Atom('atom', int, 1)),
                                jg.SwitchDict.make_key('b2', jg.Atom('atom', int, lambda elem, ctxt, lp: ctxt['b1']))]}
        test_schema = jg.SwitchDict('test', test_switch_key, test_case_keys)
        self.run_node_gen(test_schema, None, {'switch': 'a', 'a1': 1, 'a2': 1}, None)

        #  Non default as model produces appropriate entry
        self.run_node_gen(test_schema, {'switch': 'a', 'a1': 2},
                          {'switch': 'a', 'a1': 2, 'a2': 2}, {'a1': 2})
        self.run_node_gen(test_schema, {'switch': 'a', 'a1': 2, 'a2': 4},
                          {'switch': 'a', 'a1': 2, 'a2': 4}, {'a1': 2, 'a2': 4})
        self.run_node_gen(test_schema, {'switch': 'b', 'b1': 2},
                          {'switch': 'b', 'b1': 2, 'b2': 2}, {'switch': 'b', 'b1': 2})
        self.run_node_gen(test_schema, {'switch': 'b', 'b1': 2, 'b2': 4},
                          {'switch': 'b', 'b1': 2, 'b2': 4}, {'switch': 'b', 'b1': 2, 'b2': 4})
        self.run_node_gen(test_schema, {'switch': 'b', 'b1': 2, 'b2': 4},
                          {'switch': 'b', 'b1': 2, 'b2': 4}, {'switch': 'b', 'b1': 2, 'b2': 4})

    def test_gen_switch_dict_common_keys(self):
        test_switch = make_common_switch()
        self.run_node_gen(test_switch, None, {'switch': 'a', 'a1': 1, 'a2': 2, 'c1': 1, 'c2': 2}, None)

    def test_switch_models(self):
        test_switch_enum = jg.Enum('enum', ['a', 'b', 'c'], 'a', var='switch_key')
        test_switch_key = jg.SwitchDict.make_key('switcher', test_switch_enum)
        test_common_keys = [jg.SwitchDict.make_key('x', jg.Atom('atom x', int, 1, var='x')),
                            jg.SwitchDict.make_key('y', jg.Atom('atom y', int, 2, var='y'))]
        test_case_keys = {'a': [SwitchAModel,
                                jg.SwitchDict.make_key('a1', jg.Atom('atom', int, 1, var='a1')),
                                jg.SwitchDict.make_key('a2', jg.Atom('atom', int, 2, var='a2'))],
                          'b': [SwitchBModel,
                                jg.SwitchDict.make_key('b1', jg.Atom('atom', int, 1, var='b1')),
                                jg.SwitchDict.make_key('b2', jg.Atom('atom', int, 2, var='b2')),
                                jg.SwitchDict.make_key('b3', jg.Atom('atom', int, 3))],
                          'c': [SwitchCModel,
                                jg.SwitchDict.make_key('c1', jg.Atom('atom', int, 1, var='c1')),
                                jg.SwitchDict.make_key('c2', jg.Atom('atom', int, 2, var='c2')),
                                jg.SwitchDict.make_key('c3', jg.Atom('atom', int, 3))]}
        test_switch = jg.SwitchDict('test', test_switch_key, test_case_keys, common_keys=test_common_keys,
                                    model_var='switched_model', model=SwitchBaseModel)
        model = SwitchBaseModel()
        model.x = 3
        model.y = 4
        model.switch_key = 'a'
        model.switched_model = SwitchAModel()
        model.switched_model.a1 = 3
        model.switched_model.a2 = 4
        result1 = {'switcher': 'a', 'a1': 3, 'a2': 4, 'x': 3, 'y': 4}
        result2 = {'a1': 3, 'a2': 4, 'x': 3, 'y': 4}
        self.run_node_gen(test_switch, model, result1, result2)


class JsonGrammarListNodeGenTestCase(JsonGrammarBaseTestCase):
    def test_list(self):
        test_value_schema = jg.List('list', 3, jg.Atom('atom', int, value=1))
        test_unlimited_value_schema = jg.List('list', 0, jg.Atom('atom', int, value=1))
        test_value_fn_schema = jg.List('list', 3, jg.Atom('atom', int, value=lambda elem, ctxt, lp: lp[-1] * lp[-2]))
        test_default_schema = jg.List('list', 3, jg.Atom('atom', int, 1))
        test_unlimited_default_schema = jg.List('list', 0, jg.Atom('atom', int, 1))
        test_default_fn_schema = jg.List('list', 3, jg.Atom('atom', int, lambda elem, ctxt, lp: lp[-1] * lp[-2]))

        # Test list is wrong length
        self.run_node_gen_error(test_value_schema, 3, 'model_schema_mismatch')
        self.run_node_gen_error(test_value_schema, [1, 1, 1, 1], 'list_bad_length')

        # Test model is None
        self.run_node_gen(test_value_schema, None, [1, 1, 1], [1, 1, 1])
        self.run_node_gen(test_unlimited_value_schema, None, [], None)
        self.run_node_gen(test_value_fn_schema, None, [0, 2, 4], [0, 2, 4], list_pos=[2])
        self.run_node_gen(test_default_schema, None, [1, 1, 1], None)
        self.run_node_gen(test_unlimited_default_schema, None, [], None)
        self.run_node_gen(test_default_fn_schema, None, [0, 2, 4], None, list_pos=[2])

        # Test model is model, but no need to test variable, handled by test_elem
        test_obj = ObjectForTests()
        self.run_node_gen(test_value_schema, test_obj, [1, 1, 1], [1, 1, 1])
        self.run_node_gen(test_unlimited_value_schema, test_obj, [], None)
        self.run_node_gen(test_value_fn_schema, test_obj, [0, 2, 4], [0, 2, 4], list_pos=[2])
        self.run_node_gen(test_default_schema, test_obj, [1, 1, 1], None)
        self.run_node_gen(test_unlimited_default_schema, test_obj, [], None)
        self.run_node_gen(test_default_fn_schema, test_obj, [0, 2, 4], None, list_pos=[2])

        # Test model is list, and uses a function relying on list_pos, including nested list_pos
        self.run_node_gen(test_value_schema, [1, 1, 1], [1, 1, 1], None)
        self.run_node_gen(test_unlimited_value_schema, [1, 1, 1], [1, 1, 1], None)
        self.run_node_gen(test_value_fn_schema, [0, 2, 4], [0, 2, 4], None, list_pos=[2])
        self.run_node_gen(test_default_schema, [1, 1, 1], [1, 1, 1], None)
        self.run_node_gen(test_unlimited_default_schema, [1, 1, 1], [1, 1, 1], None)
        self.run_node_gen(test_default_fn_schema, [0, 2, 4], [0, 2, 4], None, list_pos=[2])

    def test_gen_list_minimal(self):
        test_schema = jg.List('list', 10, jg.Atom('atom', int, default=1))
        # Test a full list
        self.run_node_gen(test_schema, [2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
                          [2, 3, 4, 5, 6, 7, 8, 9, 10, 11], [2, 3, 4, 5, 6, 7, 8, 9, 10, 11])
        # Empty list
        self.run_node_gen(test_schema, [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
                          [1, 1, 1, 1, 1, 1, 1, 1, 1, 1], None)
        # List empty at beginning, one or two slots
        self.run_node_gen(test_schema, [1, 3, 4, 5, 6, 7, 8, 9, 10, 11],
                          [1, 3, 4, 5, 6, 7, 8, 9, 10, 11], [None, 3, 4, 5, 6, 7, 8, 9, 10, 11])
        self.run_node_gen(test_schema, [1, 1, 4, 5, 6, 7, 8, 9, 10, 11],
                          [1, 1, 4, 5, 6, 7, 8, 9, 10, 11], [None, None, 4, 5, 6, 7, 8, 9, 10, 11])
        # List empty at end, one or two slots
        self.run_node_gen(test_schema, [2, 3, 4, 5, 6, 7, 8, 9, 10, 1],
                          [2, 3, 4, 5, 6, 7, 8, 9, 10, 1], [2, 3, 4, 5, 6, 7, 8, 9, 10])
        self.run_node_gen(test_schema, [2, 3, 4, 5, 6, 7, 8, 9, 1, 1],
                          [2, 3, 4, 5, 6, 7, 8, 9, 1, 1], [2, 3, 4, 5, 6, 7, 8, 9])
        # List empty in middle, one or two slots
        self.run_node_gen(test_schema, [2, 3, 4, 5, 1, 7, 8, 9, 10, 11],
                          [2, 3, 4, 5, 1, 7, 8, 9, 10, 11], [2, 3, 4, 5, None, 7, 8, 9, 10, 11])
        self.run_node_gen(test_schema, [2, 3, 4, 5, 1, 1, 8, 9, 10, 11],
                          [2, 3, 4, 5, 1, 1, 8, 9, 10, 11], [2, 3, 4, 5, None, None, 8, 9, 10, 11])
        # List empty at beginning, middle and end
        self.run_node_gen(test_schema, [1, 1, 4, 5, 1, 1, 8, 9, 1, 1],
                          [1, 1, 4, 5, 1, 1, 8, 9, 1, 1], [None, None, 4, 5, None, None, 8, 9])


class JsonGrammarEnumNodeGenTestCase(JsonGrammarBaseTestCase):
    def test_enum(self):
        test_enum = jg.Enum('enum', ["one", "two", "three", "four"], None)
        test_default_enum = jg.Enum('enum', ["one", "two", "three", "four"], default="one")

        # Enum, empty model with no enum default value
        self.run_node_gen_error(test_enum, None, 'enum_no_default')

        # Enum with default value, empty model
        self.run_node_gen(test_default_enum, None, "one", None)

        # Enum w/ default value, model is value
        self.run_node_gen(test_enum, "one", "one", "one")
        self.run_node_gen(test_default_enum, "one", "one", None)
        self.run_node_gen(test_enum, "two", "two", "two")
        self.run_node_gen(test_default_enum, "two", "two", "two")

        test_model = ObjectForTests()
        self.run_node_gen(test_default_enum, test_model, "one", None)


class JsonGrammarAtomNodeGenTestCase(JsonGrammarBaseTestCase):
    def test_atom(self):
        # Value Atom, int, int from a function, string and bool
        value_int_atom = jg.Atom('atom', int, value=1)
        value_int_fn_atom = jg.Atom('atom', int, value=lambda elem, ctxt, lp: 1)
        value_str_atom = jg.Atom('atom', str, value="a")
        value_bool_atom = jg.Atom('atom', bool, value=True)

        default_int_atom = jg.Atom('atom', int, 1)
        default_int_fn_atom = jg.Atom('atom', int, lambda elem, ctxt, lp: 1)
        default_str_atom = jg.Atom('atom', str, "a")
        default_bool_atom = jg.Atom('atom', bool, True)

        # Val atom w/ incorrect value
        self.run_node_gen_error(value_int_atom, 2, 'model_schema_mismatch')
        self.run_node_gen_error(value_int_fn_atom, 2, 'model_schema_mismatch')
        self.run_node_gen_error(value_str_atom, 'b', 'model_schema_mismatch')
        self.run_node_gen_error(value_bool_atom, False, 'model_schema_mismatch')

        # Val atom w/ correct value
        self.run_node_gen(value_int_atom, 1, 1, None)
        self.run_node_gen(value_int_fn_atom, 1, 1, None)
        self.run_node_gen(value_str_atom, 'a', 'a', None)
        self.run_node_gen(value_bool_atom, True, True, None)

        # Val atom w/ None,
        self.run_node_gen(value_int_atom, None, 1, 1)
        self.run_node_gen(value_int_fn_atom, None, 1, 1)
        self.run_node_gen(value_str_atom, None, 'a', 'a')
        self.run_node_gen(value_bool_atom, None, True, True)

        # Val atom with model value
        test_model = ObjectForTests()
        self.run_node_gen(value_int_atom, test_model, 1, 1)
        self.run_node_gen(value_int_fn_atom, test_model, 1, 1)
        self.run_node_gen(value_str_atom, test_model, 'a', 'a')
        self.run_node_gen(value_bool_atom, test_model, True, True)

        # Default atom w/ default value
        self.run_node_gen(default_int_atom, 1, 1, None)
        self.run_node_gen(default_int_fn_atom, 1, 1, None)
        self.run_node_gen(default_str_atom, 'a', 'a', None)
        self.run_node_gen(default_bool_atom, True, True, None)

        # Default atom w/ None,
        self.run_node_gen(default_int_atom, None, 1, None)
        self.run_node_gen(default_int_fn_atom, None, 1, None)
        self.run_node_gen(default_str_atom, None, 'a', None)
        self.run_node_gen(default_bool_atom, None, True, None)

        # Default atom w/ non-default value
        self.run_node_gen(default_int_atom, 2, 2, 2)
        self.run_node_gen(default_int_fn_atom, 2, 2, 2)
        self.run_node_gen(default_str_atom, 'b', 'b', 'b')
        self.run_node_gen(default_bool_atom, False, False, False)

        # Default atom w/ Model,
        self.run_node_gen(default_int_atom, test_model, 1, None)
        self.run_node_gen(default_int_fn_atom, test_model, 1, None)
        self.run_node_gen(default_str_atom, test_model, 'a', None)
        self.run_node_gen(default_bool_atom, test_model, True, None)


class JsonGrammarPrintTestCase(unittest.TestCase):
    def test_print(self):
        grammar = jg.JsonGrammar(MC6Pro_grammar.mc6pro_schema)
        result = grammar.print()
        self.assertTrue(isinstance(result, str))
        grammar = jg.JsonGrammar(MC6Pro_intuitive.mc6pro_intuitive_schema)
        result = grammar.print()
        self.assertTrue(isinstance(result, str))


class IntuitiveMessageCatalogTestCase(unittest.TestCase):
    def test_init(self):
        message1 = im.IntuitiveMessage.make_bank_jump_message('one', 2, 1, None)
        message2 = im.IntuitiveMessage.make_bank_jump_message('two', 1, 2, None)
        messages = [message1, message2]

        catalog = MC6Pro_intuitive.MessageCatalog(messages)
        self.assertEqual(len(catalog.catalog), 2)
        self.assertEqual(catalog.lookup('one'), message1)
        self.assertEqual(catalog.lookup('two'), message2)

    def test_add(self):
        catalog = MC6Pro_intuitive.MessageCatalog()
        message = im.IntuitiveMessage.make_bank_jump_message('one', 2, 1, catalog)
        self.assertEqual('one', message)
        message = catalog.lookup('one')
        message.name = 'two'
        self.assertEqual(catalog.add(message), 'one')


class IntuitiveColorsCatalogTestCase(unittest.TestCase):
    def test_init(self):
        colors1 = MC6Pro_intuitive.ColorSchema.make_preset_schema('black', 'lime',
                                                                  'blue', 'orchid', 'green',
                                                                  'yellow', 'gray',
                                                                  name='One')
        colors2 = MC6Pro_intuitive.ColorSchema.make_preset_schema('orange', 'red',
                                                                  'skyblue', 'olivedrab', 'green',
                                                                  'deeppink', 'mediumslateblue',
                                                                  name='Two')
        colors = [colors1, colors2]
        catalog = MC6Pro_intuitive.ColorsCatalog(colors)
        self.assertEqual(len(catalog.catalog), 2)
        self.assertEqual(catalog.lookup('One'), colors1)
        self.assertEqual(catalog.lookup('Two'), colors2)

    def test_add(self):
        catalog = MC6Pro_intuitive.ColorsCatalog()
        colors1 = MC6Pro_intuitive.ColorSchema.make_preset_schema('black', 'lime',
                                                                  'blue', 'orchid', 'green',
                                                                  'yellow', 'gray',
                                                                  name='One')
        self.assertEqual(catalog.add(colors1), 'One')
        colors1.name = 'Two'
        self.assertEqual(catalog.add(colors1), 'One')


class IntuitiveColorSchemaTestCase(unittest.TestCase):
    def test_colors_schema(self):
        self.assertEqual(MC6Pro_intuitive.ColorSchema.from_base_bank_color(None), "default")
        self.assertEqual(MC6Pro_intuitive.ColorSchema.from_base_bank_color(127), "default")
        self.assertEqual(MC6Pro_intuitive.ColorSchema.from_base_bank_color(7), "white")
        self.assertIsNone(MC6Pro_intuitive.ColorSchema.to_base_bank_color("default"))
        self.assertEqual(MC6Pro_intuitive.ColorSchema.to_base_bank_color("white"), 7)
        self.assertEqual(MC6Pro_intuitive.ColorSchema.from_base_preset_color(None, False), "white")
        self.assertEqual(MC6Pro_intuitive.ColorSchema.from_base_preset_color(None, True), "black")
        self.assertEqual(MC6Pro_intuitive.ColorSchema.from_base_preset_color(0, False), "black")
        self.assertEqual(MC6Pro_intuitive.ColorSchema.from_base_preset_color(7, True), "white")
        self.assertEqual(MC6Pro_intuitive.ColorSchema.from_base_preset_color(4, False), "yellow")
        self.assertIsNone(MC6Pro_intuitive.ColorSchema.to_base_preset_color("black", True))
        self.assertIsNone(MC6Pro_intuitive.ColorSchema.to_base_preset_color("white", False))
        self.assertEqual(MC6Pro_intuitive.ColorSchema.to_base_preset_color("yellow", True), 4)
        self.assertEqual(MC6Pro_intuitive.ColorSchema.to_base_preset_color("yellow", False), 4)


class MC6ProColorsInheritanceTestCase(unittest.TestCase):
    def check_bank(self, bank, foreground_color, background_color):
        if foreground_color is None:
            self.assertIsNone(bank.text_color)
        else:
            self.assertEqual(bank.text_color, MC6Pro_intuitive.preset_colors.index(foreground_color))
        if background_color is None:
            self.assertIsNone(bank.background_color)
        else:
            self.assertEqual(bank.background_color, MC6Pro_intuitive.preset_colors.index(background_color))

    def check_preset(self, preset, preset_color, preset_toggle_color, preset_background_color,
                     preset_toggle_background_color):
        if preset_color is None:
            self.assertIsNone(preset.name_color)
        else:
            self.assertEqual(preset.name_color, MC6Pro_intuitive.preset_colors.index(preset_color))
        if preset_toggle_color is None:
            self.assertIsNone(preset.name_toggle_color)
        else:
            self.assertEqual(preset.name_toggle_color, MC6Pro_intuitive.preset_colors.index(preset_toggle_color))
        if preset_background_color is None:
            self.assertIsNone(preset.background_color)
        else:
            self.assertEqual(preset.background_color, MC6Pro_intuitive.preset_colors.index(preset_background_color))
        if preset_toggle_background_color is None:
            self.assertIsNone(preset.background_toggle_color)
        else:
            self.assertEqual(preset.background_toggle_color,
                             MC6Pro_intuitive.preset_colors.index(preset_toggle_background_color))

    def test_inheritance1(self):
        # Navigator schema:
        #   Bank: steelblue/lightsteelblue
        #   Preset: tan/cornsilk
        #   Preset Toggle: brown/maroon
        # Default schema:
        #   Bank: orange/red
        #   Preset: skyblue/olivedrab
        #   Preset Toggle: deeppink/mediumslateblue
        # Bank 2 schema:
        #   Bank: blueviolet/thistle
        #   Preset: darkseagreen/olive
        #   Preset Toggle: forestgreen/indigo
        # Preset 2 schema:
        #   Preset: khaki/lightyellow
        #   Preset Toggle: darkkhaki/lightsalmon
        intuitive_conf = jg.JsonGrammar(MC6Pro_intuitive.mc6pro_intuitive_schema, minimal=True)
        intuitive_file = jg.JsonGrammarFile(filename='Configs/ColorsTest1.yaml')
        intuitive_model = intuitive_conf.parse_config(intuitive_file.load())
        base_model = intuitive_model.to_base()
        navigator_bank = base_model.banks[0]
        self.check_bank(navigator_bank, "steelblue", "lightsteelblue")
        self.check_preset(navigator_bank.presets[0], "tan", "brown",
                          "cornsilk", "maroon")
        self.check_preset(navigator_bank.presets[1], "tan", "brown",
                          "cornsilk", "maroon")
        bank_one = base_model.banks[1]
        self.check_bank(bank_one, "orange", "red")
        self.check_preset(bank_one.presets[0], "skyblue", "deeppink",
                          "olivedrab", "mediumslateblue")
        self.check_preset(bank_one.presets[1], "khaki", "darkkhaki",
                          "lightyellow", "lightsalmon")
        self.check_preset(bank_one.presets[2], "tan", "brown",
                          "cornsilk", "maroon")
        bank_two = base_model.banks[2]
        self.check_bank(bank_two, "blueviolet", "thistle")
        self.check_preset(bank_two.presets[0], "darkseagreen", "forestgreen",
                          "olive", "indigo")
        self.check_preset(bank_two.presets[1], "khaki", "darkkhaki",
                          "lightyellow", "lightsalmon")
        self.check_preset(bank_two.presets[2], "tan", "brown",
                          "cornsilk", "maroon")

    def test_inheritance2(self):
        # Navigator schema:
        #   Bank: steelblue/lightsteelblue
        #   Preset: tan/cornsilk
        #   Preset Toggle: brown/maroon
        # Default schema:
        #   Bank: None/None
        #   Preset: None/None
        #   Preset Toggle: None/NOne
        # Bank 2 schema:
        #   Bank: blueviolet/thistle
        #   Preset: darkseagreen/olive
        #   Preset Toggle: forestgreen/indigo
        # Preset 2 schema:
        #   Preset: khaki/lightyellow
        #   Preset Toggle: darkkhaki/lightsalmon
        intuitive_conf = jg.JsonGrammar(MC6Pro_intuitive.mc6pro_intuitive_schema, minimal=True)
        intuitive_file = jg.JsonGrammarFile(filename='Configs/ColorsTest2.yaml')
        intuitive_model = intuitive_conf.parse_config(intuitive_file.load())
        base_model = intuitive_model.to_base()
        navigator_bank = base_model.banks[0]
        self.check_bank(navigator_bank, "steelblue", "lightsteelblue")
        self.check_preset(navigator_bank.presets[0], "tan", "brown",
                          "cornsilk", "maroon")
        self.check_preset(navigator_bank.presets[1], "tan", "brown",
                          "cornsilk", "maroon")
        bank_one = base_model.banks[1]
        self.check_bank(bank_one, None, None)
        self.check_preset(bank_one.presets[0], None, None,
                          None, None)
        self.check_preset(bank_one.presets[1], "khaki", "darkkhaki",
                          "lightyellow", "lightsalmon")
        self.check_preset(bank_one.presets[2], "tan", "brown",
                          "cornsilk", "maroon")
        bank_two = base_model.banks[2]
        self.check_bank(bank_two, "blueviolet", "thistle")
        self.check_preset(bank_two.presets[0], "darkseagreen", "forestgreen",
                          "olive", "indigo")
        self.check_preset(bank_two.presets[1], "khaki", "darkkhaki",
                          "lightyellow", "lightsalmon")
        self.check_preset(bank_two.presets[2], "tan", "brown",
                          "cornsilk", "maroon")

    def test_inheritance3(self):
        # Navigator schema: same as default
        # Default schema:
        #   Bank: orange/red
        #   Preset: skyblue/olivedrab
        #   Preset Toggle: deeppink/mediumslateblue
        # Bank 2 schema:
        #   Bank: blueviolet/thistle
        #   Preset: darkseagreen/olive
        #   Preset Toggle: forestgreen/indigo
        # Preset 2 schema:
        #   Preset: khaki/lightyellow
        #   Preset Toggle: darkkhaki/lightsalmon
        intuitive_conf = jg.JsonGrammar(MC6Pro_intuitive.mc6pro_intuitive_schema, minimal=True)
        intuitive_file = jg.JsonGrammarFile(filename='Configs/ColorsTest3.yaml')
        intuitive_model = intuitive_conf.parse_config(intuitive_file.load())
        base_model = intuitive_model.to_base()
        navigator_bank = base_model.banks[0]
        self.check_bank(navigator_bank, "orange", "red")
        self.check_preset(navigator_bank.presets[0], "skyblue", "deeppink",
                          "olivedrab", "mediumslateblue")
        self.check_preset(navigator_bank.presets[1], "skyblue", "deeppink",
                          "olivedrab", "mediumslateblue")
        bank_one = base_model.banks[1]
        self.check_bank(bank_one, "orange", "red")
        self.check_preset(bank_one.presets[0], "skyblue", "deeppink",
                          "olivedrab", "mediumslateblue")
        self.check_preset(bank_one.presets[1], "khaki", "darkkhaki",
                          "lightyellow", "lightsalmon")
        self.check_preset(bank_one.presets[2], "skyblue", "deeppink",
                          "olivedrab", "mediumslateblue")
        bank_two = base_model.banks[2]
        self.check_bank(bank_two, "blueviolet", "thistle")
        self.check_preset(bank_two.presets[0], "darkseagreen", "forestgreen",
                          "olive", "indigo")
        self.check_preset(bank_two.presets[1], "khaki", "darkkhaki",
                          "lightyellow", "lightsalmon")
        self.check_preset(bank_two.presets[2], "skyblue", "deeppink",
                          "olivedrab", "mediumslateblue")

    def test_inheritance4(self):
        # Navigator schema: None
        # Default schema: None
        # Bank 2 schema:
        #   Bank: blueviolet/thistle
        #   Preset: darkseagreen/olive
        #   Preset Toggle: forestgreen/indigo
        # Preset 2 schema:
        #   Preset: khaki/lightyellow
        #   Preset Toggle: darkkhaki/lightsalmon
        intuitive_conf = jg.JsonGrammar(MC6Pro_intuitive.mc6pro_intuitive_schema, minimal=True)
        intuitive_file = jg.JsonGrammarFile(filename='Configs/ColorsTest4.yaml')
        intuitive_model = intuitive_conf.parse_config(intuitive_file.load())
        base_model = intuitive_model.to_base()
        navigator_bank = base_model.banks[0]
        self.check_bank(navigator_bank, None, None)
        self.check_preset(navigator_bank.presets[0], None, None,
                          None, None)
        self.check_preset(navigator_bank.presets[1], None, None,
                          None, None)
        bank_one = base_model.banks[1]
        self.check_bank(bank_one, None, None)
        self.check_preset(bank_one.presets[0], None, None,
                          None, None)
        self.check_preset(bank_one.presets[1], "khaki", "darkkhaki",
                          "lightyellow", "lightsalmon")
        self.check_preset(bank_one.presets[2], None, None,
                          None, None)
        bank_two = base_model.banks[2]
        self.check_bank(bank_two, "blueviolet", "thistle")
        self.check_preset(bank_two.presets[0], "darkseagreen", "forestgreen",
                          "olive", "indigo")
        self.check_preset(bank_two.presets[1], "khaki", "darkkhaki",
                          "lightyellow", "lightsalmon")
        self.check_preset(bank_two.presets[2], "darkseagreen", "forestgreen",
                          "olive", "indigo")


class IntuitiveFromBaseTestCase(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(IntuitiveFromBaseTestCase, self).__init__(*args, **kwargs)
        self.midi_channels = []
        for i in range(1, 4):
            midi_channel = intuitive_midi_channel.IntuitiveMidiChannel()
            midi_channel.name = 'channel' + str(i)
            self.midi_channels.append(midi_channel)
        self.catalog = MC6Pro_intuitive.MessageCatalog()

    @staticmethod
    def mk_base_method(channel, base_type, msg_array):
        base_message = MC6Pro_grammar.MidiMessage()
        base_message.channel = channel
        base_message.type = base_type
        base_message.msg_array_data = msg_array
        return base_message

    @staticmethod
    def mk_message(name, channel, message_type, number, value):
        message = im.IntuitiveMessage()
        message.name = name
        message.type = message_type
        if message_type == 'PC':
            message.specific_message = im.PCModel()
        elif message_type == 'CC':
            message.specific_message = im.CCModel()
            message.specific_message.value = value
        else:
            raise ValueError('not implemented')
        message.specific_message.channel = channel
        message.specific_message.number = number
        return message

    def test_intuitive_midi_message(self):
        # Test adding the first MIDI message
        base_message = self.mk_base_method(None, 1, [None, None])
        message = im.IntuitiveMessage()
        self.assertEqual(message.from_base(base_message, None, self.catalog, None, self.midi_channels), "PC:channel1:0")
        result_message = self.mk_message("PC:channel1:0", 'channel1', 'PC', 0, None)
        result = {"PC:channel1:0": result_message}
        self.assertEqual(self.catalog.catalog, result)

        # Test adding a second message
        base_message = self.mk_base_method(1, 2, [0, 0])
        message = im.IntuitiveMessage()
        self.assertEqual(message.from_base(base_message, None, self.catalog, None, self.midi_channels),
                         "CC:channel1:0:0")
        result_message = self.mk_message("CC:channel1:0:0", 'channel1', 'CC', 0, 0)
        result["CC:channel1:0:0"] = result_message
        self.assertEqual(self.catalog.catalog, result)

        # Test adding a third message
        base_message = self.mk_base_method(2, 2, [2, 3])
        message = im.IntuitiveMessage()
        self.assertEqual(message.from_base(base_message, None, self.catalog, None, self.midi_channels),
                         "CC:channel2:2:3")
        result_message = self.mk_message("CC:channel2:2:3", 'channel2', 'CC', 2, 3)
        result["CC:channel2:2:3"] = result_message
        self.assertEqual(self.catalog.catalog, result)

        # Test found under same name, same value
        message = im.IntuitiveMessage()
        self.assertEqual(message.from_base(base_message, None, self.catalog, None, self.midi_channels),
                         "CC:channel2:2:3")
        self.assertEqual(self.catalog.catalog, result)

        # Test found under same name, different value
        self.catalog.catalog["CC:channel2:2:3"] = self.catalog.catalog["CC:channel1:0:0"]
        message = im.IntuitiveMessage()
        with self.assertRaises(IntuitiveException) as context:
            message.from_base(base_message, None, self.catalog, None, self.midi_channels)
        self.assertEqual(context.exception.args[0], 'name_appears')

        # Test found under different name, same value
        base_message = self.mk_base_method(3, 2, [4, 5])
        result_message = self.mk_message("foo", 'channel3', 'CC', 4, 5)
        self.catalog.add(result_message)
        message = im.IntuitiveMessage()
        self.assertEqual(message.from_base(base_message, None, self.catalog, None, self.midi_channels),
                         "foo")

    def test_different_midi_messages(self):
        # Test PC
        base_message = self.mk_base_method(1, 1, [3])
        message = im.IntuitiveMessage()
        self.assertEqual(message.from_base(base_message, None, self.catalog, None,  self.midi_channels),
                         "PC:channel1:3")
        self.assertEqual(message.specific_message.channel, 'channel1')
        self.assertEqual(message.specific_message.number, 3)
        self.assertEqual(message.type, 'PC')

        # Test CC
        base_message = self.mk_base_method(2, 2, [4, 5])
        message = im.IntuitiveMessage()
        self.assertEqual(message.from_base(base_message, None, self.catalog, None, self.midi_channels),
                         "CC:channel2:4:5")
        self.assertEqual(message.specific_message.channel, 'channel2')
        self.assertEqual(message.specific_message.number, 4)
        self.assertEqual(message.specific_message.value, 5)
        self.assertEqual(message.type, 'CC')

        # Test Bank Jump
        base_message = self.mk_base_method(None, 13, [4, None, 14])
        message = im.IntuitiveMessage()
        banks = [None, None, None, None, 'Bank 5']
        self.assertEqual(message.from_base(base_message, None, self.catalog, banks, self.midi_channels),
                         "Bank Jump:Bank 5:2")
        self.assertEqual(message.type, 'Bank Jump')
        self.assertEqual(message.specific_message.bank, 'Bank 5')
        self.assertEqual(message.specific_message.page, 2)

        # Test Toggle Page
        base_message = self.mk_base_method(None, 14, [6])
        message = im.IntuitiveMessage()
        self.assertEqual(message.from_base(base_message, None, self.catalog, None, self.midi_channels),
                         "Page Jump:3")
        self.assertEqual(message.type, 'Page Jump')
        self.assertEqual(message.specific_message.page, 3)

    # No tests written yet
    def test_intuitive_message(self):
        self.assertEqual(True, True)

    # No tests written yet
    def test_intuitive_preset(self):
        self.assertEqual(True, True)

    # No tests written yet
    def test_intuitive_bank(self):
        self.assertEqual(True, True)

    # No tests written yet
    def test_intuitive_midi_channel(self):
        self.assertEqual(True, True)


class IntuitiveToBaseTestCase(unittest.TestCase):
    # No tests written yet
    def test_intuitive_midi_message(self):
        self.assertEqual(True, True)

    # No tests written yet
    def test_intuitive_message(self):
        self.assertEqual(True, True)

    # No tests written yet
    def test_intuitive_preset(self):
        self.assertEqual(True, True)

    # No tests written yet
    def test_intuitive_bank(self):
        self.assertEqual(True, True)

    # No tests written yet
    def test_intuitive_midi_channel(self):
        self.assertEqual(True, True)

    # No tests written yet
    def test_intuitive(self):
        self.assertEqual(True, True)


class IntuitiveVersionTestCase(unittest.TestCase):
    def test_version(self):
        current_version = MC6Pro_intuitive.intuitive_version
        self.assertEqual(MC6Pro_intuitive.version_verify(current_version, None, []), current_version)

        # This should be done with bumps, once we reach a major version
        with self.assertRaises(jg.JsonGrammarException) as context:
            MC6Pro_intuitive.version_verify("0.2.0", None, [])
        self.assertEqual('bad_version', context.exception.args[0])


class MC6ProIntuitiveTestCase(unittest.TestCase):

    # Recursive json comparator, allows skipping certain keys
    # locator is the bread crumb trail
    def same_json(self, json1, json2, locator, skip_keys):
        if isinstance(json1, dict):
            locator += '{'
            self.assertTrue(isinstance(json2, dict), locator)
            self.assertEqual(json1.keys(), json2.keys(), locator)
            for key in json1.keys():
                if key not in skip_keys:
                    self.same_json(json1[key], json2[key], locator + str(key) + ' ', skip_keys)
        elif isinstance(json1, int):
            self.assertTrue(isinstance(json2, int), locator)
            self.assertEqual(json1, json2, locator)
        elif isinstance(json1, str):
            self.assertTrue(isinstance(json2, str), locator)
            self.assertEqual(json1, json2, locator)
        elif isinstance(json1, list):
            self.assertTrue(isinstance(json2, list), locator)
            self.assertEqual(len(json1), len(json2), locator + " lists different length")
            for list_pos, list_elem in enumerate(json1):
                self.same_json(list_elem, json2[list_pos], locator + '[(' + str(list_pos) + ')', skip_keys)
        else:
            self.assertTrue(False, "Unknown type: " + str(type(json1)))

    def process_one_file(self, filename, extension, skip_final=False, setlist=False):
        # Parse the base config file into a base model
        # Convert the base model into an intuitive model
        # Write the intuitive model to an intuitive config file
        # Load the intuitive config file to an intuitive model
        # Compare the reloaded intuitive model to the original
        # Convert the reloaded intuitive model to a base model
        # Compare the reloaded base model to the original base model
        # Save the base model into a base config file
        # Load the new base config file back into a base model
        # Compare against the original base model
        orig_base_config_filename = "Configs/" + filename + ".json"
        intuitive_config_filename = "tmp/" + filename + "_intuitive." + extension
        new_base_config_filename = "tmp/" + filename + ".json"
        base_grammar = jg.JsonGrammar(MC6Pro_grammar.mc6pro_schema)
        base_file = jg.JsonGrammarFile(filename=orig_base_config_filename)
        orig_base_model = base_grammar.parse_config(base_file.load())
        self.assertEqual(orig_base_model.modified, True)

        # Convert the config model into an intuitive model
        orig_int_model = MC6Pro_intuitive.MC6ProIntuitive()
        orig_int_model.from_base(orig_base_model)

        # Save the intuitive model to a file
        int_grammar = jg.JsonGrammar(MC6Pro_intuitive.mc6pro_intuitive_schema, True)
        int_file = jg.JsonGrammarFile(filename=intuitive_config_filename)
        int_file.save(int_grammar.gen_config(orig_int_model))

        # Load the intuitive string back to a model
        reloaded_int_grammar = jg.JsonGrammar(MC6Pro_intuitive.mc6pro_intuitive_schema, True)
        reloaded_int_file = jg.JsonGrammarFile(intuitive_config_filename)
        reloaded_int_model = reloaded_int_grammar.parse_config(reloaded_int_file.load())

        # Compare the reloaded model
        if reloaded_int_model is None:
            reloaded_int_model = MC6Pro_intuitive.MC6ProIntuitive()
        self.assertEqual(reloaded_int_model, orig_int_model)

        # Convert the reloaded int model to a config model
        reloaded_base_model = reloaded_int_model.to_base()

        # And compare it to the original config model
        if setlist:
            reloaded_base_model.midi_channels = None
        self.assertEqual(reloaded_base_model, orig_base_model)

        # Save a new config file
        reloaded_base_file_grammar = jg.JsonGrammar(MC6Pro_grammar.mc6pro_schema)
        reloaded_base_file = jg.JsonGrammarFile(filename=new_base_config_filename)
        reloaded_base_file.save(reloaded_base_file_grammar.gen_config(reloaded_base_model))

        # Load the new config file
        rereloaded_base_grammar = jg.JsonGrammar(MC6Pro_grammar.mc6pro_schema)
        rereloaded_base_file = jg.JsonGrammarFile(filename=new_base_config_filename)
        rereloaded_base_model = rereloaded_base_grammar.parse_config(rereloaded_base_file.load())
        self.assertEqual(rereloaded_base_model, orig_base_model)

        # Make sure the raw json is the same
        # Get rid of fields that complicate things
        if skip_final:
            return
        rereloaded_data = rereloaded_base_file.load()
        base_data = base_file.load()
        rereloaded_data['downloadDate'] = ''
        rereloaded_data['hash'] = 0
        base_data['downloadDate'] = ''
        base_data['hash'] = 0
        if 'controller_settings' in base_data['data']:
            # the midi clock output ports only care about the 11 LSBs
            controller_settings = base_data['data']['controller_settings']['data']['controller_settings']
            base_midi_clock_output_ports = controller_settings['data']['midiClockOutputPorts']
            new2_base_midi_clock_output_ports = \
                rereloaded_data['data']['controller_settings']['data']['controller_settings']['data'][
                    'midiClockOutputPorts']
            output_ports = base_midi_clock_output_ports & new2_base_midi_clock_output_ports & 2047
            self.assertEqual(output_ports, 2047)
            controller_settings['data']['midiClockOutputPorts'] = output_ports
            rereloaded_data['data']['controller_settings']['data']['controller_settings']['data'][
                'midiClockOutputPorts'] = \
                output_ports
        else:
            rereloaded_data['data'].pop('controller_settings')
        self.same_json(base_data, rereloaded_data, '',
                       ['bankMsgArray', 'sequencer_engines'])

    def test_configs_empty(self):
        self.process_one_file("Empty", "yaml")
        self.process_one_file("Empty", "json")

    def test_configs_features(self):
        self.process_one_file("Features", "yaml", True)
        self.process_one_file("Features", "json", True)

    def test_configs_MIDIClock(self):
        self.process_one_file("MIDIClock", "yaml", True)
        self.process_one_file("MIDIClock", "json", True)

    def test_configs_waveform_sequence(self):
        self.process_one_file("WaveformSequence", "yaml", True, setlist=True)
        self.process_one_file("WaveformSequence", "json", True, setlist=True)

    def test_configs_set_toggle(self):
        self.process_one_file("SetToggle", "yaml")
        self.process_one_file("Settoggle", "json")

    def test_configs_select_exp_message(self):
        self.process_one_file("SelectExpMessage", "yaml", setlist=True)
        self.process_one_file("SelectExpMessage", "json", setlist=True)

    def test_demo(self):
        base_conf = jg.JsonGrammar(MC6Pro_grammar.mc6pro_schema)
        base_file = jg.JsonGrammarFile('tmp/Demo_test.json')
        intuitive_conf = jg.JsonGrammar(MC6Pro_intuitive.mc6pro_intuitive_schema, minimal=True)
        intuitive_file = jg.JsonGrammarFile('Configs/Demo.yaml')
        intuitive_model = intuitive_conf.parse_config(intuitive_file.load())
        base_model = intuitive_model.to_base()
        self.assertIsNotNone(base_model)
        base_file.save(base_conf.gen_config(base_model))


class MC6ProNavigatorTestCase(unittest.TestCase):
    navigator_banks_one_button = [
        ["Home",
         ["Bank 1", "Bank 2", "Bank 3", "Bank 4", "Bank 5", "Next",
          "Bank 6", "Bank 7", "Bank 8", "Bank 9", "Bank 10", "Previous/Next",
          "Bank 11", "Bank 12", "Bank 13", "Bank 14", "Bank 15", "Previous/Next",
          "Bank 16", "Bank 17", "Bank 18", "Bank 19", "Bank 20", "Previous/Next"]
         ],
        ["Home (2)",
         ["Bank 21", "Bank 22", "Bank 23", "Bank 24", "Bank 25", "Previous/Next",
          "Bank 26", "Bank 27", "Bank 28", "Bank 29", "Bank 30", "Previous"]
         ],
        ["Bank 1",
         ['', '', '', '', '', 'Home']
         ],
        ["Bank 2",
         ['Preset 1', '', '', '', '', 'Home']
         ],
        ["Bank 3",
         ['Preset 1', 'Preset 2', '', '', '', 'Home']
         ],
        ["Bank 4",
         ['Preset 1', 'Preset 2', 'Preset 3', '', '', 'Home']
         ],
        ["Bank 5",
         ['Preset 1', 'Preset 2', 'Preset 3', 'Preset 4', '', 'Home']
         ],
        ["Bank 6",
         ['Preset 1', 'Preset 2', 'Preset 3', 'Preset 4', 'Preset 5', 'Home']
         ],
        ["Bank 7",
         ['Preset 1', 'Preset 2', 'Preset 3', 'Preset 4', 'Preset 5', 'Home/Next',
          'Preset 6', '', '', '', '', 'Previous']
         ],
        ["Bank 8",
         ['Preset 1', 'Preset 2', 'Preset 3', 'Preset 4', 'Preset 5', 'Home/Next',
          'Preset 6', 'Preset 7', '', '', '', 'Previous']
         ],
        ["Bank 9",
         ['Preset 1', 'Preset 2', 'Preset 3', 'Preset 4', 'Preset 5', 'Home/Next',
          'Preset 6', 'Preset 7', 'Preset 8', '', '', 'Previous']
         ],
        ["Bank 10",
         ['Preset 1', 'Preset 2', 'Preset 3', 'Preset 4', 'Preset 5', 'Home/Next',
          'Preset 6', 'Preset 7', 'Preset 8', 'Preset 9', '', 'Previous']
         ],
        ["Bank 11",
         ['Preset 1', 'Preset 2', 'Preset 3', 'Preset 4', 'Preset 5', 'Home/Next',
          'Preset 6', 'Preset 7', 'Preset 8', 'Preset 9', 'Preset 10', 'Previous']
         ],
        ["Bank 12",
         ['Preset 1', 'Preset 2', 'Preset 3', 'Preset 4', 'Preset 5', 'Home/Next',
          'Preset 6', 'Preset 7', 'Preset 8', 'Preset 9', 'Preset 10', 'Previous/Next',
          'Preset 11', '', '', '', '', 'Previous']
         ],
        ["Bank 13",
         ['Preset 1', 'Preset 2', 'Preset 3', 'Preset 4', 'Preset 5', 'Home/Next',
          'Preset 6', 'Preset 7', 'Preset 8', 'Preset 9', 'Preset 10', 'Previous/Next',
          'Preset 11', 'Preset 12', '', '', '', 'Previous']
         ],
        ["Bank 14",
         ['Preset 1', 'Preset 2', 'Preset 3', 'Preset 4', 'Preset 5', 'Home/Next',
          'Preset 6', 'Preset 7', 'Preset 8', 'Preset 9', 'Preset 10', 'Previous/Next',
          'Preset 11', 'Preset 12', 'Preset 13', '', '', 'Previous']
         ],
        ["Bank 15",
         ['Preset 1', 'Preset 2', 'Preset 3', 'Preset 4', 'Preset 5', 'Home/Next',
          'Preset 6', 'Preset 7', 'Preset 8', 'Preset 9', 'Preset 10', 'Previous/Next',
          'Preset 11', 'Preset 12', 'Preset 13', 'Preset 14', '', 'Previous']
         ],
        ["Bank 16",
         ['Preset 1', 'Preset 2', 'Preset 3', 'Preset 4', 'Preset 5', 'Home/Next',
          'Preset 6', 'Preset 7', 'Preset 8', 'Preset 9', 'Preset 10', 'Previous/Next',
          'Preset 11', 'Preset 12', 'Preset 13', 'Preset 14', 'Preset 15', 'Previous']
         ],
        ["Bank 17",
         ['Preset 1', 'Preset 2', 'Preset 3', 'Preset 4', 'Preset 5', 'Home/Next',
          'Preset 6', 'Preset 7', 'Preset 8', 'Preset 9', 'Preset 10', 'Previous/Next',
          'Preset 11', 'Preset 12', 'Preset 13', 'Preset 14', 'Preset 15', 'Previous/Next',
          'Preset 16', '', '', '', '', 'Previous']
         ],
        ["Bank 18",
         ['Preset 1', 'Preset 2', 'Preset 3', 'Preset 4', 'Preset 5', 'Home/Next',
          'Preset 6', 'Preset 7', 'Preset 8', 'Preset 9', 'Preset 10', 'Previous/Next',
          'Preset 11', 'Preset 12', 'Preset 13', 'Preset 14', 'Preset 15', 'Previous/Next',
          'Preset 16', 'Preset 17', '', '', '', 'Previous']
         ],
        ["Bank 19",
         ['Preset 1', 'Preset 2', 'Preset 3', 'Preset 4', 'Preset 5', 'Home/Next',
          'Preset 6', 'Preset 7', 'Preset 8', 'Preset 9', 'Preset 10', 'Previous/Next',
          'Preset 11', 'Preset 12', 'Preset 13', 'Preset 14', 'Preset 15', 'Previous/Next',
          'Preset 16', 'Preset 17', 'Preset 18', '', '', 'Previous']
         ],
        ["Bank 20",
         ['Preset 1', 'Preset 2', 'Preset 3', 'Preset 4', 'Preset 5', 'Home/Next',
          'Preset 6', 'Preset 7', 'Preset 8', 'Preset 9', 'Preset 10', 'Previous/Next',
          'Preset 11', 'Preset 12', 'Preset 13', 'Preset 14', 'Preset 15', 'Previous/Next',
          'Preset 16', 'Preset 17', 'Preset 18', 'Preset 19', '', 'Previous']
         ],
        ["Bank 21",
         ['Preset 1', 'Preset 2', 'Preset 3', 'Preset 4', 'Preset 5', 'Home/Next',
          'Preset 6', 'Preset 7', 'Preset 8', 'Preset 9', 'Preset 10', 'Previous/Next',
          'Preset 11', 'Preset 12', 'Preset 13', 'Preset 14', 'Preset 15', 'Previous/Next',
          'Preset 16', 'Preset 17', 'Preset 18', 'Preset 19', 'Preset 20', 'Previous']
         ],
        ["Bank 22",
         ['Preset 1', 'Preset 2', 'Preset 3', 'Preset 4', 'Preset 5', 'Home/Next',
          'Preset 6', 'Preset 7', 'Preset 8', 'Preset 9', 'Preset 10', 'Previous/Next',
          'Preset 11', 'Preset 12', 'Preset 13', 'Preset 14', 'Preset 15', 'Previous/Next',
          'Preset 16', 'Preset 17', 'Preset 18', 'Preset 19', 'Preset 20', 'Previous/Next']
         ],
        ["Bank 22 (2)",
         ['Preset 21', '', '', '', '', 'Previous']
         ],
        ["Bank 23",
         ['Preset 1', 'Preset 2', 'Preset 3', 'Preset 4', 'Preset 5', 'Home/Next',
          'Preset 6', 'Preset 7', 'Preset 8', 'Preset 9', 'Preset 10', 'Previous/Next',
          'Preset 11', 'Preset 12', 'Preset 13', 'Preset 14', 'Preset 15', 'Previous/Next',
          'Preset 16', 'Preset 17', 'Preset 18', 'Preset 19', 'Preset 20', 'Previous/Next']
         ],
        ["Bank 23 (2)",
         ['Preset 21', 'Preset 22', '', '', '', 'Previous']
         ],
        ["Bank 24",
         ['Preset 1', 'Preset 2', 'Preset 3', 'Preset 4', 'Preset 5', 'Home/Next',
          'Preset 6', 'Preset 7', 'Preset 8', 'Preset 9', 'Preset 10', 'Previous/Next',
          'Preset 11', 'Preset 12', 'Preset 13', 'Preset 14', 'Preset 15', 'Previous/Next',
          'Preset 16', 'Preset 17', 'Preset 18', 'Preset 19', 'Preset 20', 'Previous/Next']
         ],
        ["Bank 24 (2)",
         ['Preset 21', 'Preset 22', 'Preset 23', '', '', 'Previous']
         ],
        ["Bank 25",
         ['Preset 1', 'Preset 2', 'Preset 3', 'Preset 4', 'Preset 5', 'Home/Next',
          'Preset 6', 'Preset 7', 'Preset 8', 'Preset 9', 'Preset 10', 'Previous/Next',
          'Preset 11', 'Preset 12', 'Preset 13', 'Preset 14', 'Preset 15', 'Previous/Next',
          'Preset 16', 'Preset 17', 'Preset 18', 'Preset 19', 'Preset 20', 'Previous/Next']
         ],
        ["Bank 25 (2)",
         ['Preset 21', 'Preset 22', 'Preset 23', 'Preset 24', '', 'Previous']
         ],
        ["Bank 26",
         ['Preset 1', 'Preset 2', 'Preset 3', 'Preset 4', 'Preset 5', 'Home/Next',
          'Preset 6', 'Preset 7', 'Preset 8', 'Preset 9', 'Preset 10', 'Previous/Next',
          'Preset 11', 'Preset 12', 'Preset 13', 'Preset 14', 'Preset 15', 'Previous/Next',
          'Preset 16', 'Preset 17', 'Preset 18', 'Preset 19', 'Preset 20', 'Previous/Next']
         ],
        ["Bank 26 (2)",
         ['Preset 21', 'Preset 22', 'Preset 23', 'Preset 24', 'Preset 25', 'Previous']
         ],
        ["Bank 27",
         ['Preset 1', 'Preset 2', 'Preset 3', 'Preset 4', 'Preset 5', 'Home/Next',
          'Preset 6', 'Preset 7', 'Preset 8', 'Preset 9', 'Preset 10', 'Previous/Next',
          'Preset 11', 'Preset 12', 'Preset 13', 'Preset 14', 'Preset 15', 'Previous/Next',
          'Preset 16', 'Preset 17', 'Preset 18', 'Preset 19', 'Preset 20', 'Previous/Next']
         ],
        ["Bank 27 (2)",
         ['Preset 21', 'Preset 22', 'Preset 23', 'Preset 24', 'Preset 25', 'Previous/Next',
          'Preset 26', '', '', '', '', 'Previous']
         ],
        ["Bank 28",
         ['Preset 1', 'Preset 2', 'Preset 3', 'Preset 4', 'Preset 5', 'Home/Next',
          'Preset 6', 'Preset 7', 'Preset 8', 'Preset 9', 'Preset 10', 'Previous/Next',
          'Preset 11', 'Preset 12', 'Preset 13', 'Preset 14', 'Preset 15', 'Previous/Next',
          'Preset 16', 'Preset 17', 'Preset 18', 'Preset 19', 'Preset 20', 'Previous/Next']
         ],
        ["Bank 28 (2)",
         ['Preset 21', 'Preset 22', 'Preset 23', 'Preset 24', 'Preset 25', 'Previous/Next',
          'Preset 26', 'Preset 27', '', '', '', 'Previous']
         ],
        ["Bank 29",
         ['Preset 1', 'Preset 2', 'Preset 3', 'Preset 4', 'Preset 5', 'Home/Next',
          'Preset 6', 'Preset 7', 'Preset 8', 'Preset 9', 'Preset 10', 'Previous/Next',
          'Preset 11', 'Preset 12', 'Preset 13', 'Preset 14', 'Preset 15', 'Previous/Next',
          'Preset 16', 'Preset 17', 'Preset 18', 'Preset 19', 'Preset 20', 'Previous/Next']
         ],
        ["Bank 29 (2)",
         ['Preset 21', 'Preset 22', 'Preset 23', 'Preset 24', 'Preset 25', 'Previous/Next',
          'Preset 26', 'Preset 27', 'Preset 28', '', '', 'Previous']
         ],
        ["Bank 30",
         ['Preset 1', 'Preset 2', 'Preset 3', 'Preset 4', 'Preset 5', 'Home/Next',
          'Preset 6', 'Preset 7', 'Preset 8', 'Preset 9', 'Preset 10', 'Previous/Next',
          'Preset 11', 'Preset 12', 'Preset 13', 'Preset 14', 'Preset 15', 'Previous/Next',
          'Preset 16', 'Preset 17', 'Preset 18', 'Preset 19', 'Preset 20', 'Previous/Next']
         ],
        ["Bank 30 (2)",
         ['Preset 21', 'Preset 22', 'Preset 23', 'Preset 24', 'Preset 25', 'Previous/Next',
          'Preset 26', 'Preset 27', 'Preset 28', 'Preset 29', '', 'Previous']
         ]
    ]

    navigator_banks_two_button = [
        ["Home",
         ["Bank 1", "Bank 2", "Bank 3", "Bank 4", "Bank 5", "Next",
          "Bank 6", "Bank 7", "Previous", "Bank 8", "Bank 9", "Next",
          "Bank 10", "Bank 11", "Previous", "Bank 12", "Bank 13", "Next",
          "Bank 14", "Bank 15", "Previous", "Bank 16", "Bank 17", "Next"]
         ],
        ["Home (2)",
         ["Bank 18", "Bank 19", "Previous", "Bank 20", "Bank 21", "Next",
          "Bank 22", "Bank 23", "Previous", "Bank 24", "Bank 25", "Next",
          "Bank 26", "Bank 27", "Previous", "Bank 28", "Bank 29", "Bank 30"
          ]
         ],
        ["Bank 1",
         ['', '', 'Home']
         ],
        ["Bank 2",
         ['Preset 1', '', 'Home']
         ],
        ["Bank 3",
         ['Preset 1', 'Preset 2', 'Home']
         ],
        ["Bank 4",
         ['Preset 1', 'Preset 2', 'Home', 'Preset 3']
         ],
        ["Bank 5",
         ['Preset 1', 'Preset 2', 'Home', 'Preset 3', 'Preset 4']
         ],
        ["Bank 6",
         ['Preset 1', 'Preset 2', 'Home', 'Preset 3', 'Preset 4', 'Preset 5']
         ],
        ["Bank 7",
         ['Preset 1', 'Preset 2', 'Home', 'Preset 3', 'Preset 4', 'Next',
          'Preset 5', 'Preset 6', 'Previous']
         ],
        ["Bank 8",
         ['Preset 1', 'Preset 2', 'Home', 'Preset 3', 'Preset 4', 'Next',
          'Preset 5', 'Preset 6', 'Previous', 'Preset 7']
         ],
        ["Bank 9",
         ['Preset 1', 'Preset 2', 'Home', 'Preset 3', 'Preset 4', 'Next',
          'Preset 5', 'Preset 6', 'Previous', 'Preset 7', 'Preset 8']
         ],
        ["Bank 10",
         ['Preset 1', 'Preset 2', 'Home', 'Preset 3', 'Preset 4', 'Next',
          'Preset 5', 'Preset 6', 'Previous', 'Preset 7', 'Preset 8', 'Preset 9']
         ],
        ["Bank 11",
         ['Preset 1', 'Preset 2', 'Home', 'Preset 3', 'Preset 4', 'Next',
          'Preset 5', 'Preset 6', 'Previous', 'Preset 7', 'Preset 8', 'Next',
          'Preset 9', 'Preset 10', 'Previous']
         ],
        ["Bank 12",
         ['Preset 1', 'Preset 2', 'Home', 'Preset 3', 'Preset 4', 'Next',
          'Preset 5', 'Preset 6', 'Previous', 'Preset 7', 'Preset 8', 'Next',
          'Preset 9', 'Preset 10', 'Previous', 'Preset 11']
         ],
        ["Bank 13",
         ['Preset 1', 'Preset 2', 'Home', 'Preset 3', 'Preset 4', 'Next',
          'Preset 5', 'Preset 6', 'Previous', 'Preset 7', 'Preset 8', 'Next',
          'Preset 9', 'Preset 10', 'Previous', 'Preset 11', 'Preset 12']
         ],
        ["Bank 14",
         ['Preset 1', 'Preset 2', 'Home', 'Preset 3', 'Preset 4', 'Next',
          'Preset 5', 'Preset 6', 'Previous', 'Preset 7', 'Preset 8', 'Next',
          'Preset 9', 'Preset 10', 'Previous', 'Preset 11', 'Preset 12', 'Preset 13']
         ],
        ["Bank 15",
         ['Preset 1', 'Preset 2', 'Home', 'Preset 3', 'Preset 4', 'Next',
          'Preset 5', 'Preset 6', 'Previous', 'Preset 7', 'Preset 8', 'Next',
          'Preset 9', 'Preset 10', 'Previous', 'Preset 11', 'Preset 12', 'Next',
          'Preset 13', 'Preset 14', 'Previous']
         ],
        ["Bank 16",
         ['Preset 1', 'Preset 2', 'Home', 'Preset 3', 'Preset 4', 'Next',
          'Preset 5', 'Preset 6', 'Previous', 'Preset 7', 'Preset 8', 'Next',
          'Preset 9', 'Preset 10', 'Previous', 'Preset 11', 'Preset 12', 'Next',
          'Preset 13', 'Preset 14', 'Previous', 'Preset 15']
         ],
        ["Bank 17",
         ['Preset 1', 'Preset 2', 'Home', 'Preset 3', 'Preset 4', 'Next',
          'Preset 5', 'Preset 6', 'Previous', 'Preset 7', 'Preset 8', 'Next',
          'Preset 9', 'Preset 10', 'Previous', 'Preset 11', 'Preset 12', 'Next',
          'Preset 13', 'Preset 14', 'Previous', 'Preset 15', 'Preset 16']
         ],
        ["Bank 18",
         ['Preset 1', 'Preset 2', 'Home', 'Preset 3', 'Preset 4', 'Next',
          'Preset 5', 'Preset 6', 'Previous', 'Preset 7', 'Preset 8', 'Next',
          'Preset 9', 'Preset 10', 'Previous', 'Preset 11', 'Preset 12', 'Next',
          'Preset 13', 'Preset 14', 'Previous', 'Preset 15', 'Preset 16', 'Preset 17']
         ],
        ["Bank 19",
         ['Preset 1', 'Preset 2', 'Home', 'Preset 3', 'Preset 4', 'Next',
          'Preset 5', 'Preset 6', 'Previous', 'Preset 7', 'Preset 8', 'Next',
          'Preset 9', 'Preset 10', 'Previous', 'Preset 11', 'Preset 12', 'Next',
          'Preset 13', 'Preset 14', 'Previous', 'Preset 15', 'Preset 16', 'Next']
         ],
        ["Bank 19 (2)",
         ['Preset 17', 'Preset 18', 'Previous']
         ],
        ["Bank 20",
         ['Preset 1', 'Preset 2', 'Home', 'Preset 3', 'Preset 4', 'Next',
          'Preset 5', 'Preset 6', 'Previous', 'Preset 7', 'Preset 8', 'Next',
          'Preset 9', 'Preset 10', 'Previous', 'Preset 11', 'Preset 12', 'Next',
          'Preset 13', 'Preset 14', 'Previous', 'Preset 15', 'Preset 16', 'Next']
         ],
        ["Bank 20 (2)",
         ['Preset 17', 'Preset 18', 'Previous', 'Preset 19']
         ],
        ["Bank 21",
         ['Preset 1', 'Preset 2', 'Home', 'Preset 3', 'Preset 4', 'Next',
          'Preset 5', 'Preset 6', 'Previous', 'Preset 7', 'Preset 8', 'Next',
          'Preset 9', 'Preset 10', 'Previous', 'Preset 11', 'Preset 12', 'Next',
          'Preset 13', 'Preset 14', 'Previous', 'Preset 15', 'Preset 16', 'Next']
         ],
        ["Bank 21 (2)",
         ['Preset 17', 'Preset 18', 'Previous', 'Preset 19', 'Preset 20']
         ],
        ["Bank 22",
         ['Preset 1', 'Preset 2', 'Home', 'Preset 3', 'Preset 4', 'Next',
          'Preset 5', 'Preset 6', 'Previous', 'Preset 7', 'Preset 8', 'Next',
          'Preset 9', 'Preset 10', 'Previous', 'Preset 11', 'Preset 12', 'Next',
          'Preset 13', 'Preset 14', 'Previous', 'Preset 15', 'Preset 16', 'Next']
         ],
        ["Bank 22 (2)",
         ['Preset 17', 'Preset 18', 'Previous', 'Preset 19', 'Preset 20', 'Preset 21']
         ],
        ["Bank 23",
         ['Preset 1', 'Preset 2', 'Home', 'Preset 3', 'Preset 4', 'Next',
          'Preset 5', 'Preset 6', 'Previous', 'Preset 7', 'Preset 8', 'Next',
          'Preset 9', 'Preset 10', 'Previous', 'Preset 11', 'Preset 12', 'Next',
          'Preset 13', 'Preset 14', 'Previous', 'Preset 15', 'Preset 16', 'Next']
         ],
        ["Bank 23 (2)",
         ['Preset 17', 'Preset 18', 'Previous', 'Preset 19', 'Preset 20', 'Next',
          'Preset 21', 'Preset 22', 'Previous']
         ],
        ["Bank 24",
         ['Preset 1', 'Preset 2', 'Home', 'Preset 3', 'Preset 4', 'Next',
          'Preset 5', 'Preset 6', 'Previous', 'Preset 7', 'Preset 8', 'Next',
          'Preset 9', 'Preset 10', 'Previous', 'Preset 11', 'Preset 12', 'Next',
          'Preset 13', 'Preset 14', 'Previous', 'Preset 15', 'Preset 16', 'Next']
         ],
        ["Bank 24 (2)",
         ['Preset 17', 'Preset 18', 'Previous', 'Preset 19', 'Preset 20', 'Next',
          'Preset 21', 'Preset 22', 'Previous', 'Preset 23']
         ],
        ["Bank 25",
         ['Preset 1', 'Preset 2', 'Home', 'Preset 3', 'Preset 4', 'Next',
          'Preset 5', 'Preset 6', 'Previous', 'Preset 7', 'Preset 8', 'Next',
          'Preset 9', 'Preset 10', 'Previous', 'Preset 11', 'Preset 12', 'Next',
          'Preset 13', 'Preset 14', 'Previous', 'Preset 15', 'Preset 16', 'Next']
         ],
        ["Bank 25 (2)",
         ['Preset 17', 'Preset 18', 'Previous', 'Preset 19', 'Preset 20', 'Next',
          'Preset 21', 'Preset 22', 'Previous', 'Preset 23', 'Preset 24']
         ],
        ["Bank 26",
         ['Preset 1', 'Preset 2', 'Home', 'Preset 3', 'Preset 4', 'Next',
          'Preset 5', 'Preset 6', 'Previous', 'Preset 7', 'Preset 8', 'Next',
          'Preset 9', 'Preset 10', 'Previous', 'Preset 11', 'Preset 12', 'Next',
          'Preset 13', 'Preset 14', 'Previous', 'Preset 15', 'Preset 16', 'Next']
         ],
        ["Bank 26 (2)",
         ['Preset 17', 'Preset 18', 'Previous', 'Preset 19', 'Preset 20', 'Next',
          'Preset 21', 'Preset 22', 'Previous', 'Preset 23', 'Preset 24', 'Preset 25']
         ],
        ["Bank 27",
         ['Preset 1', 'Preset 2', 'Home', 'Preset 3', 'Preset 4', 'Next',
          'Preset 5', 'Preset 6', 'Previous', 'Preset 7', 'Preset 8', 'Next',
          'Preset 9', 'Preset 10', 'Previous', 'Preset 11', 'Preset 12', 'Next',
          'Preset 13', 'Preset 14', 'Previous', 'Preset 15', 'Preset 16', 'Next']
         ],
        ["Bank 27 (2)",
         ['Preset 17', 'Preset 18', 'Previous', 'Preset 19', 'Preset 20', 'Next',
          'Preset 21', 'Preset 22', 'Previous', 'Preset 23', 'Preset 24', 'Next',
          'Preset 25', 'Preset 26', 'Previous']
         ],
        ["Bank 28",
         ['Preset 1', 'Preset 2', 'Home', 'Preset 3', 'Preset 4', 'Next',
          'Preset 5', 'Preset 6', 'Previous', 'Preset 7', 'Preset 8', 'Next',
          'Preset 9', 'Preset 10', 'Previous', 'Preset 11', 'Preset 12', 'Next',
          'Preset 13', 'Preset 14', 'Previous', 'Preset 15', 'Preset 16', 'Next']
         ],
        ["Bank 28 (2)",
         ['Preset 17', 'Preset 18', 'Previous', 'Preset 19', 'Preset 20', 'Next',
          'Preset 21', 'Preset 22', 'Previous', 'Preset 23', 'Preset 24', 'Next',
          'Preset 25', 'Preset 26', 'Previous', 'Preset 27']
         ],
        ["Bank 29",
         ['Preset 1', 'Preset 2', 'Home', 'Preset 3', 'Preset 4', 'Next',
          'Preset 5', 'Preset 6', 'Previous', 'Preset 7', 'Preset 8', 'Next',
          'Preset 9', 'Preset 10', 'Previous', 'Preset 11', 'Preset 12', 'Next',
          'Preset 13', 'Preset 14', 'Previous', 'Preset 15', 'Preset 16', 'Next']
         ],
        ["Bank 29 (2)",
         ['Preset 17', 'Preset 18', 'Previous', 'Preset 19', 'Preset 20', 'Next',
          'Preset 21', 'Preset 22', 'Previous', 'Preset 23', 'Preset 24', 'Next',
          'Preset 25', 'Preset 26', 'Previous', 'Preset 27', 'Preset 28']
         ],
        ["Bank 30",
         ['Preset 1', 'Preset 2', 'Home', 'Preset 3', 'Preset 4', 'Next',
          'Preset 5', 'Preset 6', 'Previous', 'Preset 7', 'Preset 8', 'Next',
          'Preset 9', 'Preset 10', 'Previous', 'Preset 11', 'Preset 12', 'Next',
          'Preset 13', 'Preset 14', 'Previous', 'Preset 15', 'Preset 16', 'Next']
         ],
        ["Bank 30 (2)",
         ['Preset 17', 'Preset 18', 'Previous', 'Preset 19', 'Preset 20', 'Next',
          'Preset 21', 'Preset 22', 'Previous', 'Preset 23', 'Preset 24', 'Next',
          'Preset 25', 'Preset 26', 'Previous', 'Preset 27', 'Preset 28', 'Preset 29']
         ]
    ]

    def check_navigator(self, mode, navigator_banks):
        intuitive_conf = jg.JsonGrammar(MC6Pro_intuitive.mc6pro_intuitive_schema, minimal=True)
        intuitive_file = jg.JsonGrammarFile(filename='Configs/NavigatorTest.json')
        intuitive_json = intuitive_file.load()
        intuitive_model = intuitive_conf.parse_config(intuitive_json)
        base_model = intuitive_model.to_base(mode)
        self.assertIsNotNone(base_model)
        for pos, bank in enumerate(base_model.banks):
            if pos < len(navigator_banks):
                self.assertEqual(bank.name, navigator_banks[pos][0])
                for pos2, preset in enumerate(bank.presets):
                    if pos2 < len(navigator_banks[pos][1]):
                        self.assertEqual(preset.short_name, navigator_banks[pos][1][pos2])
                    else:
                        self.assertIsNone(preset)
            else:
                self.assertIsNone(bank)

    def test_navigator_two_button(self):
        self.check_navigator("Two Button", self.navigator_banks_two_button)

    def test_navigator_one_button(self):
        self.check_navigator("One Button", self.navigator_banks_one_button)


if __name__ == '__main__':
    unittest.main()
