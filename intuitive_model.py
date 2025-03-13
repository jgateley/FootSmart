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
import delay_message
import utility_message
import engage_preset_message
import simple_message as sm
import simple_grammar
import simple_model

# Notes
# Convert Devices to simple format:
# * The MIDI channel is created (right now just a name)

message_type = ['None', 'PC', 'CC', 'Delay']
message_type_default = 'None'

preset_type = ["vanilla", "bypass", "scroll", "cycle", "empty"]
preset_type_default = "vanilla"

show_enum = ["current", "next"]
show_enum_default = "current"


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


class DelayModel(jg.GrammarModel):
    def __init__(self):
        super().__init__('DelayModel')
        self.delay = None

    # Do not check version in equality
    def __eq__(self, other):
        result = (isinstance(other, CCModel) and self.delay == other.delay)
        if not result:
            self.modified = True
        return result

    def build(self, _channel):
        return delay_message.DelayModel.build(self.delay)


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

    @staticmethod
    def build(_channel):
        return utility_message.UtilityModel.build_manage_preset_scroll(None, True)


class EngagePresetModel(jg.GrammarModel):
    def __init__(self, number_banks, preset_number):
        super().__init__('EngagePresetModel')
        self.bank_number = number_banks
        self.bank_number += preset_number // 24
        self.preset_number = preset_number % 24

    # Do not check version in equality
    def __eq__(self, other):
        result = (isinstance(other, CCModel) and self.preset_number == other.preset_number)
        if not result:
            self.modified = True
        return result

    def build(self, _channel):
        return engage_preset_message.EngagePresetModel.build(self.bank_number, self.preset_number, None)


class MessageModel(jg.GrammarModel):
    def __init__(self):
        super().__init__('MessageModel')
        self.type = None
        self.name = None
        self.setup = None
        self.followup = None
        self.specific_message = None
        self.channel = None

    # Do not check version in equality
    def __eq__(self, other):
        result = (isinstance(other, MessageModel) and self.type == other.type and self.name == other.name and
                  self.setup == other.setup and self.followup == other.followup and
                  self.specific_message == other.specific_message)
        if not result:
            self.modified = True
        return result

    def build(self, intuitive_object, prefix, channel, name=None):
        if name is not None:
            self.name = name
        self.name = prefix + ' ' + self.name
        if self.setup is not None:
            self.setup = prefix + ' ' + self.setup
        if self.followup is not None:
            self.followup = prefix + ' ' + self.followup
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
        self.messages = [self.name] + self.messages
        preset_number = intuitive_object.add_engage_preset(self.messages)
        engage_preset = EngagePresetModel(len(intuitive_object.banks), preset_number)
        message = MessageModel()
        message.type = "Engage Preset"
        message.specific_message = engage_preset
        intuitive_object.add_message(self.name, message)


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
        self.action = None
        self.values = None
        self.names = None
        self.prefix = None
        self.show = None

    # Do not check version in equality
    def __eq__(self, other):
        result = (isinstance(other, PresetModel) and self.type == other.type and
                  self.actions == other.actions and self.short_name == other.short_name and
                  self.device == other.device and self.palette == other.palette and self.action == other.action and
                  self.values == other.values and self.names == other.names and self.prefix == other.prefix and
                  self.show == other.show)
        if not result:
            self.modified = True
        return result

    def build_scroll_preset(self, scroll_type, names, actions_values, intuitive_model_obj, simple_bank, preset_palette):
        if len(names) != len(actions_values):
            raise IntuitiveException('bad_names_values', 'different number of Names and Values')
        if len(names) < 1:
            raise IntuitiveException('Names cannot be empty')
        message_template = None
        if scroll_type == 'scroll':
            bank_messages = intuitive_model_obj.action_name_to_simple(actions_values[0], "On Enter Bank")
        elif scroll_type == 'cycle':
            message_template = intuitive_model_obj.action_name_to_simple(self.action, "Release")
            if len(message_template) > 1:
                raise IntuitiveException('single message', 'Cycle only supports cycling through single messages')
            message_template = message_template[0]
            # Now add the bank entry messages, but only for show: current cycles
            if self.show is None:
                bank_messages = [message_template.clone(value=actions_values[0], trigger="On Enter Bank")]
            else:
                bank_messages = []
        else:
            raise IntuitiveException('Unknown scroll type')

        ordered_names = names
        if scroll_type == 'cycle' and self.show == 'next':
            ordered_names = names[1:] + names[0:1]
        messages = []
        state_messages_length = None
        for action_value, name in zip(actions_values, ordered_names):
            # Build the rename message
            message = MessageModel()
            message.specific_message = RenamePreset(name)
            message.type = 'Preset Rename'
            messages += [message.to_simple('Release', None)]
            # Build the state changing message
            if scroll_type == 'scroll':
                state_messages = intuitive_model_obj.action_name_to_simple(action_value, 'Release')
            elif scroll_type == 'cycle':
                state_messages = [message_template.clone(value=action_value, trigger='Release')]
            else:
                raise IntuitiveException('Unknown scroll type')
            if state_messages_length is None:
                state_messages_length = len(state_messages)
            elif state_messages_length != len(state_messages):
                raise IntuitiveException('state_messages_length does not match state_messages')
            messages += state_messages
        # Now we have the list, but we need to adjust it for the initial state
        if scroll_type != 'cycle' or self.show != 'next':
            messages_to_move = messages[0:state_messages_length + 1]
            messages = messages[state_messages_length + 1:] + messages_to_move
        # Set the number of messages to scroll
        if state_messages_length > 7:
            msg = "Too many messages to scroll in scroll preset (> 8): " + str(state_messages_length + 1) + "\n"
            msg += "Bank " + simple_bank.name + "\n"
            msg += "Preset actions: "
            msg += ', '.join(names)
            raise IntuitiveException('Too many messages', msg)
        message = MessageModel()
        message.type = 'Utility'
        message.specific_message = ScrollNumberMessages(1 + state_messages_length)
        messages += [message.to_simple('Press', None)]
        # We must add the change direction message
        message = MessageModel()
        message.type = 'Utility'
        message.specific_message = ScrollReverseDirection()
        messages += [message.to_simple('Long Press', None)]
        if len(messages) > 32:
            msg = "Too many messages in scroll/cycle preset (> 32): " + str(len(messages)) + "\n"
            msg += "Bank " + simple_bank.name + "\n"
            msg += "Preset actions: "
            msg += ', '.join(names)
            raise IntuitiveException('Too many messages', msg)
        simple_preset = simple_model.SimplePreset.make(names[0], messages)
        # Message Scroll set on
        simple_preset.message_scroll = "On"
        # We must add the bank message
        if simple_bank.messages is None:
            simple_bank.messages = []
        simple_bank.messages += bank_messages
        if not simple_bank.messages:
            simple_bank.messages = None
        if preset_palette is not None:
            simple_preset.text = preset_palette.preset_text
            simple_preset.background = preset_palette.preset_background
        return simple_preset

    # Convert a preset to a simple object
    # use the preset palette if present, otherwise use the bank palette
    def to_simple(self, intuitive_model_obj, simple_bank, bank_palette):
        preset_palette = intuitive_model_obj.palettes_obj.lookup_palette(self.palette, bank_palette)
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
            messages = intuitive_model_obj.action_name_to_simple(bypass, 'Press', "one")
            messages += intuitive_model_obj.action_name_to_simple(enable, 'Press', "two")
            simple_preset = simple_model.SimplePreset.make(bypass, messages)
            simple_preset.toggle_name = enable
            simple_preset.toggle_mode = True
            simple_preset.toggle_group = intuitive_model_obj.midi_channel_catalogue[self.device]
            if self.palette is None:
                bypass_palette = intuitive_model_obj.palettes_obj.lookup_palette('bypass')
                if bypass_palette is not None:
                    preset_palette = bypass_palette
            if preset_palette is not None:
                simple_preset.text = preset_palette.preset_text
                simple_preset.background = preset_palette.preset_background
                simple_preset.text_toggle = preset_palette.preset_toggle_text
                simple_preset.background_toggle = preset_palette.preset_toggle_background
        elif self.type == 'scroll':
            # The "action name" is the name that should be displayed after pressing
            # The "action action" is the message
            # They are listed in the order they appear, and the initial state is the first action
            names = []
            actions = []
            for action in self.actions:
                names += [action['name']]
                actions += [action['action']]
            simple_preset = self.build_scroll_preset('scroll', names, actions, intuitive_model_obj, simple_bank,
                                                     preset_palette)
        elif self.type == 'cycle':
            names = []
            for name in self.names:
                if self.prefix is not None:
                    names += [self.prefix + ' ' + name]
                else:
                    names += [name]
            simple_preset = self.build_scroll_preset('cycle', names, self.values, intuitive_model_obj, simple_bank,
                                                     preset_palette)
        elif self.type == 'empty':
            simple_preset = simple_model.SimplePreset.make('', [])
            simple_preset.text = "black"
            simple_preset.background = "black"
        else:
            if self.type is not None:
                raise IntuitiveException('unknown_type', 'Unknown type ' + self.type)
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
        if not simple_preset.messages:
            simple_preset.messages = None
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
            if not simple_model_obj.messages:
                simple_model_obj.messages = None
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
        self.engage_presets = None
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

    def add_engage_preset(self, messages):
        preset_number = len(self.engage_presets)
        self.engage_presets.append(messages)
        return preset_number

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
        if isinstance(action, EngagePresetModel):
            result += [action.to_simple(trigger, toggle_state)]
        else:
            if action.setup is not None:
                result = self.action_name_to_simple(action.setup, trigger, toggle_state, new_seen)
            result += [action.to_simple(trigger, toggle_state)]
            if action.followup is not None:
                result += self.action_name_to_simple(action.followup, trigger, toggle_state, new_seen)
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

    @staticmethod
    def make_engage_preset_bank():
        bank = BankModel()
        bank.name = "FootSmart Internal"
        bank.presets = []
        return bank

    def add_engage_presets(self):
        if len(self.engage_presets) == 0:
            return
        bank = self.make_engage_preset_bank()
        self.banks.append(bank)
        for engage_preset in self.engage_presets:
            if len(bank.presets) >= 24:
                raise IntuitiveException('Not Implemented', 'Not Implemented')
            preset = PresetModel()
            preset.short_name = engage_preset[0]
            preset.actions = []
            for action in engage_preset[1:]:
                preset_action = PresetActionModel()
                preset_action.name = action
                preset_action.trigger = 'No Action'
                preset.actions.append(preset_action)
            bank.presets.append(preset)

    def to_simple(self):
        simple_model_obj = simple_model.Simple()
        self.palettes_obj = colors.Palettes(self.palettes)
        simple_model_obj.midi_channel = self.midi_channel
        # TODO: pass the Intuitive object all the way down, instead of switching to a parameter half way
        self.message_catalogue = {}
        self.midi_channel_catalogue = {}
        self.engage_presets = []

        # Add the next/previous page messages
        self.build_page_messages()

        # Convert devices to midi channels
        self.build_midi_channels(simple_model_obj)

        # Add goto bank messages to the message catalogue
        self.build_goto_bank_messages()

        # Add device messages to the message catalogue
        self.build_device_messages()

        # Add the engage_preset banks
        self.add_engage_presets()

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
