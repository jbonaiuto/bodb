from django.contrib.auth import login
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.shortcuts import redirect, get_object_or_404
from django.views.generic import View, TemplateView, UpdateView, DetailView
from django.views.generic.detail import SingleObjectTemplateResponseMixin
from django.views.generic.edit import BaseUpdateView, FormView, CreateView, BaseCreateView, DeleteView, ProcessFormView
from bodb.forms.workspace import WorkspaceInvitationForm, WorkspaceForm, WorkspaceUserForm, WorkspaceBookmarkForm
from bodb.models import Workspace, UserSubscription, WorkspaceInvitation, BrainImagingSED, ConnectivitySED, ERPSED, WorkspaceActivityItem, SelectedSEDCoord, SavedSEDCoordSelection, Model, BOP, SED, SEDCoord, SSR, Document, WorkspaceBookmark, ERPComponent, Literature, BrainRegion
from bodb.models.discussion import Post
from bodb.signals import coord_selection_created
from bodb.views.main import get_profile, BODBView, set_context_workspace, get_active_workspace
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
            profile=get_profile(self.request)
            workspace=Workspace.objects.select_related('created_by','group','forum').prefetch_related('admin_users','related_models','related_bops','related_seds','related_ssrs','related_literature','related_regions','saved_coordinate_selections').get(id=self.kwargs.get('pk',None))
            profile.active_workspace=workspace
            profile.save()
            cache.set('%d.profile' % self.request.user.id, profile)
            cache.set('%d.active_workspace' % self.request.user.id, workspace)
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
            workspace=Workspace.objects.prefetch_related('admin_users').get(id=self.kwargs.get('pk',None))
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
            workspace=Workspace.objects.prefetch_related('admin_users').get(id=self.kwargs.get('pk',None))
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
            if not Workspace.objects.filter(title=title_str).exists():
                context['available']=1
            # return an error if not
            else:
                context['available']=0
        return context


class ActiveWorkspaceDetailView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        url=get_active_workspace(get_profile(request),request).get_absolute_url()
        if 'show_tour' in self.request.GET:
            url+='?show_tour='+self.request.GET['show_tour']
        return redirect(url)


class WorkspaceInvitationResponseView(LoginRequiredMixin, BODBView):
    def get_context_data(self, **kwargs):
        context=super(WorkspaceInvitationResponseView,self).get_context_data(**kwargs)
        context['invitation']=get_object_or_404(WorkspaceInvitation.objects.select_related('workspace__group','invited_user'),activation_key=context['activation_key'])
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
            user=User.objects.prefetch_related('groups').get(id=context['invitation'].invited_user.id)
            # Add workspace group to user's groups
            user.groups.add(context['invitation'].workspace.group)
            user.save()
            # Create workspace activity item
            activity=WorkspaceActivityItem(workspace=context['invitation'].workspace, user=user)
            activity.text='%s joined the workspace' % user.username
            activity.save()
            self.template_name='bodb/workspace/workspace_invitation_accept.html'
            visibility_q=Q(created_by__is_active=True)
            if not self.request.user.is_superuser:
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
        context=set_context_workspace(context, self.request)
        context['helpPage']='workspaces.html#new-workspace'
        return context

    def form_valid(self, form):
        context=self.get_context_data()
        self.object=form.save(commit=False)
        self.object.created_by=self.request.user
        self.object.save()
        form.save_m2m()
        # add created by user to admins
        self.object.admin_users.add(self.request.user)
        self.object.save()
        for perm in workspace_permissions:
            assign_perm('bodb.%s'%perm,self.request.user,self.object)

        context['profile'].active_workspace=self.object
        context['profile'].save()
        cache.set('%d.profile' % self.request.user.id, context['profile'])
        cache.set('%d.active_workspace' % self.request.user.id, Workspace.objects.select_related('created_by','group','forum').prefetch_related('admin_users','related_models','related_bops','related_seds','related_ssrs','related_literature','related_regions','saved_coordinate_selections').get(id=self.object.id))

        visibility_q=Q(created_by__is_active=True)
        if not self.request.user.is_superuser:
            visibility_q=Q(visibility_q & Q(group__in=self.request.user.groups.all()))
        workspaces=Workspace.objects.filter(visibility_q).order_by('title')
        cache.set('%d.workspaces' % self.request.user.id, list(workspaces))

        return redirect(self.get_success_url())


class UpdateWorkspaceView(ObjectRolePermissionRequiredMixin, EditWorkspaceMixin, UpdateView):
    help_page='BODB-Edit-Workspace'
    permission_required = 'admin'

    def get_object(self, queryset=None):
        if not hasattr(self,'object'):
            self.object=get_object_or_404(Workspace.objects.select_related('created_by').prefetch_related('admin_users'),id=self.kwargs.get('pk',None))
        return self.object

    def get_context_data(self, **kwargs):
        context=super(UpdateWorkspaceView,self).get_context_data(**kwargs)
        context=set_context_workspace(context, self.request)
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
            invitation=WorkspaceInvitation.objects.select_related('invited_user').get(id=kwargs.get('pk',None))
            invitation.send()
            context={'id':invitation.id, 'username': invitation.invited_user.username, 'sent': invitation.sent.strftime("%b %d, %Y, %I:%M %p")}
        return context


class WorkspaceDetailView(ObjectRolePermissionRequiredMixin, FormView):
    template_name = 'bodb/workspace/workspace_view.html'
    form_class=WorkspaceInvitationForm
    permission_required = 'member'

    def get_object(self):
        if not hasattr(self,'object'):
            self.object=get_object_or_404(Workspace.objects.select_related('created_by','group','forum').prefetch_related('admin_users','related_models'), id=self.kwargs.get('pk', None))
        return self.object

    def get(self, request, *args, **kwargs):
        self.object=self.get_object()
        return super(WorkspaceDetailView,self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context=super(WorkspaceDetailView,self).get_context_data(**kwargs)
        context=set_context_workspace(context, self.request)
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
                subscribed_to=(user.id,'All') in context['subscriptions'] or (user.id,'Model') in context['subscriptions'] or\
                              (user.id,'BOP') in context['subscriptions'] or (user.id,'SED') in context['subscriptions'] or \
                              (user.id,'Prediction') in context['subscriptions'] or (user.id,'SSR') in context['subscriptions']
                is_admin=self.object.admin_users.filter(id=usr.id).exists()
            members.append([usr,is_admin,subscribed_to])
        context['members']=members
        if context['admin']:
            context['invitations']=WorkspaceInvitation.objects.filter(workspace=self.object).select_related('invited_user','invited_by')
        context['posts']=list(Post.objects.filter(forum=self.object.forum,parent=None).order_by('-posted').select_related('author'))
        context['bookmarks']=WorkspaceBookmark.objects.filter(workspace=self.object).select_related('collator')

        # Visibility query filter
        visibility = Document.get_security_q(user)

        literature=self.object.related_literature.distinct().select_related('collator').prefetch_related('authors__author')
        context['literatures']=Literature.get_reference_list(literature,context['workspace_literature'],
            context['fav_lit'], context['subscriptions'])

        brain_regions=self.object.related_regions.distinct().select_related('nomenclature').prefetch_related('nomenclature__species')
        context['brain_regions']=BrainRegion.get_region_list(brain_regions,context['workspace_regions'],
            context['fav_regions'])

        models=self.object.related_models.filter(visibility).distinct().select_related('collator').prefetch_related('authors__author')
        context['models']=Model.get_model_list(models, context['workspace_models'], context['fav_docs'],
            context['subscriptions'])
        context['model_seds']=Model.get_sed_map(models, user)

        bops=self.object.related_bops.filter(visibility).distinct().select_related('collator')
        context['bops']=BOP.get_bop_list(bops, context['workspace_bops'], context['fav_docs'], context['subscriptions'])
        context['bop_relationships']=BOP.get_bop_relationships(bops, user)

        generic_seds=self.object.related_seds.filter(Q(type='generic') & visibility).distinct().select_related('collator')
        context['generic_seds']=SED.get_sed_list(generic_seds, context['workspace_seds'], context['fav_docs'],
            context['subscriptions'])

        ws_imaging_seds=BrainImagingSED.objects.filter(sed_ptr__in=self.object.related_seds.filter(visibility)).distinct().select_related('collator')
        coords=[SEDCoord.objects.filter(sed=sed).select_related('coord__threedcoord') for sed in ws_imaging_seds]
        context['imaging_seds']=SED.get_sed_list(ws_imaging_seds, context['workspace_seds'], context['fav_docs'],
            context['subscriptions'])
        if user.is_authenticated() and not user.is_anonymous():
            context['imaging_seds']=BrainImagingSED.augment_sed_list(context['imaging_seds'],coords,
                context['selected_sed_coords'].values_list('sed_coordinate__id',flat=True))
        else:
            context['imaging_seds']=BrainImagingSED.augment_sed_list(context['imaging_seds'],coords, [])

        conn_seds=ConnectivitySED.objects.filter(sed_ptr__in=self.object.related_seds.filter(visibility)).distinct().select_related('collator','target_region__nomenclature','source_region__nomenclature')
        context['connectivity_seds']=SED.get_sed_list(conn_seds, context['workspace_seds'], context['fav_docs'],
            context['subscriptions'])
        context['connectivity_sed_regions']=ConnectivitySED.get_region_map(conn_seds)

        ws_erp_seds=ERPSED.objects.filter(sed_ptr__in=self.object.related_seds.filter(visibility)).distinct().select_related('collator')
        components=[ERPComponent.objects.filter(erp_sed=erp_sed).select_related('electrode_cap','electrode_position__position_system') for erp_sed in ws_erp_seds]
        context['erp_seds']=SED.get_sed_list(ws_erp_seds, context['workspace_seds'], context['fav_docs'],
            context['subscriptions'])
        context['erp_seds']=ERPSED.augment_sed_list(context['erp_seds'],components)

        ssrs=self.object.related_ssrs.filter(visibility).distinct().select_related('collator')
        context['ssrs']=SSR.get_ssr_list(ssrs, context['workspace_ssrs'], context['fav_docs'], context['subscriptions'])

        context['activity_stream']=WorkspaceActivityItem.objects.filter(workspace=self.object).order_by('-time').select_related('user')

        # loaded coordinate selection
        context['loaded_coord_selection']=None
        if user.is_authenticated() and not user.is_anonymous():
            if context['profile'].loaded_coordinate_selection and\
               context['profile'].loaded_coordinate_selection in self.object.saved_coordinate_selections.all():
                context['loaded_coord_selection']=context['profile'].loaded_coordinate_selection
                SelectedSEDCoord.objects.filter(saved_selection__id=context['loaded_coord_selection'].id).update(selected=True)
        # load saved selections
        context['saved_coord_selections']=self.object.saved_coordinate_selections.all().select_related('user','last_modified_by')

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

        return context


class DeleteWorkspaceView(ObjectRolePermissionRequiredMixin, DeleteView):
    model=Workspace
    success_url = '/bodb/workspaces/'
    permission_required = 'admin'


class SaveWorkspaceCoordinateSelectionView(ObjectRolePermissionRequiredMixin, SaveCoordinateSelectionView):
    model=Workspace

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
                active_workspace=get_active_workspace(get_profile(self.request),self.request)
                coord_selection=SavedSEDCoordSelection.objects.get(id=context['id'])
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
        active_workspace=get_active_workspace(get_profile(self.request),self.request)
        if coordSelection in active_workspace.saved_coordinate_selections.all():
            active_workspace.saved_coordinate_selections.remove(coordSelection)
            active_workspace.save()
        return super(DeleteWorkspaceCoordinateSelectionView,self).get_context_data(**kwargs)


class WorkspaceUserDetailView(ObjectRolePermissionRequiredMixin, DetailView):
    model = Workspace
    template_name = 'bodb/workspace/user_view.html'
    permission_required = 'admin'

    def get_object(self, queryset=None):
        if not hasattr(self,'object'):
            self.object=get_object_or_404(Workspace.objects.prefetch_related('admin_users'),id=self.kwargs.get('pk',None))
        return self.object

    def get_context_data(self, **kwargs):
        context = super(WorkspaceUserDetailView,self).get_context_data(**kwargs)
        context=set_context_workspace(context, self.request)
        context['user']=User.objects.prefetch_related('groups').get(id=self.kwargs['id'])
        context['helpPage']='BODB-View-Workspace-User'
        context['ispopup']=('_popup' in self.request.GET)
        context['action']=self.request.GET.get('action',None)
        for permission in workspace_permissions:
            context[permission]=context['user'].has_perm('%s' % permission,self.object)
        context['workspace']=self.object
        context['object']=context['user']
        return context


class UpdateWorkspaceUserView(ObjectRolePermissionRequiredMixin,SingleObjectTemplateResponseMixin, ProcessFormView):
    form_class = WorkspaceUserForm
    template_name = 'bodb/workspace/user_detail.html'
    helpPage='BODB-Edit-User'
    permission_required = 'admin'

    def get_object(self):
        if not hasattr(self,'object'):
            self.object=get_object_or_404(Workspace.objects.prefetch_related('admin_users'), id=self.kwargs.get('id',None))
        return self.object

    def get_form(self, form_class):
        return form_class(self.request.POST or None)

    def get_form_class(self):
        return WorkspaceUserForm

    def get_context_data(self, **kwargs):
        context = {}
        context=set_context_workspace(context, self.request)
        context['user']=User.objects.get(id=self.kwargs.get('pk',None))
        context['form']=self.form_class(self.request.POST or None, instance=context['user'])
        context['helpPage']=self.helpPage
        context['ispopup']=('_popup' in self.request.GET)
        for permission in workspace_permissions:
            if self.request.POST:
                context[permission]=permission in self.request.POST
            else:
                context[permission]=context['user'].has_perm('%s' % permission,self.object)
        context['workspace']=self.object
        context['object']=context['user']
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