from django.shortcuts import render
from rest_framework import viewsets
from users.models import BayUser, Group
from users.serializers import BayUserSerializer, GroupSerializer
from rest_framework.decorators import list_route, detail_route
from rest_framework.response import Response
from rest_framework import status

# Create your views here.


class UserViewSet(viewsets.ModelViewSet):
    queryset = BayUser.objects.all().order_by('-id')
    serializer_class = BayUserSerializer

    @detail_route(methods=['post','get'], url_path='tools')
    def tools(self, request,bid=None, pk=None):
    	from bay.models import Tool
    	from bay.serializers import ToolSerializer
    	bay_id = self.request.query_params.get('bay_id', None)
    	user = BayUser.objects.get(id=pk)
    	all_tools = Tool.objects.filter(tool_users=user)
    	bay_tools = all_tools.filter(bay_id=bay_id)
        serializer = ToolSerializer(bay_tools, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
   
    @detail_route(methods=['post','get'], url_path='utilization')
    def utilization(self, request,bid=None, pk=None):
        from bay.models import Tool, Logging
        from bay.serializers import LoggingSerializer
        user = BayUser.objects.get(id=pk)
        logging = Logging.objects.filter(user=user)
        serializer = LoggingSerializer(logging, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @detail_route(methods=['delete'],url_path='user_delete')
    def user_delete(self,request,bid=None,pk=None):
	try:
		user= BayUser.objects.get(id=pk)
		#you should not delete the entries in database, instead give a option for Activate / Deactivate
		#user.delete()
		return Response({'result':'user deleted'}, status=status.HTTP_200_OK)
	except:
		return Response({'result':'User Not found'})

class GroupViewSet(viewsets.ModelViewSet):
	queryset = Group.objects.all()
	serializer_class = GroupSerializer
