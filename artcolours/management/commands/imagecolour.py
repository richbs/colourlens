import csv
import os
import re
import time
import urllib
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.conf import settings
from artcolours.models import Artwork, Colour, ColourDistance
from roygbiv import Roygbiv
import colorsys
from colormath.color_objects import RGBColor
from optparse import make_option
from StringIO import StringIO


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


class Command(BaseCommand):
    help = "Image colour palettes from open data CSV or directory of files"

    option_list = BaseCommand.option_list + (
        make_option("-c", "--csv",
                    dest="csv_file",
                    type="string",
                    action="store",
                    help="Image data csv"
                    ),
        make_option("-d", "--dir",
                    dest="input_dir",
                    type="string",
                    action="store",
                    default=None,
                    help="Directory brimful of images"
                    ),
    )

    def roygbiv(self, image, acno, url=None):
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

                TWOPLACES = Decimal(10) ** -2
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

    def get_acno(self, filename):
        urlre = re.compile(r'^.*?([A-z0-9]+?)(?:_[0-9]+)?.jpg$')
        match = urlre.match(filename)
        if match:
            return match.group(1)
        else:
            return "Foo"

    def handle(self, *args, **options):
        print 'Images'
        input_dir = options['input_dir']

        start = time.time()
        if options['csv_file']:
            csv_file = csv.DictReader(open(options['csv_file']))
            for count, row in enumerate(csv_file):
                im = row['thumbnail_url']
                #if row['medium'].find('paint') > -1 and row['thumbnail_url']:
                if row['thumbnail_url']:
                    image_url = row['thumbnail_url']
                    response = urllib.urlopen(image_url)
                    im_bytes = response.read()
                    if len(im_bytes) == 0:
                        continue
                    ips = (time.time() - start) / (count+1)
                    print "%.2f images per second" % (ips)
                    self.roygbiv(StringIO(im_bytes), self.get_acno(image_url),
                                 row['thumbnail_url'])
        else:
            promo_ims = os.path.join(settings.BASE_DIR,
                                     '../artartists/static/images/promos')

            im_dir = input_dir or promo_ims

            for count, im in enumerate(os.listdir(im_dir)):
                full_im = os.path.join(im_dir, im)
                if not full_im.endswith('.jpg'):
                    print full_im
                    continue
                ips = (time.time() - start) / (count+1)
                print "%.2f images per second" % (ips)
                self.roygbiv(full_im, self.get_acno(full_im))
