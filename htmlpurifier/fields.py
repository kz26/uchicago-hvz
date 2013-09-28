from django.forms.fields import CharField
from htmlpurifier.purify import *

class HTMLField(CharField):
    def clean(self, value):
        raw = super(HTMLField, self).clean(value)
        return purify(raw)
