import json
import os
import shutil
import tempfile
from decimal import Decimal

from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from colourlens.models import Artwork, Colour, ColourDistance
from colourlens.utils import ArtColour

LOCMEM_CACHE = {
    'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}
}


class ArtColourTests(TestCase):

    def test_hsv_round_trip(self):
        c = ArtColour(10, 20, 30, 0.5)
        # HSV is rounded to whole degrees/percent, so allow small drift
        for rgb in [(255, 0, 0), (0, 128, 128), (200, 150, 50)]:
            for got, want in zip(c.hsv_to_rgb(*c.rgb_to_hsv(*rgb)), rgb):
                self.assertLessEqual(abs(got - want), 2)

    def test_rgb_to_hsv(self):
        c = ArtColour(255, 0, 0, 1)
        self.assertEqual(c.hsv, (0, 100, 100))
        self.assertEqual((c.hue, c.sat, c.val), (0, 100, 100))

    def test_rgb_reduce_snaps_to_six_level_cube(self):
        c = ArtColour(0, 0, 0, 1)
        self.assertEqual(c.rgb_reduce(0, 128, 255), (0, 126, 210))
        for val in c.rgb_reduce(17, 99, 201):
            self.assertIsInstance(val, int)
            self.assertEqual(val % 42, 0)

    def test_ansi_number(self):
        c = ArtColour(0, 0, 0, 1)
        self.assertEqual(c.ansi_number(0, 0, 0), 232)
        # white lands at the top of the greyscale ramp, not the cube
        self.assertEqual(c.ansi_number(255, 255, 255), 255)
        self.assertEqual(c.ansi_number(255, 0, 0), 196)

    def test_hex_me_up_exact_css_colour(self):
        css = ArtColour(255, 0, 0, 0.42).hex_me_up()
        self.assertEqual(css['hex'], '#ff0000')
        self.assertEqual(css['name'], 'red')
        self.assertEqual(css['hue'], 0)
        self.assertAlmostEqual(css['distance'], 0.0)
        self.assertAlmostEqual(css['prominence'], 0.42)

    def test_hex_me_up_snaps_to_nearest(self):
        css = ArtColour(250, 5, 5, 1).hex_me_up()
        self.assertEqual(css['hex'], '#ff0000')
        self.assertGreater(css['distance'], 0)

    def test_named_colour(self):
        self.assertEqual(ArtColour(0, 0, 255, 1).color, 'BLUE')
        self.assertEqual(ArtColour(0, 0, 0, 1).color, 'BLACK')

    def test_channel_attributes(self):
        c = ArtColour(1, 2, 3, 1)
        self.assertEqual((c.red, c.green, c.blue), (1, 2, 3))


class ModelSignalTests(TestCase):

    def setUp(self):
        self.red = Colour.objects.create(name='red', hex_value='#ff0000')
        self.blue = Colour.objects.create(name='blue', hex_value='#0000ff')
        self.artwork = Artwork.objects.create(
            accession_number='A1', institution='TEST'
        )

    def test_presence_calculated(self):
        cd = ColourDistance.objects.create(
            artwork=self.artwork, colour=self.red,
            distance=Decimal('4.00'), prominence=Decimal('0.50')
        )
        cd.save()
        # 0.5 * 100 / 4 / sqrt(4)
        self.assertEqual(cd.presence, Decimal('6.25'))

    def test_prominence_clamped(self):
        cd = ColourDistance.objects.create(
            artwork=self.artwork, colour=self.red,
            distance=Decimal('1.00'), prominence=Decimal('0.00')
        )
        cd.save()
        cd.refresh_from_db()
        self.assertEqual(cd.prominence, Decimal('0.01'))

    def test_proportions(self):
        ColourDistance.objects.create(
            artwork=self.artwork, colour=self.red,
            distance=Decimal('1.00'), prominence=Decimal('0.75')
        )
        ColourDistance.objects.create(
            artwork=self.artwork, colour=self.blue,
            distance=Decimal('1.00'), prominence=Decimal('0.25')
        )
        self.artwork.save()
        parts = dict(self.artwork.colour_parts())
        self.assertAlmostEqual(parts['#ff0000'], 75.0)
        self.assertAlmostEqual(parts['#0000ff'], 25.0)
        self.assertAlmostEqual(sum(parts.values()), 100.0)

    def test_new_artwork_has_empty_proportions(self):
        aw = Artwork.objects.create(accession_number='A2')
        self.assertEqual(json.loads(aw.proportions), [])
        self.assertEqual(aw.colour_parts(), [])

    def test_from_file(self):
        tmpdir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmpdir)
        filename = os.path.join(tmpdir, 'test.png')
        im = Image.new('RGB', (40, 40), (255, 0, 0))
        im.paste((0, 0, 255), (0, 0, 40, 10))
        im.save(filename)

        aw = Artwork.from_file('F1', 'TEST', filename)

        self.assertIsNotNone(aw)
        self.assertEqual(aw.title, 'TESTF1')
        hexes = set(aw.colours.values_list('hex_value', flat=True))
        self.assertIn('#ff0000', hexes)
        self.assertIn('#0000ff', hexes)
        self.assertTrue(aw.colour_parts())

    def test_str(self):
        cd = ColourDistance.objects.create(
            artwork=self.artwork, colour=self.red,
            distance=Decimal('4.00'), prominence=Decimal('0.50')
        )
        self.assertEqual(str(self.red), 'red')
        self.assertEqual(str(self.artwork), 'A1')
        self.assertEqual(str(cd), 'A1 red d:4.00 p:0.50')


@override_settings(CACHES=LOCMEM_CACHE)
class IndexViewTests(TestCase):

    def setUp(self):
        # tests run with DEBUG=False, so cache_page is active on index
        cache.clear()
        self.red = Colour.objects.create(name='red', hex_value='#ff0000', hue=0)
        self.blue = Colour.objects.create(name='blue', hex_value='#0000ff', hue=240)

    def make_artwork(self, number, institution='TEST', year=None,
                     colour=None, distance='5.00'):
        aw = Artwork.objects.create(
            accession_number=number, institution=institution, year=year
        )
        ColourDistance.objects.create(
            artwork=aw, colour=colour or self.red,
            distance=Decimal(distance), prominence=Decimal('0.50')
        )
        return aw

    def accessions(self, response):
        return {a.accession_number for a in response.context['artworks']}

    def test_empty_index(self):
        response = self.client.get(reverse('colour_index'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['found'], 0)

    def test_index(self):
        self.make_artwork('A1')
        response = self.client.get(reverse('colour_index'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'colour.html')
        self.assertIn('page_obj', response.context)
        self.assertEqual(self.accessions(response), {'A1'})

    def test_institution(self):
        self.make_artwork('A1', institution='LEEDS')
        self.make_artwork('A2', institution='OTHER')
        response = self.client.get(
            reverse('colour_institution', args=['LEEDS'])
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.accessions(response), {'A1'})

    def test_colour_filter(self):
        self.make_artwork('NEAR', distance='5.00')
        self.make_artwork('FAR', distance='30.00')
        self.make_artwork('BLUE', colour=self.blue)
        response = self.client.get(
            reverse('colour_index'), {'colour': '#ff0000'}
        )
        self.assertEqual(self.accessions(response), {'NEAR'})

    def test_year_filter(self):
        self.make_artwork('OLD', year=1800)
        self.make_artwork('MID', year=1900)
        self.make_artwork('NEW', year=2000)
        response = self.client.get(
            reverse('colour_index'), {'startyear': 1850, 'endyear': 1950}
        )
        self.assertEqual(self.accessions(response), {'MID'})

    def test_pagination(self):
        for i in range(30):
            self.make_artwork('A%02d' % i)
        response = self.client.get(
            reverse('colour_index'), {'page': 2, 'startyear': ''}
        )
        self.assertEqual(response.context['page_obj'].number, 2)
        self.assertEqual(len(response.context['artworks']), 6)
        self.assertNotIn('page', response.context['pagination_query'])
        self.assertIn('startyear', response.context['pagination_query'])
