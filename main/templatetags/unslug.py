from django.template.defaultfilters import stringfilter, register


@register.filter
@stringfilter
def unslugify(value):
    return " ".join([v.capitalize() for v in value.split("-")])
