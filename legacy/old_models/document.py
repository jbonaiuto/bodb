from django.contrib.auth.models import User
from django.db import models
from django.db.models.query_utils import Q
from django.template.defaultfilters import slugify
import time
import sys
from legacy.photologue.models import Gallery, Photo
from legacy.tagging.fields import TagField
from legacy.tagging.models import TaggedItem
from legacy.old_models.atlas import BrainRegion, RelatedBrainRegion, CoCoMacBrainRegion, ThreeDCoord
from legacy.old_models.literature import Literature, Journal, Book, Chapter, OrderedAuthor
from legacy.old_models.messaging import sendNotifications, Subscription
from legacy.old_models.workspace import Workspace
from legacy.util import create_gallery

# Document - base class for SED, SSR, Model, and BOP
class Document(models.Model):
    # user who added the entry
    collator = models.ForeignKey(User)
    title = models.CharField(max_length=200)
    brief_description = models.TextField(blank=True)
    # gallery of figures
    gallery = models.ForeignKey(Gallery, related_name='document_gallery')
    narrative = models.TextField(blank=True)
    # whether or not this entry is a draft
    draft = models.IntegerField(default=False)
    # whether or not this entry is public
    public = models.IntegerField(default=False)
    # date and time this entry was created
    creation_time = models.DateTimeField(auto_now_add=True,blank=True)
    # date and time this entry as last modified
    last_modified_time = models.DateTimeField(auto_now=True,blank=True)
    # When listing multiple records order by title
    class Meta:
        app_label='legacy_bodb'
        ordering=['title']

    # when printing instances of this class, print "title"
    def __unicode__(self):
        return u"%s" % self.title

    def get_collator_str(self):
        if self.collator.last_name:
            return '%s %s' % (self.collator.first_name, self.collator.last_name)
        else:
            return self.collator.username

    def get_created_str(self):
        return self.creation_time.strftime('%B %d, %Y')

    def get_modified_str(self):
        return self.last_modified_time.strftime('%B %d, %Y')

    def canEdit(self, user):
        if user.is_superuser:
            return True
        if self.collator.id==user.id:
            return True

    def save(self, force_insert=False, force_update=False):
        # creating a new object
        if self.id is None or self.gallery is None:
            # create gallery
            if len(self.title)<=50:
                self.gallery=create_gallery(self.title, slugify(self.title))
            else:
                self.gallery=create_gallery(self.title, slugify(self.title[:40]))
            self.gallery.save()

        super(Document, self).save()

    # Generates XML for the fields shared by all Document subtypes
    def data_xml(self):
        # Title and brief description are required - must print them out
        docml='<doc:title>'+unicode(self.title).encode('latin1','xmlcharrefreplace')+'</doc:title>\n'
        docml+='<doc:brief_description>'+unicode(self.brief_description).encode('latin1','xmlcharrefreplace').replace('&','&amp;')+'</doc:brief_description>\n'

        # Narrative is not required
        if self.narrative:
            docml+='<doc:narrative>'+unicode(self.narrative).encode('latin1','xmlcharrefreplace').replace('&','&amp;')+'</doc:narrative>\n'

        # XML for all figures
        if self.gallery.photos.all():

            # figures tag
            docml+='<doc:figures>\n'

            # for all figures in the gallery
            for photo in self.gallery.photos.all():
                docml+='<doc:figure id="'+str(photo.id)+'">\n'
                docml+='<doc:filename>'+photo.image_filename()+'</doc:filename>\n'
                docml+='<doc:title>'+unicode(photo.title).encode('latin1','xmlcharrefreplace')+'</doc:title>\n'
                docml+='<doc:title_slug>'+unicode(photo.title_slug).encode('latin1','xmlcharrefreplace')+'</doc:title_slug>\n'
                docml+='<doc:caption>'+unicode(photo.caption).encode('latin1','xmlcharrefreplace')+'</doc:caption>\n'
                if photo.tags:
                    docml+='<doc:tags>'+unicode(photo.tags).encode('latin1','xmlcharrefreplace')+'</doc:tags>\n'
                docml+='</doc:figure>\n'
            docml+='</doc:figures>\n'

        # XML for all references
        if self.literature.all():
            docml+='<doc:literatures>\n'

            # for all related references
            for reference in self.literature.all():
                # only export journal and book and book chapter references
                if Journal.objects.filter(id=reference.id):
                    reference=Journal.objects.get(id=reference.id)
                elif Book.objects.filter(id=reference.id):
                    reference=Book.objects.get(id=reference.id)
                elif Chapter.objects.filter(id=reference.id):
                    reference=Chapter.objects.get(id=reference.id)
                else:
                    continue
                docml+=reference.bibtexml_format()+'\n'
            docml+='</doc:literatures>\n'

        return docml

# A Brain Operating Principle (BOP): inherits from Document
class BOP(Document):
    # parent BOP
    parent = models.ForeignKey('self',null=True,related_name='bop_parent')
    # SEDs that support or set the scene for the BOP
    building_seds = models.ManyToManyField('BuildSED')
    # related BOP entries
    related_bops = models.ManyToManyField('RelatedBOP', related_name='related_bops')
    # related model entries
    related_models = models.ManyToManyField('RelatedModel')
    # related brain regions
    related_brain_regions = models.ManyToManyField('RelatedBrainRegion')
    # related literature entries
    literature = models.ManyToManyField(Literature)
    # entry tags
    tags = TagField()

    class Meta:
        app_label='legacy_bodb'
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
            made_public=not BOP.objects.get(id=self.id).public and self.public
            made_not_draft=BOP.objects.get(id=self.id).draft and not int(self.draft)
            if made_public or made_not_draft:
                notify=True

        super(BOP, self).save()

        if self.public:
            for building_sed in self.building_seds.all():
                if not building_sed.sed.public:
                    building_sed.sed.public=1
                    building_sed.sed.save()

        if notify:
            # send notifications to subscribed users
            sendNotifications(self, 'BOP')

    def get_literature(self, recursive, sed, ssr, user):
        return list(self.literature.all().distinct())

    def get_building_seds(self, user):
        bsed_q=Q()
        if user.is_authenticated() and not user.is_anonymous():
            if not user.is_superuser:
                own_entry_q=Q(sed__collator__id=user.id)
                public_q=Q(sed__public=1)
                group_q=Q(Q(sed__draft=0) & Q(sed__collator__groups__in=list(user.groups.all())))
                bsed_q=own_entry_q | public_q | group_q
        else:
            bsed_q=Q(sed__public=1)

        building_seds = list(self.building_seds.filter(bsed_q).distinct())

        return building_seds

    def get_related_bops(self, tag, reciprocal, user):
        rbop_q=Q()
        if user.is_authenticated() and not user.is_anonymous():
            if not user.is_superuser:
                own_entry_q=Q(bop__collator__id=user.id)
                public_q=Q(bop__public=1)
                group_q=Q(Q(bop__draft=0) & Q(bop__collator__groups__in=list(user.groups.all())))
                rbop_q=own_entry_q | group_q | public_q
        else:
            rbop_q=Q(bop__public=1)

        # load related BOPs
        related_bops = list(self.related_bops.filter(rbop_q).distinct())
        child_bops=BOP.objects.filter(parent__id=self.id)

        if tag:
            tag_related_bops = TaggedItem.objects.get_related(self, BOP)
            for related_bop in tag_related_bops:

                # whether or not BOP is public
                public=related_bop.public==True
                admin=False
                own=False
                group=False

                # if a user is logged in
                if user.is_authenticated() and not user.is_anonymous():
                    # check for admin status
                    admin=user.is_superuser
                    # check if BOP is owned by user
                    own=related_bop.collator.id==user.id
                    # check if user is in same group as collator
                    user_groups=list(user.groups.all())
                    collator_groups=list(related_bop.collator.groups.all())
                    intersection=filter(lambda x:x in user_groups, collator_groups)
                    group=related_bop.draft=False and len(intersection)>0

                # can view the BOP if admin, owner, its public, or if not a draft and collator is in same group
                if not related_bop in child_bops and (admin or own or public or group):
                    rb=RelatedBOP(bop=related_bop, relationship='tag similarity')
                    if rb not in related_bops:
                        related_bops.append(rb)

        if reciprocal:
            # load reciprocal relationships
            for related_bop in RelatedBOP.objects.filter(bop__id=self.id):
                rrbop_q=Q(related_bops__id=related_bop.id)
                if user.is_authenticated() and not user.is_anonymous():
                    if not user.is_superuser:
                        own_entry_q=Q(collator__id=user.id)
                        public_q=Q(public=1)
                        group_q=Q(Q(draft=0) & Q(collator__groups__in=list(user.groups.all())))
                        rrbop_q=rrbop_q & Q(own_entry_q | group_q | public_q)
                else:
                    rrbop_q=rrbop_q & Q(public=1)
                for b in BOP.objects.filter(rrbop_q):
                    if not b in child_bops:
                        rb=RelatedBOP(bop=b, relationship=related_bop.relationship)
                        if rb not in related_bops:
                            related_bops.append(rb)

        return related_bops

    def get_related_models(self, tag, reciprocal, user):
        rmod_q=Q()
        if user.is_authenticated() and not user.is_anonymous():
            if not user.is_superuser:
                own_entry_q=Q(model__collator__id=user.id)
                public_q=Q(model__public=1)
                group_q=Q(Q(model__draft=0) & Q(model__collator__groups__in=list(user.groups.all())))
                rmod_q=own_entry_q | group_q | public_q
        else:
            rmod_q=Q(bop__public=1)

        # load related Models
        related_models = list(self.related_models.filter(rmod_q).distinct())

        if tag:
            tag_related_models = TaggedItem.objects.get_related(self, Model)
            for related_model in tag_related_models:

                # whether or not BOP is public
                public=related_model.public==True
                admin=False
                own=False
                group=False

                # if a user is logged in
                if user.is_authenticated() and not user.is_anonymous():
                    # check for admin status
                    admin=user.is_superuser
                    # check if BOP is owned by user
                    own=related_model.collator.id==user.id
                    # check if user is in same group as collator
                    user_groups=list(user.groups.all())
                    collator_groups=list(related_model.collator.groups.all())
                    intersection=filter(lambda x:x in user_groups, collator_groups)
                    group=related_model.draft=False and len(intersection)>0

                # can view the BOP if admin, owner, its public, or if not a draft and collator is in same group
                if admin or own or public or group:
                    rm=RelatedModel(model=related_model, relationship='tag similarity')
                    if rm not in related_models:
                        related_models.append(rm)

        if reciprocal:
            # load reciprocal relationships
            for related_bop in RelatedBOP.objects.filter(bop__id=self.id):
                rrmod_q=Q(related_bops__id=related_bop.id)

                if user.is_authenticated() and not user.is_anonymous():
                    if not user.is_superuser:
                        own_entry_q=Q(collator__id=user.id)
                        public_q=Q(public=1)
                        group_q=Q(Q(draft=0) & Q(collator__groups__in=list(user.groups.all())))
                        rrmod_q=rrmod_q & Q(own_entry_q | group_q | public_q)
                else:
                    rrmod_q=rrmod_q & Q(public=1)
                for m in Model.objects.filter(rrmod_q):
                    rm=RelatedModel(model=m, relationship=related_bop.relationship)
                    if rm not in related_models:
                        related_models.append(rm)

        return related_models

    def get_related_brain_regions(self, tag, module, bop, user):
        related_brain_regions = list(self.related_brain_regions.all())

        if tag:
            tag_related_brain_regions = TaggedItem.objects.get_related(self, BrainRegion)
            for related_brain_region in tag_related_brain_regions:
                rb=RelatedBrainRegion(brain_region=related_brain_region, relationship='tag similarity')
                if rb not in related_brain_regions:
                    related_brain_regions.append(rb)
        return related_brain_regions

    def bopml_format(self):
        bopml='<bop public="'
        # Public attribute
        if self.public:
            bopml+='true'
        else:
            bopml+='false'

        # ID attribute
        bopml+='" id="'+str(self.id)+'">\n'
        bopml+=super(BOP,self).data_xml()

        if self.tags:
            bopml+='<doc:tags>'+unicode(self.tags).encode('latin1','xmlcharrefreplace')+'</doc:tags>\n'

        if self.parent:
            bopml+='<parent id="'+self.parent.id+'"/>\n'

        if self.building_seds.all():
            bopml+='<doc:building_seds>\n'
            for bsed in self.building_seds.all():
                bopml+=bsed.doc_ml()
            bopml+='</doc:building_seds>\n'

        if self.related_models.all():
            bopml+='<doc:related_models>\n'
            for rmod in self.related_models.all():
                bopml+=rmod.data_xml()
            bopml+='</doc:related_models>\n'
        if self.related_bops.all():
            bopml+='<doc:related_bops>\n'
            for rbop in self.related_bops.all():
                bopml+=rbop.data_xml()
            bopml+='</doc:related_bops>\n'
            # XML for related brain regions
        if self.related_brain_regions.all():
            bopml+='<doc:related_brain_regions>\n'

            # for each related brain region
            for related_region in self.related_brain_regions.all():
                bopml+=related_region.data_xml()
            bopml+='</doc:related_brain_regions>\n'

        bopml+='</bop>\n'
        return bopml

    @staticmethod
    def generate_xml(bops):
        xml='<?xml version="1.0" encoding="UTF-8"?>\n'
        xml+='<bops xmlns="http://bodb.usc.edu/bopml/" xmlns:sed="http://bodb.usc.edu/sedml/" xmlns:doc="http://bodb.usc.edu/docml/" xmlns:bibtex="http://bibtexml.sf.net/">\n'
        for bop in bops:
            xml+=bop.bopml_format()
        xml+='</bops>\n'
        return xml

def find_similar_bops(user, title, brief_description):
    similar=[]
    security_q=Q()
    if user.is_authenticated() and not user.is_anonymous():
        if not user.is_superuser:
            own_entry_q=Q(collator__id=user.id)
            public_q=Q(public=1)
            group_q=Q(Q(draft=0) & Q(collator__groups__in=list(user.groups.all())))
            security_q=own_entry_q | public_q | group_q
    else:
        security_q=Q(public=1)
    other_bops=BOP.objects.filter(security_q).distinct()
    for bop in other_bops:
        total_match=0
        for title_word in title.split(' '):
            if bop.title.find(title_word)>=0:
                total_match+=1
        for desc_word in brief_description.split(' '):
            if bop.brief_description.find(desc_word)>=0:
                total_match+=1
        similar.append((bop,total_match))
    similar.sort(key=lambda tup: tup[1],reverse=True)
    return similar

# Module variable
class Variable(models.Model):
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
        app_label='legacy_bodb'

    def data_xml(self):
        docml='<variable var_type="'+self.var_type.lower()+'" data_type="'+self.data_type+'" name="'+self.name+'">\n'
        if self.description:
            docml+='<description>'+unicode(self.description).encode('latin1','xmlcharrefreplace')+'</description>\n'
        docml+='</variable>\n'
        return docml


class Submodule(models.Model):
    module=models.ForeignKey('Module')
    class Meta:
        app_label='legacy_bodb'

    def modml_format(self):
        mod_ml='<submodule'
        mod_ml+=' id="'+str(self.id)+'">\n'
        mod_ml+=self.module.modml_format()
        mod_ml+='</submodule>\n'
        return mod_ml

# A submodule of a model: inherits from Document
class Module(Document):
    # Submodules
    submodules = models.ManyToManyField('Submodule', related_name='parent_modules')

    class Meta:
        app_label='legacy_bodb'

    def save(self, force_insert=False, force_update=False):
        super(Module, self).save()

        if self.public:
            for module in self.submodules.all():
                if not module.module.public:
                    module.module.public=1
                    module.module.save()

    def get_submodules(self, user):
        sub_q=Q()
        if user.is_authenticated() and not user.is_anonymous():
            if not user.is_superuser:
                own_entry_q=Q(module__collator__id=user.id)
                public_q=Q(module__public=1)
                group_q=Q(Q(module__draft=0) & Q(module__collator__groups__in=list(user.groups.all())))
                sub_q=own_entry_q | public_q | group_q
        else:
            sub_q=Q(module__public=1)

        submodules = list(self.submodules.filter(sub_q).distinct())

        return submodules

    def hierarchy_html(self, selected_id=None):
        html='<li>'
        if selected_id is not None:
            if selected_id==self.id:
                html+='<strong>%s</strong>' % self.title
            else:
                html+='<a href="/bodb/module/%d/">%s</a>' % (self.id, self.title)
        else:
            html+=self.title
        if self.submodules.count()>0:
            html+='<ul>'
            for submodule in self.submodules.all():
                html+=submodule.module.hierarchy_html(selected_id=selected_id)
            html+='</ul>'
        html+='</li>'
        return html

    def data_xml(self):
        mod_ml=super(Module, self).data_xml()
        #if self.parent:
        #    mod_ml+='<parent id="'+str(self.parent.id)+'"/>\n'
        variables=Variable.objects.filter(module__id=self.id)
        if variables:
            mod_ml+='<variables>\n'
            for var in variables:
                mod_ml+=var.data_xml()
            mod_ml+='</variables>\n'
        #submodules=Module.objects.filter(parent__id=self.id)
        if self.submodules.all():
            mod_ml+='<submodules>\n'
            for mod in self.submodules.all():
                mod_ml+=mod.modml_format()
            mod_ml+='</submodules>\n'
        return mod_ml

    def modml_format(self):
        mod_ml='<module public="'
        if self.public:
            mod_ml+='true'
        else:
            mod_ml+='false'
        mod_ml+='" id="'+str(self.id)+'">\n'
        mod_ml+=self.data_xml()
        mod_ml+='</module>\n'
        return mod_ml

# Model: inherits from Module
class Model(Module):
    # model authors
    authors = models.ManyToManyField(OrderedAuthor)
    # a flat list of all submodules
    all_submodules = models.ManyToManyField(Module, related_name='all_submodules')
    # list of related models
    related_models = models.ManyToManyField('RelatedModel', related_name='related_models')
    # list of related BOPs
    related_bops = models.ManyToManyField('RelatedBOP')
    # model URLs
    execution_url = models.CharField(max_length=200,blank=True,null=True)
    documentation_url = models.CharField(max_length=200,blank=True,null=True)
    description_url = models.CharField(max_length=200,blank=True,null=True)
    simulation_url = models.CharField(max_length=200,blank=True,null=True)
    # SEDs used to build the model
    building_seds = models.ManyToManyField('BuildSED')
    # SEDs used to test the model
    testing_seds = models.ManyToManyField('TestSED')
    # Model predictions
    predictions = models.ManyToManyField('Prediction')
    # related brain regions
    related_brain_regions = models.ManyToManyField('RelatedBrainRegion')
    # related literature entries
    literature = models.ManyToManyField(Literature)
    # entry tags
    tags = TagField()
    class Meta:
        app_label='legacy_bodb'
        permissions= (
            ('save_model', 'Can save the model'),
            ('public_model', 'Can make the model public'),
        )

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
            return u"%s - %s - %s" %(self.authors.all()[0].author.last_name, self.authors.all()[1].author.last_name, self.authors.all()[2].author.last_name)
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

        if self.public:
            for building_sed in self.building_seds.all():
                if not building_sed.sed.public:
                    building_sed.sed.public=1
                    building_sed.sed.save()

            for testing_sed in self.testing_seds.all():
                if not testing_sed.public:
                    testing_sed.public=1
                    testing_sed.save()

            for prediction in self.predictions.all():
                if not prediction.public:
                    prediction.public=1
                    prediction.save()
        if notify:
            # send notifications to subscribed users
            sendNotifications(self, 'Model')

    def get_related_models(self, tag, reciprocal, user):
        # get related models
        if user.is_authenticated() and not user.is_superuser:
            own_entry_q=Q(model__collator__id=user.id)
            public_q=Q(model__public=1)
            group_q=Q(Q(model__draft=0) & Q(model__collator__groups__in=list(user.groups.all())))
            rmod_q=own_entry_q | group_q | public_q
        else:
            rmod_q=Q(model__public=1)
        related_models = list(self.related_models.filter(rmod_q).distinct())

        if tag:
            # get models related by tags
            tag_related_models = TaggedItem.objects.get_related(self, Model)
            for related_model in tag_related_models:
                public=related_model.public==True
                admin=False
                own=False
                group=False

                # if a user is logged in
                if user.is_authenticated() and not user.is_anonymous():
                    # check for admin status
                    admin=user.is_superuser
                    # check if entry is owned by user
                    own=related_model.collator.id==user.id
                    # check if user is in same group as collator
                    user_groups=list(user.groups.all())
                    collator_groups=list(related_model.collator.groups.all())
                    intersection=filter(lambda x:x in user_groups, collator_groups)
                    group=related_model.draft=False and len(intersection)>0

                if admin or own or public or group:
                    rm=RelatedModel(model=related_model, relationship='tag similarity')
                    if rm not in related_models:
                        related_models.append(rm)

        if reciprocal:
            # load reciprocal relationships
            for related_model in RelatedModel.objects.filter(model__id=self.id):
                rrmod_q=Q(related_models__id=related_model.id)
                if user.is_authenticated() and not user.is_anonymous():
                    if not user.is_superuser:
                        own_entry_q=Q(collator__id=user.id)
                        public_q=Q(public=1)
                        group_q=Q(Q(draft=0) & Q(collator__groups__in=list(user.groups.all())))
                        rrmod_q=rrmod_q & Q(own_entry_q | group_q | public_q)
                else:
                    rrmod_q=rrmod_q & Q(public=1)
                for m in Model.objects.filter(rrmod_q):
                    rm=RelatedModel(model=m, relationship=related_model.relationship)
                    if rm not in related_models:
                        related_models.append(rm)

        return related_models

    def get_related_bops(self, tag, reciprocal, user):
        rbop_q=Q()
        if user.is_authenticated() and not user.is_anonymous():
            if not user.is_superuser:
                own_entry_q=Q(bop__collator__id=user.id)
                public_q=Q(bop__public=1)
                group_q=Q(Q(bop__draft=0) & Q(bop__collator__groups__in=list(user.groups.all())))
                rbop_q=own_entry_q | group_q | public_q
        else:
            rbop_q=Q(bop__public=1)
        related_bops = list(self.related_bops.filter(rbop_q).distinct())

        if tag:
            tag_related_bops = TaggedItem.objects.get_related(self, BOP)
            for related_bop in tag_related_bops:
                public=related_bop.public==True
                admin=False
                own=False
                group=False

                # if a user is logged in
                if user.is_authenticated() and not user.is_anonymous():
                    # check for admin status
                    admin=user.is_superuser
                    # check if entry is owned by user
                    own=related_bop.collator.id==user.id
                    # check if user is in same group as collator
                    user_groups=list(user.groups.all())
                    collator_groups=list(related_bop.collator.groups.all())
                    intersection=filter(lambda x:x in user_groups, collator_groups)
                    group=related_bop.draft=False and len(intersection)>0
                if admin or own or public or group:
                    rb=RelatedBOP(bop=related_bop, relationship='tag similarity')
                    if rb not in related_bops:
                        related_bops.append(rb)

        if reciprocal:
            # load reciprocal relationships
            for related_model in RelatedModel.objects.filter(model__id=self.id):
                rrbop_q=Q(related_models__id=related_model.id)
                if user.is_authenticated() and not user.is_anonymous():
                    if not user.is_superuser:
                        own_entry_q=Q(collator__id=user.id)
                        public_q=Q(public=1)
                        group_q=Q(Q(draft=0) & Q(collator__groups__in=list(user.groups.all())))
                        rrbop_q=rrbop_q & Q(own_entry_q | group_q | public_q)
                else:
                    rrbop_q=rrbop_q & Q(public=1)
                for b in BOP.objects.filter(rrbop_q):
                    rb=RelatedBOP(bop=b, relationship=related_model.relationship)
                    if rb not in related_bops:
                        related_bops.append(rb)

        return related_bops

    def get_building_seds(self, user):
        bsed_q=Q()
        if user.is_authenticated() and not user.is_anonymous():
            if not user.is_superuser:
                own_entry_q=Q(sed__collator__id=user.id)
                public_q=Q(sed__public=1)
                group_q=Q(Q(sed__draft=0) & Q(sed__collator__groups__in=list(user.groups.all())))
                bsed_q=own_entry_q | public_q | group_q
        else:
            bsed_q=Q(sed__public=1)

        building_seds = list(self.building_seds.filter(bsed_q).distinct())

        return building_seds


    def get_testing_seds(self, user):
        tsed_q=Q()
        if user.is_authenticated() and not user.is_anonymous():
            if not user.is_superuser:
                own_entry_q=Q(collator__id=user.id)
                public_q=Q(public=1)
                group_q=Q(Q(draft=0) & Q(collator__groups__in=list(user.groups.all())))
                tsed_q=Q(own_entry_q | public_q | group_q)
        else:
            tsed_q=Q(public=1)

        testing_seds = list(self.testing_seds.filter(tsed_q).distinct())

        return testing_seds

    def get_predictions(self, user):
        pred_q=Q()
        if user.is_authenticated() and not user.is_anonymous():
            if not user.is_superuser:
                own_entry_q=Q(collator__id=user.id)
                public_q=Q(public=1)
                group_q=Q(Q(draft=0) & Q(collator__groups__in=list(user.groups.all())))
                pred_q=own_entry_q | public_q | group_q
        else:
            pred_q=Q(public=1)

        predictions = list(self.predictions.filter(pred_q).distinct())

        return predictions

    def get_related_brain_regions(self, tag, sed, user):
        stime=time.time()
        related_brain_regions = list(self.related_brain_regions.all())
        if tag:
            tag_related_brain_regions = TaggedItem.objects.get_related(self, BrainRegion)
            for related_brain_region in tag_related_brain_regions:
                rb=RelatedBrainRegion(brain_region=related_brain_region, relationship='tag similarity')
                if rb not in related_brain_regions:
                    related_brain_regions.append(rb)
        etime=time.time()
        print >>sys.stderr, 'Getting base document related brain regions took %0.2f' % (etime-stime)

        if sed:
            stime=time.time()
            bsed_q=Q(sed__build_sed__model__id=self.id)
            tsed_q=Q(sed__test_sed__model__id=self.id)

            sed_q=Q(bsed_q | tsed_q)

            if user.is_authenticated() and not user.is_anonymous():
                if not user.is_superuser:
                    own_entry=Q(sed__collator__id=user.id)
                    public_q=Q(sed__public=1)
                    group_q=Q(Q(sed__draft=0) & Q(sed__collator__groups__in=list(user.groups.all())))
                    sed_q=Q(sed_q) & Q(own_entry | public_q | group_q)
            else:
                sed_q=Q(sed_q) & Q(sed__public=1)

            sed_regions=RelatedBrainRegion.objects.filter(sed_q).distinct()
            for region in sed_regions:
                if not region in related_brain_regions:
                    related_brain_regions.append(region)
            etime=time.time()
            print >>sys.stderr, 'Getting SED related brain regions took %0.2f' % (etime-stime)

        return related_brain_regions

    def get_literature(self, sed, ssr, user):
        lit_q=Q(model__id=self.id)
        if sed:
            bsed_q=Q(sed__build_sed__model__id=self.id)
            tsed_sed_q=Q(sed__test_sed__model__id=self.id)
            tsed_q=Q(testsed__model__id=self.id)
            if user.is_authenticated() and not user.is_anonymous():
                if not user.is_superuser:
                    own_entry=Q(sed__collator__id=user.id)
                    public_q=Q(sed__public=1)
                    group_q=Q(Q(sed__draft=0) & Q(sed__collator__groups__in=list(user.groups.all())))
                    bsed_q=bsed_q & Q(own_entry | public_q | group_q)
                    tsed_sed_q=tsed_sed_q & Q(own_entry | public_q | group_q)
                    own_entry=Q(testsed__collator__id=user.id)
                    public_q=Q(testsed__public=1)
                    group_q=Q(Q(testsed__draft=0) & Q(testsed__collator__groups__in=list(user.groups.all())))
                    tsed_q=tsed_q & Q(own_entry | public_q | group_q)
            else:
                bsed_q=bsed_q & Q(sed__public=1)
                tsed_sed_q=tsed_sed_q & Q(sed__public=1)
                tsed_q=tsed_q & Q(testsed__public=1)
            lit_q=lit_q | bsed_q | tsed_sed_q | tsed_q
        if ssr:
            ssr_q=Q(ssr__prediction__model__id=self.id)
            pred_q=Q(prediction__model__id=self.id)
            if user.is_authenticated() and not user.is_anonymous():
                if not user.is_superuser:
                    own_entry=Q(ssr__collator__id=user.id)
                    public_q=Q(ssr__public=1)
                    group_q=Q(Q(ssr__draft=0) & Q(ssr__collator__groups__in=list(user.groups.all())))
                    ssr_q=ssr_q & Q(own_entry | public_q | group_q)
                    own_entry=Q(prediction__collator__id=user.id)
                    public_q=Q(prediction__public=1)
                    group_q=Q(Q(prediction__draft=0) & Q(prediction__collator__groups__in=list(user.groups.all())))
                    pred_q=pred_q & Q(own_entry | public_q | group_q)
            else:
                ssr_q=ssr_q & Q(ssr__public=1)
                pred_q=pred_q & Q(prediction__public=1)

            lit_q=lit_q | ssr_q | pred_q

        return Literature.objects.filter(lit_q).distinct()

    def hierarchy_html(self, selected_id=None):
        html='<ul><li>'
        if selected_id is not None:
            if selected_id==self.id:
                html+='<strong>%s</strong>' % str(self)
            else:
                html+='<a href="/bodb/model/%d/">%s</a>' % (self.id, str(self))
        else:
            html+=str(self)
        if self.submodules.count()>0:
            html+='<ul>'
            for submodule in self.submodules.all():
                html+=submodule.module.hierarchy_html(selected_id=selected_id)
            html+='</ul>'
        html+='</li></ul>'
        return html

    def data_xml(self):
        doc_ml=super(Model,self).data_xml()
        if self.building_seds.all():
            doc_ml+='<doc:building_seds>\n'
            for bsed in self.building_seds.all():
                doc_ml+=bsed.doc_ml()
            doc_ml+='</doc:building_seds>\n'
        if self.testing_seds.all():
            doc_ml+='<doc:testing_seds>\n'
            for tsed in self.testing_seds.all():
                doc_ml+=tsed.doc_ml()
            doc_ml+='</doc:testing_seds>\n'
        if self.predictions.all():
            doc_ml+='<predictions>\n'
            for prediction in self.predictions.all():
                doc_ml+=prediction.data_xml()
            doc_ml+='</predictions>\n'
            # XML for related brain regions
        if self.related_brain_regions.all():
            doc_ml+='<doc:related_brain_regions>\n'

            # for each related brain region
            for related_region in self.related_brain_regions.all():
                doc_ml+=related_region.data_xml()
            doc_ml+='</doc:related_brain_regions>\n'
        if self.authors.all():
            doc_ml+='<authors>\n'
            for oauthor in self.authors.all():
                author=oauthor.author
                doc_ml+='<author id="'+str(author.id)+'">\n'
                if author.first_name:
                    doc_ml+='<first_name>'+unicode(author.first_name).encode('latin1','xmlcharrefreplace')+'</first_name>\n'
                if author.middle_name:
                    doc_ml+='<middle_name>'+unicode(author.middle_name).encode('latin1','xmlcharrefreplace')+'</middle_name>\n'
                if author.last_name:
                    doc_ml+='<last_name>'+unicode(author.last_name).encode('latin1','xmlcharrefreplace')+'</last_name>\n'
                doc_ml+='</author>\n'
            doc_ml+='</authors>\n'
        if self.execution_url or self.documentation_url or self.description_url or self.simulation_url:
            doc_ml+='<urls>\n'
            if self.execution_url:
                doc_ml+='<execution>'+self.execution_url+'</execution>\n'
            if self.documentation_url:
                doc_ml+='<documentation>'+self.documentation_url+'</documentation>\n'
            if self.description_url:
                doc_ml+='<description>'+self.description_url+'</description>\n'
            if self.simulation_url:
                doc_ml+='<simulation>'+self.simulation_url+'</simulation>\n'
            doc_ml+='</urls>\n'
        if self.related_models.all():
            doc_ml+='<doc:related_models>\n'
            for rmod in self.related_models.all():
                doc_ml+=rmod.data_xml()
            doc_ml+='</doc:related_models>\n'
        if self.related_bops.all():
            doc_ml+='<doc:related_bops>\n'
            for rbop in self.related_bops.all():
                doc_ml+=rbop.data_xml()
            doc_ml+='</doc:related_bops>\n'
        if self.tags:
            doc_ml+='<doc:tags>'+unicode(self.tags).encode('latin1','xmlcharrefreplace')+'</doc:tags>\n'
        return doc_ml

    def modml_format(self):
        mod_ml='<model public="'
        if self.public:
            mod_ml+='true'
        else:
            mod_ml+='false'
        mod_ml+='" id="'+str(self.id)+'">\n'
        mod_ml+=self.data_xml()
        mod_ml+='</model>\n'
        return mod_ml

    @staticmethod
    def generate_xml(models):
        xml='<?xml version="1.0" encoding="UTF-8"?>\n'
        xml+='<models xmlns="http://bodb.usc.edu/modelml/" xmlns:doc="http://bodb.usc.edu/docml/" xmlns:sed="http://bodb.usc.edu/sedml/" xmlns:ssr="http://bodb.usc.edu/ssrml/" xmlns:bibtex="http://bibtexml.sf.net/">\n'
        for model in models:
            xml+=model.modml_format()
        xml+='</models>\n'
        return xml

def find_similar_models(user, title, brief_description):
    similar=[]
    security_q=Q()
    if user.is_authenticated() and not user.is_anonymous():
        if not user.is_superuser:
            own_entry_q=Q(collator__id=user.id)
            public_q=Q(public=1)
            group_q=Q(Q(draft=0) & Q(collator__groups__in=list(user.groups.all())))
            security_q=own_entry_q | public_q | group_q
    else:
        security_q=Q(public=1)
    other_models=Model.objects.filter(security_q).distinct()
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


# The relationship between some record and a BOP
class RelatedBOP(models.Model):
    bop = models.ForeignKey('BOP', related_name='bop')
    relationship = models.TextField(blank=True)
    class Meta:
        app_label='legacy_bodb'
        ordering=['bop__title']

    def data_xml(self):
        doc_ml='<doc:related_bop id="'+str(self.id)+'">\n'
        doc_ml+='<doc:bop id="'+str(self.bop.id)+'"/>\n'
        if self.relationship:
            doc_ml+='<doc:relationship>'+unicode(self.relationship).encode('latin1','xmlcharrefreplace')+'</doc:relationship>\n'
        doc_ml+='</doc:related_bop>\n'
        return doc_ml

# The relationship between some record and a Model
class RelatedModel(models.Model):
    model = models.ForeignKey('Model', related_name='model')
    relationship = models.TextField(blank=True)
    class Meta:
        app_label='legacy_bodb'
        ordering=['model__title']

    def data_xml(self):
        doc_ml='<doc:related_model id="'+str(self.id)+'">\n'
        doc_ml+='<doc:model id="'+str(self.model.id)+'"/>\n'
        if self.relationship:
            doc_ml+='<doc:relationship>'+unicode(self.relationship).encode('latin1','xmlcharrefreplace')+'</doc:relationship>\n'
        doc_ml+='</doc:related_model>\n'
        return doc_ml


# Summary of Experimental Data (SED) - inherits from Document
class SED(Document):
    TYPE_CHOICES = (
        ('', ''),
        ('generic', 'generic'),
        ('brain imaging', 'imaging'),
        ('connectivity', 'connectivity'),
        ('event related potential', 'erp'),
    )
    type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    # entry tags
    tags = TagField()
    related_brain_regions = models.ManyToManyField('RelatedBrainRegion')
    # related literature entries
    literature = models.ManyToManyField(Literature)

    class Meta:
        app_label='legacy_bodb'
        permissions= (
            ('save_sed', 'Can save the SED'),
            ('public_sed', 'Can make the SED public'),
        )

    def save(self, force_insert=False, force_update=False):
        notify=False
        # creating a new object
        if self.id is None:
            notify=True
        else:
            made_public=not SED.objects.get(id=self.id).public and self.public
            made_not_draft=SED.objects.get(id=self.id).draft and not int(self.draft)
            if made_public or made_not_draft:
                notify=True

        super(SED, self).save()

        if notify:
            # send notifications to subscribed users
            sendNotifications(self, 'SED')

    def get_literature(self, recursive, sed, ssr, user):
        return list(self.literature.all().distinct())

    def get_related_brain_regions(self, tag, module, bop, user):
        related_brain_regions = list(self.related_brain_regions.all())

        if tag:
            tag_related_brain_regions = TaggedItem.objects.get_related(self, BrainRegion)
            for related_brain_region in tag_related_brain_regions:
                rb=RelatedBrainRegion(brain_region=related_brain_region, relationship='tag similarity')
                if rb not in related_brain_regions:
                    related_brain_regions.append(rb)

        mod_bsed_q=Q(model__building_seds__sed__id=self.id)
        mod_tsed_q=Q(model__testing_seds__sed__id=self.id)
        bop_bsed_q=Q(bop__building_seds__sed__id=self.id)

        if module:
            security_q=Q()
            if user.is_authenticated() and not user.is_anonymous():
                if not user.is_superuser:
                    own_entry_q=Q(model__collator__id=user.id)
                    public_q=Q(model__public=1)
                    group_q=Q(Q(model__draft=0) & Q(model__collator__groups__in=list(user.groups.all())))
                    security_q=own_entry_q | public_q | group_q
            else:
                security_q=Q(model__public=1)
            regions=RelatedBrainRegion.objects.filter(Q(Q(mod_bsed_q & security_q) | Q(mod_tsed_q & security_q)))
            for region in regions:
                if not region in related_brain_regions:
                    related_brain_regions.append(region)

        if bop:
            security_q=Q()
            if user.is_authenticated() and not user.is_anonymous():
                if not user.is_superuser:
                    own_entry_q=Q(bop__collator__id=user.id)
                    public_q=Q(bop__public=1)
                    group_q=Q(Q(bop__draft=0) & Q(bop__collator__groups__in=list(user.groups.all())))
                    security_q=own_entry_q | public_q | group_q
            else:
                security_q=Q(bop__public=1)
            regions=RelatedBrainRegion.objects.filter(Q(bop_bsed_q & security_q))
            for region in regions:
                if not region in related_brain_regions:
                    related_brain_regions.append(region)

        return related_brain_regions

    def get_related_models(self, user):

        security_q=Q()
        if user.is_authenticated() and not user.is_anonymous():
            if not user.is_superuser:
                own_entry_q=Q(collator__id=user.id)
                public_q=Q(public=1)
                group_q=Q(Q(draft=0) & Q(collator__groups__in=list(user.groups.all())))
                security_q=own_entry_q | public_q | group_q
        else:
            security_q=Q(public=1)

        bsed_q=Q(Q(building_seds__sed__id=self.id) & security_q)
        tsed_q=Q(Q(testing_seds__sed__id=self.id) & security_q)

        related_models=[]
        for model in Model.objects.filter(bsed_q | tsed_q).distinct():
            for bsed in model.building_seds.filter(sed__id=self.id):
                rm=RelatedModel(model=model, relationship=bsed.relevance_narrative)
                if not rm in related_models:
                    related_models.append(rm)
            for tsed in model.testing_seds.filter(sed__id=self.id):
                rm=RelatedModel(model=model, relationship=tsed.brief_description)
                if rm not in related_models:
                    related_models.append(rm)
        return related_models

    def get_related_bops(self, user):

        security_q=Q()
        if user.is_authenticated() and not user.is_anonymous():
            if not user.is_superuser:
                own_entry_q=Q(collator__id=user.id)
                public_q=Q(public=1)
                group_q=Q(Q(draft=0) & Q(collator__groups__in=list(user.groups.all())))
                security_q=own_entry_q | public_q | group_q
        else:
            security_q=Q(public=1)

        bsed_q=Q(Q(building_seds__sed__id=self.id) & security_q)

        related_bops=[]
        for bop in BOP.objects.filter(bsed_q).distinct():
            for bsed in bop.building_seds.filter(sed__id=self.id):
                rb=RelatedBOP(bop=bop, relationship=bsed.relevance_narrative)
                if rb not in related_bops:
                    related_bops.append(rb)

        return related_bops

    def get_related_seds(self, user):
        related_seds=[]
        tag_related_seds=TaggedItem.objects.get_related(self, SED)
        for related_sed in tag_related_seds:

            # whether or not SED is public
            public=related_sed.public==True
            admin=False
            own=False
            group=False

            # if a user is logged in
            if user.is_authenticated() and not user.is_anonymous():
                # check for admin status
                admin=user.is_superuser
                # check if SED is owned by user
                own=related_sed.collator.id==user.id
                # check if user is in same group as collator
                user_groups=list(user.groups.all())
                collator_groups=list(related_sed.collator.groups.all())
                intersection=filter(lambda x:x in user_groups, collator_groups)
                group=related_sed.draft=False and len(intersection)>0

            # can view the SED if admin, owner, its public, or if not a draft and collator is in same group
            if (admin or own or public or group) and related_sed not in related_seds:
                related_seds.append(related_sed)

        return related_seds

    def get_related_ssrs(self, tag, testsed, user):
        related_ssrs=[]

        if tag:
            tag_related_ssrs=TaggedItem.objects.get_related(self, SSR)
            for related_ssr in tag_related_ssrs:

                # whether or not SED is public
                public=related_ssr.public==True
                admin=False
                own=False
                group=False

                # if a user is logged in
                if user.is_authenticated() and not user.is_anonymous():
                    # check for admin status
                    admin=user.is_superuser
                    # check if SSR is owned by user
                    own=related_ssr.collator.id==user.id
                    # check if user is in same group as collator
                    user_groups=list(user.groups.all())
                    collator_groups=list(related_ssr.collator.groups.all())
                    intersection=filter(lambda x:x in user_groups, collator_groups)
                    group=related_ssr.draft=False and len(intersection)>0

                # can view the SSR if admin, owner, its public, or if not a draft and collator is in same group
                if (admin or own or public or group) and related_ssr not in related_ssrs:
                    related_ssrs.append(related_ssr)

        if testsed:
            tsed_q=Q(test_sed__sed__id=self.id)
            if user.is_authenticated() and not user.is_anonymous():
                if not user.is_superuser:
                    own_entry_q=Q(collator__id=user.id)
                    public_q=Q(public=1)
                    group_q=Q(Q(draft=0) & Q(collator__groups__in=list(user.groups.all())))
                    tsed_q=tsed_q & Q(own_entry_q | public_q | group_q)
            else:
                tsed_q=tsed_q & Q(public=1)

            ssrs=SSR.objects.filter(tsed_q)
            for ssr in ssrs:
                if not ssr in related_ssrs:
                    related_ssrs.append(ssr)

        return related_ssrs

    # Generates XML for the fields shared by all SED types
    def generic_data_xml(self):
        sedml=super(SED, self).data_xml()
        # XML for related brain regions
        if self.related_brain_regions.all():
            sedml+='<doc:related_brain_regions>\n'

            # for each related brain region
            for related_region in self.related_brain_regions.all():
                sedml+=related_region.data_xml()
            sedml+='</doc:related_brain_regions>\n'

        if self.tags:
            sedml+='<doc:tags>'+unicode(self.tags).encode('latin1','xmlcharrefreplace')+'</doc:tags>\n'
        return sedml

    ## Generate an XML file according to the SED schema for this SED
    def sedml_format(self, prefix=None):
        sedml=''
        if prefix is None:
            # SED tag
            sedml+='<sed type="generic" public="'
            # public attribute of the SED tag
            if self.public:
                sedml+='true'
            else:
                sedml+='false'
            # ID attribute of the SED tag
            sedml+='" id="'+str(self.id)+'">\n'

            # Generic SED tag
            sedml+='<sedGeneric>\n'
            sedml+=self.generic_data_xml()
            sedml+='</sedGeneric>\n'
            sedml+='</sed>\n'
        else:
            sedml+='<'+prefix+':sed type="generic" public="'
            # public attribute of the SED tag
            if self.public:
                sedml+='true'
            else:
                sedml+='false'
            # ID attribute of the SED tag
            sedml+='" id="'+str(self.id)+'">\n'

            # Generic SED tag
            sedml+='<'+prefix+':sedGeneric>\n'
            sedml+=self.generic_data_xml()
            sedml+='</'+prefix+':sedGeneric>\n'
            sedml+='</'+prefix+':sed>\n'

        return sedml

    @staticmethod
    def generate_xml(seds):
        xml='<?xml version="1.0" encoding="UTF-8"?>\n'
        xml+='<seds xmlns="http://bodb.usc.edu/sedml/" xmlns:doc="http://bodb.usc.edu/docml/" xmlns:bibtex="http://bibtexml.sf.net/">\n'
        for sed in seds:
            xml+=sed.sedml_format()
        xml+='</seds>\n'
        return xml

def find_similar_seds(user, title, brief_description):
    similar=[]
    security_q=Q()
    if user.is_authenticated() and not user.is_anonymous():
        if not user.is_superuser:
            own_entry_q=Q(collator__id=user.id)
            public_q=Q(public=1)
            group_q=Q(Q(draft=0) & Q(collator__groups__in=list(user.groups.all())))
            security_q=own_entry_q | public_q | group_q
    else:
        security_q=Q(public=1)
    other_seds=SED.objects.filter(security_q).distinct()
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


# A summary of connectivity data: inherits from SED
class ConnectivitySED(SED):
    source_region = models.ForeignKey('BrainRegion', related_name='source_region')
    target_region = models.ForeignKey('BrainRegion', related_name='target_region')

    class Meta:
        app_label='legacy_bodb'

    def save(self, force_insert=False, force_update=False):
        notify=False
        # creating a new object
        if self.id is None:
            notify=True
        else:
            made_public=not ConnectivitySED.objects.get(id=self.id).public and self.public
            made_not_draft=ConnectivitySED.objects.get(id=self.id).draft and not int(self.draft)
            if made_public or made_not_draft:
                notify=True

        super(ConnectivitySED, self).save()

        if notify:
            # send notifications to subscribed users
            sendNotifications(self, 'SED')

    # Generate XML for ConnectivitySE according to SED schema
    def sedml_format(self, prefix=None):

        if prefix is None:
            # SED tag
            sedml='<sed type="connectivity" public="'

            # Public attribute
            if self.public:
                sedml+='true'
            else:
                sedml+='false'

            # ID attribute
            sedml+='" id="'+str(self.id)+'">\n'

            sedml+='<sedConnectivity>\n'

            # Get XMl for fields shared with generic SED
            sedml+=super(ConnectivitySED,self).generic_data_xml()

            # Source region tag
            sedml+='<source_region>\n'
            sedml+='<brain_region id="'+str(self.source_region.id)+'"/>\n'
            cocomac_region=CoCoMacBrainRegion.objects.get(brain_region__id=self.source_region.id)
            cocomac_id=cocomac_region.cocomac_id.split('-',1)
            sedml+='<cocomac atlas="'+cocomac_id[0]+'" region="'+cocomac_id[1]+'"/>\n'
            sedml+='</source_region>\n'

            # Target region tag
            sedml+='<target_region>\n'
            sedml+='<brain_region id="'+str(self.target_region.id)+'"/>\n'
            cocomac_region=CoCoMacBrainRegion.objects.get(brain_region__id=self.target_region.id)
            cocomac_id=cocomac_region.cocomac_id.split('-',1)
            sedml+='<cocomac atlas="'+cocomac_id[0]+'" region="'+cocomac_id[1]+'"/>\n'
            sedml+='</target_region>\n'

            sedml+='</sedConnectivity>\n'
            sedml+='</sed>'
        else:
            # SED tag
            sedml='<'+prefix+':sed type="connectivity" public="'

            # Public attribute
            if self.public:
                sedml+='true'
            else:
                sedml+='false'

            # ID attribute
            sedml+='" id="'+str(self.id)+'">\n'

            sedml+='<'+prefix+':sedConnectivity>\n'

            # Get XMl for fields shared with generic SED
            sedml+=super(ConnectivitySED,self).generic_data_xml()

            # Source region tag
            sedml+='<'+prefix+':source_region>\n'
            sedml+='<'+prefix+':brain_region id="'+str(self.source_region.id)+'"/>\n'
            cocomac_region=CoCoMacBrainRegion.objects.get(brain_region__id=self.source_region.id)
            cocomac_id=cocomac_region.cocomac_id.split('-',1)
            sedml+='<'+prefix+':cocomac atlas="'+cocomac_id[0]+'" region="'+cocomac_id[1]+'"/>\n'
            sedml+='</'+prefix+':source_region>\n'

            # Target region tag
            sedml+='<'+prefix+':target_region>\n'
            sedml+='<'+prefix+':brain_region id="'+str(self.target_region.id)+'"/>\n'
            cocomac_region=CoCoMacBrainRegion.objects.get(brain_region__id=self.target_region.id)
            cocomac_id=cocomac_region.cocomac_id.split('-',1)
            sedml+='<'+prefix+':cocomac atlas="'+cocomac_id[0]+'" region="'+cocomac_id[1]+'"/>\n'
            sedml+='</'+prefix+':target_region>\n'

            sedml+='</'+prefix+':sedConnectivity>\n'
            sedml+='</'+prefix+':sed>'
        return sedml

    def cocomac_html_url(self):
        cocomac_url=''
        if CoCoMacBrainRegion.objects.filter(brain_region__id=self.source_region.id) and CoCoMacBrainRegion.objects.filter(brain_region__id=self.target_region.id):
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
        return cocomac_url

    def cocomac_xml_url(self):
        cocomac_url=''
        if CoCoMacBrainRegion.objects.filter(brain_region__id=self.source_region.id) and CoCoMacBrainRegion.objects.filter(brain_region__id=self.target_region.id):
            cocomac_url="http://cocomac.org/URLSearch.asp?Search=Connectivity&DataSet=PRIMPROJ&User=jbonaiuto&Password=4uhk48s3&OutputType=XML_Browser&SearchString="

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
        return cocomac_url


# ERP SED Model, inherits from SED
class ErpSED(SED):
    cognitive_paradigm=models.TextField()
    sensory_modality=models.TextField()
    response_modality=models.TextField()
    control_condition=models.TextField()
    experimental_condition=models.TextField()
    class Meta:
        app_label='legacy_bodb'

    def save(self, force_insert=False, force_update=False):
        notify=False
        # creating a new object
        if self.id is None:
            notify=True
        else:
            made_public=not ErpSED.objects.get(id=self.id).public and self.public
            made_not_draft=ErpSED.objects.get(id=self.id).draft and not int(self.draft)
            if made_public or made_not_draft:
                notify=True

        super(ErpSED, self).save()

        if notify:
            # send notifications to subscribed users
            sendNotifications(self, 'SED')


# ERP SED Component Model, 1-to-Many relationship with ERP SED Model objects
class ErpSEDComponent(models.Model):
    LATENCY_CHOICES = (
        ('exact', 'Exact'),
        ('approx', 'Approximate'),
        ('window', 'Time Window')
        )

    erp_sed=models.ForeignKey(ErpSED)
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

    interpretation=models.TextField(max_length=100)

    class Meta:
        app_label='legacy_bodb'


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
        app_label='legacy_bodb'

    def save(self, force_insert=False, force_update=False):
        notify=False
        # creating a new object
        if self.id is None:
            notify=True
        else:
            made_public=not BrainImagingSED.objects.get(id=self.id).public and self.public
            made_not_draft=BrainImagingSED.objects.get(id=self.id).draft and not int(self.draft)
            if made_public or made_not_draft:
                notify=True

        super(BrainImagingSED, self).save()

        if notify:
            # send notifications to subscribed users
            sendNotifications(self, 'SED')

    # Generate XMl for BrainImaging SED according to SED schema
    def sedml_format(self, prefix=None):

        if prefix is None:
            #SED tag
            sedml='<sed type="imaging" public="'

            # public attribute
            if self.public:
                sedml+='true'
            else:
                sedml+='false'

            # ID attribute
            sedml+='" id="'+str(self.id)+'">\n'

            sedml+='<sedImaging>\n'

            # Get XML for fields shared with generic SED
            sedml+=super(BrainImagingSED,self).generic_data_xml()

            # Method is required
            sedml+='<method>'+self.method+'</method>\n'

            # Control condition is optional
            if self.control_condition:
                sedml+='<control_condition>'+unicode(self.control_condition).encode('latin1','xmlcharrefreplace')+'</control_condition>\n'

            # Experimental condition is optional
            if self.experimental_condition:
                sedml+='<experimental_condition>'+unicode(self.experimental_condition).encode('latin1','xmlcharrefreplace')+'</experimental_condition>\n'

            # Atlas is required
            sedml+='<coord_space>'+self.coord_space.name+'</coord_space>\n'

            # Coordinates are optional
            sedCoords=SEDCoord.objects.filter(sed__id=self.id)
            if sedCoords:

                # Generate XML for data
                sedml+='<data>\n'

                # Generate meta XML
                if self.extra_header:
                    sedml+='<meta>\n'
                    sedml+='<extra_header>'+unicode(self.extra_header).encode('latin1','xmlcharrefreplace')+'</extra_header>\n'
                    sedml+='</meta>\n'

                # Generate XML for coordinates
                for coord in sedCoords.all():

                    # Coordinate tag
                    sedml+='<coordinate '
                    sedml+='x="'+str(coord.coord.x)+'" '
                    sedml+='y="'+str(coord.coord.y)+'" '
                    sedml+='z="'+str(coord.coord.z)+'" '
                    sedml+='coord_space="'+coord.coord_space.name+'" '
                    sedml+='rcbf="'+str(coord.rcbf)+'" '
                    sedml+='statistic_value="'+str(coord.statistic_value)+'" '
                    sedml+='statistic="'+coord.statistic+'" '
                    sedml+='hemisphere="'+coord.hemisphere+'" '
                    sedml+='named_brain_region="'+coord.named_brain_region+'" '
                    if self.extra_header:
                        sedml+='extra_data="'+coord.extra_data+'" '
                    sedml+='/>\n'
                sedml+='</data>\n'

            sedml+='</sedImaging>\n'
            sedml+='</sed>\n'
        else:
            #SED tag
            sedml='<'+prefix+':sed type="imaging" public="'

            # public attribute
            if self.public:
                sedml+='true'
            else:
                sedml+='false'

            # ID attribute
            sedml+='" id="'+str(self.id)+'">\n'

            sedml+='<'+prefix+':sedImaging>\n'

            # Get XML for fields shared with generic SED
            sedml+=super(BrainImagingSED,self).generic_data_xml()

            # Method is required
            sedml+='<'+prefix+':method>'+self.method+'</'+prefix+':method>\n'

            # Control condition is optional
            if self.control_condition:
                sedml+='<'+prefix+':control_condition>'+unicode(self.control_condition).encode('latin1','xmlcharrefreplace')+'</'+prefix+':control_condition>\n'

            # Experimental condition is optional
            if self.experimental_condition:
                sedml+='<'+prefix+':experimental_condition>'+unicode(self.experimental_condition).encode('latin1','xmlcharrefreplace')+'</'+prefix+':experimental_condition>\n'

            # Atlas is required
            sedml+='<'+prefix+':coord_space>'+self.coord_space.name+'</'+prefix+':coord_space>\n'

            # Coordinates are optional
            sedCoords=SEDCoord.objects.filter(sed__id=self.id)
            if sedCoords:

                # Generate XML for data
                sedml+='<'+prefix+':data>\n'

                # Generate meta XML
                if self.extra_header:
                    sedml+='<'+prefix+':meta>\n'
                    sedml+='<'+prefix+':extra_header>'+unicode(self.extra_header).encode('latin1','xmlcharrefreplace')+'</'+prefix+':extra_header>\n'
                    sedml+='</'+prefix+':meta>\n'

                # Generate XML for coordinates
                for coord in sedCoords.all():

                    # Coordinate tag
                    sedml+='<'+prefix+':coordinate '
                    sedml+='x="'+str(coord.coord.x)+'" '
                    sedml+='y="'+str(coord.coord.y)+'" '
                    sedml+='z="'+str(coord.coord.z)+'" '
                    sedml+='coord_space="'+coord.coord_space.name+'" '
                    sedml+='rcbf="'+str(coord.rcbf)+'" '
                    sedml+='statistic_value="'+str(coord.statistic_value)+'" '
                    sedml+='statistic="'+coord.statistic+'" '
                    sedml+='hemisphere="'+coord.hemisphere+'" '
                    sedml+='named_brain_region="'+coord.named_brain_region+'" '
                    if self.extra_header:
                        sedml+='extra_data="'+coord.extra_data+'" '
                    sedml+='/>\n'
                sedml+='</'+prefix+':data>\n'

            sedml+='</'+prefix+':sedImaging>\n'
            sedml+='</'+prefix+':sed>\n'

        return sedml

    def html_url_string(self):
        return ''

class BredeBrainImagingSED(BrainImagingSED):
    woexp=models.IntegerField()
    class Meta:
        app_label='legacy_bodb'

    def html_url_string(self):
        return '<a href="" onclick="window.open(\'http://neuro.imm.dtu.dk/services/brededatabase/WOEXP_'+str(self.woexp)+'.html\'); return false;">View in Brede</a>'

class BredeWikiBrainImagingSED(BredeBrainImagingSED):
    def html_url_string(self):
        url='http://neuro.imm.dtu.dk/wiki/'+self.title.replace(' ','_')
        return '<a href="" onclick="window.open(\''+url+'\'); return false;">View in Brede</a>'
    
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
    # coordinate space coordinate is from
    coord_space = models.ForeignKey('CoordinateSpace')
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
    # user who added the entry
    collator = models.ForeignKey(User)
    class Meta:
        app_label='legacy_bodb'

# A saved selection of atlas coordinates
class SavedSEDCoordSelection(models.Model):
    # user selection belongs to
    user = models.ForeignKey(User)
    workspace = models.ForeignKey(Workspace)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    # whether or not selection is currently loaded
    loaded = models.BooleanField(default=False)
    class Meta:
        app_label='legacy_bodb'

    def get_collator_str(self):
        if self.user.last_name:
            return '%s %s' % (self.user.first_name, self.user.last_name)
        else:
            return self.user.username

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
        app_label='legacy_bodb'

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

# An SED used to test a model prediction
class TestSED(Document):
    # the model prediction either explains or contradicts the SED
    RELATIONSHIP_CHOICES = (
        ('explanation', 'explanation'),
        ('contradiction', 'contradiction'),
    )
    # the SED
    sed = models.ForeignKey('SED', related_name='test_sed',null=True)
    # the SSR that either contradicts or explains the SED
    ssr = models.ForeignKey('SSR', related_name='test_sed',null=True)
    # the relationship between the SSR and SED
    relationship = models.CharField(max_length=30, choices=RELATIONSHIP_CHOICES)
    # related literature entries
    literature = models.ManyToManyField(Literature)

    class Meta:
        app_label='legacy_bodb'

    def save(self, force_insert=False, force_update=False):
        super(TestSED, self).save()

        if self.public:
            if not self.ssr.public:
                self.ssr.public=1
                self.ssr.save()
            if not self.sed.public:
                self.sed.public=1
                self.sed.save()

    def get_literature(self, recursive, sed, ssr, user):
        return list(self.literature.all().distinct())

    def doc_ml(self):
        doc_ml='<doc:testing_sed public="'
        if self.public:
            doc_ml+='true'
        else:
            doc_ml+='false'
        doc_ml+='" id="'+str(self.id)+'">\n'
        doc_ml+=super(TestSED,self).data_xml()
        doc_ml+=self.sed.sedml_format('sed')
        doc_ml+=self.ssr.ssrml_format('ssr')
        doc_ml+='<doc:relationship>'+self.relationship+'</doc:relationship>\n'
        doc_ml+='</doc:testing_sed>\n'
        return doc_ml


# An SED used to build a model or support a BOP
class BuildSED(models.Model):
    # the SED is either scene setting or supports some aspect of the model design
    RELATIONSHIP_CHOICES = (
        ('scene setting', 'scene setting'),
        ('support', 'support'),
    )
    # the SED
    sed = models.ForeignKey('SED', related_name='build_sed')
    # the relationship between the SED and model or BOP
    relationship = models.CharField(max_length=30, choices=RELATIONSHIP_CHOICES)
    # relevance narrative - how the SED relates to the model in detail
    relevance_narrative = models.TextField(blank=True)
    class Meta:
        app_label='legacy_bodb'
        ordering=['sed__title']

    def doc_ml(self):
        doc_ml='<doc:building_sed id="'+str(self.id)+'">\n'
        doc_ml+=self.sed.sedml_format('sed')
        doc_ml+='<doc:relationship>'+self.relationship+'</doc:relationship>\n'
        doc_ml+='<doc:relevance_narrative>'+unicode(self.relevance_narrative).encode('latin1','xmlcharrefreplace')+'</doc:relevance_narrative>\n'
        doc_ml+='</doc:building_sed>\n'
        return doc_ml

# Summary of Simulation Data (SSR) - inherits from Document
class SSR(Document):
    # entry tags
    tags = TagField()
    # related brain regions
    related_brain_regions = models.ManyToManyField('RelatedBrainRegion')
    # related literature entries
    literature = models.ManyToManyField(Literature)

    class Meta:
        app_label='legacy_bodb'
        permissions= (
            ('save_ssr', 'Can save the SSR'),
            ('public_ssr', 'Can make the SSR public'),
        )

    def save(self, force_insert=False, force_update=False):
        notify=False
        # creating a new object
        if self.id is None:
            notify=True
        else:
            made_public=not SSR.objects.get(id=self.id).public and self.public
            made_not_draft=SSR.objects.get(id=self.id).draft and not int(self.draft)
            if made_public or made_not_draft:
                notify=True

        super(SSR, self).save()

        if notify:
            # send notifications to subscribed users
            sendNotifications(self, 'SSR')

    def get_related_brain_regions(self, tag, module, bop, user):
        related_brain_regions = list(self.related_brain_regions.all())

        if tag:
            tag_related_brain_regions = TaggedItem.objects.get_related(self, BrainRegion)
            for related_brain_region in tag_related_brain_regions:
                rb=RelatedBrainRegion(brain_region=related_brain_region, relationship='tag similarity')
                if rb not in related_brain_regions:
                    related_brain_regions.append(rb)
        return related_brain_regions

    def get_related_ssrs(self, user):
        related_ssrs=[]
        tag_related_ssrs=TaggedItem.objects.get_related(self, SSR)
        for related_ssr in tag_related_ssrs:

            # whether or not SSR is public
            public=related_ssr.public==True
            admin=False
            own=False
            group=False

            # if a user is logged in
            if user.is_authenticated() and not user.is_anonymous():
                # check for admin status
                admin=user.is_superuser
                # check if SSR is owned by user
                own=related_ssr.collator.id==user.id
                # check if user is in same group as collator
                user_groups=list(user.groups.all())
                collator_groups=list(related_ssr.collator.groups.all())
                intersection=filter(lambda x:x in user_groups, collator_groups)
                group=related_ssr.draft=False and len(intersection)>0

            # can view the SSR if admin, owner, its public, or if not a draft and collator is in same group
            if (admin or own or public or group) and related_ssr not in related_ssrs:
                related_ssrs.append(related_ssr)

        return related_ssrs

    def get_related_seds(self, tag, testsed, user):
        related_seds=[]

        if tag:
            tag_related_seds=TaggedItem.objects.get_related(self, SED)
            for related_sed in tag_related_seds:

                # whether or not SED is public
                public=related_sed.public==True
                admin=False
                own=False
                group=False

                # if a user is logged in
                if user.is_authenticated() and not user.is_anonymous():
                    # check for admin status
                    admin=user.is_superuser
                    # check if SSR is owned by user
                    own=related_sed.collator.id==user.id
                    # check if user is in same group as collator
                    user_groups=list(user.groups.all())
                    collator_groups=list(related_sed.collator.groups.all())
                    intersection=filter(lambda x:x in user_groups, collator_groups)
                    group=related_sed.draft=False and len(intersection)>0

                # can view the SSR if admin, owner, its public, or if not a draft and collator is in same group
                if (admin or own or public or group) and related_sed not in related_seds:
                    related_seds.append(related_sed)

        if testsed:
            tsed_q=Q(test_sed__ssr__id=self.id)
            if user.is_authenticated() and not user.is_anonymous():
                if not user.is_superuser:
                    own_entry_q=Q(collator__id=user.id)
                    public_q=Q(public=1)
                    group_q=Q(Q(draft=0) & Q(collator__groups__in=list(user.groups.all())))
                    tsed_q=tsed_q & Q(own_entry_q | public_q | group_q)
            else:
                tsed_q=tsed_q & Q(public=1)

            seds=SED.objects.filter(tsed_q)
            for sed in seds:
                if not sed in related_seds:
                    related_seds.append(sed)

        return related_seds

    def get_related_models(self, user):

        security_q=Q()
        if user.is_authenticated() and not user.is_anonymous():
            if not user.is_superuser:
                own_entry_q=Q(collator__id=user.id)
                public_q=Q(public=1)
                group_q=Q(Q(draft=0) & Q(collator__groups__in=list(user.groups.all())))
                security_q=own_entry_q | public_q | group_q
        else:
            security_q=Q(public=1)

        tsed_q=Q(Q(testing_seds__ssr__id=self.id) & security_q)

        related_models=[]
        for model in Model.objects.filter(tsed_q).distinct():
            for tsed in model.testing_seds.filter(ssr__id=self.id):
                rm=RelatedModel(model=model, relationship=tsed.brief_description)
                if rm not in related_models:
                    related_models.append(rm)
        return related_models

    def get_literature(self, recursive, sed, ssr, user):
        return list(self.literature.all().distinct())

     # Generates XML for the fields shared by all SSR types
    def generic_data_xml(self):
        ssrml=super(SSR, self).data_xml()

        if self.tags:
            ssrml+='<doc:tags>'+unicode(self.tags).encode('latin1','xmlcharrefreplace')+'</doc:tags>\n'
            # XML for related brain regions
        if self.related_brain_regions.all():
            ssrml+='<doc:related_brain_regions>\n'

            # for each related brain region
            for related_region in self.related_brain_regions.all():
                ssrml+=related_region.data_xml()
            ssrml+='</doc:related_brain_regions>\n'
        return ssrml

    ## Generate an XML file according to the SSR schema for this SSR
    def ssrml_format(self, prefix=None):
        if prefix is None:
            # SSR tag
            ssrml='<ssr public="'
            # public attribute of the SSR tag
            if self.public:
                ssrml+='true'
            else:
                ssrml+='false'
            # ID attribute of the SSR tag
            ssrml+='" id="'+str(self.id)+'">\n'

            ssrml+=self.generic_data_xml()
            ssrml+='</ssr>\n'
        else:
            # SSR tag
            ssrml='<'+prefix+':ssr public="'
            # public attribute of the SSR tag
            if self.public:
                ssrml+='true'
            else:
                ssrml+='false'
            # ID attribute of the SSR tag
            ssrml+='" id="'+str(self.id)+'">\n'

            ssrml+=self.generic_data_xml()
            ssrml+='</'+prefix+':ssr>\n'

        return ssrml

    @staticmethod
    def generate_xml(ssrs):
        xml='<?xml version="1.0" encoding="UTF-8"?>\n'
        xml+='<ssrs xmlns="http://bodb.usc.edu/ssrml/" xmlns:doc="http://bodb.usc.edu/docml/" xmlns:bibtex="http://bibtexml.sf.net/">\n'
        for ssr in ssrs:
            xml+=ssr.ssrml_format()
        xml+='</ssrs>\n'
        return xml

def find_similar_ssrs(user, title, brief_description):
    similar=[]
    security_q=Q()
    if user.is_authenticated() and not user.is_anonymous():
        if not user.is_superuser:
            own_entry_q=Q(collator__id=user.id)
            public_q=Q(public=1)
            group_q=Q(Q(draft=0) & Q(collator__groups__in=list(user.groups.all())))
            security_q=own_entry_q | public_q | group_q
    else:
        security_q=Q(public=1)
    other_ssrs=SSR.objects.filter(security_q).distinct()
    for ssr in other_ssrs:
        total_match=0
        for title_word in title.split(' '):
            if ssr.title.find(title_word)>=0:
                total_match+=1
        for desc_word in brief_description.split(' '):
            if ssr.brief_description.find(desc_word)>=0:
                total_match+=1
        similar.append((ssr,total_match))
    similar.sort(key=lambda tup: tup[1],reverse=True)
    return similar

# A Prediction made by a model which may link to multiple SSRs
class Prediction(Document):
    # summaries of simulation data
    ssrs = models.ManyToManyField(SSR, blank=True)
    # entry tags
    tags = TagField()
    # related literature entries
    literature = models.ManyToManyField(Literature)

    class Meta:
        app_label='legacy_bodb'
        permissions= (
            ('save_prediction', 'Can save the Prediction'),
            ('public_prediction', 'Can make the Prediction public'),
        )

    def save(self, force_insert=False, force_update=False):
        notify=False
        # creating a new object
        if self.id is None:
            notify=True
        else:
            made_public=not Prediction.objects.get(id=self.id).public and self.public
            made_not_draft=Prediction.objects.get(id=self.id).draft and not int(self.draft)
            if made_public or made_not_draft:
                notify=True

        super(Prediction, self).save()

        if self.public:
            for ssr in self.ssrs.all():
                if not ssr.public:
                    ssr.public=1
                    ssr.save()

        if notify:
            # send notifications to subscribed users
            sendNotifications(self, 'Prediction')

    def get_related_predictions(self, user):
        related_predictions=[]
        tag_related_predictions=TaggedItem.objects.get_related(self, Prediction)
        for related_prediction in tag_related_predictions:

            # whether or not SSR is public
            public=related_prediction.public==True
            admin=False
            own=False
            group=False

            # if a user is logged in
            if user.is_authenticated() and not user.is_anonymous():
                # check for admin status
                admin=user.is_superuser
                # check if SSR is owned by user
                own=related_prediction.collator.id==user.id
                # check if user is in same group as collator
                user_groups=list(user.groups.all())
                collator_groups=list(related_prediction.collator.groups.all())
                intersection=filter(lambda x:x in user_groups, collator_groups)
                group=related_prediction.draft=False and len(intersection)>0

            # can view the SSR if admin, owner, its public, or if not a draft and collator is in same group
            if (admin or own or public or group) and related_prediction not in related_predictions:
                related_predictions.append(related_prediction)

        return related_predictions

    def get_related_models(self, user):

        security_q=Q()
        if user.is_authenticated() and not user.is_anonymous():
            if not user.is_superuser:
                own_entry_q=Q(collator__id=user.id)
                public_q=Q(public=1)
                group_q=Q(Q(draft=0) & Q(collator__groups__in=list(user.groups.all())))
                security_q=own_entry_q | public_q | group_q
        else:
            security_q=Q(public=1)

        pred_q=Q(Q(predictions__id=self.id) & security_q)

        related_models=[]
        models=list(Model.objects.filter(pred_q).distinct())
        for model in models:
            rm=RelatedModel(model=model, relationship='Model prediction')
            if rm not in related_models:
                related_models.append(rm)

        return related_models

    def get_literature(self, recursive, sed, ssr, user):
        return list(self.literature.all().distinct())

    def data_xml(self):
        mod_ml='<prediction public="'
        if self.public:
            mod_ml+='true'
        else:
            mod_ml+='false'
        mod_ml+='" id="'+str(self.id)+'">\n'
        mod_ml+=super(Prediction,self).data_xml()
        if self.tags:
            mod_ml+='<doc:tags>'+unicode(self.tags).encode('latin1','xmlcharrefreplace')+'</doc:tags>\n'
        if self.ssrs.all():
            mod_ml+='<ssrs>\n'
            for ssr in self.ssrs.all():
                mod_ml+=ssr.ssrml_format('ssr')
            mod_ml+='</ssrs>\n'
        mod_ml+='</prediction>\n'
        return mod_ml

class PhotoCollator(models.Model):
    collator = models.ForeignKey(User)
    photo = models.ForeignKey(Photo)
    class Meta:
        app_label='bodb'

def compareVariables(a, b):
    return cmp(a.name.lower(), b.name.lower())


def compareBuildSEDs(a, b):
    return cmp(a.sed.title.lower(), b.sed.title.lower())


def compareSubmodules(a, b):
    return cmp(a.module.title.lower, b.module.title.lower())

def compareDocuments(a, b):
    return cmp(a.title.lower(), b.title.lower())


def compareRelatedBops(a, b):
    return cmp(a.bop.title.lower(), b.bop.title.lower())


def compareRelatedModels(a, b):
    return cmp(a.model.title.lower(), b.model.title.lower())

def compareRelatedModels(a, b):
    return cmp(a.model.title.lower(), b.model.title.lower())


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


def fix_public_doc_bug():
    models=Model.objects.filter(public=1)
    for model in models:
        for submodule in model.all_submodules.all():
            if not submodule.public:
                submodule.public=1
                submodule.save()
        for building_sed in model.building_seds.all():
            if not building_sed.sed.public:
                building_sed.sed.public=1
                building_sed.sed.save()
        for testing_sed in model.testing_seds.all():
            if not testing_sed.public:
                testing_sed.public=1
                testing_sed.save()
            if not testing_sed.sed.public:
                testing_sed.sed.public=1
                testing_sed.sed.save()
            if not testing_sed.ssr.public:
                testing_sed.ssr.public=1
                testing_sed.ssr.save()
        for prediction in model.predictions.all():
            if not prediction.public:
                prediction.public=1
                prediction.save()
            for ssr in prediction.ssrs.all():
                if not ssr.public:
                    ssr.public=1
                    ssr.save()

def fix_draft_doc_bug():
    models=Model.objects.filter(draft=0)
    for model in models:
        for submodule in model.all_submodules.all():
            if submodule.draft:
                submodule.draft=0
                submodule.save()
        for building_sed in model.building_seds.all():
            if building_sed.sed.draft:
                building_sed.sed.draft=0
                building_sed.sed.save()
        for testing_sed in model.testing_seds.all():
            if testing_sed.draft:
                testing_sed.draft=0
                testing_sed.save()
            if testing_sed.sed.draft:
                testing_sed.sed.draft=0
                testing_sed.sed.save()
            if testing_sed.ssr.draft:
                testing_sed.ssr.draft=0
                testing_sed.ssr.save()
        for prediction in model.predictions.all():
            if prediction.draft:
                prediction.draft=0
                prediction.save()
            for ssr in prediction.ssrs.all():
                if ssr.draft:
                    ssr.draft=0
                    ssr.save()

def optimize_model_module():
    models=Model.objects.filter(draft=0)
    for model in models:
        module=Module.objects.get(id=model.id)
        for building_sed in module.building_seds.all():
            model.building_seds.add(building_sed)
            module.building_seds.remove(building_sed)
        for testing_sed in module.testing_seds.all():
            model.testing_seds.add(testing_sed)
            module.testing_seds.remove(testing_sed)
        for prediction in module.predictions.all():
            model.predictions.add(prediction)
            module.predictions.remove(prediction)
        for related_brain_region in module.related_brain_regions.all():
            model.related_brain_regions.add(related_brain_region)
            module.related_brain_regions.remove(related_brain_region)
        for lit in module.literature.all():
            model.literature.add(lit)
            module.literature.remove(lit)
        for submodule in model.all_submodules.all():
            for building_sed in submodule.building_seds.all():
                model.building_seds.add(building_sed)
                submodule.building_seds.remove(building_sed)
            for testing_sed in submodule.testing_seds.all():
                model.testing_seds.add(testing_sed)
                submodule.testing_seds.remove(testing_sed)
            for prediction in submodule.predictions.all():
                model.predictions.add(prediction)
                submodule.predictions.remove(prediction)
            for related_brain_region in submodule.related_brain_regions.all():
                model.related_brain_regions.add(related_brain_region)
                submodule.related_brain_regions.remove(related_brain_region)
            for lit in submodule.literature.all():
                model.literature.add(lit)
                submodule.literature.remove(lit)
            submodule.save()
        model.save()
