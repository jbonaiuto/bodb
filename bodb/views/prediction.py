from django.shortcuts import redirect
from django.views.generic import UpdateView, DeleteView
from bodb.forms.ssr import PredictionSSRFormSet, PredictionForm
from bodb.models import Prediction, SSR, PredictionSSR, Document, UserSubscription
from bodb.serializers import PredictionSerializer
from bodb.views.document import DocumentDetailView, DocumentAPIListView, DocumentAPIDetailView
from bodb.views.main import BODBView

class PredictionAPIListView(DocumentAPIListView):
    queryset = Prediction.objects.all()
    serializer_class = PredictionSerializer
    model = Prediction

    def get_queryset(self):
        user = self.request.user
        security_q=Document.get_security_q(user)
        return Prediction.objects.filter(security_q)

class PredictionAPIDetailView(DocumentAPIDetailView):
    queryset = Prediction.objects.all()
    serializer_class = PredictionSerializer
    model = Prediction

class UpdatePredictionView(UpdateView):
    model = Prediction
    form_class = PredictionForm
    template_name = 'bodb/prediction/prediction_detail.html'

    def get_context_data(self, **kwargs):
        context = super(UpdatePredictionView,self).get_context_data(**kwargs)
        context['predictionssr_formset']=PredictionSSRFormSet(self.request.POST or None, instance=self.object,
            queryset=PredictionSSR.objects.filter(prediction=self.object), prefix='predictionssr')
        context['ispopup']=('_popup' in self.request.GET)
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        predictionssr_formset = context['predictionssr_formset']

        if predictionssr_formset.is_valid():

            self.object = form.save(commit=False)
            # Set the collator if this is a new BOP
            if self.object.id is None:
                self.object.collator=self.request.user
            self.object.last_modified_by=self.request.user
            self.object.save()
            form.save_m2m()

            # save SSRs
            for predictionssr_form in predictionssr_formset.forms:
                if not predictionssr_form in predictionssr_formset.deleted_forms:
                    predictionssr=predictionssr_form.save(commit=False)
                    predictionssr.prediction=self.object
                    ssr=SSR(title=predictionssr_form.cleaned_data['ssr_title'],
                        brief_description=predictionssr_form.cleaned_data['ssr_brief_description'])
                    # Update ssr if editing existing one
                    if 'ssr' in predictionssr_form.cleaned_data and\
                       predictionssr_form.cleaned_data['ssr'] is not None:
                        ssr=predictionssr_form.cleaned_data['ssr']
                        ssr.title=predictionssr_form.cleaned_data['ssr_title']
                        ssr.brief_description=predictionssr_form.cleaned_data['ssr_brief_description']
                    # Set collator if this is a new SSR
                    else:
                        ssr.collator=self.object.collator
                    ssr.last_modified_by=self.request.user
                    ssr.draft=self.object.draft
                    ssr.public=self.object.public
                    ssr.save()
                    predictionssr.ssr=ssr
                    predictionssr.save()

            # remove prediction SSRs
            for predictionssr_form in predictionssr_formset.deleted_forms:
                if predictionssr_form.instance.id:
                    predictionssr_form.instance.delete()

            url=self.get_success_url()
            if context['ispopup']:
                url+='?_popup=1'
            return redirect(url)
        else:
            return self.render_to_response(self.get_context_data(form=form))


class DeletePredictionView(DeleteView):
    model=Prediction
    success_url = '/bodb/index.html'


class PredictionDetailView(DocumentDetailView):
    model = Prediction
    template_name = 'bodb/prediction/prediction_view.html'

    def get_context_data(self, **kwargs):
        context = super(PredictionDetailView, self).get_context_data(**kwargs)
        context['helpPage']='view_entry.html'
        user=self.request.user
        context['ssrs']=SSR.get_ssr_list(Prediction.get_ssrs(self.object, user), user)
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