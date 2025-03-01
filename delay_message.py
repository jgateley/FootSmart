import grammar as jg


class DelayModel(jg.GrammarModel):
    @staticmethod
    def build_from_backup(simple_message, backup_message):
        simple_message.specific_message = DelayModel()
        simple_message.name += simple_message.specific_message.from_backup(backup_message)

    @staticmethod
    def build(delay_ms):
        result = DelayModel()
        result.delay = delay_ms
        return result

    @staticmethod
    def make(delay_ms):
        result = DelayModel()
        result.delay = delay_ms
        return result

    @staticmethod
    def get_case_keys(_intuitive=False):
        return [DelayModel,
                jg.SwitchDict.make_key('delay', jg.Atom('Delay', int, var='delay'))]

    def __init__(self):
        super().__init__('DelayModel')
        self.delay = None

    def __eq__(self, other):
        result = isinstance(other, DelayModel) and self.delay == other.delay
        if not result:
            self.modified = True
        return result

    def from_backup(self, backup_message):
        if backup_message.msg_array_data is None or backup_message.msg_array_data[0] is None:
            self.delay = 0
        else:
            self.delay = backup_message.msg_array_data[0] * 10
        return str(self.delay)

    def to_backup(self, backup_message, _bank_catalog, _simple_bank, _simple_preset):
        if self.delay is not None:
            backup_message.msg_array_data[0] = self.delay // 10
