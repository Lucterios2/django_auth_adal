# -*- coding: utf-8 -*-
from datetime import datetime
import logging
from pprint import pprint

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ObjectDoesNotExist

from django_auth_msadal.models import AuthToken

logger = logging.getLogger(__name__)


class MSADALAuth(object):
    def __init__(self):
        self.use_groups = True
        if hasattr(settings, 'ADAL_USE_GROUPS') and isinstance(settings.ADAL_USE_GROUPS, bool):
            self.use_groups = settings.ADAL_USE_GROUPS

    def get_user(self, user_id):
        user_model = get_user_model()
        try:
            return user_model.objects.get(pk=user_id)
        except user_model.DoesNotExist:
            return None

    def authenticate(self, request, username=None, password=None):
        user_model = get_user_model()
        try:
            # try to retrieve user from database and update it
            usr = user_model.objects.get(username=username)
            if AuthToken.objects.get(username=username, token=password):

                # try to get groups information
                if 'graph_groups' in request.session:
                    # if we want to use ADAL group membership:
                    if self.use_groups:
                        logger.info("AUDIT LOGIN FOR: %s AT %s USING ADAL GROUPS" % (username, datetime.now()))
                        # check for groups membership
                        # first cleanup
                        alter_superuser_membership = False
                        if hasattr(settings, 'ADAL_SUPERUSER_GROUPS') and isinstance(settings.ADAL_SUPERUSER_GROUPS,
                                                                                     list) \
                                and len(settings.ADAL_SUPERUSER_GROUPS) > 0:
                            usr.is_superuser = False
                            alter_superuser_membership = True

                        alter_staff_membership = False
                        if hasattr(settings, 'ADAL_STAFF_GROUPS') and isinstance(settings.ADAL_STAFF_GROUPS, list) \
                                and len(settings.ADAL_STAFF_GROUPS) > 0:
                            usr.is_staff = False
                            alter_staff_membership = True

                        usr.save()
                        logger.info(
                            "AUDIT LOGIN FOR: %s AT %s CLEANING OLD GROUP MEMBERSHIP" % (username, datetime.now()))
                        if hasattr(settings, 'ADAL_IGNORED_LOCAL_GROUPS'):
                            grps = Group.objects.exclude(name__in=settings.ADAL_IGNORED_LOCAL_GROUPS)
                        else:
                            grps = Group.objects.all()
                        for grp in grps:
                            grp.user_set.remove(usr)
                            grp.save()

                        # then re-fill
                        if 'value' in request.session['graph_groups']:
                            for group in request.session['graph_groups']['value']:
                                if 'id' in group:
                                    logger.info("AUDIT LOGIN FOR: %s AT %s DETECTED IN GROUP %s" %
                                                (username, datetime.now(), group['displayName']))
                                    # special super user group
                                    if alter_superuser_membership:
                                        if group['id'] in settings.ADAL_SUPERUSER_GROUPS:
                                            usr.is_superuser = True
                                            logger.info("AUDIT LOGIN FOR: %s AT %s GRANTING ADMIN RIGHTS" %
                                                        (username, datetime.now()))
                                        else:
                                            logger.info("AUDIT LOGIN FOR: %s AT %s DENY ADMIN RIGHTS" %
                                                        (username, datetime.now()))
                                    # special staff group
                                    if alter_staff_membership:
                                        if group['id'] in settings.ADAL_STAFF_GROUPS:
                                            usr.is_staff = True
                                            logger.info("AUDIT LOGIN FOR: %s AT %s GRANTING STAFF RIGHTS" %
                                                        (username, datetime.now()))
                                        else:
                                            logger.info("AUDIT LOGIN FOR: %s AT %s DENY STAFF RIGHTS" %
                                                        (username, datetime.now()))
                                    # other groups membership
                                    for grp in settings.ADAL_GROUPS_MAP.keys():
                                        if group['id'] == settings.ADAL_GROUPS_MAP[grp]:
                                            try:
                                                logger.info(grp)
                                                usr.groups.add(Group.objects.get(name=grp))
                                                logger.info("AUDIT LOGIN FOR: %s AT %s ADDING GROUP %s MEMBERSHIP" %
                                                            (username, datetime.now(), grp))
                                            except ObjectDoesNotExist:
                                                pass
                        usr.save()

                    # if set, apply min group membership
                    logger.info("AUDIT LOGIN FOR: %s AT %s BEFORE MIN GROUP MEMBERSHIP" %
                                (username, datetime.now()))
                    if hasattr(settings, 'ADAL_MIN_GROUPS'):
                        for grp in settings.ADAL_MIN_GROUPS:
                            logger.info("AUDIT LOGIN FOR: %s AT %s MIN GROUP MEMBERSHIP: %s" %
                                        (username, datetime.now(), grp))
                            try:
                                usr.groups.add(Group.objects.get(name=grp))
                                logger.info("AUDIT LOGIN FOR: %s AT %s ADDING GROUP %s MIN MEMBERSHIP" %
                                            (username, datetime.now(), grp))
                            except ObjectDoesNotExist:
                                pass

                return usr
        except user_model.DoesNotExist:
            # user does not exist in database already, create it
            return None
        except AuthToken.DoesNotExist:
            return None
