from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.utils.translation import ugettext_lazy as _

# Create your models here.

class Group(models.Model):
    name = models.CharField(max_length=225, unique=True, blank=True, null=True)

    def __str__(self):
    	return self.name

class MyUserManager(BaseUserManager):
    def create_user(self, email, password=None):
        """
        Creates and saves a User with the given email, date of
        birth and password.
        """
        if not email:
            raise ValueError('Users must have an email address')
        print "--------------------->",self.model
        user = self.model(email=MyUserManager.normalize_email(email))
        print "---------------------->user",user

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password):
        """
        Creates and saves a superuser with the given email, date of
        birth and password.
        """
        u = self.create_user(email, password=password)
        u.is_admin = True
        u.save(using=self._db)
        return u

class BayUser(AbstractBaseUser):
    first_name = models.CharField(_('first name'), max_length=30)
    last_name = models.CharField(_('last name'), max_length=30, blank=True)
    email = models.EmailField(_('email address'), unique=True)
    is_admin = models.BooleanField(_('is_admin'), default=False)
    is_owner = models.BooleanField(_('is_owner'), default=False)
    is_active = models.BooleanField(_('is_active'), default=True)
    rfid = models.CharField(max_length=225, unique=True)
    group = models.ForeignKey(Group,blank=True,null=True)

    USERNAME_FIELD = 'email'

    objects = MyUserManager()

    def get_basic_serialize(self):
        return {
            'id': self.id,
            'first_name': self.first_name,
            'email': self.email
        }

    def get_full_name(self):
        # The user is identified by their email address
        return self.email

    def get_short_name(self):
        # The user is identified by their email address
        return self.email

    def __unicode__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        "Does the user have a specific permission?"
        # Simplest possible answer: Yes, always
        return True

    def has_module_perms(self, app_label):
        "Does the user have permissions to view the app `app_label`?"
        # Simplest possible answer: Yes, always
        return True

    @property
    def is_staff(self):
        "Is the user a member of staff?"
        # Simplest possible answer: All admins are staff
        return self.is_admin