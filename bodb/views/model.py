import json
import os
from django.core.files.storage import FileSystemStorage
from django.contrib.formtools.wizard.views import SessionWizardView
from django.db.models import Q
from django.forms.forms import Form
from django.http import HttpResponse
from django.shortcuts import redirect, get_object_or_404
from django.core.cache import cache
from django.views.generic import TemplateView
from django.views.generic.detail import BaseDetailView
from django.views.generic.edit import BaseUpdateView, CreateView, UpdateView, DeleteView, BaseCreateView, ProcessFormView
from bodb.forms.bop import RelatedBOPFormSet
from bodb.forms.brain_region import RelatedBrainRegionFormSet
from bodb.forms.document import DocumentFigureFormSet
from bodb.forms.model import ModelForm, VariableFormSet, RelatedModelFormSet, ModelAuthorFormSet, ModuleFormSet, ModuleForm, ModelForm1, ModelForm2, ModelForm6
from bodb.forms.sed import TestSEDFormSet, BuildSEDFormSet
from bodb.forms.ssr import PredictionFormSet
from bodb.models import Model, DocumentFigure, RelatedBOP, RelatedBrainRegion, find_similar_models, Variable, RelatedModel, ModelAuthor, Author, Module, BuildSED, TestSED, SED, WorkspaceActivityItem, Document, Literature, UserSubscription, SSR, BOP, BrainRegion, ConnectivitySED
from bodb.models.ssr import Prediction
from bodb.views.document import DocumentDetailView
from bodb.views.main import set_context_workspace, get_active_workspace, get_profile, BODBView
from bodb.views.security import ObjectRolePermissionRequiredMixin
from guardian.mixins import PermissionRequiredMixin, LoginRequiredMixin
from uscbp import settings
from uscbp.views import JSONResponseMixin

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
                        module.collator=self.request.user
                    module.last_modified_by=self.request.user
                    module.draft=self.object.draft
                    module.public=self.object.public
                    module.save()

            # remove modules
            for module_form in module_formset.deleted_forms:
                if module_form.instance.id:
                    module_form.instance.delete()

            # save predictions
            prediction_formset.instance = self.object
            for prediction_form in prediction_formset.forms:
                if not prediction_form in prediction_formset.deleted_forms:
                    prediction=prediction_form.save(commit=False)
                    # Set prediction model and collator if this is a new prediction
                    if prediction.id is None:
                        prediction.model=self.object
                        prediction.collator=self.request.user
                    prediction.last_modified_by=self.request.user
                    prediction.draft=self.object.draft
                    prediction.public=self.object.public
                    prediction.save()

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


class CreateModelView(EditModelMixin, PermissionRequiredMixin, CreateView):
    permission_required='bodb.add_model'

    def get_object(self, queryset=None):
        return None

    def get_context_data(self, **kwargs):
        context = super(CreateModelView,self).get_context_data(**kwargs)
        context=set_context_workspace(context, self.request)
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


MODEL_WIZARD_FORMS = [("step1", ModelForm1),
                      ("step2", ModelForm2),
                      ("step3", Form),
                      ("step4", Form),
                      ("step5", Form),
                      ('step6', ModelForm6)
                     ]

MODEL_WIZARD_TEMPLATES = {"step1": 'bodb/model/model_create_1.html',
                          "step2": 'bodb/model/model_create_2.html',
                          "step3": 'bodb/model/model_create_3.html',
                          "step4": 'bodb/model/model_create_4.html',
                          "step5": 'bodb/model/model_create_5.html',
                          "step6": 'bodb/model/model_create_6.html'
                         }

class CreateModelWizardView(PermissionRequiredMixin, SessionWizardView):
    permission_required='bodb.add_model'
    file_storage = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'figures'))

    def get_template_names(self):
        return [MODEL_WIZARD_TEMPLATES[self.steps.current]]

    def extract_formset_initial(self, data_key, form_prefix):
        initial = {}
        if data_key in self.storage.data:
            for key, val in self.storage.data[data_key].iteritems():
                if key.startswith('%s-' % form_prefix):
                    parts = key.split('-')
                    try:
                        idx = int(parts[1])
                        if not idx in initial:
                            initial[idx] = {}
                        initial[idx][parts[2]] = val
                    except:
                        pass
        initial = [initial[key] for key in sorted(initial)]
        return initial

    def get_context_data(self, form, **kwargs):
        context=super(CreateModelWizardView,self).get_context_data(form, **kwargs)
        context=set_context_workspace(context, self.request)
        context['helpPage']='insert_data.html#insert-model'
        context['showFigure']=True
        context['showAuthors']=True
        context['showReferences']=True
        context['showBuildSEDs']=True
        context['showTestSEDs']=True
        context['showPredictions']=True
        context['showRelatedModels']=True
        context['showRelatedBOPs']=True
        context['showRelatedBrainRegions']=True
        context['ispopup']=('_popup' in self.request.GET)
        if 'create_model_wizard_view-current_step' in self.request.POST:
            if self.request.POST['create_model_wizard_view-current_step']=='step1':
                self.storage.data['step1_data']=self.request.POST
                self.storage.data['literature']=self.request.POST.getlist('literature')
            elif self.request.POST['create_model_wizard_view-current_step']=='step2':
                self.storage.data['step2_data']=self.request.POST
                for key,file_list in self.request.FILES.iteritems():
                    self.storage.data[key]=file_list.name
            elif self.request.POST['create_model_wizard_view-current_step']=='step3':
                self.storage.data['step3_data']=self.request.POST
            elif self.request.POST['create_model_wizard_view-current_step']=='step4':
                self.storage.data['step4_data']=self.request.POST
            elif self.request.POST['create_model_wizard_view-current_step']=='step5':
                self.storage.data['step5_data']=self.request.POST
            elif self.request.POST['create_model_wizard_view-current_step']=='step6':
                self.storage.data['step6_data']=self.request.POST

        if self.steps.current=='step1':
            model_author_initial=self.extract_formset_initial('step1_data','model_author')
            context['model_author_formset'] = ModelAuthorFormSet(queryset=ModelAuthor.objects.none(),
                initial=model_author_initial, prefix='model_author', extra=len(model_author_initial))
            if 'literature' in self.storage.data:
                context['references']=Literature.objects.filter(id__in=self.storage.data['literature'])
        elif self.steps.current=='step2':
            figure_initial=self.extract_formset_initial('step2_data','figure')
            for idx in range(len(figure_initial)):
                figure_initial[idx]['figure']=os.path.join('figures',self.storage.data['figure-%d-figure' % idx])
            context['figure_formset']=DocumentFigureFormSet(queryset=DocumentFigure.objects.none(),
                initial=figure_initial,prefix='figure',extra=len(figure_initial))
            input_initial = self.extract_formset_initial('step2_data','input')
            context['input_formset']=VariableFormSet(queryset=Variable.objects.none(),initial=input_initial,
                prefix='input',extra=len(input_initial))
            output_initial = self.extract_formset_initial('step2_data','output')
            context['output_formset']=VariableFormSet(queryset=Variable.objects.none(),initial=output_initial,
                prefix='output',extra=len(output_initial))
            state_initial=self.extract_formset_initial('step2_data','state')
            context['state_formset']=VariableFormSet(queryset=Variable.objects.none(),initial=state_initial,
                prefix='state',extra=len(state_initial))
            module_initial=self.extract_formset_initial('step2_data','module')
            context['module_formset'] = ModuleFormSet(queryset=Module.objects.none(),initial=module_initial,
                prefix='module',extra=len(module_initial))
        elif self.steps.current=='step3':
            buildsed_initial=self.extract_formset_initial('step3_data','build_sed')
            for idx in range(len(buildsed_initial)):
                sed=SED.objects.get(id=buildsed_initial[idx]['sed'])
                buildsed_initial[idx]['sed_title']=sed.__unicode__()
                buildsed_initial[idx]['sed_brief_description']=sed.brief_description
                buildsed_initial[idx]['sed_type']=sed.type
            context['build_sed_formset']=BuildSEDFormSet(queryset=BuildSED.objects.none(),initial=buildsed_initial,
                prefix='build_sed',extra=len(buildsed_initial))
        elif self.steps.current=='step4':
            testsed_initial=self.extract_formset_initial('step4_data','test_sed')
            for idx in range(len(testsed_initial)):
                sed=SED.objects.get(id=testsed_initial[idx]['sed'])
                testsed_initial[idx]['sed_title']=sed.__unicode__()
                testsed_initial[idx]['sed_brief_description']=sed.brief_description
                testsed_initial[idx]['sed_type']=sed.type
                if SSR.objects.filter(id=testsed_initial[idx]['ssr']).count():
                    ssr=SSR.objects.get(id=testsed_initial[idx]['ssr'])
                    testsed_initial[idx]['ssr_title']=ssr.__unicode__()
                    testsed_initial[idx]['ssr_brief_description']=ssr.brief_description
                    testsed_initial[idx]['ssr_type']=ssr.type
                else:
                    testsed_initial[idx]['ssr_title']=''
                    testsed_initial[idx]['ssr_brief_description']=''
                    testsed_initial[idx]['ssr_type']=''
            context['test_sed_formset']=TestSEDFormSet(queryset=TestSED.objects.none(),initial=testsed_initial,
                prefix='test_sed',extra=len(testsed_initial))
        elif self.steps.current=='step5':
            prediction_initial=self.extract_formset_initial('step5_data','prediction')
            for idx in range(len(prediction_initial)):
                if SSR.objects.filter(id=prediction_initial[idx]['ssr']).count():
                    ssr=SSR.objects.get(id=prediction_initial[idx]['ssr'])
                    prediction_initial[idx]['ssr_title']=ssr.__unicode__()
                    prediction_initial[idx]['ssr_brief_description']=ssr.brief_description
                    prediction_initial[idx]['ssr_type']=ssr.type
                else:
                    prediction_initial[idx]['ssr_title']=''
                    prediction_initial[idx]['ssr_brief_description']=''
                    prediction_initial[idx]['ssr_type']=''
            context['prediction_formset']=PredictionFormSet(queryset=Prediction.objects.none(),
                initial=prediction_initial,prefix='prediction',extra=len(prediction_initial))
        elif self.steps.current=='step6':
            related_bop_initial=self.extract_formset_initial('step6_data','related_bop')
            for idx in range(len(related_bop_initial)):
                bop=BOP.objects.get(id=related_bop_initial[idx]['bop'])
                related_bop_initial[idx]['bop_title']=bop.__unicode__()
                related_bop_initial[idx]['bop_brief_description']=bop.brief_description
            context['related_bop_formset']=RelatedBOPFormSet(queryset=RelatedBOP.objects.none(),
                initial=related_bop_initial,prefix='related_bop',extra=len(related_bop_initial))
            related_model_initial=self.extract_formset_initial('step6_data','related_model')
            for idx in range(len(related_model_initial)):
                model=Model.objects.get(id=related_model_initial[idx]['model'])
                related_model_initial[idx]['model_title']=model.__unicode__()
                related_model_initial[idx]['model_brief_description']=model.brief_description
            context['related_model_formset']=RelatedModelFormSet(queryset=RelatedModel.objects.none(),
                initial=related_model_initial,prefix='related_model',extra=len(related_model_initial))
            related_region_initial=self.extract_formset_initial('step6_data','related_brain_region')
            for idx in range(len(related_region_initial)):
                region=BrainRegion.objects.get(id=related_region_initial[idx]['brain_region'])
                related_region_initial[idx]['brain_region_name']=region.__unicode__()
                related_region_initial[idx]['brain_region_nomenclature']=region.nomenclature.__unicode__()
                related_region_initial[idx]['brain_region_nomenclature_species']=region.nomenclature.species_name()
            context['related_brain_region_formset']=RelatedBrainRegionFormSet(queryset=RelatedBrainRegion.objects.none(),
                initial=related_region_initial,prefix='related_brain_region',extra=len(related_region_initial))
        return context

    def done(self, form_list, **kwargs):
        self.storage.data['step6_data']=self.request.POST

        model=Model(collator=self.request.user, last_modified_by=self.request.user,
            title=form_list[0].cleaned_data['title'], brief_description=form_list[0].cleaned_data['brief_description'],
            narrative=form_list[1].cleaned_data['narrative'], execution_url=form_list[0].cleaned_data['execution_url'],
            documentation_url=form_list[0].cleaned_data['documentation_url'],
            description_url=form_list[0].cleaned_data['description_url'],
            simulation_url=form_list[0].cleaned_data['simulation_url'],
            modeldb_accession_number=form_list[0].cleaned_data['modeldb_accession_number'],
            draft=form_list[5].cleaned_data['draft'], public=form_list[0].cleaned_data['public'])
        model.save()
        for tag in form_list[0].cleaned_data['tags']:
            model.tags.add(tag)
        for lit_id in self.storage.data['literature']:
            model.literature.add(Literature.objects.get(id=lit_id))

        # save authors
        author_formset=ModelAuthorFormSet(self.storage.data['step1_data'], queryset=ModelAuthor.objects.none(),
            prefix='model_author')
        for author_form in author_formset.forms:
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
            model.authors.add(model_author)

        # save figures
        figure_formset=DocumentFigureFormSet(self.storage.data['step2_data'], self.request.FILES or None, prefix='figure')
        figure_formset.instance = model
        for idx,figure_form in enumerate(figure_formset.forms):
            file_name=os.path.join('figures',self.storage.data['figure-%d-figure' % idx])
            figure=DocumentFigure(caption=figure_form.data['figure-%d-caption' % idx], title=figure_form.data['figure-%d-title' % idx],
                order=figure_form.data['figure-%d-order' % idx], document=model)
            figure.figure.name=file_name
            figure.document=model
            figure.save()

        # save inputs
        input_formset=VariableFormSet(self.storage.data['step2_data'], prefix='input')
        input_formset.instance=model
        for input_form in input_formset.forms:
            input=input_form.save(commit=False)
            input.module=model
            input.save()

        # save outputs
        output_formset=VariableFormSet(self.storage.data['step2_data'], prefix='output')
        output_formset.instance=model
        for output_form in output_formset.forms:
            output=output_form.save(commit=False)
            output.module=model
            output.save()

        # save states
        state_formset=VariableFormSet(self.storage.data['step2_data'], prefix='state')
        state_formset.instance=model
        for state_form in state_formset.forms:
            state=state_form.save(commit=False)
            state.module=model
            state.save()

        # save modules
        module_formset = ModuleFormSet(self.storage.data['step2_data'], prefix='module')
        for module_form in module_formset.forms:
            module=module_form.save(commit=False)
            # Set module parent and collator if this is a new module
            if module.id is None:
                module.parent=model
                module.collator=model.collator
            module.last_modified_by=self.request.user
            module.draft=model.draft
            module.public=model.public
            module.save()

        # save build SEDs
        build_sed_formset=BuildSEDFormSet(self.storage.data['step3_data'], prefix='build_sed')
        build_sed_formset.instance=model
        for build_sed_form in build_sed_formset.forms:
            build_sed=build_sed_form.save(commit=False)
            build_sed.document=model
            build_sed.save()

        # save test SEDs
        test_sed_formset=TestSEDFormSet(self.storage.data['step4_data'], prefix='test_sed')
        test_sed_formset.instance = model
        for test_sed_form in test_sed_formset.forms:
            test_sed=test_sed_form.save(commit=False)
            test_sed.model=model
            test_sed.save()

        # save predictions
        prediction_formset=PredictionFormSet(self.storage.data['step5_data'], prefix='prediction')
        prediction_formset.instance = model
        for prediction_form in prediction_formset.forms:
            prediction=prediction_form.save(commit=False)
            # Set prediction model and collator if this is a new prediction
            if prediction.id is None:
                prediction.model=model
                prediction.collator=model.collator
            prediction.last_modified_by=self.request.user
            prediction.draft=model.draft
            prediction.public=model.public
            prediction.save()

        # save related BOPs
        related_bop_formset=RelatedBOPFormSet(self.storage.data['step6_data'], prefix='related_bop')
        related_bop_formset.instance=model
        for related_bop_form in related_bop_formset.forms:
            if not related_bop_form in related_bop_formset.deleted_forms:
                related_bop=related_bop_form.save(commit=False)
                related_bop.document=model
                related_bop.save()

        # save related Models
        related_model_formset=RelatedModelFormSet(self.storage.data['step6_data'], prefix='related_model')
        related_model_formset.instance=model
        for related_model_form in related_model_formset.forms:
            if not related_model_form in related_model_formset.deleted_forms:
                related_model=related_model_form.save(commit=False)
                related_model.document=model
                related_model.save()

        # save related brain regions
        related_brain_region_formset=RelatedBrainRegionFormSet(self.storage.data['step6_data'], prefix='related_brain_region')
        related_brain_region_formset.instance=model
        for related_brain_region_form in related_brain_region_formset.forms:
            if not related_brain_region_form in related_brain_region_formset.deleted_forms:
                related_brain_region=related_brain_region_form.save(commit=False)
                related_brain_region.document=model
                related_brain_region.save()

        return redirect(model.get_absolute_url())


class UpdateModelView(EditModelMixin, ObjectRolePermissionRequiredMixin, UpdateView):
    permission_required='edit'

    def get_object(self, queryset=None):
        if not hasattr(self,'object'):
            self.object=get_object_or_404(Model.objects.select_related('collator').prefetch_related('authors__author'),id=self.kwargs.get(self.pk_url_kwarg, None))
        return self.object

    def get_context_data(self, **kwargs):
        context = super(UpdateModelView,self).get_context_data(**kwargs)
        context=set_context_workspace(context, self.request)
        context['helpPage']='insert_data.html#insert-model'
        context['showFigure']=True
        context['model_author_formset'] = ModelAuthorFormSet(self.request.POST or None,
            queryset=ModelAuthor.objects.filter(model=self.object).select_related('author'), prefix='model_author')
        context['figure_formset']=DocumentFigureFormSet(self.request.POST or None, self.request.FILES or None,
            instance=self.object, queryset=DocumentFigure.objects.filter(document=self.object), prefix='figure')
        context['related_bop_formset']=RelatedBOPFormSet(self.request.POST or None, instance=self.object,
            queryset=RelatedBOP.objects.filter(document=self.object).select_related('bop'), prefix='related_bop')
        context['build_sed_formset']=BuildSEDFormSet(self.request.POST or None, instance=self.object,
            queryset=BuildSED.objects.filter(document=self.object).select_related('sed'), prefix='build_sed')
        context['test_sed_formset']=TestSEDFormSet(self.request.POST or None, instance=self.object,
            queryset=TestSED.objects.filter(model=self.object).select_related('sed','ssr'), prefix='test_sed')
        context['prediction_formset']=PredictionFormSet(self.request.POST or None, instance=self.object,
            queryset=Prediction.objects.filter(model=self.object).select_related('ssr','collator'), prefix='prediction')
        context['related_model_formset']=RelatedModelFormSet(self.request.POST or None, instance=self.object,
            queryset=RelatedModel.objects.filter(document=self.object).select_related('model'), prefix='related_model')
        context['related_brain_region_formset']=RelatedBrainRegionFormSet(self.request.POST or None,
            instance=self.object, queryset=RelatedBrainRegion.objects.filter(document=self.object).select_related('brain_region__nomenclature').prefetch_related('brain_region__nomenclature__species'),
            prefix='related_brain_region')
        context['input_formset']=VariableFormSet(self.request.POST or None, instance=self.object,
            queryset=Variable.objects.filter(module=self.object, var_type='Input'), prefix='input')
        context['output_formset']=VariableFormSet(self.request.POST or None, instance=self.object,
            queryset=Variable.objects.filter(module=self.object, var_type='Output'), prefix='output')
        context['state_formset']=VariableFormSet(self.request.POST or None, instance=self.object,
            queryset=Variable.objects.filter(module=self.object, var_type='State'), prefix='state')
        context['module_formset'] = ModuleFormSet(self.request.POST or None, instance=self.object,
            queryset=Module.objects.filter(parent=self.object), prefix='module')
        context['references'] = self.object.literature.all().prefetch_related('authors__author')
        context['ispopup']=('_popup' in self.request.GET)
        context['bop_relationship']=False
        return context


class DeleteModelView(ObjectRolePermissionRequiredMixin,DeleteView):
    model=Model
    success_url = '/bodb/index.html'
    permission_required='delete'

    def get_context_data(self, **kwargs):
        context={}
        if 'idx' in self.request.POST:
            context['idx']=self.request.POST['idx']

        return context

    def post(self, request, *args, **kwargs):
        self.request=request
        self.delete(request, *args, **kwargs)
        return HttpResponse(json.dumps(self.get_context_data(**kwargs)), content_type='application/json')


class ModelDetailView(ObjectRolePermissionRequiredMixin,DocumentDetailView):
    model = Model
    template_name = 'bodb/model/model_view.html'
    permission_required='view'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

    def get_object(self, queryset=None):
        if not hasattr(self,'object'):
            self.object=get_object_or_404(Model.objects.select_related('forum','collator','last_modified_by').prefetch_related('authors__author'),id=self.kwargs.get(self.pk_url_kwarg, None))
        return self.object

    def get_context_data(self, **kwargs):
        context = super(ModelDetailView, self).get_context_data(**kwargs)
        user=self.request.user
        context['helpPage']='view_entry.html'
        generic_test_seds=TestSED.get_generic_testing_seds(self.object,user)
        context['generic_test_seds'] = TestSED.get_testing_sed_list(generic_test_seds, context['workspace_seds'],
            context['workspace_ssrs'], context['fav_docs'], context['subscriptions'])

        conn_test_seds=TestSED.get_connectivity_testing_seds(self.object,user)
        context['connectivity_test_seds'] = TestSED.get_testing_sed_list(conn_test_seds, context['workspace_seds'],
            context['workspace_ssrs'], context['fav_docs'], context['subscriptions'])
        context['connectivity_test_sed_seds']=[]
        for test_sed in conn_test_seds:
            conn_sed=ConnectivitySED.objects.get(id=test_sed.sed.id)
            test_sed.sed=conn_sed
            if not conn_sed in context['connectivity_test_sed_seds']:
                context['connectivity_test_sed_seds'].append(conn_sed)
        context['connectivity_test_sed_regions']=ConnectivitySED.get_region_map(context['connectivity_test_sed_seds'])

        imaging_test_seds=TestSED.get_imaging_testing_seds(self.object, user)
        context['imaging_test_seds'] = TestSED.get_testing_sed_list(imaging_test_seds, context['workspace_seds'],
            context['workspace_ssrs'], context['fav_docs'], context['subscriptions'])
        erp_test_seds=TestSED.get_erp_testing_seds(self.object, user)
        context['erp_test_seds'] = TestSED.get_testing_sed_list(erp_test_seds, context['workspace_seds'],
            context['workspace_ssrs'], context['fav_docs'], context['subscriptions'])
        predictions=Prediction.get_predictions(self.object,user)
        context['predictions'] = Prediction.get_prediction_list(predictions, context['workspace_ssrs'],
            context['fav_docs'], context['subscriptions'])
        context['inputs'] = Variable.objects.filter(var_type='Input',module=self.object)
        context['outputs'] = Variable.objects.filter(var_type='Output',module=self.object)
        context['states'] = Variable.objects.filter(var_type='State',module=self.object)
        context['modules'] = Module.objects.filter(parent=self.object)
        literature=self.object.literature.all().select_related('collator').prefetch_related('authors__author')
        context['references'] = Literature.get_reference_list(literature,context['workspace_literature'],
            context['fav_lit'], context['subscriptions'])
        context['hierarchy_html']=self.object.hierarchy_html(self.object.id)
        context['subscribed_to_collator']=(self.object.collator.id, 'Model') in context['subscriptions']
        context['subscribed_to_last_modified_by']=(self.object.last_modified_by.id, 'Model') in context['subscriptions']
        context['selected']=self.object.id in context['workspace_models']
        context['bop_relationship']=False
        context['bopGraphId']='bopRelationshipDiagram'
        context['modelGraphId']='modelRelationshipDiagram'
        return context


class ToggleSelectModelView(LoginRequiredMixin,JSONResponseMixin,BaseUpdateView):
    model = Model

    def get_context_data(self, **kwargs):
        context={'msg':u'No POST data sent.' }
        if self.request.is_ajax():
            model=Model.objects.get(id=self.kwargs.get('pk', None))
            active_workspace=get_active_workspace(get_profile(self.request),self.request)

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
            cache.set('%d.active_workspace' % self.request.user.id, active_workspace)

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
        models=Model.get_tagged_models(name, user)
        context['tagged_items']= Model.get_model_list(models, context['workspace_models'], context['fav_docs'],
            context['subscriptions'])
        return context


class UpdateModuleView(ObjectRolePermissionRequiredMixin,UpdateView):
    model = Module
    form_class = ModuleForm
    template_name = 'bodb/model/module_detail.html'
    permission_required='edit'

    def get_object(self, queryset=None):
        if not hasattr(self,'object'):
            self.object=get_object_or_404(Module.objects.select_related('collator'),id=self.kwargs.get(self.pk_url_kwarg, None))
        return self.object

    def get_form(self, form_class):
        form=super(UpdateModuleView,self).get_form(form_class)
        form.fields['parent'].queryset=self.object.get_root().get_descendants(include_self=True)
        return form

    def get_context_data(self, **kwargs):
        context = super(UpdateModuleView,self).get_context_data(**kwargs)
        context=set_context_workspace(context, self.request)
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
            self.object = form.save(commit=False)
            self.object.last_modified_by=self.request.user
            self.object.save()
            # Needed to save literature and tags
            form.save_m2m()

            # save modules
            for module_form in module_formset.forms:
                if not module_form in module_formset.deleted_forms:
                    module=module_form.save(commit=False)
                    # Set parent and collator if this is a new module
                    if not module.id:
                        module.parent=self.object
                        module.collator=self.request.user
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


class DeleteModuleView(ObjectRolePermissionRequiredMixin,DeleteView):
    model=Module
    success_url = '/bodb/index.html'
    permission_required = 'delete'


class ModuleDetailView(ObjectRolePermissionRequiredMixin,DocumentDetailView):
    model = Module
    template_name = 'bodb/model/module_view.html'
    permission_required = 'view'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

    def get_object(self, queryset=None):
        if not hasattr(self,'object'):
            self.object=get_object_or_404(Module.objects.select_related('forum','collator','last_modified_by'),id=self.kwargs.get(self.pk_url_kwarg, None))
        return self.object

    def get_context_data(self, **kwargs):
        context = super(ModuleDetailView, self).get_context_data(**kwargs)
        user=self.request.user
        context['helpPage']='view_entry.html'
        context['inputs'] = Variable.objects.filter(var_type='Input',module=self.object)
        context['outputs'] = Variable.objects.filter(var_type='Output',module=self.object)
        context['states'] = Variable.objects.filter(var_type='State',module=self.object)
        context['modules'] = Module.objects.filter(parent=self.object)
        context['hierarchy_html']=Model.objects.prefetch_related('authors__author').get(id=self.object.get_root().id).hierarchy_html(self.object.id)
        context['subscribed_to_collator']=(self.object.collator.id, 'Model') in context['subscriptions']
        context['subscribed_to_last_modified_by']=(self.object.last_modified_by.id, 'Model') in context['subscriptions']
        return context


class SimilarModelView(LoginRequiredMixin,JSONResponseMixin, BaseDetailView):

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


class BenchmarkModelView(BODBView):
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

        buildsed_q=Q(Q(build_sed__document__in=context['selected_models']))
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
                        attr='bgColor=''#00bec3'''
                        r=0
                        g=190
                        b=195
                        label='Scene Setting'
                    elif building_sed.relationship=='support':
                        attr='bgColor=''#c67cfd'''
                        r=198
                        g=124
                        b=253
                        label='Support'
                        context['scores'][modelIdx] += 1
                    attr=attr+' title="'+building_sed.relevance_narrative+'"'
                model_q=Q(model__id=model.id)
                tseds=TestSED.objects.filter(Q(sed_q) & Q(model_q))
                for testing_sed in tseds:
                    if testing_sed.relationship=='explanation':
                        attr='bgColor=''#7bad03'''
                        r=123
                        g=173
                        b=3
                        label='Explanation'
                        context['scores'][modelIdx] += 1
                    elif testing_sed.relationship=='contradiction':
                        attr='bgColor=''#f6766d'''
                        r=246
                        g=118
                        b=109
                        label='Contradiction'
                        context['scores'][modelIdx] -= 1
                    attr=attr+' title="'+testing_sed.relevance_narrative+'"'
                attrs_row.append([attr, label, link, r, g, b])
                modelIdx += 1
            context['params'].append([attrs_row, sed])
        context['col_width']=100*(1.0/(1.0+len(context['selected_models'])))
        return context


class ReverseBenchmarkModelView(BODBView):
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
                        attr='bgColor=''#00bec3'''
                        r=0
                        g=190
                        b=195
                        label='Scene Setting'
                    elif building_sed.relationship=='support':
                        attr='bgColor=''#c67cfd'''
                        r=198
                        g=124
                        b=253
                        label='Support'
                        context['scores'][modelIdx] += 1
                    attr=attr+' title="'+building_sed.relevance_narrative+'"'
                model_q=Q(model__id=model.id)
                tseds=TestSED.objects.filter(Q(sed_q) & Q(model_q))
                for testing_sed in tseds:
                    if testing_sed.relationship=='explanation':
                        attr='bgColor=''#7bad03'''
                        r=123
                        g=173
                        b=3
                        label='Explanation'
                        context['scores'][modelIdx] += 1
                    elif  testing_sed.relationship=='contradiction':
                        attr='bgColor=''#f6766d'''
                        r=246
                        g=118
                        b=109
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
