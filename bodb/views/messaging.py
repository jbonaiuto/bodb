from django.core.mail import EmailMessage
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.views.generic import View, CreateView, UpdateView, DeleteView
from bodb.forms.messaging import MessageForm
from bodb.models import Message
from bodb.views.main import set_context_workspace
from guardian.mixins import LoginRequiredMixin

class UserMessageListView(LoginRequiredMixin,View):
    template_name = 'bodb/messaging/message_list.html'

    def get_context(self, request):
        context={}
        context['messages']=request.user.message_recipient_set.all().select_related('sender','recipient')
        context['sent']=request.user.message_sender_set.all().select_related('sender','recipient')
        context['helpPage']='messages.html'
        context['ispopup']=('_popup' in request.GET)
        context=set_context_workspace(context, self.request)
        return context

    def get(self, request, *args, **kwargs):
        context=self.get_context(request)
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        context=self.get_context(request)
        # for each selected message Id
        for msg_id in request.POST.getlist('message'):
            # load message
            msg=Message.objects.get(id=msg_id)
            # delete, mark read, or mark unread
            if request.POST['delete']=='1':
                msg.delete()
            elif request.POST['mark_read']=='1':
                msg.read=1
                msg.save()
            elif request.POST['mark_unread']=='1':
                msg.read=0
                msg.save()
        return render(request, self.template_name, context)


class CreateUserMessageView(LoginRequiredMixin,CreateView):
    model = Message
    form_class = MessageForm
    template_name = 'bodb/messaging/message_compose.html'

    def get_context_data(self, **kwargs):
        context = super(CreateUserMessageView,self).get_context_data(**kwargs)
        context=set_context_workspace(context, self.request)
        context['helpPage']='messages.html#composing-a-new-message'
        return context

    def get(self, request, *args, **kwargs):
        self.object=None
        message=Message(sender=request.user, read=False)
        form=MessageForm(request.user, instance=message)
        return self.render_to_response(self.get_context_data(form=form))

    def post(self, request, *args, **kwargs):
        self.object = None
        message=Message(sender=request.user, read=False)
        form=MessageForm(request.user, request.POST, instance=message)
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        message=form.save()

        # redirect to the message list page
        return HttpResponseRedirect('/bodb/messages/')


class ReadReplyUserMessageView(LoginRequiredMixin,UpdateView):
    model = Message
    form_class = MessageForm
    template_name = 'bodb/messaging/message_detail.html'

    def get_object(self, queryset=None):
        if not hasattr(self,'object'):
            self.object=get_object_or_404(Message.objects.select_related('sender','recipient'),id=self.kwargs.get(self.pk_url_kwarg, None))
        return self.object

    def get_context_data(self, **kwargs):
        context = super(ReadReplyUserMessageView,self).get_context_data(**kwargs)
        context=set_context_workspace(context, self.request)
        context['helpPage']='messages.html#viewing-messages'
        return context

    def get(self, request, *args, **kwargs):
        self.object=get_object_or_404(Message.objects.select_related('sender','recipient'), id=self.kwargs.get('pk', None))
        # if this user is the recipient, mark the message as read
        if self.request.user==self.object.recipient:
            self.object.read=1
            self.object.save()
        form=MessageForm(request.user, self.request.POST or None, instance=Message(sender=request.user, read=False))
        return self.render_to_response(self.get_context_data(form=form,message=self.object))

    def post(self, request, *args, **kwargs):
        self.object=get_object_or_404(Message.objects.select_related('sender','recipient'), id=self.kwargs.get('pk', None))
        form=MessageForm(request.user, request.POST, instance=Message(sender=request.user, read=False))
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        reply=form.save()

        return HttpResponseRedirect('/bodb/messages/')


class DeleteUserMessageView(LoginRequiredMixin,DeleteView):
    model=Message
    success_url='/bodb/messages/'

