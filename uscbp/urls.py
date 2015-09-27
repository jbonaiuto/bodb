from django.conf.urls import patterns, include, url
from bodb.forms.admin import BodbRegistrationForm
from bodb.views.admin import UpdateUserProfileView, BodbRegistrationView
from django.conf import settings
from django.conf.urls.static import static
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
    (r'^accounts/$', include('registration.backends.default.urls')),
    (r'^accounts/username_available/$', 'bodb.views.admin.username_available', ),
    (r'^accounts/profile/$', UpdateUserProfileView.as_view(), {}, 'create_user_profile'),
    url(r'^comments/', include('django.contrib.comments.urls')),
)+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
