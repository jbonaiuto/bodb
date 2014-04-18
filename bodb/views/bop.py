from django.shortcuts import redirect
from django.views.generic import CreateView, UpdateView, DeleteView
from django.views.generic.detail import BaseDetailView
from django.views.generic.edit import BaseUpdateView, BaseCreateView
from bodb.forms.bop import BOPForm, BOPRelatedBOPFormSet
from bodb.forms.brain_region import RelatedBrainRegionFormSet
from bodb.forms.document import DocumentFigureFormSet
from bodb.forms.model import RelatedModelFormSet
from bodb.forms.sed import BuildSEDFormSet
from bodb.models import BOP, find_similar_bops, DocumentFigure, RelatedBOP, RelatedBrainRegion, RelatedModel, BuildSED, WorkspaceActivityItem, bop_gxl
from bodb.views.document import DocumentDetailView, DocumentAPIDetailView, DocumentAPIListView, generate_diagram_from_gxl
from bodb.views.main import BODBView
from uscbp.views import JSONResponseMixin

from bodb.serializers import BOPSerializer
from django.http import Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import mixins
from rest_framework import generics

class EditBOPMixin():
    model = BOP
    form_class = BOPForm
    template_name = 'bodb/bop/bop_detail.html'

    def form_valid(self, form):
        context = self.get_context_data()
        figure_formset = context['figure_formset']
        build_sed_formset = context['build_sed_formset']
        related_bop_formset = context['related_bop_formset']
        related_model_formset = context['related_model_formset']
        related_brain_region_formset = context['related_brain_region_formset']

        if figure_formset.is_valid() and related_bop_formset.is_valid() and related_brain_region_formset.is_valid() and\
           related_model_formset.is_valid() and build_sed_formset.is_valid():

            self.object = form.save(commit=False)
            # Set the collator if this is a new BOP
            if self.object.id is None:
                self.object.collator=self.request.user
            self.object.last_modified_by=self.request.user
            self.object.save()
            # Needed to save the literature and tags
            form.save_m2m()

            # save figures
            figure_formset.instance = self.object
            for figure_form in figure_formset.forms:
                if not figure_form in figure_formset.deleted_forms:
                    figure=figure_form.save(commit=False)
                    figure.document=self.object
                    figure.save()

            # delete removed figures
            for figure_form in figure_formset.deleted_forms:
                if figure_form.instance.id:
                    figure_form.instance.delete()

            # save build SEDs
            build_sed_formset.instance=self.object
            for build_sed_form in build_sed_formset.forms:
                if not build_sed_form in build_sed_formset.deleted_forms:
                    build_sed=build_sed_form.save(commit=False)
                    build_sed.document=self.object
                    build_sed.save()

            # delete removed build SEDs
            for build_sed_form in build_sed_formset.deleted_forms:
                if build_sed_form.instance.id:
                    build_sed_form.instance.delete()

            # save related BOPs
            related_bop_formset.instance=self.object
            for related_bop_form in related_bop_formset.forms:
                if not related_bop_form in related_bop_formset.deleted_forms:
                    related_bop=related_bop_form.save(commit=False)
                    related_bop.document=self.object
                    related_bop.save()

            # delete removed related BOPs
            for related_bop_form in related_bop_formset.deleted_forms:
                if related_bop_form.instance.id:
                    related_bop_form.instance.delete()

            # save related Models
            related_model_formset.instance=self.object
            for related_model_form in related_model_formset.forms:
                if not related_model_form in related_model_formset.deleted_forms:
                    related_model=related_model_form.save(commit=False)
                    related_model.document=self.object
                    related_model.save()

            # delete removed related BOPs
            for related_model_form in related_model_formset.deleted_forms:
                if related_model_form.instance.id:
                    related_model_form.instance.delete()

            # save related brain regions
            related_brain_region_formset.instance=self.object
            for related_brain_region_form in related_brain_region_formset.forms:
                if not related_brain_region_form in related_brain_region_formset.deleted_forms:
                    related_brain_region=related_brain_region_form.save(commit=False)
                    related_brain_region.document=self.object
                    related_brain_region.save()

            # delete removed related brain regions
            for related_brain_region_form in related_brain_region_formset.deleted_forms:
                if related_brain_region_form.instance.id:
                    related_brain_region_form.instance.delete()

            url=self.get_success_url()
            if context['ispopup']:
                url+='?_popup=1'
            return redirect(url)
        else:
            return self.render_to_response(self.get_context_data(form=form))

class CreateBOPView(EditBOPMixin,CreateView):

    def get_context_data(self, **kwargs):
        context = super(CreateBOPView,self).get_context_data(**kwargs)
        context['helpPage']='insert_data.html#insert-bop'
        context['figure_formset']=DocumentFigureFormSet(self.request.POST or None, self.request.FILES or None,
            prefix='figure')
        context['build_sed_formset']=BuildSEDFormSet(self.request.POST or None, prefix='build_sed')
        context['related_bop_formset']=BOPRelatedBOPFormSet(self.request.POST or None, prefix='related_bop')
        context['related_model_formset']=RelatedModelFormSet(self.request.POST or None, prefix='related_model')
        context['related_brain_region_formset']=RelatedBrainRegionFormSet(self.request.POST or None,
            prefix='related_brain_region')
        context['ispopup']=('_popup' in self.request.GET)
        context['bop_relationship']=True
        return context


class UpdateBOPView(EditBOPMixin,UpdateView):

    def get_context_data(self, **kwargs):
        context = super(UpdateBOPView,self).get_context_data(**kwargs)
        context['helpPage']='insert_data.html#insert-bop'
        context['figure_formset']=DocumentFigureFormSet(self.request.POST or None, self.request.FILES or None,
            prefix='figure', instance=self.object, queryset=DocumentFigure.objects.filter(document=self.object))
        context['build_sed_formset']=BuildSEDFormSet(self.request.POST or None, prefix='build_sed',
            instance=self.object, queryset=BuildSED.objects.filter(document=self.object))
        context['related_bop_formset']=BOPRelatedBOPFormSet(self.request.POST or None, prefix='related_bop',
            instance=self.object, queryset=RelatedBOP.objects.filter(document=self.object))
        context['related_model_formset']=RelatedModelFormSet(self.request.POST or None, prefix='related_model',
            instance=self.object, queryset=RelatedModel.objects.filter(document=self.object))
        context['related_brain_region_formset']=RelatedBrainRegionFormSet(self.request.POST or None,
            prefix='related_brain_region', instance=self.object,
            queryset=RelatedBrainRegion.objects.filter(document=self.object))
        context['references'] = self.object.literature.all()
        context['ispopup']=('_popup' in self.request.GET)
        context['bop_relationship']=True
        return context


class DeleteBOPView(DeleteView):
    model=BOP
    success_url = '/bodb/index.html'

class BOPAPIListView(DocumentAPIListView):
    queryset = BOP.objects.all()[:5]
    serializer_class = BOPSerializer
    
class BOPAPIDetailView(DocumentAPIDetailView):    
    queryset = BOP.objects.all()
    serializer_class = BOPSerializer

class BOPDetailView(DocumentDetailView):
    model = BOP
    template_name = 'bodb/bop/bop_view.html'
    
    def get_context_data(self, **kwargs):
        context = super(BOPDetailView, self).get_context_data(**kwargs)
        context['helpPage']='view_entry.html'
        user=self.request.user
        active_workspace=None
        if user.is_authenticated() and not user.is_anonymous():
            active_workspace=user.get_profile().active_workspace
        context['child_bops']=BOP.get_bop_list(BOP.get_child_bops(self.object,user), user)
        context['references'] = self.object.literature.all()
        if active_workspace is not None:
            context['selected']=active_workspace.related_bops.filter(id=self.object.id).count()>0
        context['bop_relationship']=True
        context['bopGraphId']='bopRelationshipDiagram'
        context['reverse_related_bops']=RelatedBOP.get_reverse_related_bop_list(RelatedBOP.get_reverse_related_bops(self.object,user),user)
        return context


class ToggleSelectBOPView(JSONResponseMixin,BaseUpdateView):
    model = BOP

    def get_context_data(self, **kwargs):
        context={'msg':u'No POST data sent.' }
        if self.request.is_ajax():
            bop=BOP.objects.get(id=self.kwargs.get('pk', None))
            # Load active workspace
            active_workspace=self.request.user.get_profile().active_workspace

            context={
                'bop_id': bop.id,
                'workspace': active_workspace.title
            }
            activity=WorkspaceActivityItem(workspace=active_workspace, user=self.request.user)
            if 'select' in self.request.POST:
                remove=self.request.POST['select']=='false'
            else:
                remove=bop in active_workspace.related_bops.all()
            if remove:
                active_workspace.related_bops.remove(bop)
                context['selected']=False
                activity.text='%s removed the BOP: <a href="%s">%s</a> from the workspace' % (self.request.user.username, bop.get_absolute_url(), bop.__unicode__())
            else:
                active_workspace.related_bops.add(bop)
                context['selected']=True
                activity.text='%s added the BOP: <a href="%s">%s</a> to the workspace' % (self.request.user.username, bop.get_absolute_url(), bop.__unicode__())
            activity.save()
            active_workspace.save()

        return context


class SimilarBOPView(JSONResponseMixin, BaseDetailView):

    def get(self, request, *args, **kwargs):
        # Load similar models
        title=self.request.GET['title']
        brief_desc=self.request.GET['brief_description']
        similar_bops=find_similar_bops(self.request.user, title, brief_desc)
        similar_bop_ids=[x.id for (x,matches) in similar_bops]
        similar_bop_titles=[str(x) for (x,matches) in similar_bops]

        data = {'similar_bop_ids': similar_bop_ids,
                'similar_bop_titles': similar_bop_titles}

        return self.render_to_response(data)


class BOPTaggedView(BODBView):
    template_name = 'bodb/bop/bop_tagged.html'

    def get_context_data(self, **kwargs):
        context=super(BOPTaggedView,self).get_context_data(**kwargs)
        name = self.kwargs.get('name', None)
        user=self.request.user
        context['helpPage']='tags.html'
        context['tag']=name
        context['tagged_items']=BOP.get_bop_list(BOP.get_tagged_bops(name,user),user)
        context['bopGraphId']='bopRelationshipDiagram'
        return context


class BOPDiagramView(JSONResponseMixin,BaseCreateView):
    model = BOP
    def get_context_data(self, **kwargs):
        context={'msg':u'No POST data sent.' }
        if self.request.is_ajax():
            graphTool=self.request.POST['graphTool']
            bops=BOP.objects.filter(document_ptr__in=self.request.POST.getlist('bopIds[]'))
            dot_xml=bop_gxl(bops, self.request.user)
            context['bopDiagram'], size, context['bopMap'] = generate_diagram_from_gxl(graphTool, dot_xml,
                self.request.user, ext=self.request.POST['graphID'])
            context['bopDiagramW']=size[0]
            context['bopDiagramH']=size[1]
            context['graphId']=self.request.POST['graphID']
        return context