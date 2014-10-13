import matplotlib
from matplotlib.backends.backend_agg import FigureCanvasAgg

matplotlib.use('Agg')
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models import Q
from matplotlib.figure import Figure
from numpy.core.umath import exp
from numpy.numarray import arange
from bodb.models import Document, sendNotifications, CoCoMacBrainRegion, UserSubscription, ElectrodePosition, BrainRegion
import matplotlib.pyplot as plt
from bodb.signals import coord_selection_changed, coord_selection_deleted
from model_utils.managers import InheritanceManager
from registration.models import User
import numpy as np
import scipy.io
import matplotlib.pyplot as plt

class SED(Document):
    """
    Summary of Experimental Data (SED) - inherits from Document
    """
    TYPE_CHOICES = (
        ('', ''),
        ('generic', 'generic'),
        ('brain imaging', 'imaging'),
        ('connectivity', 'connectivity'),
        ('event related potential', 'erp'),
        ('neurophysiology', 'neurophysiology')
        )
    objects = InheritanceManager()
    type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    # related literature entries
    literature = models.ManyToManyField('Literature')

    def get_absolute_url(self):
        return reverse('sed_view', kwargs={'pk': self.pk})

    class Meta:
        app_label='bodb'
        permissions= (
            ('save_sed', 'Can save the SED'),
            ('public_sed', 'Can make the SED public'),
            )

    def save(self, *args, **kwargs):
        notify=False
        # creating a new object
        if self.id is None:
            notify=True
        elif SED.objects.filter(id=self.id).count():
            made_public=not SED.objects.get(id=self.id).public and self.public
            made_not_draft=SED.objects.get(id=self.id).draft and not int(self.draft)
            if made_public or made_not_draft:
                notify=True

        super(SED, self).save(*args, **kwargs)

        if notify:
            # send notifications to subscribed users
            sendNotifications(self, 'SED')

    def as_json(self):
        json=super(SED,self).as_json()
        json['type']=self.type
        return json

    @staticmethod
    def get_literature_seds(literature, user):
        return SED.objects.filter(Q(Q(type='generic') & Q(literature=literature) &
                                    Document.get_security_q(user))).distinct()

    @staticmethod
    def get_brain_region_seds(brain_region, user):
        return SED.objects.filter(Q(Q(type='generic') & Q(related_region_document__brain_region=brain_region) &
                                    Document.get_security_q(user))).distinct()

    @staticmethod
    def get_sed_list(seds, user):
        profile=None
        active_workspace=None
        if user.is_authenticated() and not user.is_anonymous():
            profile=user.get_profile()
            active_workspace=profile.active_workspace
        sed_list=[]
        for sed in seds:
            if CoCoMacConnectivitySED.objects.filter(id=sed.id).count():
                sed=CoCoMacConnectivitySED.objects.get(id=sed.id)
            if BredeBrainImagingSED.objects.filter(id=sed.id).count():
                sed=BredeBrainImagingSED.objects.get(id=sed.id)
            selected=active_workspace is not None and active_workspace.related_seds.filter(id=sed.id).count()>0
            is_favorite=profile is not None and profile.favorites.filter(id=sed.id).count()>0
            subscribed_to_user=profile is not None and UserSubscription.objects.filter(subscribed_to_user=sed.collator,
                user=user, model_type='SED').count()>0
            sed_list.append([selected,is_favorite,subscribed_to_user,sed])
        return sed_list

    @staticmethod
    def get_tagged_seds(name, user):
        return SED.objects.filter(Q(type='generic') & Q(tags__name__iexact=name) &
                                  Document.get_security_q(user)).distinct()


# ERP SED Model, inherits from SED
class ERPSED(SED):
    cognitive_paradigm=models.TextField()
    sensory_modality=models.TextField()
    response_modality=models.TextField()
    control_condition=models.TextField()
    experimental_condition=models.TextField()

    class Meta:
        app_label='bodb'

    @staticmethod
    def augment_sed_list(sed_list, components):
        for sed_list_item,component_list in zip(sed_list,components):
            sed_list_item.append(component_list)
        return sed_list

    @staticmethod
    def get_literature_seds(literature, user):
        return ERPSED.objects.filter(Q(Q(literature=literature) & Document.get_security_q(user))).distinct()

    @staticmethod
    def get_brain_region_seds(brain_region, user):
        return ERPSED.objects.filter(Q(Q(related_region_document__brain_region=brain_region) &
                                       Document.get_security_q(user))).distinct()

    @staticmethod
    def get_tagged_seds(name, user):
        return ERPSED.objects.filter(Q(tags__name__iexact=name) & Document.get_security_q(user)).distinct()


class ElectrodeCap(models.Model):
    manufacturer=models.CharField(max_length=100)
    name=models.CharField(max_length=100)
    version=models.CharField(max_length=50)
    num_channels=models.IntegerField()
    image_filename=models.CharField(max_length=100)

    class Meta:
        app_label='bodb'

    def __unicode__(self):
        return '%s - %s (%s) %dch' % (self.manufacturer,self.name,self.version,self.num_channels)


# ERP SED Component Model, 1-to-Many relationship with ERP SED Model objects
class ERPComponent(models.Model):
    LATENCY_CHOICES = (
        ('exact', 'Exact'),
        ('approx', 'Approximate'),
        ('window', 'Time Window')
        )

    erp_sed=models.ForeignKey(ERPSED, related_name = 'components')
    component_name=models.CharField(max_length=100)

    latency_peak=models.DecimalField(decimal_places=3, max_digits=10, null=False)
    latency_peak_type=models.CharField(max_length=100, choices=LATENCY_CHOICES, default='exact')
    latency_onset=models.DecimalField(decimal_places=3, max_digits=10, null=True, blank=True)

    amplitude_peak=models.DecimalField(decimal_places=3, max_digits=10, null=True, blank=True)
    amplitude_mean=models.DecimalField(decimal_places=3, max_digits=10, null=True, blank=True)

    electrode_cap=models.ForeignKey(ElectrodeCap, null=True, blank=True)
    channel_number=models.CharField(max_length=100, blank=True)
    electrode_position=models.ForeignKey(ElectrodePosition, null=True, blank=True)

    source=models.CharField(max_length=100, blank=True)

    interpretation=models.TextField()

    class Meta:
        app_label='bodb'

    def as_json(self):
        json={
            'id': self.id,
            'name': self.component_name,
            'latency_peak': self.latency_peak.__str__(),
            'latency_peak_type': self.latency_peak_type,
            'position_system': '',
            'position': ''
        }
        if self.electrode_position is not None:
            json['position_system']=self.electrode_position.position_system.name
            json['position']=self.electrode_position.name
        return json


# A summary of brain imaging data: inherits from SED
class BrainImagingSED(SED):
    METHOD_CHOICES = (
        ('fMRI', 'fMRI'),
        ('PET', 'PET'),
        )
    HEADER_CHOICES = (
        ('x | y | z', 'x y z'),
        ('hemisphere', 'hemisphere'),
        ('rCBF', 'rCBF'),
        ('T', 'T'),
        ('Z', 'Z'),
        ('N/A', 'N/A'),
        )
    objects = InheritanceManager()
    # method can be PET or fMRI
    method = models.CharField(max_length=10, choices=METHOD_CHOICES)
    # description of control condition
    control_condition = models.TextField()
    # description of experimental condition
    experimental_condition = models.TextField()
    # coordinate space
    coord_space = models.ForeignKey('CoordinateSpace')
    # basic column headers
    core_header_1 = models.CharField(max_length=20, choices=HEADER_CHOICES, default='hemisphere')
    core_header_2 = models.CharField(max_length=20, choices=HEADER_CHOICES, default='x y z')
    core_header_3 = models.CharField(max_length=20, choices=HEADER_CHOICES, default='rCBF')
    core_header_4 = models.CharField(max_length=20, choices=HEADER_CHOICES, default='T')
    # extra column headers
    extra_header = models.TextField(blank=True)

    class Meta:
        app_label='bodb'

    def html_url_string(self):
        return ''

    def as_json(self):
        json=super(BrainImagingSED,self).as_json()
        json['url_str']=self.html_url_string()
        return json

    @staticmethod
    def get_literature_seds(literature, user):
        return BrainImagingSED.objects.filter(Q(Q(literature=literature) & Document.get_security_q(user))).distinct()

    @staticmethod
    def get_brain_region_seds(brain_region, user):
        region_q=Q(coordinates__named_brain_region=brain_region) | \
                 Q(coordinates__coord__brainregionvolume__brain_region__name=brain_region) | \
                 Q(coordinates__coord__brainregionvolume__brain_region__parent_region__name=brain_region) | \
                 Q(related_region_document__brain_region=brain_region)
        return BrainImagingSED.objects.filter(Q(region_q & Document.get_security_q(user))).distinct()

    @staticmethod
    def augment_sed_list(sed_list, coords):
        for sed_list_item,coord_list in zip(sed_list,coords):
            sed_list_item.append(coord_list)
        return sed_list

    @staticmethod
    def get_tagged_seds(name, user):
        return BrainImagingSED.objects.filter(Q(tags__name__iexact=name) & Document.get_security_q(user)).distinct()


# SED coordinate
class SEDCoord(models.Model):
    STATISTIC_CHOICES = (
        ('t', 't'),
        ('z', 'z'),
        )
    HEMISPHERE_CHOICES = (
        ('left', 'left'),
        ('interhemispheric','interhemispheric'),
        ('right', 'right'),
        )
    # SED that coordinate is from
    sed = models.ForeignKey('BrainImagingSED', related_name = 'coordinates')
    # three-d coordinate
    coord = models.ForeignKey('ThreeDCoord')
    # rCBF measure
    rcbf = models.DecimalField(decimal_places=3, max_digits=10, null=True)
    # t- or z- value
    statistic_value = models.DecimalField(decimal_places=3, max_digits=10, null=True)
    # statistic used (t or z)
    statistic = models.CharField(max_length=2, choices=STATISTIC_CHOICES, blank=True, null=True)
    # hemisphere coordinate is in
    hemisphere = models.CharField(max_length=16, choices=HEMISPHERE_CHOICES, blank=True, null=True)
    # brain region named in paper
    named_brain_region = models.CharField(max_length=200)
    # extra data (for extra headers)
    extra_data = models.TextField(blank=True, null=True)

    class Meta:
        app_label='bodb'

    def as_json(self):
        return {
            'id': self.id,
            'brain_region': self.named_brain_region,
            'hemisphere': self.hemisphere,
            'x': self.coord.x,
            'y': self.coord.y,
            'z': self.coord.z
        }


class BredeBrainImagingSED(BrainImagingSED):
    woexp=models.IntegerField()
    class Meta:
        app_label='bodb'

    def html_url_string(self):
        url='http://neuro.imm.dtu.dk/services/brededatabase/WOEXP_%s.html' % str(self.woexp)
        return '<a href="%s" onclick="window.open(\'%s\'); return false;">View in Brede</a>' % (url,url)


# A saved selection of atlas coordinates
class SavedSEDCoordSelection(models.Model):
    # user selection belongs to
    user = models.ForeignKey(User)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    last_modified_by = models.ForeignKey(User,null=True,related_name='coord_selection_last_modified_by')
    class Meta:
        app_label='bodb'

    def get_modified_by_str(self):
        if self.last_modified_by.last_name:
            return '%s %s' % (self.last_modified_by.first_name, self.last_modified_by.last_name)
        else:
            return self.last_modified_by.username

    def get_collator_str(self):
        if self.user.last_name:
            return '%s %s' % (self.user.first_name, self.user.last_name)
        else:
            return self.user.username

    def save(self, *args, **kwargs):
        if self.id:
            coord_selection_changed.send(sender=self)
        super(SavedSEDCoordSelection,self).save(**kwargs)

    def delete(self, *args, **kwargs):
        coord_selection_deleted.send(sender=self)
        super(SavedSEDCoordSelection,self).delete(**kwargs)


# A selected SED coordinate
class SelectedSEDCoord(models.Model):
    TWOD_SHAPE_CHOICES = (
        ('x', 'x'),
        ('cross', 'cross'),
        ('square', 'square'),
        ('filled square', 'filled square'),
        ('diamond', 'diamond'),
        ('filled diamond', 'filled diamond'),
        ('circle', 'circle'),
        ('filled circle', 'filled circle'),
        ('triangle', 'triangle'),
        ('filled triangle', 'filled triangle'),
        ('inverted triangle', 'inverted triangle'),
        ('filled inverted triangle', 'filled inverted triangle'),
        )
    THREED_SHAPE_CHOICES = (
        ('cube', 'cube'),
        ('sphere', 'sphere'),
        ('cone', 'cone'),
        ('cylinder', 'cylinder'),
        )
    # selection coordinate belongs to
    saved_selection = models.ForeignKey(SavedSEDCoordSelection, null=True, blank=True)
    # the coordinate the selection points to
    sed_coordinate = models.ForeignKey(SEDCoord)
    # whether or not coordinate is visible in the viewer
    visible = models.BooleanField(default=True)
    # 2D shape of coordinate
    twod_shape = models.CharField(max_length=50, choices=TWOD_SHAPE_CHOICES, default='x')
    # 3D shape of coordinate
    threed_shape = models.CharField(max_length=50, choices=THREED_SHAPE_CHOICES, default='cube')
    # coordinate color
    color = models.CharField(max_length=50, default='ff0000')
    # whether or not currently selected
    selected = models.BooleanField(default=False)
    # user selection belongs to
    user = models.ForeignKey(User)
    class Meta:
        app_label='bodb'

    # make a copy of selected coordinate
    def copy(self):
        clone=SelectedSEDCoord()
        clone.sed_coordinate=self.sed_coordinate
        clone.visible=self.visible
        clone.twod_shape=self.twod_shape
        clone.threed_shape=self.threed_shape
        clone.color=self.color
        clone.selected=self.selected
        return clone

    def get_collator_str(self):
        if self.user.last_name:
            return '%s %s' % (self.user.first_name, self.user.last_name)
        else:
            return self.user.username


# A summary of connectivity data: inherits from SED
class ConnectivitySED(SED):
    source_region = models.ForeignKey('BrainRegion', related_name='source_region')
    target_region = models.ForeignKey('BrainRegion', related_name='target_region')
    class Meta:
        app_label='bodb'

    def html_url_string(self):
        return ''

    def as_json(self):
        json=super(ConnectivitySED,self).as_json()
        json['url_str']=self.html_url_string()
        return json

    @staticmethod
    def get_literature_seds(literature, user):
        return ConnectivitySED.objects.filter(Q(Q(literature=literature) & Document.get_security_q(user))).distinct()

    @staticmethod
    def get_brain_region_seds(brain_region, user):
        region_q=Q(source_region=brain_region) | Q(target_region=brain_region) | \
                 Q(related_region_document__brain_region=brain_region)
        return ConnectivitySED.objects.filter(Q(region_q & Document.get_security_q(user))).distinct()

    @staticmethod
    def get_tagged_seds(name, user):
        return ConnectivitySED.objects.filter(Q(tags__name__iexact=name) & Document.get_security_q(user)).distinct()


class CoCoMacConnectivitySED(ConnectivitySED):
    class Meta:
        app_label='bodb'

    def html_url_string(self):
        if CoCoMacBrainRegion.objects.filter(brain_region__id=self.source_region.id) and \
           CoCoMacBrainRegion.objects.filter(brain_region__id=self.target_region.id):
            cocomac_url='http://cocomac.g-node.org/cocomac2/services/axonal_projections.php?axonOriginList='
            #cocomac_url="http://cocomac.org/URLSearch.asp?Search=Connectivity&DataSet=PRIMPROJ&User=jbonaiuto&Password=4uhk48s3&OutputType=HTML_Browser&SearchString="

            cocomac_source=CoCoMacBrainRegion.objects.get(brain_region__id=self.source_region.id)
            source_id=cocomac_source.cocomac_id.split('-',1)
            cocomac_url+='%s-%s' % (source_id[0],source_id[1])
#            cocomac_url+="(\\'"+source_id[0]+"\\')[SourceMap]"
#            cocomac_url+=" AND "
#            cocomac_url+="(\\'"+source_id[1]+"\\') [SourceSite]"
#            cocomac_url+=" AND "

            cocomac_target=CoCoMacBrainRegion.objects.get(brain_region__id=self.target_region.id)
            target_id=cocomac_target.cocomac_id.split('-',1)
            cocomac_url+='&axonTerminalList=%s-%s' % (target_id[0],target_id[1])
#            cocomac_url+="(\\'"+target_id[0]+"\\')[TargetMap]"
#            cocomac_url+=" AND "
#            cocomac_url+="(\\'"+target_id[1]+"\\') [TargetSite]"
            #cocomac_url+="&Details=&SortOrder=asc&SortBy=SOURCEMAP&Dispmax=32767&ItemsPerPage= 20"
            cocomac_url+='&includeLargeInjections=0&useAM=1&useSORT=0&output=dhtml&undefined=undefined'
            return '<a href="%s" onclick="window.open(\'%s\'); return false;">View in CoCoMac</a>' % (cocomac_url,
                                                                                                      cocomac_url)
        return ''


def conn_sed_gxl(conn_seds):
    glx='<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n'
    glx+='<gxl xmlns="http://www.gupro.de/GXL/gxl-1.0.dtd" xmlns:xlink="http://www.w3.org/1999/xlink">\n'
    glx+='<graph id="connectivity-sed-map" edgeids="true" edgemode="directed" hypergraph="false">\n'
    glx+='<attr name="overlap"><string>scale</string></attr>\n'
    nodes={}
    for sed in conn_seds:
        sourcename=str(sed.source_region.__unicode__().replace('"','\'').replace('&','&amp;'))+' ('+\
                   sed.source_region.nomenclature.name.replace('"','\'').replace('&','&amp;')+')'
        targetname=str(sed.target_region.__unicode__().replace('"','\'').replace('&','&amp;'))+' ('+\
                   sed.target_region.nomenclature.name.replace('"','\'').replace('&','&amp;')+')'
        if not str(sed.source_region.__unicode__()) in nodes:
            nodes[str(sed.source_region.__unicode__())]=[]
        nodes[str(sed.source_region.__unicode__())].append((sourcename, sed.source_region.id))
        if not str(sed.target_region.__unicode__()) in nodes:
            nodes[str(sed.target_region.__unicode__())]=[]
        nodes[str(sed.target_region.__unicode__())].append((targetname, sed.target_region.id))
    for i,(node_name, children) in enumerate(nodes.iteritems()):
        glx+='<node id="'+node_name.replace('"','\'').replace('&','&amp;')+'">\n'
        glx+='<graph id="cluster_%d" edgeids="true" edgemode="directed" hypergraph="false">\n' % i
        for (name,id) in children:
            glx+='<node id="'+name+'">\n'
            glx+='<type xlink:href="/bodb/brain_region/'+str(id)+'/" xlink:type="simple"/>\n'
            glx+='</node>\n'
        glx+='</graph>\n'
        glx+='</node>\n'
    for sed in conn_seds:
        sourcename=str(sed.source_region.__unicode__().replace('"','\'').replace('&','&amp;'))+' ('+\
                   sed.source_region.nomenclature.name.replace('"','\'').replace('&','&amp;')+')'
        targetname=str(sed.target_region.__unicode__().replace('"','\'').replace('&','&amp;'))+' ('+\
                   sed.target_region.nomenclature.name.replace('"','\'').replace('&','&amp;')+')'
        glx+='<edge id="'+str(sed.id)+'" to="'+targetname+'" from="'+sourcename+'">\n'
        glx+='<type xlink:href="/bodb/sed/'+str(sed.id)+'/" xlink:type="simple"/>\n'
        glx+='</edge>\n'
    glx+='</graph>\n'
    glx+='</gxl>\n'
    return glx


# An SED used to build a model or support a BOP
class BuildSED(models.Model):
    # the SED is either scene setting or supports some aspect of the model design
    RELATIONSHIP_CHOICES = (
        ('scene setting', 'scene setting'),
        ('support', 'support'),
        )
    # document attached to
    document = models.ForeignKey('Document', related_name='related_build_sed_document')
    # the SED
    sed = models.ForeignKey('SED', related_name='build_sed')
    # the relationship between the SED and model or BOP
    relationship = models.CharField(max_length=30, choices=RELATIONSHIP_CHOICES)
    # relevance narrative - how the SED relates to the model in detail
    relevance_narrative = models.TextField(blank=True)
    class Meta:
        app_label='bodb'
        ordering=['sed__title']

    @staticmethod
    def get_building_sed_list(bseds, user):
        profile=None
        active_workspace=None
        if user.is_authenticated() and not user.is_anonymous():
            profile=user.get_profile()
            active_workspace=profile.active_workspace
        build_sed_list=[]
        for buildsed in bseds:
            selected=active_workspace is not None and \
                     active_workspace.related_seds.filter(id=buildsed.sed.id).count()>0
            is_favorite=profile is not None and profile.favorites.filter(id=buildsed.sed.id).count()>0
            subscribed_to_user=profile is not None and \
                               UserSubscription.objects.filter(subscribed_to_user=buildsed.sed.collator, user=user,
                                   model_type='SED').count()>0
            build_sed_list.append([selected,is_favorite,subscribed_to_user,buildsed])
        return build_sed_list

    @staticmethod
    def get_building_seds(document, user):
        return BuildSED.objects.filter(Q(Q(document=document) & Document.get_security_q(user, field='sed'))).distinct()

    @staticmethod
    def get_generic_building_seds(document, user):
        return BuildSED.objects.filter(Q(Q(document=document) & Q(sed__type='generic') &
                                         Document.get_security_q(user, field='sed'))).distinct()

    @staticmethod
    def get_connectivity_building_seds(document, user):
        return BuildSED.objects.filter(Q(Q(document=document) & Q(sed__connectivitysed__isnull=False) &
                                         Document.get_security_q(user, field='sed'))).distinct()

    @staticmethod
    def get_imaging_building_seds(document, user):
        return BuildSED.objects.filter(Q(Q(document=document) & Q(sed__brainimagingsed__isnull=False) &
                                         Document.get_security_q(user, field='sed'))).distinct()

    @staticmethod
    def get_erp_building_seds(document, user):
        return BuildSED.objects.filter(Q(Q(document=document) & Q(sed__erpsed__isnull=False) &
                                         Document.get_security_q(user, field='sed'))).distinct()


def compareBuildSEDs(a, b):
    return cmp(a.sed.title.lower(), b.sed.title.lower())

class TestSEDSSR(models.Model):
    test_sed=models.ForeignKey('TestSED')
    ssr=models.ForeignKey('SSR', null=True)

    class Meta:
        app_label='bodb'

# An SED used to test a model prediction
class TestSED(models.Model):
    # the model prediction either explains or contradicts the SED
    RELATIONSHIP_CHOICES = (
        ('explanation', 'explanation'),
        ('contradiction', 'contradiction'),
        )
    model=models.ForeignKey('Model', related_name='related_test_sed_document')
    # the SED
    sed = models.ForeignKey('SED', related_name='test_sed',null=True)
    # the relationship between the SSR and SED
    relationship = models.CharField(max_length=30, choices=RELATIONSHIP_CHOICES)
    # relevance narrative - how the SED relates to the SSR in detail
    relevance_narrative = models.TextField(blank=True)

    class Meta:
        app_label='bodb'

    def save(self, force_insert=False, force_update=False):
        super(TestSED, self).save()

    @staticmethod
    def get_testing_sed_list(tseds, user):
        profile=None
        active_workspace=None
        if user.is_authenticated() and not user.is_anonymous():
            profile=user.get_profile()
            active_workspace=profile.active_workspace
        test_sed_list=[]
        for testsed in tseds:
            sed_selected=active_workspace is not None and \
                         active_workspace.related_seds.filter(id=testsed.sed.id).count()>0
            sed_is_favorite=profile is not None and profile.favorites.filter(id=testsed.sed.id).count()>0
            sed_subscribed_to_user=profile is not None and \
                                   UserSubscription.objects.filter(subscribed_to_user=testsed.sed.collator, user=user,
                                       model_type='SED').count()>0
            ssr_selected=active_workspace is not None and \
                         active_workspace.related_ssrs.filter(id=testsed.get_ssr().id).count()>0
            ssr_is_favorite=profile is not None and profile.favorites.filter(id=testsed.get_ssr().id).count()>0
            ssr_subscribed_to_user=profile is not None and\
                                   UserSubscription.objects.filter(subscribed_to_user=testsed.get_ssr().collator,
                                       user=user, model_type='SSR').count()>0
            test_sed_list.append([sed_selected,sed_is_favorite,sed_subscribed_to_user,ssr_selected,ssr_is_favorite,
                                  ssr_subscribed_to_user,testsed])
        return test_sed_list

    @staticmethod
    def get_testing_seds(model, user):
        return TestSED.objects.filter(Q(Q(model=model) & Document.get_security_q(user, field='sed') &
                                        Document.get_security_q(user, field='testsedssr__ssr'))).distinct()

    @staticmethod
    def get_generic_testing_seds(model, user):
        return TestSED.objects.filter(Q(Q(model=model) & Q(sed__type='generic') &
                                        Document.get_security_q(user, field='sed') &
                                        Document.get_security_q(user, field='testsedssr__ssr'))).distinct()

    @staticmethod
    def get_connectivity_testing_seds(model, user):
        return TestSED.objects.filter(Q(Q(model=model) & Q(sed__connectivitysed__isnull=False) &
                                        Document.get_security_q(user, field='sed') &
                                        Document.get_security_q(user, field='testsedssr__ssr'))).distinct()

    @staticmethod
    def get_imaging_testing_seds(model, user):
        return TestSED.objects.filter(Q(Q(model=model) & Q(sed__brainimagingsed__isnull=False) &
                                        Document.get_security_q(user, field='sed') &
                                        Document.get_security_q(user, field='testsedssr__ssr'))).distinct()

    @staticmethod
    def get_erp_testing_seds(model, user):
        return TestSED.objects.filter(Q(Q(model=model) & Q(sed__erpsed__isnull=False) &
                                        Document.get_security_q(user, field='sed') &
                                        Document.get_security_q(user, field='testsedssr__ssr'))).distinct()

    def get_ssr(self):
        if TestSEDSSR.objects.filter(test_sed=self).count()>0:
            return TestSEDSSR.objects.filter(test_sed=self)[0].ssr
        return None


def compareTestSEDs(a, b):
    return cmp(a.sed.title.lower(), b.sed.title.lower())


def find_similar_seds(user, title, brief_description):
    similar=[]
    other_seds=SED.objects.filter(Document.get_security_q(user)).distinct()
    for sed in other_seds:
        total_match=0
        for title_word in title.split(' '):
            if sed.title.find(title_word)>=0:
                total_match+=1
        for desc_word in brief_description.split(' '):
            if sed.brief_description.find(desc_word)>=0:
                total_match+=1
        similar.append((sed,total_match))
    similar.sort(key=lambda tup: tup[1],reverse=True)
    return similar


# A summary of neurophysiological data: inherits from SED
class NeurophysiologySED(SED):
    class Meta:
        app_label='bodb'

    @staticmethod
    def get_literature_seds(literature, user):
        return NeurophysiologySED.objects.filter(Q(Q(literature=literature) & Document.get_security_q(user))).distinct()

    @staticmethod
    def get_brain_region_seds(brain_region, user):
        region_q=Q(neurophysiology_condition__recordingtrial__unit__area=brain_region) |\
                 Q(related_region_document__brain_region=brain_region)
        return NeurophysiologySED.objects.filter(Q(region_q & Document.get_security_q(user))).distinct()

    @staticmethod
    def get_tagged_seds(name, user):
        return NeurophysiologySED.objects.filter(Q(tags__name__iexact=name) & Document.get_security_q(user)).distinct()


class NeurophysiologyCondition(models.Model):
    sed=models.ForeignKey('NeurophysiologySED')
    name=models.CharField(max_length=100)
    description=models.TextField()

    class Meta:
        app_label='bodb'

    def plot_trial_spikes(self, unit, ax, event_colors, x_min, x_max, align_to=None):
        trials=RecordingTrial.objects.filter(unit=unit, condition=self)
        for trial_idx, trial in enumerate(trials):
            align_time=trial.start_time
            if align_to is not None:
                align_time=Event.objects.get(trial=trial,name=align_to).time

            trial_relative_spike_times=trial.get_relative_spike_times(align_to=align_to)
            for spike_time in trial_relative_spike_times:
                ax.plot([spike_time,spike_time],[trial_idx,trial_idx+1],'k')

            rel_start_time=float(trial.start_time)-float(align_time)
            ax.plot([rel_start_time,rel_start_time],[trial_idx,trial_idx+1],'c')

            events=Event.objects.filter(trial=trial)
            for event in events:
                rel_event_time=float(event.time)-float(align_time)
                ax.plot([rel_event_time,rel_event_time],[trial_idx,trial_idx+1],event_colors[event.name])

        ax.set_ylim([0,len(trials)])
        ax.set_xlim([x_min,x_max])
        ax.set_ylabel('Trial')
        ax.set_title(self.name)

    def get_trial_mean_firing_rate(self, unit, bin_width, align_to=None):
        trials=RecordingTrial.objects.filter(unit=unit, condition=self)
        condition_rel_spike_times=[]
        for trial_idx, trial in enumerate(trials):
            condition_rel_spike_times.extend(trial.get_relative_spike_times(align_to=align_to))

        window=exp(-arange(-2 * bin_width, 2 * bin_width + 1) ** 2 * 1. / (2 * (bin_width) ** 2))
        num_bins=int((np.max(condition_rel_spike_times)-np.min(condition_rel_spike_times))/bin_width)
        hist,bins=np.histogram(np.array(condition_rel_spike_times), bins=num_bins)
        bin_width=bins[1]-bins[0]
        smoothed_rate=np.core.numeric.convolve(hist/float(trials.count())/bin_width, window * 1. / sum(window), mode='same')
        return bins[:-1],smoothed_rate

    def plot_trial_mean_firing_rate(self, unit, bin_width, ax, x_min, x_max, y_max, align_to=None):
        bins,smoothed_rate=self.get_trial_mean_firing_rate(unit, bin_width, align_to=align_to)
        ax.plot(bins,smoothed_rate)
        ax.set_xlim([x_min, x_max])
        ax.set_ylim([0, y_max])
        ax.set_ylabel('Firing Rate (Hz)')

    def get_population_mean_firing_rate(self, brain_region, bin_width, align_to=None):
        condition_rel_spike_times=[]
        units=Unit.objects.filter(recordingtrial__condition=self, area=brain_region).distinct()
        trial_count=0
        for unit in units:
            trials=RecordingTrial.objects.filter(unit=unit, condition=self).distinct()
            for trial in trials:
                condition_rel_spike_times.extend(trial.get_relative_spike_times(align_to=align_to))
                trial_count+=1
        window=exp(-arange(-2 * bin_width, 2 * bin_width + 1) ** 2 * 1. / (2 * (bin_width) ** 2))
        num_bins=int((np.max(condition_rel_spike_times)-np.min(condition_rel_spike_times))/bin_width)
        hist,bins=np.histogram(np.array(condition_rel_spike_times), bins=num_bins)
        bin_width=bins[1]-bins[0]
        smoothed_rate=np.core.numeric.convolve(hist/float(trial_count)/bin_width, window * 1. / sum(window), mode='same')
        return bins[:-1],smoothed_rate

    def plot_population_mean_firing_rate(self, bin_width, align_to=None, filename=None):
        regions=BrainRegion.objects.filter(unit__recordingtrial__condition=self).distinct()
        if regions.count()>2:
            fig=Figure(figsize=(10,18))
        else:
            fig=Figure()

        for idx,region in enumerate(regions):
            ax=fig.add_subplot(regions.count(),1,idx+1)
            bins,smoothed_rate=self.get_population_mean_firing_rate(region, bin_width, align_to=align_to)
            ax.plot(bins,smoothed_rate)
            #ax.set_xlim([x_min, x_max])
            #ax.set_ylim([0, y_max])
            ax.set_title(region.name)
            ax.set_ylabel('Firing Rate (Hz)')
        ax.set_xlabel('Time (s)')
        if filename is not None:
            save_to_png(fig, filename)
            plt.close(fig)
        else:
            plt.show()


class Unit(models.Model):
    type=models.CharField(max_length=50)
    area=models.ForeignKey('BrainRegion')

    class Meta:
        app_label='bodb'

    def plot_condition_spikes(self, condition_ids, bin_width, align_to=None, filename=None):

        if len(condition_ids)>1:
            fig=Figure(figsize=(10,18))
        else:
            fig=Figure()

        event_colors={
            'go': 'b',
            'mo': 'r',
            'do': 'g',
            'ho': 'm',
            'hoff': 'y',
            }

        rate_max=0
        time_min=1000
        time_max=-1000
        for idx,id in enumerate(condition_ids):
            condition=NeurophysiologyCondition.objects.get(id=id)
            bins,rate=condition.get_trial_mean_firing_rate(self, bin_width, align_to=align_to)
            if np.max(rate)>rate_max:
                rate_max=np.max(rate)
            if bins[0]<time_min:
                time_min=bins[0]
            if bins[-1]>time_max:
                time_max=bins[-1]

        for idx,id in enumerate(condition_ids):
            condition=NeurophysiologyCondition.objects.get(id=id)

            ax=fig.add_subplot(len(condition_ids)*2,1,idx*2+1)
            condition.plot_trial_spikes(self, ax, event_colors, time_min, time_max, align_to=align_to)

            ax=fig.add_subplot(len(condition_ids)*2,1,idx*2+2)
            condition.plot_trial_mean_firing_rate(self, bin_width, ax, time_min, time_max, rate_max, align_to=align_to)

        ax.set_xlabel('Time (s)')

        if filename is not None:
            save_to_png(fig, filename)
            plt.close(fig)
        else:
            plt.show()


class RecordingTrial(models.Model):
    unit=models.ForeignKey('Unit')
    condition=models.ForeignKey('NeurophysiologyCondition')
    trial_number=models.IntegerField()
    start_time=models.DecimalField(max_digits=10, decimal_places=5)
    end_time=models.DecimalField(max_digits=10, decimal_places=5)
    spike_times=models.TextField()

    class Meta:
        app_label='bodb'

    def __init__(self, *args, **kwargs):
        super(RecordingTrial,self).__init__(*args, **kwargs)
        spikes=self.spike_times.split(',')
        self.spike_times_array=np.zeros(len(spikes))
        for idx,spike in enumerate(spikes):
            if len(spike) and float(spike)>=float(self.start_time)-1.0 and float(spike)<float(self.end_time)+1.0:
                self.spike_times_array[idx]=float(spike)

    def get_relative_spike_times(self, align_to=None):
        align_time=self.start_time
        if align_to is not None:
            align_time=Event.objects.get(trial=self,name=align_to).time

        return self.spike_times_array-float(align_time)

    def get_smoothed_firing_rate(self, bin_width, align_to=None):
        window=exp(-arange(-2 * bin_width, 2 * bin_width + 1) ** 2 * 1. / (2 * (bin_width) ** 2))
        rel_spike_times=self.get_relative_spike_times(align_to=align_to)
        num_bins=int((np.max(rel_spike_times)-np.min(rel_spike_times))/bin_width)
        hist,bins=np.histogram(np.array(rel_spike_times), bins=num_bins)
        bin_width=bins[1]-bins[0]
        smoothed_rate=np.core.numeric.convolve(hist/bin_width, window * 1. / sum(window), mode='same')
        return bins[:-1],smoothed_rate


class Event(models.Model):
    trial=models.ForeignKey('RecordingTrial')
    name=models.CharField(max_length=100)
    description=models.TextField()
    time=models.DecimalField(max_digits=10, decimal_places=5)

    class Meta:
        app_label='bodb'


def save_to_png(fig, output_file):
    fig.set_facecolor("#FFFFFF")
    canvas = FigureCanvasAgg(fig)
    canvas.print_png(output_file, dpi=72)

def save_to_eps(fig, output_file):
    fig.set_facecolor("#FFFFFF")
    canvas = FigureCanvasAgg(fig)
    canvas.print_eps(output_file, dpi=72)
