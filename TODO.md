Modernisation: next steps
=========================

Remaining work from the Python 2.7 / Django 1.7 to Python 3 / Django 4.2 port
on the `modernise1` branch. Run `python manage.py test colourlens` after each
step.

1. Settings
-----------
In `coloursite/settings.py`:

- `SECRET_KEY` is hardcoded and committed. Read it from an environment
  variable and rotate the old key.
- `DEBUG = True` is hardcoded. Read it from the environment.
- `ALLOWED_HOSTS = []` only works with `DEBUG` on. Set the real host(s).
- `STATIC_ROOT = os.path.join(BASE_DIR + '/static')` passes a single string to
  `join`. Use `os.path.join(BASE_DIR, 'static')`.

2. Small cleanups
-----------------
- `colourlens/models.py` uses `from roygbiv import *`. Only `Roygbiv` is
  needed, so import that explicitly.
- The `red`, `green` and `blue` columns on `Colour` and `ColourDistance` are
  never filled in. Either populate them on import or drop them.

3. Python and Django versions
-----------------------------
- Python 3.9 reached end of life in October 2025. Move the venv to 3.12 and
  add a `.python-version` file.
- Django 4.2 LTS support ended in April 2026, and `requirements.txt` still
  says `Django<5`. Move to Django 5.2 LTS.
- After upgrading, check that RoyGBiv and cooperhewitt-swatchbook still work.
  `test_from_file` and the `hex_me_up` tests cover both.

Things to know
--------------
- RoyGBiv and cooperhewitt-swatchbook are installed straight from their GitHub
  repositories, not from fixed releases, so they can change without any change
  here. `colormath<2` and `webcolors<25` are pinned in `requirements.txt` for
  that reason. colormath 2 renamed `RGBColor` to `sRGBColor`, which would
  break `colourlens/utils.py`.
- The index view is cached for an hour whenever `DEBUG` is off, in
  production and in tests alike (the test runner turns `DEBUG` off). The view
  tests clear the cache in `setUp`.
- The pip in the current `.venv` is too old for `pip install --dry-run`.
  Upgrade pip when rebuilding the venv.
