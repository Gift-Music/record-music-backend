from django.contrib.auth.models import (
    BaseUserManager, AbstractBaseUser, PermissionsMixin
)
from django.db import models # djongo 라이브러리의 model 폴더의 fields.py 1014번째 줄 부근에 있는 from_db_value()함수의 인자 context를 context=None으로 수정해야함.
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _


class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, userid, password, username=None):
        """
        주어진 이메일, 닉네임, 비밀번호 등 개인정보로 User 인스턴스 생성
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

    def create_superuser(self, email, userid, password, username=None):
        """
        주어진 이메일, 닉네임, 비밀번호 등 개인정보로 User 인스턴스 생성
        단, 최상위 사용자이므로 권한을 부여한다.
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


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(
        verbose_name=_('Email address'),
        max_length=255,
        unique=True,
    )
    userid = models.CharField( # 해당 유저의 닉네임
        verbose_name=_('User Id'),
        max_length=30,
        unique=True
    )
    username = models.CharField(  # 해당 유저의 한글이름
        verbose_name=_('Username'),
        max_length=100,
        unique=False,
    )
    is_active = models.BooleanField(
        verbose_name=_('Is active'),
        default=True
    )
    date_joined = models.DateTimeField(
        verbose_name=_('Date joined'),
        default=timezone.now
    )
    # followers = models.ArrayReferenceField(
    #     to="self",
    #     related_name="recordmusic_followers",
    # )
    #
    # following = models.ArrayReferenceField(
    #     to="self",
    #     related_name="recordmusic_following",
    # )

    profile_image = models.ImageField(
        null=True,
    )

    objects = UserManager()

    USERNAME_FIELD = 'userid'
    REQUIRED_FIELDS = ['email']

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        ordering = ('username',)

    def __str__(self):
        return self.userid

    def get_full_name(self):
        return self.username

    def get_short_name(self):
        return self.username

    def get_absolute_url(self):
        return reversed('users:detail', kwargs={'userid':self.userid})

    @property
    def is_staff(self):
        "Is the user a member of staff?"
        # Simplest possible answer: All superusers are staff
        return self.is_superuser

    # @property
    # def followers_count(self):
    #     return self.followers.all().count()
    #
    # @property
    # def following_count(self):
    #     return self.following.all().count()