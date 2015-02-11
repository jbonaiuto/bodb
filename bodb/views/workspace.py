from django.contrib.auth import login
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.shortcuts import redirect, get_object_or_404
from django.views.generic import ListView, View, TemplateView, UpdateView, DetailView
from django.views.generic.detail import SingleObjectTemplateResponseMixin
from django.views.generic.edit import BaseUpdateView, FormView, CreateView, BaseCreateView, DeleteView, ProcessFormView
from bodb.forms.workspace import WorkspaceInvitationForm, WorkspaceForm, WorkspaceUserForm, WorkspaceBookmarkForm
from bodb.models import Workspace, UserSubscription, WorkspaceInvitation, BrainImagingSED, ConnectivitySED, ERPSED, WorkspaceActivityItem, SelectedSEDCoord, SavedSEDCoordSelection, Model, BOP, SED, SEDCoord, SSR, Document, WorkspaceBookmark, ERPComponent, Literature, BrainRegion
from bodb.models.discussion import Post
from bodb.signals import coord_selection_created
from bodb.views.main import BODBView, set_context_workspace
from bodb.views.security import ObjectRolePermissionRequiredMixin
from bodb.views.sed import SaveCoordinateSelectionView
from guardian.mixins import LoginRequiredMixin
from guardian.models import User
from guardian.shortcuts import assign_perm, remove_perm
from uscbp.views import JSONResponseMixin
from django.core.cache import cache

workspace_permissions=['add_post','add_entry','remove_entry',
                       'add_coordinate_selection','change_coordinate_selection','delete_coordinate_selection',
                       'add_bookmark','delete_bookmark']

class ActivateWorkspaceView(ObjectRolePermissionRequiredMixin, JSONResponseMixin,BaseUpdateView):
    model = Workspace
    permission_required = 'member'

    def get_context_data(self, **kwargs):
        context={'msg':u'No POST data sent.' }
        if self.request.is_ajax():
            workspace=Workspace.objects.get(id=self.kwargs.get('pk',None))
            profile=self.request.user.get_profile()
            profile.active_workspace=workspace
            profile.save()

            context={
                'id': workspace.id,
                'title': workspace.title
            }
        return context


class WorkspaceUserToggleAdminView(ObjectRolePermissionRequiredMixin, JSONResponseMixin,BaseUpdateView):
    model = Workspace
    permission_required = 'admin'

    def get_context_data(self, **kwargs):
        context={'msg':u'No POST data sent.' }
        if self.request.is_ajax():
            workspace=Workspace.objects.get(id=self.kwargs.get('pk',None))
            user=User.objects.get(id=self.request.POST['user_id'])
            if self.request.POST['admin']=='true':
                if not user in workspace.admin_users.all():
                    workspace.admin_users.add(user)
            else:
                if user in workspace.admin_users.all():
                    workspace.admin_users.remove(user)
            context={
                'user_id': user.id,
                'admin': self.request.POST['admin']=='true'
            }
        return context


class WorkspaceUserRemoveView(ObjectRolePermissionRequiredMixin, JSONResponseMixin,BaseUpdateView):
    model = Workspace
    permission_required = 'admin'

    def get_context_data(self, **kwargs):
        context={'msg':u'No POST data sent.' }
        if self.request.is_ajax():
            workspace=Workspace.objects.get(id=self.kwargs.get('pk',None))
            user=User.objects.get(id=self.request.POST['user_id'])
            if user in workspace.admin_users.all():
                workspace.admin_users.remove(user)
            user.groups.remove(workspace.group)
            user.save()
            context={'user_id': user.id}
        return context


class WorkspaceTitleAvailableView(LoginRequiredMixin, JSONResponseMixin,BaseCreateView):
    model = Workspace

    def get_context_data(self, **kwargs):
        context={'msg':u'No POST data sent.' }
        if self.request.is_ajax():
            title_str = self.request.POST['title']
            # return a response if it is unique
            if not Workspace.objects.filter(title=title_str).count():
                context['available']=1
            # return an error if not
            else:
                context['available']=0
        return context


class ActiveWorkspaceDetailView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        profile=self.request.user.get_profile()
        url=profile.active_workspace.get_absolute_url()
        if 'show_tour' in self.request.GET:
            url+='?show_tour='+self.request.GET['show_tour']
        return redirect(url)


class WorkspaceInvitationResponseView(LoginRequiredMixin, TemplateView):
    def get_context_data(self, **kwargs):
        context=super(WorkspaceInvitationResponseView,self).get_context_data(**kwargs)
        context['invitation']=get_object_or_404(WorkspaceInvitation,activation_key=context['activation_key'])
        return context

    def get(self, request, *args, **kwargs):
        context=self.get_context_data(**kwargs)
        context['invitation'].invited_user.backend = 'django.contrib.auth.backends.ModelBackend'
        login(self.request,context['invitation'].invited_user)
        if context['action']=='decline':
            context['invitation'].status='declined'
            self.template_name='bodb/workspace/workspace_invitation_decline.html'
        elif context['action']=='accept':
            context['invitation'].status='accepted'
            user=User.objects.get(id=context['invitation'].invited_user.id)
            # Add workspace group to user's groups
            user.groups.add(context['invitation'].workspace.group)
            user.save()
            # Create workspace activity item
            activity=WorkspaceActivityItem(workspace=context['invitation'].workspace, user=user)
            activity.text='%s joined the workspace' % user.username
            activity.save()
            self.template_name='bodb/workspace/workspace_invitation_accept.html'
            visibility_q=Q(created_by__is_active=True)
            if not self.self.request.user.is_superuser:
                visibility_q=Q(visibility_q & Q(group__in=self.request.user.groups.all()))
            workspaces=Workspace.objects.filter(visibility_q).order_by('title')
            cache.set('%d.workspaces' % self.request.user.id, list(workspaces))

        context['invitation'].save()
        return self.render_to_response(context)


class EditWorkspaceMixin():
    model=Workspace
    form_class = WorkspaceForm
    template_name = 'bodb/workspace/workspace_detail.html'


class CreateWorkspaceView(LoginRequiredMixin, EditWorkspaceMixin, CreateView):

    def get_context_data(self, **kwargs):
        context=super(CreateWorkspaceView,self).get_context_data(**kwargs)
        context['helpPage']='workspaces.html#new-workspace'
        return context

    def form_valid(self, form):
        self.object=form.save(commit=False)
        self.object.created_by=self.request.user
        self.object.save()
        form.save_m2m()
        # add created by user to admins
        self.object.admin_users.add(self.request.user)
        self.object.save()
        for perm in workspace_permissions:
            assign_perm('bodb.%s'%perm,self.request.user,self.object)

        self.request.user.get_profile().active_workspace=self.object
        self.request.user.get_profile().save()

        visibility_q=Q(created_by__is_active=True)
        if not self.self.request.user.is_superuser:
            visibility_q=Q(visibility_q & Q(group__in=self.request.user.groups.all()))
        workspaces=Workspace.objects.filter(visibility_q).order_by('title')
        cache.set('%d.workspaces' % self.request.user.id, list(workspaces))

        return redirect(self.get_success_url())


class UpdateWorkspaceView(ObjectRolePermissionRequiredMixin, EditWorkspaceMixin, UpdateView):
    help_page='BODB-Edit-Workspace'
    permission_required = 'admin'

    def get_context_data(self, **kwargs):
        context=super(UpdateWorkspaceView,self).get_context_data(**kwargs)
        context['helpPage']=self.help_page
        return context

    def form_valid(self, form):
        self.object=form.save()
        return redirect(self.get_success_url())


class WorkspaceInvitationView(LoginRequiredMixin, JSONResponseMixin, BaseUpdateView):
    model=WorkspaceInvitation
    def get_context_data(self, **kwargs):
        context={'msg':u'No POST data sent.' }
        if self.request.is_ajax():
            workspace=Workspace.objects.get(id=kwargs.get('pk',None))
            form=WorkspaceInvitationForm(self.request.POST)
            context={}
            if form.is_valid():
                context['invitations']=[]
                for user in form.cleaned_data['invited_users']:
                    invite=WorkspaceInvitation(workspace=workspace, invited_user=user, invited_by=self.request.user,
                        invitation_body=form.cleaned_data['invitation_body'])
                    invite.save()
                    context['invitations'].append({
                        'user': invite.invited_user.username,
                        'body': invite.invitation_body,
                        'status': invite.status,
                        'id': invite.id,
                        'sent': invite.sent.strftime("%b %d, %Y, %I:%M %p")
                    })
            else:
                print(form.errors)
        return context


class WorkspaceInvitationResendView(LoginRequiredMixin, JSONResponseMixin, BaseUpdateView):
    model=WorkspaceInvitation
    def get_context_data(self, **kwargs):
        context={'msg':u'No POST data sent.' }
        if self.request.is_ajax():
            invitation=WorkspaceInvitation.objects.get(id=kwargs.get('pk',None))
            invitation.send()
            context={'id':invitation.id, 'username': invitation.invited_user.username, 'sent': invitation.sent.strftime("%b %d, %Y, %I:%M %p")}
        return context


class WorkspaceDetailView(ObjectRolePermissionRequiredMixin, FormView):
    template_name = 'bodb/workspace/workspace_view.html'
    form_class=WorkspaceInvitationForm
    permission_required = 'member'

    def get_object(self):
        return get_object_or_404(Workspace, id=self.kwargs.get('pk', None))

    def get(self, request, *args, **kwargs):
        self.object=self.get_object()
        return super(WorkspaceDetailView,self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context=super(WorkspaceDetailView,self).get_context_data(**kwargs)
        user=self.request.user
        context['helpPage']='workspaces.html#workspace-tabs'
        context['workspace']=self.object
        context['showTour']='show_tour' in self.request.GET

        context['connectionGraphId']='connectivitySEDDiagram'
        context['erpGraphId']='erpSEDDiagram'
        context['bopGraphId']='bopRelationshipDiagram'
        context['modelGraphId']='modelRelationshipDiagram'

        context['form']=WorkspaceInvitationForm()
        invited_user_ids=[]
        for invite in WorkspaceInvitation.objects.filter(workspace=self.object).exclude(status='declined').select_related('invited_user'):
            invited_user_ids.append(invite.invited_user.id)
        context['form'].fields['invited_users'].queryset=User.objects.all().exclude(id=user.id).exclude(id__in=invited_user_ids)

        context['selected']=self.request.GET.get('selected','activity')
        context['admin']=(user in self.object.admin_users.all()) or user.is_superuser
        context['can_delete_coord_selection']=user.has_perm('delete_coordinate_selection',self.object)
        context['can_add_coord_selection']=user.has_perm('add_coordinate_selection',self.object)
        context['can_change_coord_selection']=user.has_perm('change_coordinate_selection',self.object)
        context['can_add_post']=user.has_perm('add_post',self.object)
        context['can_add_entry']=user.has_perm('add_entry',self.object)
        context['can_remove_entry']=user.has_perm('remove_entry',self.object)
        context['can_add_bookmark']=user.has_perm('add_bookmark',self.object)
        context['can_change_bookmark']=user.has_perm('change_bookmark',self.object)
        context['can_delete_bookmark']=user.has_perm('delete_bookmark',self.object)
        members=[]
        for usr in self.object.group.user_set.all():
            subscribed_to=False
            is_admin=False
            if user.is_authenticated() and not user.is_anonymous():
                subscribed_to=UserSubscription.objects.filter(subscribed_to_user=usr, user=user).exists()
                is_admin=usr in self.object.admin_users.all()
            members.append([usr,is_admin,subscribed_to])
        context['members']=members
        if context['admin']:
            context['invitations']=WorkspaceInvitation.objects.filter(workspace=self.object).select_related('invited_user','invited_by')
        context['posts']=list(Post.objects.filter(forum=self.object.forum,parent=None).order_by('-posted'))
        context['bookmarks']=WorkspaceBookmark.objects.filter(workspace=self.object)

        # Visibility query filter
        visibility = Document.get_security_q(user)

        literature=self.object.related_literature.distinct().prefetch_related('collator','authors__author')
        context['literatures']=Literature.get_reference_list(literature,user)

        brain_regions=self.object.related_regions.distinct().prefetch_related('nomenclature__species')
        context['brain_regions']=BrainRegion.get_region_list(brain_regions,user)

        models=self.object.related_models.filter(visibility).distinct().prefetch_related('collator','authors__author')
        context['models']=Model.get_model_list(models,user)
        context['model_seds']=Model.get_sed_map(models, user)

        bops=self.object.related_bops.filter(visibility).distinct().prefetch_related('collator')
        context['bops']=BOP.get_bop_list(bops,user)
        context['bop_relationships']=BOP.get_bop_relationships(bops, user)

        generic_seds=self.object.related_seds.filter(Q(type='generic') & visibility).distinct().prefetch_related('collator')
        context['generic_seds']=SED.get_sed_list(generic_seds, user)

        ws_imaging_seds=BrainImagingSED.objects.filter(sed_ptr__in=self.object.related_seds.filter(visibility)).distinct().prefetch_related('collator')
        coords=[SEDCoord.objects.filter(sed=sed).select_related('coord__threedcoord') for sed in ws_imaging_seds]
        context['imaging_seds']=SED.get_sed_list(ws_imaging_seds,user)
        context['imaging_seds']=BrainImagingSED.augment_sed_list(context['imaging_seds'],coords, user)

        conn_seds=ConnectivitySED.objects.filter(sed_ptr__in=self.object.related_seds.filter(visibility)).distinct().prefetch_related('collator','target_region__nomenclature','source_region__nomenclature')
        context['connectivity_seds']=SED.get_sed_list(conn_seds, user)
        context['connectivity_sed_regions']=ConnectivitySED.get_region_map(conn_seds)

        ws_erp_seds=ERPSED.objects.filter(sed_ptr__in=self.object.related_seds.filter(visibility)).distinct().prefetch_related('collator')
        components=[ERPComponent.objects.filter(erp_sed=erp_sed).prefetch_related('electrode_position__position_system') for erp_sed in ws_erp_seds]
        context['erp_seds']=SED.get_sed_list(ws_erp_seds, user)
        context['erp_seds']=ERPSED.augment_sed_list(context['erp_seds'],components)

        sss=self.object.related_ssrs.filter(visibility).distinct().prefetch_related('collator')
        context['ssrs']=SSR.get_ssr_list(sss, user)

        context['activity_stream']=WorkspaceActivityItem.objects.filter(workspace=self.object).order_by('-time').select_related('user')

        # loaded coordinate selection
        context['loaded_coord_selection']=None
        if user.is_authenticated() and not user.is_anonymous():
            if user.get_profile().loaded_coordinate_selection and \
               user.get_profile().loaded_coordinate_selection in self.object.saved_coordinate_selections.all():
                context['loaded_coord_selection']=user.get_profile().loaded_coordinate_selection
                SelectedSEDCoord.objects.filter(saved_selection__id=context['loaded_coord_selection'].id).update(selected=True)
        # load saved selections
        context['saved_coord_selections']=self.object.saved_coordinate_selections.all()

        # load selected coordinates
        selected_coord_objs=SelectedSEDCoord.objects.filter(selected=True, user__id=user.id).prefetch_related('sed_coordinate__sed','sed_coordinate__coord')

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

        context=set_context_workspace(context, self.request.user)

        return context


class DeleteWorkspaceView(ObjectRolePermissionRequiredMixin, DeleteView):
    model=Workspace
    success_url = '/bodb/workspaces/'
    permission_required = 'admin'


class SaveWorkspaceCoordinateSelectionView(ObjectRolePermissionRequiredMixin, SaveCoordinateSelectionView):
    model=SavedSEDCoordSelection

    def get_required_permissions(self, request=None):
        context=self.get_context_data()
        if context['action']=='add':
            return ['bodb.add_coordinate_selection']
        return ['bodb.change_coordinate_selection']

    def get_context_data(self, **kwargs):
        context={'msg':u'No POST data sent.' }
        if self.request.is_ajax():
            context=super(SaveWorkspaceCoordinateSelectionView,self).get_context_data(**kwargs)
            if context['action']=='add':
                coord_selection=SavedSEDCoordSelection.objects.get(id=context['id'])
                active_workspace=self.request.user.get_profile().active_workspace
                active_workspace.saved_coordinate_selections.add(coord_selection)
                active_workspace.save()
                coord_selection_created.send(sender=coord_selection)
        return context


class DeleteWorkspaceCoordinateSelectionView(ObjectRolePermissionRequiredMixin, JSONResponseMixin, BaseCreateView):
    model=SavedSEDCoordSelection
    permission_required = 'delete_coordinate_selection'

    def get_context_data(self, **kwargs):
        # load selection
        coordSelection=get_object_or_404(SavedSEDCoordSelection, id=self.request.POST['id'])
        active_workspace=self.request.user.get_profile().active_workspace
        if coordSelection in active_workspace.saved_coordinate_selections.all():
            active_workspace.saved_coordinate_selections.remove(coordSelection)
            active_workspace.save()
        return super(DeleteWorkspaceCoordinateSelectionView,self).get_context_data(**kwargs)


class WorkspaceUserDetailView(ObjectRolePermissionRequiredMixin, DetailView):
    model = User
    template_name = 'bodb/workspace/user_view.html'
    permission_required = 'admin'

    def get_context_data(self, **kwargs):
        context = super(WorkspaceUserDetailView,self).get_context_data(**kwargs)
        context['workspace']=Workspace.objects.get(id=self.kwargs['id'])
        context['helpPage']='BODB-View-Workspace-User'
        context['ispopup']=('_popup' in self.request.GET)
        context['action']=self.request.GET.get('action',None)
        for permission in workspace_permissions:
            context[permission]=self.object.has_perm('%s' % permission,context['workspace'])
        return context


class UpdateWorkspaceUserView(ObjectRolePermissionRequiredMixin,SingleObjectTemplateResponseMixin, ProcessFormView):
    form_class = WorkspaceUserForm
    template_name = 'bodb/workspace/user_detail.html'
    helpPage='BODB-Edit-User'
    permission_required = 'admin'

    def get_object(self):
        return Workspace.objects.get(id=self.kwargs['id'])

    def get_form_class(self):
        return WorkspaceUserForm

    def get_form(self, form_class):
        return form_class(self.request.POST or None, instance=self.object)

    def get(self, request, *args, **kwargs):
        self.object=User.objects.get(id=self.kwargs.get('pk',None))
        return super(UpdateWorkspaceUserView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object=User.objects.get(id=self.kwargs.get('pk',None))
        return super(UpdateWorkspaceUserView, self).post(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = {}
        context['form']=self.get_form(self.get_form_class())
        context['workspace']=Workspace.objects.get(id=self.kwargs['id'])
        context['helpPage']=self.helpPage
        context['ispopup']=('_popup' in self.request.GET)
        for permission in workspace_permissions:
            if self.request.POST:
                context[permission]=permission in self.request.POST
            else:
                context[permission]=self.object.check_perm('%s' % permission,context['workspace'])
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        for permission in workspace_permissions:
            if context[permission]:
                assign_perm('%s' % permission, self.object, context['workspace'])
            else:
                remove_perm('%s' % permission, self.object, context['workspace'])

        redirect_url='%s' % reverse('workspace_user_view', kwargs={'pk': self.object.id, 'id': context['workspace'].id})
        if context['ispopup']:
            redirect_url+='?_popup=1'
        return redirect(redirect_url)


class CreateWorkspaceBookmarkView(ObjectRolePermissionRequiredMixin, JSONResponseMixin, BaseUpdateView):
    model=Workspace
    permission_required = 'add_bookmark'

    def get_context_data(self, **kwargs):
        context={'msg':u'No POST data sent.' }
        if self.request.is_ajax():
            form=WorkspaceBookmarkForm(self.request.POST,prefix='bookmark')
            if form.is_valid():
                bookmark=form.save(commit=False)
                if bookmark.id is None:
                    bookmark.collator=self.request.user
                bookmark.last_modified_by=self.request.user
                bookmark.save()
                context={
                    'bookmark_id': bookmark.id,
                    'collator_id': bookmark.collator.id,
                    'collator_username': bookmark.collator.username,
                    'url': bookmark.url,
                    'urltrunc': (bookmark.url[:15]+'...') if len(bookmark.url)>15 else bookmark.url,
                    'title': bookmark.title,
                    'description': bookmark.description
                }
            else:
                print(form.errors)
        return context


class DeleteWorkspaceBookmarkView(ObjectRolePermissionRequiredMixin, JSONResponseMixin, BaseUpdateView):
    model=Workspace
    permission_required = 'delete_bookmark'

    def get_context_data(self, **kwargs):
        context={'msg':u'No POST data sent.' }
        if self.request.is_ajax():
            bookmark=WorkspaceBookmark.objects.get(id=kwargs.get('pk2'))
            bookmark.delete()
            context={
                'bookmark_id': kwargs.get('pk2')
            }
        return context