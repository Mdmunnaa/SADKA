class UnicodeSlugConverter:
    """
    Custom path converter that accepts Unicode slugs (e.g. Bengali characters),
    unlike Django's built-in 'slug' converter which is ASCII-only.
    """
    regex = r'[-\w]+'

    def to_python(self, value):
        return value

    def to_url(self, value):
        return value
