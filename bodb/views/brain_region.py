from django.contrib.sites.models import get_current_site
from django.shortcuts import redirect, get_object_or_404
from django.views.generic import ListView, CreateView, DetailView
from django.views.generic.edit import BaseCreateView, ModelFormMixin, BaseUpdateView
from bodb.forms.admin import BrainRegionRequestForm, BrainRegionRequestDenyForm
from bodb.forms.brain_region import BrainRegionForm
from bodb.models import BrainRegionRequest, BrainRegion, SED, RelatedBOP, ConnectivitySED, RelatedModel, BrainImagingSED, ERPSED, ERPComponent, WorkspaceActivityItem, NeurophysiologySED, messageUser
from bodb.search.sed import runSEDCoordSearch
from bodb.views.main import set_context_workspace, get_active_workspace, get_profile
from bodb.views.security import AdminUpdateView, AdminCreateView
from guardian.mixins import LoginRequiredMixin
from uscbp.views import JSONResponseMixin
from bodb.views.document import DocumentAPIListView, DocumentAPIDetailView
from bodb.serializers import BrainRegionSerializer

class BrainRegionRequestListView(LoginRequiredMixin,ListView):
    model=BrainRegionRequest
    template_name = 'bodb/brainRegion/brain_region_request_list_view.html'

    def get_context_data(self, **kwargs):
        context=super(BrainRegionRequestListView,self).get_context_data(**kwargs)
        context=set_context_workspace(context, self.request)
        context['helpPage']='insert_data.html#requesting-a-brain-region'
        return context

    def get_queryset(self):
        return BrainRegionRequest.objects.filter(user=self.request.user).select_related('user')


class CreateBrainRegionRequestView(LoginRequiredMixin,CreateView):
    model=BrainRegionRequest
    form_class = BrainRegionRequestForm
    template_name = 'bodb/brainRegion/brain_region_request_detail.html'

    def get_context_data(self, **kwargs):
        context = super(CreateBrainRegionRequestView,self).get_context_data(**kwargs)
        context=set_context_workspace(context, self.request)
        context['helpPage']='insert_data.html#requesting-a-brain-region'
        context['ispopup']=('_popup' in self.request.GET)
        return context

    def form_valid(self, form):
        self.object=form.save(commit=False)
        self.object.user=self.request.user
        self.object.save()

        return redirect('/bodb/index.html')


class CheckBrainRegionRequestExistsView(LoginRequiredMixin,JSONResponseMixin,BaseCreateView):
    model = BrainRegionRequest

    def get_context_data(self, **kwargs):
        context={'msg':u'No POST data sent.' }
        if self.request.is_ajax() and 'name' in self.request.POST:
            name_str = self.request.POST['name']
            if not BrainRegionRequest.objects.filter(name=name_str).exists():
                context = {'requestExists': '0'}
            else:
                context = {'requestExists': '1'}
        return context


class BrainRegionRequestDenyView(AdminUpdateView):
    model=BrainRegionRequest
    template_name = 'bodb/brainRegion/brain_region_request_deny.html'
    pk_url_kwarg='activation_key'
    form_class = BrainRegionRequestDenyForm

    def get_context_data(self, **kwargs):
        context=super(BrainRegionRequestDenyView,self).get_context_data(**kwargs)
        context=set_context_workspace(context, self.request)
        context['helpPage']='insert_data.html#approve-deny-a-brain-region-admin-only'
        return context

    def get_form_kwargs(self):
        """
        Returns the keyword arguments for instantiating the form.
        """
        kwargs = super(ModelFormMixin, self).get_form_kwargs()
        return kwargs

    def get_object(self, queryset=None):
        return BrainRegionRequest.objects.get(activation_key=self.kwargs.get('activation_key'))

    def form_valid(self, form):
        self.object.status='denied'
        self.object.save()

        # message subject
        subject='Brain Region Request Denied'
        # message text
        text='Your request for the addition of the region: %s has been denied.<br>' % self.object.name
        text+='Reason for denial: %s' % self.request.POST['reason']

        messageUser(self.request.user, subject, text)

        context=self.get_context_data(form=form)
        context['msg']='Brain region request denial sent'
        return self.render_to_response(context)


class BrainRegionRequestApproveView(AdminCreateView):
    model=BrainRegion
    template_name = 'bodb/brainRegion/brain_region_request_approve.html'
    form_class = BrainRegionForm

    def get_context_data(self, **kwargs):
        context=super(BrainRegionRequestApproveView,self).get_context_data(**kwargs)
        context=set_context_workspace(context, self.request)
        context['request']=BrainRegionRequest.objects.select_related('user').get(activation_key=self.kwargs.get('activation_key'))
        context['helpPage']='insert_data.html#approve-deny-a-brain-region-admin-only'
        return context

    def get_initial(self):
        context=self.get_context_data()
        initial=super(BrainRegionRequestApproveView,self).get_initial()
        initial['name']=context['request'].name
        initial['abbreviation']=context['request'].abbreviation
        return initial

    def form_valid(self, form):
        context=self.get_context_data(form=form)

        self.object=form.save()
        context['request'].status='approved'
        context['request'].save()

        # message subject
        subject='Brain Region Request Approved'
        # message text
        region_url = ''.join(
            ['http://', get_current_site(None).domain, '/bodb/brain_region/%d/' % self.object.id])
        text='Your request for the addition of the region: <a href="%s">%s</a> has been approved.<br>' % (region_url, self.object.name)

        messageUser(self.request.user, subject, text)


class BrainRegionAPIListView(DocumentAPIListView):
    serializer_class = BrainRegionSerializer
    model = BrainRegion

    def get_queryset(self):
        return BrainRegion.objects.all()
    
    
class BrainRegionAPIDetailView(DocumentAPIDetailView):    
    queryset = BrainRegion.objects.all()
    serializer_class = BrainRegionSerializer
    model = BrainRegion


class BrainRegionView(DetailView):
    model = BrainRegion
    template_name='bodb/brainRegion/brain_region_view.html'

    def get_object(self, queryset=None):
        return get_object_or_404(BrainRegion.objects.select_related('nomenclature__lit').prefetch_related('nomenclature__species','nomenclature__lit__authors__author'),id=self.kwargs.get(self.pk_url_kwarg, None))

    def get_context_data(self, **kwargs):
        context = super(BrainRegionView,self).get_context_data(**kwargs)
        context=set_context_workspace(context, self.request)
        user = self.request.user
        context['connectionGraphId']='connectivitySEDDiagram'
        context['erpGraphId']='erpSEDDiagram'
        context['generic_seds']=SED.get_sed_list(SED.get_brain_region_seds(self.object, user), context['profile'], context['active_workspace'])
        imaging_seds=BrainImagingSED.get_brain_region_seds(self.object, user)
        search_data={'type':'brain imaging','coordinate_brain_region':self.object.name, 'search_options':'all'}
        sedCoords=runSEDCoordSearch(imaging_seds, search_data, user.id)
        coords=[]
        for sed in imaging_seds:
            if sed.id in sedCoords:
                coords.append(sedCoords[sed.id])
            else:
                coords.append([])
        context['imaging_seds']=SED.get_sed_list(imaging_seds, context['profile'], context['active_workspace'])
        context['imaging_seds']=BrainImagingSED.augment_sed_list(context['imaging_seds'],coords, user)
        connectionSEDs=ConnectivitySED.get_brain_region_seds(self.object, user)
        context['connectivity_seds']=SED.get_sed_list(connectionSEDs, context['profile'], context['active_workspace'])
        context['connectivity_sed_regions']=ConnectivitySED.get_region_map(connectionSEDs)
        erp_seds=ERPSED.get_brain_region_seds(self.object, user)
        components=[ERPComponent.objects.filter(erp_sed=erp_sed).select_related('electrode_cap','electrode_position__position_system') for erp_sed in erp_seds]
        context['erp_seds']=SED.get_sed_list(erp_seds, context['profile'], context['active_workspace'])
        context['erp_seds']=ERPSED.augment_sed_list(context['erp_seds'],components)
        context['neurophysiology_seds']=SED.get_sed_list(NeurophysiologySED.get_brain_region_seds(self.object,user),context['profile'],context['active_workspace'])
        rbops=RelatedBOP.get_brain_region_related_bops(self.object, user)
        context['related_bops']=RelatedBOP.get_related_bop_list(rbops,context['profile'],context['active_workspace'])
        rmods=RelatedModel.get_brain_region_related_models(self.object, user)
        context['related_models']=RelatedModel.get_related_model_list(rmods,context['profile'],context['active_workspace'])
        context['helpPage']='view_entry.html'

        context['is_favorite']=False
        context['selected']=False

        if user.is_authenticated() and not user.is_anonymous():
            context['is_favorite']=context['profile'].favorite_regions.filter(id=self.object.id).exists()
            context['selected']=context['active_workspace'].related_regions.filter(id=self.object.id).exists()

        return context


class ToggleSelectBrainRegionView(LoginRequiredMixin,JSONResponseMixin,BaseUpdateView):
    model = BrainRegion

    def get_context_data(self, **kwargs):
        context={'msg':u'No POST data sent.' }
        if self.request.is_ajax():
            region=BrainRegion.objects.get(id=self.kwargs.get('pk', None))

            active_workspace=get_active_workspace(get_profile(self.request),self.request)

            context={
                'region_id':region.id,
                'workspace': active_workspace.title
            }

            activity=WorkspaceActivityItem(workspace=active_workspace, user=self.request.user)
            remove=False
            if 'select' in self.request.POST:
                remove=self.request.POST['select']=='false'
            else:
                remove=region in active_workspace.related_regions.all()
            if remove:
                active_workspace.related_regions.remove(region)
                context['selected']=False
                activity.text='%s removed the brain region: <a href="%s">%s</a> from the workspace' % (self.request.user.username, region.get_absolute_url(), region.__unicode__())
            else:
                active_workspace.related_regions.add(region)
                context['selected']=True
                activity.text='%s added the brain region: <a href="%s">%s</a> to the workspace' % (self.request.user.username, region.get_absolute_url(), region.__unicode__())
            activity.save()
            active_workspace.save()

        return context