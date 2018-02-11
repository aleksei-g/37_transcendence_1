from django.shortcuts import render, get_object_or_404
from django.contrib.auth.models import User


def user_page(request, user_id):
    user = get_object_or_404(User, id=user_id)
    return render(
        request,
        'user_page.html',
        {'user': user},
    )
