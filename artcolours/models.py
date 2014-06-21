from django.db import models
from django.db.models.signals import pre_save
from decimal import Decimal
import math


class Colour(models.Model):
    """
    A named-colour from a select palette with defined RGB colours
    """
    name = models.CharField(blank=False, max_length=20, db_index=True)
    red = models.IntegerField(blank=False, null=True)
    green = models.IntegerField(blank=False, null=True)
    blue = models.IntegerField(blank=False, null=True)

    def __unicode__(self):
        return u"%s" % (self.name)


class Artwork(models.Model):
    """
    An image of an artwork number with an accession (reference) number
    """

    accession_number = models.CharField(null=False, unique=True, max_length=10)
    colours = models.ManyToManyField(Colour, through="ColourDistance")
    image = models.CharField(null=True, blank=True, max_length=255)

    def __unicode__(self):
        return u"%s" % (self.accession_number)


class ColourDistance(models.Model):
    """
    Join Model with distance field added to show proximity to colour
    """
    artwork = models.ForeignKey(Artwork)
    colour = models.ForeignKey(Colour)
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
