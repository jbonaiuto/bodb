import autocomplete_light
from registration.models import User

autocomplete_light.register(User,
    search_fields=['^first_name', '^last_name', '^username'],
    autocomplete_js_attributes={'placeholder': 'add another user',},
)
