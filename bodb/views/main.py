from django.template.context import RequestContext
from django.template.loader import render_to_string
from django.http.response import HttpResponse
from django.views.generic import TemplateView, View
from django.views.generic.edit import BaseCreateView
from bodb.models import Model, BOP, SED, SSR, ConnectivitySED, BrainImagingSED, ERPSED, SEDCoord, SelectedSEDCoord, SavedSEDCoordSelection, Document, Prediction
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


class InsertView(BODBView):
    template_name = 'bodb/insert.html'

    def get_context_data(self, **kwargs):
        context=super(InsertView,self).get_context_data(**kwargs)
        context['helpPage']='BODB-Insert'
        return context


class DraftListView(BODBView):
    template_name = 'bodb/draft_list_view.html'

    def get_context_data(self, **kwargs):
        context=super(DraftListView,self).get_context_data(**kwargs)
        user=self.request.user
        context['models']=Model.get_model_list(Model.objects.filter(collator=user,draft=1),user)
        context['bops']=BOP.get_bop_list(BOP.objects.filter(collator=user,draft=1),user)
        context['generic_seds']=SED.get_sed_list(SED.objects.filter(type='generic',collator=user,draft=1),user)
        context['connectivity_seds']=SED.get_sed_list(ConnectivitySED.objects.filter(collator=user,draft=1),user)
        imaging_seds=BrainImagingSED.objects.filter(collator=user,draft=1)
        coords=[SEDCoord.objects.filter(sed=sed) for sed in imaging_seds]
        context['imaging_seds']=SED.get_sed_list(imaging_seds,user)
        context['imaging_seds']=BrainImagingSED.augment_sed_list(context['imaging_seds'],coords)
        context['erp_seds']=SED.get_sed_list(ERPSED.objects.filter(collator=user,draft=1),user)
        context['ssrs']=SSR.get_ssr_list(SSR.objects.filter(collator=user,draft=1),user)

        context['connectionGraphId']='connectivitySEDDiagram'
        context['bopGraphId']='bopRelationshipDiagram'

        return context


class FavoriteListView(BODBView):
    template_name = 'bodb/favorite_list_view.html'

    def get_context_data(self, **kwargs):
        context=super(FavoriteListView,self).get_context_data(**kwargs)
        user=self.request.user
        context['connectionGraphId']='connectionSEDDiagram'
        context['bopGraphId']='bopRelationshipDiagram'
        context['models']=[]
        context['bops']=[]
        context['generic_seds']=[]
        context['connectivity_seds']=[]
        context['imaging_seds']=[]
        context['erp_seds']=[]
        context['ssrs']=[]

        if user.is_authenticated() and not user.is_anonymous():
            profile=user.get_profile()
            active_workspace=profile.active_workspace

            context['models']=Model.get_model_list(Model.objects.filter(module_ptr__in=profile.favorites.all()),user)
            context['bops']=BOP.get_bop_list(BOP.objects.filter(document_ptr__in=profile.favorites.all()),user)
            context['generic_seds']=SED.get_sed_list(SED.objects.filter(type='generic',document_ptr__in=profile.favorites.all()),user)
            context['connectivity_seds']=SED.get_sed_list(ConnectivitySED.objects.filter(sed_ptr__in=profile.favorites.all()),user)
            imaging_seds=BrainImagingSED.objects.filter(sed_ptr__in=profile.favorites.all())
            coords=[SEDCoord.objects.filter(sed=sed) for sed in imaging_seds]
            context['imaging_seds']=SED.get_sed_list(imaging_seds,user)
            context['imaging_seds']=BrainImagingSED.augment_sed_list(context['imaging_seds'],coords)
            context['erp_seds']=SED.get_sed_list(ERPSED.objects.filter(sed_ptr__in=profile.favorites.all()),user)
            context['ssrs']=SSR.get_ssr_list(SSR.objects.filter(document_ptr__in=profile.favorites.all()),user)

            context['loaded_coord_selection']=profile.loaded_coordinate_selection
            context['saved_coord_selections']=SavedSEDCoordSelection.objects.filter(user=user)
            context['selected_coords']=[]
            if context['loaded_coord_selection'] is not None:
                for coord in SelectedSEDCoord.objects.filter(saved_selection=context['loaded_coord_selection']):
                    coord_array={'sed_id':coord.sed_coordinate.sed.id,
                                 'sed_name':coord.sed_coordinate.sed.title,
                                 'collator':coord.sed_coordinate.sed.get_collator_str(),
                                 'id':coord.id,
                                 'brain_region':coord.sed_coordinate.named_brain_region,
                                 'hemisphere':coord.sed_coordinate.hemisphere,
                                 'x':coord.sed_coordinate.coord.x,
                                 'y':coord.sed_coordinate.coord.y,
                                 'z':coord.sed_coordinate.coord.z,
                                 'rCBF':coord.sed_coordinate.rcbf,
                                 'statistic':coord.sed_coordinate.statistic,
                                 'statistic_value':coord.sed_coordinate.statistic_value,
                                 'extra_data':coord.sed_coordinate.extra_data}
                    context['selected_coords'].append(coord_array)
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


class TagView(BODBView):
    template_name = 'bodb/tag_view.html'

    def get_context_data(self, **kwargs):
        context=super(TagView,self).get_context_data(**kwargs)
        name = self.kwargs.get('name', None)
        user=self.request.user
        context['helpPage']='BODB-Tags'
        context['tag']=name

        context['tagged_bops']=BOP.get_bop_list(BOP.get_tagged_bops(name,user),user)
        context['tagged_models']=Model.get_model_list(Model.get_tagged_models(name, user),user)
        context['generic_seds']=SED.get_sed_list(SED.get_tagged_seds(name, user), user)
        context['connectivity_seds']=SED.get_sed_list(ConnectivitySED.get_tagged_seds(name, user),user)
        context['erp_seds']=SED.get_sed_list(ERPSED.get_tagged_seds(name, user),user)
        imaging_seds=BrainImagingSED.get_tagged_seds(name, user)
        coords=[SEDCoord.objects.filter(sed=sed) for sed in imaging_seds]
        context['imaging_seds']=SED.get_sed_list(imaging_seds,user)
        context['imaging_seds']=BrainImagingSED.augment_sed_list(context['imaging_seds'],coords)
        context['tagged_predictions']=Prediction.get_prediction_list(Prediction.get_tagged_predictions(name, user), user)
        context['tagged_ssrs']=SSR.get_ssr_list(SSR.get_tagged_ssrs(name, user), user)

        context['connectionGraphId']='connectivitySEDDiagram'
        context['bopGraphId']='bopRelationshipDiagram'
        return context


class BrainSurferView(View):

    def get(self, request, *args, **kwargs):
        response = HttpResponse(content_type='application/x-java-jnlp-file')
        response['Content-Disposition'] = 'attachment; filename="brainSurfer.jnlp"'
        jnlp_str=render_to_string("jws/brainSurferLaunch.jnlp",{'web_url': settings.URL_BASE,
                                                                'server': settings.SERVER},
            context_instance=RequestContext(request))
        response.write(jnlp_str)

        return response