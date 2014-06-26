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
    hex_value = models.CharField(blank=True, max_length=10, unique=True)
    red = models.IntegerField(blank=False, null=True)
    green = models.IntegerField(blank=False, null=True)
    blue = models.IntegerField(blank=False, null=True)
    hue = models.IntegerField(blank=True, null=True, db_index=True)
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
    def from_url(cls, accession_number, institution, image_url):
        response = urllib.urlopen(image_url)
        im_bytes = response.read()
        aw = Artwork.from_file(
            accession_number,
            institution,
            io.BytesIO(im_bytes)
        )
        if not aw:
            return None
        aw.image_url = image_url
        aw.save()
        return aw
                   
    @classmethod
    def from_file(cls, accession_number, institution, filename):
        aw, cr = Artwork.objects.get_or_create(
            institution=institution,
            accession_number=accession_number
        )
        aw.colourdistance_set.all().delete()
        aw.title = institution + accession_number
        aw.image_url = "file://%s" % filename
        try:
            roy_im = Roygbiv(filename)
        except IOError, e:
            return None
        p = roy_im.get_palette()
        rgbs = []
        preselected = []
        for palette_colour in p.colors:
            c = ArtColour(*palette_colour.value, prominence=palette_colour.prominence)
            c.hex_me_up()
            css, cr = Colour.objects.get_or_create(hex_value=c.css['hex'])
            css.name = c.css['name']
            css.hue = c.css['hue']
            dist = Decimal(c.css['distance']).quantize(TWOPLACES)
            prom = Decimal(c.css['prominence']).quantize(TWOPLACES)

            cd, cr = ColourDistance.objects.get_or_create(colour=css,
                                                          artwork=aw)
            cd.distance = dist
            cd.prominence = prom
            cd.save()
            css.save()   
            if c.color:
                cc, cr = Colour.objects.get_or_create(hex_value=c.nearest_hex)
                cc.name = c.color
                cc.elite = True
                dist = Decimal(c.distance).quantize(TWOPLACES)
                prom = Decimal(c.prominence).quantize(TWOPLACES)

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
                cc.save()  
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
