from django.shortcuts import redirect
from django.contrib import messages
from django.urls import resolve, reverse

class SellerProfileMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and not request.path.startswith('/admin/'):
            current_url = resolve(request.path_info).url_name
            seller_urls = ['add_product', 'edit_product', 'delete_product']
            
            if current_url in seller_urls:
                try:
                    request.user.seller_profile
                except:
                    messages.warning(
                        request,
                        'Necesitas crear un perfil de vendedor antes de publicar productos.'
                    )
                    return redirect('create_profile')

        response = self.get_response(request)
        return response 