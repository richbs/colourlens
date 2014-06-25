import colorsys
import math
import webcolors
from cooperhewitt import swatchbook
from colormath.color_objects import RGBColor
from decimal import Decimal
from roygbiv import Roygbiv

COLOURS = {
    'RED': ((255, 0, 0), (340, 17), (10, 100), (66, 100)),
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
    ansi = ()
    ansi_rgb = ()
    ansi_hsv = ()
    _color = None
    GREY = False
    distance = None

    def __init__(self, r, g, b):

        self.rgb = (r, g, b)
        (self.red, self.blue, self.green) = (r, g, b)
        self.hsv = self.rgb_to_hsv(r, g, b)
        (self.hue, self.sat, self.val) = (self.hsv[0], self.hsv[1], self.hsv[2])
        self.ansi = self.ansi_number(r, g, b)
        self.ansi_rgb = self.rgb_reduce(r, g, b)
        self.ansi_hsv = self.rgb_to_hsv(*self.ansi_rgb)

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

        reduced_rgb = [int(6 * float(val) / 256) * (256/6) for val in (r, g, b)]
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
        
def roygbiv(image, acno, url=None):
    roy_im = Roygbiv(image)
    p = roy_im.get_palette()
    print acno
    for palette_colour in p.colors:
        c = ArtColour(*palette_colour.value)
        if c.color:
            cc, cr = Colour.objects.get_or_create(name=c.color)
            aw, cr = Artwork.objects.get_or_create(accession_number=acno)
            aw.image = url
            aw.save()

            dist = Decimal(c.distance).quantize(TWOPLACES)
            prom = Decimal(palette_colour.prominence).quantize(TWOPLACES)

            cd, cr = ColourDistance.objects.get_or_create(colour=cc,
                                                          artwork=aw)
            if cr:
                cd.distance = dist
                cd.prominence = prom
            else:
                if cd.prominence:
                    total_area = cd.prominence + prom
                    d1 = cd.distance * (cd.prominence / total_area)
                    d2 = dist * (prom / total_area)
                    cd.distance = d1 + d2
                    cd.prominence = total_area
            cd.save()

        print '\x1b[48;5;%dm     \x1b[0m %s %.2f NEAREST %s %.2f' % (
            c.ansi, c.color, c.distance, c.nearest, c.shortest_distance)

def closest(r, g, b):

        # http://stackoverflow.com/questions/9694165/convert-rgb-color-to-english-color-name-like-green

        min_colours = {}

        for key, details in self.colours().items():

            r_c, g_c, b_c = webcolors.hex_to_rgb(key)
            rd = (r_c - r) ** 2
            gd = (g_c - g) ** 2
            bd = (b_c - b) ** 2
            min_colours[(rd + gd + bd)] = details

        idx = min(min_colours.keys())

        details = min_colours[idx]
        name = details['name']

        hex = self.hex(name)
        return hex, name

def get_colours(image):

    roy_im = Roygbiv(image)
    p = roy_im.get_palette()
    rgbs = []
    preselected = []
    for palette_colour in p.colors:
        c = ArtColour(*palette_colour.value)
        h = webcolors.rgb_to_hex(c.rgb)
        snapped, colour_name = swatchbook.closest('css3', h)
        snapped_rgb = webcolors.hex_to_rgb(snapped)
        target = RGBColor(*snapped_rgb)
        original = RGBColor(*c.rgb)
        cdist = target.delta_e(original, method="cmc")
        prom = Decimal(palette_colour.prominence).quantize(TWOPLACES)
        dist = Decimal(cdist).quantize(TWOPLACES)
        distsqrt = math.sqrt(dist)
        presence = prom * 100 / Decimal(distsqrt).quantize(TWOPLACES)
        ELITE = False
        if c.color:
            if colour_name.lower() == c.color.lower():
                ELITE = True
                    
        rgbs.append({
            'r': c.rgb[0],
            'g': c.rgb[1],
            'b': c.rgb[2],
            'name': colour_name,
            'distance': float(dist),
            'prominence': float(prom),
            'presence': float(presence),
            'elite': ELITE,
        })
         
        if not ELITE and c.color:
            distsqrt = math.sqrt(c.distance)
            presence = prom * 100 / Decimal(distsqrt).quantize(TWOPLACES)             
            rgbs.append({
                'r': c.rgb[0],
                'g': c.rgb[1],
                'b': c.rgb[2],
                'name': c.color.lower(),
                'distance': float(c.distance),
                'prominence': float(prom),
                'presence': float(presence),
                'elite': True,
            })



        print snapped, cdist, c.color, c.distance
    return rgbs