from django.shortcuts import render

def home(request):
    """Главная страница приложения"""
    return render(request, 'base.html')