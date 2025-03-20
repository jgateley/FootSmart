import copy

import backup_model
import grammar as jg
from IntuitiveException import IntuitiveException
import simple_message as sm
from version import version_verify
import colors

# This is the minimal version of the backup format.
# It is intended to be a human-readable version of the backup format.
#
# It includes to_backup and from_backup methods, these convert minimal models to backup models
#
# The main features:
# It is minimal, you only include what is significant, making it easier to edit the config file
# It is not deeply nested, again for ease of editing
#
# TODO: Select Exp Messages midi message is not implemented
# TODO: Trigger Messages midi message is not implemented


preset_message_trigger = ["No Action", "Press", "Release", "Long Press", "Long Press Scroll", "Long Press Release",
                          "Release All", "Double Tap", "Double Tap Release", "Long Double Tap",
                          "Long Double Tap Release", "On First Engage", "On First Engage (send only this)",
                          "On Disengage"]
preset_message_trigger_default = preset_message_trigger[0]

bank_message_trigger = ["unused", "On Enter Bank", "On Exit Bank", "On Enter Bank - Execute Once Only",
                        "On Exit Bank - Execute Once Only", "On Enter Bank - Page 1", "On Enter Bank - Page 2",
                        "On Toggle Page - Page 1", "On Toggle Page - Page 2"]
bank_message_trigger_default = bank_message_trigger[0]
initial_trigger = bank_message_trigger[3]


class SimpleMidiChannel(jg.GrammarModel):
    def __init__(self, name=None):
        super().__init__("SimpleMidiChannel")
        self.name = name

    def __eq__(self, other):
        result = isinstance(other, SimpleMidiChannel) and self.name == other.name
        if not result:
            self.modified = True
        return result

    def from_backup(self, backup_midi_channel):
        self.name = backup_midi_channel.name

    def to_backup(self):
        backup_midi_channel = backup_model.MidiChannel()
        backup_midi_channel.name = self.name
        return backup_midi_channel


class SimplePreset(jg.GrammarModel):
    @staticmethod
    def make(short_name, messages):
        result = SimplePreset()
        result.short_name = short_name
        result.messages = messages
        return result

    def __init__(self):
        super().__init__('SimplePreset')
        self.short_name = None
        self.long_name = None
        self.toggle_name = None
        self.message_scroll = None
        self.text = None
        self.text_toggle = None
        self.text_shift = None
        self.background = None
        self.background_toggle = None
        self.background_shift = None
        self.strip_color = None
        self.strip_toggle_color = None
        self.toggle_mode = None
        self.toggle_group = None
        self.messages = None

    def __eq__(self, other):
        result = (isinstance(other, SimplePreset) and self.short_name == other.short_name and
                  self.long_name == other.long_name and self.toggle_name == other.toggle_name and
                  self.message_scroll == other.message_scroll and
                  self.text == other.text and self.text_toggle == other.text_toggle and
                  self.text_shift == other.text_shift and self.background == other.background and
                  self.background_toggle == other.background_toggle and
                  self.background_shift == other.background_shift and
                  self.strip_color == other.strip_color and self.strip_toggle_color == other.strip_toggle_color and
                  self.toggle_mode == other.toggle_mode and self.toggle_group == other.toggle_group and
                  self.messages == other.messages)
        if not result:
            self.modified = True
        return result

    def from_backup(self, backup_preset, backup_bank, bank_catalog):
        self.short_name = backup_preset.short_name
        self.long_name = backup_preset.long_name
        self.toggle_name = backup_preset.toggle_name
        self.toggle_group = backup_preset.toggle_group
        if backup_preset.to_msg_scroll is not None and backup_preset.to_msg_scroll:
            self.message_scroll = "On"
        if backup_preset.name_color is not None:
            self.text = colors.colors[backup_preset.name_color]
        if backup_preset.name_toggle_color is not None:
            self.text_toggle = colors.colors[backup_preset.name_toggle_color]
        if backup_preset.shifted_name_color is not None:
            self.text_shift = colors.colors[backup_preset.shifted_name_color]
        if backup_preset.background_color is not None:
            self.background = colors.colors[backup_preset.background_color]
        if backup_preset.background_toggle_color is not None:
            self.background_toggle = colors.colors[backup_preset.background_toggle_color]
        if backup_preset.strip_color is not None:
            self.strip_color = colors.colors[backup_preset.strip_color]
        if backup_preset.strip_toggle_color is not None:
            self.strip_toggle_color = colors.colors[backup_preset.strip_toggle_color]
        self.toggle_mode = backup_preset.to_toggle
        if backup_preset.messages is not None:
            self.messages = [None] * 32
            for pos, backup_message in enumerate(backup_preset.messages):
                if backup_message is not None:
                    self.messages[pos] = sm.SimpleMessage()
                    self.messages[pos].from_backup(backup_message, sm.simple_message_type, backup_bank, bank_catalog,
                                                   preset_message_trigger)
            jg.prune_list(self.messages)

    def to_backup(self, bank_catalog, simple_bank):
        backup_preset = backup_model.Preset()
        backup_preset.short_name = self.short_name
        backup_preset.long_name = self.long_name
        backup_preset.toggle_name = self.toggle_name
        backup_preset.toggle_group = self.toggle_group
        if self.message_scroll is not None and self.message_scroll == "On":
            backup_preset.to_msg_scroll = True
        if self.text is not None:
            backup_preset.name_color = colors.colors.index(self.text)
        if self.text_toggle is not None:
            backup_preset.name_toggle_color = colors.colors.index(self.text_toggle)
        if self.text_shift is not None:
            backup_preset.shifted_name_color = colors.colors.index(self.text_shift)
        if self.background is not None:
            backup_preset.background_color = colors.colors.index(self.background)
        if self.background_toggle is not None:
            backup_preset.background_toggle_color = colors.colors.index(self.background_toggle)
        if self.strip_color is not None:
            backup_preset.strip_color = colors.colors.index(self.strip_color)
        if self.strip_toggle_color is not None:
            backup_preset.strip_toggle_color = colors.colors.index(self.strip_toggle_color)
        backup_preset.to_toggle = self.toggle_mode
        if self.messages is not None:
            for pos, message in enumerate(self.messages):
                if message is not None:
                    backup_message = backup_model.MidiMessage()
                    message.to_backup(backup_message, sm.simple_message_type, bank_catalog, simple_bank, self,
                                      preset_message_trigger)
                    backup_preset.set_message(backup_message, pos)
        return backup_preset


class SimpleBank(jg.GrammarModel):
    def __init__(self):
        super().__init__('SimpleBank')
        self.name = None
        self.description = None
        self.text = None
        self.background = None
        self.display_description = None
        self.clear_toggle = None
        self.messages = None
        self.presets = None
        self.exp_presets = None

    def __eq__(self, other):
        result = (isinstance(other, SimpleBank) and self.name == other.name and
                  self.description == other.description and
                  self.text == other.text and self.background == other.background and
                  self.display_description == other.display_description and
                  self.clear_toggle == other.clear_toggle and
                  self.messages == other.messages and
                  self.presets == other.presets and
                  self.exp_presets == other.exp_presets)
        if not result:
            self.modified = True
        return result

    def add_message(self, message):
        if self.messages is None:
            self.messages = []
        self.messages += message

    def from_backup(self, backup_bank, bank_catalog):
        if backup_bank.short_name is not None:
            raise IntuitiveException('unimplemented', 'bank short_name')
        self.name = backup_bank.name
        self.description = backup_bank.description
        if backup_bank.text_color is not None:
            self.text = colors.colors[backup_bank.text_color]
        if backup_bank.background_color is not None:
            self.background = colors.colors[backup_bank.background_color]
        self.display_description = backup_bank.to_display
        self.clear_toggle = backup_bank.clear_toggle
        if backup_bank.messages is not None:
            self.messages = [None] * 32
            for pos, backup_message in enumerate(backup_bank.messages):
                if backup_message is not None:
                    self.messages[pos] = sm.SimpleMessage()
                    if backup_message.trigger != 1:
                        self.messages[pos].trigger = bank_message_trigger[backup_message.trigger]
                    self.messages[pos].from_backup(backup_message, sm.bank_message_type, backup_bank, bank_catalog,
                                                   bank_message_trigger)
            jg.prune_list(self.messages)
        if backup_bank.presets is not None:
            self.presets = [None] * 24
            for pos, backup_preset in enumerate(backup_bank.presets):
                if backup_preset is not None:
                    self.presets[pos] = SimplePreset()
                    self.presets[pos].from_backup(backup_preset, backup_bank, bank_catalog)
            jg.prune_list(self.presets)
        if backup_bank.exp_presets is not None:
            self.exp_presets = [None] * 4
            for pos, backup_preset in enumerate(backup_bank.exp_presets):
                if backup_preset is not None:
                    self.exp_presets[pos] = SimplePreset()
                    self.exp_presets[pos].from_backup(backup_preset, backup_bank, bank_catalog)
            jg.prune_list(self.exp_presets)

    def to_backup(self, bank_catalog):
        backup_bank = backup_model.Bank()
        backup_bank.name = self.name
        backup_bank.description = self.description
        if self.text is not None:
            backup_bank.text_color = colors.colors.index(self.text)
        if self.background is not None:
            backup_bank.background_color = colors.colors.index(self.background)
        backup_bank.to_display = self.display_description
        backup_bank.clear_toggle = self.clear_toggle
        if self.messages is not None:
            for pos, message in enumerate(self.messages):
                if message is not None:
                    backup_message = backup_model.MidiMessage()
                    message.to_backup(backup_message, sm.bank_message_type, bank_catalog, self, None,
                                      bank_message_trigger)
                    backup_bank.set_message(backup_message, pos)
        if self.presets is not None:
            for pos, preset in enumerate(self.presets):
                if preset is not None:
                    backup_preset = preset.to_backup(bank_catalog, self)
                    backup_bank.set_preset(backup_preset, pos)
        if self.exp_presets is not None:
            for pos, preset in enumerate(self.exp_presets):
                if preset is not None:
                    backup_preset = preset.to_backup(bank_catalog, self)
                    backup_bank.set_exp_preset(backup_preset, pos)
        return backup_bank

    def lookup_preset(self, target_preset):
        for index, preset in enumerate(self.presets):
            if preset.short_name == target_preset:
                return index
        raise IntuitiveException('preset_not_found', 'Preset not found')

    def set_text(self, text):
        self.text = text

    def set_background(self, background):
        self.background = background


class Simple(jg.GrammarModel):
    page_size = 6

    @staticmethod
    def same_message_lists(list1, list2):
        if list1 is None:
            return list2 is None
        if list2 is None:
            return False
        dict1 = {}
        dict2 = {}
        for message in list1:
            dict1[message.name] = message
        for message in list2:
            dict2[message.name] = message
        if len(dict1) != len(dict2):
            return False
        for message in dict1.values():
            if message.name not in dict2:
                return False
            if message != dict2[message.name]:
                return False
        return True

    def __init__(self):
        super().__init__('Simple')
        self.midi_channels = None
        self.banks = None
        self.midi_channel = None
        self.version = None

    # Do not check version in equality
    def __eq__(self, other):
        result = (isinstance(other, Simple) and
                  self.midi_channels == other.midi_channels and
                  self.banks == other.banks and
                  self.midi_channel == other.midi_channel)
        if not result:
            self.modified = True
        return result

    # Parse the MIDI channels (names) first, as these are needed for MIDI messages
    # Then process the banks, gathering messages as we go, and handling bank arrangement
    # Then add all the gathered messages
    def from_backup(self, p_backup_model):
        self.midi_channels = [None] * 16
        if p_backup_model.midi_channels is not None:
            for pos in range(0, 15):
                if p_backup_model.midi_channels[pos] is not None:
                    self.midi_channels[pos] = SimpleMidiChannel()
                    self.midi_channels[pos].from_backup(p_backup_model.midi_channels[pos])
        jg.prune_list(self.midi_channels)
        if p_backup_model.banks is not None:
            self.banks = [None] * 128
            bank_catalog = []
            for bank in p_backup_model.banks:
                if bank is not None:
                    bank_catalog.append(bank.name)
                else:
                    bank_catalog.append(None)
            for pos, bank in enumerate(p_backup_model.banks):
                if bank is not None:
                    self.banks[pos] = SimpleBank()
                    self.banks[pos].from_backup(bank, bank_catalog)
                    if p_backup_model.bank_arrangement is not None:
                        if pos < len(p_backup_model.bank_arrangement) and p_backup_model.bank_arrangement[pos] is None:
                            raise IntuitiveException('bank_arrangement_mismatch',
                                                     'have bank but no bank arrangement')
                        if (pos < len(p_backup_model.bank_arrangement) and
                                p_backup_model.bank_arrangement[pos].name != self.banks[pos].name):
                            raise IntuitiveException('bank_order', 'bank and arrangement do not agree on order')
                elif (p_backup_model.bank_arrangement is not None and pos < len(p_backup_model.bank_arrangement) and
                      p_backup_model.bank_arrangement[pos] is not None):
                    raise IntuitiveException('bank_arrangement_mismatch', 'have bank arrangement but no bank')
            jg.prune_list(self.banks)
        elif p_backup_model.bank_arrangement is not None:
            raise IntuitiveException('banks_missing', 'bank arrangement present but banks missing')
        if len(self.midi_channels) == 0:
            self.midi_channels = None
        if p_backup_model.midi_channel is not None:
            self.midi_channel = p_backup_model.midi_channel + 1

    # Do the MIDI channel names first
    def to_backup(self):
        config = backup_model.Backup()

        # Create the channel list, mapping names to indices
        channels_list = []
        if self.midi_channels is not None:
            config_channels = [None] * 16
            for pos, channel in enumerate(self.midi_channels):
                if channel is not None:
                    channels_list.append(channel.name)
                    config_channels[pos] = channel.to_backup()
                else:
                    channels_list.append(None)
            config.midi_channels_from_list(config_channels)

        # Convert the model to a backup model
        if self.banks is not None:
            bank_catalog = {}
            for pos, bank in enumerate(self.banks):
                if bank is not None:
                    bank_catalog[bank.name] = pos
            for pos, bank in enumerate(self.banks):
                if bank is not None:
                    backup_bank = bank.to_backup(bank_catalog)
                    config.set_bank(backup_bank, pos)
                    bank_arrangement = backup_model.BankArrangementItem()
                    bank_arrangement.name = bank.name
                    config.set_bank_arrangement(bank_arrangement, pos)
        if self.midi_channel is not None:
            config.midi_channel = self.midi_channel - 1
        return config
