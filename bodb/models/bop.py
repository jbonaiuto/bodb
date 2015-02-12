from django.core.urlresolvers import reverse
from django.db import models
from django.db.models import Q
from bodb.models import RelatedBrainRegion, BuildSED
from bodb.models.messaging import sendNotifications, UserSubscription
from bodb.models.document import Document, stop_words
from mptt.fields import TreeForeignKey
from mptt.models import MPTTModel

class BOP(MPTTModel,Document):
    """
    A Brain Operating Principle (BOP): inherits from Document
    """
    # parent BOP
    parent = TreeForeignKey('self', null=True, blank=True, related_name='children')
    # related literature entries
    literature = models.ManyToManyField('Literature')

    def get_absolute_url(self):
        return reverse('bop_view', kwargs={'pk': self.pk})

    class Meta:
        app_label='bodb'
        permissions= (
            ('save_bop', 'Can save the BOP'),
            ('public_bop', 'Can make the BOP public'),
            )

    def save(self, force_insert=False, force_update=False):
        notify=False
        # creating a new object
        if self.id is None:
            notify=True
        elif BOP.objects.filter(id=self.id).count():
            made_public=not BOP.objects.get(id=self.id).public and self.public
            made_not_draft=BOP.objects.get(id=self.id).draft and not int(self.draft)
            if made_public or made_not_draft:
                notify=True

        super(BOP, self).save()

        if notify:
            # send notifications to subscribed users
            sendNotifications(self, 'BOP')

    @staticmethod
    def get_child_bops(bop, user):
        return bop.get_children().filter(Document.get_security_q(user)).distinct().select_related('collator')

    @staticmethod
    def get_literature_bops(literature, user):
        return BOP.objects.filter(Q(Q(literature=literature) & Document.get_security_q(user))).distinct().select_related('collator')

    @staticmethod
    def get_tagged_bops(name, user):
        return BOP.objects.filter(Q(tags__name__iexact=name) & Document.get_security_q(user)).distinct().select_related('collator')

    @staticmethod
    def get_bop_list(bops, user):
        profile=None
        active_workspace=None
        if user.is_authenticated() and not user.is_anonymous():
            profile=user.get_profile()
            active_workspace=profile.active_workspace
        bop_list=[]
        for bop in bops:
            selected=active_workspace is not None and active_workspace.related_bops.filter(id=bop.id).exists()
            is_favorite=profile is not None and profile.favorites.filter(id=bop.id).exists()
            subscribed_to_user=profile is not None and UserSubscription.objects.filter(subscribed_to_user=bop.collator,
                user=user, model_type='BOP').exists()
            bop_list.append([selected,is_favorite,subscribed_to_user,bop])
        return bop_list

    @staticmethod
    def get_bop_relationships(bops, user):
        map=[]
        for bop in bops:
            reverse_related_bops=RelatedBOP.get_reverse_related_bops(bop, user)
            for rrbop in reverse_related_bops:
                related_bop=BOP.objects.get(id=rrbop.document.id)
                if related_bop in bops:
                    map.append({'from':related_bop.id, 'to': bop.id, 'relationship': rrbop.relationship ,
                                'relevance_narrative': rrbop.relevance_narrative.replace('\'','\\\'').replace('\n',' ').replace('\r',' ')})
            child_bops=BOP.get_child_bops(bop, user)
            for child_bop in child_bops:
                if child_bop in bops:
                    map.append({'from':bop.id, 'to': child_bop.id, 'relationship': 'Parent-of',
                                'relevance_narrative': ''})
        return map


# The relationship between a Document and a BOP
class RelatedBOP(models.Model):
    # the SED is either scene setting or supports some aspect of the model design
    RELATIONSHIP_CHOICES = (
        ('involves', 'involves'),
        ('synonym', 'synonym'),
    )
    document = models.ForeignKey('Document', related_name='related_bop_document')
    bop = models.ForeignKey('BOP', related_name='related_bop', null=True)
    # the relationship between two BOPs
    relationship = models.CharField(max_length=30, choices=RELATIONSHIP_CHOICES, blank=True, null=True)
    relevance_narrative = models.TextField(blank=True)
    class Meta:
        app_label='bodb'
        ordering=['bop__title']

    @staticmethod
    def get_related_bop_list(rbops, user):
        profile=None
        active_workspace=None
        if user.is_authenticated() and not user.is_anonymous():
            profile=user.get_profile()
            active_workspace=profile.active_workspace
        related_bop_list=[]
        for rbop in rbops:
            selected=active_workspace is not None and active_workspace.related_bops.filter(id=rbop.bop.id).exists()
            is_favorite=profile is not None and profile.favorites.filter(id=rbop.bop.id).exists()
            subscribed_to_user=profile is not None and UserSubscription.objects.filter(subscribed_to_user=rbop.bop.collator,
                user=user, model_type='BOP').exists()
            related_bop_list.append([selected,is_favorite,subscribed_to_user,rbop])
        return related_bop_list

    @staticmethod
    def get_reverse_related_bop_list(rrbops, user):
        profile=None
        active_workspace=None
        if user.is_authenticated() and not user.is_anonymous():
            profile=user.get_profile()
            active_workspace=profile.active_workspace
        reverse_related_bop_list=[]
        for rrbop in rrbops:
            selected=active_workspace is not None and \
                     active_workspace.related_bops.filter(id=rrbop.document.id).exists()
            is_favorite=profile is not None and profile.favorites.filter(id=rrbop.document.id).exists()
            subscribed_to_user=profile is not None and \
                               UserSubscription.objects.filter(subscribed_to_user=rrbop.document.collator, user=user,
                                   model_type='BOP').exists()
            reverse_related_bop_list.append([selected,is_favorite,subscribed_to_user,rrbop])
        return reverse_related_bop_list

    @staticmethod
    def get_related_bops(document, user):
        return RelatedBOP.objects.filter(Q(Q(document=document) &
                                           Document.get_security_q(user, field='bop'))).distinct().select_related('bop__collator')

    @staticmethod
    def get_reverse_related_bops(bop, user):
        return RelatedBOP.objects.filter(Q(Q(bop=bop) & Q(document__bop__isnull=False) &
                                           Document.get_security_q(user, field='document'))).distinct().select_related('bop__collator')

    @staticmethod
    def get_brain_region_related_bops(brain_region, user):
        related_regions=RelatedBrainRegion.objects.filter(Q(Q(document__bop__isnull=False) &
                                                            Q(brain_region=brain_region) &
                                                            Document.get_security_q(user, field='document'))).distinct().select_related('document')
        related_bops=[]
        for related_region in related_regions:
            related_bops.append(RelatedBOP(bop=BOP.objects.get(id=related_region.document.id),
                    relevance_narrative=related_region.relationship))
        return related_bops

    @staticmethod
    def get_sed_related_bops(sed, user):
        related_bops=[]
        bseds=BuildSED.objects.filter(Document.get_security_q(user, field='document') & Q(sed=sed)).distinct().select_related('document')
        for bsed in bseds:
            if BOP.objects.filter(id=bsed.document.id).count():
                bop=BOP.objects.get(id=bsed.document.id)
                related_bops.append(RelatedBOP(document=sed, bop=bop, relevance_narrative='%s - %s' %
                                                                                          (bsed.relationship,
                                                                                           bsed.relevance_narrative)))

        return related_bops


def compareRelatedBops(a, b):
    return cmp(a.bop.title.lower(), b.bop.title.lower())


def find_similar_bops(user, title, brief_description):
    similar=[]
    other_bops=BOP.objects.filter(Document.get_security_q(user)).distinct()
    for bop in other_bops:
        total_match=0
        for title_word in title.split(' '):
            if not title_word in stop_words and bop.title.find(title_word)>=0:
                total_match+=1
        for desc_word in brief_description.split(' '):
            if not desc_word in stop_words and bop.brief_description.find(desc_word)>=0:
                total_match+=1
        if total_match>0:
            similar.append((bop,total_match))
    similar.sort(key=lambda tup: tup[1],reverse=True)
    return similar
