import hashlib
import random
from django.contrib.auth.models import User
from django.contrib.sites.models import get_current_site
from django.core.mail import EmailMessage
from django.core.urlresolvers import reverse
from django.db import models
from bodb.models.workspace import BodbProfile
from bodb.models.messaging import Message
from bodb.models.literature import Literature

class Atlas(models.Model):
    file=models.CharField(max_length=200)
    class Meta:
        app_label='bodb'


# Animal species
class Species(models.Model):
    genus_name = models.CharField(max_length=200)
    species_name = models.CharField(max_length=200)
    common_name = models.CharField(max_length=200, blank=True)
    creation_time = models.DateTimeField(auto_now_add=True,blank=True)
    #creation_time = models.DateTimeField(blank=True)
    # When listing multiple records - the plural form of species is species, not speciess
    class Meta:
        app_label='bodb'
        verbose_name_plural = 'species'

    # when printing instances of this class, print "genus species"
    def __unicode__(self):
        return u"%s %s" % (self.genus_name, self.species_name)


# Brain nomenclature
class Nomenclature(models.Model):
    # literature record the nomenclature is published in
    lit = models.ForeignKey(Literature,null=True)
    name = models.CharField(max_length=200)
    version = models.CharField(max_length=100)
    # species the nomenclature is based on
    species = models.ManyToManyField(Species)
    creation_time = models.DateTimeField(auto_now_add=True,blank=True)
    #creation_time = models.DateTimeField(blank=True)
    class Meta:
        app_label='bodb'
        ordering=['name']

    # when printing instances of this class, print "name (version)"
    def __unicode__(self):
        return u"%s (%s)" % (self.name, self.version)


class CoordinateSpace(models.Model):
    name = models.CharField(max_length=200)
    class Meta:
        app_label='bodb'
        ordering=['name']

    # when printing instances of this class, print "name (version)"
    def __unicode__(self):
        return u"%s" % self.name


class ElectrodePositionSystem(models.Model):
    name = models.CharField(max_length=200)
    class Meta:
        app_label='bodb'

    def __unicode__(self):
        return u'%s' % self.name

class ElectrodePosition(models.Model):
    name=models.CharField(max_length=5)
    position_system=models.ForeignKey(ElectrodePositionSystem)
    class Meta:
        app_label='bodb'

    def __unicode__(self):
        return self.name

# A three-dimensional Cartesian coordinate
class ThreeDCoord(models.Model):
    x=models.FloatField()
    y=models.FloatField()
    z=models.FloatField()
    class Meta:
        app_label='bodb'


# Brain Region
class BrainRegion(models.Model):
    REGION_TYPE_CHOICES = (
        ('', ''),
        ('fiber tract', 'fiber tract'),
        ('neural region', 'neural region'),
        ('ventricle', 'ventricle'),
        )
    # nomenclature region belongs to
    nomenclature = models.ForeignKey('Nomenclature')
    name = models.CharField(max_length=100)
    abbreviation = models.CharField(max_length=50, blank=True)
    # can be a fiber tract, neural region, or ventricle
    brain_region_type = models.CharField(max_length=100, choices=REGION_TYPE_CHOICES)
    # parent brain region
    parent_region = models.ForeignKey('BrainRegion', blank=True, null=True)
    # when listing multiple instances of this class, order by nomenclature then name
    class Meta:
        app_label='bodb'
        ordering=['nomenclature', 'name']

    # When printing instances of this class, print "nomenclature - abbreviation" or "nomenclature - name"
    def __unicode__(self):
        if len(self.abbreviation)>0:
            return u"%s" % self.abbreviation
        else:
            return u"%s" % self.name

    def get_absolute_url(self):
        return reverse('brain_region_view', kwargs={'pk': self.pk})


# Brain region volume
class BrainRegionVolume(models.Model):
    brain_region = models.ForeignKey(BrainRegion)
    coord_space = models.ForeignKey(CoordinateSpace)
    coords = models.ManyToManyField(ThreeDCoord, blank=True)
    class Meta:
        app_label='bodb'


class CoCoMacBrainRegion(models.Model):
    brain_region = models.ForeignKey(BrainRegion, related_name='cocomac_region')
    cocomac_id = models.CharField(max_length=100)
    class Meta:
        app_label='bodb'


class BrainNavigatorBrainRegion(models.Model):
    brain_region = models.ForeignKey(BrainRegion, related_name='brainnav_region')
    color = models.CharField(max_length=6)
    class Meta:
        app_label='bodb'


# The relationship between some record and a Brain Region
class RelatedBrainRegion(models.Model):
    document = models.ForeignKey('Document', related_name='related_region_document')
    brain_region = models.ForeignKey(BrainRegion, related_name='brain_region', null=True)
    relationship = models.TextField(blank=True)
    class Meta:
        app_label='bodb'
        ordering=['brain_region__nomenclature', 'brain_region__name']


def compareRelatedBrainRegions(a, b):
    if a.brain_region.abbreviation and len(a.brain_region.abbreviation)>0:
        if b.brain_region.abbreviation and len(b.brain_region.abbreviation)>0:
            return cmp(a.brain_region.abbreviation.lower(), b.brain_region.abbreviation.lower())
        else:
            return cmp(a.brain_region.abbreviation.lower(), b.brain_region.name.lower())
    else:
        if b.brain_region.abbreviation and len(b.brain_region.abbreviation)>0:
            return cmp(a.brain_region.name.lower(), b.brain_region.abbreviation.lower())
        else:
            return cmp(a.brain_region.name.lower(), b.brain_region.name.lower())


class LocalServerMapping(models.Model):
    local_region=models.ForeignKey(BrainRegion)
    server_region_id=models.IntegerField()
    class Meta:
        app_label='bodb'


class BrainRegionRequest(models.Model):
    STATUS_OPTIONS=(
        ('',''),
        ('approved','approved'),
        ('denied','denied')
    )
    user=models.ForeignKey(User, blank=True, null=True)
    name=models.TextField()
    abbreviation=models.TextField()
    parent=models.TextField()
    children=models.TextField()
    nomenclature=models.TextField()
    nomenclature_version=models.TextField()
    rationale=models.TextField()
    status=models.CharField(max_length=20, choices=STATUS_OPTIONS, blank=True)
    activation_key = models.CharField('activation key', max_length=40)

    class Meta:
        app_label='bodb'

    def send(self):
        # message subject
        subject='New Brain Region Request'
        # message text
        text='The user <i>%s</i> is requesting the addition of the following region:<br>' % self.user.username
        text+='<b>Name</b>: %s<br>' % self.name
        text+='<b>Abbreviation</b>: %s<br>' % self.abbreviation
        text+='<b>Parent</b>: %s<br>' % self.parent
        text+='<b>Children</b>: %s<br>' % self.children
        text+='<b>Nomenclature</b>: %s<br>' % self.nomenclature
        text+='<b>Nomenclature version</b>: %s<br>' % self.nomenclature_version
        text+='<b>Rationale</b>: %s' % self.rationale

        text += '<br>Click one of the following links to approve or deny the request:<br>'
        accept_url = ''.join(
            ['http://', get_current_site(None).domain, '/bodb/brain_region/request/approve/%s/' % self.activation_key])
        decline_url = ''.join(
            ['http://', get_current_site(None).domain, '/bodb/brain_region/request/deny/%s/' % self.activation_key])
        text += '<a href="%s">Approve</a><br>' % accept_url
        text += 'or<br>'
        text += '<a href="%s">Deny</a>' % decline_url

        users=User.objects.all()
        for user in users:
            if user.is_superuser:
                message=Message(recipient=user, sender=self.user, subject=subject, read=False)
                message.text=text
                message.save()

                profile=BodbProfile.objects.get(user__id=user.id)
                if profile.new_message_notify:
                    msg = EmailMessage(subject, text, 'uscbrainproject@gmail.com', [user.email])
                    msg.content_subtype = "html"  # Main content is now text/html
                    msg.send(fail_silently=True)

    def save(self, **kwargs):
        if self.id is None:
            salt = hashlib.sha1(str(random.random())).hexdigest()[:5]
            username = self.user.username
            if isinstance(username, unicode):
                username = username.encode('utf-8')
            self.activation_key = hashlib.sha1(salt+username).hexdigest()

            self.send()
        super(BrainRegionRequest,self).save(**kwargs)
