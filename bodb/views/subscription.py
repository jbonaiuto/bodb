from django.shortcuts import redirect
from django.views.generic import CreateView
from bodb.forms import SubscriptionForm, UserSubscriptionForm
from bodb.models import Subscription, UserSubscription
from registration.models import User

class CreateSubscriptionView(CreateView):
    model=Subscription
    form_class = SubscriptionForm
    template_name = 'bodb/admin/subscription_detail.html'

    def get_context_data(self, **kwargs):
        context = super(CreateSubscriptionView,self).get_context_data(**kwargs)
        context['ispopup']=('_popup' in self.request.GET)
        context['model_type']=self.request.GET.get('type','All')
        context['keywords']=self.request.GET.get('keywords','')
        return context

    def get_initial(self):
        context=self.get_context_data()
        return {
            'model_type':context['model_type'],
            'keywords':context['keywords']
        }

    def form_valid(self, form):
        self.object=form.save(commit=False)
        self.object.user=self.request.user
        self.object.save()

        return redirect('/bodb/index.html')


class CreateUserSubscriptionView(CreateView):
    model=UserSubscription
    form_class = UserSubscriptionForm
    template_name = 'bodb/admin/user_subscription_detail.html'

    def get_context_data(self, **kwargs):
        context = super(CreateUserSubscriptionView,self).get_context_data(**kwargs)
        context['ispopup']=('_popup' in self.request.GET)
        context['model_type']=self.request.GET.get('type','All')
        context['user_id']=self.request.GET.get('user',None)
        context['subscribed_to_user']=User.objects.get(id=context['user_id']).username
        return context

    def get_initial(self):
        context=self.get_context_data()
        return {
            'model_type':context['model_type'],
            'subscribed_to_user':context['user_id']
        }

    def form_valid(self, form):
        self.object=form.save(commit=False)
        self.object.user=self.request.user
        self.object.save()

        return redirect('/bodb/index.html')


