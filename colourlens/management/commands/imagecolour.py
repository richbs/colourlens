from bs4 import BeautifulSoup
import csv
import feedparser
import json
import os
import re
import urllib
from django.core.management.base import BaseCommand
from colourlens.models import Artwork
from optparse import make_option
import io
import time


def itunes_rss_color(rss_url):

    print rss_url
    d = feedparser.parse(rss_url)
    for e in d.entries:
        html_doc = e['content'][0]['value']
        cat = e.category
        identifier = e.id.split('/')[-1].split('&')[0]
        soup = BeautifulSoup(html_doc)
        im = soup.findAll('img')[0]
        name = e['im_name']
        aw = Artwork.from_url(
            identifier,
            cat,
            im['src'].replace('100x100', '150x150')
        )
        if not aw:
            continue
        aw.title = name
        aw.save()


class Command(BaseCommand):
    help = "Image colour palettes from open data CSV or directory of files"

    option_list = BaseCommand.option_list + (
        make_option("-f", "--filename",
                    dest="filedata",
                    type="string",
                    action="store",
                    help="Image data file/list",
                    default=None,
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
        make_option("-a", "--apikey",
                    dest="apikey",
                    type="string",
                    action="store",
                    default="",
                    help="The API Key from this institution"
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
        api_key = options['apikey']
        if institution == "HARVARD":

            offset = 0

            params = {
                'apikey': api_key,
                'q': 'poster',
                'size': 100,
            }
            api_url = "http://api.harvardartmuseums.org/object"

            while offset < 400:
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
                    image_url = rec['primaryimageurl'].split('?')[0] + \
                        "?width=255&height=255"
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
        elif institution == "RIJKS":
            page = 0
            params = {
                'key': api_key,
                'format': 'json',
                'f': 2,
                'p': 1,
                'ps': 100,
                'type': 'painting',
                #'place': 'Japan',
                #'f.dating.period': 17,
                'imgonly': True,
                'ii': 0,
            }
            api_url = "https://www.rijksmuseum.nl/api/en/collection"
            while page < 200:
                page += 1
                params['p'] = page
                req_url = "%s?%s" % (api_url, urllib.urlencode(params))
                print req_url
                req = urllib.urlopen(req_url)
                response = json.load(req)
                for rec in response['artObjects']:
                    object_id = rec['objectNumber']
                    if not rec['webImage']:
                        continue
                    image_url = rec['webImage']['url'].replace('=s0', '=s300')
                    print image_url
                    aw = Artwork.from_url(
                        object_id,
                        institution,
                        image_url
                    )
                    if not aw:
                        continue
                    if 'title' in rec:
                        aw.title = rec['title']
                    aw.url = rec['links']['web']
                    if 'principalOrFirstMaker' in rec:
                        aw.artist = rec['principalOrFirstMaker']
                    if rec['longTitle']:
                        aw.year = rec['longTitle'].split(' ')[-1]
                        try:
                            int(aw.year)
                        except:
                            aw.year = None
                    aw.save()
        elif institution == "APPSTORE":
            rss_base = 'https://itunes.apple.com/us/rss/%s/limit=100/genre=%d/xml'

            lists = [
                'topfreeapplications', 'toppaidapplications',
                'topgrossingapplications', 'topfreeipadapplications',
                'toppaidipadapplications', 'topgrossingipadapplications',
                'newapplications', 'newfreeapplications',
                'newpaidapplications'
            ]

            categories = range(6000, 6025)

            for c in categories:
                for l in lists:

                    rss_url = rss_base % (l, c)
                    try:
                        itunes_rss_color(rss_url)
                    except Exception, e:
                        print e
                        continue



            exit()
        elif institution == "WALTERS":
            page = 0
            params = {
                'apikey': api_key,
                #'CollectionID': 3,
                'pageSize': 100,
                'Classification': 'Painting & Drawing',
                #'Creator': 'Indian',
                'Page': page,
            }
            api_url = "http://api.thewalters.org/v1/objects.json"
            while page < 200:
                page += 1
                params['Page'] = page
                req_url = "%s?%s" % (api_url, urllib.urlencode(params))
                print req_url
                req = urllib.urlopen(req_url)
                response = json.load(req)
                for rec in response['Items']:
                    object_id = rec['ObjectNumber']
                    image_url = rec['PrimaryImage']['Large']
                    if not image_url:
                        continue
                    aw = Artwork.from_url(
                        object_id,
                        institution,
                        image_url
                    )
                    if not aw:
                        continue
                    if 'Title' in rec:
                        aw.title = rec['Title']
                    aw.url = rec['ResourceURL']
                    if 'Creator' in rec:
                        aw.artist = rec['Creator']
                    if rec['DateBeginYear']:
                        aw.year = rec['DateBeginYear']
                    print aw.image_url
                    aw.save()

        if options['filedata']:
            if institution == "TATE":
                csv_file = csv.DictReader(open(options['filedata']))
                for count, row in enumerate(csv_file):
                    im = row['thumbnailUrl']
                    if not row['accession_number'].startswith("P"):
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
            elif institution == "MNHS":
                csv_file = csv.DictReader(open(options['filedata']))
                for count, row in enumerate(csv_file):

                    if count < 4538:
                        continue
                    else:
                        aw = Artwork.from_url(
                            row['MNHS Catalog ID'],
                            institution,
                            row['Thumbnail Image URL']
                        )
                        if aw:
                            aw.title = row['Title']
                            aw.artist = row['Creators All']
                            aw.url = row['Catalog Record URL']
                            print 2222, row['Date']
                            try:
                                year = row['Date'][-4:]
                                year = int(year)
                            except:
                                year = row['Date'][0:4]
                                print 'buckock', year
                            aw.year = year
                            try:
                                aw.save()
                            except Exception, e:
                                print "ERROR", row
                                continue
                            print count, aw.accession_number
                        else:
                            print aw

                    time.sleep(0.1)
                exit()
            elif institution == "MAM":
                f = open(options['filedata'])
                for count, l in enumerate(f.readlines()):
                    fields = l.split('^')
                    if len(fields) == 30 and count > 0:
                        title = fields[6]
                        year = fields[3]
                        acno = fields[0]
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
                        acno = fields[1]
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
                    if full_im.endswith('.jpg') or full_im.endswith('.png'):
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
