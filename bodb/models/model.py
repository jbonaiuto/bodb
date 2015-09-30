from django.core.urlresolvers import reverse
from django.db import models
from django.db.models import Q
from bodb.models import Document, Author, Literature, sendNotifications, BuildSED, TestSED, RelatedBrainRegion, UserSubscription, stop_words
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

        for module in self.get_children().all():
            module.public=self.public
            module.draft=self.draft
            module.save()

    def hierarchy_html(self, selected_id=None):
        html='<li>'
        if selected_id is not None:
            if selected_id==self.id:
                html+='<strong>%s</strong>' % self.title
            else:
                html+='<a href="/bodb/module/%d/">%s</a>' % (self.id, self.title.encode("utf8"))
        else:
            html+=self.title
        children=self.get_children().all()
        if children.exists():
            html+='<ul>'
            for submodule in children:
                html+=submodule.hierarchy_html(selected_id=selected_id)
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
    execution_url = models.URLField(max_length=200,blank=True,null=True)
    documentation_url = models.URLField(max_length=200,blank=True,null=True)
    description_url = models.URLField(max_length=200,blank=True,null=True)
    simulation_url = models.URLField(max_length=200,blank=True,null=True)
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
            try:
                existing_model=Model.objects.get(id=self.id)
            except (Model.DoesNotExist, Model.MultipleObjectsReturned), err:
                existing_model=None
            if existing_model is not None:
                made_public=not existing_model.public and self.public
                made_not_draft=existing_model.draft and not int(self.draft)
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
                html+='<a href="/bodb/model/%d/">%s</a>' % (self.id, str(self).encode("utf8"))
        else:
            html+=str(self)
        children=self.get_children().all()
        if children.exists():
            html+='<ul>'
            for submodule in children:
                html+=submodule.hierarchy_html(selected_id=selected_id)
            html+='</ul>'
        html+='</li></ul>'
        return html

    def get_modeldb_url(self):
        if self.modeldb_accession_number is not None:
            url='http://senselab.med.yale.edu/ModelDB/ShowModel.asp?model='+str(self.modeldb_accession_number)
            return '<a href="%s" onclick="window.open(\'%s\'); return false;">View in ModelDB</a>' % (url,url)
        return ''

    @staticmethod
    def get_literature_models(literature, user):
        return Model.objects.filter(Q(Q(literature=literature) & Document.get_security_q(user))).distinct().select_related('collator').prefetch_related('authors__author').order_by('title')

    @staticmethod
    def get_model_list(models, workspace_models, fav_docs, subscriptions):
        model_list=[]
        for model in models:
            selected=model.id in workspace_models
            is_favorite=model.id in fav_docs
            subscribed_to_user=(model.collator.id,'Model') in subscriptions
            model_list.append([selected,is_favorite,subscribed_to_user,model])
        return model_list

    @staticmethod
    def get_tagged_models(name, user):
        return Model.objects.filter(Q(tags__name__iexact=name) & Document.get_security_q(user)).distinct().select_related('collator').prefetch_related('authors__author').order_by('title')

    @staticmethod
    def get_sed_map(models,user):
        map={}
        for model in models:
            map[model.id]=[]
            build_seds=BuildSED.get_building_seds(model,user)
            for build_sed in build_seds:
                if build_sed.sed:
                    map[model.id].append({'sed_id':build_sed.sed.id,'title':build_sed.sed.__unicode__(),
                                          'sed_desc':build_sed.sed.brief_description,
                                          'relationship':build_sed.relationship,
                                          'relevance_narrative': build_sed.relevance_narrative})
            test_seds=TestSED.get_testing_seds(model,user)
            for test_sed in test_seds:
                if test_sed.sed:
                    map[model.id].append({'sed_id':test_sed.sed.id,'title':test_sed.sed.__unicode__(),
                                          'sed_desc':test_sed.sed.brief_description,
                                          'relationship':test_sed.relationship,
                                          'relevance_narrative': test_sed.relevance_narrative})
        return map


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
    module = models.ForeignKey('Module',null=True, related_name='related_module')
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
    document = models.ForeignKey('Document', related_name='related_model_document')
    model = models.ForeignKey('Model', related_name='related_model', null=True)
    relationship = models.TextField(blank=True)

    class Meta:
        app_label='bodb'
        ordering=['model__title']

    def as_json(self):
        return {
            'id': self.id,
            'document': self.document.as_json(),
            'model': self.model.as_json(),
            'relationship': self.relationship
        }

    @staticmethod
    def get_related_model_list(rmods, workspace_models, fav_docs, subscriptions):
        related_model_list=[]
        for rmod in rmods:
            selected=rmod.model.id in workspace_models
            is_favorite=rmod.model.id in fav_docs
            subscribed_to_user=(rmod.model.collator.id, 'Model') in subscriptions
            related_model_list.append([selected,is_favorite,subscribed_to_user,rmod])
        return related_model_list

    @staticmethod
    def get_related_models(document, user):
        related_model_list=[]
        related_models=list(RelatedModel.objects.filter(Q(Q(document=document) &
                                                          Document.get_security_q(user, field='model'))).distinct().select_related('model__collator').prefetch_related('model__authors__author'))
        for related_model in related_models:
            related_model.reverse=False
            related_model_list.append(related_model)

        reverse_related_models=RelatedModel.objects.filter(Q(Q(model=document) & Q(document__module__model__isnull=False) &
                                                             Document.get_security_q(user, field='document'))).distinct().select_related('document__collator')
        for related_model in reverse_related_models:
            rmod=RelatedModel(id=related_model.id, model=Model.objects.get(id=related_model.document.id), document=related_model.model,
                relationship=related_model.relationship)
            rmod.reverse=True
            related_model_list.append(rmod)
        related_model_list.sort(key=RelatedModel.model_title)
        return related_model_list

    @staticmethod
    def get_reverse_related_model_list(rrmods, workspace_models, fav_docs, subscriptions):
        reverse_related_model_list=[]
        for rrmod in rrmods:
            rrmod.reverse=True
            selected=rrmod.document.id in workspace_models
            is_favorite=rrmod.document.id in fav_docs
            subscribed_to_user=(rrmod.document.collator.id, 'Model') in subscriptions
            reverse_related_model_list.append([selected,is_favorite,subscribed_to_user,rrmod])
        return reverse_related_model_list

    @staticmethod
    def get_sed_related_models(sed, user):
        related_models=[]
        bseds=BuildSED.objects.filter(Document.get_security_q(user, field='document') & Q(sed=sed)).distinct().select_related('document')
        for bsed in bseds:
            try:
                model=Model.objects.prefetch_related('authors__author').get(id=bsed.document.id)
            except (Model.DoesNotExist, Model.MultipleObjectsReturned), err:
                model=None
            if model is not None:
                rmod=RelatedModel(id=-1,document=sed, model=model, relationship='%s - %s' % (bsed.relationship,
                                                                                             bsed.relevance_narrative))
                rmod.reverse=True
                related_models.append(rmod)

        tseds=TestSED.objects.filter(Document.get_security_q(user, field='model') & Q(sed=sed)).distinct().select_related('model')
        for tsed in tseds:
            rmod=RelatedModel(id=-1, document=sed, model=tsed.model, relationship='%s - %s' % (tsed.relationship,
                                                                                               tsed.relevance_narrative))
            rmod.reverse=True
            related_models.append(rmod)
        related_models.sort(key=RelatedModel.model_title)

        return related_models

    @staticmethod
    def get_brain_region_related_models(brain_region, user):
        related_regions=RelatedBrainRegion.objects.filter(Q(Q(document__module__model__isnull=False) &
                                                            Q(brain_region=brain_region) &
                                                            Document.get_security_q(user, field='document'))).distinct().select_related('document').order_by('document__title')
        related_models=[]
        for related_region in related_regions:
            rmod=RelatedModel(id=-1, model=Model.objects.select_related('collator').prefetch_related('authors__author').get(id=related_region.document.id),
                relationship=related_region.relationship)
            rmod.reverse=True
            related_models.append(rmod)
        return related_models

    def model_title(self):
        return self.model.__unicode__()

    def model_description(self):
        return self.model.brief_description

    def get_relationship(self):
        return self.relationship


def compareRelatedModels(a, b):
    return cmp(a.model.title.lower(), b.model.title.lower())


def find_similar_models(user, title, brief_description):
    similar=[]
    other_models=Model.objects.filter(Document.get_security_q(user)).distinct()
    for model in other_models:
        total_match=0
        for title_word in title.split(' '):
            if not title_word in stop_words and model.title.find(title_word)>=0:
                total_match+=1
        for desc_word in brief_description.split(' '):
            if not desc_word in stop_words and model.brief_description.find(desc_word)>=0:
                total_match+=1
        if total_match>0:
            similar.append((model,total_match))
    similar.sort(key=lambda tup: tup[1],reverse=True)
    return similar


class ModelDBResult:
    def __init__(self):
        self.accession_number=''
        self.exists=False
        self.title=''
        self.description=''
        self.keywords=''
        self.literature=None
        self.authors=''