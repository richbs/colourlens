Colour Lens
===========
See it in action at [colourlens.org](http://colourlens.org/).

Working up a generic colour visualising Django site.

Requirements
------------
- Python 3.9 or later
- Django 4.2 (installed from `requirements.txt`)
- git, because RoyGBiv and cooperhewitt-swatchbook are installed straight
  from GitHub

Pillow normally installs from a prebuilt wheel. If pip has to build it from
source, install the JPEG and Python headers first, e.g.
`sudo apt-get install libjpeg-dev python3-dev`.

Setup
-----
1. `git clone git@github.com:richbs/colourlens.git`
2. `cd colourlens`
3. `python3 -m venv .venv`
4. `source .venv/bin/activate`
5. `pip install -r requirements.txt`
6. `python manage.py migrate`
7. Import some artworks (see below), e.g.
   `python manage.py imagecolour -i HARVARD -a api_key`
8. `python manage.py runserver`
9. Hit `http://127.0.0.1:8000/` in your browser.

The database is SQLite, at `coloursite/colourlens.sqlite`.

Importing artworks
------------------
`python manage.py imagecolour` fetches images, extracts their colour palettes
and stores them. Options:

- `-i`, `--institution`: which importer to use (default `TATE`)
- `-a`, `--apikey`: API key for institutions that need one
- `-f`, `--filename`: data file to read
- `-d`, `--dir`: directory of images or JSON records

Each institution reads from a different source:

| Institution | Source |
|---|---|
| `HARVARD`, `RIJKS`, `WALTERS` | Their public API: pass `-a` |
| `APPSTORE` | iTunes top-app RSS feeds: no options needed |
| `TATE` | CSV file: pass `-f` |
| `MAM` | `^`-separated text file: pass `-f` |
| `WOLF` | Tab-separated text file: pass `-f` |
| `VA`, `LEEDS` | Directory of JSON records: pass `-d` |
| Any other name | Directory of `.jpg` / `.png` files: pass `-d` (file names become accession numbers) |

For example:

    python manage.py imagecolour -i TATE -f artwork_data.csv
    python manage.py imagecolour -i LEEDS -d path/to/records/
    python manage.py imagecolour -i MINE -d path/to/images/

Tests
-----
    python manage.py test colourlens

The index page is cached for an hour whenever `DEBUG` is off. The test runner
turns `DEBUG` off, so the view tests clear the cache before each test.

Remaining modernisation work is listed in [TODO.md](TODO.md).
