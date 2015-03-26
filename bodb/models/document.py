from django.contrib.auth.models import User
from django.contrib.sites.models import get_current_site
from django.core.mail import EmailMessage
from django.db import models
from django.db.models import Q
from bodb.models import Message, BodbProfile, messageUser
from bodb.models.discussion import Forum
from bodb.signals import document_changed
from taggit.managers import TaggableManager
import os
from uscbp import settings

stop_words=['a', 'about', 'again', 'all', 'almost', 'also', 'although', 'always', 'among', 'an', 'and', 'another',
            'any', 'are', 'as', 'at', 'be', 'because', 'been', 'before', 'being', 'between', 'both', 'but', 'by', 'can',
            'could', 'did', 'do', 'does', 'done', 'due', 'during', 'each', 'either', 'enough', 'especially', 'etc',
            'for', 'found', 'from', 'further', 'had', 'has', 'have', 'having', 'here', 'how', 'however', 'i', 'if',
            'in', 'into', 'is', 'it', 'its', 'itself', 'just', 'kg', 'km', 'made', 'mainly', 'make', 'may', 'mg',
            'might', 'ml', 'mm', 'most', 'mostly', 'must', 'nearly', 'neither', 'no', 'nor', 'obtained', 'of', 'often',
            'on', 'our', 'overall', 'perhaps', 'pmid', 'quite', 'rather', 'really', 'regarding', 'seem', 'seen',
            'several', 'should', 'show', 'showed', 'shown', 'shows', 'significantly', 'since', 'so', 'some', 'such',
            'than', 'that', 'the', 'their', 'theirs', 'them', 'then', 'there', 'therefore', 'these', 'they', 'this',
            'those', 'through', 'thus', 'to', 'upon', 'use', 'used', 'using', 'various', 'very', 'was', 'we', 'were',
            'what', 'when', 'which', 'while', 'with', 'within', 'without', 'would']
    
class Document(models.Model):
    """
    Document - base class for SED, SSR, Model, and BOP
    """
    # user who added the entry
    collator = models.ForeignKey(User,null=True)
    title = models.CharField(max_length=200)
    brief_description = models.TextField(blank=True)
    narrative = models.TextField(blank=True)
    # whether or not this entry is a draft
    draft = models.IntegerField(default=False)
    # whether or not this entry is public
    public = models.IntegerField(default=False)
    # date and time this entry was created
    creation_time = models.DateTimeField(auto_now_add=True,blank=True)
    #creation_time = models.DateTimeField(blank=True)
    # date and time this entry as last modified
    last_modified_time = models.DateTimeField(auto_now=True,blank=True)
    #last_modified_time = models.DateTimeField(blank=True)
    # user who last modified the entry
    last_modified_by = models.ForeignKey(User,null=True,blank=True,related_name='last_modified_by')
    # tags
    tags = TaggableManager()
    # forum
    forum=models.ForeignKey('Forum',null=True,blank=True)

    class Meta:
        app_label='bodb'
        # When listing multiple records order by title
        ordering=['title']
        permissions=(
            ('manage', 'Manage permissions'),
            ('edit', 'Edit permissions'),
            ('delete', 'Delete permissions'),
            ('view', 'View permissions')
        )

    # when printing instances of this class, print "title"
    def __unicode__(self):
        return u"%s" % self.title

    def get_collator_str(self):
        if self.collator.last_name:
            return '%s %s' % (self.collator.first_name, self.collator.last_name)
        else:
            return self.collator.username

    def get_modified_by_str(self):
        if self.last_modified_by.last_name:
            return '%s %s' % (self.last_modified_by.first_name, self.last_modified_by.last_name)
        else:
            return self.last_modified_by.username

    def get_created_str(self):
        return self.creation_time.strftime('%B %d, %Y')

    def get_modified_str(self):
        return self.last_modified_time.strftime('%B %d, %Y')

    def check_perm(self, user, perm):
        if perm=='view':
            if user.is_authenticated() and not user.is_anonymous():
                if user.is_superuser:
                    return True
                else:
                    if self.collator.id==user.id or self.public==1:
                        return True
                    elif self.draft==0:
                        for group in user.groups.all():
                            if self.collator.groups.filter(id=group.id).exists():
                                return True
            else:
                return self.public==1
            return False
        else:
            return user.is_authenticated() and (self.collator==user or user.is_superuser or
                                                user.has_perm(perm,Document.objects.get(id=self.id)))

    def isFavorite(self, profile):
        if profile is not None:
            return profile.favorites.filter(id=self.id).exists()
        return False

    def save(self, *args, **kwargs):

        # test if document already has a forum assigned to it
        if (not hasattr(self, 'forum')) or (self.forum is None):
            doc_forum=Forum()
            doc_forum.save(*args, **kwargs)
            self.forum=doc_forum

        # Save document
        super(Document, self).save(*args, **kwargs)

        document_changed.send(sender=self)

    def as_json(self):
        return {
            'id': self.id,
            'collator_id': self.collator.id,
            'collator': self.get_collator_str(),
            'title': self.title,
            'title_str': self.__unicode__(),
            'draft': self.draft,
            'brief_description': self.brief_description
        }

    @staticmethod
    def get_security_q(user, field=None):
        q=Q()
        if user.is_authenticated() and not user.is_anonymous():
            if not user.is_superuser:
                if field is None:
                    own_entry_q=Q(collator__id=user.id)
                    public_q=Q(public=1)
                    group_q=Q(Q(draft=0) & Q(collator__groups__in=list(user.groups.all())))
                else:
                    own_entry_q=Q(**{'%s__collator__id' % field:user.id})
                    public_q=Q(**{'%s__public' % field: 1})
                    group_q=Q(Q(**{'%s__draft' % field: 0}) & Q(**{'%s__collator__groups__in' % field:list(user.groups.all())}))
                q=own_entry_q | public_q | group_q
        else:
            if field is None:
                q=Q(public=1)
            else:
                q=Q(**{'%s__public' % field:1})
        return q
    
# class ThreadToDocument(models.Model):
#     """the "through" many-to-many relation between
#     threads and groups - to distinguish full and "what's published"
#     visibility of threads to various groups
#     """
#     SHOW_PUBLISHED_RESPONSES = 0
#     SHOW_ALL_RESPONSES = 1
#     VISIBILITY_CHOICES = (
#         (SHOW_PUBLISHED_RESPONSES, 'show only published responses'),
#         (SHOW_ALL_RESPONSES, 'show all responses')
#     )
#     thread = models.ForeignKey('askbot.Thread')
#     document = models.ForeignKey(Document)
#     visibility = models.SmallIntegerField(
#                         choices=VISIBILITY_CHOICES,
#                         default=SHOW_ALL_RESPONSES
#                     )
# 
#     class Meta:
#         unique_together = ('thread', 'document')
#         db_table = 'bodb_askbotthread_documents'
#         app_label = 'bodb'
    


class DocumentFigure(models.Model):
    document = models.ForeignKey(Document, related_name='figures')
    figure = models.ImageField(upload_to='figures')
    title = models.CharField(max_length=100)
    caption = models.TextField()
    order = models.IntegerField()
    class Meta:
        app_label='bodb'
        ordering=('order',)
        
    def get_absolute_url(self):
        return os.path.join(settings.MEDIA_ROOT, self.figure.url)


class DocumentPublicRequest(models.Model):
    user = models.ForeignKey(User)
    document = models.ForeignKey(Document)
    type=models.CharField(max_length=50)
    class Meta:
        app_label='bodb'

    def send(self):
        # create Model public request
        # message subject
        subject='New %s Public Request' % self.type
        # message text
        text='The user <i>%s</i> is requesting that the following %s entry be made public:<br>' % (self.user.username, self.type)
        entry_url = ''.join(
            ['http://', get_current_site(None).domain, '/bodb/%s/%d/' % (self.type.lower(),self.document.id)])
        text+='<b>Name</b>: <a href="%s"/>%s</a><br>' % (entry_url,self.document.title)
        text+='<b>Brief Description</b>: %s<br>' % self.document.brief_description

        users=User.objects.all()
        for user in users:
            if user.is_superuser:
                messageUser(user, subject, text)

    def save(self, *args, **kwargs):
        if self.id is None:
            self.send()
        super(DocumentPublicRequest,self).save(**kwargs)

def compareDocuments(a, b):
    return cmp(a.title.lower(), b.title.lower())
