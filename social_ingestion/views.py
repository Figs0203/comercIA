from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
import requests

from .models import SocialPost, SocialAccount
from .forms import ConnectXForm
from django.conf import settings
from products.models import Product


def recommendations(request):
    category = request.GET.get('category', '').strip()
    query = request.GET.get('q', '').strip()

    # Base: posts detectados (limitado al usuario logueado si tiene SocialAccount)
    posts_qs = SocialPost.objects.none()
    if request.user.is_authenticated:
        try:
            social = SocialAccount.objects.get(user=request.user)
            posts_qs = SocialPost.objects.filter(author__iexact=social.username)
        except SocialAccount.DoesNotExist:
            pass
    if category:
        posts_qs = posts_qs.filter(matched_categories__icontains=category)
    if query:
        posts_qs = posts_qs.filter(Q(text__icontains=query) | Q(author__icontains=query))

    # Construir lista de categorías detectadas a partir de las últimas 5 publicaciones
    detected_categories: set[str] = set()
    for p in posts_qs.order_by('-published_at')[:5]:
        cats = (p.matched_categories or '')
        for c in [c.strip() for c in cats.split(',') if c.strip()]:
            detected_categories.add(c)

    # Si el usuario filtró una categoría válida, usarla preferentemente
    if category:
        detected_categories = {category}

    # Buscar productos que coincidan con las categorías detectadas
    products_qs = Product.objects.none()
    if detected_categories:
        products_qs = Product.objects.filter(available=True, category__in=sorted(detected_categories))
    if query:
        products_qs = products_qs.filter(Q(name__icontains=query) | Q(description__icontains=query))

    products_qs = products_qs.select_related('seller')[:48]

    # Paginación de posts para referencia
    paginator = Paginator(posts_qs, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    for p in page_obj.object_list:
        cats = (p.matched_categories or '')
        p.categories_list = [c.strip() for c in cats.split(',') if c.strip()]

    categories = ['Comida', 'Ropa', 'Tecnología']
    # Modo embed: simplificar layout para el iframe del home
    is_embed = request.GET.get('embed') == '1'
    context = {
        'page_obj': page_obj,
        'products': products_qs,
        'detected_categories': sorted(detected_categories),
        'category': category,
        'query': query,
        'categories': categories,
        'is_embed': is_embed,
    }
    return render(request, 'social_ingestion/recommendations.html', context)


@login_required
def connect_x(request):
    try:
        existing = SocialAccount.objects.get(user=request.user)
    except SocialAccount.DoesNotExist:
        existing = None

    if request.method == 'POST':
        form = ConnectXForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username'].strip().lstrip('@')
            bearer = getattr(settings, 'X_BEARER_TOKEN', '').strip()
            user_id = None
            if bearer and username:
                url = f"https://api.twitter.com/2/users/by/username/{username}"
                headers = {"Authorization": f"Bearer {bearer}"}
                try:
                    resp = requests.get(url, headers=headers, timeout=10)
                    if resp.status_code == 200:
                        data = resp.json()
                        user_id = data.get('data', {}).get('id')
                except requests.exceptions.RequestException:
                    user_id = None

            if existing:
                existing.username = username
                if user_id:
                    existing.external_user_id = user_id
                existing.save()
            else:
                SocialAccount.objects.create(
                    user=request.user,
                    platform='x',
                    username=username,
                    external_user_id=user_id or '',
                )
            return redirect('connect_x')
    else:
        form = ConnectXForm(initial={'username': existing.username if existing else ''})

    return render(request, 'social_ingestion/connect_x.html', {'form': form, 'existing': existing})

# Create your views here.
