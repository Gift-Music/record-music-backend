from django.contrib.auth.models import (
    BaseUserManager, AbstractBaseUser, PermissionsMixin, Permission, _user_get_permissions, _user_has_perm,
    _user_has_module_perms
)
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _


class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, userid, password, username):
        """
        Create a User instance with personal information such as email, nickname, Korean name, and password given
        """
        if not email:
            raise ValueError(_('Users must have an email address'))

        user = self.model(
            email=self.normalize_email(email),
            userid=userid,
            username=username,
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, userid, password, username):
        """
        Create a SuperUser instance with personal information such as email, nickname, Korean name, and password given
        Grant superuser privileges after account creation.
        """
        user = self.create_user(
            email=self.normalize_email(email),
            userid=userid,
            username=username,
            password=password,
        )

        user.is_superuser = True
        user.save(using=self._db)
        return user

    def get_by_natural_key(self, userid):
        return self.get(**{self.model.USERNAME_FIELD: userid})


class CustomPermissionsMixin(models.Model):
    is_superuser = models.BooleanField(
        _('superuser status'),
        default=False,
        help_text=_(
            'Designates that this user has all permissions without '
            'explicitly assigning them.'
        ),
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name=_('user permissions'),
        blank=True,
        help_text=_('Specific permissions for this user.'),
        related_name="user_set",
        related_query_name="user",
    )

    class Meta:
        abstract = True

    def get_user_permissions(self, obj=None):
        """
        Return a list of permission strings that this user has directly.
        Query all available auth backends. If an object is passed in,
        return only permissions matching this object.
        """
        return _user_get_permissions(self, obj, 'user')

    def has_perm(self, perm, obj=None):
        """
        Return True if the user has the specified permission. Query all
        available auth backends, but return immediately if any backend returns
        True. Thus, a user who has permission from a single auth backend is
        assumed to have permission in general. If an object is provided, check
        permissions for that object.
        """
        # Active superusers have all permissions.
        if self.is_active and self.is_superuser:
            return True

        # Otherwise we need to check the backends.
        return _user_has_perm(self, perm, obj)

    def has_perms(self, perm_list, obj=None):
        """
        Return True if the user has each of the specified permissions. If
        object is passed, check if the user has all required perms for it.
        """
        return all(self.has_perm(perm, obj) for perm in perm_list)

    def has_module_perms(self, app_label):
        """
        Return True if the user has any permissions in the given app label.
        Use similar logic as has_perm(), above.
        """
        # Active superusers have all permissions.
        if self.is_active and self.is_superuser:
            return True

        return _user_has_module_perms(self, app_label)


class User(AbstractBaseUser, CustomPermissionsMixin):
    email = models.EmailField(
        verbose_name=_('Email address'),
        max_length=255,
        unique=True,
    )
    userid = models.CharField( # 해당 유저의 닉네임
        verbose_name=_('User Id'),
        max_length=150,
        unique=True
    )
    username = models.CharField(  # 해당 유저의 한글이름
        verbose_name=_('Username'),
        max_length=100,
        unique=False,
        null=True,
    )
    is_active = models.BooleanField(
        verbose_name=_('Is active'),
        default=True
    )
    date_joined = models.DateTimeField(
        verbose_name=_('Date joined'),
        default=timezone.now
    )
    followers = models.ManyToManyField(
        "self",
        blank=True,
        symmetrical=False,
        related_name="recordmusic_followers"
    )

    following = models.ManyToManyField(
        "self",
        blank=True,
        symmetrical=False,
        related_name="recordmusic_following"
    )
    profile_image = models.ImageField(
        null=True
    )

    objects = UserManager()

    USERNAME_FIELD = 'userid'
    EMAIL_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'email']

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        ordering = ('username',)

    def __str__(self):
        return self.userid

    def get_name(self):
        return self.username

    def get_user_id(self):
        return self.userid

    def get_absolute_url(self):
        return reversed('users:detail', kwargs={'userid':self.userid})

    @property
    def is_staff(self):
        "Is the user a member of staff?"
        # Simplest possible answer: All superusers are staff
        return self.is_superuser

    @property
    def followers_count(self):
        return self.followers.all().count()

    @property
    def following_count(self):
        return self.following.all().count()

