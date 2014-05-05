from django.db.models import Q
from django.shortcuts import redirect
from django.views.generic import TemplateView
from django.views.generic.detail import BaseDetailView
from django.views.generic.edit import BaseUpdateView, CreateView, UpdateView, DeleteView, BaseCreateView
from bodb.forms.bop import RelatedBOPFormSet
from bodb.forms.brain_region import RelatedBrainRegionFormSet
from bodb.forms.document import DocumentFigureFormSet
from bodb.forms.model import ModelForm, VariableFormSet, RelatedModelFormSet, ModelAuthorFormSet, ModuleFormSet, ModuleForm
from bodb.forms.sed import TestSEDFormSet, BuildSEDFormSet
from bodb.forms.ssr import PredictionFormSet
from bodb.models import Model, DocumentFigure, RelatedBOP, RelatedBrainRegion, find_similar_models, Variable, RelatedModel, ModelAuthor, Author, Module, BuildSED, TestSED, SED, WorkspaceActivityItem, Document, model_gxl, Literature, UserSubscription
from bodb.models.ssr import SSR, Prediction
from bodb.views.document import DocumentAPIListView, DocumentAPIDetailView, DocumentDetailView, generate_diagram_from_gxl
from bodb.views.main import BODBView
from uscbp.views import JSONResponseMixin

from bodb.serializers import ModelSerializer
from django.http import Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import mixins
from rest_framework import generics

class EditModelMixin():
    model = Model
    form_class = ModelForm
    template_name = 'bodb/model/model_detail.html'

    def form_valid(self, form):
        context = self.get_context_data()
        model_author_formset = context['model_author_formset']
        figure_formset = context['figure_formset']
        build_sed_formset = context['build_sed_formset']
        test_sed_formset = context['test_sed_formset']
        prediction_formset = context['prediction_formset']
        related_bop_formset = context['related_bop_formset']
        related_model_formset = context['related_model_formset']
        related_brain_region_formset = context['related_brain_region_formset']
        input_formset=context['input_formset']
        output_formset=context['output_formset']
        state_formset=context['state_formset']
        module_formset=context['module_formset']

        if model_author_formset.is_valid() and figure_formset.is_valid() and related_bop_formset.is_valid() and\
           related_brain_region_formset.is_valid() and related_model_formset.is_valid() and\
           input_formset.is_valid() and output_formset.is_valid() and state_formset.is_valid() and\
           module_formset.is_valid() and build_sed_formset.is_valid() and prediction_formset.is_valid() and\
           test_sed_formset.is_valid():

            self.object = form.save(commit=False)
            # Set collator if this is a new model
            if self.object.id is None:
                self.object.collator=self.request.user
            self.object.last_modified_by=self.request.user
            self.object.save()
            # Needed to save literature and tags
            form.save_m2m()

            # save authors
            for author_form in model_author_formset.forms:
                if not author_form in model_author_formset.deleted_forms:
                    model_author=author_form.save(commit=False)
                    author=Author(first_name=author_form.cleaned_data['author_first_name'],
                        middle_name=author_form.cleaned_data['author_middle_name'],
                        last_name=author_form.cleaned_data['author_last_name'],
                        alias=author_form.cleaned_data['author_alias'],
                        email=author_form.cleaned_data['author_email'],
                        homepage=author_form.cleaned_data['author_homepage'])
                    if 'author' in author_form.cleaned_data and author_form.cleaned_data['author'] is not None:
                        author=author_form.cleaned_data['author']
                        author.first_name=author_form.cleaned_data['author_first_name']
                        author.middle_name=author_form.cleaned_data['author_middle_name']
                        author.last_name=author_form.cleaned_data['author_last_name']
                        author.alias=author_form.cleaned_data['author_alias']
                        author.email=author_form.cleaned_data['author_email']
                        author.homepage=author_form.cleaned_data['author_homepage']
                    author.save()
                    model_author.author=author
                    model_author.save()
                    self.object.authors.add(model_author)

            # remove authors
            for author_form in model_author_formset.deleted_forms:
                if author_form.instance.id:
                    author_form.instance.delete()

            # Save after modifying authors
            self.object.save()

            # save modules
            for module_form in module_formset.forms:
                if not module_form in module_formset.deleted_forms:
                    module=module_form.save(commit=False)
                    # Set module parent and collator if this is a new module
                    if module.id is None:
                        module.parent=self.object
                        module.collator=self.object.collator
                    module.last_modified_by=self.request.user
                    module.draft=self.object.draft
                    module.public=self.object.public
                    module.save()

            # remove modules
            for module_form in module_formset.deleted_forms:
                if module_form.instance.id:
                    module_form.isntance.delete()

            # save predictions
            prediction_formset.instance = self.object
            for prediction_form in prediction_formset.forms:
                if not prediction_form in prediction_formset.deleted_forms:
                    prediction=prediction_form.save(commit=False)
                    # Set prediction model and collator if this is a new prediction
                    if prediction.id is None:
                        prediction.model=self.object
                        prediction.collator=self.object.collator
                    prediction.last_modified_by=self.request.user
                    prediction.draft=self.object.draft
                    prediction.public=self.object.public
                    prediction.save()

                    # save prediction SSRs
                    for predictionssr_form in prediction_form.nested.forms:
                        if not predictionssr_form in prediction_form.nested.deleted_forms:
                            predictionssr=predictionssr_form.save(commit=False)
                            predictionssr.prediction=prediction
                            ssr=SSR(title=predictionssr_form.cleaned_data['ssr_title'],
                                brief_description=predictionssr_form.cleaned_data['ssr_brief_description'])
                            # Update ssr if editing existing one
                            if 'ssr' in predictionssr_form.cleaned_data and\
                               predictionssr_form.cleaned_data['ssr'] is not None:
                                ssr=predictionssr_form.cleaned_data['ssr']
                                ssr.title=predictionssr_form.cleaned_data['ssr_title']
                                ssr.brief_description=predictionssr_form.cleaned_data['ssr_brief_description']
                            # Set collator if this is a new SSR
                            else:
                                ssr.collator=self.object.collator
                            ssr.last_modified_by=self.request.user
                            ssr.draft=self.object.draft
                            ssr.public=self.object.public
                            ssr.save()
                            predictionssr.ssr=ssr
                            predictionssr.save()

                    # remove prediction SSRs
                    for predictionssr_form in prediction_form.nested.deleted_forms:
                        if predictionssr_form.instance.id:
                            predictionssr_form.instance.delete()

            # remove predictions
            for prediction_form in prediction_formset.deleted_forms:
                if prediction_form.instance.id:
                    prediction_form.instance.delete()

            # save test SEDs
            test_sed_formset.instance = self.object
            for test_sed_form in test_sed_formset.forms:
                if not test_sed_form in test_sed_formset.deleted_forms:
                    test_sed=test_sed_form.save(commit=False)
                    test_sed.model=self.object
                    test_sed.save()

                    # save testSED SSRs
                    for testsedssr_form in test_sed_form.nested.forms:
                        if not testsedssr_form in test_sed_form.nested.deleted_forms:
                            testsedssr=testsedssr_form.save(commit=False)
                            testsedssr.test_sed=test_sed
                            ssr=SSR(title=testsedssr_form.cleaned_data['ssr_title'],
                                brief_description=testsedssr_form.cleaned_data['ssr_brief_description'])
                            # Update ssr if editing existing one
                            if 'ssr' in testsedssr_form.cleaned_data and\
                               testsedssr_form.cleaned_data['ssr'] is not None:
                                ssr=testsedssr_form.cleaned_data['ssr']
                                ssr.title=testsedssr_form.cleaned_data['ssr_title']
                                ssr.brief_description=testsedssr_form.cleaned_data['ssr_brief_description']
                            # Set collator if this is a new SSR
                            else:
                                ssr.collator=self.object.collator
                            ssr.last_modified_by=self.request.user
                            ssr.draft=self.object.draft
                            ssr.public=self.object.public
                            ssr.save()
                            testsedssr.ssr=ssr
                            testsedssr.save()

                    # remove testSED SSRs
                    for testsedssr_form in test_sed_form.nested.deleted_forms:
                        if testsedssr_form.instance.id:
                            testsedssr_form.instance.delete()

            # remove test SEDs
            for test_sed_form in test_sed_formset.deleted_forms:
                if test_sed_form.instance.id:
                    test_sed_form.instance.delete()

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

            # save inputs
            input_formset.instance=self.object
            for input_form in input_formset.forms:
                if not input_form in input_formset.deleted_forms:
                    input=input_form.save(commit=False)
                    input.module=self.object
                    input.save()

            # delete removed inputs
            for input_form in input_formset.deleted_forms:
                if input_form.instance.id:
                    input_form.instance.delete()

            # save outputs
            output_formset.instance=self.object
            for output_form in output_formset.forms:
                if not output_form in output_formset.deleted_forms:
                    output=output_form.save(commit=False)
                    output.module=self.object
                    output.save()

            # delete removed outputs
            for output_form in output_formset.deleted_forms:
                if output_form.instance.id:
                    output_form.instance.delete()

            # save states
            state_formset.instance=self.object
            for state_form in state_formset.forms:
                if not state_form in state_formset.deleted_forms:
                    state=state_form.save(commit=False)
                    state.module=self.object
                    state.save()

            # delete removed states
            for state_form in state_formset.deleted_forms:
                if state_form.instance.id:
                    state_form.instance.delete()

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

            # delete removed related Models
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


class CreateModelView(EditModelMixin, CreateView):

    def get_context_data(self, **kwargs):
        context = super(CreateModelView,self).get_context_data(**kwargs)
        context['helpPage']='insert_data.html#insert-model'
        context['showFigure']=True
        context['model_author_formset'] = ModelAuthorFormSet(self.request.POST or None,
            queryset=ModelAuthor.objects.none(), prefix='model_author')
        context['figure_formset']=DocumentFigureFormSet(self.request.POST or None, self.request.FILES or None,
            prefix='figure')
        context['related_bop_formset']=RelatedBOPFormSet(self.request.POST or None, prefix='related_bop')
        context['build_sed_formset']=BuildSEDFormSet(self.request.POST or None, prefix='build_sed')
        context['test_sed_formset']=TestSEDFormSet(self.request.POST or None, prefix='test_sed')
        context['prediction_formset']=PredictionFormSet(self.request.POST or None, prefix='prediction')
        context['related_model_formset']=RelatedModelFormSet(self.request.POST or None, prefix='related_model')
        context['related_brain_region_formset']=RelatedBrainRegionFormSet(self.request.POST or None,
            prefix='related_brain_region')
        context['input_formset']=VariableFormSet(self.request.POST or None, prefix='input')
        context['output_formset']=VariableFormSet(self.request.POST or None, prefix='output')
        context['state_formset']=VariableFormSet(self.request.POST or None, prefix='state')
        context['module_formset'] = ModuleFormSet(self.request.POST or None, prefix='module')
        context['ispopup']=('_popup' in self.request.GET)
        context['bop_relationship']=False
        return context


class UpdateModelView(EditModelMixin, UpdateView):
    def get_context_data(self, **kwargs):
        context = super(UpdateModelView,self).get_context_data(**kwargs)
        context['helpPage']='insert_data.html#insert-model'
        context['showFigure']=True
        context['model_author_formset'] = ModelAuthorFormSet(self.request.POST or None,
            queryset=ModelAuthor.objects.filter(model=self.object), prefix='model_author')
        context['figure_formset']=DocumentFigureFormSet(self.request.POST or None, self.request.FILES or None,
            instance=self.object, queryset=DocumentFigure.objects.filter(document=self.object), prefix='figure')
        context['related_bop_formset']=RelatedBOPFormSet(self.request.POST or None, instance=self.object,
            queryset=RelatedBOP.objects.filter(document=self.object), prefix='related_bop')
        context['build_sed_formset']=BuildSEDFormSet(self.request.POST or None, instance=self.object,
            queryset=BuildSED.objects.filter(document=self.object), prefix='build_sed')
        context['test_sed_formset']=TestSEDFormSet(self.request.POST or None, instance=self.object,
            queryset=TestSED.objects.filter(model=self.object), prefix='test_sed')
        context['prediction_formset']=PredictionFormSet(self.request.POST or None, instance=self.object,
            queryset=Prediction.objects.filter(model=self.object), prefix='prediction')
        context['related_model_formset']=RelatedModelFormSet(self.request.POST or None, instance=self.object,
            queryset=RelatedModel.objects.filter(document=self.object), prefix='related_model')
        context['related_brain_region_formset']=RelatedBrainRegionFormSet(self.request.POST or None,
            instance=self.object, queryset=RelatedBrainRegion.objects.filter(document=self.object),
            prefix='related_brain_region')
        context['input_formset']=VariableFormSet(self.request.POST or None, instance=self.object,
            queryset=Variable.objects.filter(module=self.object, var_type='Input'), prefix='input')
        context['output_formset']=VariableFormSet(self.request.POST or None, instance=self.object,
            queryset=Variable.objects.filter(module=self.object, var_type='Output'), prefix='output')
        context['state_formset']=VariableFormSet(self.request.POST or None, instance=self.object,
            queryset=Variable.objects.filter(module=self.object, var_type='State'), prefix='state')
        context['module_formset'] = ModuleFormSet(self.request.POST or None, instance=self.object,
            queryset=Module.objects.filter(parent=self.object), prefix='module')
        context['references'] = self.object.literature.all()
        context['ispopup']=('_popup' in self.request.GET)
        context['bop_relationship']=False
        return context


class DeleteModelView(DeleteView):
    model=Model
    success_url = '/bodb/index.html'


class ModelDetailView(DocumentDetailView):
    model = Model
    template_name = 'bodb/model/model_view.html'

    def get_context_data(self, **kwargs):
        context = super(ModelDetailView, self).get_context_data(**kwargs)
        user=self.request.user
        context['helpPage']='view_entry.html'
        context['generic_test_seds'] = TestSED.get_testing_sed_list(TestSED.get_generic_testing_seds(self.object,user),user)
        context['connectivity_test_seds'] = TestSED.get_testing_sed_list(TestSED.get_connectivity_testing_seds(self.object,user),user)
        context['imaging_test_seds'] = TestSED.get_testing_sed_list(TestSED.get_imaging_testing_seds(self.object, user),user)
        context['erp_test_seds'] = TestSED.get_testing_sed_list(TestSED.get_erp_testing_seds(self.object, user),user)
        context['predictions'] = Prediction.get_prediction_list(Prediction.get_predictions(self.object,user),user)
        context['inputs'] = Variable.objects.filter(var_type='Input',module=self.object)
        context['outputs'] = Variable.objects.filter(var_type='Output',module=self.object)
        context['states'] = Variable.objects.filter(var_type='State',module=self.object)
        context['modules'] = Module.objects.filter(parent=self.object)
        context['references'] = Literature.get_reference_list(self.object.literature.all(),user)
        context['hierarchy_html']=self.object.hierarchy_html(self.object.id)
        if user.is_authenticated() and not user.is_anonymous():
            context['subscribed_to_collator']=UserSubscription.objects.filter(subscribed_to_user=self.object.collator,
                user=user, model_type='Model').count()>0
            context['subscribed_to_last_modified_by']=UserSubscription.objects.filter(subscribed_to_user=self.object.last_modified_by,
                user=user, model_type='Model').count()>0
            context['selected']=user.get_profile().active_workspace.related_models.filter(id=self.object.id).count()>0
        context['bop_relationship']=False
        context['bopGraphId']='bopRelationshipDiagram'
        context['modelGraphId']='modelRelationshipDiagram'
        context['reverse_related_models']=RelatedModel.get_reverse_related_model_list(RelatedModel.get_reverse_related_models(self.object,user),user)
        return context


class ToggleSelectModelView(JSONResponseMixin,BaseUpdateView):
    model = Model

    def get_context_data(self, **kwargs):
        context={'msg':u'No POST data sent.' }
        if self.request.is_ajax():
            model=Model.objects.get(id=self.kwargs.get('pk', None))
            # Load active workspace
            active_workspace=self.request.user.get_profile().active_workspace

            context={
                'model_id': model.id,
                'workspace': active_workspace.title
            }
            activity=WorkspaceActivityItem(workspace=active_workspace, user=self.request.user)
            remove=False
            if 'select' in self.request.POST:
                remove=self.request.POST['select']=='false'
            else:
                remove=model in active_workspace.related_models.all()
            if remove:
                active_workspace.related_models.remove(model)
                context['selected']=False
                activity.text='%s removed the model: <a href="%s">%s</a> from the workspace' % (self.request.user.username, model.get_absolute_url(), model.__unicode__())
            else:
                active_workspace.related_models.add(model)
                context['selected']=True
                activity.text='%s added the model: <a href="%s">%s</a> to the workspace' % (self.request.user.username, model.get_absolute_url(), model.__unicode__())
            activity.save()
            active_workspace.save()

        return context


class ModelTaggedView(BODBView):
    template_name='bodb/model/model_tagged.html'

    def get_context_data(self, **kwargs):
        context=super(ModelTaggedView,self).get_context_data(**kwargs)
        name = self.kwargs.get('name', None)
        user=self.request.user
        context['helpPage']= 'tags.html'
        context['tag']= name
        context['modelGraphId']='modelRelationshipDiagram'
        context['tagged_items']= Model.get_model_list(Model.get_tagged_models(name, user),user)
        return context


class UpdateModuleView(UpdateView):
    model = Module
    form_class = ModuleForm
    template_name = 'bodb/model/module_detail.html'

    def get_context_data(self, **kwargs):
        context = super(UpdateModuleView,self).get_context_data(**kwargs)
        context['showFigure']=True
        context['figure_formset']=DocumentFigureFormSet(self.request.POST or None, self.request.FILES or None,
            instance=self.object, queryset=DocumentFigure.objects.filter(document=self.object), prefix='figure')
        context['input_formset']=VariableFormSet(self.request.POST or None, instance=self.object,
            queryset=Variable.objects.filter(module=self.object, var_type='Input'), prefix='input')
        context['output_formset']=VariableFormSet(self.request.POST or None, instance=self.object,
            queryset=Variable.objects.filter(module=self.object, var_type='Output'), prefix='output')
        context['state_formset']=VariableFormSet(self.request.POST or None, instance=self.object,
            queryset=Variable.objects.filter(module=self.object, var_type='State'), prefix='state')
        context['module_formset'] = ModuleFormSet(self.request.POST or None, instance=self.object,
            queryset=Module.objects.filter(parent=self.object), prefix='module')
        context['ispopup']=('_popup' in self.request.GET)
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        figure_formset = context['figure_formset']
        input_formset=context['input_formset']
        output_formset=context['output_formset']
        state_formset=context['state_formset']
        module_formset=context['module_formset']
        if figure_formset.is_valid() and input_formset.is_valid() and output_formset.is_valid() and \
           state_formset.is_valid() and module_formset.is_valid():
            self.object = form.save()

            # save modules
            for module_form in module_formset.forms:
                if not module_form in module_formset.deleted_forms:
                    module=module_form.save(commit=False)
                    # Set parent and collator if this is a new module
                    if not module.id:
                        module.parent=self.object
                        module.collator=self.object.collator
                    module.last_modified_by=self.request.user
                    module.draft=self.object.draft
                    module.public=self.object.public
                    module.save()

            # remove modules
            for module_form in module_formset.deleted_forms:
                if module_form.instance.id:
                    module_form.instance.delete()

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

            # save inputs
            input_formset.instance=self.object
            for input_form in input_formset.forms:
                if not input_form in input_formset.deleted_forms:
                    input=input_form.save(commit=False)
                    input.module=self.object
                    input.save()

            # delete removed inputs
            for input_form in input_formset.deleted_forms:
                if input_form.instance.id:
                    input_form.instance.delete()

            # save outputs
            output_formset.instance=self.object
            for output_form in output_formset.forms:
                if not output_form in output_formset.deleted_forms:
                    output=output_form.save(commit=False)
                    output.module=self.object
                    output.save()

            # delete removed outputs
            for output_form in output_formset.deleted_forms:
                if output_form.instance.id:
                    output_form.instance.delete()

            # save states
            state_formset.instance=self.object
            for state_form in state_formset.forms:
                if not state_form in state_formset.deleted_forms:
                    state=state_form.save(commit=False)
                    state.module=self.object
                    state.save()

            # delete removed states
            for state_form in state_formset.deleted_forms:
                if state_form.instance.id:
                    state_form.instance.delete()

            url=self.get_success_url()
            if context['ispopup']:
                url+='?_popup=1'
            return redirect(url)
        else:
            return self.render_to_response(self.get_context_data(form=form))


class DeleteModuleView(DeleteView):
    model=Module
    success_url = '/bodb/index.html'


class ModelAPIListView(DocumentAPIListView):
    serializer_class = ModelSerializer
    model = Model

    def get_queryset(self):
        user = self.request.user
        security_q=Document.get_security_q(user)
        return Model.objects.filter(security_q)


class ModelAPIDetailView(DocumentAPIDetailView):
    queryset = Model.objects.all()
    serializer_class = ModelSerializer
    
    model = Model


class ModuleDetailView(DocumentDetailView):
    model = Module
    template_name = 'bodb/model/module_view.html'

    def get_context_data(self, **kwargs):
        context = super(ModuleDetailView, self).get_context_data(**kwargs)
        user=self.request.user
        context['helpPage']='view_entry.html'
        context['inputs'] = Variable.objects.filter(var_type='Input',module=self.object)
        context['outputs'] = Variable.objects.filter(var_type='Output',module=self.object)
        context['states'] = Variable.objects.filter(var_type='State',module=self.object)
        context['modules'] = Module.objects.filter(parent=self.object)
        context['hierarchy_html']=Model.objects.get(id=self.object.get_root().id).hierarchy_html(self.object.id)
        if user.is_authenticated() and not user.is_anonymous():
            context['subscribed_to_collator']=UserSubscription.objects.filter(subscribed_to_user=self.object.collator,
                user=user, model_type='Model').count()>0
            context['subscribed_to_last_modified_by']=UserSubscription.objects.filter(subscribed_to_user=self.object.last_modified_by,
                user=user, model_type='Model').count()>0
        return context


class SimilarModelView(JSONResponseMixin, BaseDetailView):

    def get(self, request, *args, **kwargs):
        # Load similar models
        title=self.request.GET['title']
        brief_desc=self.request.GET['brief_description']
        similar_models=find_similar_models(self.request.user, title, brief_desc)
        similar_model_ids=[x.id for (x,matches) in similar_models]
        similar_model_titles=[str(x) for (x,matches) in similar_models]

        data = {'similar_model_ids': similar_model_ids,
                'similar_model_titles': similar_model_titles}

        return self.render_to_response(data)


class BenchmarkModelView(TemplateView):
    template_name = 'bodb/model/model_benchmark.html'

    def post(self, request, *args, **kwargs):
        self.request=request
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context=super(BenchmarkModelView,self).get_context_data(**kwargs)

        user=self.request.user

        context['helpPage']='benchmarks.html'
        context['scores']=[]
        sed_info={}
        context['params']=[]
        context['seds']=[]

        # Get models from compare checkbox selections
        context['selected_models']=[]
        for model_id in self.request.POST.getlist('selectedModel'):
            context['selected_models'].append(Model.objects.get(id=model_id))

        # Initialize scores
        for model in context['selected_models']:
            context['scores'].append(0)

        buildsed_q=Q(Q(related_build_sed_document__document__in=context['selected_models']))
        testsed_q=Q(Q(test_sed__model__in=context['selected_models']))
        related_seds=SED.objects.filter(Q(buildsed_q | testsed_q) & Document.get_security_q(user))

        for sed in related_seds:
            buildsed_q=Q(related_build_sed_document__sed__id=sed.id)
            testsed_q=Q(related_test_sed_document__sed__id=sed.id)
            sed_info[sed.id]=Model.objects.filter(Q(buildsed_q | testsed_q)).count()

        # Sort SEDS by number of models they are attached to
        sed_items=sed_info.items()
        sed_items.sort(compareBenchmarkSEDs)
        for item in sed_items:
            context['seds'].append(SED.objects.get(id=item[0]))

        for sed in context['seds']:
            attrs_row=[]
            modelIdx=0
            for model in context['selected_models']:
                attr=''
                label=''
                link=''
                r=0
                g=0
                b=0
                sed_q=Q(sed__id=sed.id)
                model_q=Q(document__id=model.id)
                bseds=BuildSED.objects.filter(Q(sed_q) & Q(model_q))
                for building_sed in bseds:
                    if building_sed.relationship=='scene setting':
                        attr='bgColor=''#0099FF'''
                        r=0
                        g=153
                        b=255
                        label='Scene Setting'
                    elif building_sed.relationship=='support':
                        attr='bgColor=''#9966FF'''
                        r=153
                        g=102
                        b=255
                        label='Support'
                        context['scores'][modelIdx] += 1
                    attr=attr+' title="'+building_sed.relevance_narrative+'"'
                model_q=Q(model__id=model.id)
                tseds=TestSED.objects.filter(Q(sed_q) & Q(model_q))
                for testing_sed in tseds:
                    if testing_sed.relationship=='explanation':
                        attr='bgColor=''#00FF99'''
                        r=0
                        g=255
                        b=153
                        label='Explanation'
                        context['scores'][modelIdx] += 1
                    elif testing_sed.relationship=='contradiction':
                        attr='bgColor=''#FFFF66'''
                        r=255
                        g=255
                        b=102
                        label='Contradiction'
                        context['scores'][modelIdx] -= 1
                    attr=attr+' title="'+testing_sed.relevance_narrative+'"'
                attrs_row.append([attr, label, link, r, g, b])
                modelIdx += 1
            context['params'].append([attrs_row, sed])
        context['col_width']=100*(1.0/(1.0+len(context['selected_models'])))
        return context


class ReverseBenchmarkModelView(TemplateView):
    template_name = 'bodb/model/model_reverse_benchmark.html'

    def post(self, request, *args, **kwargs):
        self.request=request
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context=super(ReverseBenchmarkModelView,self).get_context_data(**kwargs)

        user=self.request.user

        context['helpPage']='benchmarks.html'
        context['scores']=[]
        sed_info={}
        context['params']=[]

        context['selected_seds']=[]
        for sed_id in self.request.POST.getlist('selectedSED'):
            context['selected_seds'].append(SED.objects.get(id=sed_id))

        buildsed_q=Q(related_build_sed_document__sed__in=context['selected_seds'])
        testsed_q=Q(related_test_sed_document__sed__in=context['selected_seds'])
        context['models']=Model.objects.filter(Q(buildsed_q | testsed_q) & Document.get_security_q(user)).distinct()
        for model in context['models']:
            context['scores'].append(0)

        for sed in context['selected_seds']:
            # Update list of Models
            buildsed_q=Q(related_build_sed_document__sed=sed)
            testsed_q=Q(related_test_sed_document__sed=sed)
            sed_info[sed.id]=Model.objects.filter(Q(buildsed_q | testsed_q)).count()

        # Sort SEDS by number of models they are attached to
        sed_items=sed_info.items()
        #sed_items.sort(key=itemgetter(1),reverse=True)
        sed_items.sort(compareBenchmarkSEDs)

        selected_seds=[]
        for item in sed_items:
            sed=SED.objects.get(id=item[0])
            selected_seds.append(sed)

            attrs_row=[]
            modelIdx=0
            for model in context['models']:
                attr=''
                label=''
                link=''
                r=0
                g=0
                b=0

                sed_q=Q(sed__id=sed.id)
                model_q=Q(document__id=model.id)
                bseds=BuildSED.objects.filter(Q(sed_q) & Q(model_q))
                for building_sed in bseds:
                    if building_sed.relationship=='scene setting':
                        attr='bgColor=''#0099FF'''
                        r=0
                        g=153
                        b=255
                        label='Scene Setting'
                    elif building_sed.relationship=='support':
                        attr='bgColor=''#9966FF'''
                        r=153
                        g=102
                        b=255
                        label='Support'
                        context['scores'][modelIdx] += 1
                    attr=attr+' title="'+building_sed.relevance_narrative+'"'
                model_q=Q(model__id=model.id)
                tseds=TestSED.objects.filter(Q(sed_q) & Q(model_q))
                for testing_sed in tseds:
                    if testing_sed.relationship=='explanation':
                        attr='bgColor=''#00FF99'''
                        r=0
                        g=255
                        b=153
                        label='Explanation'
                        context['scores'][modelIdx] += 1
                    elif  testing_sed.relationship=='contradiction':
                        attr='bgColor=''#FFFF66'''
                        r=255
                        g=255
                        b=102
                        label='Contradiction'
                        context['scores'][modelIdx] -= 1
                    attr=attr+' title="'+testing_sed.relevance_narrative+'"'
                attrs_row.append([attr, label, link, r, g, b])
                modelIdx += 1
            context['params'].append([attrs_row, sed])

        context['col_width']=100*(1.0/(1.0+len(context['models'])))
        return context


def compareBenchmarkSEDs(a, b):
    if a[1]==b[1]:
        return cmp(SED.objects.get(id=a[0]).title.lower(),SED.objects.get(id=b[0]).title.lower())
    else:
        return -1*cmp(a[1],b[1])


class ModelDiagramView(JSONResponseMixin,BaseCreateView):
    model = Model
    def get_context_data(self, **kwargs):
        context={'msg':u'No POST data sent.' }
        if self.request.is_ajax():
            graphTool=self.request.POST['graphTool']
            models=Model.objects.filter(document_ptr__in=self.request.POST.getlist('modelIds[]'))
            dot_xml=model_gxl(models, self.request.user)
            context['modelDiagram'], size, context['modelMap'] = generate_diagram_from_gxl(graphTool, dot_xml,
                self.request.user, ext=self.request.POST['graphID'])
            context['modelDiagramW']=size[0]
            context['modelDiagramH']=size[1]
            context['graphId']=self.request.POST['graphID']
        return context