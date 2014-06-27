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
        make_option("-f", "--filename",
                    dest="filedata",
                    type="string",
                    action="store",
                    help="Image data file"
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
                    default="TATE",
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
        institution = options['institution']
        start = time.time()
        if institution == "HARVARD":
            
            offset = 0
            
            params = {
                'apikey': '11915c50-f65c-11e3-9cde-d1a4455847d9',
                'q': 'ukiyo',
                'size': 100,
            }
            api_url = "http://api.harvardartmuseums.org/object"

            while offset < 3100:                
                params['from'] = offset
                req_url = "%s?%s" % (api_url, urllib.urlencode(params))
                print req_url
                req = urllib.urlopen(req_url)
                response = json.load(req)
                for rec in response['records']:
                    if 'primaryimageurl' not in rec:
                        continue
                    if not rec['primaryimageurl']:
                        continue
                    image_url = rec['primaryimageurl'].split('?')[0] + "?width=255&height=255"
                    print image_url
                    object_number = rec['objectnumber']
                    aw = Artwork.from_url(
                        object_number,
                        institution,
                        image_url
                    )
                    if 'title' in rec:
                        aw.title = rec['title']
                    aw.url = rec['url']
                    if 'people' in rec:
                        aw.artist = rec['people'][0]['name']
                    if rec['datebegin']:
                        aw.year = rec['datebegin']
                    aw.save()
                offset += 100
        
        exit()    
            
            
        if options['filedata']:
            if institution == "TATE":
                csv_file = csv.DictReader(open(options['filedata']))
                for count, row in enumerate(csv_file):
                    im = row['thumbnailUrl']
                    if not row['accession_number'].startswith("N"):
                        continue
                    
                    if row['thumbnailUrl']:
                        image_url = row['thumbnailUrl']
                        print image_url                    
                        aw = Artwork.from_url(
                            row['accession_number'],
                            institution,
                            image_url.replace('_8', '_7')
                        )
                        aw.title = row['title']
                        aw.artist = row['artist']
                        aw.url = row['url']
                        aw.image_url = image_url
                        if row['year']:
                            aw.year = row['year']
                        aw.save()
            elif institution == "MAM":
                f = open(options['filedata'])
                for count, l in enumerate(f.readlines()):
                    fields = l.split('^')
                    if len(fields) == 30 and count > 0:
                        title = fields[6]
                        year = fields[3]
                        acno =  fields[0]
                        url = "http://collection.mam.org/details.php?id=%s" % (acno)
                        jpg = fields[25]
                        image_url = "http://collection.mam.org/vmedia/thumbnails/%s" % (jpg)
                        print acno, image_url
                        aw = Artwork.from_url(
                            acno,
                            institution,
                            image_url
                        )
                        if not aw:
                            continue
                        aw.year = year
                        aw.title = title 
                        aw.artist = "%s, %s" % (fields[27], fields[26])
                        aw.url = url
                        aw.save()
            elif institution == "WOLF":
                 f = open(options['filedata'])
                 for count, l in enumerate(f.readlines()):
                     fields = l.split('\t')
                     if len(fields) == 3:
                         title = fields[0]
                         acno =  fields[1]
                         url = "http://%s" % (fields[2].rstrip())
                         image_url = "http://%s" % (fields[1])
                         print image_url
                         aw = Artwork.from_url(
                             acno,
                             institution,
                             image_url
                         )
                         if not aw:
                             continue
                         aw.title = title 
                         aw.url = url
                         aw.save()
        else:
            for (dirpath, dirnames, filenames) in os.walk(input_dir):
                for im in filenames:
                    full_im = os.path.join(dirpath, im)
                    acno = full_im.split('/')[-1].split('.')[0]
                    if full_im.endswith('.jpg'):
                        aw = Artwork.from_file(acno, institution, full_im)
                    elif full_im.endswith('.json'):
                        f = open(full_im)
                        json_data = f.read()
                        pdata = json.loads(json_data)
                        if institution == "VA":
                            im_id = pdata[0]['fields']['primary_image_id']
                            if not im_id:
                                continue
                            image_url = "http://media.vam.ac.uk/media/thira/collection_images/%s/%s_jpg_w.jpg" % (
                                im_id[0:6], im_id
                            )                  
                            acno = pdata[0]['fields']['object_number']
                            title = pdata[0]['fields']['title'] or \
                                        pdata[0]['fields']['object']
                            year = pdata[0]['fields']['year_start']
                            aw = Artwork.from_url(
                                acno,
                                institution,
                                image_url.replace('_w.', '_s.')
                            )     
                            aw.title = title
                            aw.image_url = image_url     
                            aw.year = year
                            print title, acno, year
                            aw.url = 'http://collections.vam.ac.uk/item/%s' % (
                                acno
                            )
                            aw.save()
                                
                            
def url_to_imagefile(url):
    
    response = urllib.urlopen(url)
    im_bytes = response.read()
    return io.BytesIO(im_bytes)
    