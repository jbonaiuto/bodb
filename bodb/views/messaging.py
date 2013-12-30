from django.core.mail import EmailMessage
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.views.generic import View, CreateView, UpdateView, DeleteView
from bodb.forms import MessageForm
from bodb.models import Message
from bodb.views.main import BODBView

class UserMessageListView(BODBView):
    template_name = 'bodb/messaging/message_list.html'

    def get_context_data(self, **kwargs):
        context=super(UserMessageListView,self).get_context_data(**kwargs)
        context['messages']=self.request.user.message_recipient_set.all()
        context['sent']=self.request.user.message_sender_set.all()
        context['helpPage']='BODB-Messaging'
        context['ispopup']=('_popup' in request.GET)
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


class CreateUserMessageView(CreateView):
    model = Message
    form_class = MessageForm
    template_name = 'bodb/messaging/message_compose.html'

    def get_context_data(self, **kwargs):
        context = super(CreateUserMessageView,self).get_context_data(**kwargs)
        context['helpPage']='BODB-Messaging'
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

        if message.recipient.get_profile().new_message_notify:
            # send email to recipient
            subject='You have a new message on BODB from '+self.request.user.username
            text='You have a new message from '+self.request.user.username+'.<br> <a href="'+self.request.build_absolute_uri('/bodb/message/'+str(message.id)+'/')+'">View message</a>'
            msg = EmailMessage(subject, text, 'uscbrainproject@gmail.com', [message.recipient.email])
            msg.content_subtype = "html"  # Main content is now text/html
            msg.send(fail_silently=True)

            # redirect to the message list page
        return HttpResponseRedirect('/bodb/messages/')


class ReadReplyUserMessageView(UpdateView):
    model = Message
    form_class = MessageForm
    template_name = 'bodb/messaging/message_detail.html'

    def get_context_data(self, **kwargs):
        context = super(ReadReplyUserMessageView,self).get_context_data(**kwargs)
        context['helpPage']='BODB-Messaging'
        return context

    def get(self, request, *args, **kwargs):
        self.object=get_object_or_404(Message, id=self.kwargs.get('pk', None))
        # if this user is the recipient, mark the message as read
        if self.request.user==self.object.recipient:
            self.object.read=1
            self.object.save()
        form=MessageForm(request.user, self.request.POST or None, instance=Message(sender=request.user, read=False))
        return self.render_to_response(self.get_context_data(form=form,message=self.object))

    def post(self, request, *args, **kwargs):
        self.object=get_object_or_404(Message, id=self.kwargs.get('pk', None))
        form=MessageForm(request.user, request.POST, instance=Message(sender=request.user, read=False))
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        reply=form.save()

        if reply.recipient.get_profile().new_message_notify:
            # send email to recipient
            subject='You have a new message on BODB from '+self.request.user.username
            text='You have a new message from '+self.request.user.username+'.<br> <a href="'+self.request.build_absolute_uri('/bodb/message/'+str(reply.id)+'/')+'">View message</a>'
            msg = EmailMessage(subject, text, 'uscbrainproject@gmail.com', [reply.recipient.email])
            msg.content_subtype = "html"  # Main content is now text/html
            msg.send(fail_silently=True)
        return HttpResponseRedirect('/bodb/messages/')


class DeleteUserMessageView(DeleteView):
    model=Message
    success_url='/bodb/messages/'

