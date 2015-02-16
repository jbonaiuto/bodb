from django.core.urlresolvers import reverse
from django.db import models
from django.db.models import Q
from bodb.models import Document, sendNotifications, UserSubscription

class SSR(Document):
    """
    Summary of Simulation Data (SSR) - inherits from Document
    """
    TYPE_CHOICES = (
        ('', ''),
        ('generic', 'generic'),
        )
    type = models.CharField(max_length=30, choices=TYPE_CHOICES)

    class Meta:
        app_label='bodb'
        permissions= (
            ('save_ssr', 'Can save the SSR'),
            ('public_ssr', 'Can make the SSR public'),
            )

    def get_absolute_url(self):
        return reverse('ssr_view', kwargs={'pk': self.pk})

    def save(self, force_insert=False, force_update=False):
        notify=False
        # creating a new object
        if self.id is None:
            notify=True
        else:
            try:
                existing_ssr=SSR.objects.get(id=self.id)
            except (SSR.DoesNotExist, SSR.MultipleObjectsReturned), err:
                existing_ssr=None
            if existing_ssr is not None:
                made_public=not existing_ssr.public and self.public
                made_not_draft=existing_ssr.draft and not int(self.draft)
                if made_public or made_not_draft:
                    notify=True

        super(SSR, self).save()

        if notify:
            # send notifications to subscribed users
            sendNotifications(self, 'SSR')

    @staticmethod
    def get_ssr_list(ssrs, profile, active_workspace):
        ssr_list=[]
        for ssr in ssrs:
            selected=active_workspace is not None and active_workspace.related_ssrs.filter(id=ssr.id).exists()
            is_favorite=profile is not None and profile.favorites.filter(id=ssr.id).exists()
            subscribed_to_user=profile is not None and UserSubscription.objects.filter(subscribed_to_user=ssr.collator,
                user=profile.user, model_type='SSR').exists()
            ssr_list.append([selected,is_favorite,subscribed_to_user,ssr])
        return ssr_list

    @staticmethod
    def get_tagged_ssrs(name, user):
        return SSR.objects.filter(Q(tags__name__iexact=name) & Document.get_security_q(user)).distinct().select_related('collator')


class Prediction(Document):
    # The model the prediction is linked to
    model=models.ForeignKey('Model', related_name = 'prediction')
    # the SSR
    ssr=models.ForeignKey('SSR', null=True)

    class Meta:
        app_label='bodb'
        permissions= (
            ('save_prediction', 'Can save the Prediction'),
            ('public_prediction', 'Can make the Prediction public'),
            )

    def get_absolute_url(self):
        return reverse('prediction_view', kwargs={'pk': self.pk})

    @staticmethod
    def get_prediction_list(predictions, profile, active_workspace):
        prediction_list=[]
        for prediction in predictions:
            if prediction.ssr is None:
                ssr_selected=False
                ssr_is_favorite=False
                ssr_subscribed_to_user=False
            else:
                ssr_selected=active_workspace is not None and active_workspace.related_ssrs.filter(id=prediction.ssr.id).exists()
                ssr_is_favorite=profile is not None and profile.favorites.filter(id=prediction.ssr.id).exists()
                ssr_subscribed_to_user=profile is not None and UserSubscription.objects.filter(subscribed_to_user=prediction.ssr.collator,
                    user=profile.user, model_type='SSR').exists()
            prediction_list.append([ssr_selected,ssr_is_favorite,ssr_subscribed_to_user,prediction])
        return prediction_list

    @staticmethod
    def get_predictions(model, user):
        return Prediction.objects.filter(Q(Q(model=model) & Document.get_security_q(user) &
                                           Document.get_security_q(user, field='ssr'))).distinct().select_related('collator','ssr__collator')

    @staticmethod
    def get_tagged_predictions(name, user):
        return Prediction.objects.filter(Q(tags__name__iexact=name) & Document.get_security_q(user)).distinct().select_related('collator','ssr__collator')

    def save(self, force_insert=False, force_update=False):
        notify=False
        # creating a new object
        if self.id is None:
            notify=True
        else:
            try:
                existing_prediction=Prediction.objects.get(id=self.id)
            except (Prediction.DoesNotExist, Prediction.MultipleObjectsReturned), err:
                existing_prediction=None
            if existing_prediction is not None:
                made_public=not existing_prediction.public and self.public
                made_not_draft=existing_prediction.draft and not int(self.draft)
                if made_public or made_not_draft:
                    notify=True

        super(Prediction, self).save()

        if notify:
            # send notifications to subscribed users
            sendNotifications(self, 'Prediction')

