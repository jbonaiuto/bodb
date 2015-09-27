from django.conf.urls import patterns, include, url
from django.views.generic import TemplateView
from bodb.forms.admin import BodbRegistrationForm
from bodb.views.admin import UpdateUserProfileView, BodbRegistrationView
from django.conf import settings
from django.conf.urls.static import static
from registration.backends.default.views import ActivationView
from registration.views import gRecaptchaVerify

if getattr(settings, 'ASKBOT_MULTILINGUAL', False) == True:
    from django.conf.urls.i18n import i18n_patterns
    urlpatterns = i18n_patterns('',
        (r'%s' % settings.ASKBOT_URL, include('askbot.urls'))
    )
else:
    urlpatterns = patterns('',
        (r'%s' % settings.ASKBOT_URL, include('askbot.urls'))
    )

urlpatterns += patterns('',
    (r'^bodb/', include('bodb.urls')),
    (r'^accounts/logout/$', 'bodb.views.admin.logout_view', ),
    (r'^accounts/register/$', BodbRegistrationView.as_view(form_class=BodbRegistrationForm), {}, 'registration_register'),
    (r'^accounts/verify/$', gRecaptchaVerify.as_view(), {}, 'grecaptcha_verify'),
    url(r'^activate/complete/$',
        TemplateView.as_view(template_name='registration/activation_complete.html'),
        name='registration_activation_complete'),
    # Activation keys get matched by \w+ instead of the more specific
    # [a-fA-F0-9]{40} because a bad activation key should still get to the view;
    # that way it can return a sensible "invalid key" message instead of a
    # confusing 404.
    url(r'^activate/(?P<activation_key>\w+)/$',
        ActivationView.as_view(),
        name='registration_activate'),
    (r'^accounts/', include('registration.backends.default.urls')),
    (r'^accounts/username_available/$', 'bodb.views.admin.username_available', ),
    (r'^accounts/profile/$', UpdateUserProfileView.as_view(), {}, 'create_user_profile'),
    url(r'^comments/', include('django.contrib.comments.urls')),
)+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
