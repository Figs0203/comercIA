from django import template

register = template.Library()

@register.filter(name='call')
def call(obj, *args):
    """Call a method on an object with the given arguments."""
    if len(args) == 1 and isinstance(args[0], (list, tuple)):
        args = args[0]
    return obj(*args) if callable(obj) else obj

@register.filter(name='addclass')
def addclass(field, css):
    return field.as_widget(attrs={'class': css}) 