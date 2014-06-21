from django.db.models import Avg, Sum
from django import forms
from django.forms.widgets import Input
from django.http import HttpResponse
from django.template import RequestContext, loader
from artcolours.models import Artwork


PROM_ATTRS = {'min': '0', 'max': '100', 'step': '5'}
DIST_ATTRS = {'min': '0', 'max': '50', 'step': '1'}


class RangeInput(Input):
    input_type = "range"


class ColourForm(forms.Form):

    def __init__(self, *args, **kwargs):
        """
        Add classes to denote type of input
        """
        super(ColourForm, self).__init__(*args, **kwargs)

        for k, v in self.fields.iteritems():
            if v.widget.__class__ == forms.CheckboxInput:
                v.widget.attrs['class'] = 'colourbox'
            elif v.widget.__class__ == RangeInput:
                v.widget.attrs['class'] = 'slider'

    black = forms.BooleanField(required=False)
    grey = forms.BooleanField(required=False)
    silver = forms.BooleanField(required=False)
    white = forms.BooleanField(required=False)
    red = forms.BooleanField(required=False)
    maroon = forms.BooleanField(required=False)
    brown = forms.BooleanField(required=False)
    orange = forms.BooleanField(required=False)
    yellow = forms.BooleanField(required=False)
    lime = forms.BooleanField(required=False)
    green = forms.BooleanField(required=False)
    olive = forms.BooleanField(required=False)
    cyan = forms.BooleanField(required=False)
    teal = forms.BooleanField(required=False)
    blue = forms.BooleanField(required=False)
    navy = forms.BooleanField(required=False)
    magenta = forms.BooleanField(required=False)
    purple = forms.BooleanField(required=False)
    prominence = forms.IntegerField(label="Increase colour area",
                                    widget=RangeInput(attrs=PROM_ATTRS))
    distance = forms.IntegerField(label="Broaden palette",
                                  widget=RangeInput(attrs=DIST_ATTRS))
    submitted = forms.CharField(widget=forms.HiddenInput())


def index(request):
    """
    Search and browse colours
    """

    FORM_INITIAL = {'prominence': 5, 'distance': 25, 'submitted': 'submitted'}
    artworks = Artwork.objects.all()
    form = ColourForm(request.GET)
    if 'submitted' in request.GET:
        if form.is_valid():
            prom = form.cleaned_data['prominence'] / 100.0
            dist = form.cleaned_data['distance']
            for cname, value in form.cleaned_data.iteritems():
                if value is True:
                    artworks = artworks.filter(
                        colours__name=cname.upper(),
                        colourdistance__prominence__gte=prom,
                        colourdistance__distance__lte=dist,
                        )

    else:
        form = ColourForm(initial=FORM_INITIAL)

    artworks = artworks.annotate(
        ave_distance=Avg("colourdistance__distance"),
        tot_prominence=Sum("colourdistance__prominence"),
        ave_presence=Avg("colourdistance__presence")
        )
    found_works = artworks.count()
    artworks = artworks.order_by('-ave_presence', 'ave_distance')[:50]
    t = loader.get_template("colour.html")
    context_data = {
        'artworks': artworks,
        'form': form,
        'found': found_works,
    }
    c = RequestContext(request, context_data)

    return HttpResponse(t.render(c))
