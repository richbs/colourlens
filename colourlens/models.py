from django.db import models
from django.db.models.signals import pre_save
from decimal import Decimal
import math
import urllib
import io
from roygbiv import Roygbiv
from colourlens.utils import ArtColour

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

    accession_number = models.CharField(null=False, unique=True, max_length=10)
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
        aw.save()
        return aw
                   
    @classmethod
    def from_file(cls, filename):
        
        roy_im = Roygbiv(filename)
        p = roy_im.get_palette()
        rgbs = []
        preselected = []
        for palette_colour in p.colors:
            c = ArtColour(*palette_colour.value)
        
        aw = Artwork()
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
