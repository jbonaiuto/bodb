from django.views.generic.edit import BaseUpdateView
from bodb.forms.discussion import PostForm
from bodb.models import Forum
from uscbp.views import JSONResponseMixin

class ForumPostView(JSONResponseMixin,BaseUpdateView):
    model = Forum

    def get_context_data(self, **kwargs):
        context={'msg':u'No POST data sent.' }
        if self.request.is_ajax():
            form=PostForm(self.request.POST,prefix=self.request.POST['prefix'])
            if form.is_valid():
                post=form.save(commit=False)
                post.author=self.request.user
                post.save()
                context={
                    'post_id': post.id,
                    'avatar_url': '',
                    'username': post.author.username,
                    'posted': post.posted.strftime("%b %d, %Y, %I:%M %p"),
                    'body': post.body,
                    'form_prefix': self.request.POST['prefix'],
                    'parent_div': self.request.POST['parentDiv'],
                    'level': post.get_level(),
                    'margin': self.request.POST['margin']
                }
                if post.author.get_profile().avatar:
                    context['avatar_url']=post.author.get_profile().avatar.url,
                if post.parent is not None:
                    context['parent_id']=post.parent.id
            else:
                print(form.errors)
        return context
