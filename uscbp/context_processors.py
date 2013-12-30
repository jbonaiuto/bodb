from bodb.models.messaging import Message

# get the number of unread messages for the current user
def unread_messages(request):
    message_count=0
    if request.user.is_authenticated() and not request.user.is_anonymous():
        messages=Message.objects.filter(recipient=request.user, read=False)
        message_count=messages.count()
    return {'message_count': message_count}
