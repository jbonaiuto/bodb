from django.contrib.sites.models import get_current_site
from django.core.mail import EmailMessage
from django.shortcuts import redirect
from django.views.generic import ListView, CreateView, DetailView
from django.views.generic.edit import BaseCreateView, UpdateView, ModelFormMixin
from bodb.forms.admin import BrainRegionRequestForm, BrainRegionRequestDenyForm
from bodb.forms.brain_region import BrainRegionForm
from bodb.models import BrainRegionRequest, BrainRegion, SED, Message, BodbProfile, RelatedBOP, ConnectivitySED, RelatedModel, BrainImagingSED, ERPSED, SelectedSEDCoord, ERPComponent
from bodb.search.sed import runSEDCoordSearch
from uscbp.views import JSONResponseMixin

class BrainRegionRequestListView(ListView):
    model=BrainRegionRequest
    template_name = 'bodb/brainRegion/brain_region_request_list_view.html'

    def get_context_data(self, **kwargs):
        context=super(BrainRegionRequestListView,self).get_context_data(**kwargs)
        context['helpPage']='insert_data.html#requesting-a-brain-region'
        return context

    def get_queryset(self):
        return BrainRegionRequest.objects.filter(user=self.request.user)


class CreateBrainRegionRequestView(CreateView):
    model=BrainRegionRequest
    form_class = BrainRegionRequestForm
    template_name = 'bodb/brainRegion/brain_region_request_detail.html'

    def get_context_data(self, **kwargs):
        context = super(CreateBrainRegionRequestView,self).get_context_data(**kwargs)
        context['helpPage']='insert_data.html#requesting-a-brain-region'
        context['ispopup']=('_popup' in self.request.GET)
        return context

    def form_valid(self, form):
        self.object=form.save(commit=False)
        self.object.user=self.request.user
        self.object.save()

        return redirect('/bodb/index.html')


class CheckBrainRegionRequestExistsView(JSONResponseMixin,BaseCreateView):
    model = BrainRegionRequest

    def get_context_data(self, **kwargs):
        context={'msg':u'No POST data sent.' }
        if self.request.is_ajax() and 'name' in self.request.POST:
            name_str = self.request.POST['name']
            if not BrainRegionRequest.objects.filter(name=name_str).count():
                context = {'requestExists': '0'}
            else:
                context = {'requestExists': '1'}
        return context


class BrainRegionRequestDenyView(UpdateView):
    model=BrainRegionRequest
    template_name = 'bodb/brainRegion/brain_region_request_deny.html'
    pk_url_kwarg='activation_key'
    form_class = BrainRegionRequestDenyForm

    def get_context_data(self, **kwargs):
        context=super(BrainRegionRequestDenyView,self).get_context_data(**kwargs)
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

        message=Message(recipient=self.object.user, sender=self.request.user, subject=subject, read=False)
        message.text=text
        message.save()

        profile=BodbProfile.objects.get(user__id=self.object.user.id)
        if profile.new_message_notify:
            msg = EmailMessage(subject, text, 'uscbrainproject@gmail.com', [self.object.user.email])
            msg.content_subtype = "html"  # Main content is now text/html
            msg.send(fail_silently=True)
        context=self.get_context_data(form=form)
        context['msg']='Brain region request denial sent'
        return self.render_to_response(context)


class BrainRegionRequestApproveView(CreateView):
    model=BrainRegion
    template_name = 'bodb/brainRegion/brain_region_request_approve.html'
    form_class = BrainRegionForm

    def get_context_data(self, **kwargs):
        context=super(BrainRegionRequestApproveView,self).get_context_data(**kwargs)
        context['request']=BrainRegionRequest.objects.get(activation_key=self.kwargs.get('activation_key'))
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

        message=Message(recipient=context['request'].user, sender=self.request.user, subject=subject, read=False)
        message.text=text
        message.save()

        profile=BodbProfile.objects.get(user__id=context['request'].user.id)
        if profile.new_message_notify:
            msg = EmailMessage(subject, text, 'uscbrainproject@gmail.com', [context['request'].user.email])
            msg.content_subtype = "html"  # Main content is now text/html
            msg.send(fail_silently=True)

        return redirect(self.get_success_url())


class BrainRegionView(DetailView):
    model = BrainRegion
    template_name='bodb/brainRegion/brain_region_view.html'

    def get_context_data(self, **kwargs):
        context = super(BrainRegionView,self).get_context_data(**kwargs)

        user = self.request.user
        context['connectionGraphId']='connectivitySEDDiagram'
        context['erpGraphId']='erpSEDDiagram'
        context['generic_seds']=SED.get_sed_list(SED.get_brain_region_seds(self.object, user), user)
        imaging_seds=BrainImagingSED.get_brain_region_seds(self.object, user)
        search_data={'type':'brain imaging','coordinate_brain_region':self.object.name, 'search_options':'all'}
        sedCoords=runSEDCoordSearch(imaging_seds, search_data, user.id)
        coords=[]
        for sed in imaging_seds:
            if sed.id in sedCoords:
                coords.append(sedCoords[sed.id])
            else:
                coords.append([])
        context['imaging_seds']=SED.get_sed_list(imaging_seds,user)
        context['imaging_seds']=BrainImagingSED.augment_sed_list(context['imaging_seds'],coords)
        connectionSEDs=ConnectivitySED.get_brain_region_seds(self.object, user)
        context['connectivity_seds']=SED.get_sed_list(connectionSEDs, user)
        erp_seds=ERPSED.get_brain_region_seds(self.object, user)
        components=[ERPComponent.objects.filter(erp_sed=erp_sed) for erp_sed in erp_seds]
        context['erp_seds']=SED.get_sed_list(erp_seds, user)
        context['erp_seds']=ERPSED.augment_sed_list(context['erp_seds'],components)
        context['related_bops']=RelatedBOP.get_related_bop_list(RelatedBOP.get_brain_region_related_bops(self.object, user),user)
        context['related_models']=RelatedModel.get_related_model_list(RelatedModel.get_brain_region_related_models(self.object, user),user)
        context['helpPage']='view_entry.html'

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
