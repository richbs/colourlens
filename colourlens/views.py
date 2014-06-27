from django.db.models import Avg, Sum, Count
from django import forms
from django.forms.widgets import Input
from django.http import HttpResponse
from django.template import RequestContext, loader
from colourlens.models import Artwork, Colour


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
        

def index(request, institution=False):
    """
    Search and browse colours
    """
    DISTANCE = 25
    artworks = Artwork.objects.select_related().all()
    colours = Colour.objects.all()
    req_colours = request.GET.getlist('colour', [])
    startyear = request.GET.get('startyear', None)
    endyear = request.GET.get('endyear', None)

    if startyear:
        artworks = artworks.filter(year__gte=startyear)
    if endyear:
        artworks = artworks.filter(year__lte=endyear)
        
    for hex_value in req_colours:
        artworks = artworks.filter(
            colours__hex_value=hex_value,
            colourdistance__distance__lte=DISTANCE,
        )


    artworks = artworks.annotate(
        ave_distance=Avg("colourdistance__distance"),
        ave_presence=Avg("colourdistance__presence"),
        tot_presence=Sum("colourdistance__presence")        
        )
    if institution:
        artworks = artworks.filter(institution=institution)

    if req_colours or institution or startyear or endyear:
        colours = colours.filter(
                        colourdistance__distance__lte=DISTANCE,
                        artwork__id__in=[a.id for a in artworks]
                            )
        
    artworks = artworks.order_by('-tot_presence').distinct()
    found_works = artworks.count()
    colours = colours.annotate(Count('artwork', distinct=True)).order_by('hue')
    tot = 0
    total_palette = reduce(lambda x,y: x+y, [c.artwork__count for c in colours])
    colour_count = colours.count()
    colour_width = 100.0 / colour_count
    institutions = Artwork.objects.all().values('institution').distinct()
    t = loader.get_template("colour.html")
    context_data = {
        'artworks': artworks[:100],
        'colours': colours,
        'colour_count': colour_count,
        'colour_width': colour_width,
        'total_palette': total_palette,
        'found': found_works,
        'institution': institution,
        'institutions': institutions,
        'req_colours': req_colours,
    }
    c = RequestContext(request, context_data)

    return HttpResponse(t.render(c))
