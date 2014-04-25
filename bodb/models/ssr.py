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
        elif SSR.objects.filter(id=self.id).count():
            made_public=not SSR.objects.get(id=self.id).public and self.public
            made_not_draft=SSR.objects.get(id=self.id).draft and not int(self.draft)
            if made_public or made_not_draft:
                notify=True

        super(SSR, self).save()

        if notify:
            # send notifications to subscribed users
            sendNotifications(self, 'SSR')

    @staticmethod
    def get_ssr_list(ssrs, user):
        profile=None
        active_workspace=None
        if user.is_authenticated() and not user.is_anonymous():
            profile=user.get_profile()
            active_workspace=profile.active_workspace
        ssr_list=[]
        for ssr in ssrs:
            selected=active_workspace is not None and active_workspace.related_ssrs.filter(id=ssr.id).count()>0
            is_favorite=profile is not None and profile.favorites.filter(id=ssr.id).count()>0
            subscribed_to_user=profile is not None and UserSubscription.objects.filter(subscribed_to_user=ssr.collator,
                user=user, model_type='SSR').count()>0
            ssr_list.append([selected,is_favorite,subscribed_to_user,ssr])
        return ssr_list

    @staticmethod
    def get_tagged_ssrs(name, user):
        return SSR.objects.filter(Q(tags__name__icontains=name) & Document.get_security_q(user)).distinct()


class Prediction(Document):
    # The model the prediction is linked to
    model=models.ForeignKey('Model', related_name = 'prediction')

    class Meta:
        app_label='bodb'
        permissions= (
            ('save_prediction', 'Can save the Prediction'),
            ('public_prediction', 'Can make the Prediction public'),
            )

    def get_absolute_url(self):
        return reverse('prediction_view', kwargs={'pk': self.pk})

    def get_ssr(self):
        if PredictionSSR.objects.filter(prediction=self).count()>0:
            return PredictionSSR.objects.filter(prediction=self)[0].ssr
        return None

    @staticmethod
    def get_prediction_list(predictions, user):
        profile=None
        active_workspace=None
        if user.is_authenticated() and not user.is_anonymous():
            profile=user.get_profile()
            active_workspace=profile.active_workspace
        prediction_list=[]
        for prediction in predictions:
            if prediction.get_ssr() is None:
                ssr_selected=False
                ssr_is_favorite=False
                ssr_subscribed_to_user=False
            else:
                ssr_selected=active_workspace is not None and active_workspace.related_ssrs.filter(id=prediction.get_ssr().id).count()>0
                ssr_is_favorite=profile is not None and profile.favorites.filter(id=prediction.get_ssr().id).count()>0
                ssr_subscribed_to_user=profile is not None and UserSubscription.objects.filter(subscribed_to_user=prediction.get_ssr().collator,
                    user=user, model_type='SSR').count()>0
            prediction_list.append([ssr_selected,ssr_is_favorite,ssr_subscribed_to_user,prediction])
        return prediction_list

    @staticmethod
    def get_predictions(model, user):
        return Prediction.objects.filter(Q(Q(model=model) & Document.get_security_q(user) &
                                           Document.get_security_q(user, field='predictionssr__ssr'))).distinct()

    @staticmethod
    def get_ssrs(prediction, user):
        return SSR.objects.filter(Q(Q(predictionssr__prediction=prediction) &
                                    Document.get_security_q(user, field='predictionssr__ssr'))).distinct()

    @staticmethod
    def get_tagged_predictions(name, user):
        return Prediction.objects.filter(Q(tags__name__icontains=name) & Document.get_security_q(user)).distinct()

    def save(self, force_insert=False, force_update=False):
        notify=False
        # creating a new object
        if self.id is None:
            notify=True
        elif Prediction.objects.filter(id=self.id).count():
            made_public=not Prediction.objects.get(id=self.id).public and self.public
            made_not_draft=Prediction.objects.get(id=self.id).draft and not int(self.draft)
            if made_public or made_not_draft:
                notify=True

        super(Prediction, self).save()

        if notify:
            # send notifications to subscribed users
            sendNotifications(self, 'Prediction')


class PredictionSSR(models.Model):
    prediction=models.ForeignKey('Prediction')
    ssr=models.ForeignKey('SSR', null=True)

    class Meta:
        app_label='bodb'