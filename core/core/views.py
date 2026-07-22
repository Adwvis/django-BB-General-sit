from django.shortcuts import redirect

def custom_404(request, exception):
    return redirect("accounts:UrlsMap")