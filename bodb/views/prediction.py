from django.db.models import Q
from django.shortcuts import redirect
from django.views.generic import UpdateView, DeleteView
from bodb.forms.ssr import PredictionForm
from bodb.models import Prediction, SSR, Document, UserSubscription, Model
from bodb.serializers import PredictionSerializer
from bodb.views.document import DocumentDetailView, DocumentAPIListView, DocumentAPIDetailView
from bodb.views.main import BODBView
from bodb.views.security import ObjectRolePermissionRequiredMixin

class PredictionAPIListView(DocumentAPIListView):
    serializer_class = PredictionSerializer
    model = Prediction

    def get_queryset(self):
        user = self.request.user
        security_q=Document.get_security_q(user)
        return Prediction.objects.filter(security_q)


class PredictionAPIDetailView(ObjectRolePermissionRequiredMixin,DocumentAPIDetailView):
    serializer_class = PredictionSerializer
    model = Prediction
    permission_required = 'view'


class UpdatePredictionView(ObjectRolePermissionRequiredMixin,UpdateView):
    model = Prediction
    form_class = PredictionForm
    template_name = 'bodb/prediction/prediction_detail.html'
    permission_required='edit'

    def get_context_data(self, **kwargs):
        context = super(UpdatePredictionView,self).get_context_data(**kwargs)
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

    def get_context_data(self, **kwargs):
        context = super(PredictionDetailView, self).get_context_data(**kwargs)
        context['helpPage']='view_entry.html'
        models=Model.objects.filter(Q(prediction=self.object))
        context['model']=None
        if models.count():
            context['model']=models[0]
        ssrs=[]
        if self.object.ssr:
            ssrs.append(self.object.ssr)
        context['ssrs']=SSR.get_ssr_list(ssrs,self.request.user)
        user=self.request.user
        if user.is_authenticated() and not user.is_anonymous():
            context['subscribed_to_collator']=UserSubscription.objects.filter(subscribed_to_user=self.object.collator,
                user=user, model_type='Prediction').count()>0
            context['subscribed_to_last_modified_by']=UserSubscription.objects.filter(subscribed_to_user=self.object.last_modified_by,
                user=user, model_type='Prediction').count()>0
        return context


class PredictionTaggedView(BODBView):
    template_name='bodb/prediction/prediction_tagged.html'

    def get_context_data(self, **kwargs):
        context=super(PredictionTaggedView,self).get_context_data(**kwargs)
        name = self.kwargs.get('name', None)
        user=self.request.user

        context['helpPage']='tags.html'
        context['tag']=name
        context['tagged_items']=Prediction.get_prediction_list(Prediction.get_tagged_predictions(name, user),user)
        return context