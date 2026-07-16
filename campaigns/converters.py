class UnicodeSlugConverter:
    """
    Custom path converter that accepts Unicode slugs (e.g. Bengali characters),
    unlike Django's built-in 'slug' converter which is ASCII-only.

    IMPORTANT: plain `\\w` is NOT enough for Bengali. Python's `\\w` only matches
    Unicode categories that count as "alphanumeric" (letters/digits) plus
    underscore. Bengali vowel signs (matras) like া ি ী ে ৈ ো ৌ and the
    virama/hasant ্ are Unicode combining marks (categories Mn/Mc), which are
    NOT alphanumeric and therefore NOT matched by `\\w` — even though they are
    a normal, essential part of almost every real Bengali word. Without the
    explicit \u0980-\u09FF range below, a correctly-generated Bengali slug
    (e.g. "রহিমের-চিকিৎসা-সহায়তা") would fail to match this converter's
    regex and every such campaign/blog URL would 404.
    """
    regex = r'[-\w\u0980-\u09FF]+'

    def to_python(self, value):
        return value

    def to_url(self, value):
        return value
