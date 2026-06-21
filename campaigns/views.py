from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q, Sum, Count
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from .models import Campaign, Category, Comment


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
    from .models import Volunteer
    success = False
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        phone = request.POST.get('phone', '').strip()
        email = request.POST.get('email', '').strip()
        profession = request.POST.get('profession', '').strip()
        address = request.POST.get('address', '').strip()
        nid = request.POST.get('nid', '').strip()
        why = request.POST.get('why_volunteer', '').strip()

        if name and phone and profession and address and nid:
            Volunteer.objects.create(
                name=name, phone=phone, email=email,
                profession=profession, address=address,
                nid=nid, why_volunteer=why,
            )
            success = True
        else:
            from django.contrib import messages
            messages.error(request, 'অনুগ্রহ করে সব তারকা (*) চিহ্নিত ঘর পূরণ করুন।')

    return render(request, 'volunteer.html', {'success': success})
