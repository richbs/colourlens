import pymongo
import urllib
from colourlens.models import Artwork, Colour, ColourDistance
from colourlens.utils import ArtColour, get_colours
from django.core.management.base import BaseCommand
from StringIO import StringIO


class Command(BaseCommand):
    
    def handle(self, *args, **options):

        client = pymongo.MongoClient();

        artworks = client.tate.artworks
        
        for a in artworks.find():
            if 'thumbnailUrl' in a and a['thumbnailUrl']:
                image_url = a['thumbnailUrl'].replace('_8', '_7')
                print image_url
                response = urllib.urlopen(image_url)
                im_bytes = response.read()
                
                if len(im_bytes) == 0 or response.getcode() != 200:
                    continue
                colours = get_colours(StringIO(im_bytes))
                a['rgbs'] = colours[0]
                artworks.save(a)

        #works = Artwork.objects.all()

        # for a in works:
        #
        #     print a.colours.all()[0]