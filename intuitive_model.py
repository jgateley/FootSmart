import copy

import grammar
import grammar as jg
from IntuitiveException import IntuitiveException
from version import version_verify
import colors
import bank_jump_message
import toggle_page_message
import PCCC_message
import preset_rename_message
import utility_message
import simple_message as sm
import simple_grammar
import simple_model

# Notes
# Convert Devices to simple format:
# * The MIDI channel is created (right now just a name)

message_type = ['None', 'PC', 'CC']
message_type_default = 'None'

preset_type = ["vanilla", "bypass", "cycle"]
preset_type_default = "vanilla"


# Messages
class PCModel(jg.GrammarModel):
    def __init__(self):
        super().__init__('PCModel')
        self.number = None

    # Do not check version in equality
    def __eq__(self, other):
        result = (isinstance(other, PCModel) and self.number == other.number)
        if not result:
            self.modified = True
        return result

    def build(self, channel):
        return PCCC_message.PCModel.make(self.number, channel)


class CCModel(jg.GrammarModel):
    def __init__(self):
        super().__init__('CCModel')
        self.number = None
        self.value = None

    # Do not check version in equality
    def __eq__(self, other):
        result = (isinstance(other, CCModel) and self.number == other.number and self.value == other.value)
        if not result:
            self.modified = True
        return result

    def build(self, channel):
        return PCCC_message.CCModel.make(self.number, self.value, channel)


class GotoBank:
    def __init__(self, bank_number):
        self.bank_number = bank_number

    def __eq__(self, other):
        result = isinstance(other, GotoBank) and self.bank_number == other.bank_number
        if not result:
            result = True
        return result

    def build(self, _channel):
        return bank_jump_message.BankJumpModel.build(self.bank_number)


class PageUpDown:
    def __init__(self, page_up):
        self.page_up = page_up

    def __eq__(self, other):
        result = isinstance(other, PageUpDown) and self.page_up == other.page_up
        if not result:
            result = True
        return result

    def build(self, _channel):
        return toggle_page_message.TogglePageModel.build(self.page_up)


class RenamePreset:
    def __init__(self, new_name):
        self.new_name = new_name

    def __eq__(self, other):
        result = isinstance(other, RenamePreset) and self.new_name == other.new_name
        if not result:
            result = True
        return result

    def build(self, _channel):
        return preset_rename_message.PresetRenameModel.build(self.new_name)


# Set the preset scroll to do n messages at a time
class ScrollNumberMessages:
    def __init__(self, number):
        self.number = number

    def __eq__(self, other):
        result = isinstance(other, ScrollNumberMessages) and self.number == other.number
        if not result:
            result = True
        return result

    def build(self, _channel):
        return utility_message.UtilityModel.build_manage_preset_scroll(self.number)


# Set the preset scroll to do n messages at a time
class ScrollReverseDirection:
    def __init__(self):
        pass

    def __eq__(self, other):
        result = isinstance(other, ScrollReverseDirection)
        if not result:
            result = True
        return result

    def build(self, _channel):
        return utility_message.UtilityModel.build_manage_preset_scroll(None, True)


class MessageModel(jg.GrammarModel):
    def __init__(self):
        super().__init__('MessageModel')
        self.type = None
        self.name = None
        self.setup = None
        self.specific_message = None
        self.channel = None

    # Do not check version in equality
    def __eq__(self, other):
        result = (isinstance(other, MessageModel) and self.type == other.type and self.name == other.name and
                  self.setup == other.setup and self.specific_message == other.specific_message)
        if not result:
            self.modified = True
        return result

    def build(self, intuitive_object, prefix, channel, name=None):
        if name is not None:
            self.name = name
        self.name = prefix + ' ' + self.name
        if self.setup is not None:
            self.setup = prefix + ' ' + self.setup
        self.channel = channel
        intuitive_object.add_message(self.name, self)

    def to_simple(self, trigger, toggle_state):
        specific_message = self.specific_message.build(self.channel)
        return sm.SimpleMessage.make(None, specific_message, self.type, trigger, toggle_state)


class DeviceGroupModel(jg.GrammarModel):
    def __init__(self):
        super().__init__('DeviceGroupModel')
        self.name = None
        self.messages = None

    # Do not check version in equality
    def __eq__(self, other):
        result = (isinstance(other, DeviceGroupModel) and self.name == other.name and
                  self.messages == other.messages)
        if not result:
            self.modified = True
        return result

    def build(self, intuitive_object, prefix):
        self.name = prefix + ' ' + self.name
        for pos in range(len(self.messages)):
            self.messages[pos] = prefix + ' ' + self.messages[pos]
        intuitive_object.add_message(self.name, self)


# MIDI Devices
class DeviceModel(jg.GrammarModel):
    def __init__(self):
        super().__init__('DeviceModel')
        self.name = None
        self.channel = None
        self.messages = None
        self.enable_message = None
        self.bypass_message = None
        self.initial = None
        self.groups = None

    # Do not check version in equality
    def __eq__(self, other):
        result = (isinstance(other, DeviceModel) and self.name == other.name and self.channel == other.channel and
                  self.messages == other.messages and self.enable_message == other.enable_message and
                  self.bypass_message == other.bypass_message and self.initial == other.initial and
                  self.groups == other.groups)
        if not result:
            self.modified = True
        return result

    def build_midi_channel(self):
        # Create the Simple midi channel
        return simple_model.SimpleMidiChannel(self.name)

    def build_messages(self, intuitive_object):
        if self.messages is not None:
            for message in self.messages:
                message.build(intuitive_object, self.name, self.channel)
        if self.enable_message is not None:
            self.enable_message.build(intuitive_object, self.name, self.channel,  name='Enable')
        if self.bypass_message is not None:
            self.bypass_message.build(intuitive_object, self.name, self.channel, name='Bypass')
        if self.groups is not None:
            for group in self.groups:
                group.build(intuitive_object, self.name)

    def add_startup_actions(self, bank0, intuitive_object):
        # Add device startup actions
        if self.initial is not None:
            if bank0 is None:
                raise IntuitiveException('need-bank-0', 'Bank 0 required for initial messages')
            if bank0.messages is None:
                bank0.messages = []
            for message in self.initial:
                message_name = self.name + ' ' + message
                bank0.messages += intuitive_object.action_name_to_simple(message_name,
                                                                         "On Enter Bank - Execute Once Only")


# Preset Actions
# These are a trigger and a name (of a message)
class PresetActionModel(jg.GrammarModel):
    def __init__(self):
        super().__init__('PresetActionModel')
        self.trigger = None
        self.name = None

    # Do not check version in equality
    def __eq__(self, other):
        result = (isinstance(other, PresetActionModel) and self.trigger == other.trigger and
                  self.name == other.name)
        if not result:
            self.modified = True
        return result


# Bank Actions
# These are a trigger and a list of messages
class BankActionModel(jg.GrammarModel):
    @staticmethod
    def mk(trigger, name):
        result = BankActionModel()
        result.name = name
        result.trigger = trigger
        return result

    def __init__(self):
        super().__init__('BankActionModel')
        self.trigger = None
        self.name = None

    # Do not check version in equality
    def __eq__(self, other):
        result = (isinstance(other, BankActionModel) and self.trigger == other.trigger and
                  self.name == other.name)
        if not result:
            self.modified = True
        return result


# Presets
class PresetModel(jg.GrammarModel):
    def __init__(self):
        super().__init__('PresetModel')
        self.type = None
        self.short_name = None
        self.actions = None
        self.device = None
        self.palette = None

    # Do not check version in equality
    def __eq__(self, other):
        result = (isinstance(other, PresetModel) and self.type == other.type and
                  self.actions == other.actions and self.short_name == other.short_name and
                  self.device == other.device and self.palette == other.palette)
        if not result:
            self.modified = True
        return result

    # Convert a preset to a simple object
    # use the preset palette if present, otherwise use the bank palette
    # TODO: This code needs to be cleaned up quite a bit
    def to_simple(self, intuitive_model_obj, simple_bank, bank_palette):
        preset_palette = intuitive_model_obj.palettes_obj.lookup_palette(self.palette, bank_palette)
        if preset_palette is None:
            preset_palette = bank_palette
        if self.type == 'bypass':
            # short name : Enabled
            # Toggle name : Disabled
            # Position 1 colors for enabled
            # Position 2 colors for disabled
            # Toggle Mode On, Need unique toggle group
            # Message 1 in position 1
            # Message 2 in position 2
            enable = self.device + ' Enable'
            bypass = self.device + ' Bypass'
            messages = intuitive_model_obj.action_name_to_simple(enable, 'Press', "one")
            messages += intuitive_model_obj.action_name_to_simple(bypass, 'Press', "two")
            simple_preset = simple_model.SimplePreset.make(enable, messages)
            simple_preset.toggle_name = bypass
            simple_preset.toggle_mode = True
            simple_preset.toggle_group = intuitive_model_obj.midi_channel_catalogue[self.device]
            bypass_palette = intuitive_model_obj.palettes_obj.lookup_palette('bypass')
            if bypass_palette is not None:
                preset_palette = bypass_palette
            if preset_palette is not None:
                simple_preset.text = preset_palette.preset_text
                simple_preset.background = preset_palette.preset_background
                simple_preset.text_toggle = preset_palette.preset_toggle_text
                simple_preset.background_toggle = preset_palette.preset_toggle_background
        elif self.type == 'cycle':
            messages = []
            # The "action name" is the name that should be displayed after pressing
            # The "action action" is the message
            # They are listed in the order they appear, and the initial state is the first action
            bank_messages = intuitive_model_obj.action_name_to_simple(self.actions[0]['action'], "On Enter Bank")
            for action in self.actions:
                # Build the rename message
                message = MessageModel()
                message.specific_message = RenamePreset(action['name'])
                message.type = 'Preset Rename'
                messages += [message.to_simple('Release', None)]
                # Build the state changing message
                messages += intuitive_model_obj.action_name_to_simple(action['action'], 'Release')
            # Now we have the list, but we need to adjust it for the initial state
            rename = messages.pop(0)
            state1 = messages.pop(0)
            messages += [rename, state1]
            # We must set the number of messages.
            message = MessageModel()
            message.type = 'Utility'
            message.specific_message = ScrollNumberMessages(2)
            messages += [message.to_simple('Press', None)]
            # We must add the change direction message
            message = MessageModel()
            message.type = 'Utility'
            message.specific_message = ScrollReverseDirection()
            messages += [message.to_simple('Long Press', None)]
            # The initial name is the first name in the list
            simple_preset = simple_model.SimplePreset.make(self.actions[0]['name'], messages)
            # Message Scroll set on
            simple_preset.message_scroll = "On"
            # We must add the bank message
            if simple_bank.messages is None:
                simple_bank.messages = []
            simple_bank.messages += bank_messages
            if preset_palette is not None:
                simple_preset.text = preset_palette.preset_text
                simple_preset.background = preset_palette.preset_background
        else:
            # Short name, colors
            # Messages
            messages = []
            if self.actions is not None:
                for action in self.actions:
                    trigger = action.trigger
                    if trigger is None:
                        trigger = 'Press'
                    messages += intuitive_model_obj.action_name_to_simple(action.name, trigger)
            if not messages:
                messages = None
            simple_preset = simple_model.SimplePreset.make(self.short_name, messages)
            if preset_palette is not None:
                simple_preset.text = preset_palette.preset_text
                simple_preset.background = preset_palette.preset_background
        return simple_preset


# Banks
class BankModel(jg.GrammarModel):
    def __init__(self):
        super().__init__('BankModel')
        self.name = None
        self.description = None
        self.palette = None
        self.presets = None
        self.actions = None

    # Do not check version in equality
    def __eq__(self, other):
        result = (isinstance(other, BankModel) and self.name == other.name and self.description == other.description and
                  self.palette == other.palette and self.presets == other.presets and self.actions == other.actions)
        if not result:
            self.modified = True
        return result

    def to_simple(self, intuitive_model_obj):
        simple_model_obj = simple_model.SimpleBank()
        simple_model_obj.name = self.name
        simple_model_obj.description = self.description
        if self.description is not None:
            simple_model_obj.display_description = True
        bank_palette = intuitive_model_obj.palettes_obj.lookup_palette(self.palette)
        if bank_palette is not None:
            simple_model_obj.set_text(bank_palette.bank_text)
            simple_model_obj.set_background(bank_palette.bank_background)
        # Actions
        # Convert them to Simple Messages
        if self.actions is not None:
            simple_model_obj.messages = []
            for action in self.actions:
                trigger = action.trigger
                if trigger is None:
                    trigger = 'On Enter Bank'
                simple_model_obj.messages += intuitive_model_obj.action_name_to_simple(action.name, trigger)
        # Presets
        if self.presets is not None:
            simple_model_obj.presets = []
            for preset in self.presets:
                simple_model_obj.presets.append(preset.to_simple(intuitive_model_obj, simple_model_obj, bank_palette))
        return simple_model_obj


class Intuitive(jg.GrammarModel):
    def __init__(self):
        super().__init__('Intuitive')
        self.midi_channel = None
        self.palettes = None
        self.devices = None
        self.banks = None
        # Non grammar variables appear here
        self.midi_channels = None
        self.message_catalogue = None
        # This is required for the toggle group, which is the same as the midi channel
        self.midi_channel_catalogue = None
        self.palettes_obj = None

    # Do not check version in equality
    def __eq__(self, other):
        result = (isinstance(other, Intuitive) and self.midi_channel == other.midi_channel and
                  self.palettes == other.palettes and
                  self.devices == other.devices and
                  self.banks == other.banks)
        if not result:
            self.modified = True
        return result

    def add_message(self, name, message):
        if name in self.message_catalogue:
            raise IntuitiveException('multiply-defined-message', "Message already exists: " + name)
        self.message_catalogue[name] = message

    def action_name_to_simple(self, action_name, trigger=None, toggle_state=None, seen=None):
        if seen is None:
            seen = []
        if action_name in seen:
            raise IntuitiveException('loop detected')
        new_seen = seen + [action_name]
        if action_name not in self.message_catalogue:
            msg = 'The action named ' + action_name + ' is not defined'
            raise IntuitiveException('action name not found', msg)
        action = self.message_catalogue[action_name]
        result = []
        if isinstance(action, DeviceGroupModel):
            for message in action.messages:
                result += self.action_name_to_simple(message, trigger, toggle_state, new_seen)
        else:
            if action.setup is not None:
                result = self.action_name_to_simple(action.setup, trigger, toggle_state, new_seen)
            result += [action.to_simple(trigger, toggle_state)]
        return result

    def build_midi_channels(self, simple_model_obj):
        simple_model_obj.midi_channels = [None] * 16
        if self.devices is not None:
            for device in self.devices:
                midi_channel = device.build_midi_channel()
                simple_model_obj.midi_channels[device.channel - 1] = midi_channel
                self.midi_channel_catalogue[device.name] = device.channel
        grammar.prune_list(simple_model_obj.midi_channels)

    def build_page_messages(self):
        message = MessageModel()
        message.specific_message = PageUpDown(True)
        message.type = 'Toggle Page'
        self.add_message('Next Page', message)
        message = MessageModel()
        message.specific_message = PageUpDown(False)
        message.type = 'Toggle Page'
        self.add_message('Previous Page', message)

    def build_goto_bank_messages(self):
        if self.banks is not None:
            for pos, bank in enumerate(self.banks):
                message = MessageModel()
                message.specific_message = GotoBank(pos)
                message.type = 'Bank Jump'
                self.add_message('Bank ' + bank.name, message)

    def build_device_messages(self):
        if self.devices is not None:
            for device in self.devices:
                device.build_messages(self)

    def add_device_startup_actions(self, bank0):
        if self.devices is not None:
            for device in self.devices:
                device.add_startup_actions(bank0, self)

    def to_simple(self):
        simple_model_obj = simple_model.Simple()
        self.palettes_obj = colors.Palettes(self.palettes)
        simple_model_obj.midi_channel = self.midi_channel
        # TODO: pass the Intuitive object all the way down, instead of switching to a parameter half way
        self.message_catalogue = {}
        self.midi_channel_catalogue = {}

        # Add the next/previous page messages
        self.build_page_messages()

        # Convert devices to midi channels
        self.build_midi_channels(simple_model_obj)

        # Add goto bank messages to the message catalogue
        self.build_goto_bank_messages()

        # Add device messages to the message catalogue
        self.build_device_messages()

        # Convert banks
        simple_model_obj.banks = []
        if self.banks is not None:
            for bank in self.banks:
                simple_model_obj.banks.append(bank.to_simple(self))
        if not simple_model_obj.banks:
            simple_model_obj.banks = None

        # Add the device startup actions to the simple model bank0
        bank0 = None
        if simple_model_obj.banks is not None:
            bank0 = simple_model_obj.banks[0]
        self.add_device_startup_actions(bank0)

        return simple_model_obj
