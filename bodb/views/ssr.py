from django.db.models import Q
from django.shortcuts import redirect, get_object_or_404
from django.views.generic import UpdateView, DeleteView, CreateView, TemplateView
from django.views.generic.edit import BaseUpdateView
from bodb.forms.document import DocumentFigureFormSet
from bodb.forms.ssr import SSRForm
from bodb.models import SSR, DocumentFigure, Model, WorkspaceActivityItem, Document, UserSubscription
from bodb.views.document import DocumentDetailView, DocumentAPIDetailView, DocumentAPIListView
from bodb.views.main import set_context_workspace, get_active_workspace, get_profile, BODBView
from bodb.views.security import ObjectRolePermissionRequiredMixin
from guardian.mixins import LoginRequiredMixin, PermissionRequiredMixin
from uscbp.views import JSONResponseMixin

from bodb.serializers import SSRSerializer

class EditSSRMixin():
    model = SSR
    form_class = SSRForm
    template_name = 'bodb/ssr/ssr_detail.html'

    def form_valid(self, form):
        context = self.get_context_data()
        figure_formset = context['figure_formset']

        if figure_formset.is_valid():

            self.object = form.save(commit=False)

            # Set the collator if this is a new BOP
            if self.object.id is None:
                self.object.collator=self.request.user
            self.object.last_modified_by=self.request.user
            self.object.save()
            # Needed to save the literature and tags
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

            url=self.get_success_url()+'?action='+context['action']
            if context['ispopup']:
                url+='&_popup=1'
            if 'type' in context and context['type'] is not None:
                url+='&type=%s' % context['type']
            if 'idx' in context and context['idx']>-1:
                url+='&idx=%s' % context['idx']
            return redirect(url)
        else:
            return self.render_to_response(self.get_context_data(form=form))


class UpdateSSRView(EditSSRMixin, ObjectRolePermissionRequiredMixin, UpdateView):
    permission_required='edit'

    def get_object(self, queryset=None):
        if not hasattr(self,'object'):
            self.object=get_object_or_404(SSR.objects.select_related('collator'),id=self.kwargs.get(self.pk_url_kwarg, None))
        return self.object

    def get_context_data(self, **kwargs):
        context = super(UpdateSSRView,self).get_context_data(**kwargs)
        context=set_context_workspace(context, self.request)
        context['figure_formset']=DocumentFigureFormSet(self.request.POST or None, self.request.FILES or None,
            instance=self.object, queryset=DocumentFigure.objects.filter(document=self.object), prefix='figure')
        context['ispopup']=('_popup' in self.request.GET)
        context['type']=self.request.GET.get('type',None)
        context['idx']=self.request.GET.get('idx',-1)
        context['action']='edit'
        return context


class CreateSSRView(EditSSRMixin, PermissionRequiredMixin, CreateView):
    permission_required='bodb.add_ssr'

    def get_object(self, queryset=None):
        return None

    def get_context_data(self, **kwargs):
        context = super(CreateSSRView,self).get_context_data(**kwargs)
        context=set_context_workspace(context, self.request)
        context['figure_formset']=DocumentFigureFormSet(self.request.POST or None, self.request.FILES or None,
            prefix='figure')
        context['ispopup']=('_popup' in self.request.GET)
        context['type']=self.request.GET.get('type',None)
        context['idx']=self.request.GET.get('idx',-1)
        context['action']='add'
        return context


class DeleteSSRView(ObjectRolePermissionRequiredMixin, DeleteView):
    model=SSR
    success_url = '/bodb/index.html'
    permission_required='delete'


class SSRAPIListView(DocumentAPIListView):
    serializer_class = SSRSerializer
    model = SSR

    def get_queryset(self):
        user = self.request.user
        security_q=Document.get_security_q(user)
        return SSR.objects.filter(security_q)


class SSRAPIDetailView(ObjectRolePermissionRequiredMixin, DocumentAPIDetailView):
    serializer_class = SSRSerializer
    model = SSR
    permission_required = 'view'


class SSRDetailView(ObjectRolePermissionRequiredMixin, DocumentDetailView):
    model = SSR
    template_name = 'bodb/ssr/ssr_view.html'
    serializer_class = SSRSerializer
    permission_required = 'view'

    def get_object(self, queryset=None):
        if not hasattr(self,'object'):
            self.object=get_object_or_404(SSR.objects.select_related('forum','collator','last_modified_by'),id=self.kwargs.get(self.pk_url_kwarg, None))
        return self.object

    def get_context_data(self, **kwargs):
        context = super(SSRDetailView, self).get_context_data(**kwargs)
        user=self.request.user
        context['helpPage']='view_entry.html'
        models=Model.objects.filter(Q(related_test_sed_document__ssr=self.object) | Q(prediction__ssr=self.object)).select_related('collator').prefetch_related('authors__author')
        context['model']=None
        if models.count():
            context['model']=models[0]
        if user.is_authenticated() and not user.is_anonymous():
            context['subscribed_to_collator']=UserSubscription.objects.filter(subscribed_to_user=self.object.collator,
                user=user, model_type='SSR').exists()
            context['subscribed_to_last_modified_by']=UserSubscription.objects.filter(subscribed_to_user=self.object.last_modified_by,
                user=user, model_type='SSR').exists()
            context['selected']=context['active_workspace'].related_ssrs.filter(id=self.object.id).exists()
        context['action']=self.request.GET.get('action',None)
        context['type']=self.request.GET.get('type',None)
        context['idx']=self.request.GET.get('idx',None)
        context['ispopup']=('_popup' in self.request.GET)
        return context


class ToggleSelectSSRView(LoginRequiredMixin, JSONResponseMixin,BaseUpdateView):
    model = SSR

    def get_context_data(self, **kwargs):
        context={'msg':u'No POST data sent.' }
        if self.request.is_ajax():
            ssr=SSR.objects.get(id=self.kwargs.get('pk', None))
            active_workspace=get_active_workspace(get_profile(self.request),self.request)

            context={
                'ssr_id': ssr.id,
                'workspace': active_workspace.title
            }
            activity=WorkspaceActivityItem(workspace=active_workspace, user=self.request.user)
            remove=False
            if 'select' in self.request.POST:
                remove=self.request.POST['select']=='false'
            else:
                remove=ssr in active_workspace.related_ssrs.all()
            if remove:
                active_workspace.related_ssrs.remove(ssr)
                context['selected']=False
                activity.text='%s removed the SSR: <a href="%s">%s</a> from the workspace' % (self.request.user.username, ssr.get_absolute_url(), ssr.__unicode__())
            else:
                active_workspace.related_ssrs.add(ssr)
                context['selected']=True
                activity.text='%s added the SSR: <a href="%s">%s</a> to the workspace' % (self.request.user.username, ssr.get_absolute_url(), ssr.__unicode__())
            activity.save()
            active_workspace.save()

        return context


class SSRTaggedView(BODBView):
    template_name='bodb/ssr/ssr_tagged.html'

    def get_context_data(self, **kwargs):
        context=super(SSRTaggedView,self).get_context_data(**kwargs)
        name = self.kwargs.get('name', None)
        user=self.request.user

        context['helpPage']='tags.html'
        context['tag']=name
        context['tagged_items']=SSR.get_ssr_list(SSR.get_tagged_ssrs(name, user), context['profile'], context['active_workspace'])
        return context