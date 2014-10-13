from django.template.context import RequestContext
from django.template.loader import render_to_string
from django.http.response import HttpResponse
from django.views.generic import TemplateView, View
from django.views.generic.edit import BaseCreateView
from bodb.models import Model, BOP, SED, SSR, ConnectivitySED, BrainImagingSED, ERPSED, SEDCoord, SelectedSEDCoord, SavedSEDCoordSelection, Document, Prediction, ERPComponent, Literature, BrainRegion, NeurophysiologySED
from uscbp import settings
from uscbp.views import JSONResponseMixin

class BODBView(TemplateView):
    def get_context_data(self, **kwargs):
        context = super(BODBView, self).get_context_data(**kwargs)
        user=self.request.user
        context['can_add_entry']=False
        context['can_remove_entry']=False
        context['selected_coord_ids']=[]

        if user.is_authenticated() and not user.is_anonymous():
            selected_coords=SelectedSEDCoord.objects.filter(selected=True, user__id=user.id)
            for coord in selected_coords:
                context['selected_coord_ids'].append(coord.sed_coordinate.id)

            active_workspace=user.get_profile().active_workspace
            context['can_add_entry']=user.has_perm('add_entry',active_workspace)
            context['can_remove_entry']=user.has_perm('remove_entry',active_workspace)
        return context


class IndexView(BODBView):
    template_name = 'bodb/index.html'

    def get_context_data(self, **kwargs):
        context=super(IndexView,self).get_context_data(**kwargs)
        context['helpPage']='index.html'
        # load recently added entries
        context['models'] = Model.objects.filter(draft=0, public=1).order_by('-creation_time')[:4]
        context['bops'] = BOP.objects.filter(draft=0, public=1).order_by('-creation_time')[:4]
        context['seds'] = SED.objects.filter(draft=0, public=1).order_by('-creation_time')[:4]
        context['ssrs'] = SSR.objects.filter(draft=0, public=1).order_by('-creation_time')[:4]

        context['model_count']=Model.objects.filter(draft=0, public=1).count()
        context['bop_count']=BOP.objects.filter(draft=0, public=1).count()
        context['sed_count']=SED.objects.filter(draft=0, public=1).count()
        context['ssr_count']=SSR.objects.filter(draft=0, public=1).count()

        context['model_date']=''
        if Model.objects.filter(draft=0, public=1).count()>0:
            context['model_date']=Model.objects.filter(draft=0, public=1).order_by('-creation_time')[0].creation_time.strftime('%B %d, %Y')
        context['bop_date']=''
        if BOP.objects.filter(draft=0, public=1).count()>0:
            context['bop_date']=BOP.objects.filter(draft=0, public=1).order_by('-creation_time')[0].creation_time.strftime('%B %d, %Y')
        context['sed_date']=''
        if SED.objects.filter(draft=0, public=1).count()>0:
            context['sed_date']=SED.objects.filter(draft=0, public=1).order_by('-creation_time')[0].creation_time.strftime('%B %d, %Y')
        context['ssr_date']=''
        if SSR.objects.filter(draft=0, public=1).count()>0:
            context['ssr_date']=SSR.objects.filter(draft=0, public=1).order_by('-creation_time')[0].creation_time.strftime('%B %d, %Y')

        return context


class AboutView(BODBView):
    template_name = 'bodb/about.html'

    def get_context_data(self, **kwargs):
        context=super(BODBView,self).get_context_data(**kwargs)
        context['helpPage']='index.html'
        return context


class InsertView(BODBView):
    template_name = 'bodb/insert.html'

    def get_context_data(self, **kwargs):
        context=super(InsertView,self).get_context_data(**kwargs)
        context['helpPage']='insert_data.html'
        context['showTour']='show_tour' in self.request.GET
        return context


class DraftListView(BODBView):
    template_name = 'bodb/draft_list_view.html'

    def get_context_data(self, **kwargs):
        context=super(DraftListView,self).get_context_data(**kwargs)
        context['helpPage']='view_entry.html#drafts'
        user=self.request.user
        context['models']=Model.get_model_list(Model.objects.filter(collator=user,draft=1),user)
        context['bops']=BOP.get_bop_list(BOP.objects.filter(collator=user,draft=1),user)
        context['generic_seds']=SED.get_sed_list(SED.objects.filter(type='generic',collator=user,draft=1),user)
        context['connectivity_seds']=SED.get_sed_list(ConnectivitySED.objects.filter(collator=user,draft=1),user)
        imaging_seds=BrainImagingSED.objects.filter(collator=user,draft=1)
        coords=[SEDCoord.objects.filter(sed=sed) for sed in imaging_seds]
        context['imaging_seds']=SED.get_sed_list(imaging_seds,user)
        context['imaging_seds']=BrainImagingSED.augment_sed_list(context['imaging_seds'],coords)
        erp_seds=ERPSED.objects.filter(collator=user,draft=1)
        components=[ERPComponent.objects.filter(erp_sed=erp_sed) for erp_sed in erp_seds]
        context['erp_seds']=SED.get_sed_list(erp_seds, user)
        context['erp_seds']=ERPSED.augment_sed_list(context['erp_seds'],components)
        context['neurophysiology_seds']=SED.get_sed_list(NeurophysiologySED.objects.filter(collator=user,draft=1),user)
        context['ssrs']=SSR.get_ssr_list(SSR.objects.filter(collator=user,draft=1),user)

        context['connectionGraphId']='connectivitySEDDiagram'
        context['erpGraphId']='erpSEDDiagram'
        context['bopGraphId']='bopRelationshipDiagram'
        context['modelGraphId']='modelRelationshipDiagram'

        return context


class FavoriteListView(BODBView):
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
        context['bops']=[]
        context['generic_seds']=[]
        context['connectivity_seds']=[]
        context['imaging_seds']=[]
        context['erp_seds']=[]
        context['neurophysiology_seds']=[]
        context['ssrs']=[]

        if user.is_authenticated() and not user.is_anonymous():
            profile=user.get_profile()

            context['literatures']=Literature.get_reference_list(Literature.objects.filter(id__in=profile.favorite_literature.all()),user)
            context['brain_regions']=BrainRegion.get_region_list(BrainRegion.objects.filter(id__in=profile.favorite_regions.all()),user)
            context['models']=Model.get_model_list(Model.objects.filter(document_ptr__in=profile.favorites.all()),user)
            context['bops']=BOP.get_bop_list(BOP.objects.filter(document_ptr__in=profile.favorites.all()),user)
            context['generic_seds']=SED.get_sed_list(SED.objects.filter(type='generic',document_ptr__in=profile.favorites.all()),user)
            context['connectivity_seds']=SED.get_sed_list(ConnectivitySED.objects.filter(document_ptr__in=profile.favorites.all()),user)
            imaging_seds=BrainImagingSED.objects.filter(document_ptr__in=profile.favorites.all())
            coords=[SEDCoord.objects.filter(sed=sed) for sed in imaging_seds]
            context['imaging_seds']=SED.get_sed_list(imaging_seds,user)
            context['imaging_seds']=BrainImagingSED.augment_sed_list(context['imaging_seds'],coords)
            erp_seds=ERPSED.objects.filter(document_ptr__in=profile.favorites.all())
            components=[ERPComponent.objects.filter(erp_sed=erp_sed) for erp_sed in erp_seds]
            context['erp_seds']=SED.get_sed_list(erp_seds, user)
            context['erp_seds']=ERPSED.augment_sed_list(context['erp_seds'],components)
            context['neurophysiology_seds']=SED.get_sed_list(NeurophysiologySED.objects.filter(document_ptr__in=profile.favorites.all()),user)
            context['ssrs']=SSR.get_ssr_list(SSR.objects.filter(document_ptr__in=profile.favorites.all()),user)

            context['loaded_coord_selection']=profile.loaded_coordinate_selection
            context['saved_coord_selections']=SavedSEDCoordSelection.objects.filter(user=user)
            # load selected coordinates
            selected_coord_objs=SelectedSEDCoord.objects.filter(selected=True, user__id=user.id)

            context['selected_coords']=[]
            for coord in selected_coord_objs:
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
            selected_coord_ids=[]
            for coord in selected_coord_objs:
                selected_coord_ids.append(coord.sed_coordinate.id)
            context['selected_coord_ids']=selected_coord_ids
            context['can_delete_coord_selection']=True
            context['can_add_coord_selection']=True
            context['can_change_coord_selection']=True
        return context


class ToggleFavoriteView(JSONResponseMixin,BaseCreateView):
    model = Document

    def get_context_data(self, **kwargs):
        context={'msg':u'No POST data sent.' }
        if self.request.is_ajax():
            user=self.request.user
            if user.is_authenticated() and not user.is_anonymous():
                profile=user.get_profile()
                document_id=self.request.POST['id']
                context['icon_id']=self.request.POST['icon_id']
                if Document.objects.filter(id=document_id).count():
                    document=Document.objects.get(id=document_id)
                    if not profile.favorites.filter(id=document_id).count():
                        profile.favorites.add(document)
                        context['action']='added'
                    else:
                        profile.favorites.remove(document)
                        context['action']='removed'
                    profile.save()
            return context


class ToggleFavoriteBrainRegionView(JSONResponseMixin,BaseCreateView):
    model = BrainRegion

    def get_context_data(self, **kwargs):
        context={'msg':u'No POST data sent.' }
        if self.request.is_ajax():
            user=self.request.user
            if user.is_authenticated() and not user.is_anonymous():
                profile=user.get_profile()
                region_id=self.request.POST['id']
                context['icon_id']=self.request.POST['icon_id']
                if BrainRegion.objects.filter(id=region_id).count():
                    brain_region=BrainRegion.objects.get(id=region_id)
                    if not profile.favorite_regions.filter(id=region_id).count():
                        profile.favorite_regions.add(brain_region)
                        context['action']='added'
                    else:
                        profile.favorite_regions.remove(brain_region)
                        context['action']='removed'
                    profile.save()
            return context


class ToggleFavoriteLiteratureView(JSONResponseMixin,BaseCreateView):
    model = Literature

    def get_context_data(self, **kwargs):
        context={'msg':u'No POST data sent.' }
        if self.request.is_ajax():
            user=self.request.user
            if user.is_authenticated() and not user.is_anonymous():
                profile=user.get_profile()
                lit_id=self.request.POST['id']
                context['icon_id']=self.request.POST['icon_id']
                if Literature.objects.filter(id=lit_id).count():
                    lit=Literature.objects.get(id=lit_id)
                    if not profile.favorite_literature.filter(id=lit_id).count():
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

        context['tagged_bops']=BOP.get_bop_list(BOP.get_tagged_bops(name,user),user)
        context['tagged_models']=Model.get_model_list(Model.get_tagged_models(name, user),user)
        context['generic_seds']=SED.get_sed_list(SED.get_tagged_seds(name, user), user)
        context['connectivity_seds']=SED.get_sed_list(ConnectivitySED.get_tagged_seds(name, user),user)
        erp_seds=ERPSED.get_tagged_seds(name, user)
        components=[ERPComponent.objects.filter(erp_sed=erp_sed) for erp_sed in erp_seds]
        context['erp_seds']=SED.get_sed_list(erp_seds, user)
        context['erp_seds']=ERPSED.augment_sed_list(context['erp_seds'],components)
        imaging_seds=BrainImagingSED.get_tagged_seds(name, user)
        coords=[SEDCoord.objects.filter(sed=sed) for sed in imaging_seds]
        context['imaging_seds']=SED.get_sed_list(imaging_seds,user)
        context['imaging_seds']=BrainImagingSED.augment_sed_list(context['imaging_seds'],coords)
        context['neurophysiology_seds']=SED.get_sed_list(NeurophysiologySED.get_tagged_seds(name, user), user)
        context['tagged_predictions']=Prediction.get_prediction_list(Prediction.get_tagged_predictions(name, user), user)
        context['tagged_ssrs']=SSR.get_ssr_list(SSR.get_tagged_ssrs(name, user), user)

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