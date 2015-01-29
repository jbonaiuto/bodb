import datetime
import hashlib
import random
from django.contrib.auth.models import Group, Permission
from django.contrib.sites.models import get_current_site
from django.core.mail import EmailMessage
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from bodb.models.discussion import Forum
from bodb.models.messaging import Message, UserSubscription
from bodb.signals import forum_post_added, document_changed, coord_selection_created, coord_selection_changed, coord_selection_deleted, bookmark_added, bookmark_deleted
from guardian.shortcuts import assign_perm
from registration.models import User

class Workspace(models.Model):
    created_by = models.ForeignKey(User)
    group = models.ForeignKey(Group)
    admin_users = models.ManyToManyField(User,related_name='workspace_admin')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    forum=models.ForeignKey('Forum')
    related_models = models.ManyToManyField('Model')
    related_bops = models.ManyToManyField('BOP')
    related_seds = models.ManyToManyField('SED')
    related_ssrs = models.ManyToManyField('SSR')
    related_literature = models.ManyToManyField('Literature')
    related_regions = models.ManyToManyField('BrainRegion')
    saved_coordinate_selections = models.ManyToManyField('SavedSEDCoordSelection')
    created_date = models.DateTimeField(auto_now_add=True,blank=True)

    class Meta:
        app_label='bodb'
        permissions=(
            ('add_post','Add discussion post'),
            ('add_entry','Add workspace entry'),
            ('remove_entry','Remove workspace entry'),
            ('add_coordinate_selection','Add coordinate selection'),
            ('change_coordinate_selection','Modify coordinate selection'),
            ('delete_coordinate_selection','Delete coordinate selection'),
            ('add_bookmark', 'Add bookmark'),
            ('delete_bookmark', 'Delete bookmark'),
            ('change_bookmark', 'Modify bookmark')
        )

    # override Workspace.save()
    #   if this is the first save,
    #     1. automatically creates a group
    #     2. assigns user to new group
    def save(self, *args, **kwargs):

        init_permissions=False
        # test if workspace exists
        if (not hasattr(self, 'id')) or (self.id is None):
            init_permissions=True

        # test if workspace already has a group assigned to it
        if (not hasattr(self, 'group')) or (self.group is None):

            # create new group name from title or username
            group_name=self.title+'-workspace group'
            if self.title=='Default':
                group_name='%s-%s' % (self.created_by.username,group_name)
            group_count=Group.objects.filter(name__icontains=group_name).count()
            if group_count>0:
                group_name='%s_%d' %  (group_name, group_count+1)

            # create new group
            workspace_group=Group(name=group_name)
            workspace_group.save()
            self.group=workspace_group

            # now add user to new group
            self.created_by.groups.add(self.group)

        # test if workspace already has a forum assigned to it
        if (not hasattr(self, 'forum')) or (self.forum is None):
            workspace_forum=Forum()
            workspace_forum.save()

            self.forum=workspace_forum

        # Save workspace
        super(Workspace, self).save(*args, **kwargs)

        if init_permissions:
            self.admin_users.add(self.created_by)
            for permission_code,permission_name in Workspace._meta.permissions:
                assign_perm(permission_code,self.created_by,self)

    def get_created_by_str(self):
        if self.created_by.last_name:
            return '%s %s' % (self.created_by.first_name, self.created_by.last_name)
        else:
            return self.created_by.username

    def get_users(self):
        return User.objects.filter(groups=self.group)

    def get_absolute_url(self):
        return reverse('workspace_view', kwargs={'pk': self.pk})

    def as_json(self):
        return {
            'id': self.id,
            'created_by_id': self.created_by.id,
            'created_by': self.get_created_by_str(),
            'title': self.title,
            'description': self.description
        }

    @staticmethod
    def get_workspace_list(workspaces, user):
        profile=None
        if user.is_authenticated() and not user.is_anonymous():
            profile=user.get_profile()
        workspace_list=[]
        for w in workspaces:
            subscribed_to_user=profile is not None and UserSubscription.objects.filter(subscribed_to_user=w.created_by, user=user).count()>0
            workspace_list.append([subscribed_to_user,w])
        return workspace_list

    def check_perm(self, user, perm):
        if perm=='admin':
            return self.admin_users.filter(id=user.id).count()>0
        elif perm=='member':
            return self.get_users().filter(id=user.id).count()>0 or user.is_superuser
        else:
            return user.has_perm(perm, self)


class WorkspaceInvitation(models.Model):
    STATUS_OPTIONS=(
        ('',''),
        ('accepted','accepted'),
        ('declined','declined')
    )
    workspace=models.ForeignKey('Workspace')
    invited_user=models.ForeignKey(User, related_name='invited_user')
    invited_by=models.ForeignKey(User, related_name='invited_by')
    invitation_body=models.CharField(max_length=1000, blank=False)
    status=models.CharField(max_length=20, choices=STATUS_OPTIONS, blank=True)
    activation_key = models.CharField('activation key', max_length=40)
    sent=models.DateTimeField(auto_now=True, blank=True)

    class Meta:
        app_label='bodb'

    def send(self):
        # message subject
        subject = 'Invitation to join a BODB Workspace'
        # message text
        text = 'You\'ve been invited by %s to join the BODB workspace: %s.<br>' % (
        self.invited_by, self.workspace.title)
        text += self.invitation_body
        text += '<br>Click one of the following links to accept or decline the invitation:<br>'
        accept_url = ''.join(
            ['http://', get_current_site(None).domain, '/bodb/workspace_invite/accept/%s/' % self.activation_key])
        decline_url = ''.join(
            ['http://', get_current_site(None).domain, '/bodb/workspace_invite/decline/%s/' % self.activation_key])
        text += '<a href="%s">Accept</a><br>' % accept_url
        text += 'or<br>'
        text += '<a href="%s">Decline</a>' % decline_url
        self.sent=datetime.datetime.now()
        # send internal message
        profile=BodbProfile.objects.get(user__id=self.invited_user.id)
        notification_type = profile.notification_preference
        if notification_type == 'message' or notification_type == 'both':
            message = Message(recipient=self.invited_user, subject=subject, read=False)
            message.text = text
            message.save()

        # send email message
        if notification_type == 'email' or notification_type == 'both':
            msg = EmailMessage(subject, text, 'uscbrainproject@gmail.com', [self.invited_user.email])
            msg.content_subtype = "html"  # Main content is now text/html
            msg.send(fail_silently=True)

    def save(self, **kwargs):
        if self.id is None:
            salt = hashlib.sha1(str(random.random())).hexdigest()[:5]
            username = self.invited_user.username
            if isinstance(username, unicode):
                username = username.encode('utf-8')
            self.activation_key = hashlib.sha1(salt+username).hexdigest()

            self.send()
        super(WorkspaceInvitation,self).save(**kwargs)


class WorkspaceBookmark(models.Model):
    workspace=models.ForeignKey(Workspace)
    url = models.CharField(max_length=200)
    # bookmark title
    title = models.CharField(max_length=200)
    # description of the bookmark
    description=models.TextField(blank=True)
    # user who created the bookmark
    collator=models.ForeignKey(User,null=True)
    # date and time this entry was created
    creation_time = models.DateTimeField(auto_now_add=True,blank=True)
    # date and time this entry as last modified
    last_modified_time = models.DateTimeField(auto_now=True,blank=True)
    # user who last modified the entry
    last_modified_by = models.ForeignKey(User,null=True,blank=True,related_name='bookmark_last_modified_by')
    class Meta:
        app_label='bodb'

    def save(self, **kwargs):
        if self.id is None:
            bookmark_added.send(sender=self)
        super(WorkspaceBookmark,self).save(**kwargs)

    def delete(self, using=None):
        bookmark_deleted.send(sender=self)
        super(WorkspaceBookmark,self).delete(using=using)


class WorkspaceActivityItem(models.Model):
    workspace=models.ForeignKey(Workspace)
    user=models.ForeignKey(User)
    time=models.DateTimeField(auto_now_add=True, blank=True)
    text=models.TextField()
    class Meta:
        app_label='bodb'


@receiver(forum_post_added)
def workspace_forum_post_added(sender, **kwargs):
    if Workspace.objects.filter(forum=sender.forum):
        workspace=Workspace.objects.get(forum=sender.forum)
        activity=WorkspaceActivityItem(workspace=workspace, user=sender.author)
        activity.text='%s added a comment to the workspace: %s' % (sender.author.username, sender.body)
        activity.save()
    for workspace in Workspace.objects.filter(related_models__forum=sender.forum):
        for model in workspace.related_models.filter(forum=sender.forum):
            activity=WorkspaceActivityItem(workspace=workspace, user=sender.author)
            activity.text='%s added a comment to the model <a href="%s">%s</a>: %s' % (sender.author.username,model.get_absolute_url(), model.__unicode__(), sender.body)
            activity.save()
    for workspace in Workspace.objects.filter(related_bops__forum=sender.forum):
        for bop in workspace.related_bops.filter(forum=sender.forum):
            activity=WorkspaceActivityItem(workspace=workspace, user=sender.author)
            activity.text='%s added a comment to the BOP <a href="%s">%s</a>: %s' % (sender.author.username, bop.get_absolute_url(), bop.__unicode__(), sender.body)
            activity.save()
    for workspace in Workspace.objects.filter(related_seds__forum=sender.forum):
        for sed in workspace.related_seds.filter(forum=sender.forum):
            activity=WorkspaceActivityItem(workspace=workspace, user=sender.author)
            activity.text='%s added a comment to the SED <a href="%s">%s</a>: %s' % (sender.author.username, sed.get_absolute_url(), sed.__unicode__(), sender.body)
            activity.save()
    for workspace in Workspace.objects.filter(related_ssrs__forum=sender.forum):
        for ssr in workspace.related_ssrs.filter(forum=sender.forum):
            activity=WorkspaceActivityItem(workspace=workspace, user=sender.author)
            activity.text='%s added a comment to the SSR <a href="%s">%s</a>: %s' % (sender.author.username, ssr.get_absolute_url(), ssr.__unicode__(), sender.body)
            activity.save()


@receiver(document_changed)
def workspace_document_changed(sender, **kwargs):
    for workspace in Workspace.objects.filter(related_models=sender):
        activity=WorkspaceActivityItem(workspace=workspace, user=sender.last_modified_by)
        activity.text='%s modified the model <a href="%s">%s</a>' % (sender.last_modified_by.username,sender.get_absolute_url(), sender.__unicode__())
        activity.save()

    for workspace in Workspace.objects.filter(related_bops=sender):
        activity=WorkspaceActivityItem(workspace=workspace, user=sender.last_modified_by)
        activity.text='%s modified the BOP <a href="%s">%s</a>' % (sender.last_modified_by.username,sender.get_absolute_url(), sender.__unicode__())
        activity.save()

    for workspace in Workspace.objects.filter(related_seds=sender):
        activity=WorkspaceActivityItem(workspace=workspace, user=sender.last_modified_by)
        activity.text='%s modified the SED <a href="%s">%s</a>' % (sender.last_modified_by.username,sender.get_absolute_url(), sender.__unicode__())
        activity.save()

    for workspace in Workspace.objects.filter(related_ssrs=sender):
        activity=WorkspaceActivityItem(workspace=workspace, user=sender.last_modified_by)
        activity.text='%s modified the SSR <a href="%s">%s</a>' % (sender.last_modified_by.username,sender.get_absolute_url(), sender.__unicode__())
        activity.save()


@receiver(coord_selection_created)
def workspace_coord_selection_created(sender, **kwargs):
    for workspace in Workspace.objects.filter(saved_coordinate_selections=sender):
        activity=WorkspaceActivityItem(workspace=workspace, user=sender.user)
        activity.text='%s added the coordinate selection: %s' % (sender.user.username, sender.name)
        activity.save()


@receiver(coord_selection_changed)
def workspace_coord_selection_changed(sender, **kwargs):
    for workspace in Workspace.objects.filter(saved_coordinate_selections=sender):
        activity=WorkspaceActivityItem(workspace=workspace, user=sender.last_modified_by)
        activity.text='%s modified the coordinate selection: %s' % (sender.last_modified_by.username, sender.name)
        activity.save()


@receiver(coord_selection_deleted)
def workspace_coord_selection_deleted(sender, **kwargs):
    for workspace in Workspace.objects.filter(saved_coordinate_selections=sender):
        activity=WorkspaceActivityItem(workspace=workspace, user=sender.user)
        activity.text='%s deleted the coordinate selection: %s' % (sender.user.username, sender.name)
        activity.save()


@receiver(bookmark_added)
def workspace_bookmark_added(sender, **kwargs):
    activity=WorkspaceActivityItem(workspace=sender.workspace, user=sender.collator)
    activity.text='%s added a bookmark: <a href="%s">%s</a>' % (sender.collator.username, sender.url, sender.title)
    activity.save()


@receiver(bookmark_deleted)
def workspace_bookmark_deleted(sender, **kwargs):
    activity=WorkspaceActivityItem(workspace=sender.workspace, user=sender.last_modified_by)
    activity.text='%s deleted the bookmark: <a href="%s">%s</a>' % (sender.last_modified_by.username, sender.url,
                                                                     sender.title)
    activity.save()

class AllocatedUserAccount(models.Model):
    username = models.CharField(max_length=30, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    group = models.ForeignKey(Group)
    class Meta:
        app_label='bodb'


class BodbProfile(models.Model):
    NOTIFICATION_TYPE_CHOICES = (
        ('email', 'email'),
        ('message', 'message'),
        ('both', 'both'),
        )
    user = models.ForeignKey(User, unique=True)
    # gallery - first image is avatar
    avatar=models.ImageField(upload_to='avatars', blank=True, null=True)
    # whether or not to email the user when new messages are received
    new_message_notify = models.BooleanField(default=True)
    # User's active workspace
    active_workspace = models.ForeignKey(Workspace,null=True)
    # User's loaded coordinate selection
    loaded_coordinate_selection=models.ForeignKey('SavedSEDCoordSelection',null=True)
    # User's affiliation
    affiliation = models.CharField(max_length=200)
    # type of notification to use - email, internal BODB message, or both
    notification_preference = models.CharField(max_length=100, choices=NOTIFICATION_TYPE_CHOICES, default='both')
    # favorite entries
    favorites = models.ManyToManyField('Document')
    favorite_literature = models.ManyToManyField('Literature')
    favorite_regions = models.ManyToManyField('BrainRegion')
    class Meta:
        app_label='bodb'

    @staticmethod
    def get_user_list(users, user):
        profile=None
        if user.is_authenticated() and not user.is_anonymous():
            profile=user.get_profile()
        user_list=[]
        for u in users:
            subscribed_to_user=profile is not None and UserSubscription.objects.filter(subscribed_to_user=u, user=user).count()>0
            user_list.append([subscribed_to_user,u])
        return user_list

    @staticmethod
    def as_json(user):
        return {
            'id': user.id,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email
        }

# create a new profile for the given user
def create_user_profile(user):

    # create a default workspace for the user
    default_workspace=Workspace(title='Default', created_by=user)
    default_workspace.save()

    # create a profile
    profile=BodbProfile(user=user, active_workspace=default_workspace)
    profile.save()

    # check if this user is already allocated to a group
    allocatedAccount=None
    if AllocatedUserAccount.objects.filter(username=user.username):
        allocatedAccount=AllocatedUserAccount.objects.get(username=user.username)
    elif AllocatedUserAccount.objects.filter(email=user.email):
        allocatedAccount=AllocatedUserAccount.objects.get(email=user.email)

    if allocatedAccount is not None:
        user.groups.add(allocatedAccount.group)

    # initialize the default permissions
    #    skip the user if it a superuser
    #    skip setting permissions if occurs during 'syncdb' bootstrapping
    #        (by testing for the 'add_literature' permission)
    if not user.is_superuser and Permission.objects.filter(codename='add_literature'):
        user.user_permissions.add(Permission.objects.get(codename='add_literature'))
        user.user_permissions.add(Permission.objects.get(codename='change_literature'))
        user.user_permissions.add(Permission.objects.get(codename='delete_literature'))
        user.user_permissions.add(Permission.objects.get(codename='add_model'))
        user.user_permissions.add(Permission.objects.get(codename='change_model'))
        user.user_permissions.add(Permission.objects.get(codename='delete_model'))
        user.user_permissions.add(Permission.objects.get(codename='add_module'))
        user.user_permissions.add(Permission.objects.get(codename='change_module'))
        user.user_permissions.add(Permission.objects.get(codename='delete_module'))
        user.user_permissions.add(Permission.objects.get(codename='add_bop'))
        user.user_permissions.add(Permission.objects.get(codename='change_bop'))
        user.user_permissions.add(Permission.objects.get(codename='delete_bop'))
        user.user_permissions.add(Permission.objects.get(codename='add_sed'))
        user.user_permissions.add(Permission.objects.get(codename='change_sed'))
        user.user_permissions.add(Permission.objects.get(codename='delete_sed'))
        user.user_permissions.add(Permission.objects.get(codename='add_ssr'))
        user.user_permissions.add(Permission.objects.get(codename='change_ssr'))
        user.user_permissions.add(Permission.objects.get(codename='delete_ssr'))
        user.user_permissions.add(Permission.objects.get(codename='add_prediction'))
        user.user_permissions.add(Permission.objects.get(codename='change_prediction'))
        user.user_permissions.add(Permission.objects.get(codename='delete_prediction'))

    user.save()

    if allocatedAccount is not None:
        allocatedAccount.delete()


def parse_class_list(in_filename, out_filename, group_id):
    in_file=open(in_filename,'r')
    out_file=open(out_filename,'w')

    for line in in_file:
        line_parts=line.rstrip().split(',')
        user_name=line_parts[0]
        email=line_parts[1]
        sql='''
            INSERT INTO
                uscbp.bodb_allocateduseraccount(username, email, group_id)
            VALUES ('%s', '%s', %d);
            ''' % (user_name,email,group_id)
        out_file.write('%s\n' % sql)
    in_file.close()
    out_file.close()


# A signal handler for the User.post_save event.
def user_post_save_handler(sender, instance, created, **kwargs):
    if created:
        create_user_profile(user=instance)


# Register the User.post_save signal handler
post_save.connect(user_post_save_handler, sender=User)