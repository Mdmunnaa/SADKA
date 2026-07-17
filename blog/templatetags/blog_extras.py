from django import template
from django.utils.translation import get_language

register = template.Library()


@register.filter
def localized_blog_title(post):
    """Returns post.title_en if the active language is English and a
    translation exists, otherwise falls back to the original Bangla title.
    Usage: {{ post|localized_blog_title }}"""
    lang = get_language()
    return post.display_title(language='en' if lang == 'en' else 'bn')


@register.filter
def localized_blog_excerpt(post):
    lang = get_language()
    return post.display_excerpt(language='en' if lang == 'en' else 'bn')


@register.filter
def localized_blog_content(post):
    lang = get_language()
    return post.display_content(language='en' if lang == 'en' else 'bn')


@register.filter
def localized_blog_meta_title(post):
    lang = get_language()
    return post.get_meta_title(language='en' if lang == 'en' else 'bn')


@register.filter
def localized_blog_meta_description(post):
    lang = get_language()
    return post.get_meta_description(language='en' if lang == 'en' else 'bn')
