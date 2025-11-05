"""
URL configuration for comercia project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from products import views as products_views
from social_ingestion import views as social_views
from seller_profiles import views as profile_views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.views.static import serve
from django.conf.urls.i18n import i18n_patterns
from django.urls import include

urlpatterns = [path('i18n/', include('django.conf.urls.i18n'))]

urlpatterns += i18n_patterns(
    # Admin
    path('admin/', admin.site.urls),
    
    # Products app URLs
    path('', products_views.home, name='home'),
    path('api/products/', products_views.products_api, name='products_api'),
    path('productos-aliados/', products_views.aliados_list, name='aliados_list'),
    path('productos/', products_views.productos_externos, name='productos_externos'),
    path('reporte/descargar/', products_views.download_report, name='download_report'),
    path('add-product/', products_views.add_product, name='add_product'),
    path('edit-product/<int:product_id>/', products_views.edit_product, name='edit_product'),
    path('delete-product/<int:product_id>/', products_views.delete_product, name='delete_product'),
    path('product/<int:product_id>/', products_views.product_detail, name='product_detail'),
    path('chat-search/', products_views.chat_search, name='chat_search'),
    path('registrar-click-whatsapp/', products_views.register_whatsapp_click, name='register_whatsapp_click'),
    
    # Authentication URLs
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    path('register/', products_views.register, name='register'),
    
    # Password reset URLs
    path('password_reset/', auth_views.PasswordResetView.as_view(
        template_name='registration/password_reset_form.html',
        email_template_name='registration/password_reset_email.html',
        subject_template_name='registration/password_reset_subject.txt'
    ), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='registration/password_reset_done.html'
    ), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='registration/password_reset_confirm.html'
    ), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='registration/password_reset_complete.html'
    ), name='password_reset_complete'),
    
    # Comments URLs
    path('comment/add/<int:product_id>/', products_views.add_comment, name='add_comment'),
    path('comment/delete/<int:comment_id>/', products_views.delete_comment, name='delete_comment'),
    
    # Favorites URLs
    path('favorite/toggle/<int:product_id>/', products_views.toggle_favorite, name='toggle_favorite'),
    path('favorites/', products_views.favorites_list, name='favorites_list'),
    
    # Seller profiles URLs
    path('profile/', profile_views.view_profile, name='view_profile'),
    path('profile/create/', profile_views.create_profile, name='create_profile'),
    path('profile/edit/', profile_views.edit_profile, name='edit_profile'),
    path('seller/<int:user_id>/', profile_views.public_profile, name='public_profile'),
    path('sellers/', profile_views.seller_list, name='seller_list'),

    # Social ingestion URLs
    path('connect-x/', social_views.connect_x, name='connect_x'),
    path('recomendaciones/', social_views.recommendations, name='recommendations'),
    path('mis-intereses/', social_views.add_interest, name='add_interest'),
    
    # Development URLs
    path('start-ngrok/', products_views.start_ngrok_view, name='start_ngrok'),
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    ]