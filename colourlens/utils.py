import colorsys
import webcolors
from cooperhewitt import swatchbook
from colormath.color_objects import RGBColor
from decimal import Decimal

COLOURS = {
    'RED': ((255, 0, 0), (340, 17), (10, 100), (40, 100)),
    'ORANGE': ((252, 106, 8), (18, 45), None, (66, 100)),
    'YELLOW': ((255, 255, 0), (46, 66), None, (76, 100)),
    'LIME': ((0, 255, 0), (67, 165), (15, 100), (66, 100)),
    'CYAN': ((0, 255, 255), (166, 201), (15, 100), (66, 100)),
    'BLUE': ((0, 0, 255), (202, 260), None, (66, 100)),
    'MAGENTA': ((255, 0, 255), (261, 339), None, (66, 100)),
    'MAROON': ((128, 0, 0), (340, 17), (20, 100), (24, 65)),
    'BROWN':  ((107, 48, 2), (18, 45), None, (26, 65)),
    'OLIVE': ((128, 128, 0), (46, 66), (26, 100), (26, 81)),
    'GREEN': ((0, 128, 0), (67, 165), None, (18, 65)),
    'TEAL': ((0, 128, 128), (166, 201), None, (33, 65)),
    'NAVY': ((0, 0, 128), (202, 260), None, (18, 65)),
    'PURPLE': ((128, 0, 128), (261, 339), None, (33, 65)),
}
GREYSCALE = {
    'BLACK': ((0, 0, 0), (0, 359), (0, 100), (0, 17)),
    'WHITE': ((255, 255, 255), (0, 359), (0, 5), (90, 100)),
    'SILVER': ((192, 192, 192), (0, 359), (0, 10), (61, 89)),
    'GREY': ((128, 128, 128), (0, 359), (0, 10), (26, 60)),
}

DEFAULT_SAT = (25, 100)
DEFAUL_VAL = (50, 100)

TWOPLACES = Decimal(10) ** -2


class ArtColour:

    hsv = ()
    rgb = ()
    hex_value = ()
    css = ()
    ansi = ()
    ansi_rgb = ()
    ansi_hsv = ()
    _color = None
    GREY = False
    distance = None
    prominence = None

    def __init__(self, r, g, b, prominence):

        self.rgb = (r, g, b)
        self.prominence = prominence
        (self.red, self.blue, self.green) = (r, g, b)
        self.hsv = self.rgb_to_hsv(r, g, b)
        (self.hue, self.sat, self.val) = \
            (self.hsv[0], self.hsv[1], self.hsv[2])
        self.ansi = self.ansi_number(r, g, b)
        self.ansi_rgb = self.rgb_reduce(r, g, b)
        self.ansi_hsv = self.rgb_to_hsv(*self.ansi_rgb)
        self.hex_value = None
        self.nearest_hex = None

    def rgb_to_hsv(self, r, g, b):

        fracs = [ch/255.0 for ch in (r, g, b)]
        hsv = colorsys.rgb_to_hsv(*fracs)
        return (int(round(hsv[0] * 360)),
                int(round(hsv[1] * 100)),
                int(round(hsv[2] * 100)))

    def hsv_to_rgb(self, h, s, v):

        rgb = colorsys.hsv_to_rgb(h/360.0, s/100.0, v/100.0)

        return (int(round(rgb[0] * 255)),
                int(round(rgb[1] * 255)),
                int(round(rgb[2] * 255)))

    def rgb_reduce(self, r, g, b):

        reduced_rgb = [int(6 * float(val) / 256)
                       * (256/6) for val in (r, g, b)]
        return tuple(reduced_rgb)

    def spin(self, deg):
        return (deg + 180) % 360 - 180

    @property
    def color(self):
        if self._color is None:
            self._color = self._get_color()
        return self._color

    def _get_color(self):

        self.nearest = None
        self.shortest_distance = 100
        chosen_name = None
        for color_dict in (COLOURS, GREYSCALE):
            for name, color in color_dict.iteritems():
                desired_rgb = color[0]

                target = RGBColor(*desired_rgb)
                cdist = target.delta_e(RGBColor(*self.rgb), method="cmc")

                if self.nearest is None or cdist < self.shortest_distance:
                    self.nearest = name
                    self.nearest_rgb = desired_rgb

                    self.shortest_distance = cdist
                    self.distance = cdist

                # print 'Checking', name
                (hue_lo, hue_hi) = color[1]

                if hue_lo > hue_hi:
                    h = self.spin(self.hue)
                    hue_lo = self.spin(hue_lo)
                    hue_hi = self.spin(hue_hi)
                else:
                    h = self.hue
                sat_range = color[2] or DEFAULT_SAT
                val_range = color[3] or DEFAUL_VAL

                if h in range(hue_lo, hue_hi + 1) and \
                    self.sat in range(sat_range[0], sat_range[1] + 1) and \
                        self.val in range(val_range[0], val_range[1] + 1):
                    # TODO set up desirable hues, sat and b per named colour
                    target = RGBColor(*desired_rgb)
                    self.distance = cdist
                    chosen_name = name
                    self.nearest_hex = webcolors.rgb_to_hex(self.nearest_rgb)
                    return chosen_name

        return None

    def ansi_number(self, r, g, b):
        '''
        Convert an RGB colour to 256 colour ANSI graphics.
        '''
        grey = False
        poss = True
        step = 2.5

        while poss:  # As long as the colour could be grey scale
            if r < step or g < step or b < step:
                grey = r < step and g < step and b < step
                poss = False

            step += 42.5

        if grey:
            colour = 232 + int(float(sum([r, g, b]) / 33.0))
        else:
            colour = sum([16] + [int((6 * float(val) / 256)) * mod
                         for val, mod in ((r, 36), (g, 6), (b, 1))])
        return colour

    def hex_me_up(self):

        self.hex_value = webcolors.rgb_to_hex(self.rgb)
        snapped, colour_name = swatchbook.closest('css3', self.hex_value)
        snapped_rgb = webcolors.hex_to_rgb(snapped)
        hsv = self.rgb_to_hsv(*snapped_rgb)
        target = RGBColor(*snapped_rgb)
        original = RGBColor(*self.rgb)
        cdist = target.delta_e(original, method="cmc")
        prom = Decimal(self.prominence).quantize(TWOPLACES)
        dist = Decimal(cdist).quantize(TWOPLACES)
        ELITE = False

        self.css = {
            'r': self.rgb[0],
            'g': self.rgb[1],
            'b': self.rgb[2],
            'hue': hsv[0],
            'hex': snapped,
            'name': colour_name,
            'distance': float(dist),
            'prominence': float(prom),
            'elite': ELITE,
        }

        return self.css
