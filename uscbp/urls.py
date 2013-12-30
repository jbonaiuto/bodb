from django.conf.urls import patterns, include, url
from bodb.forms import BodbRegistrationForm
from bodb.views.admin import UpdateUserProfileView, BodbRegistrationView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = patterns('',
    (r'^bodb/', include('bodb.urls')),
    (r'^accounts/logout/$', 'bodb.views.admin.logout_view', ),
    (r'^accounts/register/$', BodbRegistrationView.as_view(form_class=BodbRegistrationForm), {}, 'registration_register'),
    (r'^accounts/', include('registration.backends.default.urls')),
    (r'^accounts/username_available/$', 'bodb.views.admin.username_available', ),
    (r'^accounts/profile/$', UpdateUserProfileView.as_view(), {}, 'create_user_profile'),
    url(r'^comments/', include('django.contrib.comments.urls')),
)+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
