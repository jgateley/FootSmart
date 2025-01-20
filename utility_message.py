import grammar as jg
import simple_message
from IntuitiveException import IntuitiveException

utility_message_type = ["Set Message Scroll Counter", "Clear Global Preset Toggles", "Increase MIDI Clock BPM by 1",
                        "Decrease MIDI Clock BPM by 1", "Set Scroll Counter Values", "Set MIDI Output Mask",
                        "Manage Preset Scroll", "Set Bank Background/Text Color",
                        "Set Preset Background/Text/Strip Color", "no default"]
preset_enum = ['A', 'B', 'C', 'D', 'E', 'F',
               'G', 'H', 'I', 'J', 'K', 'L',
               'M', 'N', 'O', 'P', 'Q', 'R',
               'S', 'T', 'U', 'V', 'W', 'X']
msg_scroll_position = ['Msg 1', 'Msg 2', 'Msg 3', 'Msg 4', 'Msg 5', 'Msg 6', 'Msg 7', 'Msg 8',
                       'Msg 9', 'Msg 10', 'Msg 11', 'Msg 12', 'Msg 13', 'Msg 14', 'Msg 15', 'Msg 16',
                       'Msg 17', 'Msg 18', 'Msg 19', 'Msg 20', 'Msg 21', 'Msg 22', 'Msg 23', 'Msg 24',
                       'Msg 25', 'Msg 26', 'Msg 27', 'Msg 28', 'Msg 29', 'Msg 30', 'Msg 31', 'Msg 32',
                       'Reset']
set_scroll_counter_type = ['', '', '', 'Update', 'Reset', 'Increase', 'Decrease']
manage_preset_scroll_type = ["Do Nothing", "Toggle Scroll Direction",
                             "Toggle Scroll Direction and Execute",
                             "Reverse Direction Once and Execute", "Set number of messages to scroll"]

# Set Scroll Counter Values:
# Step values: 1 to 63
# Decrease Counter 3 by 4 with wraparound: 4, 99, 68 -- 0x4, 0x63, 0x44
# Decrease Counter 3 by 4 with no wraparound, 4, 99, 4 -- 0x4, 0x63, 0x04
# Decrease Counter 3 by 1 with no wraparound, 4, 99, 1 -- 0x4, 0x63, 0x01
# Decrease Counter 3 by 43 with no wraparound 4, 99, 63 -- 0x4, 0x63, 0x3F
# Decrease Counter 0 by 4 with no wraparound 4, 96, 4 -- 0x4, 0x60, 0x04
# Decrease Counter F by 4 with no wraparound 4, 111, 4 -- 0x4 0x6f 0x04
# Increase Counter 3 by 4 with no wraparound 4, 83, 4 -- 0x4, 0x53, 0x04
# Update Counter 3 by 5,  4, 51, None, 5 -- 0x04, 0x33, None, 0x05
# Reset Counter 5,   4, 69 -- 0x04, 0x45
# Opcode, byte 1, high nybble
#   Decrease: 0x6-
#   Increase: 0x5-
#   Update:   0x3-
#   Reset:    0x4-
# Byte 1, low nybble:
#   Reset: counter number
#   Update: Counter number
#   Increase: Counter number
#   Decrease: Counter number
# Byte 2:
#   Reset: not used
#   Update: not used
#   Increase/Decrease: 0x40 is the wraparound bit
#                      0x3F is the mask for the step
# Byte 3, only update, amount to update to

# Set MIDI Output Mask values
# DIN MIDI5, USB MIDI Port: No 1, 2, No 3, 4, No USB Host, 3.5MM MIDI, Omniport 1, no 2, 3, 4
# 1 0101 0 1 1011
# 101 0101 1011 or x75 xB
# 5, None, 117, 5
# All: 5, None 127, 15 - 0x7F 0x0F
# None: 5 None,
# 126 15: no DIN5 = 7E F ~ 0000 0001 0000
# 125 15 no USB port 1 = 7D F ~ 0000 0010 0000
# 127 14 no USB port 2 = 7F E ~ 0000 0000 0001
# 127 13, no usb port 3 = 7F D ~ 0000 0000 0010
# 127 11 no usb port 4 = 7F B ~ 0000 0000 0100
# 127 7 usb host = 7F 7 ~ 0000 0000 1000
# 63 15 3.5mm midi = 41 F/0100 0001 1111 ~ 0011 1110 0000
# 123 15 omni 1 = 7B F/0111 1011 1111 ~ 0000 0100 0000
# 119 15, omni 2 = 77 F/0111 0111 1111 ~ 0000 1000 0000
# 111 15 omni 3 = 6F F/0110 1111 1111 ~ 0001 0000 0000
# 95 15 omni 4 =  5F F/0101 1111 1111 ~ 0010 0000 0000
# 64 4 only 3.5MIDI 40 4


class UtilityModel(jg.GrammarModel):
    @staticmethod
    def build_from_backup(psimple_message, backup_message):
        psimple_message.specific_message = UtilityModel()
        psimple_message.name += psimple_message.specific_message.from_backup(backup_message)

    @staticmethod
    def build_manage_preset_scroll(number_messages=None, reverse=None):
        result = UtilityModel()
        result.utility_type = "Manage Preset Scroll"
        if number_messages is not None:
            result.manage_preset_scroll = "Set number of messages to scroll"
            result.preset_scroll_message_count = number_messages
        elif reverse is not None:
            result.manage_preset_scroll = "Toggle Scroll Direction and Execute"
        else:
            raise IntuitiveException('programmer error', "Please provide number of messages or reverse direction")
        return result

    @staticmethod
    def get_case_keys(_intuitive=False):
        return [UtilityModel,
                jg.SwitchDict.make_key('utility_type', jg.Enum('Type', utility_message_type,
                                                               'no default', var='utility_type')),
                jg.SwitchDict.make_key('preset', jg.Enum('Preset', preset_enum, preset_enum[0], var='preset')),
                jg.SwitchDict.make_key('message scroll position', jg.Enum('Message Scroll Position',
                                                                          msg_scroll_position, msg_scroll_position[0],
                                                                          var='message_scroll_position')),
                jg.SwitchDict.make_key('manage preset scroll subtype',
                                       jg.Enum('Manage Preset Scroll Subtype',
                                               manage_preset_scroll_type, manage_preset_scroll_type[0],
                                               var='manage_preset_scroll')),
                jg.SwitchDict.make_key('set scroll counter', jg.Enum('Set Scroll Counter',
                                                                     set_scroll_counter_type, '',
                                                                     var='set_scroll_counter')),
                jg.SwitchDict.make_key('counter', jg.Atom('counter', int, 0, var='counter')),
                jg.SwitchDict.make_key('wraparound', jg.Atom('wraparound', int, 0, var='wraparound')),
                jg.SwitchDict.make_key('step', jg.Atom('step', int, 0, var='step')),
                jg.SwitchDict.make_key('update', jg.Atom('update', int, 0, var='update')),
                jg.SwitchDict.make_key('mask byte 1', jg.Atom('mask byte 1', int, 0, var='mask_byte_1')),
                jg.SwitchDict.make_key('mask byte 2', jg.Atom('mask byte 2', int, 0, var='mask_byte_2')),
                jg.SwitchDict.make_key('background color', jg.Atom('background color', int, 0, var='background_color')),
                jg.SwitchDict.make_key('text color', jg.Atom('text color', int, 0, var='text_color')),
                jg.SwitchDict.make_key('strip color', jg.Atom('strip color', int, 0, var='strip_color')),
                jg.SwitchDict.make_key('preset scroll message count', jg.Atom('preset scroll message count', int, 0,
                                                                              var='preset_scroll_message_count'))]

    def __init__(self):
        super().__init__('UtilityModel')
        self.utility_type = None
        self.preset = None
        self.message_scroll_position = None
        self.preset_scroll_message_count = None
        self.manage_preset_scroll = None
        self.background_color = None
        self.text_color = None
        self.strip_color = None
        self.set_scroll_counter = None
        self.counter = None
        self.wraparound = None
        self.step = None
        self.update = None
        self.mask_byte_1 = None
        self.mask_byte_2 = None

    def __eq__(self, other):
        result = (isinstance(other, UtilityModel) and self.utility_type == other.utility_type and
                  self.preset == other.preset and self.message_scroll_position == other.message_scroll_position and
                  self.preset_scroll_message_count == other.preset_scroll_message_count and
                  self.manage_preset_scroll == other.manage_preset_scroll and
                  self.background_color == other.background_color and self.text_color == other.text_color and
                  self.strip_color == other.strip_color and
                  self.set_scroll_counter == other.set_scroll_counter and self.counter == other.counter and
                  self.wraparound == other.wraparound and self.step == other.step and self.update == other.update and
                  self.mask_byte_1 == other.mask_byte_1 and self.mask_byte_2 == other.mask_byte_2)
        if not result:
            self.modified = True
        return result

    def from_backup(self, backup_message):
        type_index = backup_message.msg_array_data[0]
        if type_index is None:
            type_index = 0
        self.utility_type = utility_message_type[type_index]
        name = self.utility_type
        if self.utility_type == 'Set Message Scroll Counter':
            preset = backup_message.msg_array_data[1]
            if preset is None:
                preset = 0
            self.preset = preset_enum[preset]
            name += ':' + self.preset
            message_scroll_position = backup_message.msg_array_data[2]
            if message_scroll_position is None:
                message_scroll_position = 0
            if message_scroll_position > 32:
                message_scroll_position = 32
            self.message_scroll_position = msg_scroll_position[message_scroll_position]
            name += ':' + self.message_scroll_position
        elif self.utility_type == 'Clear Global Preset Toggles':
            pass
        elif self.utility_type == 'Increase MIDI Clock BPM by 1':
            pass
        elif self.utility_type == 'Decrease MIDI Clock BPM by 1':
            pass
        elif self.utility_type == 'Set Scroll Counter Values':
            self.set_scroll_counter = set_scroll_counter_type[backup_message.msg_array_data[1] >> 4]
            self.counter = backup_message.msg_array_data[1] & 0xF
            name += ':' + self.set_scroll_counter + ':' + str(self.counter)
            if self.counter == 0:
                self.counter = None
            if backup_message.msg_array_data[2] is not None:
                self.wraparound = backup_message.msg_array_data[2] & 0x40
                if self.wraparound:
                    name += ':wrap'
                else:
                    name += ':nowrap'
                if not self.wraparound:
                    self.wraparound = None
                self.step = backup_message.msg_array_data[2] & 0x3F
                name += ':' + str(self.step)
            if backup_message.msg_array_data[3] is not None:
                self.update = backup_message.msg_array_data[3]
        elif self.utility_type == 'Set MIDI Output Mask':
            self.mask_byte_1 = backup_message.msg_array_data[2]
            self.mask_byte_2 = backup_message.msg_array_data[3]
            name += ':' + str(self.mask_byte_1) + ':' + str(self.mask_byte_2)
        elif self.utility_type == "Manage Preset Scroll":
            # Manage preset scroll
            subtype = backup_message.msg_array_data[1]
            if subtype is None:
                subtype = 0
            self.manage_preset_scroll = manage_preset_scroll_type[subtype]
            name += ':' + self.manage_preset_scroll
            if subtype == 4:
                self.preset_scroll_message_count = backup_message.msg_array_data[2]
                name += ':' + str(self.preset_scroll_message_count)
        elif self.utility_type == 'Set Preset Background/Text/Strip Color':
            # We could turn these into text colors, but there are many more than I currently have
            # I think (dim) is a factor here
            # 140 is 8C, and is palevioletred (dim)
            # palevioletred is 61 and 3D
            self.background_color = backup_message.msg_array_data[1]
            self.text_color = backup_message.msg_array_data[2]
            self.strip_color = backup_message.msg_array_data[3]
            name += ':' + str(self.background_color) + ':' + str(self.text_color) + ':' + str(self.strip_color)
        elif self.utility_type == "Set Bank Background/Text Color":
            self.background_color = backup_message.msg_array_data[1]
            self.text_color = backup_message.msg_array_data[2]
            name += ':' + str(self.background_color) + ':' + str(self.text_color)
        else:
            raise IntuitiveException('Not implemented')
        return name

    # TODO: Can we remove bank_catalog from to_backup parameter list?
    # TODO: general cleanup on this list, some may not be required
    def to_backup(self, backup_message, _bank_catalog, _simple_bank, _simple_preset):
        backup_sets = [0]*4
        backup_message.type = simple_message.simple_message_type.index("Utility")
        backup_message.msg_array_data[0] = utility_message_type.index(self.utility_type)
        if self.preset is not None and self.preset != 'A':
            backup_sets[1] += 1
            backup_message.msg_array_data[1] = preset_enum.index(self.preset)
        if self.manage_preset_scroll is not None and self.manage_preset_scroll != 'Do Nothing':
            backup_sets[1] += 1
            backup_message.msg_array_data[1] = manage_preset_scroll_type.index(self.manage_preset_scroll)
        if self.background_color is not None and self.background_color != 0:
            backup_sets[1] += 1
            backup_message.msg_array_data[1] = self.background_color
        if self.set_scroll_counter is not None and self.set_scroll_counter != '':
            backup_sets[1] += 1
            backup_message.msg_array_data[1] = set_scroll_counter_type.index(self.set_scroll_counter) << 4
            if self.counter is not None:
                backup_message.msg_array_data[1] |= self.counter
        elif self.counter is not None and self.counter != 0:
            raise IntuitiveException('Not valid')
        if self.message_scroll_position is not None and self.message_scroll_position != 'Msg 1':
            backup_sets[2] += 1
            backup_message.msg_array_data[2] = msg_scroll_position.index(self.message_scroll_position)
            if backup_message.msg_array_data[2] > 31:
                backup_message.msg_array_data[2] = 127
        if self.preset_scroll_message_count is not None and self.preset_scroll_message_count != 0:
            if self.preset_scroll_message_count < 0 or self.preset_scroll_message_count > 8:
                raise IntuitiveException('Not valid', 'Preset Scroll Message Count out of range')
            backup_sets[2] += 1
            backup_message.msg_array_data[2] = self.preset_scroll_message_count
        if self.text_color is not None and self.text_color != 0:
            backup_sets[2] += 1
            backup_message.msg_array_data[2] = self.text_color
        if (self.wraparound is not None and self.wraparound != 0) or (self.step is not None and self.step != 0):
            backup_sets[2] += 1
            if self.wraparound:
                backup_message.msg_array_data[2] = 0x40
            else:
                backup_message.msg_array_data[2] = 0
            if self.step:
                backup_message.msg_array_data[2] |= self.step
        if self.mask_byte_1 is not None and self.mask_byte_1 != 0:
            backup_sets[2] += 1
            backup_message.msg_array_data[2] = self.mask_byte_1
        if backup_message.msg_array_data[0] == 1:
            # I don't know what this 6 is
            backup_message.msg_array_data[2] = 6
        if self.strip_color is not None and self.strip_color != 0:
            backup_sets[3] += 1
            backup_message.msg_array_data[3] = self.strip_color
        if self.update is not None and self.update != 0:
            backup_sets[3] += 1
            backup_message.msg_array_data[3] = self.update
        if backup_sets[1] > 1 or backup_sets[2] > 1 or backup_sets[3] > 1:
            raise IntuitiveException('Not valid')
        if self.mask_byte_2 is not None and self.mask_byte_2 != 0:
            backup_sets[3] += 1
            backup_message.msg_array_data[3] = self.mask_byte_2
        # check backup_sets
        if backup_sets[0] > 1 or backup_sets[1] > 1 or backup_sets[2] > 1 or backup_sets[3] > 1:
            raise IntuitiveException('Not valid')
