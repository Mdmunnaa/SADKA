from .spam_protection import form_timestamp


def spam_protection(request):
    """Makes {{ spam_form_timestamp }} available in every template — needed
    because the donation form (in base.html) is rendered on every single
    page, not just from one view's GET handler."""
    return {'spam_form_timestamp': form_timestamp()}


def payment_gateway_info(request):
    """Lets the donate modal (in base.html, rendered on every page) know
    whether to show the manual 'send money to this number, then enter your
    reference' fields (today's default), or the simpler 'you'll be taken to
    a secure payment page' message used once an automated gateway is active.
    Uses the same fallback-aware lookup donate() itself uses, so the modal
    never promises a gateway redirect that won't actually happen (e.g. a
    gateway name is set in settings but its API keys haven't been added yet)."""
    from donations.gateways import get_active_gateway, ManualGateway
    is_manual = isinstance(get_active_gateway(), ManualGateway)
    return {'payment_gateway_is_manual': is_manual}


def general_fund_campaign(request):
    """Makes the permanent 'সাধারণ সদকা তহবিল' (General Sadaqah Fund)
    campaign available in every template, so the navbar's 'ডোনেট করুন'
    button can open the donate modal directly for it instead of sending
    people to browse the campaign list first. Returns None (rather than
    raising) if that campaign has been deleted/renamed for any reason —
    base.html falls back to linking to the campaign list in that case, so
    the site never breaks over this."""
    from campaigns.models import Campaign
    campaign = Campaign.objects.filter(slug='general-sadaqah-fund').first()
    return {'general_fund_campaign': campaign}
