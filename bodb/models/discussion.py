from django.db import models
from bodb.signals import forum_post_added
from mptt.fields import TreeForeignKey
from mptt.models import MPTTModel
from registration.models import User
from django.conf import settings

class Forum(models.Model):
    class Meta:
        app_label='bodb'

class Post(MPTTModel):
    forum=models.ForeignKey(Forum,null=True)
    parent=TreeForeignKey('self', null=True, blank=True, related_name='children')
    posted = models.DateTimeField(auto_now_add=True,blank=True)
    author=models.ForeignKey(User,null=True)
    body=models.TextField()
    class Meta:
        app_label='bodb'

    def get_children(self):
        return self.children.all().order_by('-posted')

    def save(self, *args, **kwargs):
        if not self.id:
            forum_post_added.send(sender=self)
        super(Post,self).save(*args, **kwargs)
        
    @property
    def site_url(self):
        return settings.URL_BASE
