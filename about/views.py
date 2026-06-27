from django.shortcuts import render


def about(request):
    """关于页面"""
    return render(request, 'about.html')