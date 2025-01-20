import grammar as jg
import copy
from IntuitiveException import IntuitiveException


class PresetRenameModel(jg.GrammarModel):
    @staticmethod
    def build_from_backup(simple_message, backup_message):
        simple_message.specific_message = PresetRenameModel()
        simple_message.name += simple_message.specific_message.from_backup(backup_message)

    @staticmethod
    def build(new_name):
        result = PresetRenameModel()
        result.new_name = new_name
        return result

    @staticmethod
    def get_case_keys(_intuitive=False):
        return [PresetRenameModel,
                jg.SwitchDict.make_key('new_name', jg.Atom('New Name', str, var='new_name'))]

    def __init__(self):
        super().__init__('PresetRenameModel')
        self.new_name = None

    def __eq__(self, other):
        result = isinstance(other, PresetRenameModel) and self.new_name == other.new_name
        if not result:
            self.modified = True
        return result

    def from_backup(self, backup_message):
        chars = copy.deepcopy(backup_message.msg_array_data)
        jg.prune_list(chars)
        self.new_name = ''.join(map(chr, chars))
        return self.new_name

    def to_backup(self, backup_message, _bank_catalog, _simple_bank, _simple_preset):
        if len(self.new_name) > 18:
            raise IntuitiveException('name too long', 'The name ' + self.new_name + ' is too long')
        data = map(ord, [*self.new_name])
        for i, val in enumerate(data):
            backup_message.msg_array_data[i] = val
