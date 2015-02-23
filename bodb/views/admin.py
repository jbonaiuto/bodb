from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group, Permission
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseServerError, HttpResponseRedirect
from django.shortcuts import redirect, render_to_response, render, get_object_or_404
from django.views.generic import UpdateView, View, DetailView
from django.views.generic.edit import BaseUpdateView
from bodb.forms.admin import BodbProfileForm, UserForm, GroupForm
from bodb.forms.subscription import SubscriptionFormSet, UserSubscriptionFormSet
from bodb.models import BodbProfile, Nomenclature, Model, BOP, SED, ConnectivitySED, BrainImagingSED, SEDCoord, ERPSED, ERPComponent, SSR, Literature
from bodb.views.main import set_context_workspace
from bodb.views.security import AdminCreateView, AdminUpdateView
from guardian.mixins import LoginRequiredMixin
from guardian.shortcuts import assign_perm, remove_perm
from registration.backends.default.views import RegistrationView
from registration.models import User
from uscbp import settings
from uscbp.views import JSONResponseMixin
from django.core.cache import cache

@login_required
def logout_view(request):
    # perform logout
    logout(request)
    # redirect to index
    return render_to_response('registration/logout.html', dictionary={'user':User.objects.get(id = settings.ANONYMOUS_USER_ID)})


# check if a username is unique
def username_available(request):
    # if ajax request and username provided
    if request.is_ajax() and 'username' in request.POST:
        username_str = request.POST['username']
        # return response if username is unique
        if not User.objects.filter(username=username_str).exists():
            return HttpResponse(username_str)
        # return error if already taken
        else:
            return HttpResponseServerError(username_str)
    return HttpResponseServerError("Requires a username field.")


class UpdateUserProfileView(LoginRequiredMixin,UpdateView):
    form_class = BodbProfileForm
    model = BodbProfile
    template_name = 'registration/profile_detail.html'
    success_url = '/accounts/profile/?msg=saved'

    def get_object(self, queryset=None):
        return self.request.user.get_profile()

    def get_context_data(self, **kwargs):
        context = super(UpdateUserProfileView,self).get_context_data(**kwargs)
        context=set_context_workspace(context, self.request)
        context['helpPage']='user_profile.html'
        context['subscription_formset']=SubscriptionFormSet(self.request.POST or None,instance=self.request.user,
            prefix='subscription')
        context['user_subscription_formset']=UserSubscriptionFormSet(self.request.POST or None,
            instance=self.request.user, prefix='user_subscription')
        context['msg']=self.request.GET.get('msg',None)
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        subscription_formset = context['subscription_formset']
        user_subscription_formset = context['user_subscription_formset']
        if subscription_formset.is_valid() and user_subscription_formset.is_valid():
            self.object = form.save()

            # save subscriptions
            subscription_formset.instance = self.object
            for subscription_form in subscription_formset.forms:
                if not subscription_form in subscription_formset.deleted_forms:
                    subscription_form.save()

            # save user subscriptions
            user_subscription_formset.instance = self.object
            for user_subscription_form in user_subscription_formset.forms:
                if not user_subscription_form in user_subscription_formset.deleted_forms:
                    user_subscription_form.save()

            # delete removed subscriptions
            for subscription_form in subscription_formset.deleted_forms:
                if subscription_form.instance.id:
                    subscription_form.instance.delete()

            # delete removed user subscriptions
            for user_subscription_form in user_subscription_formset.deleted_forms:
                if user_subscription_form.instance.id:
                    user_subscription_form.instance.delete()

            # update user object
            user=self.request.user
            user.first_name=self.request.POST['first_name']
            user.last_name=self.request.POST['last_name']
            user.email=self.request.POST['email']
            if 'password1' in self.request.POST and len(self.request.POST['password1']):
                user.set_password(self.request.POST['password1'])
            user.save()

            cache.set('%d.profile' % user.id, self.object)

            return redirect(self.success_url)
        else:
            return self.render_to_response(self.get_context_data(form=form))


class AdminDetailView(View):
    template='bodb/admin/admin.html'

    def get(self, request, *args, **kwargs):
        if request.user.is_superuser:
            context={'helpPage':'admin.html',
                     'users': User.objects.all().order_by('username').prefetch_related('groups'),
                     'groups': Group.objects.all().order_by('name'),
                     'nomenclatures': Nomenclature.objects.all().order_by('name')}
            context=set_context_workspace(context, self.request)
            return render(request, self.template, context)
        else:
            return HttpResponseRedirect('/bodb/index.html')


bodb_permissions=['add_literature','change_literature','delete_literature',
                  'add_model', 'save_model', 'public_model', 'change_model', 'delete_model',
                  'add_module', 'change_module', 'delete_module',
                  'add_bop', 'save_bop', 'public_bop', 'change_bop', 'delete_bop',
                  'add_sed', 'save_sed', 'public_sed', 'change_sed', 'delete_sed',
                  'add_ssr', 'save_ssr', 'public_ssr', 'change_ssr', 'delete_ssr',
                  'add_prediction', 'save_prediction', 'public_prediction', 'change_prediction',
                  'delete_prediction',
                  'add_nomenclature', 'change_nomenclature', 'delete_nomenclature']


class EditUserMixin():
    model = User
    form_class = UserForm
    template_name = 'bodb/admin/user_detail.html'

    def form_valid(self, form):
        if self.request.user.is_superuser:
            context = self.get_context_data()
            user=form.save()

            for permission in bodb_permissions:
                if context[permission]:
                    assign_perm('bodb.%s' % permission, user)
                else:
                    remove_perm('bodb.%s' % permission, user)

            redirect_url='%s?action=%s' % (reverse('user_view', kwargs={'pk': user.id}),self.action)
            if context['ispopup']:
                redirect_url+='&_popup=1'
        else:
            redirect_url='/bodb/index.html'
        return redirect(redirect_url)


class CreateUserView(EditUserMixin,AdminCreateView):
    action='add'

    def get_context_data(self, **kwargs):
        context = super(CreateUserView,self).get_context_data(**kwargs)
        context=set_context_workspace(context, self.request)
        context['helpPage']='admin.html#insert-user'
        context['ispopup']=('_popup' in self.request.GET)
        if self.request.POST:
            for permission in bodb_permissions:
                context[permission]=permission in self.request.POST
        else:
            for permission in bodb_permissions:
                context[permission]=False
        return context


class UpdateUserView(EditUserMixin,AdminUpdateView):
    action='edit'

    def get_context_data(self, **kwargs):
        context = super(UpdateUserView,self).get_context_data(**kwargs)
        context=set_context_workspace(context, self.request)
        context['helpPage']='admin.html#edit-user'
        context['ispopup']=('_popup' in self.request.GET)
        if self.request.POST:
            for permission in bodb_permissions:
                context[permission]=permission in self.request.POST
        else:
            for permission in bodb_permissions:
                context[permission]=self.object.has_perm('bodb.%s' % permission)
        return context


class UserDetailView(DetailView):
    model = User
    template_name = 'bodb/admin/user_view.html'

    def get_object(self, queryset=None):
        if not hasattr(self,'object'):
            self.object=get_object_or_404(User.objects.prefetch_related('groups'),id=self.kwargs.get(self.pk_url_kwarg, None))
        return self.object

    def get_context_data(self, **kwargs):
        context = super(UserDetailView,self).get_context_data(**kwargs)
        context=set_context_workspace(context, self.request)
        context['helpPage']='admin.html#view-user'
        context['ispopup']=('_popup' in self.request.GET)
        context['action']=self.request.GET.get('action',None)
        for permission in bodb_permissions:
            context[permission]=self.object.has_perm('bodb.%s' % permission)

        models=Model.objects.filter(collator=self.object).select_related('collator').prefetch_related('authors__author')
        context['models']=Model.get_model_list(models,context['workspace_models'], context['fav_docs'],
            context['subscriptions'])
        context['model_seds']=Model.get_sed_map(models, self.request.user)

        bops=BOP.objects.filter(collator=self.object).select_related('collator')
        context['bops']=BOP.get_bop_list(bops, context['workspace_bops'], context['fav_docs'], context['subscriptions'])
        context['bop_relationships']=BOP.get_bop_relationships(bops, self.request.user)

        generic_seds=SED.objects.filter(type='generic',collator=self.object).select_related('collator')
        context['generic_seds']=SED.get_sed_list(generic_seds, context['workspace_seds'], context['fav_docs'],
            context['subscriptions'])

        conn_seds=ConnectivitySED.objects.filter(collator=self.object).select_related('collator','target_region__nomenclature','source_region__nomenclature')
        context['connectivity_seds']=SED.get_sed_list(conn_seds, context['workspace_seds'], context['fav_docs'],
            context['subscriptions'])
        context['connectivity_sed_regions']=ConnectivitySED.get_region_map(conn_seds)

        imaging_seds=BrainImagingSED.objects.filter(collator=self.object).select_related('collator')
        coords=[SEDCoord.objects.filter(sed=sed).select_related('coord__threedcoord') for sed in imaging_seds]
        context['imaging_seds']=SED.get_sed_list(imaging_seds, context['workspace_seds'], context['fav_docs'],
            context['subscriptions'])
        context['imaging_seds']=BrainImagingSED.augment_sed_list(context['imaging_seds'],coords,
            context['selected_sed_coords'].values_list('sed_coordinate__id',flat=True))

        erp_seds=ERPSED.objects.filter(collator=self.object).select_related('collator')
        components=[ERPComponent.objects.filter(erp_sed=erp_sed).select_related('electrode_cap','electrode_position__position_system') for erp_sed in erp_seds]
        context['erp_seds']=SED.get_sed_list(erp_seds, context['workspace_seds'], context['fav_docs'],
            context['subscriptions'])
        context['erp_seds']=ERPSED.augment_sed_list(context['erp_seds'],components)

        ssrs=SSR.objects.filter(collator=self.object).select_related('collator')
        context['ssrs']=SSR.get_ssr_list(ssrs, context['workspace_ssrs'], context['fav_docs'], context['subscriptions'])

        literature=Literature.objects.filter(collator=self.object).select_related('collator').prefetch_related('authors__author')
        context['literatures']=Literature.get_reference_list(literature,context['workspace_literature'],
            context['fav_lit'], context['subscriptions'])
        return context


class UserToggleActiveView(JSONResponseMixin,BaseUpdateView):
    model = User

    def get_context_data(self, **kwargs):
        context={'msg':u'No POST data sent.' }
        if self.request.is_ajax() and 'active' in self.request.POST and self.request.user.is_superuser:
            user=User.objects.get(id=self.kwargs.get('pk', None))
            # change active status
            user.is_active=(self.request.POST['active']=='true')
            user.save()

            context={
                'id': user.id,
                'active': user.is_active
            }
        return context


class UserToggleStaffView(JSONResponseMixin,BaseUpdateView):
    model = User

    def get_context_data(self, **kwargs):
        context={'msg':u'No POST data sent.' }
        if self.request.is_ajax() and 'staff' in self.request.POST and self.request.user.is_superuser:
            user=User.objects.get(id=self.kwargs.get('pk', None))
            # change staff status
            user.is_staff=(self.request.POST['staff']=='true')
            user.save()

            context = {
                'id': user.id,
                'staff': user.is_staff
            }
        return context


class UserToggleAdminView(JSONResponseMixin,BaseUpdateView):
    model = User

    def get_context_data(self, **kwargs):
        context={'msg':u'No POST data sent.' }
        if self.request.is_ajax() and 'admin' in self.request.POST and self.request.user.is_superuser:
            user=User.objects.get(id=self.kwargs.get('pk', None))
            # change admin status
            user.is_superuser=(self.request.POST['admin']=='true')
            user.save()

            context = {
                'id': user.id,
                'admin': user.is_superuser
            }
        return context


class GetUserIconUrlView(JSONResponseMixin,BaseUpdateView):
    model = User

    def get_context_data(self, **kwargs):
        context = {'msg':u'No POST data sent.' }
        if self.request.is_ajax():
            user=User.objects.get(id=self.kwargs.get('pk',None))
            # get icon url
            if user.get_profile().avatar:
                context = {'url': user.get_profile().avatar.url }
            else:
                context = {'url':''}
        return context


class CreateGroupView(AdminCreateView):
    model = Group
    form_class = GroupForm
    template_name = 'bodb/admin/group_detail.html'

    def get_context_data(self, **kwargs):
        context = super(CreateGroupView,self).get_context_data(**kwargs)
        context=set_context_workspace(context, self.request)
        context['helpPage']='admin.html#insert-group'
        if self.request.POST:
            for permission in bodb_permissions:
                context[permission]=permission in self.request.POST
        else:
            for permission in bodb_permissions:
                context[permission]=False
        context['ispopup']=('_popup' in self.request.GET)
        return context

    def form_valid(self, form):
        context = self.get_context_data()

        group=form.save()

        for permission in bodb_permissions:
            if context[permission]:
                assign_perm('bodb.%s' % permission, group)
            else:
                remove_perm('bodb.%s' % permission, group)

        redirect_url='%s?action=add' % reverse('group_view', kwargs={'pk': group.id})
        if context['ispopup']:
            redirect_url+='&_popup=1'
        return redirect(redirect_url)


class UpdateGroupView(AdminUpdateView):
    model = Group
    form_class = GroupForm
    template_name = 'bodb/admin/group_detail.html'

    def get_context_data(self, **kwargs):
        context = super(UpdateGroupView,self).get_context_data(**kwargs)
        context=set_context_workspace(context, self.request)
        context['helpPage']='admin.html#edit-group'
        if self.request.POST:
            for permission in bodb_permissions:
                context[permission]=permission in self.request.POST
        else:
            for permission in bodb_permissions:
                context[permission]=self.object.permissions.filter(id=Permission.objects.get(codename=permission).id)
        context['ispopup']=('_popup' in self.request.GET)
        return context

    def form_valid(self, form):
        context = self.get_context_data()

        group=form.save()

        for permission in bodb_permissions:
            if context[permission]:
                assign_perm('bodb.%s' % permission, group)
            else:
                remove_perm('bodb.%s' % permission, group)

        redirect_url='%s?action=edit' % reverse('group_view', kwargs={'pk': group.id})
        if context['ispopup']:
            redirect_url+='&_popup=1'
        return redirect(redirect_url)


class GroupDetailView(DetailView):
    model = Group
    template_name = 'bodb/admin/group_view.html'

    def get_context_data(self, **kwargs):
        context = super(GroupDetailView,self).get_context_data(**kwargs)
        context=set_context_workspace(context, self.request)
        context['helpPage']='admin.html#view-group'
        context['ispopup']=('_popup' in self.request.GET)
        context['action']=self.request.GET.get('action',None)
        for permission in bodb_permissions:
            context[permission]=self.object.permissions.filter(id=Permission.objects.get(codename=permission).id)
        return context


class DeleteGroupView(JSONResponseMixin,BaseUpdateView):
    model = Group

    def get_context_data(self, **kwargs):
        context={'msg':u'No POST data sent.' }
        if self.request.is_ajax() and self.request.user.is_superuser:
            # load group
            group=Group.objects.get(id=self.kwargs.get('pk', None))

            # remove users
            related_users=User.objects.filter(groups__id=self.request.POST['id']).prefetch_related('groups')
            for user in related_users:
                user.groups.remove(group)
                user.save()

            # delete group
            group.delete()
            context = {'id': self.request.POST['id']}
        return context


class BodbRegistrationView(RegistrationView):

    def get_context_data(self, **kwargs):
        context=super(RegistrationView,self).get_context_data(**kwargs)
        context=set_context_workspace(context, self.request)
        context['helpPage']='login_register.html'
        return context

    def form_valid(self, request, form):
        new_user = self.register(request, **form.cleaned_data)
        profile=new_user.get_profile()
        new_user.first_name=request.POST['first_name']
        new_user.last_name=request.POST['last_name']
        new_user.save()
        profile.affiliation=request.POST['affiliation']
        profile.save()
        cache.set('%d.profile' % new_user.id, self.object)

        success_url = self.get_success_url(request, new_user)

        # success_url may be a simple string, or a tuple providing the
        # full argument set for redirect(). Attempting to unpack it
        # tells us which one it is.
        try:
            to, args, kwargs = success_url
            return redirect(to, *args, **kwargs)
        except ValueError:
            return redirect(success_url)