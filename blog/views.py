from django.shortcuts import render, get_object_or_404
from django.http import Http404
from django.core.paginator import Paginator
from django.db.models import Q, F

from .models import BlogPost, BlogCategory, BlogTag
from campaigns.models import Campaign


def _pick_cta_campaign(preferred=None):
    """Choose which campaign the blog's Donate buttons should point to.
    Prefers an explicitly related campaign (if still active/urgent),
    otherwise falls back to the most urgent / featured active campaign."""
    if preferred and preferred.status in ('active', 'urgent'):
        return preferred
    return Campaign.objects.filter(status__in=['urgent', 'active']) \
        .order_by('-is_featured', '-created_at').first()


def blog_list(request):
    posts = BlogPost.published.select_related('category', 'related_campaign').prefetch_related('tags')

    category_slug = request.GET.get('category')
    tag_slug = request.GET.get('tag')
    search = request.GET.get('q')

    selected_category = None
    selected_tag = None

    if category_slug:
        selected_category = BlogCategory.objects.filter(slug=category_slug).first()
        if selected_category:
            posts = posts.filter(category=selected_category)
    if tag_slug:
        selected_tag = BlogTag.objects.filter(slug=tag_slug).first()
        if selected_tag:
            posts = posts.filter(tags=selected_tag)
    if search:
        posts = posts.filter(
            Q(title__icontains=search) | Q(excerpt__icontains=search) | Q(content__icontains=search)
        )

    paginator = Paginator(posts, 9)
    page_obj = paginator.get_page(request.GET.get('page'))

    categories = BlogCategory.objects.all()
    cta_campaign = _pick_cta_campaign()

    seo_parts = []
    if selected_category:
        seo_parts.append(selected_category.name)
    if search:
        seo_parts.append(f'"{search}"')

    if seo_parts:
        seo_title = f"{' · '.join(seo_parts)} — ব্লগ — সহায়.bd"
    else:
        seo_title = "ব্লগ — সহায়.bd"
    seo_description = "সহায়.bd এর ব্লগ — impact story, যাকাত গাইড, ক্যাম্পেইন আপডেট ও ঘোষণা। আপনার দানে যা বদলে যাচ্ছে, তার গল্প পড়ুন।"

    context = {
        'posts': page_obj,
        'page_obj': page_obj,
        'categories': categories,
        'selected_category': selected_category,
        'selected_tag': selected_tag,
        'search': search,
        'cta_campaign': cta_campaign,
        'seo_title': seo_title,
        'seo_description': seo_description,
    }
    return render(request, 'blog/list.html', context)


def blog_detail(request, slug):
    post = get_object_or_404(BlogPost, slug=slug)

    # Staff can preview drafts/scheduled posts; the public cannot.
    if not post.is_visible and not (request.user.is_authenticated and request.user.is_staff):
        raise Http404

    # Best-effort view counter (fine if two requests race; not financial data)
    BlogPost.objects.filter(pk=post.pk).update(views_count=F('views_count') + 1)

    related_posts = BlogPost.published.exclude(pk=post.pk)
    if post.category:
        related_posts = related_posts.filter(category=post.category)
    related_posts = related_posts.select_related('category')[:3]

    cta_campaign = _pick_cta_campaign(post.related_campaign)

    context = {
        'post': post,
        'related_posts': related_posts,
        'cta_campaign': cta_campaign,
    }
    return render(request, 'blog/detail.html', context)
