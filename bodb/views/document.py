import Image
import fileinput
import os
from django.contrib.auth.models import Group
from django.shortcuts import redirect
from django.views.generic import DetailView
from django.views.generic.edit import BaseCreateView
import sys
import time
from bodb.models import DocumentFigure, RelatedBOP, RelatedModel, RelatedBrainRegion, Post, BuildSED, Document, DocumentPublicRequest, Model, BOP, SED, SSR, SelectedSEDCoord
from guardian.shortcuts import assign_perm, remove_perm, get_perms
from registration.models import User
from uscbp import settings
from uscbp.views import JSONResponseMixin

from bodb.serializers import DocumentSerializer
from bodb.permissions import IsEditorOrReadOnly
from django.http import Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import mixins
from rest_framework import generics
from rest_framework import permissions

from rest_framework.renderers import JSONRenderer, XMLRenderer
from bodb.renderers import BODBBrowsableAPIRenderer

class DocumentAPIListView(generics.ListCreateAPIView):
    renderer_classes = (BODBBrowsableAPIRenderer, JSONRenderer, XMLRenderer,)
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    permission_classes = (IsEditorOrReadOnly,)
    model = Document

    def get_queryset(self):
        user = self.request.user
        security_q=Document.get_security_q(user)
        return Document.objects.filter(security_q)

class DocumentDetailView(DetailView):

    def get_context_data(self, **kwargs):
        context = super(DocumentDetailView, self).get_context_data(**kwargs)
        user=self.request.user
        context['helpPage']='index.html'
        context['figures'] = DocumentFigure.objects.filter(document=self.object)
        context['generic_build_seds'] = BuildSED.get_building_sed_list(BuildSED.get_generic_building_seds(self.object, user),user)
        context['connectivity_build_seds'] = BuildSED.get_building_sed_list(BuildSED.get_connectivity_building_seds(self.object, user),user)
        context['imaging_build_seds'] = BuildSED.get_building_sed_list(BuildSED.get_imaging_building_seds(self.object, user),user)
        context['erp_build_seds'] = BuildSED.get_building_sed_list(BuildSED.get_erp_building_seds(self.object, user),user)
        context['related_bops'] = RelatedBOP.get_related_bop_list(RelatedBOP.get_related_bops(self.object, user),user)
        context['related_models'] = RelatedModel.get_related_model_list(RelatedModel.get_related_models(self.object, user),user)
        context['related_brain_regions'] = RelatedBrainRegion.get_related_brain_region_list(RelatedBrainRegion.objects.filter(document=self.object), user)
        context['canEdit']=self.object.check_perm(user,'edit')
        context['canDelete']=self.object.check_perm(user,'delete')
        context['canManage']=self.object.check_perm(user,'manage')
        context['ispopup']=('_popup' in self.request.GET)
        context['posts']=list(Post.objects.filter(forum=self.object.forum,parent=None).order_by('-posted'))
        context['is_favorite']=False
        context['selected']=False
        context['can_add_post']=False
        context['public_request_sent']=False
        context['can_add_entry']=False
        context['can_remove_entry']=False
        context['selected_coord_ids']=[]
        if user.is_authenticated() and not user.is_anonymous():
            active_workspace=user.get_profile().active_workspace
            context['is_favorite']=user.get_profile().favorites.filter(id=self.object.id).count()>0
            context['selected']=active_workspace.related_bops.filter(id=self.object.id).count()>0
            context['can_add_post']=True
            context['can_add_entry']=user.has_perm('add_entry',active_workspace)
            context['can_remove_entry']=user.has_perm('remove_entry',active_workspace)
            context['public_request_sent']=DocumentPublicRequest.objects.filter(user=user,document=self.object).count()>0
            selected_coords=SelectedSEDCoord.objects.filter(selected=True, user__id=user.id)
            for coord in selected_coords:
                context['selected_coord_ids'].append(coord.sed_coordinate.id)
        return context
    
class DocumentAPIDetailView(generics.RetrieveUpdateDestroyAPIView):
    
    renderer_classes = (BODBBrowsableAPIRenderer, JSONRenderer, XMLRenderer)
    
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
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
            if Model.objects.filter(id=self.request.POST['documentId']).count():
                type='Model'
            elif BOP.objects.filter(id=self.request.POST['documentId']).count():
                type='BOP'
            elif SED.objects.filter(id=self.request.POST['documentId']).count():
                type='SED'
            elif SSR.objects.filter(id=self.request.POST['documentId']).count():
                type='SSR'
            public_request=DocumentPublicRequest(user=self.request.user, document=document, type=type)
            public_request.save()
        return context


def generate_diagram_from_gxl(graphTool, dotXML, user, ext=''):
    prefix='%s.%s' % (user.username,time.strftime("%Y.%m.%d.%H:%M:%S"))
    xml_path = os.path.join(settings.MEDIA_ROOT, 'export', '%s.%s.xml' % (prefix,ext))
    dot_path = os.path.join(settings.MEDIA_ROOT, 'export', '%s.%s.dot' % (prefix,ext))
    FILE = open(xml_path, 'w')
    FILE.write(unicode(dotXML.encode('latin1','ignore')))
    FILE.close()
    os.system('gxl2dot -o %s %s' % (dot_path, xml_path))
    for line in fileinput.input(dot_path, inplace=1):
        if '_gxl_type' in line:
            line = line.replace('_gxl_type', 'URL')
        if 'name' in line:
            line = line.replace('name','label')
        sys.stdout.write(line)
    map_path = os.path.join(settings.MEDIA_ROOT, 'export', '%s.%s.map' % (prefix,ext))
    diagram = os.path.join('export', '%s.%s.png' % (prefix,ext))
    png_path = os.path.join(settings.MEDIA_ROOT, diagram)
    os.system('%s -Tcmapx -o%s -Tpng -o%s %s' % (graphTool, map_path, png_path, dot_path))
    FILE = open(map_path, 'r')
    map = FILE.read()
    map_lines=map.split('\n')
    map='\n'.join(map_lines[1:-2])
    FILE.close()
    im=Image.open(png_path)
    return diagram, im.size, map