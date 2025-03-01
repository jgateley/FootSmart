import copy

import PCCC_message
import bank_jump_message
import delay_message
import grammar as jg
import preset_rename_message
import simple_model
import toggle_page_message
import utility_message

# TODO: Messages are a work in progress. The original implementation was not great, there was a long if/then/else
# TODO: chain in from_backup.
# TODO: As I implement each message type in intuitive, I am moving messages into their own files/classes

simple_message_type = ["unused", "PC", "CC", "Note On", "Note Off",
                       "Real Time", "SysEx", "MIDI Clock", "message8",
                       "message9", "Bank Up", "Bank Down", "Bank Change Mode",
                       # 13
                       "Bank Jump", "Toggle Page", "Set Toggle", "Set MIDI Thru",
                       # 17
                       "Select Exp Message", "Looper Mode", "message19", "message20",
                       "message21", "Toggle Preset", "Delay", "MIDI Clock Tap",
                       "Song Position", "CC Waveform Generator", "Engage Preset", "message28",
                       "message29", "message30", "CC Sequence Generator", "CC Value Scroll",
                       # 33
                       "PC Number Scroll", "PC Multichannel", "message35", "Utility",
                       "message37", "message38", "message39", "Relay Switching",
                       "MIDI MMC", "Trigger Messages", "message43", "Preset Rename",
                       # Below here are Simple Only actions
                       # TODO These should go away
                       # 45
                       # "Page Jump", throws count off by one
                       # "Preset Scroll Message Count", now count off by two
                       "Disengage Looper Mode",
                       # 48
                       'Stop CC Waveform Generator', 'Stop CC Sequence Generator',
                       # 50
                       'Stop All CC Waveform Generator', 'Stop All CC Sequence Generator',
                       # 52
                       'Start CC Waveform Generator', 'Start CC Sequence Generator',
                       # 54
                       'Start CC Waveform Generator No MIDI Clock', 'Start CC Sequence Generator No MIDI Clock',
                       # 56
                       'MIDI Clock Tap Menu', 'PC Number Scroll Update', 'CC Value Scroll Update']
simple_message_default = simple_message_type[0]

bank_message_type = ["unused", "PC", "CC", "Note On", "Note Off",
                     "Real Time", "Set Toggle", "Select Exp Message", "message8",
                     "message9", "Delay", "Song Position", "Looper Mode",
                     "PC Scroll Up", "PC Scroll Down",
                     "Engage Preset", "Utility", "PC Multichannel", "MIDI Clock", "Relay Switching",
                     "MIDI MMC", "message21", "message22", "message23", "CC Waveform Generator",
                     "CC Sequence Generator", "message26", "Toggle Page"]

onoff_type = ["Off", "On"]
onoff_default = onoff_type[0]


class PCMultichannelModel(jg.GrammarModel):

    def __init__(self):
        super().__init__('PCMultichannelModel')
        self.number = None
        self.channels = None

    def __eq__(self, other):
        result = isinstance(other, PCMultichannelModel) and self.number == other.number
        result = result and self.channels == other.channels
        if not result:
            self.modified = True
        return result

    def midi_multichannel_from_backup(self, backup_message):
        multichannel = backup_message.msg_array_data[1]
        if multichannel is None:
            multichannel = 0
        channel = 0
        self.channels = []
        while multichannel > 0:
            if multichannel & 1:
                self.channels.append(channel)
            multichannel = multichannel >> 1
            channel += 1

    def from_backup(self, backup_message):
        self.number = backup_message.msg_array_data[0]
        if self.number is None:
            self.number = 0
        self.midi_multichannel_from_backup(backup_message)
        channels_str = []
        for channel in self.channels:
            channels_str.append(str(channel))
        return ','.join(channels_str) + ':' + str(self.number)

    def to_backup(self, backup_message, _bank_catalog, _simple_bank, _simple_preset):
        backup_message.msg_array_data[0] = self.number
        backup_message.msg_array_data[1] = 0
        for channel in self.channels:
            backup_message.msg_array_data[1] |= 1 << channel


# pc_number_scroll_type = ['Send Only', 'Increase and Send', 'Decrease and Send', 'Update Only', 'Reset Only',
#                          'Increase Only', 'Decrease Only']
# Opcode is byte 0 upper 4 bits
# Counter is byte 0 lower 4 bits
# If it is a change opcode, wrap is byte 2 == 0
# If CC, CC number is byte 1
class PCCCNumberValueScrollBaseModel(jg.GrammarModel):
    pc_number_scroll_change = ["", "Increase", "Decrease"]
    pc_number_scroll_change_default = pc_number_scroll_change[0]

    @staticmethod
    def common_keys():
        return [jg.SwitchDict.make_key('send', jg.Atom('Send', bool, var='send')),
                jg.SwitchDict.make_key('change',
                                       jg.Enum('Change', PCCCNumberValueScrollBaseModel.pc_number_scroll_change,
                                               PCCCNumberValueScrollBaseModel.pc_number_scroll_change_default,
                                               var='change')),
                jg.SwitchDict.make_key('counter',
                                       jg.Atom('Counter', int, 0, var='counter')),
                jg.SwitchDict.make_key('channel', jg.Atom('Channel', int, '', var='channel')),
                jg.SwitchDict.make_key('wrap', jg.Atom('Wrap', bool, True, var='wrap'))]

    @staticmethod
    def cc_keys():
        return [jg.SwitchDict.make_key('number', jg.Atom('Number', int, var='number')),
                jg.SwitchDict.make_key('step', jg.Atom('Step', int, var='step'))]

    @staticmethod
    def update_keys():
        return [jg.SwitchDict.make_key('counter', jg.Atom('Counter', int, 0, var='counter')),
                jg.SwitchDict.make_key('value', jg.Atom('Value', int, 0, var='value'))]

    @staticmethod
    def get_opcode(backup_message):
        if backup_message.msg_array_data is None or backup_message.msg_array_data[0] is None:
            opcode = 0
        else:
            opcode = (backup_message.msg_array_data[0] & 0b11110000) >> 4
        return opcode

    @staticmethod
    def get_specific_message(simple_message, backup_message):
        opcode = PCCCNumberValueScrollBaseModel.get_opcode(backup_message)
        if opcode == 3 or opcode == 4:
            if simple_message.type == 'PC Number Scroll':
                simple_message.type = 'PC Number Scroll Update'
                simple_message.specific_message = PCNumberScrollUpdateModel()
            else:
                simple_message.type = 'CC Value Scroll Update'
                simple_message.specific_message = CCValueScrollUpdateModel()
            simple_message.name = simple_message.type + ':'
        else:
            if simple_message.type == 'PC Number Scroll':
                simple_message.specific_message = PCNumberScrollModel()
            else:
                simple_message.specific_message = CCValueScrollModel()

    def __init__(self):
        super().__init__('PCCCNumberValueScrollBaseModel')
        self.send = None
        self.change = None
        self.counter = None
        self.value = None
        self.channel = None
        self.wrap = None
        self.number = None
        self.step = None

    def __eq__(self, other):
        result = isinstance(other, PCCCNumberValueScrollBaseModel) and self.send == other.send
        result = result and self.change == other.change and self.counter == other.counter
        result = result and self.value == other.value and self.channel == other.channel and self.wrap == other.wrap
        result = result and self.number == other.number and self.step == other.step
        if not result:
            self.modified = True
        return result

    def eq_common(self, other):
        result = isinstance(other, PCCCNumberValueScrollBaseModel) and self.send == other.send
        result = result and self.change == other.change and self.counter == other.counter
        result = result and self.channel == other.channel and self.wrap == other.wrap
        if not result:
            self.modified = True
        return result

    def eq_cc(self, other):
        result = isinstance(other, PCCCNumberValueScrollBaseModel)
        result = result and self.number == other.number and self.step == other.step
        if not result:
            self.modified = True
        return result

    def eq_update(self, other):
        result = isinstance(other, PCCCNumberValueScrollBaseModel)
        result = result and self.value == other.value and self.counter == other.counter
        if not result:
            self.modified = True
        return result

    def from_backup_common(self, backup_message, name):
        opcode = PCCCNumberValueScrollBaseModel.get_opcode(backup_message)
        self.send = opcode < 3
        if self.send:
            name.append('Send')
        if opcode == 1 or opcode == 5:
            self.change = "Increase"
        elif opcode == 2 or opcode == 6:
            self.change = "Decrease"
        if self.change is not None:
            name.append(self.change)
        if self.change == PCCCNumberValueScrollBaseModel.pc_number_scroll_change_default:
            self.change = None
        if self.send:
            self.channel = backup_message.channel
            name.append(str(self.channel))

    def from_backup_wrap(self, is_cc, backup_message, name):
        if is_cc:
            if self.change is not None:
                if backup_message.msg_array_data is None or backup_message.msg_array_data[2] is None:
                    self.wrap = True
                else:
                    self.wrap = (backup_message.msg_array_data[2] & 64) != 0
        else:
            if self.change is not None:
                if backup_message.msg_array_data is None or backup_message.msg_array_data[2] is None:
                    self.wrap = True
                else:
                    self.wrap = backup_message.msg_array_data[2] == 0
        if self.wrap is None or self.wrap:
            name.append("Wrap")
            self.wrap = None
        else:
            name.append("No Wrap")
        if is_cc:
            name.append(str(self.step))

    def from_backup_cc(self, backup_message, name):
        self.number = 0
        if backup_message.msg_array_data is not None and backup_message.msg_array_data[1] is not None:
            self.number = backup_message.msg_array_data[1]
        name.append('CC' + str(self.number))
        if backup_message.msg_array_data is None or backup_message.msg_array_data[2] is None:
            self.step = 0
        else:
            self.step = backup_message.msg_array_data[2] & 63
        name.append('Step ' + str(self.step))

    def from_backup_counter(self, backup_message, name):
        if backup_message.msg_array_data is None or backup_message.msg_array_data[0] is None:
            self.counter = 0
        else:
            self.counter = (backup_message.msg_array_data[0] & 0b1111)
        name.append('Counter ' + str(self.counter))
        if self.counter == 0:
            self.counter = None

    def from_backup_update(self, backup_message, name):
        opcode = PCCCNumberValueScrollBaseModel.get_opcode(backup_message)
        self.value = 0
        if opcode == 3 and backup_message.msg_array_data is not None and backup_message.msg_array_data[1] is not None:
            self.value = backup_message.msg_array_data[1]
        name.append(str(self.value))
        if self.value == 0:
            self.value = None

    def to_backup_common(self, backup_message):
        if self.send:
            if self.change == 'Increase':
                opcode = 1
            elif self.change == 'Decrease':
                opcode = 2
            else:
                opcode = 0
        else:
            if self.change == 'Increase':
                opcode = 5
            else:
                opcode = 6
        backup_message.msg_array_data[0] = opcode << 4
        if self.channel is not None:
            backup_message.channel = self.channel
            if backup_message.channel == 1:
                backup_message.channel = None

    def to_backup_wrap(self, is_cc, backup_message):
        if self.change is not None:
            if is_cc:
                if self.step != 1:
                    if self.wrap is None or self.wrap:
                        wrap = 1
                    else:
                        wrap = 0
                    backup_message.msg_array_data[2] |= wrap << 6
            else:
                if self.wrap is not None and not self.wrap:
                    backup_message.msg_array_data[2] = 1

    def to_backup_cc(self, backup_message):
        backup_message.msg_array_data[1] = self.number
        if self.step is not None and self.step != 0:
            backup_message.msg_array_data[2] = self.step

    def to_backup_counter(self, backup_message):
        counter = self.counter
        if counter is None:
            counter = 0
        if backup_message.msg_array_data[0] is None:
            backup_message.msg_array_data[0] = 0
        backup_message.msg_array_data[0] |= counter

    def to_backup_update(self, backup_message):
        opcode = 4
        if self.value is not None and self.value != 0:
            opcode = 3
            backup_message.msg_array_data[1] = self.value
        backup_message.msg_array_data[0] = (backup_message.msg_array_data[0] & 0xF) | (opcode << 4)


class PCNumberScrollModel(PCCCNumberValueScrollBaseModel):
    @staticmethod
    def get_keys():
        return PCCCNumberValueScrollBaseModel.common_keys()

    def __init__(self):
        super().__init__()

    def __eq__(self, other):
        result = isinstance(other, PCNumberScrollModel) and self.eq_common(other)
        if not result:
            self.modified = True
        return result

    def from_backup(self, backup_message):
        name = []
        self.from_backup_common(backup_message, name)
        self.from_backup_counter(backup_message, name)
        self.from_backup_wrap(False, backup_message, name)
        return ':'.join(name)

    def to_backup(self, backup_message, _bank_catalog, _simple_bank, _simple_preset):
        self.to_backup_common(backup_message)
        self.to_backup_counter(backup_message)
        self.to_backup_wrap(False, backup_message)


class CCValueScrollModel(PCCCNumberValueScrollBaseModel):
    @staticmethod
    def get_keys():
        return PCCCNumberValueScrollBaseModel.common_keys() + PCCCNumberValueScrollBaseModel.cc_keys()

    def __init__(self):
        super().__init__()

    def __eq__(self, other):
        result = isinstance(other, CCValueScrollModel) and self.eq_common(other) and self.eq_cc(other)
        if not result:
            self.modified = True
        return result

    def from_backup(self, backup_message):
        name = []
        self.from_backup_common(backup_message, name)
        self.from_backup_counter(backup_message, name)
        self.from_backup_cc(backup_message, name)
        self.from_backup_wrap(True, backup_message, name)
        return ':'.join(name)

    def to_backup(self, backup_message, _bank_catalog, _simple_bank, _simple_preset):
        self.to_backup_common(backup_message)
        self.to_backup_counter(backup_message)
        self.to_backup_cc(backup_message)
        self.to_backup_wrap(True, backup_message)


class PCNumberScrollUpdateModel(PCCCNumberValueScrollBaseModel):
    @staticmethod
    def get_keys():
        return PCCCNumberValueScrollBaseModel.update_keys()

    def __init__(self):
        super().__init__()

    def __eq__(self, other):
        result = isinstance(other, PCNumberScrollUpdateModel) and self.eq_update(other)
        if not result:
            self.modified = True
        return result

# Opcode 3 is update, opcode 4 is reset
    def from_backup(self, backup_message):
        name = []
        self.from_backup_counter(backup_message, name)
        self.from_backup_update(backup_message, name)
        return ':'.join(name)

    def to_backup(self, backup_message, _bank_catalog, _simple_bank, _simple_preset):
        backup_message.type = simple_message_type.index("PC Number Scroll")
        self.to_backup_common(backup_message)
        self.to_backup_counter(backup_message)
        self.to_backup_update(backup_message)


class CCValueScrollUpdateModel(PCCCNumberValueScrollBaseModel):
    @staticmethod
    def get_keys():
        return PCCCNumberValueScrollBaseModel.update_keys()

    def __init__(self):
        super().__init__()

    def __eq__(self, other):
        result = isinstance(other, CCValueScrollUpdateModel) and self.eq_update(other)
        if not result:
            self.modified = True
        return result

    def from_backup(self, backup_message):
        name = []
        self.from_backup_counter(backup_message, name)
        self.from_backup_update(backup_message, name)
        return ':'.join(name)

    def to_backup(self, backup_message, _bank_catalog, _simple_bank, _simple_preset):
        self.to_backup_common(backup_message)
        self.to_backup_counter(backup_message)
        self.to_backup_update(backup_message)


class NoteOnModel(jg.GrammarModel):
    @staticmethod
    def get_common_keys():
        return [jg.SwitchDict.make_key('note', jg.Atom('Note', int, var='note')),
                jg.SwitchDict.make_key('velocity', jg.Atom('Velocity', int, var='velocity')),
                jg.SwitchDict.make_key('channel', jg.Atom('Channel', int, var='channel'))]

    @staticmethod
    def get_keys():
        return NoteOnModel.get_common_keys()

    def __init__(self):
        super().__init__('NoteOnModel')
        self.channel = None
        self.note = None
        self.velocity = None

    def __eq__(self, other):
        result = isinstance(other, NoteOnModel) and self.channel == other.channel and self.note == other.note
        result = result and self.velocity == other.velocity
        if not result:
            self.modified = True
        return result

    def from_backup(self, channel, backup_message):
        self.channel = channel
        if backup_message.msg_array_data is None:
            self.note = 0
            self.velocity = 0
        else:
            if backup_message.msg_array_data[0] is None:
                self.note = 0
            else:
                self.note = backup_message.msg_array_data[0]
            if backup_message.msg_array_data[1] is None:
                self.velocity = 0
            else:
                self.velocity = backup_message.msg_array_data[1]
        note_name = str(self.note)
        return note_name + ':' + str(self.velocity) + ':' + str(self.channel)

    def to_backup(self, backup_message, _bank_catalog, _simple_bank, _simple_preset):
        backup_message.msg_array_data[0] = self.note
        backup_message.msg_array_data[1] = self.velocity
        backup_message.channel = self.channel
        if backup_message.channel == 1:
            backup_message.channel = None


class NoteOffModel(jg.GrammarModel):
    @staticmethod
    def get_keys():
        all_notes_key = jg.SwitchDict.make_key('all_notes', jg.Atom('All Notes', bool, var='all_notes'))
        return NoteOnModel.get_common_keys() + [all_notes_key]

    def __init__(self):
        super().__init__('NoteOffModel')
        self.channel = None
        self.note = None
        self.velocity = None
        self.all_notes = None

    def __eq__(self, other):
        result = isinstance(other, NoteOffModel) and self.channel == other.channel and self.note == other.note
        result = result and self.velocity == other.velocity and self.all_notes == other.all_notes
        if not result:
            self.modified = True
        return result

    def from_backup(self, channel, backup_message):
        self.channel = channel
        if backup_message.msg_array_data is None:
            self.note = 0
            self.velocity = 0
            self.all_notes = False
        else:
            if backup_message.msg_array_data[0] is None:
                self.note = 0
            else:
                self.note = backup_message.msg_array_data[0]
            if backup_message.msg_array_data[1] is None:
                self.velocity = 0
            else:
                self.velocity = backup_message.msg_array_data[1]
            if backup_message.msg_array_data[2] == 1:
                self.all_notes = True
        note_name = str(self.note)
        if self.all_notes:
            note_name = 'all'
        return note_name + ':' + str(self.velocity) + ':' + str(self.channel)

    def to_backup(self, backup_message, _bank_catalog, _simple_bank, _simple_preset):
        backup_message.channel = self.channel
        if backup_message.channel == 1:
            backup_message.channel = None
        backup_message.msg_array_data[0] = self.note
        backup_message.msg_array_data[1] = self.velocity
        if self.all_notes:
            backup_message.msg_array_data[2] = 1


class RealTimeModel(jg.GrammarModel):
    realtime_message_type = ["Nothing", "Start", "Stop", "Continue"]
    realtime_message_default = realtime_message_type[0]

    def __init__(self):
        super().__init__('RealTimeModel')
        self.real_time_type = None

    def __eq__(self, other):
        result = isinstance(other, RealTimeModel) and self.real_time_type == other.real_time_type
        if not result:
            self.modified = True
        return result

    def from_backup(self, backup_message):
        if backup_message.msg_array_data is None or backup_message.msg_array_data[0] is None:
            self.real_time_type = RealTimeModel.realtime_message_default
        else:
            self.real_time_type = RealTimeModel.realtime_message_type[backup_message.msg_array_data[0]]
        return self.real_time_type

    def to_backup(self, backup_message, _bank_catalog, _simple_bank, _simple_preset):
        backup_message.msg_array_data[0] = RealTimeModel.realtime_message_type.index(self.real_time_type)


class SongPositionModel(jg.GrammarModel):
    def __init__(self):
        super().__init__('SongPositionModel')
        self.song_position = None

    def __eq__(self, other):
        result = isinstance(other, SongPositionModel) and self.song_position == other.song_position
        if not result:
            self.modified = True
        return result

    def from_backup(self, backup_message):
        if backup_message.msg_array_data is None or backup_message.msg_array_data[1] is None:
            self.song_position = 0
        else:
            self.song_position = backup_message.msg_array_data[1]
        return str(self.song_position)

    def to_backup(self, backup_message, _bank_catalog, _simple_bank, _simple_preset):
        backup_message.msg_array_data[1] = self.song_position


class MIDIMMCModel(jg.GrammarModel):
    midi_mmc_enum = ["Nothing", "Stop", "Play", "Deferred PLay", "Fast Forward", "Rewind", "Record Strobe",
                     "Record Exit",
                     "Record Pause", "Pause", "Eject", "Chase", "MMC Reset"]
    midi_mmc_default = midi_mmc_enum[0]

    def __init__(self):
        super().__init__('MIDIMMCModel')
        self.midi_mmc_type = None

    def __eq__(self, other):
        result = isinstance(other, MIDIMMCModel) and self.midi_mmc_type == other.midi_mmc_type
        if not result:
            self.modified = True
        return result

    def from_backup(self, backup_message):
        if backup_message.msg_array_data is None or backup_message.msg_array_data[0] is None:
            self.midi_mmc_type = MIDIMMCModel.midi_mmc_default
        else:
            self.midi_mmc_type = MIDIMMCModel.midi_mmc_enum[backup_message.msg_array_data[0]]
        return self.midi_mmc_type

    def to_backup(self, backup_message, _bank_catalog, _simple_bank, _simple_preset):
        backup_message.msg_array_data[0] = MIDIMMCModel.midi_mmc_enum.index(self.midi_mmc_type)


class MIDIClockModel(jg.GrammarModel):
    bpm_decimal_enum = ['+0', '+0.25', '+0.5', '0.75']
    bpm_decimal_default = bpm_decimal_enum[0]

    @staticmethod
    def is_tap_menu(message, msg_array_data):
        if msg_array_data is None:
            is_tap_menu = False
        elif msg_array_data[2] is None:
            is_tap_menu = False
        else:
            is_tap_menu = (msg_array_data[2] & 0b1) != 0
        if is_tap_menu:
            message.type = 'MIDI Clock Tap Menu'
            message.name = message.type + ':'
            message.specific_message = MIDIClockTapMenuModel()
        else:
            message.specific_message = MIDIClockModel()

    def __init__(self):
        super().__init__('MIDIClockModel')
        self.stop_clock = None
        self.bpm = None
        self.bpm_decimal = None

    def __eq__(self, other):
        result = isinstance(other, MIDIClockModel) and self.stop_clock == other.stop_clock and self.bpm == other.bpm
        result = result and self.bpm_decimal == other.bpm_decimal
        if not result:
            self.modified = True
        return result

    def from_backup(self, backup_message):
        name = []
        if backup_message.msg_array_data is None:
            self.stop_clock = True
            name.append('Stop MIDI Clock')
        else:
            flags = backup_message.msg_array_data[2]
            if flags is None:
                flags = 0
            if flags & 0b1111 != flags:
                raise IntuitiveException('bad_midi_clock', "Got a MIDI Clock message with flags I cannot parse")
            self.stop_clock = flags & 0b10 == 0
            if self.stop_clock:
                name.append("Stop MIDI Clock")
            else:
                name.append("Don't Stop MIDI Clock")
            if backup_message.msg_array_data[0] is not None:
                raise IntuitiveException('bad_midi_clock', "Got a MIDI Clock message I cannot parse")
            if not self.stop_clock:
                bpm = backup_message.msg_array_data[1]
                if bpm is None:
                    bpm = 0
                self.bpm = bpm
                name.append(str(self.bpm))
                bpm_decimal_index = (flags & 0b1100) >> 2
                self.bpm_decimal = MIDIClockModel.bpm_decimal_enum[bpm_decimal_index]
                name.append(self.bpm_decimal)
        return ':'.join(name)

    def to_backup(self, backup_message, _bank_catalog, _simple_bank, _simple_preset):
        if self.bpm is None:
            backup_message.msg_array_data[1] = None
        else:
            backup_message.msg_array_data[1] = self.bpm
        if self.bpm_decimal is not None:
            bpm_index = MIDIClockModel.bpm_decimal_enum.index(self.bpm_decimal)
        else:
            bpm_index = MIDIClockModel.bpm_decimal_enum.index(MIDIClockModel.bpm_decimal_default)
        flags = bpm_index << 2
        if not self.stop_clock:
            flags = flags | 0b10
        if flags != 0:
            backup_message.msg_array_data[2] = flags


class MIDIClockTapMenuModel(jg.GrammarModel):
    def __init__(self):
        super().__init__('MIDIClockTapMenuModel')
        self.use_current_bpm = None
        self.bpm = None
        self.bpm_decimal = None

    def __eq__(self, other):
        result = isinstance(other, MIDIClockTapMenuModel) and self.use_current_bpm == other.use_current_bpm
        result = result and self.bpm == other.bpm and self.bpm_decimal == other.bpm_decimal
        if not result:
            self.modified = True
        return result

    def from_backup(self, backup_message):
        name = []
        if backup_message.msg_array_data is None:
            self.use_current_bpm = True
            name.append('Use Current BPM')
            self.bpm = 0
            name.append('0')
            self.bpm_decimal = MIDIClockModel.bpm_decimal_default
            name.append(self.bpm_decimal)
        else:
            flags = backup_message.msg_array_data[2]
            if flags is None:
                flags = 0
            if flags & 0b1111 != flags:
                raise IntuitiveException('bad_midi_clock', "Got a MIDI Clock message with flags I cannot parse")
            self.use_current_bpm = flags & 0b10 != 0
            if self.use_current_bpm:
                name.append('Use Current BPM')
            else:
                name.append("Don't Use Current BPM")
            if not self.use_current_bpm:
                bpm = backup_message.msg_array_data[1]
                if bpm is None:
                    bpm = 0
                self.bpm = bpm
                name.append(str(self.bpm))
                bpm_decimal_index = (flags & 0b1100) >> 2
                self.bpm_decimal = MIDIClockModel.bpm_decimal_enum[bpm_decimal_index]
                name.append(self.bpm_decimal)
        if self.bpm == 0:
            self.bpm = None
        if self.bpm_decimal == MIDIClockModel.bpm_decimal_default:
            self.bpm_decimal = None
        return ':'.join(name)

    def to_backup(self, backup_message, _bank_catalog, _simple_bank, _simple_preset):
        backup_message.type = simple_message_type.index('MIDI Clock')
        if self.bpm is None:
            backup_message.msg_array_data[1] = None
        else:
            backup_message.msg_array_data[1] = self.bpm
        if self.bpm_decimal is not None:
            bpm_index = MIDIClockModel.bpm_decimal_enum.index(self.bpm_decimal)
        else:
            bpm_index = MIDIClockModel.bpm_decimal_enum.index(MIDIClockModel.bpm_decimal_default)
        flags = bpm_index << 2
        if self.use_current_bpm:
            flags = flags | 2
        flags = flags | 1
        backup_message.msg_array_data[2] = flags


class RelaySwitchingModel(jg.GrammarModel):
    tip_ring_action_type = ["Nothing", "Tap - NO", "Tap - NC", "Engage", "Disengage", "Toggle", "Sync Clock 8 Taps"]
    tip_ring_action_default = tip_ring_action_type[0]

    relay_type = ['Omniport 1', 'Omniport 2', 'Omniport 3', 'Omniport 4', 'Relay Port A', 'Relay Port B']
    relay_default = relay_type[0]

    def __init__(self):
        super().__init__('RelaySwitchingModel')
        self.relay = None
        self.tip_action = None
        self.ring_action = None

    def __eq__(self, other):
        result = isinstance(other, RelaySwitchingModel) and self.relay == other.relay
        result = result and self.tip_action == other.tip_action and self.ring_action == other.ring_action
        if not result:
            self.modified = True
        return result

    def from_backup(self, backup_message):
        if backup_message.msg_array_data is None:
            self.relay = RelaySwitchingModel.relay_default
            self.tip_action = RelaySwitchingModel.tip_ring_action_default
            self.ring_action = RelaySwitchingModel.tip_ring_action_default
        else:
            if backup_message.msg_array_data[0] is None:
                self.relay = RelaySwitchingModel.relay_default
            else:
                self.relay = RelaySwitchingModel.relay_type[backup_message.msg_array_data[0]]
            if backup_message.msg_array_data[1] is None:
                self.tip_action = RelaySwitchingModel.tip_ring_action_default
            else:
                self.tip_action = RelaySwitchingModel.tip_ring_action_type[backup_message.msg_array_data[1]]
            if backup_message.msg_array_data[2] is None:
                self.ring_action = RelaySwitchingModel.tip_ring_action_default
            else:
                self.ring_action = RelaySwitchingModel.tip_ring_action_type[backup_message.msg_array_data[2]]
        relay_type_name = self.relay
        if self.relay == RelaySwitchingModel.relay_default:
            self.relay = None
        return relay_type_name + ':' + self.tip_action + ':' + self.ring_action

    def to_backup(self, backup_message, _bank_catalog, _simple_bank, _simple_preset):
        if self.relay is not None and self.relay != RelaySwitchingModel.relay_default:
            backup_message.msg_array_data[0] = RelaySwitchingModel.relay_type.index(self.relay)
        if self.tip_action is not None and self.tip_action != RelaySwitchingModel.tip_ring_action_default:
            backup_message.msg_array_data[1] = RelaySwitchingModel.tip_ring_action_type.index(self.tip_action)
        if self.ring_action is not None and self.ring_action != RelaySwitchingModel.tip_ring_action_default:
            backup_message.msg_array_data[2] = RelaySwitchingModel.tip_ring_action_type.index(self.ring_action)


class MIDIThruModel(jg.GrammarModel):
    def __init__(self):
        super().__init__('MIDIThruModel')
        self.value = None

    def __eq__(self, other):
        result = isinstance(other, MIDIThruModel) and self.value == other.value
        if not result:
            self.modified = True
        return result

    def from_backup(self, backup_message):
        if backup_message.msg_array_data is None or backup_message.msg_array_data[0] is None:
            self.value = onoff_default
        else:
            self.value = onoff_type[backup_message.msg_array_data[0]]
        name = self.value
        if self.value == onoff_default:
            self.value = None
        return name

    def to_backup(self, backup_message, _bank_catalog, _simple_bank, _simple_preset):
        if self.value is not None and self.value != MIDIThruModel.onoff_default:
            backup_message.msg_array_data[0] = onoff_type.index(self.value)


class WaveformSequenceBaseModel(jg.GrammarModel):
    note_divisions = ["Whole", "Half", "Quarter", "Eighth", "Triplets", "Sixteenth", "2 Whole", "3 Whole", "4 Whole"]
    note_divisions_default = note_divisions[0]

    @staticmethod
    def engine_keys():
        return [jg.SwitchDict.make_key('engine', jg.Atom('Engine', int, var='engine'))]

    @staticmethod
    def common_keys():
        return [jg.SwitchDict.make_key('perpetual', jg.Atom('Perpetual', bool, False, var='perpetual')),
                jg.SwitchDict.make_key('number', jg.Atom('Number', int, var='number')),
                jg.SwitchDict.make_key('channel', jg.Atom('Channel', int, '', var='channel'))]

    @staticmethod
    def waveform_keys():
        return [jg.SwitchDict.make_key('reverse_waveform',
                                       jg.Atom('Reverse Waveform', bool, False,
                                               var='reverse_waveform'))]

    @staticmethod
    def midi_clock_keys():
        return [jg.SwitchDict.make_key('note_division',
                                       jg.Enum('Note Division', WaveformSequenceBaseModel.note_divisions,
                                               WaveformSequenceBaseModel.note_divisions_default, var='note_division'))]

    @staticmethod
    def no_midi_clock_keys():
        return [jg.SwitchDict.make_key('cps',
                                       jg.Atom('Cycles Per Second', int, var='cpm')),
                jg.SwitchDict.make_key('multiplier',
                                       jg.Atom('Speed Multiplier', int,
                                               var='multiplier'))]

    @staticmethod
    def is_stop(data):
        if data is None or data[1] is None or (data[1] & 0xF0) == 0:
            return True
        return False

    @staticmethod
    def determine_start_type(simple_message, data):
        follow_midi_clock = (data[1] & 0x4) != 0
        if simple_message.type == 'CC Waveform Generator':
            if follow_midi_clock:
                simple_message.type = 'Start CC Waveform Generator'
                simple_message.specific_message = StartWaveformModel()
            else:
                simple_message.type = 'Start CC Waveform Generator No MIDI Clock'
                simple_message.specific_message = StartWaveformNoMIDIClockModel()
        else:
            if follow_midi_clock:
                simple_message.type = 'Start CC Sequence Generator'
                simple_message.specific_message = StartSequenceModel()
            else:
                simple_message.type = 'Start CC Sequence Generator No MIDI Clock'
                simple_message.specific_message = StartSequenceNoMIDIClockModel()
        simple_message.name = simple_message.type + ':'

    @staticmethod
    def determine_stop_type(simple_message, data):
        stop_all = data is not None and data[4] is not None and data[4] == 15
        if simple_message.type == 'CC Waveform Generator':
            if stop_all:
                simple_message.type = 'Stop All CC Waveform Generator'
                simple_message.specific_message = StopAllWaveformModel()
            else:
                simple_message.type = 'Stop CC Waveform Generator'
                simple_message.specific_message = StopWaveformModel()
        else:
            if stop_all:
                simple_message.type = 'Stop All CC Sequence Generator'
                simple_message.specific_message = StopAllSequenceModel()
            else:
                simple_message.type = 'Stop CC Sequence Generator'
                simple_message.specific_message = StopSequenceModel()
        simple_message.name = simple_message.type
        if simple_message.specific_message is not None:
            simple_message.name += ':'

    def __init__(self):
        super().__init__('WaveformSequenceBaseModel')
        self.engine = None
        self.perpetual = None
        self.note_division = None
        self.cpm = None
        self.multiplier = None
        self.reverse_waveform = None
        self.number = None
        self.channel = None

    def __eq__(self, other):
        result = isinstance(other, WaveformSequenceBaseModel)
        if not result:
            self.modified = True
        return result

    def eq_engine(self, other):
        return self.engine == other.engine

    def eq_common(self, other):
        return self.perpetual == other.perpetual and self.number == other.number and self.channel == other.channel

    def eq_midi_clock(self, other):
        return self.note_division == other.note_division

    def eq_no_midi_clock(self, other):
        return self.cpm == other.cpm and self.multiplier == other.multiplier

    def eq_waveform(self, other):
        return self.reverse_waveform == other.reverse_waveform

    def from_backup_engine(self, backup_message):
        if backup_message.msg_array_data is None:
            self.engine = 0
        else:
            if backup_message.msg_array_data[4] is None:
                self.engine = 0
            else:
                self.engine = backup_message.msg_array_data[4]
        self.engine += 1
        return str(self.engine)

    def from_backup_common(self, backup_message, channel, name):
        self.channel = channel
        if backup_message.msg_array_data is None:
            self.perpetual = False
            self.number = 0
        else:
            if backup_message.msg_array_data[1] is None:
                raise IntuitiveException('unexpected', 'unexpected')
            self.perpetual = backup_message.msg_array_data[1] & 0x20 != 0
            if backup_message.msg_array_data[0] is None:
                self.number = 0
            else:
                self.number = backup_message.msg_array_data[0]
        if self.perpetual:
            name.append('Perpetual')
        else:
            name.append('Once Only')
        if not self.perpetual:
            self.perpetual = None
        name.append(str(self.number))
        name.append(str(self.channel))

    def from_backup_midi_clock(self, backup_message, name):
        if backup_message.msg_array_data is None or backup_message.msg_array_data[2] is None:
            note_division = 0
        else:
            note_division = backup_message.msg_array_data[2]
        self.note_division = WaveformSequenceBaseModel.note_divisions[note_division]
        name.append(self.note_division)
        if self.note_division == WaveformSequenceBaseModel.note_divisions_default:
            self.note_division = None

    def from_backup_no_midi_clock(self, backup_message, name):
        if backup_message.msg_array_data is None or backup_message.msg_array_data[2] is None:
            cpm = 0
        else:
            cpm = backup_message.msg_array_data[2]
        self.cpm = cpm + 1
        self.multiplier = 1 << ((backup_message.msg_array_data[1] & 0x18) >> 3)
        name.append(str(self.cpm) + ' CPM')
        name.append(str(self.multiplier) + 'x')

    def from_backup_waveform(self, backup_message, name):
        if backup_message.msg_array_data is None or backup_message.msg_array_data[3] is None:
            self.reverse_waveform = False
        else:
            self.reverse_waveform = backup_message.msg_array_data[3] != 0
        if self.reverse_waveform:
            name.append('Reverse')
        else:
            name.append('No Reverse')
        if not self.reverse_waveform:
            self.reverse_waveform = None

    def to_backup_engine(self, backup_message):
        if self.engine is not None:
            backup_message.msg_array_data[4] = self.engine - 1

    def to_backup_common(self, backup_message):
        backup_message.channel = self.channel
        if backup_message.channel == 1:
            backup_message.channel = None
        if backup_message.msg_array_data[1] is None:
            backup_message.msg_array_data[1] = 0
        if self.perpetual:
            backup_message.msg_array_data[1] |= 0x20
        if self.number is not None and self.number != 0:
            backup_message.msg_array_data[0] = self.number

    def to_backup_midi_clock(self, backup_message):
        if self.note_division is not None and self.note_division != WaveformSequenceBaseModel.note_divisions_default:
            backup_message.msg_array_data[2] = WaveformSequenceBaseModel.note_divisions.index(self.note_division)

    def to_backup_no_midi_clock(self, backup_message):
        if self.cpm is not None and self.cpm != 1:
            backup_message.msg_array_data[2] = self.cpm - 1
        if self.multiplier is not None and self.multiplier != 0:
            multiplier = self.multiplier
            val = 0
            while multiplier > 1:
                val += 1
                multiplier >>= 1
            if backup_message.msg_array_data[1] is None:
                backup_message.msg_array_data[1] = 0
            backup_message.msg_array_data[1] |= val << 3

    def to_backup_waveform(self, backup_message):
        if self.reverse_waveform:
            backup_message.msg_array_data[3] = 1


class StopWaveformModel(WaveformSequenceBaseModel):
    @staticmethod
    def get_keys():
        return WaveformSequenceBaseModel.engine_keys()

    def __init__(self):
        super().__init__()

    def __eq__(self, other):
        result = isinstance(other, StopWaveformModel)
        result = result and self.eq_engine(other)
        if not result:
            self.modified = True
        return result

    def from_backup(self, backup_message):
        name = [self.from_backup_engine(backup_message)]
        return ':'.join(name)

    def to_backup(self, backup_message, _bank_catalog, _simple_bank, _simple_preset):
        backup_message.type = simple_message_type.index("CC Waveform Generator")
        self.to_backup_engine(backup_message)


class StopAllWaveformModel(WaveformSequenceBaseModel):
    def __init__(self):
        super().__init__()

    def __eq__(self, other):
        result = isinstance(other, StopAllWaveformModel)
        if not result:
            self.modified = True
        return result

    @staticmethod
    def from_backup(_backup_message):
        return ''

    @staticmethod
    def to_backup(backup_message, _bank_catalog, _simple_bank, _simple_preset):
        backup_message.type = simple_message_type.index("CC Waveform Generator")
        backup_message.msg_array_data[4] = 15


class StopSequenceModel(WaveformSequenceBaseModel):
    @staticmethod
    def get_keys():
        return WaveformSequenceBaseModel.engine_keys()

    def __init__(self):
        super().__init__()

    def __eq__(self, other):
        result = isinstance(other, StopSequenceModel)
        result = result and self.eq_engine(other)
        if not result:
            self.modified = True
        return result

    def from_backup(self, backup_message):
        name = [self.from_backup_engine(backup_message)]
        return ':'.join(name)

    def to_backup(self, backup_message, _bank_catalog, _simple_bank, _simple_preset):
        backup_message.type = simple_message_type.index("CC Sequence Generator")
        self.to_backup_engine(backup_message)


class StopAllSequenceModel(WaveformSequenceBaseModel):
    def __init__(self):
        super().__init__()

    def __eq__(self, other):
        result = isinstance(other, StopAllSequenceModel)
        if not result:
            self.modified = True
        return result

    @staticmethod
    def from_backup(_backup_message):
        return ''

    @staticmethod
    def to_backup(backup_message, _bank_catalog, _simple_bank, _simple_preset):
        backup_message.type = simple_message_type.index("CC Sequence Generator")
        backup_message.msg_array_data[4] = 15


class StartWaveformModel(WaveformSequenceBaseModel):
    @staticmethod
    def get_keys():
        return (WaveformSequenceBaseModel.engine_keys() + WaveformSequenceBaseModel.common_keys() +
                WaveformSequenceBaseModel.midi_clock_keys() + WaveformSequenceBaseModel.waveform_keys())

    def __init__(self):
        super().__init__()

    def __eq__(self, other):
        result = isinstance(other, StartWaveformModel)
        result = result and self.eq_engine(other)
        result = result and self.eq_common(other)
        result = result and self.eq_midi_clock(other)
        result = result and self.eq_waveform(other)
        if not result:
            self.modified = True
        return result

    def from_backup(self, backup_message, channel):
        name = []
        self.from_backup_common(backup_message, channel, name)
        self.from_backup_midi_clock(backup_message, name)
        self.from_backup_waveform(backup_message, name)
        name.append(self.from_backup_engine(backup_message))
        return ':'.join(name)

    def to_backup(self, backup_message, _bank_catalog, _simple_bank, _simple_preset):
        backup_message.type = simple_message_type.index("CC Waveform Generator")
        backup_message.msg_array_data[1] = 0x43  # start, don't stop, unknown 2 bits at end
        self.to_backup_common(backup_message)
        self.to_backup_midi_clock(backup_message)
        self.to_backup_waveform(backup_message)
        self.to_backup_engine(backup_message)


class StartSequenceModel(WaveformSequenceBaseModel):
    @staticmethod
    def get_keys():
        return (WaveformSequenceBaseModel.engine_keys() + WaveformSequenceBaseModel.common_keys() +
                WaveformSequenceBaseModel.midi_clock_keys())

    def __init__(self):
        super().__init__()

    def __eq__(self, other):
        result = isinstance(other, StartSequenceModel)
        result = result and self.eq_engine(other)
        result = result and self.eq_common(other)
        result = result and self.eq_midi_clock(other)
        if not result:
            self.modified = True
        return result

    def from_backup(self, backup_message, channel):
        name = []
        self.from_backup_common(backup_message, channel, name)
        self.from_backup_midi_clock(backup_message, name)
        name.append(self.from_backup_engine(backup_message))
        return ':'.join(name)

    def to_backup(self, backup_message, _bank_catalog, _simple_bank, _simple_preset):
        backup_message.type = simple_message_type.index("CC Sequence Generator")
        backup_message.msg_array_data[1] = 0x43  # start, don't stop, unknown 2 bits at end
        self.to_backup_common(backup_message)
        self.to_backup_midi_clock(backup_message)
        self.to_backup_engine(backup_message)


class StartWaveformNoMIDIClockModel(WaveformSequenceBaseModel):
    @staticmethod
    def get_keys():
        return (WaveformSequenceBaseModel.engine_keys() + WaveformSequenceBaseModel.common_keys() +
                WaveformSequenceBaseModel.no_midi_clock_keys() + WaveformSequenceBaseModel.waveform_keys())

    def __init__(self):
        super().__init__()

    def __eq__(self, other):
        result = isinstance(other, StartWaveformNoMIDIClockModel)
        result = result and self.eq_engine(other)
        result = result and self.eq_common(other)
        result = result and self.eq_no_midi_clock(other)
        result = result and self.eq_waveform(other)
        if not result:
            self.modified = True
        return result

    def from_backup(self, backup_message, channel):
        name = []
        self.from_backup_common(backup_message, channel, name)
        self.from_backup_waveform(backup_message, name)
        self.from_backup_no_midi_clock(backup_message, name)
        name.append(self.from_backup_engine(backup_message))
        return ':'.join(name)

    def to_backup(self, backup_message, _bank_catalog, _simple_bank, _simple_preset):
        backup_message.type = simple_message_type.index("CC Waveform Generator")
        backup_message.msg_array_data[1] = 0x43  # start, don't stop, unknown 2 bits at end
        self.to_backup_common(backup_message)
        self.to_backup_waveform(backup_message)
        self.to_backup_no_midi_clock(backup_message)
        self.to_backup_engine(backup_message)


class StartSequenceNoMIDIClockModel(WaveformSequenceBaseModel):
    @staticmethod
    def get_keys():
        return (WaveformSequenceBaseModel.engine_keys() + WaveformSequenceBaseModel.common_keys() +
                WaveformSequenceBaseModel.no_midi_clock_keys())

    def __init__(self):
        super().__init__()

    def __eq__(self, other):
        result = isinstance(other, StartSequenceNoMIDIClockModel)
        result = result and self.eq_engine(other)
        result = result and self.eq_common(other)
        result = result and self.eq_no_midi_clock(other)
        if not result:
            self.modified = True
        return result

    def from_backup(self, backup_message, channel):
        name = []
        self.from_backup_common(backup_message, channel, name)
        self.from_backup_no_midi_clock(backup_message, name)
        name.append(self.from_backup_engine(backup_message))
        return ':'.join(name)

    def to_backup(self, backup_message, _bank_catalog, _simple_bank, _simple_preset):
        backup_message.type = simple_message_type.index("CC Sequence Generator")
        backup_message.msg_array_data[1] = 0x43  # start, don't stop, unknown 2 bits at end
        self.to_backup_common(backup_message)
        self.to_backup_no_midi_clock(backup_message)
        self.to_backup_engine(backup_message)


# TODO: use bank number instead of bank name
class EngagePresetModel(jg.GrammarModel):
    engage_preset_action = ["No Action", "Press", "Release", "Long Press", "Long Press Scroll", "Long Press Release",
                            "Release All", "Double Tap", "Double Tap Release", "Long Double Tap",
                            "Long Double Tap Release"]
    engage_preset_action_default = engage_preset_action[0]

    def __init__(self):
        super().__init__('EngagePresetModel')
        self.bank = None
        self.preset = None
        self.action = None

    def __eq__(self, other):
        result = isinstance(other, EngagePresetModel) and self.bank == other.bank and self.preset == other.preset
        result = result and self.action == other.action
        if not result:
            self.modified = True
        return result

    def from_backup(self, banks, backup_message):
        if backup_message.msg_array_data is None:
            self.bank = banks[0]
            self.preset = 'A'
            self.action = EngagePresetModel.engage_preset_action_default
        else:
            if backup_message.msg_array_data[0] is None:
                self.bank = banks[0]
            else:
                self.bank = banks[backup_message.msg_array_data[0]]
            if backup_message.msg_array_data[1] is None:
                self.preset = 'A'
            else:
                self.preset = chr(backup_message.msg_array_data[1])
            if backup_message.msg_array_data[2] is None:
                self.action = simple_model.preset_message_trigger[0]
            else:
                self.action = simple_model.preset_message_trigger[backup_message.msg_array_data[2]]
        return self.bank + ':' + self.preset + ':' + self.action

    def to_backup(self, backup_message, bank_catalog, _simple_bank, _simple_preset):
        bank_number = bank_catalog[self.bank]
        if bank_number != 0:
            backup_message.msg_array_data[0] = bank_number
        if self.preset != 'A':
            backup_message.msg_array_data[1] = ord(self.preset)
        if self.action != simple_model.preset_message_trigger_default:
            backup_message.msg_array_data[2] = simple_model.preset_message_trigger.index(self.action)


# TODO: Can we get rid of simple bank?
class SetToggleModel(jg.GrammarModel):
    preset_mapping = [[0, 0x1],   # 0, A
                      [0, 0x2],   # 1, B
                      [0, 0x4],   # 2, C
                      [0, 0x8],   # 3, D
                      [0, 0x10],  # 4, E
                      [0, 0x20],  # 5, F
                      [0, 0x40],  # 6, G
                      [1, 0x1],   # 7, H
                      [1, 0x2],   # 8, I
                      [1, 0x4],   # 9, J
                      [1, 0x8],   # 10, K
                      [1, 0x10],  # 11, L
                      [1, 0x20],  # 12, M
                      [1, 0x40],  # 13, N
                      [2, 0x1],   # 14, O
                      [2, 0x2],   # 15, P
                      [2, 0x4],   # 16, Q
                      [2, 0x8],   # 17, R
                      [2, 0x10],  # 18, S
                      [2, 0x20],  # 19, T
                      [2, 0x40],  # 20, U
                      [3, 0x1],   # 21, V
                      [3, 0x2],   # 22, W
                      [3, 0x4],   # 23, X
                      ]
    set_toggle_type = ["Dis-engage Toggle", "Unused", "Engage Toggle", "Toggle", "Shift", "Shift+", "Unshift"]
    set_toggle_default = set_toggle_type[0]

    def __init__(self):
        super().__init__('SetToggleModel')
        self.position = None
        self.presets = None

    def __eq__(self, other):
        result = isinstance(other, SetToggleModel) and self.position == other.position and self.presets == other.presets
        if not result:
            self.modified = True
        return result

    # Set Toggle has a toggle position and a set of presets
    # In the backup message, the toggle position is stored in the channel (weird),
    # and the presets are bytes 0-3 of the msg_array_data (one bit per preset)
    # The toggle position is
    #    Disengage Toggle: Channel None (0)
    #    Engage Toggle: Channel 2
    #    Toggle: Channel 3
    #    Shift: Channel 4
    #    Shift+: Channel 5
    #    Unshift: Channel 6
    # Because of the weird 0 to 2 jump, the simple implementation has "unused" in position 1
    # Presets are stored low to high (preset A is bit 0 of the first byte), and each byte uses 7 bits
    # msg_array_data[0]: A, B, C, D, E, F, G
    # msg_array_data[1]: H, I, J, K, L, M, N
    # msg_array_data[2]: O, P, Q, R, S, T, U
    # msg_array_data[3]: V, W, X
    def from_backup(self, backup_message, backup_bank):
        if backup_message.channel is None:
            self.position = SetToggleModel.set_toggle_default
        else:
            self.position = SetToggleModel.set_toggle_type[backup_message.channel]
        name = self.position + ':'
        if self.position == SetToggleModel.set_toggle_default:
            self.position = None
        if backup_message.msg_array_data is not None:
            self.from_backup_presets(backup_message, backup_bank)
            name += ','.join(self.presets)
        return name

    def from_backup_presets(self, backup_message, backup_bank):
        self.presets = []
        for preset_number, preset_map in enumerate(self.preset_mapping):
            if (backup_message.msg_array_data[preset_map[0]] is not None and
                    backup_message.msg_array_data[preset_map[0]] & preset_map[1]):
                self.presets.append(backup_bank.presets[preset_number].short_name)

    def to_backup(self, backup_message, _bank_catalog, simple_bank, _simple_preset):
        if self.position is not None:
            backup_message.channel = SetToggleModel.set_toggle_type.index(self.position)
        backup_message.msg_array_data[0] = 0
        backup_message.msg_array_data[1] = 0
        backup_message.msg_array_data[2] = 0
        backup_message.msg_array_data[3] = 0
        for preset in self.presets:
            preset_number = simple_bank.lookup_preset(preset)
            preset_map = self.preset_mapping[preset_number]
            backup_message.msg_array_data[preset_map[0]] |= preset_map[1]


# TODO: Can we get rid of simple_bank?
class TriggerMessagesModel(jg.GrammarModel):
    def __init__(self):
        super().__init__('TriggerMessagesModel')
        self.preset = None
        self.messages = None
        self.message_numbers = None
        # TODO: justify not implementing this
        raise Exception("Trigger Messages Not implemented, not required")

    def __eq__(self, other):
        result = isinstance(other, TriggerMessagesModel) and self.preset == other.preset
        result = result and self.messages == other.messages
        if not result:
            self.modified = True
        return result

    def from_backup(self, backup_message, backup_bank):
        preset_number = 0
        if backup_message.msg_array_data is not None and backup_message.msg_array_data[0] is not None:
            preset_number = backup_message.msg_array_data[0]
        self.preset = backup_bank.presets[preset_number].short_name
        if backup_message.msg_array_data is None:
            self.message_numbers = 0
        else:
            if backup_message.msg_array_data[5] is None:
                self.message_numbers = 0
            else:
                self.message_numbers = backup_message.msg_array_data[5]
        return self.preset + ':' + str(self.message_numbers)

    def from_backup_cleanup(self, presets):
        if self.messages is not None:
            return
        for preset in presets:
            if preset is not None and preset.short_name == self.preset:
                self.messages = []
                message_number = 0
                message_numbers = self.message_numbers
                while message_numbers > 0:
                    if message_numbers & 1:
                        if message_number < len(preset.messages):
                            self.messages.append(preset.messages[message_number].midi_message)
                        else:
                            print("Warning, message " + str(message_number) +
                                  " is not populated in preset. Ignoring in Trigger Messages.")
                    message_number += 1
                    message_numbers >>= 1
                return
        raise IntuitiveException('preset_not_found', 'In cleanup, preset not found')

    def to_backup(self, backup_message, _bank_catalog, simple_bank, _simple_preset):
        preset_number = simple_bank.lookup_preset(self.preset)
        if preset_number != 0:
            backup_message.msg_array_data[0] = preset_number
        preset = simple_bank.presets[preset_number]
        backup_message.msg_array_data[5] = 0
        for message in self.messages:
            backup_message.msg_array_data[5] |= 1 << preset.lookup_message(message)


class SelectExpMessageModel(jg.GrammarModel):

    message_map = [[4, 0x1],   # message 1
                   [4, 0x2],   # message 2
                   [4, 0x4],   # message 3
                   [4, 0x8],   # message 4
                   [4, 0x10],  # message 5
                   [4, 0x20],  # message 6
                   [3, 0x1],   # message 7
                   [3, 0x2],   # message 8
                   [3, 0x4],   # message 9
                   [3, 0x8],   # message 10
                   [3, 0x10],  # message 11
                   [3, 0x20],  # message 12
                   [3, 0x40],  # message 13
                   [2, 0x1],   # message 14
                   [2, 0x2],   # message 15
                   [2, 0x4],   # message 16
                   [2, 0x8],   # message 17
                   [2, 0x10],  # message 18
                   [2, 0x20],  # message 19
                   [2, 0x40],  # message 20
                   [1, 0x1],   # message 21
                   [1, 0x2],   # message 22
                   [1, 0x4],   # message 23
                   [1, 0x8],   # message 24
                   [1, 0x10],  # message 25
                   [1, 0x20],  # message 26
                   [1, 0x40],  # message 27
                   [0, 0x4],   # message 28
                   [0, 0x8],   # message 29
                   [0, 0x10],  # message 30
                   [0, 0x20],  # message 31
                   [0, 0x40],  # message 32
                   ]

    def __init__(self):
        super().__init__('SelectExpMessageModel')
        self.input = None
        self.messages = None
        self.message_numbers = None
        raise Exception("Select Exp Message Not implemented")

    # eq will not be accurate in the period between from_backup and from_backup_cleanup, not sure if this is an issue
    def __eq__(self, other):
        result = isinstance(other, SelectExpMessageModel) and self.input == other.input
        result = result and self.messages == other.messages
        if not result:
            self.modified = True
        return result

    # The backup message contains an exp (no 1 -4), and up to 32 messages
    # These are stored in msg_array_data places 0 through 4:
    # 0aaa aaxx 0bbb bbbb 0ccc cccc 0ddd dddd 00ee eeee
    # xx is the exp number (0 based, for 1-4)
    # ee eeee is messages number 1 through 6
    # ddd dddd is messages 7 through 13
    # ccc cccc is messages 14 through 20
    # bbb bbbb is messages 21 through 27
    # aaa aa is messages 28 through 32
    def from_backup(self, backup_message):
        self.message_numbers = []
        if backup_message.msg_array_data is None:
            self.input = 0
        else:
            if backup_message.msg_array_data[0] is None:
                self.input = 0
            else:
                self.input = backup_message.msg_array_data[0] & 0x3
            for message_number, message in enumerate(self.message_map):
                if backup_message.msg_array_data[message[0]] is not None:
                    if backup_message.msg_array_data[message[0]] & message[1]:
                        self.message_numbers.append(message_number)
        self.input += 1
        input_name = str(self.input)
        if self.input == 1:
            self.input = None
        return input_name + ':' + str(self.message_numbers)

    def from_backup_cleanup(self, messages):
        if self.messages is not None:
            return
        self.messages = []
        for message_number in self.message_numbers:
            if message_number < len(messages):
                self.messages.append(messages[message_number].midi_message)
            else:
                print("Warning, message " + str(message_number) +
                      " is not populated in preset. Ignoring in Select Exp Message.")
        if not self.messages:
            self.messages = None
        return

    # TODO: Can we get rid of simple_preset
    def to_backup(self, backup_message, _bank_catalog, _simple_bank, simple_preset):
        backup_message.msg_array_data[0] = 0
        backup_message.msg_array_data[1] = 0
        backup_message.msg_array_data[2] = 0
        backup_message.msg_array_data[3] = 0
        backup_message.msg_array_data[4] = 0
        if self.input is not None:
            backup_message.msg_array_data[0] |= self.input - 1
        if self.messages is not None:
            for message in self.messages:
                message_number = simple_preset.lookup_message(message)
                map_entry = self.message_map[message_number]
                backup_message.msg_array_data[map_entry[0]] |= map_entry[1]


class LooperModeModel(jg.GrammarModel):
    looper_mode = ['Toggle', 'Engage']
    looper_mode_default = looper_mode[0]

    def __init__(self):
        super().__init__('LooperModeModel')
        self.mode = None
        self.selected_switches = None
        self.switches = None
        self.disable_message = None

    def __eq__(self, other):
        result = isinstance(other, LooperModeModel) and self.mode == other.mode
        result = result and self.selected_switches == other.selected_switches and self.switches == other.switches
        result = result and self.disable_message == other.disable_message
        if not result:
            self.modified = True
        return result

    def from_backup(self, backup_message):
        if backup_message.msg_array_data is None:
            self.mode = LooperModeModel.looper_mode_default
            self.selected_switches = False
            self.switches = []
            self.disable_message = False
        else:
            if backup_message.msg_array_data[0] is None:
                self.mode = LooperModeModel.looper_mode_default
                self.selected_switches = False
                self.disable_message = False
            else:
                self.mode = LooperModeModel.looper_mode[backup_message.msg_array_data[0] & 3]
                self.selected_switches = (backup_message.msg_array_data[0] & 4) != 0
                self.disable_message = (backup_message.msg_array_data[0] & 8) != 0
            self.switches = []
            if backup_message.msg_array_data[1] is not None:
                switch = 0
                switches = backup_message.msg_array_data[1]
                while switches > 0:
                    if switches & 1:
                        self.switches.append(chr(ord('A') + switch))
                    switch += 1
                    switches >>= 1
        name = self.mode + ':'
        if self.mode == LooperModeModel.looper_mode_default:
            self.mode = None
        if self.selected_switches:
            name += ','.join(self.switches)
        else:
            name += 'all'
            self.selected_switches = None
        if self.disable_message:
            name += ':disableLCD'
        else:
            name += ':enableLCD'
            self.disable_message = None
        if not self.switches:
            self.switches = None
        return name

    def to_backup(self, backup_message, _bank_catalog, _simple_bank, _simple_preset):
        backup_message.msg_array_data[0] = 0
        if self.mode is not None:
            backup_message.msg_array_data[0] |= LooperModeModel.looper_mode.index(self.mode)
        if self.selected_switches is not None and self.selected_switches:
            backup_message.msg_array_data[0] |= 4
        if self.disable_message is not None and self.disable_message:
            backup_message.msg_array_data[0] |= 8
        if self.switches is not None:
            backup_message.msg_array_data[1] = 0
            for switch in self.switches:
                backup_message.msg_array_data[1] |= 1 << ord(switch) - ord('A')


class DisengageLooperModeModel(jg.GrammarModel):
    def __init__(self):
        super().__init__('DisengageLooperModeModel')
        self.disable_message = None

    def __eq__(self, other):
        result = isinstance(other, DisengageLooperModeModel) and self.disable_message == other.disable_message
        if not result:
            self.modified = True
        return result

    def from_backup(self, backup_message):
        if backup_message.msg_array_data is None or backup_message.msg_array_data[0] is None:
            self.disable_message = False
        else:
            self.disable_message = (backup_message.msg_array_data[0] & 8) != 0
        if self.disable_message:
            return "disableLCD"
        else:
            return "enableLCD"

    def to_backup(self, backup_message, _bank_catalog, _simple_bank, _simple_preset):
        backup_message.type = simple_message_type.index("Looper Mode")
        backup_message.msg_array_data[0] = 2
        if self.disable_message is not None and self.disable_message:
            backup_message.msg_array_data[0] |= 8


class SysExModel(jg.GrammarModel):
    def __init__(self):
        super().__init__('SysExModel')
        self.data = None

    def __eq__(self, other):
        result = isinstance(other, SysExModel) and self.data == other.data
        if not result:
            self.modified = True
        return result

    def from_backup(self, backup_message):
        if backup_message.msg_array_data is None:
            self.data = None
        else:
            raise IntuitiveException('not_implemented', 'Not Implemented')
        return str(self.data)

    def to_backup(self, _backup_message, _bank_catalog, _simple_bank, _simple_preset):
        if self.data is not None:
            raise IntuitiveException('not_implemented', 'Not Implemented')


# MIDI and controller messages are their own top level category, and are named
# This class is messages, including MIDI messages
# But also including other messages such as those which control the MC6Pro
# They can be referenced in banks etc.
#
class SimpleMessage(jg.GrammarModel):
    preset_toggle_state = ["one", "two", "both", "shift"]
    preset_toggle_state_default = preset_toggle_state[2]

    to_bank_classes = {'PC': PCCC_message.PCModel,
                       'CC': PCCC_message.CCModel,
                       'Bank Jump': bank_jump_message.BankJumpModel,
                       'Toggle Page': toggle_page_message.TogglePageModel,
                       'Preset Rename': preset_rename_message.PresetRenameModel,
                       'Utility': utility_message.UtilityModel,
                       'Delay': delay_message.DelayModel}

    @staticmethod
    def make(name, specific_message, ptype, trigger, toggle_state):
        result = SimpleMessage()
        result.name = name
        result.type = ptype
        result.specific_message = specific_message
        result.trigger = trigger
        result.toggle_state = toggle_state
        return result

    @staticmethod
    def make_toggle_page_message(name, page_up, message_catalog):
        result = SimpleMessage()
        result.name = name
        result.type = 'Toggle Page'
        result.specific_message = TogglePageModel().mk_toggle_page_message(page_up)
        return message_catalog.add(result)

    def __init__(self):
        super().__init__('SimpleMessage')
        self.name = None
        self.specific_message = None
        self.type = None
        self.trigger = None
        self.toggle_state = None

    def __eq__(self, other):
        result = isinstance(other, SimpleMessage) and self.type == other.type
        result = result and self.specific_message == other.specific_message
        result = result and self.trigger == other.trigger
        result = result and self.toggle_state == other.toggle_state
        if not result:
            self.modified = True
        return result

    def clone(self, value=None, trigger=None):
        result = copy.deepcopy(self)
        if value is not None:
            if isinstance(self.specific_message, PCCC_message.CCModel):
                result.specific_message.value = value
            else:
                raise IntuitiveException('cannot clone non CC message', 'cannot clone non CC message')
        if trigger is not None:
            result.trigger = trigger
        return result

    # This creates a name out of the MIDI message parameters
    def from_backup(self, backup_message, message_type, backup_bank, banks, trigger_enum):

        if backup_message.type is not None:
            self.type = message_type[backup_message.type]
        else:
            raise IntuitiveException('unimplemented', 'Fix me')

        if backup_message.trigger is not None:
            self.trigger = trigger_enum[backup_message.trigger]
        if backup_message.toggle_state is not None:
            self.toggle_state = SimpleMessage.preset_toggle_state[backup_message.toggle_state]

        self.name = self.type + ':'
        if self.trigger is not None:
            self.name += self.trigger
        self.name += ':'
        # Lookup the message type model, and build from the backup message
        # TODO: this is in transition, only messages that are handled in intuitive are here
        # TODO: the rest of the messages are in the big huge if, to be transitioned as they are
        # TODO: implemented in intuitive
        if self.type in self.to_bank_classes:
            self.to_bank_classes[self.type].build_from_backup(self, backup_message)
        elif self.type == 'PC Multichannel':
            self.specific_message = PCMultichannelModel()
            self.name += self.specific_message.from_backup(backup_message)
        elif self.type == 'Note On' or self.type == 'Note Off':
            if self.type == 'Note On':
                self.specific_message = NoteOnModel()
            else:
                self.specific_message = NoteOffModel()
            channel = backup_message.channel
            if channel is None:
                channel = 1
            self.name += self.specific_message.from_backup(channel, backup_message)
        elif self.type == 'Real Time':
            self.specific_message = RealTimeModel()
            self.name += self.specific_message.from_backup(backup_message)
        elif self.type == 'Song Position':
            self.specific_message = SongPositionModel()
            self.name += self.specific_message.from_backup(backup_message)
        elif self.type == 'MIDI MMC':
            self.specific_message = MIDIMMCModel()
            self.name += self.specific_message.from_backup(backup_message)
        elif self.type == 'MIDI Clock':
            MIDIClockModel.is_tap_menu(self, backup_message.msg_array_data)
            self.name += self.specific_message.from_backup(backup_message)
        elif self.type == 'MIDI Clock Tap':
            # N0 data, no specific message
            self.name = self.name.replace(':', '')
        elif self.type == 'PC Number Scroll' or self.type == 'CC Value Scroll':
            PCCCNumberValueScrollBaseModel.get_specific_message(self, backup_message)
            self.name += self.specific_message.from_backup(backup_message)
        elif self.type == 'CC Waveform Generator' or self.type == 'CC Sequence Generator':
            if WaveformSequenceBaseModel.is_stop(backup_message.msg_array_data):
                WaveformSequenceBaseModel.determine_stop_type(self, backup_message.msg_array_data)
                if self.specific_message is not None:
                    self.name += self.specific_message.from_backup(backup_message)
            else:
                WaveformSequenceBaseModel.determine_start_type(self, backup_message.msg_array_data)
                channel = backup_message.channel
                if channel is None:
                    channel = 1
                self.name += self.specific_message.from_backup(backup_message, channel)
        elif self.type == 'Engage Preset':
            self.specific_message = EngagePresetModel()
            self.name += self.specific_message.from_backup(banks, backup_message)
        elif self.type == 'Trigger Messages':
            self.specific_message = TriggerMessagesModel()
            self.name += self.specific_message.from_backup(backup_message, backup_bank)
        elif self.type == 'Bank Up':
            self.name = self.name.replace(':', '')
        elif self.type == 'Bank Down':
            self.name = self.name.replace(':', '')
        elif self.type == 'Bank Change Mode':
            self.name = self.name.replace(':', '')
        elif self.type == 'Toggle Preset':
            self.name = self.name.replace(':', '')
        elif self.type == 'Set Toggle':
            self.specific_message = SetToggleModel()
            self.name += self.specific_message.from_backup(backup_message, backup_bank)
        elif self.type == 'Set MIDI Thru':
            self.specific_message = MIDIThruModel()
            self.name += self.specific_message.from_backup(backup_message)
        elif self.type == 'Select Exp Message':
            self.specific_message = SelectExpMessageModel()
            self.name += self.specific_message.from_backup(backup_message)
        elif self.type == 'Looper Mode':
            if backup_message.msg_array_data is None or backup_message.msg_array_data[0] is None:
                self.specific_message = LooperModeModel()
            else:
                if backup_message.msg_array_data[0] & 3 == 2:
                    self.type = 'Disengage Looper Mode'
                    self.name = self.type + ':'
                    self.specific_message = DisengageLooperModeModel()
                else:
                    self.specific_message = LooperModeModel()
            self.name += self.specific_message.from_backup(backup_message)
        elif self.type == 'Relay Switching':
            self.specific_message = RelaySwitchingModel()
            self.name += self.specific_message.from_backup(backup_message)
        elif self.type == 'SysEx':
            self.specific_message = SysExModel()
            self.name += self.specific_message.from_backup(backup_message)
        else:
            raise IntuitiveException('unrecognized', 'Invalid message type: ' + self.type)

        return self.name

    # Add the MIDI message directly to the backup message
    def to_backup(self, backup_message, message_type, bank_catalog, simple_bank, simple_preset, trigger_enum):
        backup_message.type = message_type.index(self.type)
        backup_message.msg_array_data = [None] * 18
        if self.specific_message is not None:
            self.specific_message.to_backup(backup_message, bank_catalog, simple_bank,
                                            simple_preset)

        # Canonicalize the backup_message
        # Trigger
        if self.trigger is not None:
            backup_message.trigger = trigger_enum.index(self.trigger)
        if backup_message.trigger == 0:
            backup_message.trigger = None
        if self.toggle_state is not None:
            backup_message.toggle_state = SimpleMessage.preset_toggle_state.index(self.toggle_state)
        # msg_array_data: replace 0 elements with None, and truncate to the first non-None element (from the end)
        empty = True
        for pos, elem in enumerate(backup_message.msg_array_data):
            if elem == 0:
                backup_message.msg_array_data[pos] = None
            elif elem is not None:
                empty = False
        if empty:
            backup_message.msg_array_data = None


# MIDI message: This is misnamed, should be controller message?
# It is MIDI messages (PC and CC with one or two values)
# Or controller messages (Jump Bank or Toggle Page with page and bank values)
message_switch_key = jg.SwitchDict.make_key('type',
                                            jg.Enum('Type', simple_message_type,
                                                    simple_message_default, var='type'))
simple_common_keys = [jg.SwitchDict.make_key('name', jg.Atom('Name', str, '', var='name'))]
simple_bank_common_keys = [jg.Dict.make_key('trigger',
                                            jg.Enum('Trigger', simple_model.bank_message_trigger,
                                                    simple_model.bank_message_trigger_default,
                                                    var='trigger'))]
simple_preset_common_keys = [jg.Dict.make_key('trigger',
                                              jg.Enum('Trigger', simple_model.preset_message_trigger,
                                                      simple_model.preset_message_trigger_default,
                                                      var='trigger')),
                             jg.Dict.make_key('toggle_state',
                                              jg.Enum('Toggle', SimpleMessage.preset_toggle_state,
                                                      SimpleMessage.preset_toggle_state_default,
                                                      var='toggle_state'))]

transition_message_case_keys = {
    'PC Multichannel': [PCMultichannelModel,
                        jg.SwitchDict.make_key('multichannel',
                                               jg.List('Multichannel', 0, jg.Atom('Channel', int),
                                                       var='channels')),
                        jg.SwitchDict.make_key('number', jg.Atom('Number', int, var='number'))],
    'Bank Up': [],
    'Bank Down': [],
    'Note On': [NoteOnModel] + NoteOnModel.get_keys(),
    'Note Off': [NoteOffModel] + NoteOffModel.get_keys(),
    'Real Time': [RealTimeModel,
                  jg.SwitchDict.make_key('real_time',
                                         jg.Enum('Real Time', RealTimeModel.realtime_message_type,
                                                 RealTimeModel.realtime_message_default,
                                                 var='real_time_type'))],
    'Song Position': [SongPositionModel,
                      jg.SwitchDict.make_key('song_position',
                                             jg.Atom('Song Position', int, var='song_position'))],
    'MIDI MMC': [MIDIMMCModel,
                 jg.SwitchDict.make_key('MMC Type',
                                        jg.Enum('MMC Type', MIDIMMCModel.midi_mmc_enum, MIDIMMCModel.midi_mmc_default,
                                                var='midi_mmc_type'))],
    'MIDI Clock': [MIDIClockModel,
                   jg.SwitchDict.make_key('stop_clock',
                                          jg.Atom('Stop MIDI Clock', bool, var='stop_clock')),
                   jg.SwitchDict.make_key('bpm', jg.Atom('BPM', int, 0, var='bpm')),
                   jg.SwitchDict.make_key('bpm_decimal',
                                          jg.Enum('BPM Decimal', MIDIClockModel.bpm_decimal_enum,
                                                  MIDIClockModel.bpm_decimal_default,
                                                  var='bpm_decimal'))],
    'MIDI Clock Tap Menu': [MIDIClockTapMenuModel,
                            jg.SwitchDict.make_key('use_current_bpm',
                                                   jg.Atom('Use Current BPM', bool, var='use_current_bpm')),
                            jg.SwitchDict.make_key('bpm', jg.Atom('BPM', int, 0, var='bpm')),
                            jg.SwitchDict.make_key('bpm_decimal',
                                                   jg.Enum('BPM Decimal', MIDIClockModel.bpm_decimal_enum,
                                                           MIDIClockModel.bpm_decimal_default,
                                                           var='bpm_decimal'))],
    'MIDI Clock Tap': [],
    'Relay Switching': [RelaySwitchingModel,
                        jg.SwitchDict.make_key('relay',
                                               jg.Enum('Relay', RelaySwitchingModel.relay_type,
                                                       RelaySwitchingModel.relay_default, var='relay')),
                        jg.SwitchDict.make_key('tip_action',
                                               jg.Enum('Tip Action', RelaySwitchingModel.tip_ring_action_type,
                                                       RelaySwitchingModel.tip_ring_action_default, var='tip_action')),
                        jg.SwitchDict.make_key('ring_action',
                                               jg.Enum('Ring Action', RelaySwitchingModel.tip_ring_action_type,
                                                       RelaySwitchingModel.tip_ring_action_default,
                                                       var='ring_action'))],
    'Set MIDI Thru': [MIDIThruModel,
                      jg.SwitchDict.make_key('value',
                                             jg.Enum('Set MIDI Thru', onoff_type, onoff_default, var='value'))],
    'PC Number Scroll': [PCNumberScrollModel] + PCNumberScrollModel.get_keys(),
    'CC Value Scroll': [CCValueScrollModel] + CCValueScrollModel.get_keys(),
    'PC Number Scroll Update': [PCNumberScrollUpdateModel] + PCNumberScrollUpdateModel.get_keys(),
    'CC Value Scroll Update': [PCNumberScrollUpdateModel] + CCValueScrollUpdateModel.get_keys(),
    'Bank Change Mode': [],
    'Stop CC Waveform Generator': [StopWaveformModel] + StopWaveformModel.get_keys(),
    'Stop CC Sequence Generator': [StopSequenceModel] + StopSequenceModel.get_keys(),
    'Stop All CC Waveform Generator': [StopAllWaveformModel],
    'Stop All CC Sequence Generator': [StopAllSequenceModel],
    'Start CC Waveform Generator': [StartWaveformModel] + StartWaveformModel.get_keys(),
    'Start CC Sequence Generator': [StartSequenceModel] + StartSequenceModel.get_keys(),
    'Start CC Waveform Generator No MIDI Clock':
        [StartWaveformNoMIDIClockModel] + StartWaveformNoMIDIClockModel.get_keys(),
    'Start CC Sequence Generator No MIDI Clock':
        [StartSequenceNoMIDIClockModel] + StartSequenceNoMIDIClockModel.get_keys(),
    'Engage Preset': [EngagePresetModel,
                      jg.SwitchDict.make_key('bank', jg.Atom('Bank', str, var='bank')),
                      jg.SwitchDict.make_key('preset', jg.Atom('Preset', str, var='preset')),
                      jg.SwitchDict.make_key('Action',
                                             jg.Enum('Action', EngagePresetModel.engage_preset_action,
                                                     EngagePresetModel.engage_preset_action_default,
                                                     var='action'))],
    'Toggle Preset': [],
    'Set Toggle': [SetToggleModel,
                   jg.SwitchDict.make_key('position',
                                          jg.Enum('Position', SetToggleModel.set_toggle_type,
                                                  SetToggleModel.set_toggle_default,
                                                  var='position')),
                   jg.SwitchDict.make_key('presets',
                                          jg.List('Presets', 24, jg.Atom('Preset', str), var='presets'))],
    'Trigger Messages': [TriggerMessagesModel,
                         jg.SwitchDict.make_key('preset', jg.Atom('Preset', str, var='preset')),
                         jg.SwitchDict.make_key('messages',
                                                jg.List('Messages', 32, jg.Atom('Message', str),
                                                        var='messages'))],
    'Select Exp Message': [SelectExpMessageModel,
                           jg.SwitchDict.make_key('input', jg.Atom('Input', int, 1, var='input')),
                           jg.SwitchDict.make_key('messages',
                                                  jg.List('Messages', 32, jg.Atom('Message', str),
                                                          var='messages'))],
    'Looper Mode': [LooperModeModel,
                    jg.SwitchDict.make_key('Mode', jg.Enum('Mode', LooperModeModel.looper_mode,
                                                           LooperModeModel.looper_mode_default, var='mode')),
                    jg.SwitchDict.make_key('Selected Switches', jg.Atom('Selected Switches', bool, False,
                                                                        var='selected_switches')),
                    jg.SwitchDict.make_key('switches',
                                           jg.List('Switches', 6, jg.Atom('Switch', str), var='switches')),
                    jg.SwitchDict.make_key('disable_message',
                                           jg.Atom('Disable Message', bool, False, var='disable_message'))],
    'Disengage Looper Mode': [DisengageLooperModeModel,
                              jg.SwitchDict.make_key('disable_message',
                                                     jg.Atom('Disable Message', bool, False,
                                                             var='disable_message'))],
    'SysEx': [SysExModel,
              jg.SwitchDict.make_key('data',
                                     jg.List('Data', 18, jg.Atom('Data Element', int), var='data'))]
}


# TODO: Cleanup
# Transition code: the message_case_keys is a constant
# We need it to vary, depending on if it is a backup, simple, or intuitive/config use
# For now, we copy all the constant elements, and then remove the ones we need to modify one at a time
# This starts with the PC/CC messages
# def make_message_case_keys(intuitive=False):
#     case_keys = copy.deepcopy(transition_message_case_keys)
#     for message_type in SimpleMessage.to_bank_classes:
#         case_keys[message_type] = SimpleMessage.to_bank_classes[message_type].get_case_keys(intuitive)
#     return case_keys
#
def make_message_case_keys():
    case_keys = copy.deepcopy(transition_message_case_keys)
    for message_type in SimpleMessage.to_bank_classes:
        case_keys[message_type] = SimpleMessage.to_bank_classes[message_type].get_case_keys()
    return case_keys


def mk_message_schema(common_keys=None):
    if common_keys is None:
        common_keys = simple_common_keys
    return jg.SwitchDict('message_schema', message_switch_key,
                         make_message_case_keys(), common_keys,
                         model=SimpleMessage, model_var='specific_message')


simple_bank_message_schema = mk_message_schema(simple_bank_common_keys)

simple_preset_message_schema = mk_message_schema(simple_preset_common_keys)
