colourlens
==========

Working up a generic colour processing Django site

Pre-requisites: Assuming use of virtualenv. Also need libjpeg-dev and python-dev for image work, e.g:

1. `sudo apt-get install libjpeg-dev python-dev`
2. `git clone git@github.com:richbs/colourlens.git`
3. `cd colourlens`
4. `virtualenv --distribute venv`
5. `source venv/bin/activate`
6. `pip install -r requirements.txt`
7. `python manage.py syncdb --noinput`
8. `python manage.py imagecolour -i HARVARD`
9. `python manage.py runserver`
10. Hit `http://127.0.0.1:8000/` in your browser.

