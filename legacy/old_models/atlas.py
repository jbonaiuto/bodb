from django.contrib.auth.models import User
from django.core.mail import EmailMessage
from django.db import models
from django.template.defaultfilters import slugify
from legacy.old_models.workspace import BodbProfile
from legacy.old_models.messaging import Message
from legacy.photologue.models import Gallery
from legacy.tagging.fields import TagField
from legacy.old_models.literature import Literature
from legacy.util import create_gallery

class Atlas(models.Model):
    file=models.CharField(max_length=200)
    class Meta:
        app_label='legacy_bodb'

# Animal species
class Species(models.Model):
    genus_name = models.CharField(max_length=200)
    species_name = models.CharField(max_length=200)
    common_name = models.CharField(max_length=200, blank=True)
    creation_time = models.DateTimeField(auto_now_add=True,blank=True)
    # When listing multiple records - the plural form of species is species, not speciess
    class Meta:
        app_label='legacy_bodb'
        verbose_name_plural = 'species'

    # when printing instances of this class, print "genus species"
    def __unicode__(self):
        return u"%s %s" % (self.genus_name, self.species_name)


# Brain nomenclature
class Nomenclature(models.Model):
    # literature record the nomenclature is published in
    lit = models.ForeignKey(Literature)
    name = models.CharField(max_length=200)
    version = models.CharField(max_length=100)
    # species the nomenclature is based on
    species = models.ManyToManyField(Species)
    creation_time = models.DateTimeField(auto_now_add=True,blank=True)
    # gallery of nomenclature images
    gallery = models.ForeignKey(Gallery, related_name='nomenclature_gallery',null=True)
    class Meta:
        app_label='legacy_bodb'
        ordering=['name']

    # when printing instances of this class, print "name (version)"
    def __unicode__(self):
        return u"%s (%s)" % (self.name, self.version)

    def save(self, force_insert=False, force_update=False):
        # creating a new object
        if self.id is None or self.gallery is None:
            # create gallery
            if len(self.name)<=50:
                self.gallery=create_gallery(self.name, slugify(self.name))
            else:
                self.gallery=create_gallery(self.name, slugify(self.name[:40]))
            self.gallery.save()

        super(Nomenclature, self).save()


class CoordinateSpace(models.Model):
    name = models.CharField(max_length=200)
    class Meta:
        app_label='legacy_bodb'
        ordering=['name']

    # when printing instances of this class, print "name (version)"
    def __unicode__(self):
        return u"%s" % self.name


# A three-dimensional Cartesian coordinate
class ThreeDCoord(models.Model):
    x=models.FloatField()
    y=models.FloatField()
    z=models.FloatField()
    class Meta:
        app_label='legacy_bodb'

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
    # entry tags
    tags = TagField()
    # when listing multiple instances of this class, order by nomenclature then name
    class Meta:
        app_label='legacy_bodb'
        ordering=['nomenclature', 'name']

    # When printing instances of this class, print "nomenclature - abbreviation" or "nomenclature - name"
    def __unicode__(self):
        if len(self.abbreviation)>0:
            return u"%s" % self.abbreviation
        else:
            return u"%s" % self.name

    def data_xml(self):
        # brain region info
        docml='<doc:brain_region id="'+str(self.id)+'">\n'
        docml+='<doc:name>'+unicode(self.name).encode('latin1','xmlcharrefreplace')+'</doc:name>\n'
        if self.abbreviation:
            docml+='<doc:abbreviation>'+unicode(self.abbreviation).encode('latin1','xmlcharrefreplace')+'</doc:abbreviation>\n'
        docml+='<doc:nomenclature>'+unicode(self.nomenclature).encode('latin1','xmlcharrefreplace').replace('&','&amp;')+'</doc:nomenclature>\n'
        docml+='<doc:species>'+unicode(self.nomenclature.species.all()[0]).encode('latin1','xmlcharrefreplace')+'</doc:species>\n'
        docml+='</doc:brain_region>\n'
        return docml

# Brain region volume
class BrainRegionVolume(models.Model):
    brain_region = models.ForeignKey(BrainRegion)
    coord_space = models.ForeignKey(CoordinateSpace)
    coords = models.ManyToManyField(ThreeDCoord, blank=True)
    class Meta:
        app_label='legacy_bodb'

class CoCoMacBrainRegion(models.Model):
    brain_region = models.ForeignKey(BrainRegion, related_name='cocomac_region')
    cocomac_id = models.CharField(max_length=100)
    class Meta:
        app_label='legacy_bodb'

class BrainNavigatorBrainRegion(models.Model):
    brain_region = models.ForeignKey(BrainRegion, related_name='brainnav_region')
    color = models.CharField(max_length=6)
    class Meta:
        app_label='legacy_bodb'


# The relationship between some record and a Brain Region
class RelatedBrainRegion(models.Model):
    brain_region = models.ForeignKey(BrainRegion, related_name='brain_region')
    relationship = models.TextField(blank=True)
    class Meta:
        app_label='legacy_bodb'
        ordering=['brain_region__nomenclature', 'brain_region__name']

    def data_xml(self):
        docml='<doc:related_brain_region>\n'

        docml+=self.brain_region.data_xml()

        # relationship to document
        docml+='<doc:relationship>'+unicode(self.relationship).encode('latin1','xmlcharrefreplace')+'</doc:relationship>\n'

        docml+='</doc:related_brain_region>\n'
        return docml

class LocalServerMapping(models.Model):
    local_region=models.ForeignKey(BrainRegion)
    server_region_id=models.IntegerField()
    class Meta:
        app_label='bodb'

class BrainRegionRequest(models.Model):
    user=models.ForeignKey(User, blank=True, null=True)
    name=models.TextField()
    abbreviation=models.TextField()
    parent=models.TextField()
    children=models.TextField()
    nomenclature=models.TextField()
    nomenclature_version=models.TextField()
    rationale=models.TextField()
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