import grammar as jg
from version import version_verify
import colors
import simple_message as sm
import simple_model
import intuitive_model


system_schema = \
    jg.Dict('system',
            [jg.Dict.make_key('version', jg.Atom('Version', str, value=version_verify), required=True),
             jg.Dict.make_key('midi_channel', jg.Atom('MIDIChannel', int, var='midi_channel'))])

palette_schema = jg.Dict('palette',
                         [jg.Dict.make_key('name', jg.Atom('name', str, var='name'), required=True),
                          jg.Dict.make_key('text', colors.make_enum('TextColor', 'default', var='text')),
                          jg.Dict.make_key('background', colors.make_enum('BackgroundColor', 'default',
                                                                          var='background')),
                          jg.Dict.make_key('bank_text', colors.make_enum('BankTextColor', 'default', var='bank_text')),
                          jg.Dict.make_key('bank_background', colors.make_enum('BankBackgroundColor', 'default',
                                                                               var='bank_background')),
                          jg.Dict.make_key('preset_text', colors.make_enum('PresetTextColor', 'default',
                                                                           var='preset_text')),
                          jg.Dict.make_key('preset_background', colors.make_enum('PresetBackgroundColor', 'default',
                                                                                 var='preset_background')),
                          jg.Dict.make_key('preset_shifted_text', colors.make_enum('PresetShiftedTextColor', 'default',
                                                                                   var='preset_shifted_text')),
                          jg.Dict.make_key('preset_shifted_background',
                                           colors.make_enum('PresetShiftedBackgroundColor', 'default',
                                                            var='preset_shifted_background')),
                          jg.Dict.make_key('preset_toggle_text', colors.make_enum('PresetToggleTextColor', 'default',
                                                                                  var='preset_toggle_text')),
                          jg.Dict.make_key('preset_toggle_background',
                                           colors.make_enum('PresetToggleBackgroundColor', 'default',
                                                            var='preset_toggle_background')),
                          jg.Dict.make_key('preset_led', colors.make_enum('PresetLedColor', 'default',
                                                                          var='preset_led')),
                          jg.Dict.make_key('preset_led_shifted', colors.make_enum('PresetLedShiftedColor', 'default',
                                                                                  var='preset_led_shifted')),
                          jg.Dict.make_key('preset_led_toggle', colors.make_enum('PresetLedToggleColor', 'default',
                                                                                 var='preset_led_toggle')),],
                         model=colors.PaletteModel)

palettes_schema = jg.List('palettes', 0, palette_schema, var='palettes')

message_switch_key = jg.SwitchDict.make_key('type',
                                            jg.Enum('Type', intuitive_model.message_type,
                                                    intuitive_model.message_type_default, var='type'))
message_common_keys = [jg.SwitchDict.make_key('name', jg.Atom('Name', str, '', var='name')),
                       jg.SwitchDict.make_key('setup', jg.Atom('Setup', str, '', var='setup'))]
message_case_keys = {'PC': [intuitive_model.PCModel,
                            jg.SwitchDict.make_key('number', jg.Atom('Number', int, var='number')),
                            jg.SwitchDict.make_key('channel', jg.Atom('Channel', str, var='channel'))],
                     'CC': [intuitive_model.CCModel,
                            jg.SwitchDict.make_key('number', jg.Atom('Number', int, var='number')),
                            jg.SwitchDict.make_key('value', jg.Atom('Value', int, var='value')),
                            jg.SwitchDict.make_key('channel', jg.Atom('Channel', str, var='channel'))]}


def make_message_schema(var=None):
    return jg.SwitchDict('message_schema', message_switch_key, message_case_keys, message_common_keys,
                         model=intuitive_model.MessageModel, model_var='specific_message', var=var)


device_group_schema = jg.Dict('device group',
                              [jg.Dict.make_key('name', jg.Atom('Name', str, '', var='name')),
                               jg.Dict.make_key('messages', jg.List('messages', 0, jg.Atom('message name', str),
                                                                    var='messages'))],
                              model=intuitive_model.DeviceGroupModel)

device_schema = jg.Dict('device',
                        [jg.Dict.make_key('name', jg.Atom('name', str, var='name')),
                         jg.Dict.make_key('channel', jg.Atom('channel', int, var='channel')),
                         jg.Dict.make_key('messages', jg.List('messages', 0,
                                                              make_message_schema(), var='messages')),
                         jg.Dict.make_key('enable', make_message_schema('enable_message')),
                         jg.Dict.make_key('bypass', make_message_schema('bypass_message')),
                         jg.Dict.make_key('initial', jg.List('initial', 0,
                                                             jg.Atom('message', str), var='initial')),
                         jg.Dict.make_key('groups', jg.List('groups', 0, device_group_schema, var='groups'))],
                        model=intuitive_model.DeviceModel)

devices_schema = jg.List('devices', 0, device_schema, var='devices')

preset_action = jg.Dict('preset action',
                        [jg.Dict.make_key('name', jg.Atom('name', str, var='name')),
                         jg.Dict.make_key('trigger', jg.Enum('trigger_enum', simple_model.preset_message_trigger,
                                                             "Press",
                                                             var='trigger'))],
                        model=intuitive_model.PresetActionModel)

bank_action = jg.Dict('bank action',
                      [jg.Dict.make_key('name', jg.Atom('name', str, var='name')),
                       jg.Dict.make_key('trigger', jg.Enum('trigger_enum', simple_model.bank_message_trigger,
                                                           "On Enter Bank", var='trigger'))],
                      model=intuitive_model.BankActionModel)

scroll_action_schema = jg.Dict('scroll action',
                               [jg.Dict.make_key('name', jg.Atom('name', str)),
                                jg.Dict.make_key('action', jg.Atom('action', str))])

preset_switch_key = jg.SwitchDict.make_key('type',
                                           jg.Enum('Type', intuitive_model.preset_type,
                                                   intuitive_model.preset_type_default, var='type'))
preset_common_keys = [jg.Dict.make_key('palette', jg.Atom('palette', str, var='palette'))]
preset_case_keys = {
    'vanilla': [jg.SwitchDict.make_key('short_name', jg.Atom('short_name', str, var='short_name')),
                jg.SwitchDict.make_key('actions', jg.List('action list', 0, preset_action, var='actions')),
                ],
    'bypass': [jg.SwitchDict.make_key('device', jg.Atom('device', str, var='device'), required=True)],
    'scroll': [jg.SwitchDict.make_key('actions', jg.List('actions', 0, scroll_action_schema, var='actions'))],
    'cycle': [jg.SwitchDict.make_key('action', jg.Atom('action', str, var='action')),
              jg.SwitchDict.make_key('values', jg.List('values', 0, jg.Atom('value', int), var='values')),
              jg.SwitchDict.make_key('names', jg.List('names', 0, jg.Atom('name', str), var='names')),
              jg.SwitchDict.make_key('prefix', jg.Atom('prefix', str, var='prefix')),
              jg.SwitchDict.make_key('show', jg.Enum('Show Enum', intuitive_model.show_enum,
                                                     intuitive_model.show_enum_default, var='show'))],
    'empty': []
}

preset_schema = jg.SwitchDict('preset', preset_switch_key, preset_case_keys, preset_common_keys,
                              model=intuitive_model.PresetModel)

bank_schema = jg.Dict('bank',
                      [jg.Dict.make_key('name', jg.Atom('name', str, var='name')),
                       jg.Dict.make_key('description', jg.Atom('description', str, var='description')),
                       jg.Dict.make_key('palette', jg.Atom('palette', str, var='palette')),
                       jg.Dict.make_key('presets', jg.List('preset list', 0, preset_schema, var='presets')),
                       jg.SwitchDict.make_key('actions', jg.List('actions', 0, bank_action, var='actions'))],
                      model=intuitive_model.BankModel)

banks_schema = jg.List('bank list', 0, bank_schema, var='banks')

intuitive_schema = \
    jg.Dict('intuitive',
            [jg.Dict.make_key('system', system_schema, required=True),
             jg.Dict.make_key('palettes', palettes_schema),
             jg.Dict.make_key('devices', devices_schema),
             jg.Dict.make_key('banks', banks_schema)],
            model=intuitive_model.Intuitive)
