from django.db import models
from django.contrib.auth.models import User, Permission, Group
from django.db.models.signals import post_save
from legacy.photologue.models import Gallery

class Workspace(models.Model):
    admin = models.ForeignKey(User)
    group = models.ForeignKey(Group)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    related_models = models.ManyToManyField('Model')
    related_bops = models.ManyToManyField('BOP')
    related_seds = models.ManyToManyField('SED')
    related_ssrs = models.ManyToManyField('SSR')
    created_date = models.DateTimeField(auto_now_add=True,blank=True)
    class Meta:
        app_label='legacy_bodb'

    # override Workspace.save()
    #   if this is the first save,
    #     1. automatically creates a group
    #     2. assigns user to new group
    def save(self, *args, **kwargs):

        # test if workspace already has a group assigned to it
        if (not hasattr(self, 'group')) or (self.group is None):

            # create new group name from title or username
            group_name=self.admin.username+'-'+self.title+'-group'
            group_count=Group.objects.filter(name__icontains=group_name).count()
            group_name='%s_%d' %  (group_name, group_count)
           
            # create new group
            workspace_group=Group(name=group_name)
            workspace_group.save()
            self.group=workspace_group

            # now add user to new group
            self.admin.groups.add(self.group)
 
        # Save workspace
        super(Workspace, self).save(*args, **kwargs)

    def get_admin_str(self):
        if self.admin.last_name:
            return '%s %s' % (self.admin.first_name, self.admin.last_name)
        else:
            return self.admin.username


# User profile
class BodbProfile(models.Model):
    TAG_DIST_CHOICES = (
        ('linear', 'linear'),
        ('log', 'log'),
    )
    NOTIFICATION_TYPE_CHOICES = (
        ('email', 'email'),
        ('message', 'message'),
        ('both', 'both'),
        )
    user = models.ForeignKey(User, unique=True)
    # gallery - first image is avatar
    gallery = models.ForeignKey(Gallery, related_name='user_gallery')
    # whether or not to email the user when new messages are received
    new_message_notify = models.BooleanField(default=True)
    # Tag cloud distribution
    tag_dist = models.CharField(default='linear', max_length=6)
    # User's active workspace
    active_workspace = models.ForeignKey(Workspace)
    # User's affiliation
    affiliation = models.CharField(max_length=200)
    # type of notification to use - email, internal BODB message, or both
    notification_preference = models.CharField(max_length=100, choices=NOTIFICATION_TYPE_CHOICES)

    class Meta:
        app_label='legacy_bodb'

    # returns url of user's avatar
    def get_avatar_url(self):
        if self.gallery.photos.all():
            return self.gallery.photos.all()[0].get_thumbnail_url()
        else:
            return ''

    # returns url of user's avatar icon
    def get_icon_url(self):
        if self.gallery.photos.all():
            return self.gallery.photos.all()[0].get_icon_url()
        else:
            return ''


class AllocatedUserAccount(models.Model):
    username = models.CharField(max_length=30, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    group = models.ForeignKey(Group)
    class Meta:
        app_label='legacy_bodb'


# create a new profile for the given user
def create_user_profile(user):

    # create a default workspace for the user
    default_workspace=Workspace(title='Default', admin=user)
    default_workspace.save()
     
    # create a gallery to contain the user's avatar
    gallery=Gallery(title=user.username,title_slug=user.username)
    gallery.save()

    # create a profile
    profile=BodbProfile(user=user, gallery=gallery, active_workspace=default_workspace)
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
#post_save.connect(user_post_save_handler, sender=User)
