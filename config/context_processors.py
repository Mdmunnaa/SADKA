from .spam_protection import form_timestamp


def spam_protection(request):
    """Makes {{ spam_form_timestamp }} available in every template — needed
    because the donation form (in base.html) is rendered on every single
    page, not just from one view's GET handler."""
    return {'spam_form_timestamp': form_timestamp()}
