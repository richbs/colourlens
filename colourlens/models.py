from django.db import models
from django.db.models.signals import pre_save
from decimal import Decimal
import math
import urllib
import urlparse
import io
from roygbiv import Roygbiv
from colourlens.utils import ArtColour

TWOPLACES = Decimal(10) ** -2

class Colour(models.Model):
    """
    A named-colour from a select palette with defined RGB colours
    """
    name = models.CharField(blank=False, max_length=20, db_index=True)
    hex_value = models.CharField(blank=True, max_length=10, db_index=True)
    red = models.IntegerField(blank=False, null=True)
    green = models.IntegerField(blank=False, null=True)
    blue = models.IntegerField(blank=False, null=True)
    elite = models.BooleanField(default=False)

    def __unicode__(self):
        return u"%s" % (self.name)


class Artwork(models.Model):
    """
    An image of an artwork number with an accession (reference) number
    """

    accession_number = models.CharField(unique=True, max_length=100)
    title = models.CharField(blank=True, max_length=100)
    artist = models.CharField(blank=True, max_length=100)
    year = models.IntegerField(blank=True, null=True)
    url = models.URLField(blank=True)
    image_url = models.URLField(blank=True)
    institution = models.CharField(blank=True, max_length=10, db_index=True)
    colours = models.ManyToManyField(Colour, through="ColourDistance")

    @classmethod
    def from_url(cls, image_url):
        response = urllib.urlopen(image_url)
        im_bytes = response.read()
        aw = Artwork.from_file(io.BytesIO(im_bytes))
        aw.image_url = image_url
        aw.accession_number = image_url
        aw.save()
        return aw
                   
    @classmethod
    def from_file(cls, filename):
        aw = Artwork()
        aw.accession_number = filename
        aw.title = filename
        aw.image_url = "file://%s" % filename
        
        roy_im = Roygbiv(filename)
        p = roy_im.get_palette()
        rgbs = []
        preselected = []
        for palette_colour in p.colors:
            c = ArtColour(*palette_colour.value)
            if c.color:
                cc, cr = Colour.objects.get_or_create(name=c.color)
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
        aw.save()
        
        return aw
        
    def __unicode__(self):
        return u"%s" % (self.accession_number)


class ColourDistance(models.Model):
    """
    Join Model with distance field added to show proximity to colour
    """
    artwork = models.ForeignKey(Artwork)
    colour = models.ForeignKey(Colour)
    red = models.IntegerField(blank=False, null=True)
    green = models.IntegerField(blank=False, null=True)
    blue = models.IntegerField(blank=False, null=True)
    distance = models.DecimalField(max_digits=5, decimal_places=2,
                                   null=True, db_index=True)
    prominence = models.DecimalField(max_digits=3, decimal_places=2,
                                     null=True, db_index=True)
    presence = models.DecimalField(max_digits=5, decimal_places=2, null=True,
                                   db_index=True)

    class Meta:
        unique_together = ('artwork', 'colour')

    def __unicode__(self):
        return u"s%s %s d:%s p:%s" % (self.artwork, self.colour,
                                      self.distance, self.prominence)


def calculate_colour_presence(sender, instance, **kwargs):
    """
    Calculates colour "presence" in image. This is distance as
    a factor of colour area
    """
    if instance.distance and instance.prominence:
        dist = Decimal(instance.distance)
        prom = Decimal(instance.prominence)
        distsqrt = math.sqrt(dist)
        instance.presence = prom * 100 / Decimal(distsqrt)

pre_save.connect(calculate_colour_presence, sender=ColourDistance)
