import csv
import json
import os
import re
import time
import urllib
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.conf import settings
from colourlens.models import Artwork, Colour, ColourDistance
from colourlens.utils import ArtColour, roygbiv, get_colours
from optparse import make_option
from StringIO import StringIO
import io

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
                    help="Directory brimful of images or json"
                    ),
        make_option("-i", "--institution",
                    dest="institution",
                    type="string",
                    action="store",
                    default=None,
                    help="Institution"
                    ),
    )

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
                im = row['thumbnailUrl']
                #if row['medium'].find('paint') > -1 and row['thumbnailUrl']:
                if row['thumbnailUrl']:
                    image_url = row['thumbnailUrl']                    
                    aw = Artwork.from_url(image_url)

        else:
            promo_ims = os.path.join(settings.BASE_DIR,
                                     '../artartists/static/images/promos')

            im_dir = input_dir or promo_ims
            for (dirpath, dirnames, filenames) in os.walk(im_dir):
                for im in filenames:
                    full_im = os.path.join(dirpath, im)

                    if full_im.endswith('.jpg'):
                        aw = Artwork.from_file(full_im)
                        print aw
                    elif full_im.endswith('.json'):
                        f = open(full_im)
                        json_data = f.read()
                        pdata = json.loads(json_data)
                        

def url_to_imagefile(url):
    
    response = urllib.urlopen(url)
    im_bytes = response.read()
    return io.BytesIO(im_bytes)
    