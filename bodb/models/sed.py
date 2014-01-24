import fileinput
import os
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models import Q
import sys
from bodb.models import Document, sendNotifications, CoCoMacBrainRegion, UserSubscription
from bodb.signals import coord_selection_changed, coord_selection_deleted
from model_utils.managers import InheritanceManager
from registration.models import User
from uscbp import settings

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

    def save(self, force_insert=False, force_update=False):
        notify=False
        # creating a new object
        if self.id is None:
            notify=True
        elif SED.objects.filter(id=self.id).count():
            made_public=not SED.objects.get(id=self.id).public and self.public
            made_not_draft=SED.objects.get(id=self.id).draft and not int(self.draft)
            if made_public or made_not_draft:
                notify=True

        super(SED, self).save()

        if notify:
            # send notifications to subscribed users
            sendNotifications(self, 'SED')

    @staticmethod
    def get_literature_seds(literature, user):
        return SED.objects.filter(Q(Q(type='generic') & Q(literature=literature) &
                                    Document.get_security_q(user))).distinct()

    @staticmethod
    def get_brain_region_seds(brain_region, user):
        return SED.objects.filter(Q(Q(type='generic') & Q(relatedbrainregion__brain_region=brain_region) &
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
        return SED.objects.filter(Q(type='generic') & Q(tags__name__icontains=name) &
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
    def get_literature_seds(literature, user):
        return ERPSED.objects.filter(Q(Q(literature=literature) & Document.get_security_q(user))).distinct()

    @staticmethod
    def get_brain_region_seds(brain_region, user):
        return ERPSED.objects.filter(Q(Q(relatedbrainregion__brain_region=brain_region) &
                                       Document.get_security_q(user))).distinct()

    @staticmethod
    def get_tagged_seds(name, user):
        return ERPSED.objects.filter(Q(tags__name__icontains=name) & Document.get_security_q(user)).distinct()


# ERP SED Component Model, 1-to-Many relationship with ERP SED Model objects
class ERPComponent(models.Model):
    LATENCY_CHOICES = (
        ('exact', 'Exact'),
        ('approx', 'Approximate'),
        ('window', 'Time Window')
        )

    erp_sed=models.ForeignKey(ERPSED)
    component_name=models.CharField(max_length=100)

    latency_peak=models.DecimalField(decimal_places=3, max_digits=10, null=False)
    latency_peak_type=models.CharField(max_length=100, choices=LATENCY_CHOICES, default='exact')
    latency_onset=models.DecimalField(decimal_places=3, max_digits=10, null=True, blank=True)

    amplitude_peak=models.DecimalField(decimal_places=3, max_digits=10, null=True, blank=True)
    amplitude_mean=models.DecimalField(decimal_places=3, max_digits=10, null=True, blank=True)

    scalp_region=models.CharField(max_length=100)

    electrode_cap=models.CharField(max_length=100, blank=True)
    electrode_name=models.CharField(max_length=100, blank=True)

    source=models.CharField(max_length=100, blank=True)

    interpretation=models.TextField()

    class Meta:
        app_label='bodb'


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

    @staticmethod
    def get_literature_seds(literature, user):
        return BrainImagingSED.objects.filter(Q(Q(literature=literature) & Document.get_security_q(user))).distinct()

    @staticmethod
    def get_brain_region_seds(brain_region, user):
        region_q=Q(sedcoord__named_brain_region=brain_region) | \
                 Q(sedcoord__coord__brainregionvolume__brain_region__name=brain_region) | \
                 Q(sedcoord__coord__brainregionvolume__brain_region__parent_region__name=brain_region) | \
                 Q(relatedbrainregion__brain_region=brain_region)
        return BrainImagingSED.objects.filter(Q(region_q & Document.get_security_q(user))).distinct()

    @staticmethod
    def augment_sed_list(sed_list, coords):
        for sed_list_item,coord_list in zip(sed_list,coords):
            sed_list_item.append(coord_list)
        return sed_list

    @staticmethod
    def get_tagged_seds(name, user):
        return BrainImagingSED.objects.filter(Q(tags__name__icontains=name) & Document.get_security_q(user)).distinct()


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
    sed = models.ForeignKey('BrainImagingSED')
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

    @staticmethod
    def get_literature_seds(literature, user):
        return ConnectivitySED.objects.filter(Q(Q(literature=literature) & Document.get_security_q(user))).distinct()

    @staticmethod
    def get_brain_region_seds(brain_region, user):
        region_q=Q(source_region=brain_region) | Q(target_region=brain_region) | \
                 Q(relatedbrainregion__brain_region=brain_region)
        return ConnectivitySED.objects.filter(Q(region_q & Document.get_security_q(user))).distinct()

    @staticmethod
    def get_tagged_seds(name, user):
        return ConnectivitySED.objects.filter(Q(tags__name__icontains=name) & Document.get_security_q(user)).distinct()


class CoCoMacConnectivitySED(ConnectivitySED):
    class Meta:
        app_label='bodb'

    def html_url_string(self):
        if CoCoMacBrainRegion.objects.filter(brain_region__id=self.source_region.id) and \
           CoCoMacBrainRegion.objects.filter(brain_region__id=self.target_region.id):
            cocomac_url="http://cocomac.org/URLSearch.asp?Search=Connectivity&DataSet=PRIMPROJ&User=jbonaiuto&Password=4uhk48s3&OutputType=HTML_Browser&SearchString="

            cocomac_source=CoCoMacBrainRegion.objects.get(brain_region__id=self.source_region.id)
            source_id=cocomac_source.cocomac_id.split('-',1)
            cocomac_url+="(\\'"+source_id[0]+"\\')[SourceMap]"
            cocomac_url+=" AND "
            cocomac_url+="(\\'"+source_id[1]+"\\') [SourceSite]"
            cocomac_url+=" AND "

            cocomac_target=CoCoMacBrainRegion.objects.get(brain_region__id=self.target_region.id)
            target_id=cocomac_target.cocomac_id.split('-',1)
            cocomac_url+="(\\'"+target_id[0]+"\\')[TargetMap]"
            cocomac_url+=" AND "
            cocomac_url+="(\\'"+target_id[1]+"\\') [TargetSite]"
            cocomac_url+="&Details=&SortOrder=asc&SortBy=SOURCEMAP&Dispmax=32767&ItemsPerPage= 20"
            return '<a href="%s" onclick="window.open(\'%s\'); return false;">View in CoCoMac</a>' % (cocomac_url,
                                                                                                      cocomac_url)
        return ''


def conn_sed_gxl(conn_seds):
    glx='<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n'
    glx+='<gxl xmlns="http://www.gupro.de/GXL/gxl-1.0.dtd" xmlns:xlink="http://www.w3.org/1999/xlink">\n'
    glx+='<graph id="connectivity-sed-map" edgeids="true" edgemode="directed" hypergraph="false">\n'
    nodes={}
    for sed in conn_seds:
        sourcename=str(sed.source_region.__unicode__())+' ('+sed.source_region.nomenclature.name+')'
        targetname=str(sed.target_region.__unicode__())+' ('+sed.target_region.nomenclature.name+')'
        if not str(sed.source_region.__unicode__()) in nodes:
            nodes[str(sed.source_region.__unicode__())]=[]
        nodes[str(sed.source_region.__unicode__())].append((sourcename, sed.source_region.id))
        if not str(sed.target_region.__unicode__()) in nodes:
            nodes[str(sed.target_region.__unicode__())]=[]
        nodes[str(sed.target_region.__unicode__())].append((targetname, sed.target_region.id))
    for node_name, children in nodes.iteritems():
        glx+='<node id="'+node_name+'">\n'
        glx+='<graph id="'+node_name+'_subgraph" edgeids="true" edgemode="directed" hypergraph="false">\n'
        for (name,id) in children:
            glx+='<node id="'+name+'">\n'
            glx+='<type xlink:href="/bodb/brain_region/'+str(id)+'/" xlink:type="simple"/>\n'
            glx+='</node>\n'
        glx+='</graph>\n'
        glx+='</node>\n'
    for sed in conn_seds:
        sourcename=str(sed.source_region.__unicode__())+' ('+sed.source_region.nomenclature.name+')'
        targetname=str(sed.target_region.__unicode__())+' ('+sed.target_region.nomenclature.name+')'
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
    document = models.ForeignKey('Document')
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
    model=models.ForeignKey('Model')
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