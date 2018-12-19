from datetime import datetime
from pprint import pprint

from django.conf import settings
from django.http import HttpResponse
import adal
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib.auth import authenticate, get_user_model, login as django_login
from django_auth_msadal.models import AuthToken
from django_auth_msadal.msgraph import get_authorization_url, AUTHORITY_URL, MSGRAPH, graph_get_me, graph_get_my_groups


# Create your views here.
def login(request):
    authorization_url = get_authorization_url(request)
    resp = HttpResponse(status=307)
    resp['location'] = authorization_url
    return resp


def token_exchange(request):
    code = request.GET['code']
    state = request.GET['state']
    if state != request.session.get('state'):
        raise ValueError("State does not match")
    auth_context = adal.AuthenticationContext(AUTHORITY_URL)
    token_response = auth_context.acquire_token_with_authorization_code(code,
                                                                        request.build_absolute_uri(reverse('token')),
                                                                        MSGRAPH,
                                                                        settings.CLIENT_ID,
                                                                        settings.CLIENT_SECRET)
    # It is recommended to save this to a database when using a production app.
    request.session['token'] = token_response

    graph_data = graph_get_me(request)
    request.session['graph_me'] = graph_data

    user_model = get_user_model()
    try:
        # try to retrieve user from database and update it
        usr = user_model.objects.get(username=token_response['userId'])
    except user_model.DoesNotExist:
        # user does not exist in database already, create it
        usr = user_model()
        usr.username = token_response['userId']

    usr.first_name = graph_data['givenName']
    usr.last_name = graph_data['surname']
    usr.email = graph_data['mail']

    # update existing or new user with LDAP data
    usr.set_password(token_response['accessToken'])
    usr.last_login = datetime.now()
    usr.save()

    try:
        # try to retrieve user from database and update it
        token = AuthToken.objects.get(username=token_response['userId'])
    except AuthToken.DoesNotExist:
        # user does not exist in database already, create it
        token = AuthToken()
        token.username = token_response['userId']

    token.token = request.session['token']['accessToken']
    token.save()

    # management of groups
    graph_data = graph_get_my_groups(request)
    request.session['graph_groups'] = graph_data

    # authenticate against Django
    user = authenticate(request=request, username=token_response['userId'],
                        password=token_response['accessToken'])

    if user is not None:
        django_login(request, user)
    else:
        redirect('login')

    return redirect(settings.HOME_REDIRECTION)
