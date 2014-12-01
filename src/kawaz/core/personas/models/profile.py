import os
from django.conf import settings
from django.dispatch import receiver
from django.db import models
from django.db.models.signals import post_save
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import pgettext_lazy
from .persona import Persona


class ProfileManager(models.Manager):
    def active(self):
        """
        アクティブなユーザーのみを含むプロフィールのQuerySetを返す
        """
        return self.filter(user__is_active=True)

    def published(self, user):
        """
        指定されたユーザーが閲覧可能なProfileを含むQuerySetを返す
        """
        qs = self.active()
        if user.is_authenticated() and user.role not in 'wille':
            # ログインユーザーかつWilleではない場合はすべて閲覧可能
            return qs
        # 公開プロフィールのみを返す
        return qs.filter(pub_state='public')


class Profile(models.Model):
    """
    ユーザーのプロフィール（補完情報）モデル
    """

    # Profileは下書き状態がないため重複しているが独自に定義している
    PUB_STATES = (
        ('public',      _("Public")),
        ('protected',   _("Internal")),
    )

    # 必須設定
    pub_state = models.CharField(_("Publish status"), max_length=10,
                                 choices=PUB_STATES, default="public")
    # オプション設定
    birthday = models.DateField(_('Birthday'), null=True, blank=True)
    place = models.CharField(_('Address'), max_length=255, blank=True)
    url = models.URLField(_("URL"), max_length=255, blank=True)
    remarks = models.TextField(pgettext_lazy("Profile", "Remarks"))
    skills = models.ManyToManyField('Skill', verbose_name=_('Skills'),
                                    related_name='users',
                                    null=True, blank=True)
    # Note:
    #   ProfileにはView権限が存在しているため{{ user.profile.birthday }}など
    #   テンプレート側から間違えてアクセスし秘密情報を露呈してしまうのを防ぐ
    #   ためにPersona.profileでは無くPersona._profileとして逆リファレンスを
    #   張っている。
    #   このためProfileのビュー以外からProfileにアクセスする必要がある場合
    #   （例: PersonaDetailView）は別に'profile'というContextを渡しView側
    #   で権限のチェックを行うようにする
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, verbose_name=_('User'),
        related_name='_profile', unique=True,
        primary_key=True, editable=False)
    created_at = models.DateTimeField(_('Created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated at'), auto_now=True)

    objects = ProfileManager()

    class Meta:
        ordering = ('user__nickname',)
        verbose_name = _("Profile")
        verbose_name_plural = _("Profiles")
        permissions = (
            ('view_profile', 'Can view the profile'),
        )

    def __str__(self):
        return self.user.nickname

    def get_absolute_url(self):
        # テンプレートなどで間違えて使用されていた場合を考え
        # メソッド自体は残し例外を投げる
        raise Exception(
            'Profile.get_absolute_url is obsolete. '
            'Use Persona.get_absolute_url instead. '
            'e.g. user.profile.get_absolute_url => '
            'user.get_absolute_url'
        )


class Skill(models.Model):
    """ユーザーが「何ができるか？」を表すモデル"""
    label = models.CharField(_('Label'), unique=True, max_length=32)
    description = models.CharField(_('Description'), max_length=128)
    order = models.IntegerField(_("Order"), default=0)

    def __str__(self):
        return self.label

    class Meta:
        ordering = ('order', 'pk',)
        verbose_name = _("Skill")
        verbose_name_plural = _("Skills")


class Service(models.Model):
    """外部サービスを表すモデル"""

    def _get_upload_path(self, filename):
        return os.path.join('personas', 'services', filename)

    label = models.CharField(_('Label'), max_length=64, unique=True)
    icon = models.ImageField(_('Icon'), upload_to=_get_upload_path)
    url_pattern = models.CharField(_('URL pattern'), max_length=256,
                                   null=True, blank=True)

    def __str__(self):
        return self.label

    class Meta:
        ordering = ('pk',)
        verbose_name = _('Service')
        verbose_name_plural = _('Services')


class Account(models.Model):
    """ユーザーが使用しているサービスのアカウントを表すモデル"""
    profile = models.ForeignKey(
        Profile, verbose_name=_('Account'), editable=False,
        related_name='accounts')
    service = models.ForeignKey(Service, verbose_name=_('Service'))
    pub_state = models.CharField(_('Publish status'),
                                 choices=Profile.PUB_STATES,
                                 max_length=10, default='public')
    username = models.CharField(_('Username'), max_length=64)

    class Meta:
        verbose_name = _('Account')
        verbose_name_plural = _('Accounts')
        unique_together = ('service', 'username'),
        permissions = (
            ('view_account', 'Can view the account'),
        )

    def __str__(self):
        return "%s (%s @ %s)" % (self.username,
                                 self.profile.user.username,
                                 self.service.label)

    @property
    def url(self):
        return self.service.url_pattern.format(username=self.username)


# 更新情報を記録
from activities.registry import registry
from ..activities.profile import ProfileActivityMediator
from ..activities.profile import AccountActivityMediator
registry.register(Profile, ProfileActivityMediator())
registry.register(Account, AccountActivityMediator())


# パーミッション関係を設定
from permission import add_permission_logic
from kawaz.core.publishments.perms import PublishmentPermissionLogic
from kawaz.core.personas.perms import RoleBasedAuthorPermissionLogic
from kawaz.core.personas.perms import NervPermissionLogic

add_permission_logic(Skill, NervPermissionLogic(
    any_permission=True
))
add_permission_logic(Service, NervPermissionLogic(
    any_permission=True
))
add_permission_logic(Account, RoleBasedAuthorPermissionLogic(
    field_name='profile__user',
    any_permission=False,
    change_permission=False,
    delete_permission=True
))
add_permission_logic(Account, PublishmentPermissionLogic(
    author_field_name='profile__user'
))
add_permission_logic(Profile, RoleBasedAuthorPermissionLogic(
    field_name='user',
    change_permission=True,
    delete_permission=False
))
add_permission_logic(Profile, PublishmentPermissionLogic(
    author_field_name='user'
))
