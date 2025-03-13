import grammar as jg
import simple_model


class EngagePresetModel(jg.GrammarModel):
    engage_preset_action = ["No Action", "Press", "Release", "Long Press", "Long Press Scroll", "Long Press Release",
                            "Release All", "Double Tap", "Double Tap Release", "Long Double Tap",
                            "Long Double Tap Release"]
    engage_preset_action_default = engage_preset_action[0]

    @staticmethod
    def build(bank, preset, action):
        result = EngagePresetModel()
        result.bank = bank
        result.preset = preset
        result.action = action
        return result

    @staticmethod
    def build_from_backup(simple_message, backup_message):
        simple_message.specific_message = EngagePresetModel()
        simple_message.name += simple_message.specific_message.from_backup(backup_message)

    @staticmethod
    def get_case_keys(_intuitive=False):
        return [EngagePresetModel,
                jg.SwitchDict.make_key('bank', jg.Atom('Bank', int, var='bank')),
                jg.SwitchDict.make_key('current_bank', jg.Atom('CurrentBank', bool, default=False, var='current_bank')),
                jg.SwitchDict.make_key('preset', jg.Atom('Preset', int, var='preset')),
                jg.SwitchDict.make_key('action',
                                       jg.Enum('Action', EngagePresetModel.engage_preset_action,
                                               EngagePresetModel.engage_preset_action_default,
                                               var='action'))]

    def __init__(self):
        super().__init__('EngagePresetModel')
        self.bank = None
        self.current_bank = None
        self.preset = None
        self.action = None

    def __eq__(self, other):
        result = isinstance(other, EngagePresetModel) and self.bank == other.bank and self.preset == other.preset
        result = result and self.action == other.action and self.current_bank == other.current_bank
        if not result:
            self.modified = True
        return result

    def from_backup(self, backup_message):
        if backup_message.msg_array_data is None:
            self.bank = 0
            self.current_bank = False
            self.preset = 0
            self.action = EngagePresetModel.engage_preset_action_default
        else:
            if backup_message.msg_array_data[0] is None:
                self.bank = 0
            else:
                self.bank = backup_message.msg_array_data[0]
            if backup_message.msg_array_data[1] is None:
                self.preset = 0
            else:
                self.preset = backup_message.msg_array_data[1]
                if self.preset >= 64:
                    self.preset -= 64
                    self.current_bank = True
            if backup_message.msg_array_data[2] is None:
                self.action = simple_model.preset_message_trigger[0]
            else:
                self.action = simple_model.preset_message_trigger[backup_message.msg_array_data[2]]
        if self.current_bank:
            bank_name = 'Current Bank(' + str(self.bank) + ')'
        else:
            bank_name = str(self.bank)
        return bank_name + ':' + str(self.preset) + ':' + self.action

    def to_backup(self, backup_message, _bank_catalog, _simple_bank, _simple_preset):
        bank_number = self.bank
        if bank_number != 0:
            backup_message.msg_array_data[0] = bank_number
        preset = self.preset
        if self.current_bank:
            preset += 64
        if preset != 0:
            backup_message.msg_array_data[1] = preset
        if self.action is not None and self.action != simple_model.preset_message_trigger_default:
            backup_message.msg_array_data[2] = simple_model.preset_message_trigger.index(self.action)
