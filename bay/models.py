from django.db import models
from django.conf import settings
from bay.constants import TOOL_MAIN_STATUS, MAINTENANCE_STATUS
from users.models import BayUser
# Create your models here.


class BaseTable(models.Model):
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Project(BaseTable):
    name = models.CharField(max_length=225, blank=True, null=True)
    description = models.CharField(max_length=225, blank=True, null=True)
    users = models.ManyToManyField(BayUser)

    def get_basic_serialize(self):
        return {
            'id': self.id,
            'first_name': self.name
        }
    def __unicode__(self):
	return self.name

class Bay(models.Model):
    name = models.CharField(max_length=225, blank=True, null=True)
    mac_id = models.CharField(max_length=225)
    location = models.CharField(max_length=225, blank=True, null=True)
    is_active = models.BooleanField(default=False)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def get_basic_serialize(self):
        data = {}
        data['name'] = self.name
        data['id'] = self.id
        data['is_active'] = self.is_active
        return data
	
    def __unicode__(self):
	return self.name

#Added on 27-07-2017
class ToolCategory(models.Model):
    category_name = models.CharField(max_length=100, null=True)
    percentage = models.IntegerField(default=0, blank=True, null=True)

    def __unicode__(self):
        return self.category_name


class Tool(BaseTable):
    name = models.CharField(max_length=225)
    status = models.CharField(max_length=200,choices=TOOL_MAIN_STATUS, null=True, blank=True,default='ID')
    maintenance_status = models.CharField(max_length=200, choices=MAINTENANCE_STATUS, null=True, blank=True)
    bay = models.ForeignKey(Bay, default=False, null=True)
    projects = models.ManyToManyField(Project, through='ToolProject', related_name='ToolProject')
    image = models.ImageField('Upload Image',blank=True,null=True)
    tool_owner = models.ForeignKey(BayUser,blank=True,null=True, related_name='ToolOwner')
    tool_users = models.ManyToManyField(BayUser, related_name='ToolUser')
    bay_number = models.CharField(max_length=255, blank=True, null=True)
    current_project = models.ForeignKey(Project, related_name='CurrentProject', blank=True,null=True)
    is_active = models.BooleanField(default=False)
    tool_category = models.ForeignKey(ToolCategory, blank=True, null=True)

    class Meta:
        ordering = ['id']

    def get_basic_serialize(self):
        return {
            'id': self.id,
            'first_name': self.name
        }
    def get_projects(self):
	return {
	    'projects':self.projects
	}

    def __unicode__(self):
	return self.name

class ToolProject(BaseTable):
    project = models.ForeignKey(Project)
    tool = models.ForeignKey('Tool')
    is_enabled = models.BooleanField(default=False)

    class Meta:
        ordering = ['id']


class ToolImage(models.Model):
    image = models.ImageField('Upload Image')


class Logging(BaseTable):
    user = models.ForeignKey(BayUser)
    project = models.ForeignKey(Project)
    tool = models.ForeignKey(Tool)
    status = models.CharField(max_length=200,choices=TOOL_MAIN_STATUS, null=True, blank=True,default='ID')
