import grammar as jg
import IntuitiveException


colors = ["black", "lime", "blue", "purple", "yellow", "orchid", "gray", "white",
          "orange", "red", "skyblue", "deeppink", "olivedrab", "mediumslateblue", "darkgreen", "green",
          "color16", "color17", "color18", "color19", "color20", "color21", "color22", "color23",
          "color24", "color25", "color26", "color27", "color28", "aqua", "turquoise", "cadetblue",
          "steelblue", "lightsteelblue", "tan", "brown", "cornsilk", "maroon", "lavender", "teal",
          "darkseagreen", "forestgreen", "olive", "indigo", "blueviolet", "thistle", "rebeccapurple", "gold",
          "khaki", "darkkhaki", "lightyellow", "lightsalmon", "tomato", "orangered", "darkorange", "indianred",
          "salmon", "firebrick", "darkred", "lightpink", "hotpink", "palevioletred", "slategray", "lightgray",
          "color64", "color65", "color66", "color67", "color68", "color69", "color70", "color71",
          "color72", "color73", "color74", "color75", "color76", "color77", "color78", "color79",
          "color80", "color81", "color82", "color83", "color84", "color85", "color86", "color87",
          "color88", "color89", "color90", "color91", "color92", "color93", "color94", "color95",
          "color96", "color97", "color98", "color99", "color100", "color101", "color102", "color103",
          "color104", "color105", "color106", "color107", "color108", "color109", "color110", "color111",
          "color112", "color113", "color114", "color115", "color116", "color117", "color118", "color119",
          "color120", "color121", "color122", "color123", "color124", "color125", "color126", "default"]
default_color = colors[7]
empty_color = colors[0]


def make_enum(name, default=default_color, var=None):
    return jg.Enum(name, colors, default, var=var)


class PaletteModel(jg.GrammarModel):
    def __init__(self):
        super().__init__('PaletteModel')
        self.name = None
        self.text = None
        self.background = None
        self.bank_text = None
        self.bank_background = None
        self.preset_text = None
        self.preset_background = None
        self.preset_shifted_text = None
        self.preset_shifted_background = None
        self.preset_toggle_text = None
        self.preset_toggle_background = None
        self.preset_led = None
        self.preset_led_shifted = None
        self.preset_led_toggle = None

    # Do not check version in equality
    def __eq__(self, other):
        result = (isinstance(other, PaletteModel) and self.text == other.text and
                  self.background == other.background and
                  self.preset_text == other.preset_text and self.preset_background == other.preset_background and
                  self.preset_shifted_text == other.preset_shifted_text and
                  self.preset_shifted_background == other.preset_shifted_background and
                  self.preset_toggle_text == other.preset_toggle_text and
                  self.preset_toggle_background == other.preset_toggle_background and
                  self.preset_led == other.preset_led and self.preset_led_shifted == other.preset_led_shifted and
                  self.preset_led_toggle == other.preset_led_toggle)
        if not result:
            self.modified = True
        return result


class Palettes:
    def __init__(self, palettes):
        self.palettes = {}
        self.default = None
        self.bypass = None
        if palettes is not None:
            for palette in palettes:
                self.palettes[palette.name] = palette
        if 'default' in self.palettes:
            self.default = self.palettes['default']
        if 'bypass' in self.palettes:
            self.bypass = self.palettes['bypass']

    def lookup_palette(self, palette_name, default_palette=None):
        palette = None
        if palette_name is not None:
            if palette_name not in self.palettes:
                raise IntuitiveException.IntuitiveException('no-palette', 'Palette does not exist: %s' % palette_name)
            palette = self.palettes[palette_name]
        if palette is None:
            if default_palette is not None:
                palette = default_palette
            elif 'default' in self.palettes:
                palette = self.default
        if palette is None:
            return None
        if palette.bank_text is None:
            palette.bank_text = palette.text
        if palette.bank_background is None:
            palette.bank_background = palette.background
        if palette.preset_text is None:
            palette.preset_text = palette.text
        if palette.preset_background is None:
            palette.preset_background = palette.background
        if palette.preset_shifted_text is None:
            palette.preset_shifted_text = palette.text
        if palette.preset_shifted_background is None:
            palette.preset_shifted_background = palette.background
        if palette.preset_toggle_text is None:
            palette.preset_toggle_text = palette.text
        if palette.preset_toggle_background is None:
            palette.preset_toggle_background = palette.background
        return palette
