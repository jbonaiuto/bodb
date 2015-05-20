from django.db.models import Max, Min
from django.shortcuts import redirect
from django.template.context import RequestContext
from django.template.loader import render_to_string
from django.http.response import HttpResponse
from django.views.generic import TemplateView, View
from django.views.generic.edit import BaseCreateView
from bodb.models import Model, BOP, SED, SSR, ConnectivitySED, BrainImagingSED, ERPSED, SEDCoord, SelectedSEDCoord, SavedSEDCoordSelection, Document, Prediction, ERPComponent, Literature, BrainRegion, Workspace, BodbProfile, UserSubscription
from guardian.mixins import LoginRequiredMixin
from uscbp import settings
from uscbp.views import JSONResponseMixin
from django.core.cache import cache

def get_profile(request):
    profile=None
    if request.user.is_authenticated() and not request.user.is_anonymous():
        profile = cache.get('%d.profile' % request.user.id)
        if not profile:
            profile = BodbProfile.objects.select_related('active_workspace',
                'loaded_coordinate_selection__last_modified_by', 'loaded_coordinate_selection__user', 'user').get(
                user__id=request.user.id)
            cache.set('%d.profile' % request.user.id, profile)
    return profile


def get_active_workspace(user_profile, request):
    active_workspace = None
    if request.user.is_authenticated() and not request.user.is_anonymous():
        active_workspace = cache.get('%d.active_workspace' % request.user.id)
        if active_workspace is None:
            active_workspace = Workspace.objects.select_related('created_by', 'group', 'forum').get(id=user_profile.active_workspace.id)
            cache.set('%d.active_workspace' % request.user.id, active_workspace)
    return active_workspace


def set_context_workspace(context, request):
    context['can_add_entry']=False
    context['can_remove_entry']=False
    context['active_workspace']=None
    context['profile']=get_profile(request)
    context['active_workspace']=get_active_workspace(context['profile'], request)
    context['fav_lit']=[]
    context['fav_regions']=[]
    context['fav_docs']=[]
    context['subscriptions']=[]
    context['workspace_literature']=[]
    context['workspace_regions']=[]
    context['workspace_models']=[]
    context['workspace_bops']=[]
    context['workspace_seds']=[]
    context['workspace_ssrs']=[]
    context['selected_sed_coords']=[]
    if request.user.is_authenticated() and not request.user.is_anonymous():
        context['can_add_entry'] = request.user.has_perm('add_entry', context['active_workspace'])
        context['can_remove_entry'] = request.user.has_perm('remove_entry', context['active_workspace'])
        context['fav_lit']=context['profile'].favorite_literature.all().values_list('id',flat=True)
        context['fav_regions']=context['profile'].favorite_regions.all().values_list('id',flat=True)
        context['fav_docs']=context['profile'].favorites.all().values_list('id',flat=True)
        context['subscriptions']=UserSubscription.objects.filter(user=context['profile'].user,).values_list('subscribed_to_user__id','model_type')
        context['workspace_literature']=context['active_workspace'].related_literature.all().values_list('id',flat='True')
        context['workspace_regions']=context['active_workspace'].related_regions.all().values_list('id',flat=True)
        context['workspace_models']=context['active_workspace'].related_models.all().values_list('id',flat=True)
        context['workspace_bops']=context['active_workspace'].related_bops.all().values_list('id',flat=True)
        context['workspace_seds']=context['active_workspace'].related_seds.all().values_list('id',flat=True)
        context['workspace_ssrs']=context['active_workspace'].related_ssrs.all().values_list('id',flat=True)
        context['selected_sed_coords']=SelectedSEDCoord.objects.filter(selected=True, user__id=context['profile'].user.id).select_related('sed_coordinate__coord','sed_coordinate__sed','user')
    return context


class BODBView(TemplateView):

    def get_context_data(self, **kwargs):
        context=super(BODBView,self).get_context_data()
        context=set_context_workspace(context, self.request)
        return context


class IndexView(BODBView):
    template_name = 'bodb/index.html'

    def get(self, request, *args, **kwargs):
        user=request.user
        if user.is_authenticated() and not user.is_anonymous() and user.id>-1 and request.COOKIES.get('index_page_tour_seen')=='TRUE' and not request.GET.get('ignore_redirect',0)=='1':
            return redirect('/bodb/workspace/active/')
        else:
            return TemplateView.get(self, request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context=super(IndexView,self).get_context_data(**kwargs)
        context['helpPage']='index.html'
        # load recently added entries
        context['models'] = cache.get('recent_models')
        if not context['models']:
            context['models']=list(Model.objects.filter(draft=0, public=1).order_by('-creation_time').prefetch_related('authors__author')[:4])
            cache.set('recent_models',context['models'])
        context['bops'] = cache.get('recent_bops')
        if not context['bops']:
            context['bops']=list(BOP.objects.filter(draft=0, public=1).order_by('-creation_time')[:4])
            cache.set('recent_bops',context['bops'])
        context['seds'] = cache.get('recent_seds')
        if not context['seds']:
            context['seds']=list(SED.objects.filter(draft=0, public=1).order_by('-creation_time')[:4])
            cache.set('recent_seds',context['seds'])
        context['ssrs'] = cache.get('recent_ssrs')
        if not context['ssrs']:
            context['ssrs']=list(SSR.objects.filter(draft=0, public=1).order_by('-creation_time')[:4])
            cache.set('recent_ssrs',context['ssrs'])

        context['model_date']=cache.get('last_model_date')
        context['model_count']=cache.get('all_model_count')
        if not context['model_date']:
            context['model_date']=''
            public_models=Model.objects.filter(draft=0, public=1).order_by('-creation_time')
            context['model_count']=public_models.count()
            if context['model_count']>0:
                context['model_date']=public_models[0].creation_time.strftime('%B %d, %Y')
            cache.set('last_model_date', context['model_date'])
            cache.set('all_model_count', context['model_count'])

        context['bop_date']=cache.get('last_bop_date')
        context['bop_count']=cache.get('all_bop_count')
        if not context['bop_date']:
            context['bop_date']=''
            public_bops=BOP.objects.filter(draft=0, public=1).order_by('-creation_time')
            context['bop_count']=public_bops.count()
            if context['bop_count']>0:
                context['bop_date']=public_bops[0].creation_time.strftime('%B %d, %Y')
            cache.set('last_bop_date', context['bop_date'])
            cache.set('all_bop_count', context['bop_count'])

        context['sed_date']=cache.get('last_sed_date')
        context['sed_count']=cache.get('all_sed_count')
        if not context['sed_date']:
            context['sed_date']=''
            public_seds=SED.objects.filter(draft=0, public=1).order_by('-creation_time')
            context['sed_count']=public_seds.count()
            if context['sed_count']>0:
                context['sed_date']=public_seds[0].creation_time.strftime('%B %d, %Y')
            cache.set('last_sed_date', context['sed_date'])
            cache.set('all_sed_count', context['sed_count'])

        context['ssr_date']=cache.get('last_ssr_date')
        context['ssr_count']=cache.get('all_ssr_count')
        if not context['ssr_date']:
            context['ssr_date']=''
            public_ssrs=SSR.objects.filter(draft=0, public=1).order_by('-creation_time')
            context['ssr_count']=public_ssrs.count()
            if context['ssr_count']>0:
                context['ssr_date']=public_ssrs[0].creation_time.strftime('%B %d, %Y')
            cache.set('last_ssr_date', context['ssr_date'])
            cache.set('all_ssr_count', context['ssr_count'])

        return context


class AboutView(BODBView):
    template_name = 'bodb/about.html'

    def get_context_data(self, **kwargs):
        context=super(AboutView,self).get_context_data(**kwargs)
        context['helpPage']='index.html'
        return context


class InsertView(LoginRequiredMixin,BODBView):
    template_name = 'bodb/insert.html'

    def get_context_data(self, **kwargs):
        context=super(InsertView,self).get_context_data(**kwargs)
        context['helpPage']='insert_data.html'
        context['showTour']='show_tour' in self.request.GET
        return context


class DraftListView(LoginRequiredMixin,BODBView):
    template_name = 'bodb/draft_list_view.html'

    def get_context_data(self, **kwargs):
        context=super(DraftListView,self).get_context_data(**kwargs)
        context['helpPage']='view_entry.html#drafts'
        user=self.request.user

        models=Model.objects.filter(collator=user,draft=1).select_related('collator').prefetch_related('authors__author').order_by('title')
        context['models']=Model.get_model_list(models, context['workspace_models'], context['fav_docs'],
            context['subscriptions'])
        context['model_seds']=Model.get_sed_map(models, user)

        bops=BOP.objects.filter(collator=user,draft=1).select_related('collator').order_by('title')
        context['bops']=BOP.get_bop_list(bops, context['workspace_bops'], context['fav_docs'], context['subscriptions'])
        context['bop_relationships']=BOP.get_bop_relationships(bops, user)

        generic_seds=SED.objects.filter(type='generic',collator=user,draft=1).select_related('collator').order_by('title')
        context['generic_seds']=SED.get_sed_list(generic_seds, context['workspace_seds'], context['fav_docs'],
            context['subscriptions'])

        conn_seds=ConnectivitySED.objects.filter(collator=user,draft=1).select_related('collator','target_region__nomenclature','source_region__nomenclature').order_by('title')
        context['connectivity_seds']=SED.get_sed_list(conn_seds, context['workspace_seds'], context['fav_docs'],
            context['subscriptions'])
        context['connectivity_sed_regions']=ConnectivitySED.get_region_map(conn_seds)

        imaging_seds=BrainImagingSED.objects.filter(collator=user,draft=1).select_related('collator').order_by('title')
        coords=[SEDCoord.objects.filter(sed=sed).select_related('coord__threedcoord') for sed in imaging_seds]
        context['imaging_seds']=SED.get_sed_list(imaging_seds, context['workspace_seds'], context['fav_docs'],
            context['subscriptions'])
        if user.is_authenticated() and not user.is_anonymous():
            context['imaging_seds']=BrainImagingSED.augment_sed_list(context['imaging_seds'],coords,
                context['selected_sed_coords'].values_list('sed_coordinate__id',flat=True))
        else:
            context['imaging_seds']=BrainImagingSED.augment_sed_list(context['imaging_seds'],coords, [])

        erp_seds=ERPSED.objects.filter(collator=user,draft=1).select_related('collator').order_by('title')
        components=[ERPComponent.objects.filter(erp_sed=erp_sed).select_related('electrode_cap','electrode_position__position_system') for erp_sed in erp_seds]
        context['erp_seds']=SED.get_sed_list(erp_seds, context['workspace_seds'], context['fav_docs'],
            context['subscriptions'])
        context['erp_seds']=ERPSED.augment_sed_list(context['erp_seds'],components)

        ssrs=SSR.objects.filter(collator=user,draft=1).select_related('collator').order_by('title')
        context['ssrs']=SSR.get_ssr_list(ssrs, context['workspace_ssrs'], context['fav_docs'], context['subscriptions'])

        context['connectionGraphId']='connectivitySEDDiagram'
        context['erpGraphId']='erpSEDDiagram'
        context['bopGraphId']='bopRelationshipDiagram'
        context['modelGraphId']='modelRelationshipDiagram'

        return context


class FavoriteListView(LoginRequiredMixin,BODBView):
    template_name = 'bodb/favorite_list_view.html'

    def get_context_data(self, **kwargs):
        context=super(FavoriteListView,self).get_context_data(**kwargs)
        context['helpPage']='favorites.html'
        user=self.request.user
        context['connectionGraphId']='connectionSEDDiagram'
        context['erpGraphId']='erpSEDDiagram'
        context['bopGraphId']='bopRelationshipDiagram'
        context['modelGraphId']='modelRelationshipDiagram'
        context['literatures']=[]
        context['brain_regions']=[]
        context['models']=[]
        context['model_seds']=[]
        context['bops']=[]
        context['bop_relationships']=[]
        context['generic_seds']=[]
        context['connectivity_seds']=[]
        context['imaging_seds']=[]
        context['erp_seds']=[]
        context['ssrs']=[]

        if user.is_authenticated() and not user.is_anonymous():

            # load selected coordinates
            context['selected_coords']=[]
            for coord in context['selected_sed_coords']:
                coord_array={
                    'sed_name':coord.sed_coordinate.sed.title,
                    'sed_id':coord.sed_coordinate.sed.id,
                    'id':coord.id,
                    'collator':coord.get_collator_str(),
                    'collator_id':coord.user.id,
                    'brain_region':coord.sed_coordinate.named_brain_region,
                    'hemisphere':coord.sed_coordinate.hemisphere,
                    'x':coord.sed_coordinate.coord.x,
                    'y':coord.sed_coordinate.coord.y,
                    'z':coord.sed_coordinate.coord.z,
                    'rCBF':None,
                    'statistic':coord.sed_coordinate.statistic,
                    'statistic_value':None,
                    'extra_data':coord.sed_coordinate.extra_data
                }
                if coord.sed_coordinate.rcbf is not None:
                    coord_array['rCBF']=coord.sed_coordinate.rcbf.__float__()
                if coord.sed_coordinate.statistic_value is not None:
                    coord_array['statistic_value']=coord.sed_coordinate.statistic_value.__float__()
                context['selected_coords'].append(coord_array)

            # load selected coordinate Ids
            context['can_delete_coord_selection']=True
            context['can_add_coord_selection']=True
            context['can_change_coord_selection']=True

            literature=Literature.objects.filter(id__in=context['fav_lit']).select_related('collator').prefetch_related('authors__author')
            literature=list(literature)
            literature.sort(key=Literature.author_names)
            context['literatures']=Literature.get_reference_list(literature,context['workspace_literature'],
                context['fav_lit'], context['subscriptions'])

            brain_regions=BrainRegion.objects.filter(id__in=context['fav_regions']).select_related('nomenclature').prefetch_related('nomenclature__species').order_by('name')
            context['brain_regions']=BrainRegion.get_region_list(brain_regions,context['workspace_regions'],
                context['fav_regions'])

            models=Model.objects.filter(document_ptr__in=context['fav_docs']).select_related('collator').prefetch_related('authors__author').order_by('title')
            context['models']=Model.get_model_list(models, context['workspace_models'], context['fav_docs'],
                context['subscriptions'])
            context['model_seds']=Model.get_sed_map(models, user)

            bops=BOP.objects.filter(document_ptr__in=context['fav_docs']).select_related('collator').order_by('title')
            context['bops']=BOP.get_bop_list(bops, context['workspace_bops'], context['fav_docs'],
                context['subscriptions'])
            context['bop_relationships']=BOP.get_bop_relationships(bops, user)

            generic_seds=SED.objects.filter(type='generic',document_ptr__in=context['fav_docs']).select_related('collator').order_by('title')
            context['generic_seds']=SED.get_sed_list(generic_seds, context['workspace_seds'], context['fav_docs'],
                context['subscriptions'])

            conn_seds=ConnectivitySED.objects.filter(document_ptr__in=context['fav_docs']).select_related('collator','target_region__nomenclature','source_region__nomenclature').order_by('title')
            context['connectivity_seds']=SED.get_sed_list(conn_seds, context['workspace_seds'], context['fav_docs'],
                context['subscriptions'])
            context['connectivity_sed_regions']=ConnectivitySED.get_region_map(conn_seds)

            imaging_seds=BrainImagingSED.objects.filter(document_ptr__in=context['fav_docs']).select_related('collator').order_by('title')
            coords=[SEDCoord.objects.filter(sed=sed).select_related('coord__threedcoord') for sed in imaging_seds]
            context['imaging_seds']=SED.get_sed_list(imaging_seds, context['workspace_seds'], context['fav_docs'],
                context['subscriptions'])
            if user.is_authenticated() and not user.is_anonymous():
                context['imaging_seds']=BrainImagingSED.augment_sed_list(context['imaging_seds'],coords,
                    context['selected_sed_coords'].values_list('sed_coordinate__id',flat=True))
            else:
                context['imaging_seds']=BrainImagingSED.augment_sed_list(context['imaging_seds'],coords, [])

            erp_seds=ERPSED.objects.filter(document_ptr__in=context['fav_docs']).select_related('collator').order_by('title')
            components=[ERPComponent.objects.filter(erp_sed=erp_sed).select_related('electrode_cap','electrode_position__position_system') for erp_sed in erp_seds]
            context['erp_seds']=SED.get_sed_list(erp_seds, context['workspace_seds'], context['fav_docs'],
                context['subscriptions'])
            context['erp_seds']=ERPSED.augment_sed_list(context['erp_seds'],components)

            ssrs=SSR.objects.filter(document_ptr__in=context['fav_docs']).select_related('collator').order_by('title')
            context['ssrs']=SSR.get_ssr_list(ssrs, context['workspace_ssrs'], context['fav_docs'],
                context['subscriptions'])

            context['loaded_coord_selection']=context['profile'].loaded_coordinate_selection
            context['saved_coord_selections']=SavedSEDCoordSelection.objects.filter(user=user).select_related('user','last_modified_by')

        return context


class ToggleFavoriteView(LoginRequiredMixin,JSONResponseMixin,BaseCreateView):
    model = Document

    def get_context_data(self, **kwargs):
        context={'msg':u'No POST data sent.' }
        if self.request.is_ajax():
            user=self.request.user
            if user.is_authenticated() and not user.is_anonymous():
                profile=get_profile(self.request)
                document_id=self.request.POST['id']
                context['icon_id']=self.request.POST['icon_id']

                try:
                    document=Document.objects.get(id=document_id)
                except (Document.DoesNotExist, Document.MultipleObjectsReturned), err:
                    document=None

                if document is not None:
                    if not profile.favorites.filter(id=document_id).exists():
                        profile.favorites.add(document)
                        context['action']='added'
                    else:
                        profile.favorites.remove(document)
                        context['action']='removed'
                    profile.save()
            return context


class ToggleFavoriteBrainRegionView(LoginRequiredMixin,JSONResponseMixin,BaseCreateView):
    model = BrainRegion

    def get_context_data(self, **kwargs):
        context={'msg':u'No POST data sent.' }
        if self.request.is_ajax():
            user=self.request.user

            if user.is_authenticated() and not user.is_anonymous():
                profile=get_profile(self.request)
                region_id=self.request.POST['id']
                context['icon_id']=self.request.POST['icon_id']

                try:
                    brain_region=BrainRegion.objects.get(id=region_id)
                except (BrainRegion.DoesNotExist, BrainRegion.MultipleObjectsReturned), err:
                    brain_region=None

                if brain_region is not None:
                    if not profile.favorite_regions.filter(id=region_id).exists():
                        profile.favorite_regions.add(brain_region)
                        context['action']='added'
                    else:
                        profile.favorite_regions.remove(brain_region)
                        context['action']='removed'
                    profile.save()
            return context


class ToggleFavoriteLiteratureView(LoginRequiredMixin,JSONResponseMixin,BaseCreateView):
    model = Literature

    def get_context_data(self, **kwargs):
        context={'msg':u'No POST data sent.' }
        if self.request.is_ajax():
            user=self.request.user

            if user.is_authenticated() and not user.is_anonymous():
                profile=get_profile(self.request)
                lit_id=self.request.POST['id']
                context['icon_id']=self.request.POST['icon_id']

                try:
                    lit=Literature.objects.get(id=lit_id)
                except (Literature.DoesNotExist, Literature.MultipleObjectsReturned), err:
                    lit=None

                if lit is not None:
                    if not profile.favorite_literature.filter(id=lit_id).exists():
                        profile.favorite_literature.add(lit)
                        context['action']='added'
                    else:
                        profile.favorite_literature.remove(lit)
                        context['action']='removed'
                    profile.save()
            return context


class TagView(BODBView):
    template_name = 'bodb/tag_view.html'

    def get_context_data(self, **kwargs):
        context=super(TagView,self).get_context_data(**kwargs)
        name = self.kwargs.get('name', None)
        user=self.request.user
        context['helpPage']='tags.html'
        context['tag']=name

        bops=BOP.get_tagged_bops(name,user)
        context['tagged_bops']=BOP.get_bop_list(bops, context['workspace_bops'], context['fav_docs'],
            context['subscriptions'])
        models=Model.get_tagged_models(name, user)
        context['tagged_models']=Model.get_model_list(models, context['workspace_models'], context['fav_docs'],
            context['subscriptions'])
        generic_seds=SED.get_tagged_seds(name, user)
        context['generic_seds']=SED.get_sed_list(generic_seds, context['workspace_seds'], context['fav_docs'],
            context['subscriptions'])
        conn_seds=ConnectivitySED.get_tagged_seds(name, user)
        context['connectivity_seds']=SED.get_sed_list(conn_seds, context['workspace_seds'], context['fav_docs'],
            context['subscriptions'])
        context['connectivity_sed_regions']=ConnectivitySED.get_region_map(conn_seds)
        erp_seds=ERPSED.get_tagged_seds(name, user)
        components=[ERPComponent.objects.filter(erp_sed=erp_sed).select_related('electrode_cap','electrode_position__position_system') for erp_sed in erp_seds]
        context['erp_seds']=SED.get_sed_list(erp_seds, context['workspace_seds'], context['fav_docs'],
            context['subscriptions'])
        context['erp_seds']=ERPSED.augment_sed_list(context['erp_seds'],components)
        imaging_seds=BrainImagingSED.get_tagged_seds(name, user)
        coords=[SEDCoord.objects.filter(sed=sed).select_related('coord') for sed in imaging_seds]
        context['imaging_seds']=SED.get_sed_list(imaging_seds, context['workspace_seds'], context['fav_docs'],
            context['subscriptions'])
        context['imaging_seds']=BrainImagingSED.augment_sed_list(context['imaging_seds'],coords,
            context['selected_sed_coords'].values_list('sed_coordinate__id',flat=True))
        predictions=Prediction.get_tagged_predictions(name, user)
        context['tagged_predictions']=Prediction.get_prediction_list(predictions, context['workspace_ssrs'],
            context['fav_docs'], context['subscriptions'])
        ssrs=SSR.get_tagged_ssrs(name, user)
        context['tagged_ssrs']=SSR.get_ssr_list(ssrs, context['workspace_ssrs'], context['fav_docs'],
            context['subscriptions'])

        context['connectionGraphId']='connectivitySEDDiagram'
        context['erpGraphId']='erpSEDDiagram'
        context['bopGraphId']='bopRelationshipDiagram'
        context['modelGraphId']='modelRelationshipDiagram'
        return context


class BrainSurferView(View):

    def get(self, request, *args, **kwargs):
        jnlp_str=render_to_string("jws/brainSurferLaunch.jnlp",{'web_url': settings.URL_BASE,
                                                                'server': settings.SERVER,
                                                                'database': settings.DATABASES['default']['NAME']},
            context_instance=RequestContext(request))
        response = HttpResponse(jnlp_str, content_type='application/x-java-jnlp-file')
        response['Content-Disposition'] = 'attachment; filename="brainSurfer.jnlp"'
        return response