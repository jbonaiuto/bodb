from bodb.models.messaging import Message
from django.core.cache import cache

# get the number of unread messages for the current user
def unread_messages(request):
    message_count=0
    if request.user.is_authenticated() and not request.user.is_anonymous():
        user_message_count=cache.get('%d.message_count' % request.user.id)
        if not user_message_count:
            messages=Message.objects.filter(recipient=request.user, read=False)
            user_message_count=messages.count()
            cache.set('%d.message_count' % request.user.id, user_message_count)
        message_count=user_message_count
    return {'message_count': message_count}
