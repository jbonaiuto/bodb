from django.db.models import Q
from django.shortcuts import redirect, get_object_or_404
from django.views.generic import UpdateView, DeleteView, TemplateView
from bodb.forms.ssr import PredictionForm
from bodb.models import Prediction, SSR, Document, UserSubscription, Model
from bodb.views.document import DocumentDetailView, DocumentAPIListView, DocumentAPIDetailView
from bodb.views.main import BODBView, set_context_workspace
from bodb.views.security import ObjectRolePermissionRequiredMixin

class UpdatePredictionView(ObjectRolePermissionRequiredMixin,UpdateView):
    model = Prediction
    form_class = PredictionForm
    template_name = 'bodb/prediction/prediction_detail.html'
    permission_required='edit'

    def get_object(self, queryset=None):
        if not hasattr(self,'object'):
            self.object=get_object_or_404(Prediction.objects.select_related('collator','ssr__collator'),id=self.kwargs.get(self.pk_url_kwarg, None))
        return self.object

    def get_context_data(self, **kwargs):
        context = super(UpdatePredictionView,self).get_context_data(**kwargs)
        context=set_context_workspace(context, self.request)
        context['ssrs']=[self.object.ssr]
        context['ispopup']=('_popup' in self.request.GET)
        return context

    def form_valid(self, form):
        context = self.get_context_data()

        self.object = form.save(commit=False)
        # Set the collator if this is a new BOP
        if self.object.id is None:
            self.object.collator=self.request.user
        self.object.last_modified_by=self.request.user
        self.object.save()
        form.save_m2m()

        url=self.get_success_url()
        if context['ispopup']:
            url+='?_popup=1'
        return redirect(url)


class DeletePredictionView(ObjectRolePermissionRequiredMixin, DeleteView):
    model=Prediction
    success_url = '/bodb/index.html'
    permission_required = 'delete'


class PredictionDetailView(ObjectRolePermissionRequiredMixin, DocumentDetailView):
    model = Prediction
    template_name = 'bodb/prediction/prediction_view.html'
    permission_required = 'view'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

    def get_object(self, queryset=None):
        if not hasattr(self,'object'):
            self.object=get_object_or_404(Prediction.objects.select_related('forum','collator','last_modified_by','ssr__collator'),id=self.kwargs.get(self.pk_url_kwarg, None))
        return self.object

    def get_context_data(self, **kwargs):
        context = super(PredictionDetailView, self).get_context_data(**kwargs)
        context['helpPage']='view_entry.html'
        models=Model.objects.filter(Q(prediction=self.object)).select_related('collator').prefetch_related('authors__author')
        context['model']=None
        if models.exists():
            context['model']=models[0]
        ssrs=[]
        if self.object.ssr:
            ssrs.append(self.object.ssr)
        context['ssrs']=SSR.get_ssr_list(ssrs, context['workspace_ssrs'], context['fav_docs'], context['subscriptions'])
        context['subscribed_to_collator']=(self.object.collator.id, 'Prediction') in context['subscriptions']
        context['subscribed_to_last_modified_by']=(self.object.last_modified_by.id, 'Prediction') in \
                                                  context['subscriptions']
        return context


class PredictionTaggedView(BODBView):
    template_name='bodb/prediction/prediction_tagged.html'

    def get_context_data(self, **kwargs):
        context=super(PredictionTaggedView,self).get_context_data(**kwargs)
        name = self.kwargs.get('name', None)
        user=self.request.user

        context['helpPage']='tags.html'
        context['tag']=name
        predictions=Prediction.get_tagged_predictions(name, user)
        context['tagged_items']=Prediction.get_prediction_list(predictions, context['workspace_ssrs'],
            context['fav_docs'], context['subscriptions'])
        return context