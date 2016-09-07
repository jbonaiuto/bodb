from datetime import datetime
from django.contrib.auth.models import Group
from django.shortcuts import redirect
from django.views.generic import DetailView
from django.views.generic.edit import BaseCreateView
from bodb.models import DocumentFigure, RelatedBOP, RelatedModel, RelatedBrainRegion, BuildSED, Document, DocumentPublicRequest, Model, BOP, SED, SSR, RecentlyViewedEntry, Module, Prediction, ConnectivitySED
from bodb.views.main import set_context_workspace
from guardian.shortcuts import assign_perm, remove_perm, get_perms
from registration.models import User
from uscbp.views import JSONResponseMixin

from bodb.permissions import IsEditorOrReadOnly
from rest_framework import generics

class DocumentAPIListView(generics.ListCreateAPIView):
    queryset = Document.objects.all()
    permission_classes = (IsEditorOrReadOnly,)
    model = Document

    def get_queryset(self):
        user = self.request.user
        security_q=Document.get_security_q(user)
        return Document.objects.filter(security_q)

class DocumentDetailView(DetailView):

    model=Document

    def get(self, request, *args, **kwargs):
        id=self.kwargs.get('pk', None)
        if BOP.objects.filter(id=id).exists():
            return redirect('/bodb/bop/%s/' % id)
        elif Model.objects.filter(id=id).exists():
            return redirect('/bodb/model/%s/' % id)
        elif Module.objects.filter(id=id).exists():
            return redirect('/bodb/module/%s/' % id)
        elif Prediction.objects.filter(id=id).exists():
            return redirect('/bodb/prediction/%s/' % id)
        elif SED.objects.filter(id=id).exists():
            return redirect('/bodb/sed/%s/' % id)
        elif SSR.objects.filter(id=id).exists():
            return redirect('/bodb/ssr/%s/' % id)

    def get_context_data(self, **kwargs):
        context = super(DocumentDetailView, self).get_context_data(**kwargs)
        context=set_context_workspace(context, self.request)
        user=self.request.user
        context['helpPage']='index.html'
        context['figures'] = DocumentFigure.objects.filter(document=self.object).order_by('order')
        context['generic_build_seds']=[]
        context['connectivity_build_seds']=[]
        context['imaging_build_seds']=[]
        context['erp_build_seds']=[]
        context['connectivity_build_sed_seds']=[]
        if BuildSED.get_building_seds(self.object,user).exists():
            generic_build_seds=BuildSED.get_generic_building_seds(self.object, user)
            context['generic_build_seds'] = BuildSED.get_building_sed_list(generic_build_seds,
                context['workspace_seds'], context['fav_docs'], context['subscriptions'])

            conn_build_seds=BuildSED.get_connectivity_building_seds(self.object, user)
            for build_sed in conn_build_seds:
                conn_sed=ConnectivitySED.objects.get(id=build_sed.sed.id)
                build_sed.sed=conn_sed
                if not conn_sed in context['connectivity_build_sed_seds']:
                    context['connectivity_build_sed_seds'].append(conn_sed)
            context['connectivity_build_sed_regions']=ConnectivitySED.get_region_map(context['connectivity_build_sed_seds'])
            context['connectivity_build_seds'] = BuildSED.get_building_sed_list(conn_build_seds,
                context['workspace_seds'], context['fav_docs'], context['subscriptions'])

            imaging_build_seds=BuildSED.get_imaging_building_seds(self.object, user)
            context['imaging_build_seds'] = BuildSED.get_imaging_building_sed_list(imaging_build_seds,
                context['workspace_seds'], context['fav_docs'], context['subscriptions'])
            erp_build_seds=BuildSED.get_erp_building_seds(self.object, user)
            context['erp_build_seds'] = BuildSED.get_building_sed_list(erp_build_seds, context['workspace_seds'],
                context['fav_docs'], context['subscriptions'])

        rbops=RelatedBOP.get_related_bops(self.object, user)
        context['related_bops'] = RelatedBOP.get_related_bop_list(rbops, context['workspace_bops'], context['fav_docs'],
            context['subscriptions'])
        rmods=RelatedModel.get_related_models(self.object, user)
        context['related_models'] = RelatedModel.get_related_model_list(rmods, context['workspace_models'],
            context['fav_docs'], context['subscriptions'])
        related_regions=list(RelatedBrainRegion.objects.filter(document=self.object).select_related('brain_region__nomenclature').prefetch_related('brain_region__nomenclature__species'))
        related_regions.sort(key=RelatedBrainRegion.brain_region_name)
        context['related_brain_regions'] = RelatedBrainRegion.get_related_brain_region_list(related_regions,
            context['workspace_regions'], context['fav_regions'])
        context['canEdit']=self.object.check_perm(user,'edit')
        context['canDelete']=self.object.check_perm(user,'delete')
        context['canManage']=self.object.check_perm(user,'manage')
        context['ispopup']=('_popup' in self.request.GET)
        context['is_favorite']=self.object.id in context['fav_docs']

        context['can_add_post']=False
        context['public_request_sent']=False
        if user.is_authenticated() and not user.is_anonymous():
            context['can_add_post']=True
            context['public_request_sent']=DocumentPublicRequest.objects.filter(user=user,document=self.object).exists()

            # If the user has viewed this entry recently, update the view time
            if RecentlyViewedEntry.objects.filter(user=self.request.user, document=self.object).exists():
                view=RecentlyViewedEntry.objects.get(user=self.request.user, document=self.object)
                view.date_viewed=datetime.now()
                view.save()
            # Save recently viewed entry for the current user
            else:
                view=RecentlyViewedEntry(user=self.request.user, document=self.object)
                view.save()
            # Remove all but 10 most recently viewed entries
            if RecentlyViewedEntry.objects.filter(user=self.request.user).count()>10:
                views = RecentlyViewedEntry.objects.filter(user=self.request.user).order_by('date_viewed').reverse()[:10].values_list("id", flat=True)  # only retrieve ids.
                RecentlyViewedEntry.objects.exclude(pk__in=list(views)).delete()

        return context
    
class DocumentAPIDetailView(generics.RetrieveUpdateDestroyAPIView):
    
    queryset = Document.objects.all()
    permission_classes = (IsEditorOrReadOnly,)
 

class ManageDocumentPermissionsView(DetailView):
    template_name = 'bodb/document_permissions_detail.html'

    def post(self, request, *args, **kwargs):
        self.object=Document.objects.get(id=self.kwargs.get('pk',None))
        context = self.get_context_data(**kwargs)
        for user in context['users']:
            if context['user_manage_permissions'][user]:
                assign_perm('manage', user, self.object)
            else:
                remove_perm('manage', user, self.object)
            if context['user_edit_permissions'][user]:
                assign_perm('edit', user, self.object)
            else:
                remove_perm('edit', user, self.object)
            if context['user_delete_permissions'][user]:
                assign_perm('delete', user, self.object)
            else:
                remove_perm('delete', user, self.object)
        for group in context['groups']:
            if context['group_manage_permissions'][group]:
                assign_perm('manage', group, self.object)
            else:
                remove_perm('manage', group, self.object)
            if context['group_edit_permissions'][group]:
                assign_perm('edit', group, self.object)
            else:
                remove_perm('edit', group, self.object)
            if context['group_delete_permissions'][group]:
                assign_perm('delete', group, self.object)
            else:
                remove_perm('delete', group, self.object)

        redirect_url='/bodb/document/%d/permissions/' % self.object.id
        if context['ispopup']:
            redirect_url+='?_popup=1'
        return redirect(redirect_url)

    def get(self, request, *args, **kwargs):
        self.object=Document.objects.get(id=self.kwargs.get('pk',None))
        return self.render_to_response(self.get_context_data())

    def get_context_data(self, **kwargs):
        context=super(DetailView,self).get_context_data(**kwargs)
        context=set_context_workspace(context, self.request)
        context['document']=self.object
        context['helpPage']='permissions.html#individual-entry-permissions'
        context['users']=User.objects.all().exclude(id=self.request.user.id)
        context['groups']=Group.objects.filter(user__id=self.request.user.id)
        context['ispopup']=('_popup' in self.request.GET)
        context['user_manage_permissions']={}
        context['user_edit_permissions']={}
        context['user_delete_permissions']={}
        context['group_manage_permissions']={}
        context['group_edit_permissions']={}
        context['group_delete_permissions']={}
        for user in context['users']:
            context['user_manage_permissions'][user]=False
            context['user_edit_permissions'][user]=False
            context['user_delete_permissions'][user]=False
            if self.request.POST:
                context['user_manage_permissions'][user]=('user-%d_manage' % user.id) in self.request.POST
                context['user_edit_permissions'][user]=('user-%d_edit' % user.id) in self.request.POST
                context['user_delete_permissions'][user]=('user-%d_delete' % user.id) in self.request.POST
            else:
                context['user_manage_permissions'][user]=user.has_perm('manage',self.object)
                context['user_edit_permissions'][user]=user.has_perm('edit',self.object)
                context['user_delete_permissions'][user]=user.has_perm('delete',self.object)
        for group in context['groups']:
            context['group_manage_permissions'][group]=False
            context['group_edit_permissions'][group]=False
            context['group_delete_permissions'][group]=False
            if self.request.POST:
                context['group_manage_permissions'][group]=('group-%d_manage' % group.id) in self.request.POST
                context['group_edit_permissions'][group]=('group-%d_edit' % group.id) in self.request.POST
                context['group_delete_permissions'][group]=('group-%d_delete' % group.id) in self.request.POST
            else:
                context['group_manage_permissions'][group]='manage' in get_perms(group,self.object)
                context['group_edit_permissions'][group]='edit' in get_perms(group,self.object)
                context['group_delete_permissions'][group]='delete' in get_perms(group,self.object)
        return context


class DocumentPublicRequestView(JSONResponseMixin,BaseCreateView):
    model = Document

    def get_context_data(self, **kwargs):
        context={'msg':u'No POST data sent.' }
        if self.request.is_ajax() and 'documentId' in self.request.POST:
            document = Document.objects.get(id=self.request.POST['documentId'])
            type=''
            if Model.objects.filter(id=self.request.POST['documentId']).exists():
                type='Model'
            elif BOP.objects.filter(id=self.request.POST['documentId']).exists():
                type='BOP'
            elif SED.objects.filter(id=self.request.POST['documentId']).exists():
                type='SED'
            elif SSR.objects.filter(id=self.request.POST['documentId']).exists():
                type='SSR'
            public_request=DocumentPublicRequest(user=self.request.user, document=document, type=type)
            public_request.save()
        return context
