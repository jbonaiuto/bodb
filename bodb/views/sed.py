from django.contrib.sites.models import get_current_site
import os
from string import atof
from django.contrib.auth import login
import json
from django.http import HttpResponse
from django.shortcuts import redirect, get_object_or_404
from django.views.generic import CreateView, UpdateView, DeleteView, TemplateView, DetailView, View
from django.views.generic.detail import BaseDetailView
from django.views.generic.edit import BaseUpdateView, BaseCreateView
from bodb.forms.brain_region import RelatedBrainRegionFormSet
from bodb.forms.document import DocumentFigureFormSet
from bodb.forms.sed import SEDForm, BrainImagingSEDForm, SEDCoordCleanFormSet, ConnectivitySEDForm, ERPSEDForm, ERPComponentFormSet
from bodb.models import DocumentFigure, RelatedBrainRegion, RelatedBOP, ThreeDCoord, WorkspaceActivityItem, RelatedModel, ElectrodePositionSystem, ElectrodePosition, Document, Literature, Message
from bodb.models.sed import SED, find_similar_seds, ERPSED, ERPComponent, BrainImagingSED, SEDCoord, ConnectivitySED, SavedSEDCoordSelection, SelectedSEDCoord, BredeBrainImagingSED, CoCoMacConnectivitySED, ElectrodeCap
from bodb.views.document import DocumentAPIListView, DocumentAPIDetailView, DocumentDetailView
from bodb.views.main import set_context_workspace, BODBView, get_active_workspace, get_profile
from bodb.views.model import CreateModelView
from bodb.views.security import ObjectRolePermissionRequiredMixin
from guardian.mixins import PermissionRequiredMixin, LoginRequiredMixin
from guardian.shortcuts import assign_perm
from registration.models import User
from uscbp import settings
from uscbp.settings import MEDIA_ROOT
from uscbp.views import JSONResponseMixin
from bodb.serializers import SEDSerializer, ERPSEDSerializer, BrainImagingSEDSerializer, ConnectivitySEDSerializer
from django.http import HttpResponseForbidden
from django.core.cache import cache

class EditSEDMixin():
    model = SED
    form_class = SEDForm
    template_name = 'bodb/sed/generic/generic_sed_detail.html'

    def form_valid(self, form):
        context = self.get_context_data()
        figure_formset = context['figure_formset']
        related_brain_region_formset = context['related_brain_region_formset']

        if figure_formset.is_valid() and related_brain_region_formset.is_valid():

            self.object = form.save(commit=False)
            # Set collator if this is a new SED
            if self.object.id is None:
                self.object.collator=self.request.user
            self.object.last_modified_by=self.request.user
            self.object.save()
            # Needed for literature and tags
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
            params='?type='+context['type']+'&action='+context['action']
            if context['ispopup']:
                params+='&_popup=1'
            if context['multiple']:
                params+='&_multiple=1'
            url+=params

            return redirect(url)
        else:
            return self.render_to_response(self.get_context_data(form=form))


class CreateSEDView(EditSEDMixin, PermissionRequiredMixin, CreateView):
    permission_required='bodb.add_sed'

    def get_object(self, queryset=None):
        return None

    def get_context_data(self, **kwargs):
        context = super(CreateSEDView,self).get_context_data(**kwargs)
        context=set_context_workspace(context, self.request)
        context['figure_formset']=DocumentFigureFormSet(self.request.POST or None, self.request.FILES or None,
            prefix='figure')
        context['related_brain_region_formset']=RelatedBrainRegionFormSet(self.request.POST or None,
            prefix='related_brain_region')
        context['helpPage']='insert_data.html#insert-generic-sed'
        context['ispopup']=('_popup' in self.request.GET)
        context['action']='add'
        context['multiple']=('_multiple' in self.request.GET)
        context['type']=self.request.GET.get('type','')
        return context


class UpdateSEDView(EditSEDMixin, ObjectRolePermissionRequiredMixin, UpdateView):
    permission_required='edit'

    def get_object(self, queryset=None):
        if not hasattr(self,'object'):
            self.object=get_object_or_404(SED.objects.select_related('collator'),id=self.kwargs.get(self.pk_url_kwarg, None))
        return self.object

    def get_context_data(self, **kwargs):
        context = super(UpdateSEDView,self).get_context_data(**kwargs)
        context=set_context_workspace(context, self.request)
        context['figure_formset']=DocumentFigureFormSet(self.request.POST or None, self.request.FILES or None,
            instance=self.object, queryset=DocumentFigure.objects.filter(document=self.object), prefix='figure')
        context['related_brain_region_formset']=RelatedBrainRegionFormSet(self.request.POST or None,
            instance=self.object, queryset=RelatedBrainRegion.objects.filter(document=self.object).select_related('brain_region__nomenclature').prefetch_related('brain_region__nomenclature__species'),
            prefix='related_brain_region')
        context['references'] = self.object.literature.all().prefetch_related('authors__author')
        context['helpPage']='insert_data.html#insert-generic-sed'
        context['action']='edit'
        context['ispopup']=('_popup' in self.request.GET)
        context['multiple']=('_multiple' in self.request.GET)
        context['type']=self.request.GET.get('type','')
        return context


class DeleteSEDView(ObjectRolePermissionRequiredMixin,DeleteView):
    model=SED
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


class SEDAPIListView(DocumentAPIListView):
    serializer_class = SEDSerializer
    model = SED

    def get_queryset(self):
        user = self.request.user
        security_q=Document.get_security_q(user)
        return SED.objects.filter(security_q)


class ERPSEDAPIListView(DocumentAPIListView):
    serializer_class = ERPSEDSerializer
    model = ERPSED

    def get_queryset(self):
        user = self.request.user
        security_q=Document.get_security_q(user)
        return ERPSED.objects.filter(security_q)


class BrainImagingSEDAPIListView(DocumentAPIListView):
    serializer_class = BrainImagingSEDSerializer
    model = BrainImagingSED

    def get_queryset(self):
        user = self.request.user
        security_q=Document.get_security_q(user)
        return BrainImagingSED.objects.filter(security_q)


class ConnectivitySEDAPIListView(DocumentAPIListView):
    serializer_class = ConnectivitySEDSerializer
    model = ConnectivitySED

    def get_queryset(self):
        user = self.request.user
        security_q=Document.get_security_q(user)
        return ConnectivitySED.objects.filter(security_q)


class SEDAPIDetailView(ObjectRolePermissionRequiredMixin,DocumentAPIDetailView):
    serializer_class = SEDSerializer
    model = SED
    permission_required = 'view'

    def get(self, request, *args, **kwargs):
        id=self.kwargs.get('pk', None)
        type=SED.objects.get(id=id).type
        if type=='event related potential':
            self.serializer_class = ERPSEDSerializer
            self.model=ERPSED
        elif type=='brain imaging':
            self.serializer_class = BrainImagingSEDSerializer
            self.model=BrainImagingSED
            if BredeBrainImagingSED.objects.filter(id=id).exists():
                self.model=BredeBrainImagingSED
        elif type=='connectivity':
            self.serializer_class = ConnectivitySEDSerializer
            self.model=ConnectivitySED
            if CoCoMacConnectivitySED.objects.filter(id=id).exists():
                self.model=CoCoMacConnectivitySED
        self.queryset = self.model.objects.all()
        return super(SEDAPIDetailView, self).get(request, *args, **kwargs)


class SEDDetailView(ObjectRolePermissionRequiredMixin,DocumentDetailView):

    model = SED
    template_name = 'bodb/sed/generic/generic_sed_view.html'
    permission_required = 'view'

    def get_object(self, queryset=None):
        return get_object_or_404(self.model.objects.select_related('forum','collator','last_modified_by','coord_space','source__region__nomenclature','target_region__nomenclature'),id=self.kwargs.get(self.pk_url_kwarg, None))

    def get(self, request, *args, **kwargs):
        id=self.kwargs.get('pk', None)
        type=SED.objects.get(id=id).type
        if type=='event related potential':
            self.model=ERPSED
            self.template_name = 'bodb/sed/erp/erp_sed_view.html'
        elif type=='brain imaging':
            self.model=BrainImagingSED
            if BredeBrainImagingSED.objects.filter(id=id).exists():
                self.model=BredeBrainImagingSED
            self.template_name = 'bodb/sed/brain_imaging/brain_imaging_sed_view.html'
        elif type=='connectivity':
            self.model=ConnectivitySED
            if CoCoMacConnectivitySED.objects.filter(id=id).exists():
                self.model=CoCoMacConnectivitySED
            self.template_name = 'bodb/sed/connectivity/connectivity_sed_view.html'
        user = self.request.user
        security_q=Document.get_security_q(user)
        self.queryset = self.model.objects.all()
        return DetailView.get(self, request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(SEDDetailView, self).get_context_data(**kwargs)
        user=self.request.user
        context['helpPage']='view_entry.html'
        if self.object.type=='event related potential':
            context['erp_components'] = ERPComponent.objects.filter(erp_sed=self.object).select_related('electrode_cap','electrode_position__position_system')
        elif self.object.type=='connectivity':
            context['url']=self.object.html_url_string()
            context['connectivitysed']=self.object
        elif self.object.type=='brain imaging':
            context['url']=self.object.html_url_string()
            context['brainimagingsed']=self.object
            # load coordinates
            coords=SEDCoord.objects.filter(sed=self.object).select_related('coord')

            # create list of columns
            cols=['Brain Region','Hemisphere']
            header_str=self.object.core_header_1+' | '+self.object.core_header_2+' | '+self.object.core_header_3 +\
                       ' | '+self.object.core_header_4
            header_elems=header_str.split(' | ')
            for elem in header_elems:
                if not elem=='N/A' and not elem=='hemisphere':
                    cols.append(elem)
            if self.object.extra_header.find(' | ')>-1:
                extra_header_elems=self.object.extra_header.split(' | ')
            else:
                extra_header_elems=self.object.extra_header.split('|')
            for elem in extra_header_elems:
                cols.append(elem)
            context['cols']=cols

            # process each coordinate
            imagingData=[]
            for coord in coords:

                # create data row
                data_row=[str(coord.id)]
                data_row.append(coord.named_brain_region)
                data_row.append(coord.hemisphere)
                for col in header_elems:
                    if col=='x':
                        data_row.append(coord.coord.x)
                    elif col=='y':
                        data_row.append(coord.coord.y)
                    elif col=='z':
                        data_row.append(coord.coord.z)
                    elif col=='rCBF':
                        data_row.append(coord.rcbf)
                    elif col=='T' or col=='Z':
                        data_row.append(coord.statistic_value)
                if coord.extra_data.find(' | ')>-1:
                    extra_data=coord.extra_data.split(' | ')
                else:
                    extra_data=coord.extra_data.split('|')
                for elem in extra_data:
                    data_row.append(elem)

                # append row to data
                imagingData.append(data_row)
            context['data']=imagingData
            # load selected coordinate Ids
            context['selected_coords']=[]
            if user.is_authenticated() and not user.is_anonymous():
                for coord in context['selected_sed_coords']:
                    context['selected_coords'].append(str(coord.sed_coordinate.id))
        references=self.object.literature.all().select_related('collator').prefetch_related('authors__author')
        context['references'] = Literature.get_reference_list(references,context['workspace_literature'],
            context['fav_lit'], context['subscriptions'])
        rmods=RelatedModel.get_sed_related_models(self.object,user)
        context['related_models'] = RelatedModel.get_reverse_related_model_list(rmods, context['workspace_models'],
            context['fav_docs'], context['subscriptions'])
        rbops=RelatedBOP.get_sed_related_bops(self.object,user)
        context['related_bops'] = RelatedBOP.get_reverse_related_bop_list(rbops, context['workspace_bops'],
            context['fav_docs'], context['subscriptions'])
        context['subscribed_to_collator']=(self.object.collator.id, 'SED') in context['subscriptions']
        context['subscribed_to_last_modified_by']=(self.object.last_modified_by.id, 'SED') in context['subscriptions']
        context['selected']=self.object.id in context['workspace_seds']
        context['type']=self.request.GET.get('type',None)
        context['action']=self.request.GET.get('action',None)
        context['ispopup']=('_popup' in self.request.GET)
        context['multiple']=('_multiple' in self.request.GET)
        return context


class EditBrainImagingSEDMixin():
    model=BrainImagingSED
    form_class=BrainImagingSEDForm
    template_name='bodb/sed/brain_imaging/brain_imaging_sed_detail.html'

    def form_valid(self, form):
        context=self.get_context_data()
        figure_formset = context['figure_formset']
        related_brain_region_formset = context['related_brain_region_formset']

        if figure_formset.is_valid() and related_brain_region_formset.is_valid():

            self.object = form.save(commit=False)
            # Set collator if this is a new SED
            if self.object.id is None:
                self.object.collator=self.request.user
            self.object.last_modified_by=self.request.user
            self.object.save()
            # Needed for literature and tags
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


            # import coordinates - get index of each column
            brainRegionIdx=0
            hemisphereIdx=-1
            xIdx=-1
            yIdx=-1
            zIdx=-1
            rCBFIdx=-1
            tstatIdx=-1
            zstatIdx=-1
            col_string=self.object.core_header_1+' | '+self.object.core_header_2+' | '+self.object.core_header_3+' | '+self.object.core_header_4

            i=1
            for col in col_string.split(' | '):
                if col=='hemisphere':
                    hemisphereIdx=i
                elif col=='x':
                    xIdx=i
                elif col=='y':
                    yIdx=i
                elif col=='z':
                    zIdx=i
                elif col=='rCBF':
                    rCBFIdx=i
                elif col=='T':
                    tstatIdx=i
                elif col=='Z':
                    zstatIdx=i
                else:
                    continue
                i+=1

            # data rows
            if form.cleaned_data['data'].find('\r\n')>-1:
                data=form.cleaned_data['data'].split('\r\n')
            else:
                data=form.cleaned_data['data'].split('\n')

            # first clear coordinates from SED
            coords=SEDCoord.objects.filter(sed=self.object)
            for coord in coords:
                # delete selections of this coordinate
                SelectedSEDCoord.objects.filter(sed_coordinate=coord).delete()
                coord.delete()

            # process each row
            errorRows=[]
            idx=1

            for row in data:
                if len(row)>0:
                    # split row into columns
                    row_elems=[x.strip() for x in row.split('|')]

                    # create SED Coordinate from row data
                    coord=SEDCoord()
                    coord.named_brain_region=row_elems[brainRegionIdx]
                    if tstatIdx>-1:
                        coord.statistic='t'
                        if len(row_elems[tstatIdx])>0:
                            coord.statistic_value=row_elems[tstatIdx]
                    elif zstatIdx>-1:
                        coord.statistic='z'
                        if len(row_elems[zstatIdx])>0:
                            coord.statistic_value=row_elems[zstatIdx]
                    if rCBFIdx>-1:
                        coord.rcbf=row_elems[rCBFIdx]

                    x=0
                    y=0
                    z=0
                    if xIdx>-1:
                        x=float(row_elems[xIdx])
                    if yIdx>-1:
                        y=float(row_elems[yIdx])
                    if zIdx>-1:
                        z=float(row_elems[zIdx])

                    try:
                        coord.coord=ThreeDCoord.objects.get(x=x, y=y, z=z)
                    except (ThreeDCoord.DoesNotExist, ThreeDCoord.MultipleObjectsReturned), err:
                        coord.coord=None

                    if coord.coord is None:
                        realCoord=ThreeDCoord(x=x, y=y, z=z)
                        realCoord.save()
                        coord.coord=realCoord

                    if hemisphereIdx>-1:
                        coord.hemisphere=row_elems[hemisphereIdx]
                        if coord.hemisphere=='l' or coord.hemisphere=='L':
                            coord.hemisphere='left'
                        elif coord.hemisphere=='r' or coord.hemisphere=='R':
                            coord.hemisphere='right'
                        elif coord.hemisphere=='i' or coord.hemisphere=='I':
                            coord.hemisphere='interhemispheric'
                        if coord.hemisphere=='left' and atof(coord.coord.x)>=0:
                            errorRows.append(idx)
                        elif coord.hemisphere=='right' and atof(coord.coord.x)<=0:
                            errorRows.append(idx)
                        elif coord.hemisphere=='interhemispheric' and atof(coord.coord.x)!=0:
                            errorRows.append(idx)
                    else:
                        if atof(coord.coord.x)<0:
                            coord.hemisphere='left'
                        elif atof(coord.coord.x)>0:
                            coord.hemisphere='right'
                        else:
                            coord.hemisphere='interhemispheric'
                    coord.extra_data=''
                    j=0
                    while j+i<len(row_elems):
                        if j>0:
                            coord.extra_data+='|'
                        coord.extra_data+=row_elems[j+i]
                        j+=1

                    coord.sed=self.object

                    # save SED Coord
                    coord.save()
                idx += 1

            if len(errorRows)>0:
                url='/bodb/sed/imaging/%d/clean/' % self.object.id
                params='?type='+context['type']+'&action='+context['action']
                if context['ispopup']:
                    params+='&_popup=1'
                if context['multiple']:
                    params+='&_multiple=1'
                url+=params
                return redirect(url)
            else:
                url=self.get_success_url()
                params='?type='+context['type']+'&action='+context['action']
                if context['ispopup']:
                    params+='&_popup=1'
                if context['multiple']:
                    params+='&_multiple=1'
                url+=params
                return redirect(url)
        else:
            return self.render_to_response(self.get_context_data(form=form))


class CreateBrainImagingSEDView(EditBrainImagingSEDMixin, PermissionRequiredMixin, CreateView):
    permission_required='bodb.add_sed'

    def get_object(self, queryset=None):
        return None

    def get_initial(self):
        return {
            'core_header_1':'hemisphere',
            'core_header_2':'x y z',
            'core_header_3':'rCBF',
            'core_header_4':'Z'
        }

    def get_context_data(self, **kwargs):
        context = super(CreateBrainImagingSEDView,self).get_context_data(**kwargs)
        context=set_context_workspace(context, self.request)
        context['figure_formset']=DocumentFigureFormSet(self.request.POST or None, self.request.FILES or None,
            prefix='figure')
        context['related_brain_region_formset']=RelatedBrainRegionFormSet(self.request.POST or None,
            prefix='related_brain_region')
        context['helpPage']='insert_data.html#summary-of-brain-imaging-summary-data'
        context['ispopup']=('_popup' in self.request.GET)
        context['action']='add'
        context['multiple']=('_multiple' in self.request.GET)
        context['type']=self.request.GET.get('type','')
        return context


class UpdateBrainImagingSEDView(EditBrainImagingSEDMixin, ObjectRolePermissionRequiredMixin, UpdateView):
    permission_required='edit'

    def get_object(self, queryset=None):
        if not hasattr(self,'object'):
            self.object=get_object_or_404(BrainImagingSED.objects.select_related('collator','coord_space'),id=self.kwargs.get(self.pk_url_kwarg, None))
        return self.object

    def get_initial(self):
        # load coordinates
        coords=SEDCoord.objects.filter(sed=self.object).select_related('coord')

        # construct column list - core headers
        header_str=self.object.core_header_1+' | '+self.object.core_header_2+' | '+self.object.core_header_3 + ' | '+\
                   self.object.core_header_4
        header_elems=[x.strip() for x in header_str.split('|')]

        imagingDataStr=''
        # process coordinates
        for coord in coords:
            # put data in right order according to headers
            data_row=[]
            data_row_str=''
            data_row_str+=coord.named_brain_region
            for col in header_elems:
                if col=='hemisphere':
                    data_row.append(coord.hemisphere)
                    data_row_str+=' | '+coord.hemisphere
                elif col=='x':
                    data_row.append(coord.coord.x)
                    data_row_str+=' | '+str(coord.coord.x)
                elif col=='y':
                    data_row.append(coord.coord.y)
                    data_row_str+=' | '+str(coord.coord.y)
                elif col=='z':
                    data_row.append(coord.coord.z)
                    data_row_str+=' | '+str(coord.coord.z)
                elif col=='rCBF':
                    data_row.append(coord.rcbf)
                    data_row_str+=' | '+str(coord.rcbf)
                elif col=='T' or col=='Z':
                    data_row.append(coord.statistic_value)
                    data_row_str+=' | '+str(coord.statistic_value)
            extra_data=[x.strip() for x in coord.extra_data.split('|')]
            for elem in extra_data:
                if len(elem):
                    data_row.append(elem)
                    data_row_str+=' | '+elem

            if len(imagingDataStr)>0:
                imagingDataStr+='\n'
            imagingDataStr+=data_row_str
        return {'data': imagingDataStr}

    def get_context_data(self, **kwargs):
        context = super(UpdateBrainImagingSEDView,self).get_context_data(**kwargs)
        context=set_context_workspace(context, self.request)
        context['figure_formset']=DocumentFigureFormSet(self.request.POST or None, self.request.FILES or None,
            instance=self.object, queryset=DocumentFigure.objects.filter(document=self.object), prefix='figure')
        context['related_brain_region_formset']=RelatedBrainRegionFormSet(self.request.POST or None,
            instance=self.object, queryset=RelatedBrainRegion.objects.filter(document=self.object).select_related('brain_region__nomenclature').prefetch_related('brain_region__nomenclature__species'),
            prefix='related_brain_region')
        context['references'] = self.object.literature.all().prefetch_related('authors__author')
        context['helpPage']='insert_data.html#summary-of-brain-imaging-summary-data'
        context['action']='edit'
        context['ispopup']=('_popup' in self.request.GET)
        context['multiple']=('_multiple' in self.request.GET)
        context['type']=self.request.GET.get('type','')
        return context


class CleanBrainImagingSEDView(BODBView):
    template_name = 'bodb/sed/brain_imaging/brain_imaging_sed_clean.html'

    def get_initial(self):
        id=self.kwargs.get('pk', None)
        coords=SEDCoord.objects.filter(sed__id=id).select_related('coord')
        # look for errors in each coord
        init=[]
        for coord in coords:
            error=False
            row={'hemisphere_error':'0'}
            # check for mismatch hemisphere / coord
            if (coord.hemisphere=='left' and atof(coord.coord.x)>=0) or (coord.hemisphere=='right' and atof(coord.coord.x)<=0) or (coord.hemisphere=='interhemispheric' and atof(coord.coord.x)!=0):
                row['hemisphere_error']='1'
                error=True
                # add new SEDCoordForm data to initial
            if error:
                row['sed_coord_id']=coord.id
                row['coord_space']=coord.sed.coord_space
                init.append(row)
        return init

    def get(self, request, *args, **kwargs):
        id=self.kwargs.get('pk', None)
        init=self.get_initial()
        # create formset with initial data and POST data
        sedCoordCleanFormSet=SEDCoordCleanFormSet(initial=init)
        if len(init):
            # forward to sed clean view
            return self.render_to_response({'sedCoordCleanFormSet': sedCoordCleanFormSet,
                                            'ispopup': ('_popup' in request.GET),
                                            'helpPage':'insert_data.html#summary-of-brain-imaging-summary-data'})
        else:
            url='/bodb/sed/%s/' % id
            params='?type='+request.GET.get('type',None)+'&action='+request.GET.get('action',None)
            if '_popup' in request.GET:
                params+='&_popup=1'
            if '_multiple' in request.GET:
                params+='&_multiple=1'
            url+=params
            return redirect(url)

    def post(self, request, *args, **kwargs):
        id=self.kwargs.get('pk', None)
        # create formset with initial data and POST data
        sedCoordCleanFormSet=SEDCoordCleanFormSet(request.POST, initial=self.get_initial())
        # if valid
        if sedCoordCleanFormSet.is_valid():
            # update coords
            for form in sedCoordCleanFormSet.forms:
                coord=SEDCoord.objects.select_related('coord').get(id=form.cleaned_data['sed_coord_id'])
                if form.cleaned_data['hemisphere_error']=='1':
                    if form.cleaned_data['hemisphere_options']=='hemisphere':
                        if atof(coord.coord.x)<0:
                            coord.hemisphere='left'
                        elif not atof(coord.coord.x):
                            coord.hemisphere='interhemispheric'
                        elif atof(coord.coord.x)>0:
                            coord.hemisphere='right'
                    elif form.cleaned_data['hemisphere_options']=='coordinate':
                        if (coord.hemisphere=='left' and coord.coord.x>0) or (coord.hemisphere=='right' and coord.coord.x<0):
                            coord.coord.x*=-1
                        elif coord.hemisphere=='interhemispheric':
                            coord.coord.x=0
                coord.coord.save()
                coord.save()
                # forward to SED view
            url='/bodb/sed/%s/' % id
            params='?type='+request.GET.get('type','')+'&action='+request.GET.get('action','')
            if '_popup' in request.GET:
                params+='&_popup=1'
            if '_multiple' in request.GET:
                params+='&_multiple=1'
            url+=params
            return redirect(url)
            # forward to sed clean view
        return self.render_to_response({'sedCoordCleanFormSet': sedCoordCleanFormSet,
                                        'ispopup': ('_popup' in request.GET),
                                        'helpPage':'insert_data.html#summary-of-brain-imaging-summary-data'})


class DeleteBrainImagingSEDView(ObjectRolePermissionRequiredMixin, DeleteView):
    model=BrainImagingSED
    success_url = '/bodb/index.html'
    permission_required = 'delete'

    def get_context_data(self, **kwargs):
        context={}
        if 'idx' in self.request.POST:
            context['idx']=self.request.POST['idx']

        return context

    def post(self, request, *args, **kwargs):
        self.request=request
        self.delete(request, *args, **kwargs)
        return HttpResponse(json.dumps(self.get_context_data(**kwargs)), content_type='application/json')


class EditConnectivitySEDMixin():
    model = ConnectivitySED
    form_class = ConnectivitySEDForm
    template_name = 'bodb/sed/connectivity/connectivity_sed_detail.html'

    def form_valid(self, form):
        context=self.get_context_data()
        figure_formset = context['figure_formset']
        related_brain_region_formset = context['related_brain_region_formset']

        if figure_formset.is_valid() and related_brain_region_formset.is_valid():
            self.object = form.save(commit=False)
            # Set collator if this is a new SED
            if self.object.id is None:
                self.object.collator=self.request.user
            self.object.last_modified_by=self.request.user
            self.object.save()
            # Needed for literature and tags
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
            params='?type='+context['type']+'&action='+context['action']
            if context['ispopup']:
                params+='&_popup=1'
            if context['multiple']:
                params+='&_multiple=1'
            url+=params
            return redirect(url)
        else:
            return self.render_to_response(self.get_context_data(form=form))


class CreateConnectivitySEDView(EditConnectivitySEDMixin, PermissionRequiredMixin, CreateView):
    permission_required='bodb.add_sed'

    def get_object(self, queryset=None):
        return None

    def get_context_data(self, **kwargs):
        context = super(CreateConnectivitySEDView, self).get_context_data(**kwargs)
        context=set_context_workspace(context, self.request)
        context['figure_formset']=DocumentFigureFormSet(self.request.POST or None, self.request.FILES or None,
            prefix='figure')
        context['related_brain_region_formset']=RelatedBrainRegionFormSet(self.request.POST or None,
            prefix='related_brain_region')
        context['helpPage']='insert_data.html#summary-of-connectivity-data'
        context['ispopup']=('_popup' in self.request.GET)
        context['action']='add'
        context['multiple']=('_multiple' in self.request.GET)
        context['type']=self.request.GET.get('type','')
        return context


class UpdateConnectivitySEDView(EditConnectivitySEDMixin, ObjectRolePermissionRequiredMixin, UpdateView):
    permission_required='edit'

    def get_object(self, queryset=None):
        if not hasattr(self,'object'):
            self.object=get_object_or_404(ConnectivitySED.objects.select_related('collator','source_region__nomenclature','target_region__nomenclature').prefetch_related('source_region__nomenclature__species','target_region__nomenclature__species'),id=self.kwargs.get(self.pk_url_kwarg, None))
        return self.object

    def get_context_data(self, **kwargs):
        context = super(UpdateConnectivitySEDView,self).get_context_data(**kwargs)
        context=set_context_workspace(context, self.request)
        context['figure_formset']=DocumentFigureFormSet(self.request.POST or None, self.request.FILES or None,
            instance=self.object, queryset=DocumentFigure.objects.filter(document=self.object), prefix='figure')
        context['related_brain_region_formset']=RelatedBrainRegionFormSet(self.request.POST or None,
            instance=self.object, queryset=RelatedBrainRegion.objects.filter(document=self.object).select_related('brain_region__nomenclature').prefetch_related('brain_region__nomenclature__species'),
            prefix='related_brain_region')
        context['references'] = self.object.literature.all().prefetch_related('authors__author')
        context['helpPage']='insert_data.html#summary-of-connectivity-data'
        context['action']='edit'
        context['ispopup']=('_popup' in self.request.GET)
        context['multiple']=('_multiple' in self.request.GET)
        context['type']=self.request.GET.get('type','')
        return context


class DeleteConnectivitySEDView(ObjectRolePermissionRequiredMixin, DeleteView):
    model=ConnectivitySED
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


class EditERPSEDMixin():
    model = ERPSED
    form_class = ERPSEDForm
    template_name = 'bodb/sed/erp/erp_sed_detail.html'

    def form_valid(self, form):
        context = self.get_context_data()
        erp_component_formset = context['erp_component_formset']
        figure_formset = context['figure_formset']
        related_brain_region_formset = context['related_brain_region_formset']

        if figure_formset.is_valid() and related_brain_region_formset.is_valid() and erp_component_formset.is_valid():

            self.object = form.save(commit=False)
            # Set collator if this is a new SED
            if self.object.id is None:
                self.object.collator=self.request.user
            self.object.last_modified_by=self.request.user
            self.object.save()
            # Needed for literature and tags
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

            # save ERP components
            erp_component_formset.instance=self.object
            for erp_component_form in erp_component_formset.forms:
                if not erp_component_form in erp_component_formset.deleted_forms:
                    erp_component=erp_component_form.save(commit=False)
                    erp_component.erp_sed=self.object
                    erp_component.save()

            # delete removed ERP components
            for erp_component_form in erp_component_formset.deleted_forms:
                if erp_component_form.instance.id:
                    erp_component_form.instance.delete()

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
            params='?type='+context['type']+'&action='+context['action']
            if context['ispopup']:
                params+='&_popup=1'
            if context['multiple']:
                params+='&_multiple=1'
            url+=params
            return redirect(url)
        else:
            return self.render_to_response(self.get_context_data(form=form))


class CreateERPSEDView(EditERPSEDMixin, PermissionRequiredMixin, CreateView):
    permission_required='bodb.add_bop'

    def get_object(self, queryset=None):
        return None

    def get_context_data(self, **kwargs):
        context = super(CreateERPSEDView, self).get_context_data(**kwargs)
        context=set_context_workspace(context, self.request)
        context['electrode_position_systems']=ElectrodePositionSystem.objects.all()
        context['electrode_caps']=ElectrodeCap.objects.all()
        context['erp_component_formset']=ERPComponentFormSet(self.request.POST or None, prefix='erp_component')
        context['figure_formset']=DocumentFigureFormSet(self.request.POST or None, self.request.FILES or None,
            prefix='figure')
        context['related_brain_region_formset']=RelatedBrainRegionFormSet(self.request.POST or None,
            prefix='related_brain_region')
        context['helpPage']='insert_data.html#summary-of-event-related-potential-data'
        context['ispopup']=('_popup' in self.request.GET)
        context['action']='add'
        context['multiple']=('_multiple' in self.request.GET)
        context['type']=self.request.GET.get('type','')
        return context


class UpdateERPSEDView(EditERPSEDMixin, ObjectRolePermissionRequiredMixin, UpdateView):
    permission_required='edit'

    def get_object(self, queryset=None):
        if not hasattr(self,'object'):
            self.object=get_object_or_404(ERPSED.objects.select_related('collator'),id=self.kwargs.get(self.pk_url_kwarg, None))
        return self.object

    def get_context_data(self, **kwargs):
        context = super(UpdateERPSEDView,self).get_context_data(**kwargs)
        context=set_context_workspace(context, self.request)
        context['electrode_position_systems']=ElectrodePositionSystem.objects.all()
        context['electrode_caps']=ElectrodeCap.objects.all()
        context['erp_component_formset']=ERPComponentFormSet(self.request.POST or None, instance=self.object,
            queryset=ERPComponent.objects.filter(erp_sed=self.object).select_related('electrode_cap','electrode_position__position_system'),prefix='erp_component')
        for subform in context['erp_component_formset'].forms:
            if 'electrode_position' in subform.initial and subform.initial['electrode_position'] is not None:
                position=ElectrodePosition.objects.select_related('position_system').get(id=subform.initial['electrode_position'])
                subform.initial['electrode_position_system']=position.position_system.id
        context['figure_formset']=DocumentFigureFormSet(self.request.POST or None, self.request.FILES or None,
            instance=self.object, queryset=DocumentFigure.objects.filter(document=self.object), prefix='figure')
        context['related_brain_region_formset']=RelatedBrainRegionFormSet(self.request.POST or None,
            instance=self.object, queryset=RelatedBrainRegion.objects.filter(document=self.object).select_related('brain_region__nomenclature').prefetch_related('brain_region__nomenclature__species'),
            prefix='related_brain_region')
        context['references'] = self.object.literature.all().prefetch_related('authors__author')
        context['helpPage']='insert_data.html#summary-of-event-related-potential-data'
        context['action']='edit'
        context['ispopup']=('_popup' in self.request.GET)
        context['multiple']=('_multiple' in self.request.GET)
        context['type']=self.request.GET.get('type','')
        return context


class DeleteERPSEDView(PermissionRequiredMixin, DeleteView):
    model=ERPSED
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


class ToggleSelectSEDView(LoginRequiredMixin,JSONResponseMixin,BaseUpdateView):
    model = SED

    def get_context_data(self, **kwargs):
        context={'msg':u'No POST data sent.' }
        if self.request.is_ajax():
            sed=SED.objects.get(id=self.kwargs.get('pk', None))
            active_workspace=get_active_workspace(get_profile(self.request),self.request)

            context={
                'sed_id': sed.id,
                'workspace': active_workspace.title
            }
            activity=WorkspaceActivityItem(workspace=active_workspace, user=self.request.user)
            if 'select' in self.request.POST:
                remove=self.request.POST['select']=='false'
            else:
                remove=sed in active_workspace.related_seds.all()
            if remove:
                active_workspace.related_seds.remove(sed)
                context['selected']=False
                activity.text='%s removed the SED: <a href="%s">%s</a> from the workspace' % (self.request.user.username, sed.get_absolute_url(), sed.__unicode__())
            else:
                active_workspace.related_seds.add(sed)
                context['selected']=True
                activity.text='%s added the SED: <a href="%s">%s</a> to the workspace' % (self.request.user.username, sed.get_absolute_url(), sed.__unicode__())
            activity.save()
            active_workspace.save()
            cache.set('%d.active_workspace' % self.request.user.id, active_workspace)

        return context


class SimilarSEDView(LoginRequiredMixin, JSONResponseMixin, BaseDetailView):

    def get(self, request, *args, **kwargs):
        # Load similar models
        title=self.request.GET['title']
        brief_desc=self.request.GET['brief_description']
        similar_seds=find_similar_seds(self.request.user, title, brief_desc)
        similar_sed_ids=[x.id for (x,matches) in similar_seds]
        similar_sed_titles=[str(x) for (x,matches) in similar_seds]

        data = {'similar_sed_ids': similar_sed_ids,
                'similar_sed_titles': similar_sed_titles}

        return self.render_to_response(data)


class SEDTaggedView(BODBView):
    template_name='bodb/sed/sed_tagged.html'

    def get_context_data(self, **kwargs):
        context=super(SEDTaggedView,self).get_context_data(**kwargs)
        name = self.kwargs.get('name', None)
        # get tagged items

        user=self.request.user
        context['helpPage']='tags.html'
        context['tag']=name
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
        if user.is_authenticated() and not user.is_anonymous():
            context['imaging_seds']=BrainImagingSED.augment_sed_list(context['imaging_seds'],coords,
                context['selected_sed_coords'].values_list('sed_coordinate__id',flat=True))
        else:
            context['imaging_seds']=BrainImagingSED.augment_sed_list(context['imaging_seds'],coords, [])
        context['connectionGraphId']='connectivitySEDDiagram'
        context['erpGraphId']='erpSEDDiagram'
        return context


class SelectSelectedSEDCoordView(LoginRequiredMixin, JSONResponseMixin, BaseCreateView):
    model=SelectedSEDCoord
    def get_context_data(self, **kwargs):
        context={'msg':u'No POST data sent.' }
        if self.request.is_ajax():
            # load selected atlas coordinate
            selectedCoord=get_object_or_404(SelectedSEDCoord, id=self.request.POST['coordId'])
            # add to currently loaded selection
            if 'selectionId' in self.request.POST:
                selectedCoord.saved_selection=SavedSEDCoordSelection.objects.get(id=self.request.POST['selectionId'])
                # select coord
            selectedCoord.selected=True
            # save selected coord
            selectedCoord.save()
            context = {'id':selectedCoord.id, 'selected':True }
        return context


class UnselectSelectedSEDCoordView(LoginRequiredMixin, JSONResponseMixin, BaseCreateView):
    model=SelectedSEDCoord
    def get_context_data(self, **kwargs):
        context={'msg':u'No POST data sent.' }
        if self.request.is_ajax():
            # load selected atlas coord
            selectedCoord=get_object_or_404(SelectedSEDCoord, id=self.request.POST['coordId'])
            # delete selected atlas coord (atlas coord remains intact)
            selectedCoord.delete()
            context = {'id':selectedCoord.id, 'selected':False }
        return context


class SelectSEDCoordView(LoginRequiredMixin, JSONResponseMixin, BaseCreateView):
    model=SelectedSEDCoord
    def get_context_data(self, **kwargs):
        context={'msg':u'No POST data sent.' }
        if self.request.is_ajax():
            profile=get_profile(self.request)
            # created selected SED coord
            selectedCoord=SelectedSEDCoord()
            # load SED coord
            selectedCoord.sed_coordinate=get_object_or_404(SEDCoord, id=self.request.POST['coordId'])
            selectedCoord.selected=True
            selectedCoord.user=self.request.user
            # add to currently loaded selection (if one is currently loaded)
            if profile.loaded_coordinate_selection:
                selectedCoord.saved_selection=profile.loaded_coordinate_selection
                # set shape and color to be same as other selected coords from same SED
            if SelectedSEDCoord.objects.filter(selected=True, sed_coordinate__sed__id=selectedCoord.sed_coordinate.sed.id).exists():
                otherCoord=SelectedSEDCoord.objects.filter(selected=True, sed_coordinate__sed__id=selectedCoord.sed_coordinate.sed.id)[0]
                selectedCoord.twod_shape=otherCoord.twod_shape
                selectedCoord.threed_shape=otherCoord.threed_shape
                selectedCoord.color=otherCoord.color

            # save selected SED coord
            selectedCoord.save()

            context = {'id':self.request.POST['coordId'], 'sed_id': selectedCoord.sed_coordinate.sed.id, 'selected':True }
        return context


class UnselectSEDCoordView(LoginRequiredMixin, JSONResponseMixin, BaseCreateView):
    model=SelectedSEDCoord
    def get_context_data(self, **kwargs):
        context={'msg':u'No POST data sent.' }
        if self.request.is_ajax():
            sed_id=None
            # load selected SED coordinate pointing to atlas coord
            for selectedCoord in SelectedSEDCoord.objects.filter(sed_coordinate__id=self.request.POST['coordId'], selected=True,
                user=self.request.user).select_related('sed_coordinate__sed'):
                sed_id=selectedCoord.sed_coordinate.sed.id
                # delete selected SED coordinate (SED coordinate remains intact)
                selectedCoord.delete()
            context = {'id':self.request.POST['coordId'], 'sed_id': sed_id, 'selected':False }
        return context


class CoordinateSelectionView(LoginRequiredMixin, JSONResponseMixin, BaseCreateView):
    model=SavedSEDCoordSelection
    def get_context_data(self, **kwargs):
        context={'msg':u'No POST data sent.' }
        if self.request.is_ajax():
            profile=get_profile(self.request)
            # load requested coordinate selection
            selection=get_object_or_404(SavedSEDCoordSelection.objects.select_related('user','last_modified_by'), id=self.request.POST['id'])
            profile.loaded_coordinate_selection=selection
            profile.save()
            cache.set('%d.profile' % self.request.user.id, profile)

            # unselect currently selected atlas coords
            SelectedSEDCoord.objects.filter(selected=True, user=self.request.user).exclude(saved_selection__id=self.request.POST['id']).update(selected=False)

            context={
                'id':selection.id,
                'name':selection.name,
                'description':selection.description,
                'collator':selection.get_collator_str(),
                'collator_id':selection.user.id,
                'last_modified_by':selection.get_modified_by_str(),
                'last_modified_by_id':selection.last_modified_by.id,
                }

            selected_coord_objs=SelectedSEDCoord.objects.filter(saved_selection=selection).select_related('sed_coordinate__sed')

            context['selected_coords']=[]
            for coord in selected_coord_objs:
                coord.selected=True
                coord.save()
                coord_array={'sed_name':coord.sed_coordinate.sed.title,
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
                             'extra_data':coord.sed_coordinate.extra_data}
                if coord.sed_coordinate.rcbf is not None:
                    coord_array['rCBF']=coord.sed_coordinate.rcbf.__float__()
                if coord.sed_coordinate.statistic_value is not None:
                    coord_array['statistic_value']=coord.sed_coordinate.statistic_value.__float__()
                context['selected_coords'].append(coord_array)
        return context


class CloseCoordinateSelectionView(LoginRequiredMixin, JSONResponseMixin, BaseCreateView):
    model=SavedSEDCoordSelection
    def get_context_data(self, **kwargs):
        context={'msg':u'No POST data sent.' }
        if self.request.is_ajax():
            profile=get_profile(self.request)

            # unload all other selections
            # unload other coordinate selections
            if profile.loaded_coordinate_selection:
                profile.loaded_coordinate_selection=None
                profile.save()
                cache.set('%d.profile' % self.request.user.id, profile)
                # unselect all coordinates belonging to loaded selection
            if 'id' in self.request.POST and len(self.request.POST['id']):
                SelectedSEDCoord.objects.filter(selected=True, saved_selection__id=self.request.POST['id'],
                    user=self.request.user).update(selected=False)
            context={}
        return context


class DeleteCoordinateSelectionView(LoginRequiredMixin, JSONResponseMixin, BaseCreateView):
    model=SavedSEDCoordSelection
    def get_context_data(self, **kwargs):
        context={'msg':u'No POST data sent.' }
        if self.request.is_ajax():
            profile=get_profile(self.request)
            # delete coordinates in selection
            SelectedSEDCoord.objects.filter(saved_selection__id=self.request.POST['id']).delete()
            # load selection
            coordSelection=get_object_or_404(SavedSEDCoordSelection, id=self.request.POST['id'])
            if profile.loaded_coordinate_selection==coordSelection:
                profile.loaded_coordinate_selection=None
                profile.save()
                cache.set('%d.profile' % self.request.user.id, profile)
                # delete selection
            coordSelection.delete()
            context = {'id': self.request.POST['id']}
        return context


class SaveCoordinateSelectionView(LoginRequiredMixin, JSONResponseMixin, BaseUpdateView):
    model=SavedSEDCoordSelection
    def get_context_data(self, **kwargs):
        context={'msg':u'No POST data sent.' }
        if self.request.is_ajax():
            profile=get_profile(self.request)
            # create new coordinate selection
            coordSelection=SavedSEDCoordSelection()
            action='add'

            # editing existing coordinate selection
            if 'id' in self.request.POST and len(self.request.POST['id'])>0:
                # load coordinate selection
                coordSelection=get_object_or_404(SavedSEDCoordSelection, id=self.request.POST['id'])
                action='edit'
            else:
                coordSelection.user=self.request.user
                # unload other loaded coordinate selections
                if profile.loaded_coordinate_selection:
                    profile.loaded_coordinate_selection=None
                    profile.save()
                    cache.set('%d.profile' % self.request.user.id, profile)
            coordSelection.last_modified_by=self.request.user

            # set selection info
            coordSelection.name=self.request.POST['name']
            coordSelection.description=self.request.POST['description']

            # save selection
            coordSelection.save()
            profile.loaded_coordinate_selection=coordSelection
            profile.save()
            cache.set('%d.profile' % self.request.user.id, profile)

            # load selected coordinates
            selected_coords=SelectedSEDCoord.objects.filter(selected=True, user=self.request.user).select_related('saved_selection')

            # process each coordinate
            for coord in selected_coords:
                # add to current selecction
                if not coord.saved_selection:
                    coord.saved_selection=coordSelection
                # add new selected coordinate for new selection
                elif not(coord.saved_selection.id==coordSelection.id):
                    coord.selected=False
                    clone=coord.copy()
                    clone.saved_selection=coordSelection
                    clone.user=self.request.user
                    clone.selected=True
                    clone.save()
                    # save coordinate
                coord.save()

            # return selection id and whether added or edited
            context = {
                'id': coordSelection.id,
                'name': coordSelection.name,
                'collator': coordSelection.get_collator_str(),
                'collator_id': coordSelection.user.id,
                'description': coordSelection.description,
                'action': action
            }
        return context


class ElectrodePositionsView(JSONResponseMixin, BaseUpdateView):
    model=ElectrodePositionSystem
    def get_context_data(self, **kwargs):
        context={'msg':u'No POST data sent.' }
        if self.request.is_ajax():
            positions=ElectrodePosition.objects.filter(position_system__id=self.kwargs.get('pk'))
            position_ids=[position.id for position in positions]
            position_names=[position.name for position in positions]
            context={
                'form_id': self.request.GET.get('form_id'),
                'new_val': self.request.GET.get('new_val'),
                'position_ids': position_ids,
                'position_names': position_names
            }
        return context


