from django.db.models import Q
from django.shortcuts import redirect, render
from django.views.generic import UpdateView, DeleteView, View
from django.views.generic.edit import BaseUpdateView
from bodb.forms import DocumentFigureFormSet, SSRForm
from bodb.models import SSR, DocumentFigure, Model, WorkspaceActivityItem
from bodb.views.document import DocumentDetailView
from bodb.views.main import BODBView
from uscbp.views import JSONResponseMixin


class UpdateSSRView(UpdateView):
    model = SSR
    form_class = SSRForm
    template_name = 'bodb/ssr/ssr_detail.html'

    def get_context_data(self, **kwargs):
        context = super(UpdateSSRView,self).get_context_data(**kwargs)
        context['figure_formset']=DocumentFigureFormSet(self.request.POST or None, self.request.FILES or None,
            instance=self.object, queryset=DocumentFigure.objects.filter(document=self.object), prefix='figure')
        context['ispopup']=('_popup' in self.request.GET)
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        figure_formset = context['figure_formset']

        if figure_formset.is_valid():

            self.object = form.save()

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

            url=self.get_success_url()
            if context['ispopup']:
                url+='?_popup=1'
            return redirect(url)
        else:
            return self.render_to_response(self.get_context_data(form=form))


class DeleteSSRView(DeleteView):
    model=SSR
    success_url = '/bodb/index.html'


class SSRDetailView(DocumentDetailView):
    model = SSR
    template_name = 'bodb/ssr/ssr_view.html'

    def get_context_data(self, **kwargs):
        context = super(SSRDetailView, self).get_context_data(**kwargs)
        context['model']=Model.objects.filter(Q(testsed__testsedssr__ssr=self.object) | Q(prediction__predictionssr__ssr=self.object))[0]
        if self.request.user.is_authenticated() and not self.request.user.is_anonymous():
            context['selected']=self.request.user.get_profile().active_workspace.related_ssrs.filter(id=self.object.id).count()>0
        return context


class ToggleSelectSSRView(JSONResponseMixin,BaseUpdateView):
    model = SSR

    def get_context_data(self, **kwargs):
        context={'msg':u'No POST data sent.' }
        if self.request.is_ajax():
            ssr=SSR.objects.get(id=self.kwargs.get('pk', None))
            # Load active workspace
            active_workspace=self.request.user.get_profile().active_workspace

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

        context['helpPage']='BODB-Tags'
        context['tag']=name
        context['tagged_items']=SSR.get_ssr_list(SSR.get_tagged_ssrs(name, user),user)
        return context