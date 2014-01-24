from django.contrib.auth.models import User
from django.db import models
from django.core.mail import EmailMessage
from django.conf import settings

# A message passed between users
from django.db.models.query_utils import Q

class Message(models.Model):
    # user who the message is for
    recipient = models.ForeignKey(User, related_name='message_recipient_set')
    # user who sent the message
    sender = models.ForeignKey(User, related_name='message_sender_set', null=True)
    subject = models.CharField(max_length=200)
    text = models.TextField()
    # whether or not the recipient has read the message
    read = models.BooleanField(default=False)
    # when the message was sent
    sent = models.DateTimeField(auto_now_add=True,blank=True)
    # when listing instances of this class, order by sent date in descending order
    class Meta:
        app_label='legacy_bodb'
        ordering=['-sent']

# A user's subscription to be notified of new entries
class Subscription(models.Model):
    MODEL_TYPE_CHOICES = (
        ('All', 'All'),
        ('Model', 'Model'),
        ('BOP', 'BOP'),
        ('SED', 'SED'),
        ('Prediction', 'Prediction'),
        ('SSR', 'SSR'),
    )
    # subscribed user
    user = models.ForeignKey(User)
    # type of entry they are interested in
    model_type = models.CharField(max_length=100, choices=MODEL_TYPE_CHOICES)
    # keywords in the entry title, description, narrative, or tags. If blank, notifications
    # will be sent for all new entries of model_type
    keywords = models.CharField(max_length=500)
    class Meta:
        app_label='legacy_bodb'

class UserSubscription(Subscription):
    subscribed_to_user = models.ForeignKey(User, related_name='subscribed_to')
    class Meta:
        app_label='legacy_bodb'

# send notifications to users give model_type, the new entry, and subscriptions for
# this type
def sendNotifications(document, model_type):
    type_q=Q(Q(model_type=model_type) | Q(model_type='All'))
    full_q=type_q
    if not document.public:
        print('document is not public')
        if not int(document.draft):
            print('document is not a draft')
            full_q=Q(type_q & Q(Q(user__is_superuser=1) | Q(user__groups__in=list(document.collator.groups.all()))))
        else:
            full_q=Q(type_q & Q(user__is_superuser=1))

    subscriptions=Subscription.objects.filter(full_q).exclude(user=document.collator)
    # iterate through subscriptions
    for subscription in subscriptions:
        # send notification
        if subscription_matches(subscription, document):
            sendNotification(subscription, document)
    user_subscriptions=UserSubscription.objects.filter(subscribed_to_user=document.collator).exclude(user=document.collator)
    for subscription in user_subscriptions:
        if subscription_matches(subscription, document):
            sendNotification(subscription, document)

def subscription_matches(subscription, document):
    # if they specified any keywords
    if subscription.keywords and len(subscription.keywords):
        # iterate through keywords
        words=subscription.keywords.split()
        for word in words:

            # if the word is in the document title, description, narrative,
            # or tags
            if ((word.lower() in document.title.lower()) or
                (word.lower() in document.brief_description.lower()) or
                (word.lower() in document.narrative.lower()) or
                (word.lower() in document.tags.lower())):
                return True

    # send a notification for all new entries if no keywords specified
    else:
        return True
    return False

# send a notification given a subscription and a new document
def sendNotification(subscription, document):
    # message subject
    subject='New '+subscription.model_type+' notification'
    # message text
    text='A new '+subscription.model_type+' has been added to BODB.<br>'
    if subscription.keywords and len(subscription.keywords):
        text='A new '+subscription.model_type+' has been added to BODB with one or more of the following keywords: '+subscription.keywords+'.<br>'
    text+='<b>Collator</b>: ' + document.collator.username+'<br>'
    text+='<b>Name</b>: <a href="'+settings.URL_BASE+'/bodb/'+subscription.model_type.lower()+'/'+str(document.id)+'/">'+document.title+'</a><br>'
    text+='<b>Description</b>: '+document.brief_description

    # send internal message
    notification_type=subscription.user.get_profile().notification_preference
    if notification_type=='message' or notification_type=='both':
        message=Message(recipient=subscription.user, subject=subject, read=False)
        message.text=text
        message.save()

    # send email message
    if notification_type=='email' or notification_type=='both':
        msg = EmailMessage(subject, text, 'uscbrainproject@gmail.com', [subscription.user.email])
        msg.content_subtype = "html"  # Main content is now text/html
        msg.send(fail_silently=True)

