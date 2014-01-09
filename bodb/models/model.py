from django.core.urlresolvers import reverse
from django.db import models
from django.db.models import Q
from bodb.models import Document, Author, Literature, sendNotifications, BuildSED, TestSED, RelatedBrainRegion, UserSubscription
from mptt.fields import TreeForeignKey
from mptt.models import MPTTModel

class Module(MPTTModel,Document):
    parent = TreeForeignKey('self', null=True, blank=True, related_name='children')

    class Meta:
        app_label='bodb'

    def get_absolute_url(self):
        return reverse('module_view', kwargs={'pk': self.pk})

    def save(self, force_insert=False, force_update=False):
        super(Module, self).save()

        if self.public:
            for module in self.get_children().all():
                if not module.module.public:
                    module.module.public=1
                    module.module.save()

    def hierarchy_html(self, selected_id=None):
        html='<li>'
        if selected_id is not None:
            if selected_id==self.id:
                html+='<strong>%s</strong>' % self.title
            else:
                html+='<a href="/bodb/module/%d/">%s</a>' % (self.id, self.title)
        else:
            html+=self.title
        if self.get_children().count()>0:
            html+='<ul>'
            for submodule in self.get_children().all():
                html+=submodule.module.hierarchy_html(selected_id=selected_id)
            html+='</ul>'
        html+='</li>'
        return html


def compareModules(a, b):
    return cmp(a.module.title.lower, b.module.title.lower())


class ModelAuthor(models.Model):
    author = models.ForeignKey(Author)
    order = models.IntegerField()
    class Meta:
        app_label='bodb'
        ordering=['order']


class Model(Module):
    # model authors
    authors = models.ManyToManyField(ModelAuthor)
    # model URLs
    execution_url = models.CharField(max_length=200,blank=True,null=True)
    documentation_url = models.CharField(max_length=200,blank=True,null=True)
    description_url = models.CharField(max_length=200,blank=True,null=True)
    simulation_url = models.CharField(max_length=200,blank=True,null=True)
    modeldb_accession_number = models.IntegerField(blank=True,null=True)
    # related literature entries
    literature = models.ManyToManyField(Literature)

    class Meta:
        app_label='bodb'
        permissions= (
            ('save_model', 'Can save the model'),
            ('public_model', 'Can make the model public'),
            )

    def get_absolute_url(self):
        return reverse('model_view', kwargs={'pk': self.pk})

    # when printing an instance of this class, print "title (authors)"
    def __unicode__(self):
        return u"%s (%s)" % (self.title,self.author_names())

    # print authors
    def author_names(self):
        # author1 et al. if more than 3 authors
        if len(self.authors.all())>3:
            return u"%s et al." % self.authors.all()[0].author.last_name
        # author1 - author2 - author3 if 3 authors
        elif len(self.authors.all())>2:
            return u"%s - %s - %s" %(self.authors.all()[0].author.last_name, self.authors.all()[1].author.last_name,
                                     self.authors.all()[2].author.last_name)
        # author1 - author2 if 2 authors
        elif len(self.authors.all())>1:
            return u"%s - %s" %(self.authors.all()[0].author.last_name, self.authors.all()[1].author.last_name)
        # author1 last name if 1 author
        elif len(self.authors.all())>0:
            return self.authors.all()[0].author.last_name
        return ''

    def save(self, force_insert=False, force_update=False):
        notify=False

        # creating a new object
        if self.id is None:
            notify=True
        else:
            made_public=not Model.objects.get(id=self.id).public and self.public
            made_not_draft=Model.objects.get(id=self.id).draft and not int(self.draft)
            if made_public or made_not_draft:
                notify=True


        super(Model, self).save()

        if notify:
            # send notifications to subscribed users
            sendNotifications(self, 'Model')

    def hierarchy_html(self, selected_id=None):
        html='<ul><li>'
        if selected_id is not None:
            if selected_id==self.id:
                html+='<strong>%s</strong>' % str(self)
            else:
                html+='<a href="/bodb/model/%d/">%s</a>' % (self.id, str(self))
        else:
            html+=str(self)
        if self.get_children().count()>0:
            html+='<ul>'
            for submodule in self.get_children().all():
                html+=submodule.module.hierarchy_html(selected_id=selected_id)
            html+='</ul>'
        html+='</li></ul>'
        return html

    def get_modeldb_url(self):
        url='http://senselab.med.yale.edu/ModelDB/ShowModel.asp?model='+self.modeldb_accession_number
        return '<a href="%s" onclick="window.open(\'%s\'); return false;">View in ModelDB</a>' % (url,url)

    @staticmethod
    def get_literature_models(literature, user):
        return Model.objects.filter(Q(Q(literature=literature) & Document.get_security_q(user))).distinct()

    @staticmethod
    def get_model_list(models, user):
        profile=None
        active_workspace=None
        if user.is_authenticated() and not user.is_anonymous():
            profile=user.get_profile()
            active_workspace=profile.active_workspace
        model_list=[]
        for model in models:
            selected=active_workspace is not None and \
                     active_workspace.related_models.filter(id=model.id).count()>0
            is_favorite=profile is not None and profile.favorites.filter(id=model.id).count()>0
            subscribed_to_user=profile is not None and \
                               UserSubscription.objects.filter(subscribed_to_user=model.collator, user=user,
                                   model_type='Model').count()>0
            model_list.append([selected,is_favorite,subscribed_to_user,model])
        return model_list

    @staticmethod
    def get_tagged_models(name, user):
        return Model.objects.filter(Q(tags__name__icontains=name) & Document.get_security_q(user)).distinct()


class Variable(models.Model):
    """
    Module variable
    """
    VAR_TYPE_CHOICES = (
        ('Input', 'Input'),
        ('Output', 'Output'),
        ('State', 'State')
        )
    # module that variable belongs to
    module = models.ForeignKey('Module',null=True)
    # variable type - can be input, output, or state
    var_type = models.CharField(max_length=20, choices=VAR_TYPE_CHOICES)
    # data type
    data_type = models.CharField(max_length=200)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    class Meta:
        app_label='bodb'


def compareVariables(a, b):
    return cmp(a.name.lower(), b.name.lower())


# The relationship between a Document and a Model
class RelatedModel(models.Model):
    document = models.ForeignKey('Document')
    model = models.ForeignKey('Model', related_name='related_model', null=True)
    relationship = models.TextField(blank=True)

    class Meta:
        app_label='bodb'
        ordering=['model__title']

    @staticmethod
    def get_related_model_list(rmods, user):
        profile=None
        active_workspace=None
        if user.is_authenticated() and not user.is_anonymous():
            profile=user.get_profile()
            active_workspace=profile.active_workspace
        related_model_list=[]
        for rmod in rmods:
            selected=active_workspace is not None and \
                     active_workspace.related_models.filter(id=rmod.model.id).count()>0
            is_favorite=profile is not None and profile.favorites.filter(id=rmod.model.id).count()>0
            subscribed_to_user=profile is not None and \
                               UserSubscription.objects.filter(subscribed_to_user=rmod.model.collator, user=user,
                                   model_type='Model').count()>0
            related_model_list.append([selected,is_favorite,subscribed_to_user,rmod])
        return related_model_list

    @staticmethod
    def get_related_models(document, user):
        return RelatedModel.objects.filter(Q(Q(document=document) &
                                             Document.get_security_q(user, field='model'))).distinct()

    @staticmethod
    def get_reverse_related_model_list(rrmods, user):
        profile=None
        active_workspace=None
        if user.is_authenticated() and not user.is_anonymous():
            profile=user.get_profile()
            active_workspace=profile.active_workspace
        reverse_related_model_list=[]
        for rrmod in rrmods:
            selected=active_workspace is not None and \
                     active_workspace.related_models.filter(id=rrmod.document.id).count()>0
            is_favorite=profile is not None and profile.favorites.filter(id=rrmod.document.id).count()>0
            subscribed_to_user=profile is not None and \
                               UserSubscription.objects.filter(subscribed_to_user=rrmod.document.collator, user=user,
                                   model_type='Model').count()>0
            reverse_related_model_list.append([selected,is_favorite,subscribed_to_user,rrmod])
        return reverse_related_model_list

    @staticmethod
    def get_reverse_related_models(model, user):
        return RelatedModel.objects.filter(Q(Q(model=model) & Q(document__module__model__isnull=False) &
                                             Document.get_security_q(user, field='document'))).distinct()

    @staticmethod
    def get_sed_related_models(sed, user):
        related_models=[]
        bseds=BuildSED.objects.filter(Document.get_security_q(user, field='document') & Q(sed=sed)).distinct()
        for bsed in bseds:
            if Model.objects.filter(id=bsed.document.id).count():
                model=Model.objects.get(id=bsed.document.id)
                related_models.append(RelatedModel(document=sed, model=model, relationship='%s - %s' %
                                                                                           (bsed.relationship,
                                                                                            bsed.relevance_narrative)))

        tseds=TestSED.objects.filter(Document.get_security_q(user, field='model') & Q(sed=sed)).distinct()
        for tsed in tseds:
            related_models.append(RelatedModel(document=sed, model=tsed.model, relationship='%s - %s' %
                                                                                            (tsed.relationship,
                                                                                             tsed.relevance_narrative)))

        return related_models

    @staticmethod
    def get_brain_region_related_models(brain_region, user):
        related_regions=RelatedBrainRegion.objects.filter(Q(Q(document__module__model__isnull=False) &
                                                            Q(brain_region=brain_region) &
                                                            Document.get_security_q(user, field='document'))).distinct()
        related_models=[]
        for related_region in related_regions:
            related_models.append(RelatedModel(model=Model.objects.get(id=related_region.document.id),
                relationship=related_region.relationship))
        return related_models


def compareRelatedModels(a, b):
    return cmp(a.model.title.lower(), b.model.title.lower())


def find_similar_models(user, title, brief_description):
    similar=[]
    other_models=Model.objects.filter(Document.get_security_q(user)).distinct()
    for model in other_models:
        total_match=0
        for title_word in title.split(' '):
            if model.title.find(title_word)>=0:
                total_match+=1
        for desc_word in brief_description.split(' '):
            if model.brief_description.find(desc_word)>=0:
                total_match+=1
        similar.append((model,total_match))
    similar.sort(key=lambda tup: tup[1],reverse=True)
    return similar


def model_gxl(models, user):
    glx='<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n'
    glx+='<gxl xmlns="http://www.gupro.de/GXL/gxl-1.0.dtd" xmlns:xlink="http://www.w3.org/1999/xlink">\n'
    glx+='<graph id="model-map" edgeids="true" edgemode="directed" hypergraph="false">\n'
    for model in models:
        glx+='<node id="%d">\n' % model.id
        glx+='<graph id="%d_subgraph" edgeids="true" edgemode="directed" hypergraph="false">\n' % model.id
        glx+='<node id="%s">\n' % model.title
        glx+='<type xlink:href="/bodb/model/%d/" xlink:type="simple"/>\n' % model.id
        glx+='</node>\n'
        glx+='</graph>\n'
        glx+='</node>\n'

        conn_build_seds=BuildSED.get_connectivity_building_seds(model,user)
        for bsed in conn_build_seds:
            glx+='<node id="%d">\n' % bsed.sed.id
            glx+='<graph id="%d_subgraph" edgeids="true" edgemode="directed" hypergraph="false">\n' % bsed.sed.id
            glx+='<node id="%s">\n' % bsed.sed.title
            glx+='<type xlink:href="/bodb/sed/%d/" xlink:type="simple"/>\n' % bsed.sed.id
            glx+='</node>\n'
            glx+='</graph>\n'
            glx+='</node>\n'

        img_build_seds=BuildSED.get_imaging_building_seds(model,user)
        for bsed in img_build_seds:
            glx+='<node id="%d">\n' % bsed.sed.id
            glx+='<graph id="%d_subgraph" edgeids="true" edgemode="directed" hypergraph="false">\n' % bsed.sed.id
            glx+='<node id="%s">\n' % bsed.sed.title
            glx+='<type xlink:href="/bodb/sed/%d/" xlink:type="simple"/>\n' % bsed.sed.id
            glx+='</node>\n'
            glx+='</graph>\n'
            glx+='</node>\n'

        erp_build_seds=BuildSED.get_erp_building_seds(model,user)
        for bsed in erp_build_seds:
            glx+='<node id="%d">\n' % bsed.sed.id
            glx+='<graph id="%d_subgraph" edgeids="true" edgemode="directed" hypergraph="false">\n' % bsed.sed.id
            glx+='<node id="%s">\n' % bsed.sed.title
            glx+='<type xlink:href="/bodb/sed/%d/" xlink:type="simple"/>\n' % bsed.sed.id
            glx+='</node>\n'
            glx+='</graph>\n'
            glx+='</node>\n'

        gen_build_seds=BuildSED.get_generic_building_seds(model,user)
        for bsed in gen_build_seds:
            glx+='<node id="%d">\n' % bsed.sed.id
            glx+='<graph id="%d_subgraph" edgeids="true" edgemode="directed" hypergraph="false">\n' % bsed.sed.id
            glx+='<node id="%s">\n' % bsed.sed.title
            glx+='<type xlink:href="/bodb/sed/%d/" xlink:type="simple"/>\n' % bsed.sed.id
            glx+='</node>\n'
            glx+='</graph>\n'
            glx+='</node>\n'

        conn_test_seds=TestSED.get_connectivity_testing_seds(model,user)
        for tsed in conn_test_seds:
            glx+='<node id="%d">\n' % tsed.sed.id
            glx+='<graph id="%d_subgraph" edgeids="true" edgemode="directed" hypergraph="false">\n' % tsed.sed.id
            glx+='<node id="%s">\n' % tsed.sed.title
            glx+='<type xlink:href="/bodb/sed/%d/" xlink:type="simple"/>\n' % tsed.sed.id
            glx+='</node>\n'
            glx+='</graph>\n'
            glx+='</node>\n'

        img_test_seds=TestSED.get_imaging_testing_seds(model,user)
        for tsed in img_test_seds:
            glx+='<node id="%d">\n' % tsed.sed.id
            glx+='<graph id="%d_subgraph" edgeids="true" edgemode="directed" hypergraph="false">\n' % tsed.sed.id
            glx+='<node id="%s">\n' % tsed.sed.title
            glx+='<type xlink:href="/bodb/sed/%d/" xlink:type="simple"/>\n' % tsed.sed.id
            glx+='</node>\n'
            glx+='</graph>\n'
            glx+='</node>\n'

        erp_test_seds=TestSED.get_erp_testing_seds(model,user)
        for tsed in erp_test_seds:
            glx+='<node id="%d">\n' % tsed.sed.id
            glx+='<graph id="%d_subgraph" edgeids="true" edgemode="directed" hypergraph="false">\n' % tsed.sed.id
            glx+='<node id="%s">\n' % tsed.sed.title
            glx+='<type xlink:href="/bodb/sed/%d/" xlink:type="simple"/>\n' % tsed.sed.id
            glx+='</node>\n'
            glx+='</graph>\n'
            glx+='</node>\n'

        gen_test_seds=TestSED.get_generic_testing_seds(model,user)
        for tsed in gen_test_seds:
            glx+='<node id="%d">\n' % tsed.sed.id
            glx+='<graph id="%d_subgraph" edgeids="true" edgemode="directed" hypergraph="false">\n' % tsed.sed.id
            glx+='<node id="%s">\n' % tsed.sed.title
            glx+='<type xlink:href="/bodb/sed/%d/" xlink:type="simple"/>\n' % tsed.sed.id
            glx+='</node>\n'
            glx+='</graph>\n'
            glx+='</node>\n'

    for model in models:
        conn_build_seds=BuildSED.get_connectivity_building_seds(model,user)
        for bsed in conn_build_seds:
            glx+='<edge id="%d-%d" to="%s" from="%s">\n' % (model.id,bsed.sed.id,model.title,bsed.sed.title)
            glx+='<attr name="name"><string>%s</string></attr>\n' % bsed.relationship
            glx+='</edge>\n'

        img_build_seds=BuildSED.get_imaging_building_seds(model,user)
        for bsed in img_build_seds:
            glx+='<edge id="%d-%d" to="%s" from="%s">\n' % (model.id,bsed.sed.id,model.title,bsed.sed.title)
            glx+='<attr name="name"><string>%s</string></attr>\n' % bsed.relationship
            glx+='</edge>\n'

        erp_build_seds=BuildSED.get_erp_building_seds(model,user)
        for bsed in erp_build_seds:
            glx+='<edge id="%d-%d" to="%s" from="%s">\n' % (model.id,bsed.sed.id,model.title,bsed.sed.title)
            glx+='<attr name="name"><string>%s</string></attr>\n' % bsed.relationship
            glx+='</edge>\n'

        gen_build_seds=BuildSED.get_generic_building_seds(model,user)
        for bsed in gen_build_seds:
            glx+='<edge id="%d-%d" to="%s" from="%s">\n' % (model.id,bsed.sed.id,model.title,bsed.sed.title)
            glx+='<attr name="name"><string>%s</string></attr>\n' % bsed.relationship
            glx+='</edge>\n'

        conn_test_seds=TestSED.get_connectivity_testing_seds(model,user)
        for tsed in conn_test_seds:
            glx+='<edge id="%d-%d" to="%s" from="%s">\n' % (model.id,tsed.sed.id,model.title,tsed.sed.title)
            glx+='<attr name="name"><string>%s</string></attr>\n' % tsed.relationship
            glx+='</edge>\n'

        img_test_seds=TestSED.get_imaging_testing_seds(model,user)
        for tsed in img_test_seds:
            glx+='<edge id="%d-%d" to="%s" from="%s">\n' % (model.id,tsed.sed.id,model.title,tsed.sed.title)
            glx+='<attr name="name"><string>%s</string></attr>\n' % tsed.relationship
            glx+='</edge>\n'

        erp_test_seds=TestSED.get_erp_testing_seds(model,user)
        for tsed in erp_test_seds:
            glx+='<edge id="%d-%d" to="%s" from="%s">\n' % (model.id,tsed.sed.id,model.title,tsed.sed.title)
            glx+='<attr name="name"><string>%s</string></attr>\n' % tsed.relationship
            glx+='</edge>\n'

        gen_test_seds=TestSED.get_generic_testing_seds(model,user)
        for tsed in gen_test_seds:
            glx+='<edge id="%d-%d" to="%s" from="%s">\n' % (model.id,tsed.sed.id,model.title,tsed.sed.title)
            glx+='<attr name="name"><string>%s</string></attr>\n' % tsed.relationship
            glx+='</edge>\n'
    glx+='</graph>\n'
    glx+='</gxl>\n'
    return glx