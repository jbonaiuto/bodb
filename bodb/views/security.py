from django.utils.http import urlquote
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import redirect, render_to_response
from django.template import RequestContext, TemplateDoesNotExist
from django.views.generic import DetailView
from django.views.generic.edit import UpdateView, CreateView
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.core.exceptions import ImproperlyConfigured
from django.core.exceptions import PermissionDenied
from guardian.conf import settings as guardian_settings
from collections import Iterable
from django.conf import settings


class AdminUpdateView(UpdateView):
    def get(self, request, *args, **kwargs):
        if self.request.user.is_superuser:
            return super(AdminUpdateView, self).get(request, *args, **kwargs)
        else:
            return redirect('/bodb/')

    def post(self, request, *args, **kwargs):
        if self.request.user.is_superuser:
            return super(AdminUpdateView, self).post(request, *args, **kwargs)
        else:
            form_class = self.get_form_class()
            form = self.get_form(form_class)
            return self.form_invalid(form)

class AdminCreateView(CreateView):
    def get(self, request, *args, **kwargs):
        if self.request.user.is_superuser:
            return super(AdminCreateView, self).get(request, *args, **kwargs)
        else:
            return redirect('/bodb/')

    def post(self, request, *args, **kwargs):
        if self.request.user.is_superuser:
            return super(AdminCreateView, self).post(request, *args, **kwargs)
        else:
            return redirect('/bodb/')

class AdminDetailView(DetailView):
    def get(self, request, *args, **kwargs):
        if self.request.user.is_superuser:
            return super(AdminDetailView, self).get(request, *args, **kwargs)
        else:
            return redirect('/bodb/')

class ObjectRolePermissionRequiredMixin(object):
    """
    A view mixin that verifies if the current logged in user has the specified
    permission by wrapping the ``request.user.has_perm(..)`` method.

    If a `get_object()` method is defined either manually or by including
    another mixin (for example ``SingleObjectMixin``) or ``self.object`` is
    defiend then the permission will be tested against that specific instance.

    .. note:
       Testing of a permission against a specific object instance requires an
       authentication backend that supports. Please see ``django-guardian`` to
       add object level permissions to your project.

    The mixin does the following:

        If the user isn't logged in, redirect to settings.LOGIN_URL, passing
        the current absolute path in the query string. Example:
        /accounts/login/?next=/polls/3/.

        If the `raise_exception` is set to True than rather than redirect to
        login page a `PermissionDenied` (403) is raised.

        If the user is logged in, and passes the permission check than the view
        is executed normally.

    **Example Usage**::

        class SecureView(PermissionRequiredMixin, View):
            ...
            permission_required = 'auth.change_user'
            ...

    **Class Settings**

    ``PermissionRequiredMixin.permission_required``

        *Default*: ``None``, must be set to either a string or list of strings
        in format: *<app_label>.<permission_codename>*.

    ``PermissionRequiredMixin.login_url``

        *Default*: ``settings.LOGIN_URL``

    ``PermissionRequiredMixin.redirect_field_name``

        *Default*: ``'next'``

    ``PermissionRequiredMixin.return_403``

        *Default*: ``False``. Returns 403 error page instead of redirecting
        user.

    ``PermissionRequiredMixin.raise_exception``

        *Default*: ``False``

        `permission_required` - the permission to check of form "<app_label>.<permission codename>"
                                i.e. 'polls.can_vote' for a permission on a model in the polls application.
    """
    ### default class view settings
    login_url = settings.LOGIN_URL
    permission_required = None
    redirect_field_name = REDIRECT_FIELD_NAME
    return_403 = False
    raise_exception = False

    def get_required_permissions(self, request=None):
        """
        Returns list of permissions in format *<app_label>.<codename>* that
        should be checked against *request.user* and *object*. By default, it
        returns list from ``permission_required`` attribute.

        :param request: Original request.
        """
        if isinstance(self.permission_required, basestring):
            perms = [self.permission_required]
        elif isinstance(self.permission_required, Iterable):
            perms = [p for p in self.permission_required]
        else:
            raise ImproperlyConfigured("'PermissionRequiredMixin' requires "
                                       "'permission_required' attribute to be set to "
                                       "'<app_label>.<permission codename>' but is set to '%s' instead"
                                       % self.permission_required)
        return perms

    def check_permissions(self, request):
        """
        Checks if *request.user* has all permissions returned by
        *get_required_permissions* method.

        :param request: Original request.
        """
        obj = (hasattr(self, 'get_object') and self.get_object()
               or getattr(self, 'object', None))


        forbidden = get_403_or_None(request,
            perms=self.get_required_permissions(request),
            obj=obj,
            login_url=self.login_url,
            redirect_field_name=self.redirect_field_name,
            return_403=self.return_403,
        )
        if forbidden:
            self.on_permission_check_fail(request, forbidden, obj=obj)
        if forbidden and self.raise_exception:
            raise PermissionDenied()
        return forbidden

    def on_permission_check_fail(self, request, response, obj=None):
        """
        Method called upon permission check fail. By default it does nothing and
        should be overridden, if needed.

        :param request: Original request
        :param response: 403 response returned by *check_permissions* method.
        :param obj: Object that was fetched from the view (using ``get_object``
          method or ``object`` attribute, in that order).
        """

    def dispatch(self, request, *args, **kwargs):
        self.request = request
        self.args = args
        self.kwargs = kwargs
        response = self.check_permissions(request)
        if response:
            return response
        return super(ObjectRolePermissionRequiredMixin, self).dispatch(request, *args,
            **kwargs)


def get_403_or_None(request, perms, obj, login_url=None,
                    redirect_field_name=None, return_403=False):
    login_url = login_url or settings.LOGIN_URL
    redirect_field_name = redirect_field_name or REDIRECT_FIELD_NAME

    # Handles both original and with object provided permission check
    # as ``obj`` defaults to None

    has_permissions= all(obj.check_perm(request.user,perm) for perm in perms)

    if not has_permissions:
        if return_403:
            if guardian_settings.RENDER_403:
                try:
                    response = render_to_response(
                        guardian_settings.TEMPLATE_403, {},
                        RequestContext(request))
                    response.status_code = 403
                    return response
                except TemplateDoesNotExist as e:
                    if settings.DEBUG:
                        raise e
            elif guardian_settings.RAISE_403:
                raise PermissionDenied
            return HttpResponseForbidden()
        else:
            path = urlquote(request.get_full_path())
            tup = login_url, redirect_field_name, path
            return HttpResponseRedirect("%s?%s=%s" % tup)
