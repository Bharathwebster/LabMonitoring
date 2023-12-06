from rest_framework import serializers
from bay.models import Bay, Tool, Project, ToolProject, ToolImage, Logging, ToolCategory
#, Console
from users.serializers import BayUserSerializer
from users.models import BayUser
from bay.constants import TOOL_MAIN_STATUS, MAINTENANCE_STATUS

MISSING_MODEL_CLASS = "Missing 'model_class' attribute"
MISSING_SERIALIZE_METHOD = "Model class should have set 'get_basic_serialize' method"

class PkDictField(serializers.Field):

    """
    Serializer field taking input pk of foreign key and output serialized object.
    """
   
    def __init__(self, *args, **kwargs):
        self.model_class=kwargs.pop('model_class',None)
        self.model_serializer_function = kwargs.pop('serializer_function','get_basic_serialize')
        assert self.model_class, MISSING_MODEL_CLASS
        assert hasattr(self.model_class, self.model_serializer_function), MISSING_SERIALIZE_METHOD
        super(PkDictField, self).__init__(*args, **kwargs)
   
    def to_internal_value(self, data):
        if data:
            if isinstance(data, dict):
                pk = data.get("id")
            else:
                pk = data
            try:
                return self.model_class.objects.get(pk=pk)
            except:
                raise serializers.ValidationError("Invalid pk %s - object does not exist." % (data))
        else:
            return None

    def to_representation(self, value):
        return value.__getattribute__(self.model_serializer_function)()


#class ConsoleSerializer(serializers.ModelSerializer):
#    class Meta:
#        model = Console
#	fields = ('console_number')


class BaySerializer(serializers.ModelSerializer):
    tools = serializers.SerializerMethodField()

    class Meta:
        model = Bay
        fields = ('id','name','mac_id','location','is_active','tools')
        #fields = ('id','name','mac_id','location','is_active','tools', 'console')

    def get_tools(self,obj):
        if obj.tool_set.all():
            return ToolSerializer(obj.tool_set.all(), many=True).data
        else:
            return None


class ToolSerializer(serializers.ModelSerializer):
    #image_url = serializers.SerializerMethodField()
    #bay = serializers.SerializerMethodField()
    status_value = serializers.SerializerMethodField()
    tool_owner = PkDictField(model_class=BayUser,required=False, allow_null=True)
    current_project = PkDictField(model_class=Project,required=False, allow_null=True)


    class Meta:
        model = Tool
        #fields = ('id','name','status','status_value','image','image_url','tool_owner','bay_number','current_project','is_active')
        fields = ('id','name','status','status_value','bay','image','tool_owner','bay_number','current_project','is_active')
        # read_only_fields = ('bay')

    def get_tools(self,obj):
        if obj.tool_set.all():
            return ToolSerializer(obj.tool_set.all(), many=True).data
        else:
            return None
    '''
    def get_bay(self, obj):
        if hasattr(obj,'bay'):
            return obj.bay.get_basic_serialize()
        else:
            return None
    '''
    def get_image_url(self,obj):
        if obj.image:
	    #return 'http://122.166.6.252:8871'+obj.image.url
	    return 'http://49.204.68.18:8871'+obj.image.url
        return None

    def get_status_value(self, obj):
        if obj.status:
            for tool_status in TOOL_MAIN_STATUS:
                if tool_status[0] == obj.status:
                    return tool_status[1]
            return 'Vacant'
        else:
            return 'Vacant'

class ProjectSerializer(serializers.ModelSerializer):

    class Meta:
        model = Project
        fields = ('id','name','description')

class ToolProjectSerializer(serializers.ModelSerializer):
    project = ProjectSerializer()
    class Meta:
        model = ToolProject
        fields = ('project','is_enabled',)


class ToolImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ToolImage
        fields = ('id', 'image')

class LoggingSerializer(serializers.ModelSerializer):
    user = PkDictField(model_class=BayUser,required=False, allow_null=True)
    project = PkDictField(model_class=Project,required=False, allow_null=True)
    tool = PkDictField(model_class=Tool,required=False, allow_null=True)
    class Meta:
        model = Logging
        #fields = ('user','project','status','tool','created_on')
	fields = '__all__'
# added for anular5 cpu
class ConsoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bay
        # fields = '__all__'
        fields = ('id','name','mac_id','location','is_active',)
	#fields = '__all__'


#class TestToolSerializer(serializers.ModelSerializer):
   # bay = ConsoleSerializer()
   # class Meta:
    #    model = Tool
        #fields = ['id','name','status','status_value','bay','image','image_url','tool_owner','is_active','bay_number','current_project']
     #   fields = ('id','name','status','bay','image','tool_owner','is_active','bay_number','current_project',)
	#fields = '__all__'


class AddToolSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tool
        fields = ('name','bay_number','tool_owner','image',)


class AddImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tool
        fields = ('image',)


class BayUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bay
        #fields = '__all__'
        fields = ('id','name','mac_id','location','is_active','tools',)


class Tool2Serializer(serializers.ModelSerializer):
    class Meta:
        model = Tool
        #fields = '__all__'
        fields = ('id','name','status','bay','image','tool_owner','is_active','bay_number','current_project',)


class NewToolSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tool
        fields = ('name','bay_number','bay','tool_owner','current_project','is_active','status', 'tool_users','tool_category',
                  'image')



class TestToolSerializer(serializers.ModelSerializer):
    bay = ConsoleSerializer()
    class Meta:
        model = Tool
        fields = ('id','name','status','bay','image','tool_owner','is_active','bay_number','current_project','maintenance_status','projects','tool_users','tool_category')

class ToolCategorySerializer1(serializers.ModelSerializer):
    class Meta:
        model = ToolCategory
        #fields = '__all__'
        fields = ('category_name','percentage',)

class MoveToolSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tool
        fields = ('id','name','bay_number','bay','is_active','status',)

class SwapToolSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tool
        fields = ('bay_number','bay','id',)

class ChangeStatusSerializer1(serializers.ModelSerializer):
    class Meta:
        model = Tool
        fields = ('id','status',)

class ImageOnlySerializer(serializers.ModelSerializer):
    class Meta:
        model = Tool
        fields = ('id','image')