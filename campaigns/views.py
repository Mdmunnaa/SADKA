from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q, Sum, Count
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from .models import Campaign, Category, Comment
from config.spam_protection import is_bot_submission, is_rate_limited


def custom_404(request, exception=None):
    return render(request, '404.html', status=404)


def custom_500(request):
    return render(request, '500.html', status=500)


def home(request):
    featured = Campaign.objects.filter(status__in=['active', 'urgent'], is_featured=True)[:3]
    urgent = Campaign.objects.filter(status='urgent').order_by('-created_at')[:4]
    active = Campaign.objects.filter(status='active').order_by('-created_at')[:6]
    completed = Campaign.objects.filter(status='completed').order_by('-created_at')[:3]
    categories = Category.objects.all()

    # Stats
    from donations.models import Donation
    from django.db.models import Sum, Count
    stats = {
        'total_raised': Donation.objects.filter(is_verified=True).aggregate(t=Sum('amount'))['t'] or 0,
        'total_donors': Donation.objects.filter(is_verified=True).count(),
        'total_campaigns': Campaign.objects.exclude(status='paused').count(),
        'completed_campaigns': Campaign.objects.filter(status='completed').count(),
    }

    context = {
        'featured': featured,
        'urgent': urgent,
        'active': active,
        'completed': completed,
        'categories': categories,
        'stats': stats,
    }
    return render(request, 'campaigns/home.html', context)


def campaign_list(request):
    campaigns = Campaign.objects.exclude(status='paused')
    categories = Category.objects.all()

    # Filter
    category_id = request.GET.get('category')
    status = request.GET.get('status')
    search = request.GET.get('q')

    if category_id:
        campaigns = campaigns.filter(category_id=category_id)
    if status:
        campaigns = campaigns.filter(status=status)
    if search:
        campaigns = campaigns.filter(Q(title__icontains=search) | Q(description__icontains=search))

    # Dynamic SEO title/description based on active filters
    status_labels = {'urgent': 'জরুরি', 'active': 'চলমান', 'completed': 'সম্পন্ন'}
    selected_category_obj = Category.objects.filter(id=category_id).first() if category_id else None

    seo_parts = []
    if selected_category_obj:
        seo_parts.append(selected_category_obj.name)
    if status in status_labels:
        seo_parts.append(status_labels[status])
    if search:
        seo_parts.append(f'"{search}"')

    if seo_parts:
        seo_title = f"{' · '.join(seo_parts)} ক্যাম্পেইন — সহায়.bd"
        seo_description = f"{' ও '.join(seo_parts)} সম্পর্কিত ডোনেশন ক্যাম্পেইন দেখুন এবং সহায়তা করুন। সহায়.bd-তে বিকাশ/নগদে সহজে দান করুন।"
    else:
        seo_title = "সকল ক্যাম্পেইন — সহায়.bd"
        seo_description = "বাংলাদেশের অসহায় মানুষদের জন্য চলমান সকল ডোনেশন ক্যাম্পেইন দেখুন। চিকিৎসা, শিক্ষা, খাদ্য ও দুর্যোগ সহায়তায় আজই দান করুন।"

    # Pagination — 9 campaigns per page (matches 3-column grid nicely)
    paginator = Paginator(campaigns, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'campaigns': page_obj,
        'page_obj': page_obj,
        'categories': categories,
        'selected_category': category_id,
        'selected_status': status,
        'search': search,
        'seo_title': seo_title,
        'seo_description': seo_description,
    }
    return render(request, 'campaigns/list.html', context)


def campaign_detail(request, slug):
    campaign = get_object_or_404(Campaign, slug=slug)
    updates = campaign.updates.all()
    recent_donors = campaign.donations.filter(is_verified=True).order_by('-created_at')[:10]
    comments = campaign.comments.filter(is_approved=True)
    related = Campaign.objects.filter(
        category=campaign.category, status__in=['active', 'urgent']
    ).exclude(pk=campaign.pk)[:3]

    if request.method == 'POST' and 'comment_message' in request.POST:
        if is_bot_submission(request):
            # Pretend it worked — never tell a bot *why* it failed, or it
            # just adapts. A genuine visitor never sees this branch at all.
            return redirect('campaign_detail', slug=slug)
        if is_rate_limited(request, 'campaign_comment', limit=5, window_seconds=600):
            messages.error(request, 'একটু পর আবার চেষ্টা করুন — অনেকগুলো মন্তব্য একসাথে জমা হয়েছে।')
            return redirect('campaign_detail', slug=slug)

        message_text = request.POST.get('comment_message', '').strip()
        name = request.POST.get('comment_name', '').strip() or 'অজ্ঞাত'
        if message_text:
            Comment.objects.create(campaign=campaign, name=name, message=message_text)
            messages.success(request, 'আপনার মন্তব্য যুক্ত হয়েছে। জাযাকাল্লাহ খায়রান!')
        else:
            messages.error(request, 'মন্তব্য খালি রাখা যাবে না।')
        return redirect('campaign_detail', slug=slug)

    context = {
        'campaign': campaign,
        'updates': updates,
        'recent_donors': recent_donors,
        'comments': comments,
        'related': related,
    }
    return render(request, 'campaigns/detail.html', context)


# ════ STATIC PAGES ════

def about(request):
    area_list = [
        {'icon': '🩺', 'title': 'চিকিৎসা সহায়তা', 'desc': 'জটিল ও ব্যয়বহুল রোগে আক্রান্ত অসহায় রোগীদের পাশে দাঁড়ানো।'},
        {'icon': '📚', 'title': 'শিক্ষাবৃত্তি ও উপকরণ', 'desc': 'সুবিধাবঞ্চিত মেধাবী শিক্ষার্থীদের পড়াশোনার খরচ বহন করা।'},
        {'icon': '🌧️', 'title': 'দুর্যোগ ও ত্রাণ', 'desc': 'বন্যা, শীত বা যেকোনো প্রাকৃতিক দুর্যোগে দ্রুততম সময়ে ত্রাণ বিতরণ।'},
        {'icon': '🤲', 'title': 'সাধারণ তহবিল ও সাদাকাহ', 'desc': 'এতিমখানা, বৃদ্ধাশ্রম এবং অতি দরিদ্র পরিবারের কর্মসংস্থানের ব্যবস্থা।'},
    ]
    return render(request, 'about.html', {'area_list': area_list})


def terms_of_service(request):
    terms_sections = [
        {
            'icon': 'check2-circle',
            'title': '১. শর্তাবলি গ্রহণ',
            'body': '\'সহায়.bd\' ওয়েবসাইট ভিজিট, দান, ভলান্টিয়ার আবেদন বা যেকোনোভাবে ব্যবহার করার মাধ্যমে আপনি এই শর্তাবলি মেনে নিচ্ছেন বলে ধরে নেওয়া হবে। শর্তাবলির সাথে দ্বিমত থাকলে অনুগ্রহ করে এই প্ল্যাটফর্ম ব্যবহার থেকে বিরত থাকুন।',
        },
        {
            'icon': 'building',
            'title': '২. প্ল্যাটফর্ম পরিচিতি',
            'body': '\'সহায়.bd\' একটি অলাভজনক, দাতব্য উদ্দেশ্যে পরিচালিত ডিজিটাল প্ল্যাটফর্ম, যেখানে সাধারণ মানুষের দান/সদকা/যাকাত সংগ্রহ করে যাচাইকৃত উপায়ে অসহায় ও সুবিধাবঞ্চিত মানুষের কল্যাণে ব্যয় করা হয়। প্ল্যাটফর্মের পরিচালনাগত ও নিবন্ধন সংক্রান্ত হালনাগাদ তথ্য "আমাদের সম্পর্কে" পাতায় পাওয়া যাবে।',
        },
        {
            'icon': 'cash-coin',
            'title': '৩. দান, ফেরত ও যাচাইকরণ নীতি',
            'body': 'সকল দান স্বেচ্ছাপ্রণোদিত এবং সাধারণত অ-ফেরতযোগ্য। প্রতিটি দান নিশ্চিত হওয়ার আগে প্রদত্ত Transaction ID/Reference যাচাই করে দেখা হয় — তাই ড্যাশবোর্ডে "যাচাইকৃত" স্ট্যাটাস দেখতে কিছুটা সময় লাগতে পারে। ভুলবশত ডাবল পেমেন্ট বা স্পষ্ট টেকনিক্যাল ত্রুটির ক্ষেত্রে আমাদের সাথে যোগাযোগ করলে যথাযথ যাচাই সাপেক্ষে সমাধানের চেষ্টা করা হবে।',
        },
        {
            'icon': 'moon-stars-fill',
            'title': '৪. যাকাত ও সদকা সংক্রান্ত বিশেষ শর্ত',
            'body': 'যাকাত হিসেবে প্রদত্ত অর্থ ইসলামি শরিয়াহ অনুমোদিত নির্দিষ্ট আটটি খাতেই ব্যয় করা হয়, অন্য কোনো খাতে নয়। সাধারণ সদকা/দান নমনীয়ভাবে প্রয়োজন অনুযায়ী সংশ্লিষ্ট ক্যাম্পেইনে ব্যয় করা হয়।',
        },
        {
            'icon': 'piggy-bank',
            'title': '৫. তহবিল বরাদ্দে বিচক্ষণতা',
            'body': 'কোনো নির্দিষ্ট ক্যাম্পেইনের জন্য সংগৃহীত অর্থ প্রয়োজনের তুলনায় বেশি হয়ে গেলে, উদ্বৃত্ত অর্থ একই ধরনের ভবিষ্যৎ ক্যাম্পেইনে বা সাধারণ তহবিলে ব্যবহারের এখতিয়ার কর্তৃপক্ষের থাকবে। এই নীতি ওয়েবসাইটে প্রকাশিত থাকবে।',
        },
        {
            'icon': 'person-badge',
            'title': '৬. ভলান্টিয়ার সংক্রান্ত শর্ত',
            'body': 'ভলান্টিয়ার হিসেবে যুক্ত হওয়া সম্পূর্ণ স্বেচ্ছাসেবামূলক ও অবৈতনিক। ভলান্টিয়ার আইডি কার্ড শুধুমাত্র পরিচয় যাচাইয়ের উদ্দেশ্যে ইস্যু করা হয় এবং যেকোনো সময় কর্তৃপক্ষ তা বাতিল/স্থগিত করার অধিকার রাখে। আইডি কার্ডের মালিকানা \'সহায়.bd\'-এর, এবং তা অপব্যবহার আইনি ব্যবস্থার আওতাভুক্ত হতে পারে।',
        },
        {
            'icon': 'shield-exclamation',
            'title': '৭. নিষিদ্ধ কার্যকলাপ',
            'body': 'ভুয়া/মিথ্যা পেমেন্ট রেফারেন্স প্রদান, মন্তব্য বিভাগে স্প্যাম বা বিজ্ঞাপন পোস্ট করা, অন্য কারো পরিচয়ে ভলান্টিয়ার/দাতা সেজে প্রতারণা, বা ওয়েবসাইটের স্বাভাবিক কার্যক্রমে বাধা সৃষ্টি করার যেকোনো চেষ্টা কঠোরভাবে নিষিদ্ধ এবং তা সংশ্লিষ্ট আইন অনুযায়ী ব্যবস্থার আওতাভুক্ত হতে পারে।',
        },
        {
            'icon': 'exclamation-diamond',
            'title': '৮. দায়বদ্ধতার সীমাবদ্ধতা',
            'body': 'বিকাশ/নগদ/রকেটের মতো তৃতীয়-পক্ষীয় মোবাইল ব্যাংকিং সেবার সাময়িক বিভ্রাট বা ত্রুটির জন্য \'সহায়.bd\' দায়ী থাকবে না। ওয়েবসাইট "যেমন আছে" ভিত্তিতে প্রদান করা হয়; কারিগরি ত্রুটিমুক্ত থাকার নিশ্চয়তা দেওয়া হয় না, তবে যেকোনো সমস্যা দ্রুত সমাধানের চেষ্টা করা হবে।',
        },
        {
            'icon': 'arrow-repeat',
            'title': '৯. শর্তাবলির পরিবর্তন',
            'body': 'প্রয়োজন অনুযায়ী এই শর্তাবলি যেকোনো সময় হালনাগাদ করা হতে পারে। উল্লেখযোগ্য পরিবর্তন হলে ওয়েবসাইটে জানিয়ে দেওয়া হবে। পরিবর্তনের পরেও প্ল্যাটফর্ম ব্যবহার চালিয়ে গেলে তা নতুন শর্তাবলি মেনে নেওয়া হিসেবে গণ্য হবে।',
        },
        {
            'icon': 'bank',
            'title': '১০. প্রযোজ্য আইন',
            'body': 'এই শর্তাবলি বাংলাদেশের প্রচলিত আইন অনুযায়ী পরিচালিত ও ব্যাখ্যাযোগ্য। যেকোনো আইনি বিরোধের ক্ষেত্রে বাংলাদেশের আদালতের এখতিয়ার প্রযোজ্য হবে।',
        },
    ]
    return render(request, 'terms.html', {'terms_sections': terms_sections})


def privacy(request):
    privacy_sections = [
        {
            'icon': 'shield-lock-fill',
            'title': '১. আমরা কী কী তথ্য সংগ্রহ করি?',
            'body': 'দান করার সময় আমরা আপনার নাম, ইমেইল অ্যাড্রেস, মোবাইল নম্বর এবং ট্রানজেকশন আইডি সংগ্রহ করে থাকি। যারা ভলান্টিয়ার হিসেবে যুক্ত হতে চান, তাদের ক্ষেত্রে জাতীয় পরিচয়পত্র (NID), পেশা এবং বর্তমান ঠিকানার তথ্য সংগ্রহ করি।',
        },
        {
            'icon': 'info-circle-fill',
            'title': '২. তথ্য ব্যবহারের উদ্দেশ্য',
            'body': 'আপনার দেওয়া তথ্য শুধুমাত্র ডোনেশনের হিসাব রাখা, ডিজিটাল রসিদ পাঠানো, ক্যাম্পেইনের সফলতার আপডেট জানানো এবং ভলান্টিয়ারদের সাথে যোগাযোগের কাজে ব্যবহার করা হয়।',
        },
        {
            'icon': 'x-circle-fill',
            'title': '৩. তথ্য শেয়ার ও থার্ড-পার্টি পলিসি',
            'body': 'আমরা অত্যন্ত কঠোরভাবে প্রতিশ্রুতিবদ্ধ যে, কোনো ডোনার বা ভলান্টিয়ারের ব্যক্তিগত তথ্য আমরা কখনোই কোনো থার্ড-পার্টি, মার্কেটিং কোম্পানি বা অন্য কোনো সংস্থার কাছে বিক্রি বা শেয়ার করি না।',
        },
        {
            'icon': 'eye-slash-fill',
            'title': '৪. নাম গোপন রেখে দান (Anonymous Donation)',
            'body': 'আপনি চাইলে "নাম গোপন রাখুন (Anonymous)" অপশনটি ব্যবহার করতে পারেন। এক্ষেত্রে আপনার ডোনেশনটি সফল হলেও ওয়েবসাইটে বা পাবলিক লিস্টে আপনার নাম বা পরিচয় সম্পূর্ণ গোপন রাখা হবে।',
        },
        {
            'icon': 'check-circle-fill',
            'title': '৫. পেমেন্ট নিরাপত্তা ও ডেটা এনক্রিপশন',
            'body': 'আমরা সরাসরি আপনার কোনো ব্যাংক অ্যাকাউন্ট, কার্ডের পিন বা পাসওয়ার্ড সংরক্ষণ করি না। পেমেন্টের কাজটি সম্পূর্ণ নিরাপদ এবং এনক্রিপ্টেড পেমেন্ট গেটওয়ে ও মোবাইল ব্যাংকিং (বিকাশ, নগদ, রকেট) চ্যানেলের মাধ্যমে সম্পন্ন হয়।',
        },
    ]
    return render(request, 'privacy.html', {'privacy_sections': privacy_sections})


def faq(request):
    faqs = [
        {'q': 'আপনারা অ্যাকাউন্টের হিসাব বা অডিট কীভাবে করেন?',
         'a': 'আমরা প্রতিটি ক্যাম্পেইনের ফান্ড কালেকশন এবং খরচের রিয়েল-টাইম আপডেট ওয়েবসাইটে প্রকাশ করি। সকল প্রকার খরচের রশিদ ও ভাউচার ওয়েবসাইটের আপডেট ট্যাবে যুক্ত করে থাকি।'},
        {'q': '\'সহায়.bd\' মূলত কী কী ধরনের কাজ করে?',
         'a': 'আমরা মূলত অসহায় রোগীদের চিকিৎসা সহায়তা, সুবিধাবঞ্চিত শিশুদের শিক্ষা, দুর্যোগে ত্রাণ বিতরণ, এতিমখানা ও বৃদ্ধাশ্রমে সহায়তা এবং কর্মসংস্থান তৈরির মতো সমাজকল্যাণমূলক প্রজেক্ট নিয়ে কাজ করি।'},
        {'q': 'আমি কীভাবে ভলান্টিয়ার হতে পারি?',
         'a': 'যে কেউ চাইলে আমাদের সমাজসেবামূলক কাজের অংশ হতে পারেন! "ভলান্টিয়ার হোন" পেজে ফর্ম পূরণের মাধ্যমে খুব সহজেই আমাদের নেটওয়ার্কের সাথে যুক্ত হতে পারবেন।'},
        {'q': 'এই প্ল্যাটফর্মের প্রতিষ্ঠাতা কারা?',
         'a': '\'সহায়.bd\' একদল নিবেদিতপ্রাণ তরুণ, আইটি প্রফেশনাল এবং সমাজকর্মীদের একটি সম্মিলিত উদ্যোগ। সমাজের সুবিধাবঞ্চিত মানুষের জন্য একটি স্বচ্ছ ডিজিটাল প্ল্যাটফর্ম গড়ার স্বপ্ন থেকেই এটি প্রতিষ্ঠিত হয়েছে।'},
        {'q': 'আমি কি আপনাদের কার্যক্রম সরাসরি ভিজিট করতে পারি?',
         'a': 'অবশ্যই! আমরা আমাদের কাজের ক্ষেত্রে সর্বোচ্চ স্বচ্ছতায় বিশ্বাস করি। যেকোনো ডোনার বা শুভানুধ্যায়ী আমাদের সাথে যোগাযোগ করে চলমান প্রজেক্টগুলো সরাসরি মাঠে গিয়ে ভিজিট করতে পারবেন।'},
        {'q': 'আপনারা কি রাস্তায় বা বাড়ি বাড়ি গিয়ে ফান্ড কালেকশন করেন?',
         'a': 'না। \'সহায়.bd\' কখনোই রাস্তাঘাটে বা বাড়ি বাড়ি গিয়ে সরাসরি নগদ অর্থ সংগ্রহ করে না। আমাদের সকল ডোনেশন শুধুমাত্র ওয়েবসাইট ও অফিসিয়াল মোবাইল ব্যাংকিং (বিকাশ/নগদ/রকেট)-এর মাধ্যমেই গ্রহণ করা হয়।'},
        {'q': 'যাকাত বা ফিতরার টাকা কি এই প্ল্যাটফর্মে দেওয়া যাবে?',
         'a': 'হ্যাঁ, দেওয়া যাবে। আমাদের যাকাত ক্যালকুলেটর ব্যবহার করে হিসাব করুন এবং আমাদের সাধারণ তহবিলে দান করুন। যাকাতের টাকা ইসলামিক শরিয়াহ অনুযায়ী যাচাইকৃত নির্দিষ্ট খাতেই ব্যয় করা হয়।'},
    ]
    return render(request, 'faq.html', {'faqs': faqs})


def volunteer_signup(request):
    from django.urls import reverse
    from .models import Volunteer

    if not request.user.is_authenticated:
        # Consistent with the blog-comment login gate elsewhere on the site:
        # volunteering is tied to the same donor account system, so a person
        # can later log back in to check status / download their ID card.
        messages.info(request, 'ভলান্টিয়ার আবেদন করতে হলে আগে লগইন বা রেজিস্ট্রেশন করুন।')
        return redirect(f"{reverse('donor_login')}?next={request.path}")

    existing = Volunteer.objects.filter(user=request.user).first()
    if existing:
        return redirect('volunteer_dashboard')

    success = False
    if request.method == 'POST':
        if is_bot_submission(request):
            return redirect('volunteer_signup')
        if is_rate_limited(request, 'volunteer_signup', limit=3, window_seconds=3600):
            messages.error(request, 'একটু পর আবার চেষ্টা করুন।')
            return redirect('volunteer_signup')

        name = request.POST.get('name', '').strip()
        phone = request.POST.get('phone', '').strip()
        email = request.POST.get('email', '').strip()
        profession = request.POST.get('profession', '').strip()
        address = request.POST.get('address', '').strip()
        nid = request.POST.get('nid', '').strip()
        why = request.POST.get('why_volunteer', '').strip()

        if name and phone and profession and address and nid:
            Volunteer.objects.create(
                user=request.user,
                name=name, phone=phone, email=email,
                profession=profession, address=address,
                nid=nid, why_volunteer=why,
            )
            success = True
        else:
            messages.error(request, 'অনুগ্রহ করে সব তারকা (*) চিহ্নিত ঘর পূরণ করুন।')

    return render(request, 'volunteer.html', {'success': success})


@login_required(login_url='donor_login')
def volunteer_dashboard(request):
    from .models import Volunteer
    volunteer = Volunteer.objects.filter(user=request.user).first()
    if not volunteer:
        return redirect('volunteer_signup')

    verify_url = request.build_absolute_uri(
        f"/volunteer/verify/{volunteer.volunteer_id}/"
    ) if volunteer.volunteer_id else None

    return render(request, 'volunteer_dashboard.html', {
        'volunteer': volunteer,
        'verify_url': verify_url,
    })


@login_required(login_url='donor_login')
def volunteer_id_card_download(request):
    from django.http import HttpResponse, Http404
    from .models import Volunteer
    from .id_card import generate_volunteer_id_card_pdf

    volunteer = Volunteer.objects.filter(user=request.user).first()
    if not volunteer or volunteer.status != 'approved':
        raise Http404

    verify_url = request.build_absolute_uri(f"/volunteer/verify/{volunteer.volunteer_id}/")
    pdf_buf = generate_volunteer_id_card_pdf(volunteer, verify_url)

    response = HttpResponse(pdf_buf.read(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="sahay-volunteer-{volunteer.volunteer_id}.pdf"'
    return response


def volunteer_verify(request, volunteer_id):
    """Public page — no login required. Anyone (a donor, a beneficiary, a
    curious neighbour) can scan the QR code on a volunteer's card or type in
    the ID to confirm it's a real, currently-approved Sahay.bd volunteer.
    Deliberately shows only name/photo/status — never phone, NID, address,
    or email, since this page is public."""
    from .models import Volunteer
    volunteer = Volunteer.objects.filter(volunteer_id=volunteer_id).first()
    return render(request, 'volunteer_verify.html', {
        'volunteer': volunteer,
        'volunteer_id': volunteer_id,
    })



