import uuid
from pprint import pprint

import requests
from django.conf import settings
from django.urls import reverse

MSGRAPH = "https://graph.microsoft.com"  # Add the resource you want the access token for
AUTHORITY_HOST_URL = "https://login.microsoftonline.com"

# These settings are for the Microsoft Graph API Call
API_VERSION = 'v1.0'

AUTHORITY_URL = AUTHORITY_HOST_URL + '/' + settings.TENANT
TEMPLATE_AUTHZ_URL = ('https://login.microsoftonline.com/{}/oauth2/authorize?' +
                      'response_type=code&client_id={}&redirect_uri={}&' +
                      'state={}&resource={}')


def get_authorization_url(request):
    auth_state = str(uuid.uuid4())
    request.session['state'] = auth_state

    return TEMPLATE_AUTHZ_URL.format(
        settings.TENANT,
        settings.CLIENT_ID,
        request.build_absolute_uri(reverse('token')),
        auth_state,
        MSGRAPH)


def graph_get(request, end_point_uri):
    endpoint = MSGRAPH + '/' + API_VERSION + end_point_uri
    token = request.session['token']
    print("------------------------------------------------------------------------------------")
    print("GRAPH_GET %s" % end_point_uri)
    pprint(token)
    print("------------------------------------------------------------------------------------")
    http_headers = {'Authorization': 'Bearer ' + token['accessToken'],
                    'User-Agent': 'django_auth_msadal',
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                    'client-request-id': str(uuid.uuid4())}
    return requests.get(endpoint, headers=http_headers, stream=False).json()


def graph_get_me(request):
    return graph_get(request, '/me/')


def graph_get_my_groups(request):
    return graph_get(request, '/me/memberOf')
