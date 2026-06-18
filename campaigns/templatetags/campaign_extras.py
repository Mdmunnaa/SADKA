from django import template
from django.utils.translation import get_language

register = template.Library()


@register.filter
def localized_title(campaign):
    """Returns campaign.title_en if current active language is English and a translation
    exists, otherwise falls back to the original Bangla title. Usage: {{ c|localized_title }}"""
    lang = get_language()
    return campaign.display_title(language='en' if lang == 'en' else 'bn')


@register.filter
def localized_description(campaign):
    lang = get_language()
    return campaign.display_description(language='en' if lang == 'en' else 'bn')


@register.filter
def localized_short_description(campaign):
    lang = get_language()
    return campaign.display_short_description(language='en' if lang == 'en' else 'bn')
