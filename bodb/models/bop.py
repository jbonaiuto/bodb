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
        else:
            try:
                existing_bop=BOP.objects.get(id=self.id)
            except (BOP.DoesNotExist, BOP.MultipleObjectsReturned), err:
                existing_bop=None
            if existing_bop is not None:
                made_public=not existing_bop.public and self.public
                made_not_draft=existing_bop.draft and not int(self.draft)
                if made_public or made_not_draft:
                    notify=True

        super(BOP, self).save()

        if notify:
            # send notifications to subscribed users
            sendNotifications(self, 'BOP')

    @staticmethod
    def get_child_bops(bop, user):
        return bop.get_children().filter(Document.get_security_q(user)).distinct().select_related('collator').order_by('title')

    @staticmethod
    def get_literature_bops(literature, user):
        return BOP.objects.filter(Q(Q(literature=literature) & Document.get_security_q(user))).distinct().select_related('collator').order_by('title')

    @staticmethod
    def get_tagged_bops(name, user):
        return BOP.objects.filter(Q(tags__name__iexact=name) & Document.get_security_q(user)).distinct().select_related('collator').order_by('title')

    @staticmethod
    def get_bop_list(bops, workspace_bops, fav_docs, subscriptions):
        bop_list=[]
        for bop in bops:
            selected=bop.id in workspace_bops
            is_favorite=bop.id in fav_docs
            subscribed_to_user=(bop.collator.id,'BOP') in subscriptions
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
                                'relevance_narrative': rrbop.relevance_narrative})
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

    def bop_title(self):
        return self.bop.__unicode__()

    @staticmethod
    def get_related_bop_list(rbops, workspace_bops, fav_docs, subscriptions):
        related_bop_list=[]
        for rbop in rbops:
            selected=rbop.bop.id in workspace_bops
            is_favorite=rbop.bop.id in fav_docs
            subscribed_to_user=(rbop.bop.collator.id, 'BOP') in subscriptions
            related_bop_list.append([selected,is_favorite,subscribed_to_user,rbop])
        return related_bop_list

    @staticmethod
    def get_reverse_related_bop_list(rrbops, workspace_bops, fav_docs, subscriptions):
        reverse_related_bop_list=[]
        for rrbop in rrbops:
            selected=rrbop.document.id in workspace_bops
            is_favorite=rrbop.document.id in fav_docs
            subscribed_to_user=(rrbop.document.collator.id, 'BOP') in subscriptions
            reverse_related_bop_list.append([selected,is_favorite,subscribed_to_user,rrbop])
        return reverse_related_bop_list

    @staticmethod
    def get_related_bops(document, user):
        related_bop_list=[]
        rbops=list(RelatedBOP.objects.filter(Q(Q(document=document) &
                                           Document.get_security_q(user, field='bop'))).distinct().select_related('bop__collator'))
        for rbop in rbops:
            rbop.reverse=False
            related_bop_list.append(rbop)

        rrbops=RelatedBOP.get_reverse_related_bops(document, user)
        for rrbop in rrbops:
            rbop=RelatedBOP(id=rrbop.id, bop=BOP.objects.get(id=rrbop.document.id), document=rrbop.bop,
                relationship=rrbop.relationship, relevance_narrative=rrbop.relevance_narrative)
            rbop.reverse=True
            related_bop_list.append(rbop)
        related_bop_list.sort(key=RelatedBOP.bop_title)
        return related_bop_list

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
            rbop=RelatedBOP(id=-1, bop=BOP.objects.select_related('collator').get(id=related_region.document.id),
                relevance_narrative=related_region.relationship)
            rbop.reverse=True
            related_bops.append(rbop)
        return related_bops

    @staticmethod
    def get_sed_related_bops(sed, user):
        related_bops=[]
        bseds=BuildSED.objects.filter(Document.get_security_q(user, field='document') & Q(sed=sed)).distinct().select_related('document')
        for bsed in bseds:
            try:
                bop=BOP.objects.get(id=bsed.document.id)
            except (BOP.DoesNotExist, BOP.MultipleObjectsReturned), err:
                bop=None
            if bop is not None:
                rbop=RelatedBOP(id=-1, document=sed, bop=bop, relevance_narrative='%s - %s' % (bsed.relationship,
                                                                                               bsed.relevance_narrative))
                rbop.reverse=True
                related_bops.append(rbop)

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
