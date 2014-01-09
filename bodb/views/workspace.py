from django.contrib.auth import login
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.shortcuts import redirect, get_object_or_404
from django.views.generic import ListView, View, TemplateView, UpdateView, DetailView
from django.views.generic.detail import SingleObjectTemplateResponseMixin
from django.views.generic.edit import BaseUpdateView, FormView, CreateView, BaseCreateView, DeleteView, ProcessFormView
from bodb.forms import WorkspaceInvitationForm, WorkspaceForm, WorkspaceUserForm, WorkspaceBookmarkForm
from bodb.models import Workspace, UserSubscription, WorkspaceInvitation, BrainImagingSED, ConnectivitySED, ERPSED, WorkspaceActivityItem, SelectedSEDCoord, SavedSEDCoordSelection, Model, BOP, SED, SEDCoord, SSR, Document, WorkspaceBookmark
from bodb.models.discussion import Post
from bodb.signals import coord_selection_created
from bodb.views.main import BODBView
from bodb.views.sed import SaveCoordinateSelectionView
from guardian.models import User
from guardian.shortcuts import assign_perm, remove_perm
from uscbp.views import JSONResponseMixin

workspace_permissions=['add_post','add_entry','remove_entry',
                       'add_coordinate_selection','change_coordinate_selection','delete_coordinate_selection',
                       'add_bookmark','delete_bookmark']

class WorkspaceListView(ListView):
    template_name = 'bodb/workspace/workspace_list_view.html'

    def get_queryset(self):
        visibility_q=Q(created_by__is_active=True)
        if not self.request.user.is_superuser:
            visibility_q=Q(visibility_q & Q(group__in=self.request.user.groups.all()))
        return Workspace.objects.filter(visibility_q).order_by('title')


    def get_context_data(self, **kwargs):
        context=super(WorkspaceListView,self).get_context_data(object_list=self.get_queryset())
        context['active_workspace']=self.request.user.get_profile().active_workspace
        context['helpPage']='BODB-Workspace'
        return context


class ActivateWorkspaceView(JSONResponseMixin,BaseUpdateView):
    model = Workspace

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


class WorkspaceUserToggleAdminView(JSONResponseMixin,BaseUpdateView):
    model = Workspace

    def get_context_data(self, **kwargs):
        context={'msg':u'No POST data sent.' }
        if self.request.is_ajax():
            workspace=Workspace.objects.get(id=self.kwargs.get('pk',None))
            user=User.objects.get(id=self.request.POST['user_id'])
            if self.request.POST['admin']:
                if not user in workspace.admin_users.all():
                    workspace.admin_users.add(user)
            else:
                if user in workspace.admin_users.all():
                    workspace.admin_users.remove(user)
            context={
                'user_id': user.id,
                'admin': self.request.POST['admin']
            }
        return context


class WorkspaceUserRemoveView(JSONResponseMixin,BaseUpdateView):
    model = Workspace

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


class WorkspaceTitleAvailableView(JSONResponseMixin,BaseCreateView):
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


class ActiveWorkspaceDetailView(View):
    def get(self, request, *args, **kwargs):
        profile=self.request.user.get_profile()
        return redirect(profile.active_workspace.get_absolute_url())


class WorkspaceInvitationResponseView(TemplateView):
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
        context['invitation'].save()
        return self.render_to_response(context)


class EditWorkspaceMixin():
    model=Workspace
    form_class = WorkspaceForm
    template_name = 'bodb/workspace/workspace_detail.html'


class CreateWorkspaceView(EditWorkspaceMixin, CreateView):
    help_page='BODB-Insert-Workspace'

    def get_context_data(self, **kwargs):
        context=super(CreateWorkspaceView,self).get_context_data(**kwargs)
        context['helpPage']=self.help_page
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

        return redirect(self.get_success_url())


class UpdateWorkspaceView(EditWorkspaceMixin, UpdateView):
    help_page='BODB-Edit-Workspace'

    def get_context_data(self, **kwargs):
        context=super(UpdateWorkspaceView,self).get_context_data(**kwargs)
        context['helpPage']=self.help_page
        return context

    def form_valid(self, form):
        self.object=form.save()
        return redirect(self.get_success_url())


class WorkspaceInvitationView(JSONResponseMixin, BaseUpdateView):
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


class WorkspaceInvitationResendView(JSONResponseMixin, BaseUpdateView):
    model=WorkspaceInvitation
    def get_context_data(self, **kwargs):
        context={'msg':u'No POST data sent.' }
        if self.request.is_ajax():
            invitation=WorkspaceInvitation.objects.get(id=kwargs.get('pk',None))
            invitation.send()
            context={'id':invitation.id, 'username': invitation.invited_user.username, 'sent': invitation.sent.strftime("%b %d, %Y, %I:%M %p")}
        return context


class WorkspaceDetailView(BODBView,FormView):
    template_name = 'bodb/workspace/workspace_view.html'
    form_class=WorkspaceInvitationForm

    def get(self, request, *args, **kwargs):
        self.object=get_object_or_404(Workspace, id=self.kwargs.get('pk', None))
        return super(WorkspaceDetailView,self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context=super(WorkspaceDetailView,self).get_context_data(**kwargs)
        context['helpPage']='BODB-View-Workspace'
        context['workspace']=self.object

        context['connectionGraphId']='connectivitySEDDiagram'
        context['bopGraphId']='bopRelationshipDiagram'
        context['modelGraphId']='modelRelationshipDiagram'

        context['form']=WorkspaceInvitationForm(initial={
            'invited_by':self.request.user,
            'workspace':self.object
        })
        invited_user_ids=[]
        for invite in WorkspaceInvitation.objects.filter(workspace=self.object).exclude(status='declined'):
            invited_user_ids.append(invite.invited_user.id)
        context['form'].fields['invited_users'].queryset=User.objects.all().exclude(id=self.request.user.id).exclude(id__in=invited_user_ids)

        context['selected']=self.request.GET.get('selected','activity')
        context['admin']=(self.request.user in self.object.admin_users.all()) or self.request.user.is_superuser
        context['can_delete_coord_selection']=self.request.user.has_perm('delete_coordinate_selection',self.object)
        context['can_add_coord_selection']=self.request.user.has_perm('add_coordinate_selection',self.object)
        context['can_change_coord_selection']=self.request.user.has_perm('change_coordinate_selection',self.object)
        context['can_add_post']=self.request.user.has_perm('add_post',self.object)
        context['can_add_entry']=self.request.user.has_perm('add_entry',self.object)
        context['can_remove_entry']=self.request.user.has_perm('remove_entry',self.object)
        context['can_add_bookmark']=self.request.user.has_perm('add_bookmark',self.object)
        context['can_change_bookmark']=self.request.user.has_perm('change_bookmark',self.object)
        context['can_delete_bookmark']=self.request.user.has_perm('delete_bookmark',self.object)
        members=[]
        for usr in self.object.group.user_set.all():
            subscribed_to=UserSubscription.objects.filter(subscribed_to_user=usr, user=self.request.user).count()>0
            is_admin=usr in self.object.admin_users.all()
            members.append([usr,is_admin,subscribed_to])
        context['members']=members
        if context['admin']:
            context['invitations']=WorkspaceInvitation.objects.filter(workspace=self.object)
        context['posts']=list(Post.objects.filter(forum=self.object.forum,parent=None).order_by('-posted'))
        context['bookmarks']=WorkspaceBookmark.objects.filter(workspace=self.object)

        # Visibility query filter
        user=self.request.user
        visibility = Document.get_security_q(user)

        context['models']=Model.get_model_list(self.object.related_models.filter(visibility).distinct(),user)
        context['bops']=BOP.get_bop_list(self.object.related_bops.filter(visibility).distinct(),user)
        context['generic_seds']=SED.get_sed_list(self.object.related_seds.filter(Q(type='generic') & visibility).distinct(),
            user)
        ws_imaging_seds=BrainImagingSED.objects.filter(sed_ptr__in=self.object.related_seds.filter(visibility)).distinct()
        coords=[SEDCoord.objects.filter(sed=sed) for sed in ws_imaging_seds]
        context['imaging_seds']=SED.get_sed_list(ws_imaging_seds,user)
        context['imaging_seds']=BrainImagingSED.augment_sed_list(context['imaging_seds'],coords)
        context['connectivity_seds']=SED.get_sed_list(ConnectivitySED.objects.filter(sed_ptr__in=self.object.related_seds.filter(visibility)).distinct(),
            user)
        context['erp_seds']=SED.get_sed_list(ERPSED.objects.filter(sed_ptr__in=self.object.related_seds.filter(visibility)).distinct(),user)
        context['ssrs']=SSR.get_ssr_list(self.object.related_ssrs.filter(visibility).distinct(), user)

        context['activity_stream']=WorkspaceActivityItem.objects.filter(workspace=self.object).order_by('-time')

        # loaded coordinate selection
        context['loaded_coord_selection']=None
        if self.request.user.get_profile().loaded_coordinate_selection and \
           self.request.user.get_profile().loaded_coordinate_selection in self.object.saved_coordinate_selections.all():
            context['loaded_coord_selection']=self.request.user.get_profile().loaded_coordinate_selection
            SelectedSEDCoord.objects.filter(saved_selection__id=context['loaded_coord_selection'].id).update(selected=True)
        # load saved selections
        context['saved_coord_selections']=self.object.saved_coordinate_selections.all()

        # load selected coordinates
        selected_coord_objs=SelectedSEDCoord.objects.filter(selected=True, user__id=self.request.user.id)

        context['selected_coords']=[]
        for coord in selected_coord_objs:
            coord_array={
                'sed_name':coord.sed_coordinate.sed.title,
                'sed_id':coord.sed_coordinate.sed.id,
                'id':coord.id,
                'collator':coord.get_collator_str(),
                'brain_region':coord.sed_coordinate.named_brain_region,
                'hemisphere':coord.sed_coordinate.hemisphere,
                'x':coord.sed_coordinate.coord.x,
                'y':coord.sed_coordinate.coord.y,
                'z':coord.sed_coordinate.coord.z,
                'rCBF':None,
                'statistic':coord.sed_coordinate.statistic,
                'statistic_value':coord.sed_coordinate.statistic_value.__float__(),
                'extra_data':coord.sed_coordinate.extra_data
            }
            if coord.sed_coordinate.rcbf is not None:
                coord_array['rCBF']=coord.sed_coordinate.rcbf.__float__()
            context['selected_coords'].append(coord_array)

        # load selected coordinate Ids
        selected_coord_ids=[]
        for coord in selected_coord_objs:
            selected_coord_ids.append(coord.sed_coordinate.id)
        context['selected_coord_ids']=selected_coord_ids

        return context


class DeleteWorkspaceView(DeleteView):
    model=Workspace
    success_url = '/bodb/workspaces/'


class SaveWorkspaceCoordinateSelectionView(SaveCoordinateSelectionView):
    model=SavedSEDCoordSelection
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


class DeleteWorkspaceCoordinateSelectionView(JSONResponseMixin, BaseCreateView):
    model=SavedSEDCoordSelection
    def get_context_data(self, **kwargs):
        # load selection
        coordSelection=get_object_or_404(SavedSEDCoordSelection, id=self.request.POST['id'])
        active_workspace=self.request.user.get_profile().active_workspace
        if coordSelection in active_workspace.saved_coordinate_selections.all():
            active_workspace.saved_coordinate_selections.remove(coordSelection)
            active_workspace.save()
        return super(DeleteWorkspaceCoordinateSelectionView,self).get_context_data(**kwargs)


class WorkspaceUserDetailView(DetailView):
    model = User
    template_name = 'bodb/workspace/user_view.html'

    def get_context_data(self, **kwargs):
        context = super(WorkspaceUserDetailView,self).get_context_data(**kwargs)
        context['workspace']=Workspace.objects.get(id=self.kwargs['id'])
        context['helpPage']='BODB-View-Workspace-User'
        context['ispopup']=('_popup' in self.request.GET)
        context['action']=self.request.GET.get('action',None)
        for permission in workspace_permissions:
            context[permission]=self.object.has_perm('%s' % permission,context['workspace'])
        return context


class UpdateWorkspaceUserView(SingleObjectTemplateResponseMixin, ProcessFormView):
    form_class = WorkspaceUserForm
    template_name = 'bodb/workspace/user_detail.html'
    helpPage='BODB-Edit-User'

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
                context[permission]=self.object.has_perm('%s' % permission,context['workspace'])
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


class CreateWorkspaceBookmarkView(JSONResponseMixin, BaseUpdateView):
    model=Workspace

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


class DeleteWorkspaceBookmarkView(JSONResponseMixin, BaseUpdateView):
    model=Workspace

    def get_context_data(self, **kwargs):
        context={'msg':u'No POST data sent.' }
        if self.request.is_ajax():
            bookmark=WorkspaceBookmark.objects.get(id=kwargs.get('pk2'))
            bookmark.delete()
            context={
                'bookmark_id': kwargs.get('pk2')
            }
        return context