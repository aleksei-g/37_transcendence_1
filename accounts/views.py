from django.http import HttpResponse

def user_page(request, user_id):
    return HttpResponse(
        '<title>User page</title>'
        '<h1>Hello, User!</h1>'
        '<p>Your id: {}</p>'
        .format(user_id)
    )
