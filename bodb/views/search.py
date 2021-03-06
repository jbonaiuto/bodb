import datetime
import json
from Bio import Entrez
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from bodb.search.workspace import runWorkspaceSearch
from bodb.views.main import set_context_workspace

Entrez.email = 'uscbrainproject@gmail.com'
from django.http import HttpResponse
from bodb.search.user import runUserSearch
from registration.models import User
from bodb.search.atlas import runBrainRegionSearch
from bodb.search.bop import runBOPSearch
from bodb.search.literature import runLiteratureSearch
from bodb.search.model import runModelSearch
from bodb.search.sed import runSEDSearch, runSEDCoordSearch
from bodb.search.ssr import runSSRSearch
from federation.modeldb.search import runModelDBSearch
from django.views.generic.edit import FormView
from federation.brede.search import runBredeSearch
from federation.cocomac.search import runCoCoMacSearch2
from bodb.forms.search import AllSearchForm, BOPSearchForm, SEDSearchForm, LiteratureSearchForm, BrainRegionSearchForm, ModelSearchForm, DocumentSearchForm, PubmedSearchForm, ModelDBSearchForm, UserSearchForm, WorkspaceSearchForm
from bodb.models import BOP, SED, Literature, BrainRegion, Model, SSR, PubMedResult, ERPSED, BrainImagingSED, ConnectivitySED, ERPComponent, BodbProfile, Workspace, Species, stop_words

class SearchView(FormView):
    form_class = AllSearchForm
    template_name='bodb/search/search.html'

    def get_context_data(self, **kwargs):
        context = super(SearchView,self).get_context_data(**kwargs)
        context=set_context_workspace(context, self.request)
        context['helpPage']='search_data.html'
        context['showTour']='show_tour' in self.request.GET
        context['showTabs']=True
        context['ispopup']=('_popup' in self.request.GET)
        
        context['bop_search_form']=BOPSearchForm(self.request.POST or None,prefix='bop')
        context['model_search_form']=ModelSearchForm(self.request.POST or None,prefix='model')
        context['sed_search_form']=SEDSearchForm(self.request.POST or None,prefix='sed')
        context['ssr_search_form']=DocumentSearchForm(self.request.POST or None,prefix='ssr')
        context['literature_search_form']=LiteratureSearchForm(self.request.POST or None,prefix='literature')
        genus_options=Species.get_genus_options()
        species_options=Species.get_species_options()
        context['brain_region_search_form']=BrainRegionSearchForm(genus_options, species_options, self.request.POST or None,prefix='brain_region')
        context['user_search_form']=UserSearchForm(self.request.POST or None,prefix='user')
        context['workspace_search_form']=WorkspaceSearchForm(self.request.POST or None, prefix='workspace')
        
        context['searchType']=self.request.POST.get('searchType','all')
        context['allConnectionGraphId']='allConnectivitySEDDiagram'
        context['allErpGraphId']='allErpSEDDiagram'
        context['sedConnectionGraphId']='sedConnectivitySEDDiagram'
        context['sedErpGraphId']='sedErpSEDDiagram'
        context['allBopGraphId']='allBOPRelationshipDiagram'
        context['bopBOPGraphId']='bopRelationshipDiagram'
        context['allModelGraphId']='allModelRelationshipDiagram'
        context['modelModelGraphId']='modelRelationshipDiagram'
        return context

    def form_valid(self, form):
        context=self.get_context_data(form=form)
        bop_form = context['bop_search_form']
        model_form = context['model_search_form']
        sed_form = context['sed_search_form']
        ssr_form = context['ssr_search_form']
        literature_form = context['literature_search_form']
        brain_region_form = context['brain_region_search_form']
        user_form=context['user_search_form']
        workspace_form=context['workspace_search_form']

        user=self.request.user

        genericSEDs=[]
        connectivitySEDs=[]
        erpSEDs=[]
        imagingSEDs=[]
        sedCoords=[]

        literature=Literature.objects.none()
        bops=BOP.objects.none()
        models=Model.objects.none()
        ssrs=SSR.objects.none()
        brain_regions=BrainRegion.objects.none()
        users=User.objects.none()
        workspaces=Workspace.objects.none()

        bop_order_by=self.request.POST.get('bop_order_by','title')
        bop_direction=self.request.POST.get('bop_direction','ascending')
        region_order_by=self.request.POST.get('region_order_by','name')
        region_direction=self.request.POST.get('region_direction','ascending')
        literature_order_by=self.request.POST.get('literature_order_by','string')
        literature_direction=self.request.POST.get('literature_direction','ascending')
        model_order_by=self.request.POST.get('model_order_by','title')
        model_direction=self.request.POST.get('model_direction','ascending')
        generic_sed_order_by=self.request.POST.get('generic_sed_order_by','title')
        generic_sed_direction=self.request.POST.get('generic_sed_direction','ascending')
        erp_sed_order_by=self.request.POST.get('erp_sed_order_by','title')
        erp_sed_direction=self.request.POST.get('erp_sed_direction','ascending')
        connectivity_sed_order_by=self.request.POST.get('connectivity_sed_order_by','title')
        connectivity_sed_direction=self.request.POST.get('connectivity_sed_direction','ascending')
        imaging_sed_order_by=self.request.POST.get('imaging_sed_order_by','title')
        imaging_sed_direction=self.request.POST.get('imaging_sed_direction','ascending')
        ssr_order_by=self.request.POST.get('ssr_order_by','title')
        ssr_direction=self.request.POST.get('ssr_direction','ascending')
        user_order_by=self.request.POST.get('user_order_by','username')
        user_direction=self.request.POST.get('user_direction','ascending')
        workspace_order_by=self.request.POST.get('workspace_order_by','title')
        workspace_direction=self.request.POST.get('workspace_direction','ascending')

        searchType=self.request.POST['searchType']
        if searchType=='bops' and bop_form.is_valid():
            bop_form.cleaned_data['bop_order_by']=bop_order_by
            bop_form.cleaned_data['bop_direction']=bop_direction
            bops=runBOPSearch(bop_form.cleaned_data, user.id)
        elif searchType=='models' and model_form.is_valid():
            model_form.cleaned_data['model_order_by']=model_order_by
            model_form.cleaned_data['model_direction']=model_direction
            models=runModelSearch(model_form.cleaned_data, user.id)
        elif searchType=='seds' and sed_form.is_valid():
            sed_form.cleaned_data['generic_sed_order_by']=generic_sed_order_by
            sed_form.cleaned_data['generic_sed_direction']=generic_sed_direction
            sed_form.cleaned_data['connectivity_sed_order_by']=connectivity_sed_order_by
            sed_form.cleaned_data['connectivity_sed_direction']=connectivity_sed_direction
            sed_form.cleaned_data['erp_sed_order_by']=erp_sed_order_by
            sed_form.cleaned_data['erp_sed_direction']=erp_sed_direction
            sed_form.cleaned_data['imaging_sed_order_by']=imaging_sed_order_by
            sed_form.cleaned_data['imaging_sed_direction']=imaging_sed_direction
            seds=runSEDSearch(sed_form.cleaned_data, user.id)
            for idx,sedObj in enumerate(seds):
                if sedObj.type=='event related potential':
                    erpSEDs.append(ERPSED.objects.select_related('collator').get(id=sedObj.id))
                elif sedObj.type=='brain imaging':
                    imagingSEDs.append(BrainImagingSED.objects.select_related('collator').get(id=sedObj.id))
                elif sedObj.type=='connectivity':
                    connectivitySEDs.append(ConnectivitySED.objects.select_related('collator','target_region__nomenclature','source_region__nomenclature').prefetch_related('target_region__nomenclature__species','source_region__nomenclature__species').get(id=sedObj.id))
                elif sedObj.type=='generic':
                    genericSEDs.append(sedObj)
            if sed_form.cleaned_data['type']=='' or sed_form.cleaned_data['type']=='connectivity':
                cococmacConnSEDs=runCoCoMacSearch2(sed_form.cleaned_data, user.id)
                for connSED in cococmacConnSEDs:
                    connectivitySEDs.append(connSED)

            if sed_form.cleaned_data['type']=='' or sed_form.cleaned_data['type']=='brain imaging':
                bredeImagingSEDs=runBredeSearch(sed_form.cleaned_data, user.id)
                for imagingSED in bredeImagingSEDs:
                    imagingSEDs.append(imagingSED)
            if 'generic_sed_order_by' in sed_form.cleaned_data:
                if sed_form.cleaned_data['generic_sed_order_by']=='title':
                    genericSEDs.sort(key=lambda x: x.title,reverse=sed_form.cleaned_data['generic_sed_direction']=='descending')
                elif sed_form.cleaned_data['generic_sed_order_by']=='collator':
                    genericSEDs.sort(key=SED.get_collator_str,reverse=sed_form.cleaned_data['generic_sed_direction']=='descending')
                elif sed_form.cleaned_data['generic_sed_order_by']=='brief_description':
                    genericSEDs.sort(key=lambda x: x.brief_description,reverse=sed_form.cleaned_data['generic_sed_direction']=='descending')

            if 'connectivity_sed_order_by' in sed_form.cleaned_data:
                if sed_form.cleaned_data['connectivity_sed_order_by']=='title':
                    connectivitySEDs.sort(key=lambda x: x.title,reverse=sed_form.cleaned_data['connectivity_sed_direction']=='descending')
                elif sed_form.cleaned_data['connectivity_sed_order_by']=='collator':
                    connectivitySEDs.sort(key=ConnectivitySED.get_collator_str,reverse=sed_form.cleaned_data['connectivity_sed_direction']=='descending')
                elif sed_form.cleaned_data['connectivity_sed_order_by']=='brief_description':
                    connectivitySEDs.sort(key=lambda x: x.brief_description,reverse=sed_form.cleaned_data['connectivity_sed_direction']=='descending')

            if 'erp_sed_order_by' in sed_form.cleaned_data:
                if sed_form.cleaned_data['erp_sed_order_by']=='title':
                    erpSEDs.sort(key=lambda x: x.title,reverse=sed_form.cleaned_data['erp_sed_direction']=='descending')
                elif sed_form.cleaned_data['erp_sed_order_by']=='collator':
                    erpSEDs.sort(key=ERPSED.get_collator_str,reverse=sed_form.cleaned_data['erp_sed_direction']=='descending')
                elif sed_form.cleaned_data['erp_sed_order_by']=='brief_description':
                    erpSEDs.sort(key=lambda x: x.brief_description,reverse=sed_form.cleaned_data['erp_sed_direction']=='descending')

            if 'imaging_sed_order_by' in sed_form.cleaned_data:
                if sed_form.cleaned_data['imaging_sed_order_by']=='title':
                    imagingSEDs.sort(key=lambda x: x.title,reverse=sed_form.cleaned_data['imaging_sed_direction']=='descending')
                elif sed_form.cleaned_data['imaging_sed_order_by']=='collator':
                    imagingSEDs.sort(key=BrainImagingSED.get_collator_str,reverse=sed_form.cleaned_data['imaging_sed_direction']=='descending')
                elif sed_form.cleaned_data['imaging_sed_order_by']=='brief_description':
                    imagingSEDs.sort(key=lambda x: x.brief_description,reverse=sed_form.cleaned_data['imaging_sed_direction']=='descending')
            sedCoords=runSEDCoordSearch(imagingSEDs, sed_form.cleaned_data, user.id)

        elif searchType=='ssrs' and ssr_form.is_valid():
            ssr_form.cleaned_data['ssr_order_by']=ssr_order_by
            ssr_form.cleaned_data['ssr_direction']=ssr_direction
            ssrs=runSSRSearch(ssr_form.cleaned_data, user.id)
        elif searchType=='literature'and literature_form.is_valid():
            literature_form.cleaned_data['literature_order_by']=literature_order_by
            literature_form.cleaned_data['literature_direction']=literature_direction
            literature=runLiteratureSearch(literature_form.cleaned_data, user.id)
        elif searchType=='brain_regions' and brain_region_form.is_valid():            
            brain_region_form.cleaned_data['region_order_by']=region_order_by
            brain_region_form.cleaned_data['region_direction']=region_direction
            brain_regions=runBrainRegionSearch(brain_region_form.cleaned_data)
        elif searchType=='users' and user_form.is_valid():
            user_form.cleaned_data['user_order_by']=user_order_by
            user_form.cleaned_data['user_direction']=user_direction
            users=runUserSearch(user_form.cleaned_data, user.id)
        elif searchType=='workspaces' and workspace_form.is_valid():
            workspace_form.cleaned_data['workspace_order_by']=workspace_order_by
            workspace_form.cleaned_data['workspace_direction']=workspace_direction
            workspaces=runWorkspaceSearch(workspace_form.cleaned_data, user.id)
        else:
            form.cleaned_data['bop_order_by']=bop_order_by
            form.cleaned_data['bop_direction']=bop_direction
            form.cleaned_data['region_order_by']=region_order_by
            form.cleaned_data['region_direction']=region_direction
            form.cleaned_data['literature_order_by']=literature_order_by
            form.cleaned_data['literature_direction']=literature_direction
            form.cleaned_data['model_order_by']=model_order_by
            form.cleaned_data['model_direction']=model_direction
            form.cleaned_data['generic_sed_order_by']=generic_sed_order_by
            form.cleaned_data['generic_sed_direction']=generic_sed_direction
            form.cleaned_data['connectivity_sed_order_by']=connectivity_sed_order_by
            form.cleaned_data['connectivity_sed_direction']=connectivity_sed_direction
            form.cleaned_data['erp_sed_order_by']=erp_sed_order_by
            form.cleaned_data['erp_sed_direction']=erp_sed_direction
            form.cleaned_data['imaging_sed_order_by']=imaging_sed_order_by
            form.cleaned_data['imaging_sed_direction']=imaging_sed_direction
            form.cleaned_data['ssr_order_by']=ssr_order_by
            form.cleaned_data['ssr_direction']=ssr_direction
            form.cleaned_data['user_order_by']=user_order_by
            form.cleaned_data['user_direction']=user_direction
            form.cleaned_data['workspace_order_by']=workspace_order_by
            form.cleaned_data['workspace_direction']=workspace_direction
            bops=runBOPSearch(form.cleaned_data, user.id)
            models=runModelSearch(form.cleaned_data, user.id)
            seds=runSEDSearch(form.cleaned_data, user.id)
            for idx,sedObj in enumerate(seds):
                if sedObj.type=='event related potential':
                    erpSEDs.append(ERPSED.objects.select_related('collator').get(id=sedObj.id))
                elif sedObj.type=='brain imaging':
                    imagingSEDs.append(BrainImagingSED.objects.select_related('collator').get(id=sedObj.id))
                elif sedObj.type=='connectivity':
                    connectivitySEDs.append(ConnectivitySED.objects.select_related('collator','target_region__nomenclature','source_region__nomenclature').prefetch_related('target_region__nomenclature__species','source_region__nomenclature__species').get(id=sedObj.id))
                elif sedObj.type=='generic':
                    genericSEDs.append(sedObj)
            cocomacConnSEDs=runCoCoMacSearch2(form.cleaned_data, user.id)
            for connSED in cocomacConnSEDs:
                connectivitySEDs.append(connSED)
            bredeImagingSEDs=runBredeSearch(form.cleaned_data, user.id)
            for imagingSED in bredeImagingSEDs:
                imagingSEDs.append(imagingSED)

            if 'generic_sed_order_by' in form.cleaned_data:
                if form.cleaned_data['generic_sed_order_by']=='title':
                    genericSEDs.sort(key=lambda x: x.title,reverse=form.cleaned_data['generic_sed_direction']=='descending')
                elif form.cleaned_data['generic_sed_order_by']=='collator':
                    genericSEDs.sort(key=SED.get_collator_str,reverse=form.cleaned_data['generic_sed_direction']=='descending')
                elif form.cleaned_data['generic_sed_order_by']=='brief_description':
                    genericSEDs.sort(key=lambda x: x.brief_description,reverse=form.cleaned_data['generic_sed_direction']=='descending')
                    
            if 'connectivity_sed_order_by' in form.cleaned_data:
                if form.cleaned_data['connectivity_sed_order_by']=='title':
                    connectivitySEDs.sort(key=lambda x: x.title,reverse=form.cleaned_data['connectivity_sed_direction']=='descending')
                elif form.cleaned_data['connectivity_sed_order_by']=='collator':
                    connectivitySEDs.sort(key=ConnectivitySED.get_collator_str,reverse=form.cleaned_data['connectivity_sed_direction']=='descending')
                elif form.cleaned_data['connectivity_sed_order_by']=='brief_description':
                    connectivitySEDs.sort(key=lambda x: x.brief_description,reverse=form.cleaned_data['connectivity_sed_direction']=='descending')

            if 'erp_sed_order_by' in form.cleaned_data:
                if form.cleaned_data['erp_sed_order_by']=='title':
                    erpSEDs.sort(key=lambda x: x.title,reverse=form.cleaned_data['erp_sed_direction']=='descending')
                elif form.cleaned_data['erp_sed_order_by']=='collator':
                    erpSEDs.sort(key=ERPSED.get_collator_str,reverse=form.cleaned_data['erp_sed_direction']=='descending')
                elif form.cleaned_data['erp_sed_order_by']=='brief_description':
                    erpSEDs.sort(key=lambda x: x.brief_description,reverse=form.cleaned_data['erp_sed_direction']=='descending')

            if 'imaging_sed_order_by' in form.cleaned_data:
                if form.cleaned_data['imaging_sed_order_by']=='title':
                    imagingSEDs.sort(key=lambda x: x.title,reverse=form.cleaned_data['imaging_sed_direction']=='descending')
                elif form.cleaned_data['imaging_sed_order_by']=='collator':
                    imagingSEDs.sort(key=BrainImagingSED.get_collator_str,reverse=form.cleaned_data['imaging_sed_direction']=='descending')
                elif form.cleaned_data['imaging_sed_order_by']=='brief_description':
                    imagingSEDs.sort(key=lambda x: x.brief_description,reverse=form.cleaned_data['imaging_sed_direction']=='descending')
                    
            sedCoords=runSEDCoordSearch(imagingSEDs, form.cleaned_data, user.id)

            ssrs=runSSRSearch(form.cleaned_data, user.id)
            workspaces=runWorkspaceSearch(form.cleaned_data, user.id)
            literature=runLiteratureSearch(form.cleaned_data, user.id)
            brain_regions=runBrainRegionSearch(form.cleaned_data)
            users=runUserSearch(form.cleaned_data, user.id)

        context['bops']=BOP.get_bop_list(bops, context['workspace_bops'], context['fav_docs'], context['subscriptions'])
        context['bop_relationships']=BOP.get_bop_relationships(bops, user)
        context['models']=Model.get_model_list(models, context['workspace_models'], context['fav_docs'],
            context['subscriptions'])
        context['model_seds']=Model.get_sed_map(models, user)
        context['generic_seds']=SED.get_sed_list(genericSEDs, context['workspace_seds'], context['fav_docs'],
            context['subscriptions'])
        context['erp_seds']=SED.get_sed_list(erpSEDs, context['workspace_seds'], context['fav_docs'],
            context['subscriptions'])
        context['erp_seds']=ERPSED.augment_sed_list(context['erp_seds'],
            [ERPComponent.objects.filter(erp_sed=erp_sed).select_related('electrode_cap','electrode_position__position_system') for erp_sed in erpSEDs])
        context['connectivity_seds']=SED.get_sed_list(connectivitySEDs, context['workspace_seds'], context['fav_docs'],
            context['subscriptions'])
        context['connectivity_sed_regions']=ConnectivitySED.get_region_map(connectivitySEDs)
        context['imaging_seds']=SED.get_sed_list(imagingSEDs, context['workspace_seds'], context['fav_docs'],
            context['subscriptions'])
        if user.is_authenticated() and not user.is_anonymous():
            context['imaging_seds']=BrainImagingSED.augment_sed_list(context['imaging_seds'],
                [sedCoords[sed.id] for sed in imagingSEDs],
                context['selected_sed_coords'].values_list('sed_coordinate__id',flat=True))
        else:
            context['imaging_seds']=BrainImagingSED.augment_sed_list(context['imaging_seds'],
                [sedCoords[sed.id] for sed in imagingSEDs], [])
        context['ssrs']=SSR.get_ssr_list(ssrs, context['workspace_ssrs'], context['fav_docs'], context['subscriptions'])
        context['literatures']=Literature.get_reference_list(literature,context['workspace_literature'],
            context['fav_lit'], context['subscriptions'])
        context['brain_regions']=BrainRegion.get_region_list(brain_regions,context['workspace_regions'],
            context['fav_regions'])
        context['users']=BodbProfile.get_user_list(users,user)
        context['workspaces']=Workspace.get_workspace_list(workspaces,user)

        if self.request.is_ajax():
            bop_list=[(selected,is_favorite,subscribed_to_user,bop.as_json())
                      for (selected,is_favorite,subscribed_to_user,bop) in context['bops']]
            bop_paginator=Paginator(bop_list,int(self.request.POST.get('bop-results_per_page','10')))
            bop_page=self.request.POST.get('bop_page')
            try:
                bops=bop_paginator.page(bop_page)
            except PageNotAnInteger:
                bops=bop_paginator.page(1)
            except EmptyPage:
                bops=bop_paginator.page(bop_paginator.num_pages)
            context['bop_relationships']=BOP.get_bop_relationships([x[3] for x in context['bops'][bops.start_index():bops.end_index()]], user)

            model_list=[(selected,is_favorite,subscribed_to_user,model.as_json())
                        for (selected,is_favorite,subscribed_to_user,model) in context['models']]
            model_paginator=Paginator(model_list,int(self.request.POST.get('model-results_per_page','10')))
            model_page=self.request.POST.get('model_page')
            try:
                models=model_paginator.page(model_page)
            except PageNotAnInteger:
                models=model_paginator.page(1)
            except EmptyPage:
                models=model_paginator.page(model_paginator.num_pages)
            context['model_seds']=Model.get_sed_map([x[3] for x in context['models'][models.start_index():models.end_index()]], user)

            ssr_list=[(selected,is_favorite,subscribed_to_user,ssr.as_json())
                      for (selected,is_favorite,subscribed_to_user,ssr) in context['ssrs']]
            ssr_paginator=Paginator(ssr_list,int(self.request.POST.get('ssr-results_per_page','10')))
            ssr_page=self.request.POST.get('ssr_page')
            try:
                ssrs=ssr_paginator.page(ssr_page)
            except PageNotAnInteger:
                ssrs=ssr_paginator.page(1)
            except EmptyPage:
                ssrs=ssr_paginator.page(ssr_paginator.num_pages)

            literature_list=[(selected,is_favorite,subscribed_to_user,reference.as_json())
                             for (selected,is_favorite,subscribed_to_user,reference) in context['literatures']]
            literature_paginator=Paginator(literature_list,int(self.request.POST.get('literature-results_per_page','10')))
            literature_page=self.request.POST.get('literature_page')
            try:
                literatures=literature_paginator.page(literature_page)
            except PageNotAnInteger:
                literatures=literature_paginator.page(1)
            except EmptyPage:
                literatures=literature_paginator.page(literature_paginator.num_pages)
                
            brain_region_list=[(selected,is_favorite,region.as_json())
                               for (selected,is_favorite,region) in context['brain_regions']]
            brain_region_paginator=Paginator(brain_region_list,int(self.request.POST.get('brain_region-results_per_page','10')))
            brain_region_page=self.request.POST.get('brain_region_page')
            try:
                brain_regions=brain_region_paginator.page(brain_region_page)
            except PageNotAnInteger:
                brain_regions=brain_region_paginator.page(1)
            except EmptyPage:
                brain_regions=brain_region_paginator.page(brain_region_paginator.num_pages)
            
            user_list=[(subscribed_to_user,BodbProfile.as_json(u)) for (subscribed_to_user,u) in context['users']]
            user_paginator=Paginator(user_list,int(self.request.POST.get('user-results_per_page','10')))
            user_page=self.request.POST.get('user_page')
            try:
                users=user_paginator.page(user_page)
            except PageNotAnInteger:
                users=user_paginator.page(1)
            except EmptyPage:
                users=user_paginator.page(user_paginator.num_pages)

            workspace_list=[(subscribed_to_user,w.as_json()) for (subscribed_to_user,w) in context['workspaces']]
            workspace_paginator=Paginator(workspace_list,int(self.request.POST.get('workspace-results_per_page','10')))
            workspace_page=self.request.POST.get('workspace_page')
            try:
                workspaces=workspace_paginator.page(workspace_page)
            except PageNotAnInteger:
                workspaces=workspace_paginator.page(1)
            except EmptyPage:
                workspaces=workspace_paginator.page(workspace_paginator.num_pages)

            ajax_context={
                'bops': bops.object_list,
                'bop_relationships': context['bop_relationships'],
                'bops_count': bop_paginator.count,
                'bops_num_pages': bop_paginator.num_pages,
                'bops_page_number': bops.number,
                'bops_has_next': bops.has_next(),
                'bops_has_previous': bops.has_previous(),
                'bops_start_index':bops.start_index(),
                'bops_end_index': bops.end_index(),
                'models': models.object_list,
                'model_seds': context['model_seds'],
                'models_count': model_paginator.count,
                'models_num_pages': model_paginator.num_pages,
                'models_page_number': models.number,
                'models_has_next': models.has_next(),
                'models_has_previous': models.has_previous(),
                'models_start_index':models.start_index(),
                'models_end_index': models.end_index(),
                'generic_seds': [(selected,is_favorite,subscribed_to_user,sed.as_json())
                                 for (selected,is_favorite,subscribed_to_user,sed) in context['generic_seds']],
                'erp_seds': [(selected,is_favorite,subscribed_to_user,sed.as_json(),
                              [component.as_json() for component in components])
                             for (selected,is_favorite,subscribed_to_user,sed,components) in context['erp_seds']],
                'connectivity_seds': [(selected,is_favorite,subscribed_to_user,sed.as_json())
                                      for (selected,is_favorite,subscribed_to_user,sed) in context['connectivity_seds']],
                'connectivity_sed_regions': context['connectivity_sed_regions'],
                'imaging_seds': [(selected,is_favorite,subscribed_to_user,sed.as_json(),
                                  [(coord.as_json(),coord_selected) for (coord,coord_selected) in coords])
                                 for (selected,is_favorite,subscribed_to_user,sed,coords) in context['imaging_seds']],
                'ssrs': ssrs.object_list,
                'ssrs_count': ssr_paginator.count,
                'ssrs_num_pages': ssr_paginator.num_pages,
                'ssrs_page_number': ssrs.number,
                'ssrs_has_next': ssrs.has_next(),
                'ssrs_has_previous': ssrs.has_previous(),
                'ssrs_start_index':ssrs.start_index(),
                'ssrs_end_index': ssrs.end_index(),
                'literatures': literatures.object_list,
                'literatures_count': literature_paginator.count,
                'literatures_num_pages': literature_paginator.num_pages,
                'literatures_page_number': literatures.number,
                'literatures_has_next': literatures.has_next(),
                'literatures_has_previous': literatures.has_previous(),
                'literatures_start_index':literatures.start_index(),
                'literatures_end_index': literatures.end_index(),
                'brain_regions': brain_regions.object_list,
                'brain_regions_count': brain_region_paginator.count,
                'brain_regions_num_pages': brain_region_paginator.num_pages,
                'brain_regions_page_number': brain_regions.number,
                'brain_regions_has_next': brain_regions.has_next(),
                'brain_regions_has_previous': brain_regions.has_previous(),
                'brain_regions_start_index':brain_regions.start_index(),
                'brain_regions_end_index': brain_regions.end_index(),
                'users': users.object_list,
                'users_count': user_paginator.count,
                'users_num_pages': user_paginator.num_pages,
                'users_page_number': users.number,
                'users_has_next': users.has_next(),
                'users_has_previous': users.has_previous(),
                'users_start_index':users.start_index(),
                'users_end_index': users.end_index(),
                'workspaces': workspaces.object_list,
                'workspaces_count': workspace_paginator.count,
                'workspaces_num_pages': workspace_paginator.num_pages,
                'workspaces_page_number': workspaces.number,
                'workspaces_has_next': workspaces.has_next(),
                'workspaces_has_previous': workspaces.has_previous(),
                'workspaces_start_index': workspaces.start_index(),
                'workspaces_end_index': workspaces.end_index()
            }
            if bops.has_next():
                ajax_context['bops_next_page_number']=bops.next_page_number()
            if bops.has_previous():
                ajax_context['bops_previous_page_number']=bops.previous_page_number()
            if models.has_next():
                ajax_context['models_next_page_number']=models.next_page_number()
            if models.has_previous():
                ajax_context['models_previous_page_number']=models.previous_page_number()
            if ssrs.has_next():
                ajax_context['ssrs_next_page_number']=ssrs.next_page_number()
            if ssrs.has_previous():
                ajax_context['ssrs_previous_page_number']=ssrs.previous_page_number()
            if literatures.has_next():
                ajax_context['literatures_next_page_number']=literatures.next_page_number()
            if literatures.has_previous():
                ajax_context['literatures_previous_page_number']=literatures.previous_page_number()
            if brain_regions.has_next():
                ajax_context['brain_regions_next_page_number']=brain_regions.next_page_number()
            if brain_regions.has_previous():
                ajax_context['brain_regions_previous_page_number']=brain_regions.previous_page_number()
            if users.has_next():
                ajax_context['users_next_page_number']=users.next_page_number()
            if users.has_previous():
                ajax_context['users_previous_page_number']=users.previous_page_number()
            if workspaces.has_next():
                ajax_context['workspaces_next_page_number']=workspaces.next_page_number()
            if workspaces.has_previous():
                ajax_context['workspaces_previous_page_number']=workspaces.previous_page_number()
            ajax_context['bop_order_by']= bop_order_by
            ajax_context['bop_direction']= bop_direction
            ajax_context['region_order_by']= region_order_by
            ajax_context['region_direction']= region_direction
            ajax_context['literature_order_by']= literature_order_by
            ajax_context['literature_direction']= literature_direction
            ajax_context['model_order_by']= model_order_by
            ajax_context['model_direction']= model_direction
            ajax_context['generic_sed_order_by']=generic_sed_order_by
            ajax_context['generic_sed_direction']=generic_sed_direction
            ajax_context['connectivity_sed_order_by']=connectivity_sed_order_by
            ajax_context['connectivity_sed_direction']=connectivity_sed_direction
            ajax_context['erp_sed_order_by']=erp_sed_order_by
            ajax_context['erp_sed_direction']=erp_sed_direction
            ajax_context['imaging_sed_order_by']=imaging_sed_order_by
            ajax_context['imaging_sed_direction']=imaging_sed_direction
            ajax_context['ssr_order_by']= ssr_order_by
            ajax_context['ssr_direction']= ssr_direction
            ajax_context['user_order_by']= user_order_by
            ajax_context['user_direction']= user_direction
            ajax_context['workspace_order_by']= workspace_order_by
            ajax_context['workspace_direction']= workspace_direction
            ajax_context['up_image']= self.request.POST.get('up_image','')
            ajax_context['down_image']=self.request.POST.get('down_image','')

            return HttpResponse(json.dumps(ajax_context), content_type='application/json')
        return self.render_to_response(context)


class BOPSearchView(FormView):
    form_class=BOPSearchForm
    template_name='bodb/search/search.html'

    def get_context_data(self, **kwargs):
        context = super(BOPSearchView,self).get_context_data(**kwargs)
        context=set_context_workspace(context, self.request)
        context['helpPage']='search_data.html#bops'
        context['bop_search_form']=context.get('form')
        context['bopGraphId']='bopRelationshipDiagram'
        context['searchType']='bops'
        context['searchLabel']='Brain Operating Principles (BOPs)'
        context['exclude']=self.request.GET.get('exclude',None)
        context['ispopup']=('_popup' in self.request.GET)
        context['multiple']=('_multiple' in self.request.GET)

        return context

    def form_valid(self, form):
        context=self.get_context_data(form=form)
        user=self.request.user

        order_by=self.request.POST.get('bop_order_by','title')
        direction=self.request.POST.get('bop_direction','ascending')

        form.cleaned_data['bop_order_by']=order_by
        form.cleaned_data['bop_direction']=direction
        bops=runBOPSearch(form.cleaned_data, user.id, exclude=context['exclude'])

        context['bops']=BOP.get_bop_list(bops, context['workspace_bops'], context['fav_docs'], context['subscriptions'])
        context['bop_relationships']=BOP.get_bop_relationships(bops, user)

        if self.request.is_ajax():
            bop_list=[(selected,is_favorite,subscribed_to_user,bop.as_json())
                      for (selected,is_favorite,subscribed_to_user,bop) in context['bops']]
            bop_paginator=Paginator(bop_list,int(self.request.POST.get('results_per_page','10')))
            bop_page=self.request.POST.get('bop_page')
            try:
                bops=bop_paginator.page(bop_page)
            except PageNotAnInteger:
                bops=bop_paginator.page(1)
            except EmptyPage:
                bops=bop_paginator.page(bop_paginator.num_pages)

            ajax_context={
                'bops': bops.object_list,
                'bop_order_by': order_by,
                'bop_direction': direction,
                'up_image': self.request.POST.get('up_image',''),
                'down_image': self.request.POST.get('down_image',''),
                'bop_relationships': context['bop_relationships'],
                'bops_count': bop_paginator.count,
                'bops_num_pages': bop_paginator.num_pages,
                'bops_page_number': bops.number,
                'bops_has_next': bops.has_next(),
                'bops_has_previous': bops.has_previous(),
                'bops_start_index':bops.start_index(),
                'bops_end_index': bops.end_index(),
            }

            if bops.has_next():
                ajax_context['bops_next_page_number']=bops.next_page_number()
            if bops.has_previous():
                ajax_context['bops_previous_page_number']=bops.previous_page_number()
            return HttpResponse(json.dumps(ajax_context), content_type='application/json')
        return self.render_to_response(context)


class BrainRegionSearchView(FormView):
    form_class=BrainRegionSearchForm
    template_name='bodb/search/search.html'

    def get_form(self, form_class):
        """
        Returns an instance of the form to be used in this view.
        """
        genus_options=Species.get_genus_options()
        species_options=Species.get_species_options()
        return form_class(genus_options, species_options, **self.get_form_kwargs())

    def get_context_data(self, **kwargs):
        context = super(BrainRegionSearchView,self).get_context_data(**kwargs)
        context=set_context_workspace(context, self.request)
        user=self.request.user
        context['helpPage']='search_data.html#brain-regions'
        context['brain_region_search_form']=context.get('form')
        context['searchType']='brain_regions'
        context['searchLabel']='Brain Regions'
        context['ispopup']=('_popup' in self.request.GET)
        context['multiple']=('_multiple' in self.request.GET)
        if 'fieldName' in self.request.GET:
            context['fieldName']=self.request.GET['fieldName']
        return context

    def form_valid(self, form):
        order_by=self.request.POST.get('region_order_by','name')
        direction=self.request.POST.get('region_direction','ascending')

        form.cleaned_data['region_order_by']=order_by
        form.cleaned_data['region_direction']=direction

        brain_regions=runBrainRegionSearch(form.cleaned_data)

        # first request for search page - start with all record search
        context=self.get_context_data(form=form)
        user=self.request.user
        context['brain_regions']=BrainRegion.get_region_list(brain_regions,context['workspace_regions'],
            context['fav_regions'])
        if self.request.is_ajax():
            brain_region_list=[(selected,is_favorite,region.as_json())
                               for (selected,is_favorite,region) in context['brain_regions']]
            brain_region_paginator=Paginator(brain_region_list,int(self.request.POST.get('results_per_page','10')))
            brain_region_page=self.request.POST.get('brain_region_page')
            try:
                brain_regions=brain_region_paginator.page(brain_region_page)
            except PageNotAnInteger:
                brain_regions=brain_region_paginator.page(1)
            except EmptyPage:
                brain_regions=brain_region_paginator.page(brain_region_paginator.num_pages)
            ajax_context={
                'region_order_by': order_by,
                'region_direction': direction,
                'up_image': self.request.POST.get('up_image',''),
                'down_image': self.request.POST.get('down_image',''),
                'brain_regions': brain_regions.object_list,
                'brain_regions_count': brain_region_paginator.count,
                'brain_regions_num_pages': brain_region_paginator.num_pages,
                'brain_regions_page_number': brain_regions.number,
                'brain_regions_has_next': brain_regions.has_next(),
                'brain_regions_has_previous': brain_regions.has_previous(),
                'brain_regions_start_index':brain_regions.start_index(),
                'brain_regions_end_index': brain_regions.end_index(),
            }
            if brain_regions.has_next():
                ajax_context['brain_regions_next_page_number']=brain_regions.next_page_number()
            if brain_regions.has_previous():
                ajax_context['brain_regions_previous_page_number']=brain_regions.previous_page_number()
            return HttpResponse(json.dumps(ajax_context), content_type='application/json')
        return self.render_to_response(context)


class LiteratureSearchView(FormView):
    form_class=LiteratureSearchForm
    template_name='bodb/search/search.html'

    def get_context_data(self, **kwargs):
        context = super(LiteratureSearchView,self).get_context_data(**kwargs)
        context=set_context_workspace(context, self.request)
        user=self.request.user
        context['helpPage']='search_data.html#literature'
        context['literature_search_form']=context.get('form')
        context['searchType']='literature'
        context['searchLabel']='Literature'
        context['ispopup']=('_popup' in self.request.GET)
        context['multiple']=('_multiple' in self.request.GET)
        return context

    def form_valid(self, form):
        order_by=self.request.POST.get('literature_order_by','string')
        direction=self.request.POST.get('literature_direction','ascending')
        form.cleaned_data['literature_order_by']=order_by
        form.cleaned_data['literature_direction']=direction

        literatures=runLiteratureSearch(form.cleaned_data, self.request.user.id)

        # first request for search page - start with all record search
        context=self.get_context_data(form=form)
        context['literatures']=Literature.get_reference_list(literatures,context['workspace_literature'],
            context['fav_lit'], context['subscriptions'])
        if self.request.is_ajax():
            literature_list=[(selected,is_favorite,subscribed_to_user,reference.as_json())
                             for (selected,is_favorite,subscribed_to_user,reference) in context['literatures']]
            literature_paginator=Paginator(literature_list,int(self.request.POST.get('results_per_page','10')))
            literature_page=self.request.POST.get('literature_page')
            try:
                literatures=literature_paginator.page(literature_page)
            except PageNotAnInteger:
                literatures=literature_paginator.page(1)
            except EmptyPage:
                literatures=literature_paginator.page(literature_paginator.num_pages)
            ajax_context={
                'literature_order_by': order_by,
                'literature_direction': direction,
                'up_image': self.request.POST.get('up_image',''),
                'down_image': self.request.POST.get('down_image',''),
                'literatures': literatures.object_list,
                'literatures_count': literature_paginator.count,
                'literatures_num_pages': literature_paginator.num_pages,
                'literatures_page_number': literatures.number,
                'literatures_has_next': literatures.has_next(),
                'literatures_has_previous': literatures.has_previous(),
                'literatures_start_index':literatures.start_index(),
                'literatures_end_index': literatures.end_index(),
            }
            if literatures.has_next():
                ajax_context['literatures_next_page_number']=literatures.next_page_number()
            if literatures.has_previous():
                ajax_context['literatures_previous_page_number']=literatures.previous_page_number()
            return HttpResponse(json.dumps(ajax_context), content_type='application/json')
        return self.render_to_response(context)


class ModelSearchView(FormView):
    form_class=ModelSearchForm
    template_name='bodb/search/search.html'

    def get_context_data(self, **kwargs):
        context = super(ModelSearchView,self).get_context_data(**kwargs)
        context=set_context_workspace(context, self.request)
        context['helpPage']='search_data.html#models'
        context['model_search_form']=context.get('form')
        context['searchType']='models'
        context['searchLabel']='Models'
        context['ispopup']=('_popup' in self.request.GET)
        context['multiple']=('_multiple' in self.request.GET)
        context['exclude']=self.request.GET.get('exclude',None)
        context['modelGraphId']='modelRelationshipDiagram'
        return context

    def form_valid(self, form):
        context=self.get_context_data(form=form)
        user=self.request.user

        order_by=self.request.POST.get('model_order_by','title')
        direction=self.request.POST.get('model_direction','ascending')

        form.cleaned_data['model_order_by']=order_by
        form.cleaned_data['model_direction']=direction

        models=runModelSearch(form.cleaned_data, user.id, exclude=context['exclude'])
        context['models']=Model.get_model_list(models, context['workspace_models'], context['fav_docs'],
            context['subscriptions'])
        context['model_seds']=Model.get_sed_map(models, user)

        if self.request.is_ajax():
            model_list=[(selected,is_favorite,subscribed_to_user,model.as_json())
                        for (selected,is_favorite,subscribed_to_user,model) in context['models']]
            model_paginator=Paginator(model_list,int(self.request.POST.get('results_per_page','10')))
            model_page=self.request.POST.get('model_page')
            try:
                models=model_paginator.page(model_page)
            except PageNotAnInteger:
                models=model_paginator.page(1)
            except EmptyPage:
                models=model_paginator.page(model_paginator.num_pages)
            ajax_context={
                'model_order_by': order_by,
                'model_direction': direction,
                'up_image': self.request.POST.get('up_image',''),
                'down_image': self.request.POST.get('down_image',''),
                'models': models.object_list,
                'model_seds': context['model_seds'],
                'models_count': model_paginator.count,
                'models_num_pages': model_paginator.num_pages,
                'models_page_number': models.number,
                'models_has_next': models.has_next(),
                'models_has_previous': models.has_previous(),
                'models_start_index':models.start_index(),
                'models_end_index': models.end_index(),
            }
            if models.has_next():
                ajax_context['models_next_page_number']=models.next_page_number()
            if models.has_previous():
                ajax_context['models_previous_page_number']=models.previous_page_number()
            return HttpResponse(json.dumps(ajax_context), content_type='application/json')
        return self.render_to_response(context)


class SEDSearchView(FormView):
    form_class=SEDSearchForm
    template_name='bodb/search/search.html'

    def get_context_data(self, **kwargs):
        context = super(SEDSearchView,self).get_context_data(**kwargs)
        context=set_context_workspace(context, self.request)
        user=self.request.user
        context['helpPage']='search_data.html#summary-of-experimental-data'
        context['sed_search_form']=context.get('form')
        context['searchType']='seds'
        context['searchLabel']='Summaries of Experimental Data (SEDs)'
        context['ispopup']=('_popup' in self.request.GET)
        context['multiple']=('_multiple' in self.request.GET)
        context['type']=self.request.GET.get('type',None)
        context['connectionGraphId']='connectivitySEDDiagram'
        context['erpGraphId']='erpSEDDiagram'

        return context

    def form_valid(self, form):
        context=self.get_context_data(form=form)
        user=self.request.user

        genericSEDs=[]
        connectivitySEDs=[]
        erpSEDs=[]
        imagingSEDs=[]

        generic_sed_order_by=self.request.POST.get('generic_sed_order_by','title')
        generic_sed_direction=self.request.POST.get('generic_sed_direction','ascending')
        erp_sed_order_by=self.request.POST.get('erp_sed_order_by','title')
        erp_sed_direction=self.request.POST.get('erp_sed_direction','ascending')
        connectivity_sed_order_by=self.request.POST.get('connectivity_sed_order_by','title')
        connectivity_sed_direction=self.request.POST.get('connectivity_sed_direction','ascending')
        imaging_sed_order_by=self.request.POST.get('imaging_sed_order_by','title')
        imaging_sed_direction=self.request.POST.get('imaging_sed_direction','ascending')

        form.cleaned_data['generic_sed_order_by']=generic_sed_order_by
        form.cleaned_data['generic_sed_direction']=generic_sed_direction
        form.cleaned_data['connectivity_sed_order_by']=connectivity_sed_order_by
        form.cleaned_data['connectivity_sed_direction']=connectivity_sed_direction
        form.cleaned_data['erp_sed_order_by']=erp_sed_order_by
        form.cleaned_data['erp_sed_direction']=erp_sed_direction
        form.cleaned_data['imaging_sed_order_by']=imaging_sed_order_by
        form.cleaned_data['imaging_sed_direction']=imaging_sed_direction

        seds=runSEDSearch(form.cleaned_data, user.id)
        for idx,sedObj in enumerate(seds):
            if sedObj.type=='event related potential':
                erpSEDs.append(ERPSED.objects.select_related('collator').get(id=sedObj.id))
            elif sedObj.type=='brain imaging':
                imagingSEDs.append(BrainImagingSED.objects.select_related('collator').get(id=sedObj.id))
            elif sedObj.type=='connectivity':
                connectivitySEDs.append(ConnectivitySED.objects.select_related('collator','target_region__nomenclature','source_region__nomenclature').prefetch_related('target_region__nomenclature__species','source_region__nomenclature__species').get(id=sedObj.id))
            elif sedObj.type=='generic':
                genericSEDs.append(sedObj)
        if form.cleaned_data['type']=='' or form.cleaned_data['type']=='connectivity':
            cocomacConnSEDs=runCoCoMacSearch2(form.cleaned_data, user.id)
            for connSED in cocomacConnSEDs:
                connectivitySEDs.append(connSED)
        if form.cleaned_data['type']=='' or form.cleaned_data['type']=='brain imaging':
            bredeImagingSEDs=runBredeSearch(form.cleaned_data, user.id)
            for imagingSED in bredeImagingSEDs:
                imagingSEDs.append(imagingSED)

        if 'generic_sed_order_by' in form.cleaned_data:
            if form.cleaned_data['generic_sed_order_by']=='title':
                genericSEDs.sort(key=lambda x: x.title,reverse=form.cleaned_data['generic_sed_direction']=='descending')
            elif form.cleaned_data['generic_sed_order_by']=='collator':
                genericSEDs.sort(key=SED.get_collator_str,reverse=form.cleaned_data['generic_sed_direction']=='descending')
            elif form.cleaned_data['generic_sed_order_by']=='brief_description':
                genericSEDs.sort(key=lambda x: x.brief_description,reverse=form.cleaned_data['generic_sed_direction']=='descending')

        if 'connectivity_sed_order_by' in form.cleaned_data:
            if form.cleaned_data['connectivity_sed_order_by']=='title':
                connectivitySEDs.sort(key=lambda x: x.title,reverse=form.cleaned_data['connectivity_sed_direction']=='descending')
            elif form.cleaned_data['connectivity_sed_order_by']=='collator':
                connectivitySEDs.sort(key=ConnectivitySED.get_collator_str,reverse=form.cleaned_data['connectivity_sed_direction']=='descending')
            elif form.cleaned_data['connectivity_sed_order_by']=='brief_description':
                connectivitySEDs.sort(key=lambda x: x.brief_description,reverse=form.cleaned_data['connectivity_sed_direction']=='descending')

        if 'erp_sed_order_by' in form.cleaned_data:
            if form.cleaned_data['erp_sed_order_by']=='title':
                erpSEDs.sort(key=lambda x: x.title,reverse=form.cleaned_data['erp_sed_direction']=='descending')
            elif form.cleaned_data['erp_sed_order_by']=='collator':
                erpSEDs.sort(key=ERPSED.get_collator_str,reverse=form.cleaned_data['erp_sed_direction']=='descending')
            elif form.cleaned_data['erp_sed_order_by']=='brief_description':
                erpSEDs.sort(key=lambda x: x.brief_description,reverse=form.cleaned_data['erp_sed_direction']=='descending')

        if 'imaging_sed_order_by' in form.cleaned_data:
            if form.cleaned_data['imaging_sed_order_by']=='title':
                imagingSEDs.sort(key=lambda x: x.title,reverse=form.cleaned_data['imaging_sed_direction']=='descending')
            elif form.cleaned_data['imaging_sed_order_by']=='collator':
                imagingSEDs.sort(key=BrainImagingSED.get_collator_str,reverse=form.cleaned_data['imaging_sed_direction']=='descending')
            elif form.cleaned_data['imaging_sed_order_by']=='brief_description':
                imagingSEDs.sort(key=lambda x: x.brief_description,reverse=form.cleaned_data['imaging_sed_direction']=='descending')
                
        sedCoords=runSEDCoordSearch(imagingSEDs, form.cleaned_data, user.id)

        # load selected sed ids
        context['generic_seds']=SED.get_sed_list(genericSEDs, context['workspace_seds'], context['fav_docs'],
            context['subscriptions'])
        context['erp_seds']=SED.get_sed_list(erpSEDs, context['workspace_seds'], context['fav_docs'],
            context['subscriptions'])
        context['erp_seds']=ERPSED.augment_sed_list(context['erp_seds'],
            [ERPComponent.objects.filter(erp_sed=erp_sed).select_related('electrode_cap','electrode_position__position_system') for erp_sed in erpSEDs])
        context['connectivity_seds']=SED.get_sed_list(connectivitySEDs, context['workspace_seds'], context['fav_docs'],
            context['subscriptions'])
        context['connectivity_sed_regions']=ConnectivitySED.get_region_map(connectivitySEDs)
        context['imaging_seds']=SED.get_sed_list(imagingSEDs, context['workspace_seds'], context['fav_docs'],
            context['subscriptions'])
        if user.is_authenticated() and not user.is_anonymous():
            context['imaging_seds']=BrainImagingSED.augment_sed_list(context['imaging_seds'],
                [sedCoords[sed.id] for sed in imagingSEDs],
                context['selected_sed_coords'].values_list('sed_coordinate__id',flat=True))
        else:
            context['imaging_seds']=BrainImagingSED.augment_sed_list(context['imaging_seds'],
                [sedCoords[sed.id] for sed in imagingSEDs], [])
        if self.request.is_ajax():
            ajax_context={
                'up_image': self.request.POST.get('up_image',''),
                'down_image': self.request.POST.get('down_image',''),
                'generic_seds': [(selected,is_favorite,subscribed_to_user,sed.as_json())
                                 for (selected,is_favorite,subscribed_to_user,sed) in context['generic_seds']],
                'erp_seds': [(selected,is_favorite,subscribed_to_user,sed.as_json(),
                              [component.as_json() for component in components])
                             for (selected,is_favorite,subscribed_to_user,sed,components) in context['erp_seds']],
                'connectivity_seds': [(selected,is_favorite,subscribed_to_user,sed.as_json())
                                      for (selected,is_favorite,subscribed_to_user,sed) in context['connectivity_seds']],
                'connectivity_sed_regions': context['connectivity_sed_regions'],
                'imaging_seds': [(selected,is_favorite,subscribed_to_user,sed.as_json(),
                                  [(coord.as_json(),coord_selected) for (coord, coord_selected) in coords])
                                 for (selected,is_favorite,subscribed_to_user,sed,coords) in context['imaging_seds']],
            }
            ajax_context['generic_sed_order_by']=generic_sed_order_by
            ajax_context['generic_sed_direction']=generic_sed_direction
            ajax_context['connectivity_sed_order_by']=connectivity_sed_order_by
            ajax_context['connectivity_sed_direction']=connectivity_sed_direction
            ajax_context['erp_sed_order_by']=erp_sed_order_by
            ajax_context['erp_sed_direction']=erp_sed_direction
            ajax_context['imaging_sed_order_by']=imaging_sed_order_by
            ajax_context['imaging_sed_direction']=imaging_sed_direction
            return HttpResponse(json.dumps(ajax_context), content_type='application/json')
        return self.render_to_response(context)


class ModelDBSearchView(FormView):
    form_class=ModelDBSearchForm
    template_name = 'bodb/search/search_modeldb.html'

    def get_context_data(self, **kwargs):
        context=super(ModelDBSearchView,self).get_context_data(**kwargs)
        context=set_context_workspace(context, self.request)
        context['helpPage']='insert_data.html#search-modeldb'
        context['ispopup']=('_popup' in self.request.GET)
        return context

    def form_valid(self, form):
        context=self.get_context_data()

        searchData={'keywords': form.cleaned_data['all']}
        results=runModelDBSearch(searchData, self.request.user.id)
        context['search_results']=results
        context['form']=form
        return self.render_to_response(context)

class PubmedSearchView(FormView):
    form_class=PubmedSearchForm
    template_name='bodb/search/search_pubmed.html'
    initial = {'start':0}
    # get 10 results at a time
    number=10

    def get_context_data(self, **kwargs):
        context = super(PubmedSearchView,self).get_context_data(**kwargs)
        context=set_context_workspace(context, self.request)
        context['helpPage']='insert_data.html#pubmed-search'
        context['ispopup']=('_popup' in self.request.GET)
        return context

    def form_valid(self, form):
        context=self.get_context_data()

        # get search phrase
        searchPhrase=''
        if len(form.cleaned_data['all']):
            for i,word in enumerate(form.cleaned_data['all'].split()):
                if not word in stop_words:
                    if i>0:
                        searchPhrase+='+AND+'
                    searchPhrase+='%s[tiab]' % word.replace(':','')
        if len(form.cleaned_data['journal']):
            if len(searchPhrase):
                searchPhrase+='+AND+'
            searchPhrase+='%s[ta]' % form.cleaned_data['journal']
        if len(form.cleaned_data['volume']):
            if len(searchPhrase):
                searchPhrase+='+AND+'
            searchPhrase+='%s[vi]' % form.cleaned_data['volume']
        if len(form.cleaned_data['authors']):
            if len(searchPhrase):
                searchPhrase+='+AND+'
            for i,word in enumerate(form.cleaned_data['authors'].split()):
                if i>0:
                    searchPhrase+='+AND+'
                searchPhrase+='%s[au]' % word
        if len(form.cleaned_data['issue']):
            if len(searchPhrase):
                searchPhrase+='+AND+'
            searchPhrase+='%s[ip]' % form.cleaned_data['issue']
        if len(form.cleaned_data['title']):
            if len(searchPhrase):
                searchPhrase+='+AND+'
            for i,word in enumerate(form.cleaned_data['title'].split()):
                if not word in stop_words:
                    if i>0:
                        searchPhrase+='+AND+'
                    searchPhrase+='%s[Title]' % word.replace(':','')
        minDate='1900'
        if len(form.cleaned_data['min_year']):
            minDate=form.cleaned_data['min_year']
        maxDate=str(datetime.datetime.now().year+1)
        if len(form.cleaned_data['max_year']):
            maxDate=form.cleaned_data['max_year']

        # get starting record
        start=int(form.cleaned_data['start'])

        # starting record of the previous page of results
        lastStart=start-self.number
        if lastStart<0:
            lastStart=0

        # total number of results (can be more than 10)
        total=0

        # if there is a search phrase
        search_results=[]
        if len(searchPhrase)>0:
            # get IDs of pubmed articles matching the search phrase
            id_handle=Entrez.esearch(db="pubmed", term=searchPhrase, retmax=self.number, retstart=start, mindate=minDate,
                maxdate=maxDate)
            id_records=Entrez.read(id_handle)
            # get the total number of results
            total=int(id_records['Count'])
            if total>0 and len(id_records['IdList']):
                # get the pubmed article associated with each ID
                article_handles=Entrez.esummary(db="pubmed", id=','.join(id_records['IdList']))
                article_records=Entrez.read(article_handles)
                # read each result
                for article_record in article_records:
                    # create a pubmedresult object
                    pm_result=PubMedResult()
                    pm_result.pubmedId=str(article_record['Id'])
                    if Literature.objects.filter(pubmed_id=pm_result.pubmedId).exists():
                        pm_result.exists=True
                    if 'AuthorList' in article_record:
                        pm_result.authors_display=", ".join(article_record['AuthorList'])
                        pm_result.authors=", ".join(article_record['AuthorList']).replace('\'', '\\\'')
                    if 'PubDate' in article_record:
                        pm_result.year=article_record['PubDate'].split(' ')[0]
                    if 'Title' in article_record:
                        pm_result.title_display=article_record['Title']
                        pm_result.title=article_record['Title'].replace('\'', '\\\'')
                    if 'Source' in article_record:
                        pm_result.journal_display=article_record['Source']
                        pm_result.journal=article_record['Source'].replace('\'', '\\\'')
                    if 'Volume' in article_record:
                        pm_result.volume=article_record['Volume']
                    if 'Issue' in article_record:
                        pm_result.issue=article_record['Issue']
                    if 'Pages' in article_record:
                        pm_result.pages=article_record['Pages']
                    if 'LangList' in article_record:
                        pm_result.language=", ".join(article_record['LangList'])
                    pm_result.url='http://www.ncbi.nlm.nih.gov/pubmed/'+article_record['Id']
                    search_results.append(pm_result)

        # calculate start and end index
        startIdx=start+1
        endIdx=start+len(search_results)

        # whether or not there are any more results to get (after this request)
        has_more=False
        if total>endIdx:
            has_more=True

        # return results and query terms to pubmed search template
        context['search_results']=search_results
        context['startIdx']=startIdx
        context['endIdx']=endIdx
        context['next_start']=str(start+self.number)
        context['last_start']=lastStart
        context['has_more']=has_more
        context['total']=total
        context['form']=form
        return self.render_to_response(context)




