from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.views import APIView
from bay.models import Bay, Tool, Project, ToolProject, ToolImage, Logging,ToolCategory
from users.models import BayUser
from bay.serializers import BaySerializer, ToolSerializer , ProjectSerializer, ToolProjectSerializer,ToolImageSerializer, LoggingSerializer, ConsoleSerializer,AddToolSerializer, \
    AddImageSerializer, BayUpdateSerializer, Tool2Serializer, NewToolSerializer, TestToolSerializer, ToolCategorySerializer1, \
    MoveToolSerializer,ChangeStatusSerializer1,SwapToolSerializer,ImageOnlySerializer
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import list_route, detail_route
from users.serializers import BayUserSerializer, GroupSerializer
from django.http import HttpResponse
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from dateutil.rrule import rrule,MONTHLY
import xlwt
import datetime
import pytz
from django.conf import settings


from rest_framework.permissions import BasePermission
from rest_framework.permissions import IsAuthenticated
from easy_pdf.views import PDFTemplateView

# added by cpu on 23 april 2018 angular 5

from rest_framework.generics import UpdateAPIView, ListAPIView, RetrieveUpdateDestroyAPIView


# Start of  ToolViewSet
# Start of ToolViewSet Class --
class AddToolPermission(BasePermission):

    def has_permission(self, request, view):
        try:
            bid = int(view.kwargs.get('bid'))
	    #if ( bid != 257 ):
            bay_obj = Bay.objects.get(id=bid)
            if bay_obj.tool_set.count() >=6:
                return False
        except:
            return True
        return True

def home(request):
    return render(request, 'home.html')


class ToolViewSet(viewsets.ModelViewSet):
    #queryset = Tool.objects.all()
    serializer_class = ToolSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [AddToolPermission()]
        else:
            return [IsAuthenticated(),]

    def get_serializer_context(self):
        return {'request': self.request}

    def get_queryset(self):
	if self.kwargs.has_key('bid'):
            return Tool.objects.filter(bay_id=self.kwargs['bid']).order_by('-created_on')
        # employee = Employee.objects.get(user__id=int(self.kwargs['uid']))
        return Tool.objects.all().order_by('-created_on')
	'''
	tsat = tool['is_active']
	bay_num = (self.request.query_params.get('bid'))

        #tool = Tool.objects.get(bay_number=bay_num)
	#tact = tool.is_active
	if bay_num is not None :
	    #bayset = Tool.objects.filter(bay_number=bay_num)

	    bayset = Tool.objects.filter(bay_number=bay_num,is_active=True)
	    return bayset

	    for i in range(0,len(bayset)):
	        if bayset[i].is_active== True:
		    return  bayset[i]
		else:
		    continue

	else:
	    return Tool.objects.all().order_by('-created_on')

        if self.kwargs.has_key('bid'):
            return Tool.objects.filter(bay_id=self.kwargs['bid']).order_by('-created_on')
        # employee = Employee.objects.get(user__id=int(self.kwargs['uid']))
        return Tool.objects.all().order_by('-created_on')
	'''
    def perform_create(self,serializer):
    	bay_id = self.kwargs['bid']
    	bay_obj = Bay.objects.get(id=bay_id)
    	key = serializer._validated_data
        print key
    	key['bay'] = bay_obj
        if key.get('status'):
            key['status'] = 'ID' 
    	obj = serializer.save(**key)
    	return obj

    def update(self, request, bid=None, pk=None,**kwagrs):
        try:
            if type(request.data['image']) == unicode:
                request.data.pop('image')
        except:
            pass        
        serializer = self.get_serializer(self.get_object(), data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        # try:
        #     image_cropper(get_image_dimensions(self.request.data),
        #                   self.get_object().logo)
        # except Exception, e:
        #     logging.error(e, exc_info=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @detail_route(methods=['post','get'], url_path='assign-projects')
    def assign_projects(self, request, bid=None, pk=None):
        tool_obj = self.get_object()
        if request.method == 'POST':
            project_ids = request.data['project_ids']
            tool_obj.projects.clear()
            if project_ids:
                for project_id in project_ids:
                    try:
                        project = Project.objects.get(id = project_id)
                        tool_project = ToolProject()
                        tool_project.project = project
                        tool_project.tool = tool_obj
                        tool_project.is_enabled = True
                        tool_project.save()                        
                    except:
                        pass
                peojects = ToolProject.objects.filter(tool=tool_obj)
                serializer = ToolProjectSerializer(peojects, many=True)
                data = serializer.data[:]
                return Response(data, status=status.HTTP_200_OK)
            return Response({'status': 'saved'}, status=status.HTTP_200_OK)
        else:
            peojects = ToolProject.objects.filter(tool=tool_obj)
            serializer = ToolProjectSerializer(peojects, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(data, status=status.HTTP_200_OK)

    @detail_route(methods=['post','get'], url_path='users')
    def assign_users(self, request,bid=None, pk=None):
        tool_obj = self.get_object()
        if request.method == 'POST':
            user_ids = request.data['user_ids']
            tool_obj.tool_users.clear()
            if user_ids:
                for user_id in user_ids:
                    try:
                        user = BayUser.objects.get(id = user_id)
                        tool_obj.tool_users.add(user)
                    except:
                        import sys
                        print sys.exc_info()
                        pass
                users = tool_obj.tool_users.all()
                serializer = BayUserSerializer(users, many=True)
                data = serializer.data[:]
                return Response(data, status=status.HTTP_200_OK)
            return Response({'status': 'saved'}, status=status.HTTP_200_OK)
        else:
            users = tool_obj.tool_users.all()
            serializer = BayUserSerializer(users, many=True)
            print serializer.data
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(data, status=status.HTTP_200_OK)

    @list_route(methods=['get','put','delete'], url_path='delete')
    def tool_delete(self, request, *args, **kwargs):
        tool_ids = request.data.get('tool_ids')
        if tool_ids:
	    # We should not delete the entries in the table , instead update the maintenance_status to "NA" Not Active if it is NULL the tool is active
            Tool.objects.filter(id__in=tool_ids).delete()

            return Response({'status':'Deleted'}, status=status.HTTP_200_OK)
        else:
            return Response({'status':'No tool ids'}, status=status.HTTP_200_OK)


    
    
    def valid_date(pk,start_date=None,end_date=None):
            if start_date == None:

                start_date = datetime.datetime.now()+ datetime.timedelta(-30)
                start_date = start_date.strftime("%Y-%m-%d")
                time_zone = pytz.timezone(settings.TIME_ZONE)
                start_date = time_zone.localize(datetime.datetime.strptime(start_date,'%Y-%m-%d'))

                end_date = timezone.now()

            days = (end_date - start_date).days
            list_date = []
            list_date.append(start_date)
            for i in range(1, days+1):
                tmp_date = start_date + datetime.timedelta(i)
                list_date.append(tmp_date)
            trend_data = []
            for tmp_date in list_date:
                start_date = tmp_date
                previous_log = Logging.objects.filter(created_on__lt=start_date,tool_id=pk).order_by('created_on').last()
                second_date = start_date + datetime.timedelta(1)
                next_log = Logging.objects.filter(created_on__gt=second_date, tool_id=pk).order_by('created_on').first()
                data = {}
                data['date'] = start_date
                data[u'PR'] = 0
                data[u'IN'] = 0
                data[u'MA'] = 0
                data[u'ID'] = 0
                logging = Logging.objects.filter(created_on__gte=start_date,created_on__lt=second_date,tool_id=pk).order_by('created_on')
                for i in range(0,len(logging)):
                    log = logging[i]
                    if i>0:
                        previous_log = logging[i-1]
                        start_date = previous_log.created_on
                    if log.created_on > start_date:
                        first_time =  ((log.created_on - start_date).total_seconds())/3600
                        previous_status = previous_log.status if previous_log else 'ID'
                        data[previous_status] += first_time
                    if i == len(logging) -1:
                        second_time =  ((second_date - log.created_on).total_seconds())/3600
                        data[log.status] += second_time
                if len(logging)==0 and previous_log:
                    data[previous_log.status] = 24
                elif len(logging)==0 and previous_log == None:
                    data[u'ID'] = 24

                trend_data.append(data)
            return trend_data
   
    @detail_route(methods=['post','get'], url_path='utilization')
    def utilization(self, request,bid=None, pk=None):
        today = timezone.now()
	start_date = datetime.date.today()
	start_date = start_date.replace(month=2,day=18)
        time_zone = pytz.timezone(settings.TIME_ZONE)
        first_date = start_date.strftime('%Y-%m-%d')
        start_date = time_zone.localize(datetime.datetime.strptime(first_date,'%Y-%m-%d'))
	#pk = Tool.objects.get(bay_number=pk).id
    	ToolUtil = Logging.objects.filter(created_on__gte=start_date, created_on__lte=today, tool_id=pk).order_by('created_on')
        tool = Tool.objects.get(id=pk)
	con = tool.created_on
	if con > start_date:
		start_date = con
		Idle_Time = (ToolUtil.first().created_on - tool.created_on).total_seconds() if ToolUtil else 0
	else:
		Idle_Time = (ToolUtil.first().created_on - start_date).total_seconds() if ToolUtil else 0
        total_seconds = ((today - start_date).total_seconds())
    	ToolUtil = Logging.objects.filter(created_on__gte=start_date, created_on__lte=today, tool_id=pk).order_by('created_on')
        InUse_Time = 0
        Maintenance_Time = 0
        Installation_Time = 0
        total_seconds_day = 24 * 60 * 60
        previous_log = Logging.objects.filter(created_on__lt=start_date,tool_id=pk).order_by('created_on').last()
        second_date = today
        next_log = Logging.objects.filter(created_on__gt=second_date, tool_id=pk).order_by('created_on').first()
        data = {}
        data['date'] = start_date
        data[u'PR'] = 0
        data[u'IN'] = 0
        data[u'MA'] = 0
        data[u'ID'] = 0
        logging = Logging.objects.filter(created_on__gte=start_date,created_on__lt=second_date,tool_id=pk).order_by('created_on')
        for i in range(0,len(logging)):
            log = logging[i]
            if i>0:
                previous_log = logging[i-1]
                start_date = previous_log.created_on
            if log.created_on > start_date:
                first_time =  ((log.created_on - start_date).total_seconds())/3600
                previous_status = previous_log.status if previous_log else 'ID'
                data[previous_status] += first_time
            if i == len(logging) -1:
                second_time =  ((second_date - log.created_on).total_seconds())/3600
                data[log.status] += second_time
        if len(logging)==0 and previous_log:
            data[previous_log.status] = total_seconds/3600
        elif len(logging)==0 and previous_log == None:
            data[u'ID'] += total_seconds/3600

        InUse_Time = data[u'PR']
        Idle_Time = data[u'ID']
        Installation_Time = data[u'IN']
        Maintenance_Time = data[u'MA']


        total_percent = InUse_Time + Idle_Time + Maintenance_Time + Installation_Time + 0.001

        InUse_Time = (InUse_Time/total_percent)*100
        Idle_Time = (Idle_Time/total_percent)*100
        Maintenance_Time = (Maintenance_Time/total_percent)*100
        Installation_Time = (Installation_Time/total_percent)*100

        time = {"Productive":InUse_Time,"Idle":Idle_Time,"Maintenance":Maintenance_Time,"Installation":Installation_Time}
        return Response(time)

    @detail_route(methods=['post','get'], url_path='user_utilization')
    def user_utilization(self, request,bid=None, pk=None):
        tool = Tool.objects.get(id=pk)
        users= tool.tool_users.all()
	start_date = datetime.date.today()
        start_date = start_date.replace(month=2,day=18)
        time_zone = pytz.timezone(settings.TIME_ZONE)
        first_date = start_date.strftime('%Y-%m-%d')
        start_date = time_zone.localize(datetime.datetime.strptime(first_date,'%Y-%m-%d'))
        today = timezone.now()
        end_date = today
	total_seconds = ( today-start_date).total_seconds()
        projects = tool.projects.all()
        response_data = []
        #for project in projects:
        for user in users:
            ToolUtil = Logging.objects.filter (created_on__gte=start_date, created_on__lte=today,tool_id=pk, user=user).order_by('created_on')
            InUse_Time = 0
            Idle_Time = 0
            Maintenance_Time = 0
            Installation_Time = 0
	    try:
	        Total_Time = 0
                Last = (len(ToolUtil)) - 1
                Last_Time = ToolUtil[Last].created_on
                Start_Time = ToolUtil[0].created_on
                # Epoch = datetime.datetime(1970,1,1)
                Status = ""
                for i in range(0,len(ToolUtil)-1):
                    Status = ToolUtil[i].status
                    TimeDiff = ToolUtil[i+1].created_on - ToolUtil[i].created_on
                    print TimeDiff
                    if(Status == "PR"):
                        InUse_Time = InUse_Time + TimeDiff.total_seconds()#*100)/total_seconds_day
                    elif(Status == "ID"):
                        Idle_Time = Idle_Time + TimeDiff.total_seconds()#*100)/total_seconds_day
                    elif(Status == "IN"):
                        Installation_Time = Installation_Time + TimeDiff.total_seconds()#)*100)/total_seconds_day
                    else:
                        Maintenance_Time = Maintenance_Time + TimeDiff.total_seconds()#)*100)/total_seconds_day

                if Start_Time.date() != start_date.date():
                    TimeDiff = Start_Time - start_date
                    obj = Logging.objects.filter(created_on__lt = Start_Time, tool_id=pk ,user=user).order_by('created_on')
                    status = obj.last().status
                    if(status == "PR"):
                        InUse_Time +=  TimeDiff.total_seconds()
                    elif(status == "ID"):
                        Idle_Time += TimeDiff.total_seconds()
                    elif(status == "IN"):
                        Installation_Time += TimeDiff.total_seconds()
                    else:
                        Maintenance_Time += TimeDiff.total_seconds()

		status = ToolUtil.last().status
                remain_time = (today - ToolUtil.last().created_on).total_seconds()
                if(status == "PR"):
                    InUse_Time += remain_time
                elif(status == "ID"):
                    Idle_Time += remain_time
                elif(status == "IN"):
                    Installation_Time += remain_time
                else:
                    Maintenance_Time += remain_time

            except:
                pass

	    if len(ToolUtil) ==0:
                obj = Logging.objects.filter(created_on__lt=start_date,tool_id=pk,user=user).order_by('created_on')
                Last = len(obj)
                if Last > 0:
                    tool = obj.last()
                    if(tool.status == "PR"):
                        InUse_Time = total_seconds
                    elif(tool.status == "ID"):
                        Idle_Time = total_seconds
                    elif(tool.status == "IN"):
                        Installation_Time = total_seconds
                    elif(tool.status == "MA"):
                        Maintenance_Time = total_seconds
		else:
		    pass
                #utilization = InUse_Time + Idle_Time + Installation_Time + Maintenance_Time #commented by cpu
            utilization = InUse_Time + Installation_Time
            utilzation_data= {}
            utilzation_data['first_name'] = user.first_name
            utilzation_data['last_name'] = user.last_name
            utilzation_data['utilization'] = utilization/3600
            response_data.append(utilzation_data)
            
        return Response(response_data)


    @detail_route(methods=['post','get'], url_path='project_utilization')
    def project_utilization(self, request,bid=None, pk=None):
        tool = Tool.objects.get(id=pk)
	start_date = datetime.date.today()
	start_date = start_date.replace(month=2,day=18)
        time_zone = pytz.timezone(settings.TIME_ZONE)
        first_date = start_date.strftime('%Y-%m-%d')
        start_date = time_zone.localize(datetime.datetime.strptime(first_date,'%Y-%m-%d'))
        today = timezone.now()
	end_date = today
        projects = tool.projects.all()
        response_data = []
        for project in projects:
            #ToolUtil = Logging.objects.filter(tool_id=pk,project=project).order_by('created_on')
            ToolUtil = Logging.objects.filter(created_on__gte=start_date, created_on__lte=today,tool_id=pk,project=project).order_by('created_on')
            # today = timezone.now()
            # start_date = tool.created_on
            total_seconds = (today - start_date).total_seconds()
            InUse_Time = 0
            Idle_Time = (ToolUtil.first().created_on - start_date).total_seconds() if ToolUtil else 0
            Maintenance_Time = 0
            Installation_Time = 0
            # requested_time = int(request.query_params.get("hours", 8))
            # total_seconds_day = requested_time * 60 * 60

            try:
                Total_Time = 0
                Last = (len(ToolUtil)) - 1
                Last_Time = ToolUtil[Last].created_on
                Start_Time = ToolUtil[0].created_on
                # Epoch = datetime.datetime(1970,1,1)
                Status = ""

		loopcnt = len(ToolUtil)-1
                for i in range(0,len(ToolUtil)-1):
                    Status = ToolUtil[i].status
                    TimeDiff = ToolUtil[i+1].created_on - ToolUtil[i].created_on
                    print TimeDiff
                    if(Status == "PR"):
                        InUse_Time = InUse_Time + TimeDiff.total_seconds()#*100)/total_seconds_day
                    elif(Status == "ID"):
                        Idle_Time = Idle_Time + TimeDiff.total_seconds()#*100)/total_seconds_day
                    elif(Status == "IN"):
                        Installation_Time = Installation_Time + TimeDiff.total_seconds()#)*100)/total_seconds_day
                    else:
                        Maintenance_Time = Maintenance_Time + TimeDiff.total_seconds()#)*100)/total_seconds_day

		if Start_Time.date() != start_date.date():
        	        TimeDiff = Start_Time - start_date
                	obj = Logging.objects.filter(created_on__lt = Start_Time, tool_id=pk ,project=project).order_by('created_on')
	                status = obj.last().status
	                if(status == "PR"):
	                    InUse_Time +=  TimeDiff.total_seconds()
	                elif(status == "ID"):
	                    Idle_Time += TimeDiff.total_seconds()
	                elif(status == "IN"):
	                    Installation_Time += TimeDiff.total_seconds()
	                else:
        	            Maintenance_Time += TimeDiff.total_seconds()


		#status = ToolUtil.last().status
                #remain_time = (today - ToolUtil.last().created_on).total_seconds()
		'''
		if(status == "PR"):
            	    InUse_Time += remain_time
       	     	    obj = Logging.objects.filter(created_on__lt=start_date,tool_id=pk,project=project).order_by('created_on')
        	    tool = obj.last()
         	    if(tool.status == "PR"):
                        InUse_Time = (total_seconds - ( Idle_Time + Installation_Time + Maintenance_Time ))
            	    elif(tool.status == "IN"):
                	Installation_Time = (total_seconds - ( Idle_Time + InUse_Time + Maintenance_Time ))
           	    elif(tool.status == "ID"):
                	Idle_Time = (total_seconds - ( Installation_Time + InUse_Time + Maintenance_Time ))
            	    else:
                    	Maintenance_Time = (total_seconds - ( Idle_Time + InUse_Time + Installation_Time ))
       	    	elif(status == "ID"):
            	    Idle_Time += remain_time
         	    obj = Logging.objects.filter(created_on__lt=start_date,tool_id=pk,project=project).order_by('created_on')
            	    tool = obj.last()
            	    if(tool.status == "PR"):
			InUse_Time = (total_seconds - ( Idle_Time + Installation_Time + Maintenance_Time ))
            	    elif(tool.status == "IN"):
               	 	Installation_Time = (total_seconds - ( Idle_Time + InUse_Time + Maintenance_Time ))
             	    elif(tool.status == "ID"):
                	Idle_Time = (total_seconds - ( Installation_Time + InUse_Time + Maintenance_Time ))
            	    else:
                   	 Maintenance_Time = (total_seconds - ( Idle_Time + InUse_Time + Installation_Time ))
        	elif(status == "IN"):
            	    Installation_Time += remain_time
                    obj = Logging.objects.filter(created_on__lt=start_date,tool_id=pk,project=project).order_by('created_on')
                    tool = obj.last()
            	    if(tool.status == "PR"):
                	InUse_Time = (total_seconds - ( Idle_Time + Installation_Time + Maintenance_Time ))
           	    elif(tool.status == "IN"):
                	Installation_Time = (total_seconds - ( Idle_Time + InUse_Time + Maintenance_Time ))
          	    elif(tool.status == "ID"):
                	Idle_Time = (total_seconds - ( Installation_Time + InUse_Time + Maintenance_Time ))
            	    else:
                    	Maintenance_Time = (total_seconds - ( Idle_Time + InUse_Time + Installation_Time ))
            #Idle_Time = total_seconds -(InUse_Time+Installation_Time+Maintenance_Time)
        	else:
            	    Maintenance_Time += remain_time
            	    obj = Logging.objects.filter(created_on__lt=start_date,tool_id=pk,project=project).order_by('created_on')
                    tool = obj.last()
            	    if(tool.status == "PR"):
               	        InUse_Time = (total_seconds - ( Idle_Time + Installation_Time + Maintenance_Time ))
            	    elif(tool.status == "IN"):
                	Installation_Time = (total_seconds - ( Idle_Time + InUse_Time + Maintenance_Time ))
                    elif(tool.status == "ID"):
                	Idle_Time = (total_seconds - ( Installation_Time + InUse_Time + Maintenance_Time ))
            	    else:
                    	Maintenance_Time = (total_seconds - ( Idle_Time + InUse_Time + Installation_Time ))
            #Idle_Time = total_seconds -(InUse_Time+Installation_Time+Maintenance_Time)

        	if ( loopcnt == 0 ):
                    prevobj = Logging.objects.filter(created_on__lt=start_date,tool_id=pk,project=project).order_by('created_on')
                    prevlog = prevobj.last()
            	    if ( ( prevlog.status == "PR") and (status == "PR") ):
                	InUse_Time = total_seconds
                	Installation_Time = Idle_Time = Maintenance_Time = 0
            	    else:
               	 	InUse_Time = (total_seconds - ( Idle_Time + Installation_Time + Maintenance_Time ))
            	    if ( ( prevlog.status == "IN") and (status == "IN") ):
                	Installation_Time = total_seconds
                	InUse_Time = Idle_Time = Maintenance_Time = 0
            	    else:
                	Installation_Time = (total_seconds - ( Idle_Time + InUse_Time + Maintenance_Time ))
            	    if ( ( prevlog.status == "MA") and (status == "MA") ):
                	Maintenance_Time = total_seconds
                	InUse_Time = Idle_Time = Installation_Time = 0
            	    else:
               		Maintenance_Time = (total_seconds - ( Idle_Time + InUse_Time + Installation_Time ))
            	    if ( ( prevlog.status == "ID") and (status == "ID") ):
                	Idle_Time = total_seconds
                	InUse_Time = Maintenance_Time = Installation_Time = 0
            	    else:
                	Idle_Time = (total_seconds - ( Maintenance_Time + InUse_Time + Installation_Time ))
		'''
                #if(status == "PR"):
                    #InUse_Time += remain_time
                #elif(status == "ID"):
                    #Idle_Time += remain_time
                #elif(status == "IN"):
                    #Installation_Time += remain_time
                #else:
                    #Maintenance_Time += remain_time
            except:
		pass
	    if len(ToolUtil) ==0:
               	#Idle_Time = total_seconds

                obj = Logging.objects.filter(created_on__lt=start_date,tool_id=pk,project=project).order_by('created_on')
	        Last = len(obj)
	        if Last > 0:
        	    #status = obj.last().status
                    tool = obj.last()
                    if(tool.status == "PR"):
                    	InUse_Time = total_seconds
                    elif(tool.status == "ID"):
                    	Idle_Time = total_seconds
                    elif(tool.status == "IN"):
                    	Installation_Time = total_seconds
                    else:
                    	Maintenance_Time = total_seconds

            utilization = InUse_Time + Installation_Time #Idle_Time + Maintenance_Time
            utilzation_data= {}
            utilzation_data['project_name'] = project.name
	    utilzation_data['utilization'] = utilization/3600
            response_data.append(utilzation_data)

        return Response(response_data)  

    @list_route(methods=['get','put','delete'], url_path='lab_utilization')
    def lab_utilization(self, request, *args, **kwargs):
        tools = Tool.objects.all()
        total_inuse = 0
        total_idle = 0
        total_installation = 0
        total_maintenance = 0
        total_seconds_console = 0
        for tool in tools:
            today = timezone.now()
	    start_date = datetime.date.today()
	    start_date = start_date.replace(month=2,day=18)
            time_zone = pytz.timezone(settings.TIME_ZONE)
            first_date = start_date.strftime('%Y-%m-%d')
            start_date = time_zone.localize(datetime.datetime.strptime(first_date,'%Y-%m-%d'))
    	    ToolUtil = Logging.objects.filter(created_on__gte=start_date, created_on__lte=today, tool_id=tool.id).order_by('created_on')
            InUse_Time = 0
	    con = tool.created_on
	    if con > start_date:
            	start_date = con
                Idle_Time = (ToolUtil.first().created_on - tool.created_on).total_seconds() if ToolUtil else 0
            else:
                Idle_Time = (ToolUtil.first().created_on - start_date).total_seconds() if ToolUtil else 0
            total_seconds = ((today - start_date).total_seconds())
    	    ToolUtil = Logging.objects.filter(created_on__gte=start_date, created_on__lte=today, tool_id=tool.id).order_by('created_on')
            
            Maintenance_Time = 0
            Installation_Time = 0
            #requested_time = int(request.query_params.get("hours", 8))
            total_seconds_day = 24 * 60 * 60
            
	    previous_log = Logging.objects.filter(created_on__lt=start_date,tool_id=tool.id).order_by('created_on').last()
            second_date = today
            next_log = Logging.objects.filter(created_on__gt=second_date, tool_id=tool.id).order_by('created_on').first()
            data = {}
            data['date'] = start_date
            data[u'PR'] = 0
            data[u'IN'] = 0
            data[u'MA'] = 0
            data[u'ID'] = 0
            logging = Logging.objects.filter(created_on__gte=start_date,created_on__lt=second_date,tool_id=tool.id).order_by('created_on')
            for i in range(0,len(logging)):
                log = logging[i]
                if i>0:
                    previous_log = logging[i-1]
                    start_date = previous_log.created_on
                if log.created_on > start_date:
                    first_time =  ((log.created_on - start_date).total_seconds())/3600
                    previous_status = previous_log.status if previous_log else 'ID'
                    data[previous_status] += first_time
                if i == len(logging) -1:
                    second_time =  ((second_date - log.created_on).total_seconds())/3600
                    data[log.status] += second_time
            if len(logging)==0 and previous_log:
                data[previous_log.status] = total_seconds/3600
            elif len(logging)==0 and previous_log == None:
                data[u'ID'] = total_seconds/3600

            InUse_Time = data[u'PR']
            Idle_Time = data[u'ID']
            Installation_Time = data[u'IN']
            Maintenance_Time = data[u'MA']

            total_percent = InUse_Time + Idle_Time + Maintenance_Time + Installation_Time + 0.001

            total_inuse += ((InUse_Time/total_percent)*100 )
            total_idle += ((Idle_Time/total_percent)*100) 
            total_installation += ((Installation_Time/total_percent)*100) 
            total_maintenance += ((Maintenance_Time/total_percent)*100)
            total_seconds_console += total_seconds 

        print "---------------------", total_inuse

	nooftools = len(tools)
        InUse_Time = (total_inuse/nooftools)
        Idle_Time = (total_idle/nooftools)
        Installation_Time = (total_installation/nooftools)
        Maintenance_Time = (total_maintenance/nooftools)
        Idle_Time = 100 - (InUse_Time+Installation_Time+Maintenance_Time)
        #time = {"Productive_Time":InUse_Time,"Idle_Time":Idle_Time,"Maintenance_Time":Maintenance_Time,"Installation_Time":Installation_Time}
        time = {"Productive_Time":InUse_Time,"Idle_Time":Idle_Time,"Maintenance_Time":Maintenance_Time,"Installation_Time":Installation_Time,"PR":total_inuse,"TOT":total_seconds_console,"IN":total_installation,"MA":total_maintenance,"ID":total_idle}
        return Response(time)
    
    @list_route(methods=['get','put','delete'], url_path='lab_utilization_qtr')
    def lab_utilization_qtr(self, request, *args, **kwargs):
	out = []
    	overall_Pr=0
        overall_In =0
        overall_Id = 0
        overall_Ma= 0
        InUse_Time = 0
        Maintenance_Time = 0
        Installation_Time = 0
 	Idle_Time = 0
	total_inuse = 0
        total_idle  = 0
        total_installation = 0
        total_maintenance = 0


        tools = Tool.objects.all()
        val_tool = len(tools)
        print val_tool
        #tool_cnt = 0
        for tool in tools:
            today = timezone.now()
            end_date = today
            today_date = datetime.date.today()
            #first_date = today_date - relativedelta(months=+3)
            presentmonth = today_date.month
            if (presentmonth >=2 ) and ( presentmonth <= 4 ):
                today_date = today_date.replace(month=2,day=1)
            elif (presentmonth >=5 ) and ( presentmonth <= 7 ):
                today_date = today_date.replace(month=5,day=1)
            elif (presentmonth >=8 ) and ( presentmonth <= 10 ):
                today_date = today_date.replace(month=8,day=1)
            elif (presentmonth >=11 ) and ( presentmonth <= 1 ):
                today_date = today_date.replace(month=11,day=1)
 	    first_date = today_date
            time_zone = pytz.timezone(settings.TIME_ZONE)
            first_date = first_date.strftime('%Y-%m-%d')
            start_date = time_zone.localize(datetime.datetime.strptime(first_date,'%Y-%m-%d'))
            ToolUtil = Logging.objects.filter(created_on__gte=start_date, created_on__lte=today, tool_id=tool.id).order_by('created_on')
            InUse_Time = 0
            con = tool.created_on
            if con > start_date:
                start_date = con
                Idle_Time = (ToolUtil.first().created_on - tool.created_on).total_seconds() if ToolUtil else 0
            else:
                Idle_Time = (ToolUtil.first().created_on - start_date).total_seconds() if ToolUtil else 0
            total_seconds = ((today - start_date).total_seconds())
            ToolUtil = Logging.objects.filter(created_on__gte=start_date, created_on__lte=today, tool_id=tool.id).order_by('created_on')

            Maintenance_Time = 0
            Installation_Time = 0
            #requested_time = int(request.query_params.get("hours", 8))
            total_seconds_day = 24 * 60 * 60

            previous_log = Logging.objects.filter(created_on__lt=start_date,tool_id=tool.id).order_by('created_on').last()
            second_date = today
            next_log = Logging.objects.filter(created_on__gt=second_date, tool_id=tool.id).order_by('created_on').first()
            data = {}
            data['date'] = start_date
            data[u'PR'] = 0
            data[u'IN'] = 0
            data[u'MA'] = 0
            data[u'ID'] = 0
            InUse_Time = 0
            Installation_Time = 0
            Maintenance_Time = 0
            logging = Logging.objects.filter(created_on__gte=start_date,created_on__lt=second_date,tool_id=tool.id).order_by('created_on')
            for i in range(0,len(logging)):
                log = logging[i]
                if i>0:
                    previous_log = logging[i-1]
                    start_date = previous_log.created_on
                if log.created_on > start_date:
                    first_time =  ((log.created_on - start_date).total_seconds())/3600
                    previous_status = previous_log.status if previous_log else 'ID'
                    data[previous_status] += first_time
                if i == len(logging) -1:
                    second_time =  ((second_date - log.created_on).total_seconds())/3600
                    data[log.status] += second_time
            if len(logging)==0 and previous_log:
                data[previous_log.status] = total_seconds/3600
            elif len(logging)==0 and previous_log == None:
                data[u'ID'] = total_seconds/3600

            InUse_Time = data[u'PR']
            Idle_Time = data[u'ID']
            Installation_Time = data[u'IN']
            Maintenance_Time = data[u'MA']
            total_percent = InUse_Time + Idle_Time + Maintenance_Time + Installation_Time + 0.001
            total_inuse += ((InUse_Time/total_percent)*100 )
            total_idle += ((Idle_Time/total_percent)*100)
            total_installation += ((Installation_Time/total_percent)*100)
            total_maintenance += ((Maintenance_Time/total_percent)*100)
            #total_seconds_console += total_seconds

        print "---------------------", total_inuse

        nooftools = len(tools)
        InUse_Time = (total_inuse/nooftools)
        Idle_Time = (total_idle/nooftools)
        Installation_Time = (total_installation/nooftools)
        Maintenance_Time = (total_maintenance/nooftools)
        Idle_Time = 100 - (InUse_Time+Installation_Time+Maintenance_Time)

        time = {"Productive_Time":InUse_Time,"Idle_Time":Idle_Time,"Maintenance_Time":Maintenance_Time,"Installation_Time":Installation_Time}
    	return Response(time)



    @list_route(methods=['get','put','delete'], url_path='lab_first_qtr')
    def lab_first_qtr(self, request, *args, **kwargs):
	out = []
    	overall_Pr=0
        overall_In =0
        overall_Id = 0
        overall_Ma= 0
        InUse_Time = 0
        Maintenance_Time = 0
        Installation_Time = 0
 	Idle_Time = 0
	total_inuse = 0
        total_idle  = 0
        total_installation = 0
        total_maintenance = 0


        tools = Tool.objects.all()
        val_tool = len(tools)
        print val_tool
        #tool_cnt = 0
        for tool in tools:
            today = timezone.now()
            today_date = datetime.date.today()
            #first_date = today_date - relativedelta(months=+3)
            today_date = today_date.replace(month=2,day=1)
            end_date = today_date.replace(month=4,day=30)
 	    first_date = today_date
 	    final_date = str(end_date)
 	    #last_date = end_date
            time_zone = pytz.timezone(settings.TIME_ZONE)
            first_date = first_date.strftime('%Y-%m-%d')
            start_date = time_zone.localize(datetime.datetime.strptime(first_date,'%Y-%m-%d'))
            last_date = time_zone.localize(datetime.datetime.strptime(final_date,'%Y-%m-%d'))
            ToolUtil = Logging.objects.filter(created_on__gte=start_date, created_on__lte=last_date, tool_id=tool.id).order_by('created_on')
            InUse_Time = 0
            con = tool.created_on
            if con > start_date:
                start_date = con
                Idle_Time = (ToolUtil.first().created_on - tool.created_on).total_seconds() if ToolUtil else 0
            else:
                Idle_Time = (ToolUtil.first().created_on - start_date).total_seconds() if ToolUtil else 0
            total_seconds = ((last_date - start_date).total_seconds())
            ToolUtil = Logging.objects.filter(created_on__gte=start_date, created_on__lte=end_date, tool_id=tool.id).order_by('created_on')

            Maintenance_Time = 0
            Installation_Time = 0
            #requested_time = int(request.query_params.get("hours", 8))
            total_seconds_day = 24 * 60 * 60

            previous_log = Logging.objects.filter(created_on__lt=start_date,tool_id=tool.id).order_by('created_on').last()
            second_date = last_date
            next_log = Logging.objects.filter(created_on__gt=second_date, tool_id=tool.id).order_by('created_on').first()
            data = {}
            data['date'] = start_date
            data[u'PR'] = 0
            data[u'IN'] = 0
            data[u'MA'] = 0
            data[u'ID'] = 0
            InUse_Time = 0
            Installation_Time = 0
            Maintenance_Time = 0
            logging = Logging.objects.filter(created_on__gte=start_date,created_on__lt=second_date,tool_id=tool.id).order_by('created_on')
            for i in range(0,len(logging)):
                log = logging[i]
                if i>0:
                    previous_log = logging[i-1]
                    start_date = previous_log.created_on
                if log.created_on > start_date:
                    first_time =  ((log.created_on - start_date).total_seconds())/3600
                    previous_status = previous_log.status if previous_log else 'ID'
                    data[previous_status] += first_time
                if i == len(logging) -1:
                    second_time =  ((second_date - log.created_on).total_seconds())/3600
                    data[log.status] += second_time
            if len(logging)==0 and previous_log:
                data[previous_log.status] = total_seconds/3600
            elif len(logging)==0 and previous_log == None:
                data[u'ID'] = total_seconds/3600

            InUse_Time = data[u'PR']
            Idle_Time = data[u'ID']
            Installation_Time = data[u'IN']
            Maintenance_Time = data[u'MA']
            total_percent = InUse_Time + Idle_Time + Maintenance_Time + Installation_Time + 0.001
            total_inuse += ((InUse_Time/total_percent)*100 )
            total_idle += ((Idle_Time/total_percent)*100)
            total_installation += ((Installation_Time/total_percent)*100)
            total_maintenance += ((Maintenance_Time/total_percent)*100)
            #total_seconds_console += total_seconds

        print "---------------------", total_inuse

        nooftools = len(tools)
        InUse_Time = (total_inuse/nooftools)
        Idle_Time = (total_idle/nooftools)
        Installation_Time = (total_installation/nooftools)
        Maintenance_Time = (total_maintenance/nooftools)
        Idle_Time = 100 - (InUse_Time+Installation_Time+Maintenance_Time)

        time = {"Productive_Time":InUse_Time,"Idle_Time":Idle_Time,"Maintenance_Time":Maintenance_Time,"Installation_Time":Installation_Time}
    	return Response(time)


    @detail_route(methods=['get','put','delete'], url_path='tool_utilization_qtr')
    def tool_utilization_qtr(self, request, pk):
        today = timezone.now()
        end_date = today
        today_date = datetime.date.today()
        #first_date = today_date - relativedelta(months=+3)
        presentmonth = today_date.month
        if (presentmonth >=2 ) and ( presentmonth <= 4 ):
                today_date = today_date.replace(month=2,day=1)
        elif (presentmonth >=5 ) and ( presentmonth <= 7 ):
                today_date = today_date.replace(month=5,day=1)
        elif (presentmonth >=8 ) and ( presentmonth <= 10 ):
                today_date = today_date.replace(month=8,day=1)
        elif (presentmonth >=11 ) and ( presentmonth <= 1 ):
                today_date = today_date.replace(month=11,day=1)
#        first_date = today_date.replace(day=1)
        #first_date = startqtr(today_date)
        first_date = today_date
        time_zone = pytz.timezone(settings.TIME_ZONE)
        first_date = first_date.strftime('%Y-%m-%d')
        start_date = time_zone.localize(datetime.datetime.strptime(first_date,'%Y-%m-%d'))


        total_inuse = 0
        total_idle = 0
        total_installation = 0
        total_maintenance = 0
        total_seconds_console = 0
        #tool = Tool.objects.get(bay_number=pk)
        tool = Tool.objects.get(id=pk)
        con = tool.created_on
        if con > start_date:
            start_date = con
 
        ToolUtil = Logging.objects.filter(tool_id=tool.id,created_on__gte = start_date, created_on__lte= end_date ).order_by('created_on')
        total_seconds = ((today - start_date).total_seconds())
    	try:
            #time  = utilization_tool(tool.id, start_date, end_date)
            time  = utilization(tool.id, start_date, end_date)

        except:
            pass

        return Response(time)


    @detail_route(methods=['get','put','delete'], url_path='trend')

    def trend(self, request, bid=None, pk=None):
        tmp_logging = Logging.objects.filter(tool_id=pk).order_by('created_on')
        for log in tmp_logging:
            print log.created_on, log.status, log.id
        tool = Tool.objects.get(id=pk)
        try:
            time_zone = pytz.timezone(settings.TIME_ZONE)
            start_date_str = request.GET.get("start_date", None)
            start_date = time_zone.localize(datetime.datetime.strptime(start_date_str,'%Y-%m-%d'))
        except:
            start_date = time_zone.localize(datetime.datetime.strptime('2017-2-18','%Y-%m-%d'))
        try:
            time_zone = pytz.timezone(settings.TIME_ZONE)
            end_date_str = request.GET.get("end_date", None)
            end_date = time_zone.localize(datetime.datetime.strptime(end_date_str,'%Y-%m-%d'))
            today_date = timezone.now()
	    if end_date > today_date:
		end_date = today_date
        except:
	#    import sys
        #    print sys.exc_info()
            end_date = timezone.now()
       	con = tool.created_on
	if con > start_date:
	    start_date = con
	days = (end_date - start_date).days
        list_date = []
        list_date.append(start_date)
        for i in range(1, days+1):
            tmp_date = start_date + datetime.timedelta(i)
            list_date.append(tmp_date)
        trend_data = []
        for tmp_date in list_date:
            start_date = tmp_date
            previous_log = Logging.objects.filter(created_on__lt=start_date,tool_id=pk).order_by('created_on').last()
            second_date = start_date + datetime.timedelta(1)
            next_log = Logging.objects.filter(created_on__gt=second_date, tool_id=pk).order_by('created_on').first()
            data = {}
            data['date'] = start_date
            data[u'PR'] = 0
            data[u'IN'] = 0
            data[u'MA'] = 0
            data[u'ID'] = 0
            logging = Logging.objects.filter(created_on__gte=start_date,created_on__lt=second_date,tool_id=pk).order_by('created_on')
	    loopcnt = len(logging) - 1
            #for i in range(0,len(logging)-1):
            for i in range(0,len(logging)):
                log = logging[i]
                if i>0:
                    previous_log = logging[i-1]
                    start_date = previous_log.created_on
                if log.created_on > start_date:
                    first_time =  ((log.created_on - start_date).total_seconds())/3600
                    previous_status = previous_log.status if previous_log else 'ID'
                    data[previous_status] += first_time
                if i == len(logging) -1:
                    second_time =  ((second_date - log.created_on).total_seconds())/3600
                    data[log.status] += second_time
            if len(logging)==0 and previous_log:
                data[previous_log.status] = 24
            elif len(logging)==0 and previous_log == None:
                data[u'ID'] = 24
	    #if loopcnt == 0 :
	    #	first_time = ( (logging[0].created_on - start_date).total_seconds())/3600
            #	data[logging[0].status] += first_time
            trend_data.append(data)
        return Response({'trend':trend_data}, status=status.HTTP_200_OK)




class BayViewSet(viewsets.ModelViewSet):
    queryset = Bay.objects.all().order_by('-created_on')
    serializer_class = BaySerializer

    def create(self, request, *args, **kwargs):
	print request
        mac_id = request.data['mac_id']
        if Bay.objects.filter(mac_id=mac_id):
            obj = Bay.objects.get(mac_id=mac_id)
            serializer = self.get_serializer(obj,data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
        else:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_update(self, serializer):
    	return super(BayViewSet,self).perform_update(serializer)
    
    def get_bay_info(self, request):
        mac_id = request.data['mac_id']
        rfid = request.data['RFID']
        data = []# {}
        user = BayUser.objects.get(rfid =rfid)
        data['user'] = BayUserSerializer(user).data
        data['bay_id'] = Bay.objects.get(mac_id=mac_id).id
        return Response(data, status=status.HTTP_200_OK)

    @list_route(methods=['get','put','delete'], url_path='delete')
    def bay_delete(self, request, *args, **kwargs):
        bay_ids = request.data.get('bay_ids')
        if bay_ids:
	    # We should not delete the entries in the tabl we should lookout for workaround to maintain old logging
            #Bay.objects.filter(id__in=bay_ids).delete()
            return Response({'status':'Deleted'}, status=status.HTTP_200_OK)
        else:
            return Response({'status':'No tool ids'}, status=status.HTTP_200_OK)
    

class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all().order_by('-created_on')
    serializer_class = ProjectSerializer

    def perform_create(self,serializer):
        key = serializer.data
        obj = serializer.save(**key)
        return obj

    @detail_route(methods=['post','get'], url_path='assign-users')
    def assign_users(self, request, pk=None):
        project_obj = self.get_object()
        if request.method == 'POST':
            user_ids = request.data['user_ids']
            if user_ids:
                project_obj.users.clear()
                for user_id in user_ids:
                    try:
                        user = BayUser.objects.get(id = user_id)
                        project_obj.users.add(user)
                    except:
                        pass
                users = project_obj.users.all()
                serializer = BayUserSerializer(users, many=True)
                data = serializer.data[:]
                return Response(data, status=status.HTTP_200_OK)
            return Response({'status': 'saved'}, status=status.HTTP_200_OK)
        else:
            users = project_obj.users.all()
            serializer = BayUserSerializer(users, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(data, status=status.HTTP_200_OK)

    @list_route(methods=['get','put','delete'], url_path='delete')
    def project_delete(self, request, *args, **kwargs):
        project_ids = request.data.get('project_ids')
        if project_ids:
	    # We should not delete the entries in the table , instead update the maintenance_status to "NA" Not Active if it is NULL the tool is active
            #Project.objects.filter(id__in=project_ids).delete()
            return Response({'status':'Deleted'}, status=status.HTTP_200_OK)
        else:
            return Response({'status':'No project ids'}, status=status.HTTP_200_OK)


class ImageViewSet(viewsets.ModelViewSet):
    queryset = ToolImage.objects.all()
    serializer_class = ToolImageSerializer

from rest_framework import generics

class MailerView(generics.ListCreateAPIView):
    queryset = Tool.objects.all()
    serializer_class = ToolSerializer
    def create(self,request):
        return Response({"sds":"sds"})


class LoggingView(generics.ListCreateAPIView):
    queryset = Logging.objects.all()
    serializer_class = LoggingSerializer


def logging_view(request):
    logg_objs = Logging.objects.all().order_by('created_on')
    for obj in logg_objs:
        print "################################################"
        print obj.__dict__
        print "################################################"

    return HttpResponse(logg_objs)

import datetime


class ToolPDFView(PDFTemplateView):
    template_name = 'toolstatus.html'
    def get_context_data(self, **kwargs):
        context = super(ToolPDFView, self).get_context_data(pagesize="A4",title="Tool Status",**kwargs)
        context['tools'] = Tool.objects.all()
	return context


import xlwt
import datetime
import pytz
from django.conf import settings

@detail_route(methods=['post','get'], url_path='bay_tools')
def bay_tools(request):
    res = timezone.now()
    return res

def export_console_xls(request):
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename=Console.xls'
    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet("Console Report",cell_overwrite_ok=True)
    
    row_num = 0
    
    columns = [
        (u"Console Name", 2000),
        (u"mac_id", 6000),
        (u"Number of Tools", 8000),
        (u"Created date", 8000),
        (u"Is Active", 8000),
    ]

    font_style = xlwt.XFStyle()
    font_style.font.bold = True

    for col_num in xrange(len(columns)):
        ws.write(row_num, col_num, columns[col_num][0], font_style)
        # set column width
        ws.col(col_num).width = columns[col_num][1]

    font_style = xlwt.XFStyle()
    font_style.alignment.wrap = 1
    queryset = Bay.objects.all()
    null = ""
   # if [queryset][name] = 'null':
    for obj in queryset:
        if obj.name != 'null':
	    row_num += 1
            row = [
                obj.name,
                obj.mac_id,
                len(obj.tool_set.all()),
                obj.created_on.strftime('%Y-%m-%d %H:%M'),
                obj.is_active,
            ]
	else:
	    pass
        for col_num in xrange(len(row)):
            ws.write(row_num, col_num, row[col_num], font_style)
            
    wb.save(response)
    return response
 
def utilization_tool(tool_id, start_date=None,end_date=None):

    end_date = end_date
    tool_id = tool_id
    tool = Tool.objects.get(id=tool_id)
    start_date = start_date if start_date else tool.created_on
    today = end_date
    ToolUtil = Logging.objects.filter(created_on__gte=start_date, created_on__lte=end_date, tool_id=tool_id).order_by('created_on')
    print today
    con = tool.created_on
    if con > start_date:
	start_date = con
    ToolUtil = Logging.objects.filter(created_on__gte=start_date, created_on__lte=today, tool_id=tool.id).order_by('created_on')
    total_seconds = ((today - start_date).total_seconds())
    InUse_Time = 0
    Maintenance_Time = 0
    Installation_Time = 0
    Idle_Time=0

    previous_log = Logging.objects.filter(created_on__lt=start_date,tool_id=tool_id).order_by('created_on').last()
    second_date = start_date + datetime.timedelta(1)
    next_log = Logging.objects.filter(created_on__gt=second_date, tool_id=tool_id).order_by('created_on').first()
    data = {}
    data['date'] = start_date
    data[u'PR'] = 0
    data[u'IN'] = 0
    data[u'MA'] = 0
    data[u'ID'] = 0
    logging = Logging.objects.filter(created_on__gte=start_date,created_on__lt=second_date,tool_id=tool_id).order_by('created_on')
    for i in range(0,len(logging)):
        log = logging[i]
        if i>0:
            previous_log = logging[i-1]
            start_date = previous_log.created_on
        if log.created_on > start_date:
            first_time =  ((log.created_on - start_date).total_seconds())/3600
            previous_status = previous_log.status if previous_log else 'ID'
            data[previous_status] += first_time
        if i == len(logging) -1:
            second_time =  ((second_date - log.created_on).total_seconds())/3600
            data[log.status] += second_time
    if len(logging)==0 and previous_log:
        data[previous_log.status] = 24
    elif len(logging)==0 and previous_log == None:
        data[u'ID'] = 24

    InUse_Time = data[u'PR']
    Idle_Time = data[u'ID']
    Installation_Time = data[u'IN']
    Maintenance_Time = data[u'MA']
    total_percent = InUse_Time + Idle_Time + Maintenance_Time + Installation_Time + 0.001

    InUse_percent = (InUse_Time/total_percent)*100
    Idle_percent = (Idle_Time/total_percent)*100
    Maintenance_percent = (Maintenance_Time/total_percent)*100
    Installation_percent = (Installation_Time/total_percent)*100

    time = {"InUse_Time":InUse_Time,"Idle_Time":Idle_Time,"Maintenance_Time":Maintenance_Time,"Installation_Time":Installation_Time,"InUse_percent":InUse_percent,"Idle_percent":Idle_percent,"Maintenance_percent":Maintenance_percent,"Installation_percent":Installation_percent}
    return time

                                                                                                                                          

def utilization(tool_id, start_date=None,end_date=None):
    end_date = end_date
    tool_id = tool_id
    tool = Tool.objects.get(id=tool_id)
    start_date = start_date if start_date else tool.created_on
    today = end_date
    ToolUtil = Logging.objects.filter(created_on__gte=start_date, created_on__lte=end_date, tool_id=tool_id).order_by('created_on')
    print today
    InUse_Time = 0
    con = tool.created_on
    if con > start_date:
    	start_date = con
        Idle_Time = (ToolUtil.first().created_on - tool.created_on).total_seconds() if ToolUtil else 0
    else:
        Idle_Time = (ToolUtil.first().created_on - start_date).total_seconds() if ToolUtil else 0
    total_seconds = ((today - start_date).total_seconds())
    ToolUtil = Logging.objects.filter(created_on__gte=start_date, created_on__lte=end_date, tool_id=tool_id).order_by('created_on')

    Maintenance_Time = 0
    Installation_Time = 0
    Idle_Time=0
    previous_log = Logging.objects.filter(created_on__lt=start_date,tool_id=tool_id).order_by('created_on').last()
    second_date = today
    next_log = Logging.objects.filter(created_on__gt=second_date, tool_id=tool_id).order_by('created_on').first()
    data = {}
    data['date'] = start_date
    data[u'PR'] = 0
    data[u'IN'] = 0
    data[u'MA'] = 0
    data[u'ID'] = 0
    logging = Logging.objects.filter(created_on__gte=start_date,created_on__lt=second_date,tool_id=tool_id).order_by('created_on')
    
    for i in range(0,len(logging)):
        log = logging[i]
        if i>0:
            previous_log = logging[i-1]
            start_date = previous_log.created_on
        if log.created_on > start_date:
            first_time =  ((log.created_on - start_date).total_seconds())/3600
            previous_status = previous_log.status if previous_log else 'ID'
            data[previous_status] += first_time
        if i == len(logging) -1:
            second_time =  ((second_date - log.created_on).total_seconds())/3600
            data[log.status] += second_time
    if len(logging)==0 and previous_log:
	data[previous_log.status] = total_seconds/3600
    elif len(logging)==0 and previous_log == None:
        data[u'ID'] = total_seconds/3600
    InUse_Time = data[u'PR']
    Idle_Time = data[u'ID']
    Installation_Time = data[u'IN']
    Maintenance_Time = data[u'MA']

    
    total_percent = InUse_Time + Idle_Time + Maintenance_Time + Installation_Time + 0.001
    
    InUse_percent = (InUse_Time/total_percent)*100
    Idle_percent = (Idle_Time/total_percent)*100
    Maintenance_percent = (Maintenance_Time/total_percent)*100
    Installation_percent = (Installation_Time/total_percent)*100

    time = {"InUse_Time":InUse_Time,"Idle_Time":Idle_Time,"Maintenance_Time":Maintenance_Time,"Installation_Time":Installation_Time,"InUse_percent":InUse_percent,"Idle_percent":Idle_percent,"Maintenance_percent":Maintenance_percent,"Installation_percent":Installation_percent}    
    return time


import xlsxwriter
import StringIO
from django.utils.translation import ugettext
def export_tool_xls(request):
    end = datetime.datetime.now()
    rt = 0
    try:
        time_zone = pytz.timezone(settings.TIME_ZONE)
        start_time_str = request.GET.get("start_date",None)
        start_date = time_zone.localize(datetime.datetime.strptime(start_time_str,'%Y-%m-%d'))
        start_date = start_date 
        filename = 'Tools_'+timezone.now().strftime("%Y_%m_%d_%H_%M")+'.xlsx'
    except:
        #start_date = None
        start_date = time_zone.localize(datetime.datetime.strptime('2017-2-18','%Y-%m-%d'))
        #filename = 'RealTimeData__'+timezone.now().strftime("%Y_%m_%d_%H_%M")+'.xls'
        filename = 'RealTimeData__'+timezone.now().strftime("%Y_%m_%d_%H_%M")+'.xlsx'
	rt=1
    try:
        time_zone = pytz.timezone(settings.TIME_ZONE)
        end_date_str = request.GET.get("end_date",None)
        end_date = time_zone.localize(datetime.datetime.strptime(end_date_str,'%Y-%m-%d'))
        end_date = end_date #+ datetime.timedelta(1)
        today_date = timezone.now()
        today_date=today_date.strftime("%Y-%m-%d")
        today_date = time_zone.localize(datetime.datetime.strptime(today_date,'%Y-%m-%d'))

        if end_date > today_date:
            end_date = today_date
    except:
        end_date = timezone.now()

#    response = HttpResponse(content_type='application/ms-excel')
#    response['Content-Disposition'] = 'attachment; filename='+filename

    tools = Tool.objects.all()
    val_tool = len(tools)
    total_pr =0
    total_id =0
    total_in =0
    total_mn =0
    total_pr1 =0
    total_id1 =0
    total_in1 =0
    total_mn1 =0
    
    output = StringIO.StringIO()
    wb = xlsxwriter.Workbook(output,{'in_memory':True})
    ws = wb.add_worksheet("Tools Report")
    bold = wb.add_format({'bold':True})
    row_num = 0

    headings = ['Tool Name', 'Console Name', 'Bay Number','Number of Project assigned','Number of user assigned', 'Current Project','Current Status','Bay Start date', 'End Date','Production Time in hour','Production Time %','Mainatinence Time in hour','Maintainence Time %','idle Time in hour','Idle Time %','Installation Time in hour','Installation Time %']
    format = wb.add_format()
   # format.set_bold()
    format.set_font_color('black')
    for col_num in xrange(len(headings)):
        ws.write(row_num, col_num, headings[col_num], format)
	ws.set_column(row_num, col_num, 20)
    
    queryset = Tool.objects.all()

    for obj in queryset:
	if obj.bay.name != 'Console 1':
	    tool = Tool.objects.get(id=obj.id)
	    con = tool.created_on
	    if con > start_date :
	        start_date = con
	    if con > end_date:
	        break
            time = utilization(obj.id,start_date,end_date)
	    total_pr += time['InUse_Time']
	    total_id += time['Idle_Time']
	    total_in += time['Installation_Time']
	    total_mn += time['Maintenance_Time']
	    total_pr1 += time['InUse_percent']
	    total_id1 += time['Idle_percent']
	    total_in1 += time['Installation_percent']
	    total_mn1 += time['Maintenance_percent']
            row_num += 1
	    if rt == 1 :
                row = [
                    obj.name,
                    obj.bay.name,
                    obj.bay_number,
                    len(obj.projects.all()),
                    len(obj.tool_users.all()),
                    obj.current_project.name if obj.current_project else "No project currently running",
                    obj.get_status_display(),
  	                start_date.strftime('%Y-%m-%d %H:%M') if start_date else obj.created_on.strftime('%Y-%m-%d %H:%M'),
            	        end.strftime('%Y-%m-%d %H:%M'),
                    time["InUse_Time"] if time else None ,
	                time["InUse_percent"],
                    time["Maintenance_Time"] if time else None,
	                time["Maintenance_percent"],
                    time["Idle_Time"] if time else None,
	                time["Idle_percent"],
                    time["Installation_Time"] if time else None,
	                time["Installation_percent"],
                ]
	    else :
                row = [
                    obj.name,
                    obj.bay.name,
                    obj.bay_number,
                    len(obj.projects.all()),
                    len(obj.tool_users.all()),
                    obj.current_project.name if obj.current_project else "No project currently running",
                    obj.get_status_display(),
  	                start_date.strftime('%Y-%m-%d %H:%M') if start_date else obj.created_on.strftime('%Y-%m-%d %H:%M'),
            	        end_date.strftime('%Y-%m-%d %H:%M'),
                    time["InUse_Time"] if time else None ,
	                time["InUse_percent"],
                    time["Maintenance_Time"] if time else None,
	                time["Maintenance_percent"],
                    time["Idle_Time"] if time else None,
	                time["Idle_percent"],
                    time["Installation_Time"] if time else None,
	                time["Installation_percent"],
                ]
      
            for col_num in xrange(len(row)):
    	        ws.write(row_num, col_num, row[col_num], format)
	else:
	    pass
    total_pr1 /= val_tool
    total_id1 /= val_tool
    total_in1 /= val_tool
    total_mn1 /= val_tool
    worksheet_d = wb.add_worksheet("Chart Data")
    worksheet_c = wb.add_worksheet("Charts")
    
     #pie chart
    pie_chart = wb.add_chart({'type': 'pie'})
    pie_values = []
    pie_values.append(total_pr)
    pie_values.append(total_in)
    pie_values.append(total_id)
    pie_values.append(total_mn)
    pie_values.append(total_pr1)
    pie_values.append(total_in1)
    pie_values.append(total_id1)
    pie_values.append(total_mn1)
    pie_categories = ["Production","Installation","Idle","Maintenance"]
    cell_index = 8
    worksheet_d.write_column("{0}1".format(chr(ord('A') + cell_index)),
                             pie_values)
    worksheet_d.write_column("{0}1".format(chr(ord('A') + cell_index + 1)),
                             pie_categories)
    pie_chart.add_series({
        'name': ugettext('overall status statistics'),
        'values': '=Chart Data!${0}${1}:${0}${2}'
        .format(chr(ord('A') + cell_index), 5, 8),
        'categories': '=Chart Data!${0}${1}:${0}${2}'
        .format(chr(ord('A') + cell_index + 1), 1, 4),
        'data_labels': {'percentage': True},
        #'data_labels': {'value': True},
        'points':[{'fill':{'color':'#c2de80'}},
		  {'fill':{'color':'#ffff80'}},
		  {'fill':{'color':'#ff7f7f'}},
		  {'fill':{'color':'#9ac3f5'}}]
	})
    worksheet_c.insert_chart('B5', pie_chart)



    # Creating the column chart
    bar_chart = wb.add_chart({'type': 'column'})
    bar_chart.add_series({
        'name': 'Production Status',
        'values': '=Chart Data!${0}${1}:${0}${2}'
        .format(chr(ord('A') + cell_index), 1, 1),
        'categories': '=Chart Data!${0}${1}:${0}${2}'
        .format(chr(ord('A') + cell_index+1), 1,1),
        'data_labels': {'value': True, 'num_format': u'#0 "hrs"'},
	'fill':{'color':'#c2de80'}
    })
   
    bar_chart.add_series({
        'name': 'Installation Status',
        'values': '=Chart Data!${0}${1}:${0}${2}'
        .format(chr(ord('A') + cell_index), 2, 2),
        'categories': '=Chart Data!${0}${1}:${0}${2}'
        .format(chr(ord('A') + cell_index+1), 2,2),
        'data_labels': {'value': True, 'num_format': u'#0 "hrs"'},
	'fill':{'color':'#ffff80'}
    })

    bar_chart.add_series({
        'name': 'Idle Status',
        'values': '=Chart Data!${0}${1}:${0}${2}'
        .format(chr(ord('A') + cell_index), 3, 3),
        'categories': '=Chart Data!${0}${1}:${0}${2}'
        .format(chr(ord('A') + cell_index+1), 3,3),
        'data_labels': {'value': True, 'num_format': u'#0 "hrs"'},
	'fill':{'color':'#ff7f7f'}
    })

    bar_chart.add_series({
        'name': 'Maintenance Status',
        'values': '=Chart Data!${0}${1}:${0}${2}'
        .format(chr(ord('A') + cell_index), 4, 4),
        'categories': '=Chart Data!${0}${1}:${0}${2}'
        .format(chr(ord('A') + cell_index+1), 4,4),
        'data_labels': {'value': True, 'num_format': u'#0 "hrs"'},
	'fill':{'color':'#9ac3f5'}
    })



    # adding other options
    bar_chart.set_title({'name': ugettext("Bar chart for status")})

    worksheet_c.insert_chart('B20', bar_chart, {'x_scale': 1, 'y_scale': 1})


    
      
  # construct response
    wb.close()
    output.seek(0)
    
    if rt == 1:
    	filename = 'RealTimeData_'+timezone.now().strftime("%Y_%m_%d_%H_%M")+'.xlsx'
    else:
	filename = 'Tools_'+timezone.now().strftime("%Y_%m_%d_%H_%M")+'.xlsx'
    response = HttpResponse(output.read(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response['Content-Disposition'] = "attachment; filename="+filename
    
    return response

def export_tool_qtr_xls(request):
    end = datetime.datetime.now()
    end = datetime.datetime.now()
    today = timezone.now()
    end_date = today
    today_date = datetime.date.today()
    
    presentmonth = today_date.month
    if (presentmonth >=2 ) and ( presentmonth <= 4 ):
           today_date = today_date.replace(month=2,day=1)
    elif (presentmonth >=5 ) and ( presentmonth <= 7 ):
           today_date = today_date.replace(month=5,day=1)
    elif (presentmonth >=8 ) and ( presentmonth <= 10 ):
           today_date = today_date.replace(month=8,day=1)
    elif (presentmonth >=11 ) and ( presentmonth <= 1 ):
           today_date = today_date.replace(month=11,day=1)

    first_date = today_date
    time_zone = pytz.timezone(settings.TIME_ZONE)
    first_date = first_date.strftime('%Y-%m-%d')
    start_date = time_zone.localize(datetime.datetime.strptime(first_date,'%Y-%m-%d'))


    tools = Tool.objects.all()
    val_tool = len(tools)
    total_pr =0
    total_id =0
    total_in =0
    total_mn =0
    total_pr1 =0
    total_id1 =0
    total_in1 =0
    total_mn1 =0

    output = StringIO.StringIO()
    wb = xlsxwriter.Workbook(output,{'in_memory':True})
    ws = wb.add_worksheet("Tools Report")
    bold = wb.add_format({'bold':True})
    row_num = 0

    headings = ['Tool Name', 'Console Name', 'Bay Number','Number of Project assigned','Number of user assigned', 'Current Project','Current Status','Bay Start date', 'End Date','Production Time in hour','Production Time %','Mainatinence Time in hour','Maintainence Time %','idle Time in hour','Idle Time %','Installation Time in hour','Installation Time %']
    format = wb.add_format()
    headings = ['Tool Name', 'Console Name', 'Bay Number','Number of Project assigned','Number of user assigned', 'Current Project','Current Status','Bay Start date', 'End Date','Production Time in hour','Production Time %','Mainatinence Time in hour','Maintainence Time %','idle Time in hour','Idle Time %','Installation Time in hour','Installation Time %']
    format = wb.add_format()
    format.set_font_color('black')
    for col_num in xrange(len(headings)):
        ws.write(row_num, col_num, headings[col_num], format)
        ws.set_column(row_num, col_num, 20)

    queryset = Tool.objects.all()

    for obj in queryset:
        tool = Tool.objects.get(id=obj.id)
	con = tool.created_on
	if con > start_date :
	    start_date = con
        time = utilization(obj.id,start_date,end_date)
        total_pr += time['InUse_Time']
        total_id += time['Idle_Time']
        total_in += time['Installation_Time']
        total_mn += time['Maintenance_Time']
	total_pr1 += time['InUse_percent']
	total_id1 += time['Idle_percent']
	total_in1 += time['Installation_percent']
	total_mn1 += time['Maintenance_percent']
        row_num += 1
        row = [
            obj.name,
            obj.bay.name,
            obj.bay_number,
            len(obj.projects.all()),
            len(obj.tool_users.all()),
            obj.current_project.name if obj.current_project else "No project currently running",
            obj.get_status_display(),
                start_date.strftime('%Y-%m-%d %H:%M') if start_date else obj.created_on.strftime('%Y-%m-%d %H:%M'),
            end.strftime('%Y-%m-%d %H:%M'),
            time["InUse_Time"] if time else None ,
                time["InUse_percent"],
            time["Maintenance_Time"] if time else None,
                time["Maintenance_percent"],
            time["Idle_Time"] if time else None,
                time["Idle_percent"],
            time["Installation_Time"] if time else None,
                time["Installation_percent"],
        ]
        for col_num in xrange(len(row)):
            ws.write(row_num, col_num, row[col_num], format)
    total_pr1 /= val_tool
    total_id1 /= val_tool
    total_in1 /= val_tool
    total_mn1 /= val_tool
    worksheet_d = wb.add_worksheet("Chart Data")
    worksheet_c = wb.add_worksheet("Charts")

     #pie chart
    pie_chart = wb.add_chart({'type': 'pie'})
    pie_values = []
    pie_values.append(total_pr)
    pie_values.append(total_in)
    pie_values.append(total_id)
    pie_values.append(total_mn)
    pie_values.append(total_pr1)
    pie_values.append(total_in1)
    pie_values.append(total_id1)
    pie_values.append(total_mn1)
    pie_categories = ["Production","Installation","Idle","Maintenance"]
    cell_index = 8
    worksheet_d.write_column("{0}1".format(chr(ord('A') + cell_index)),
                             pie_values)
    worksheet_d.write_column("{0}1".format(chr(ord('A') + cell_index + 1)),
                             pie_categories)
    pie_chart.add_series({
        'name': ugettext('overall status statistics'),
        'values': '=Chart Data!${0}${1}:${0}${2}'
        .format(chr(ord('A') + cell_index), 5, 8),
        'categories': '=Chart Data!${0}${1}:${0}${2}'
        .format(chr(ord('A') + cell_index + 1), 1, 4),
        #'data_labels': {'value': True},
        'data_labels': {'percentage': True},
        'points':[{'fill':{'color':'#c2de80'}},
                  {'fill':{'color':'#ffff80'}},
                  {'fill':{'color':'#ff7f7f'}},
                  {'fill':{'color':'#9ac3f5'}}]
        })
    worksheet_c.insert_chart('B5', pie_chart)


    # Creating the column chart
    bar_chart = wb.add_chart({'type': 'column'})
    bar_chart.add_series({
        'name': 'Production Status',
        'values': '=Chart Data!${0}${1}:${0}${2}'
        .format(chr(ord('A') + cell_index), 1, 1),
        'categories': '=Chart Data!${0}${1}:${0}${2}'
        .format(chr(ord('A') + cell_index+1), 1,1),
        'data_labels': {'value': True, 'num_format': u'#0 "hrs"'},
        'fill':{'color':'#c2de80'}
    })

    bar_chart.add_series({
        'name': 'Installation Status',
        'values': '=Chart Data!${0}${1}:${0}${2}'
        .format(chr(ord('A') + cell_index), 2, 2),
        'categories': '=Chart Data!${0}${1}:${0}${2}'
        .format(chr(ord('A') + cell_index+1), 2,2),
        'data_labels': {'value': True, 'num_format': u'#0 "hrs"'},
        'fill':{'color':'#ffff80'}
    })

    bar_chart.add_series({
        'name': 'Idle Status',
        'values': '=Chart Data!${0}${1}:${0}${2}'
        .format(chr(ord('A') + cell_index), 3, 3),
        'categories': '=Chart Data!${0}${1}:${0}${2}'
        .format(chr(ord('A') + cell_index+1), 3,3),
        'data_labels': {'value': True, 'num_format': u'#0 "hrs"'},
        'fill':{'color':'#ff7f7f'}
    })
    bar_chart.add_series({
        'name': 'Maintenance Status',
        'values': '=Chart Data!${0}${1}:${0}${2}'
        .format(chr(ord('A') + cell_index), 4, 4),
        'categories': '=Chart Data!${0}${1}:${0}${2}'
        .format(chr(ord('A') + cell_index+1), 4,4),
        'data_labels': {'value': True, 'num_format': u'#0 "hrs"'},
        'fill':{'color':'#9ac3f5'}
    })

    # adding other options
    bar_chart.set_title({'name': ugettext("Bar chart for status")})

    worksheet_c.insert_chart('B20', bar_chart, {'x_scale': 1, 'y_scale': 1})

    #construct response
    wb.close()
    output.seek(0)

    filename = 'RealTimeQtrData_'+timezone.now().strftime("%Y_%m_%d_%H_%M")+'.xlsx'
    response = HttpResponse(output.read(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response['Content-Disposition'] = "attachment; filename="+filename
    return response


 


def project_utilization(project, start_date=None,end_date=None):
    #tool_id = tool_id
    #tool = Tool.objects.get(id=tool_id)
    #start_date = start_date if start_date else tool.created_on
    end_date = end_date 
    today = end_date
    ToolUtil = Logging.objects.filter(created_on__gte=start_date, created_on__lte=end_date, project=project).order_by('created_on')
    #today = timeizone.now()
    Last = 0
    print today
    total_seconds = ((today - start_date).total_seconds())
    InUse_Time = 0
    #Idle_Time = (ToolUtil.first().created_on - start_date).total_seconds() if ToolUtil else 0
    Idle_Time = 0
    Maintenance_Time = 0
    Installation_Time = 0
    status = ""
    try:
	Total_Time = 0
        Last = (len(ToolUtil)) - 1
        Last_Time = ToolUtil[Last].created_on
        Start_Time = ToolUtil[0].created_on
        Status = ""

        loopcnt = len(ToolUtil) -1

        for i in range(0,len(ToolUtil)-1):
            Status = ToolUtil[i].status
            TimeDiff = ToolUtil[i+1].created_on - ToolUtil[i].created_on
            print TimeDiff
            if(Status == "PR"):
                InUse_Time = ((InUse_Time + TimeDiff.total_seconds()))#/total_seconds_day
            elif(Status == "ID"):
                Idle_Time = ((Idle_Time + TimeDiff.total_seconds()))#/total_seconds_day
            elif(Status == "IN"):
                Installation_Time = ((Installation_Time + TimeDiff.total_seconds()))#/total_seconds_day
            else:
                Maintenance_Time = ((Maintenance_Time + TimeDiff.total_seconds()))#/total_seconds_day


        status = ToolUtil.last().status
        remain_time = (today - ToolUtil.last().created_on).total_seconds()
        if(status == "PR"):
            InUse_Time += remain_time
            obj = Logging.objects.filter(created_on__lt=start_date,project=project).order_by('created_on')
            tool = obj.last()
            if(tool.status == "PR"):
                InUse_Time = (total_seconds - ( Idle_Time + Installation_Time + Maintenance_Time ))
            elif(tool.status == "IN"):
                Installation_Time = (total_seconds - ( Idle_Time + InUse_Time + Maintenance_Time ))
            elif(tool.status == "ID"):
                Idle_Time = (total_seconds - ( Installation_Time + InUse_Time + Maintenance_Time ))
            else:
                Maintenance_Time = (total_seconds - ( Idle_Time + InUse_Time + Installation_Time ))
        elif(status == "ID"):
            Idle_Time += remain_time
            obj = Logging.objects.filter(created_on__lt=start_date,project=project).order_by('created_on')
            tool = obj.last()
            if(tool.status == "PR"):
                InUse_Time = (total_seconds - ( Idle_Time + Installation_Time + Maintenance_Time ))
            elif(tool.status == "IN"):
                Installation_Time = (total_seconds - ( Idle_Time + InUse_Time + Maintenance_Time ))
            elif(tool.status == "ID"):
                Idle_Time = (total_seconds - ( Installation_Time + InUse_Time + Maintenance_Time ))
            else:
                Maintenance_Time = (total_seconds - ( Idle_Time + InUse_Time + Installation_Time ))
        elif(status == "IN"):
            Installation_Time += remain_time
            obj = Logging.objects.filter(created_on__lt=start_date,project=project).order_by('created_on')
            tool = obj.last()
            if(tool.status == "PR"):
                InUse_Time = (total_seconds - ( Idle_Time + Installation_Time + Maintenance_Time ))
            elif(tool.status == "IN"):
                Installation_Time = (total_seconds - ( Idle_Time + InUse_Time + Maintenance_Time ))
            elif(tool.status == "ID"):
                Idle_Time = (total_seconds - ( Installation_Time + InUse_Time + Maintenance_Time ))
            else:
                Maintenance_Time = (total_seconds - ( Idle_Time + InUse_Time + Installation_Time ))
            #Idle_Time = total_seconds -(InUse_Time+Installation_Time+Maintenance_Time)
        else:
            Maintenance_Time += remain_time
            obj = Logging.objects.filter(created_on__lt=start_date,project=project).order_by('created_on')
            tool = obj.last()
            if(tool.status == "PR"):
                InUse_Time = (total_seconds - ( Idle_Time + Installation_Time + Maintenance_Time ))
            elif(tool.status == "IN"):
                Installation_Time = (total_seconds - ( Idle_Time + InUse_Time + Maintenance_Time ))
            elif(tool.status == "ID"):
                Idle_Time = (total_seconds - ( Installation_Time + InUse_Time + Maintenance_Time ))
            else:
                Maintenance_Time = (total_seconds - ( Idle_Time + InUse_Time + Installation_Time ))
            #Idle_Time = total_seconds -(InUse_Time+Installation_Time+Maintenance_Time)

        if ( loopcnt == 0 ):
            prevobj = Logging.objects.filter(created_on__lt=start_date,project=project).order_by('created_on')
            prevlog = prevobj.last()
            if ( ( prevlog.status == "PR") and (status == "PR") ):
                InUse_Time = total_seconds
                Installation_Time = Idle_Time = Maintenance_Time = 0
            else:
                InUse_Time = (total_seconds - ( Idle_Time + Installation_Time + Maintenance_Time ))
            if ( ( prevlog.status == "IN") and (status == "IN") ):
                Installation_Time = total_seconds
                InUse_Time = Idle_Time = Maintenance_Time = 0
            else:
                Installation_Time = (total_seconds - ( Idle_Time + InUse_Time + Maintenance_Time ))
            if ( ( prevlog.status == "MA") and (status == "MA") ):
                Maintenance_Time = total_seconds
                InUse_Time = Idle_Time = Installation_Time = 0
            else:
                Maintenance_Time = (total_seconds - ( Idle_Time + InUse_Time + Installation_Time ))
            if ( ( prevlog.status == "ID") and (status == "ID") ):
                Idle_Time = total_seconds
                InUse_Time = Maintenance_Time = Installation_Time = 0
            else:
                Idle_Time = (total_seconds - ( Maintenance_Time + InUse_Time + Installation_Time ))


    except:
        pass
    # will take care of  if there is no swipe between dates
    if len(ToolUtil) ==0:
        #Idle_Time = total_seconds
        obj = Logging.objects.filter(created_on__lt=start_date,project=project).order_by('created_on')
        Last = len(obj)
        if Last > 0:
            tool = obj.last()
            if(tool.status == "PR"):
                InUse_Time = total_seconds
            elif(tool.status == "ID"):
                Idle_Time = total_seconds
            elif(tool.status == "IN"):
                Installation_Time = total_seconds
            else:
                Maintenance_Time = total_seconds

	'''
        Total_Time = 0
        Last = (len(ToolUtil)) - 1
        Last_Time = ToolUtil[Last].created_on
        Start_Time = ToolUtil[0].created_on
        Status = ""
        for i in range(0,len(ToolUtil)-1):
            Status = ToolUtil[i].status
            TimeDiff = ToolUtil[i+1].created_on - ToolUtil[i].created_on
            print TimeDiff
            if(Status == "PR"):
                InUse_Time = ((InUse_Time + TimeDiff.total_seconds()))#/total_seconds_day
            elif(Status == "ID"):
                Idle_Time = ((Idle_Time + TimeDiff.total_seconds()))#/total_seconds_day
            elif(Status == "IN"):
                Installation_Time = ((Installation_Time + TimeDiff.total_seconds()))#/total_seconds_day
            else:
                Maintenance_Time = ((Maintenance_Time + TimeDiff.total_seconds()))#/total_seconds_day

	if Start_Time.date() != start_date.date():
            TimeDiff = Start_Time - start_date
            obj = Logging.objects.filter(created_on__lt = Start_Time, project=project).order_by('created_on')
	    status = obj.last().status
	    if(status == "PR"):
	        InUse_Time +=  TimeDiff.total_seconds()
	    elif(status == "ID"):
	        Idle_Time += TimeDiff.total_seconds()
	    elif(status == "IN"):
	        Installation_Time += TimeDiff.total_seconds()
	    else:
                Maintenance_Time += TimeDiff.total_seconds()


        status = ToolUtil.last().status
        remain_time = (today - ToolUtil.last().created_on).total_seconds()
        if(status == "PR"):
            InUse_Time += remain_time
        elif(status == "ID"):
            Idle_Time += remain_time
        elif(status == "IN"):
            Installation_Time += remain_time
        else:
            Maintenance_Time += remain_time
    except:
        pass

    if len(ToolUtil) ==0:
        obj = Logging.objects.filter(created_on__lt=start_date, project=project).order_by('created_on')
        Last = len(obj) 
        if Last > 0:
	   status = obj.last().status
           if(status == "PR"):
               InUse_Time = total_seconds
           elif(status == "ID"):
               Idle_Time = total_seconds
           elif(status == "IN"):
               Installation_Time = total_seconds
           else:
               Maintenance_Time = total_seconds
    '''
    print "---------------------->", total_seconds, start_date
    print "---------------------->", InUse_Time
    print "---------------------->", Idle_Time
    print "---------------------->", Installation_Time
    print "---------------------->", Maintenance_Time
    InUse_Time = (InUse_Time/3600)
    Idle_Time = (Idle_Time/3600)
    Installation_Time = (Installation_Time/3600)
    Maintenance_Time = (Maintenance_Time/3600)

    #utilization = Idle_Time + Installation_Time
    #utilization = InUse_Time + Installation_Time

    #return utilization
    time = {"InUse_Time":InUse_Time,"Idle_Time":Idle_Time,"Maintenance_Time":Maintenance_Time,"Installation_Time":Installation_Time}    
    return time



def export_project_xls(request):
    end = datetime.datetime.now()
    try:
        time_zone = pytz.timezone(settings.TIME_ZONE)
        start_time_str = request.GET.get("start_date",None)
        start_date = time_zone.localize(datetime.datetime.strptime(start_time_str,'%Y-%m-%d'))
    except:
        start_date = time_zone.localize(datetime.datetime.strptime('2017-2-18','%Y-%m-%d'))
    try:
        time_zone = pytz.timezone(settings.TIME_ZONE)
        end_date_str = request.GET.get("end_date",None)
        end_date = time_zone.localize(datetime.datetime.strptime(end_date_str,'%Y-%m-%d'))
	end_date = end_date #+ datetime.timedelta(1)
    except:
        end_date = timezone.now()


    response = HttpResponse(content_type='application/ms-excel')
    filename = 'projects'+timezone.now().strftime("%Y_%m_%d_%H_%M")+'.xls'
    response['Content-Disposition'] = 'attachment; filename='+filename
    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet("Projects Report")
    
    row_num = 0
    
    columns = [
        (u"Project Name", 2000),
        (u"Tools", 6000),
        (u"Number of User working", 8000),
	(u"Start Date", 8000),
	(u"End Date", 8000),
        (u"Production Time in hour", 8000),
        (u"Maintenance Time in hour", 8000),
        (u"Idle Time in hour", 8000),
        (u"Installation Time in hour", 8000),
    ]

    font_style = xlwt.XFStyle()
    font_style.font.bold = True

    for col_num in xrange(len(columns)):
        ws.write(row_num, col_num, columns[col_num][0], font_style)
        # set column width
        ws.col(col_num).width = columns[col_num][1]

    font_style = xlwt.XFStyle()
    font_style.alignment.wrap = 1
    queryset = Project.objects.all()
    for obj in queryset:
        utilization = 0
        #for tool in obj.ToolProject.all():
	time = project_utilization(obj,start_date,end_date)
        row_num += 1
        row = [
            obj.name,
            str(obj.ToolProject.all().values_list('name',flat=True)),
            len(obj.users.all()),
  	    start_date.strftime('%Y-%m-%d %H:%M') if start_date else obj.created_on.strftime('%Y-%m-%d %H:%M'),
            end_date.strftime('%Y-%m-%d %H:%M'),
            time["InUse_Time"] if time else None ,
            time["Maintenance_Time"] if time else None,
            time["Idle_Time"] if time else None,
            time["Installation_Time"] if time else None,
        ]
        for col_num in xrange(len(row)):
            ws.write(row_num, col_num, row[col_num], font_style)
            
    wb.save(response)
    return response      

def user_utilization(tool_id, user, start_date=None,end_date=None):
    end_date = end_date
    tool_id = tool_id
    tool = Tool.objects.get(id=tool_id)
    today = end_date
    ToolUtil = Logging.objects.filter(created_on__gte=start_date, created_on__lte=end_date,tool_id=tool_id, user=user).order_by('created_on')
    #today = timeizone.now()
    Last = 0
    print today
    total_seconds = ((today - start_date).total_seconds())
    InUse_Time = 0
    Idle_Time = (ToolUtil.first().created_on - start_date).total_seconds() if ToolUtil else 0
    Maintenance_Time = 0
    Installation_Time = 0
    

    try:
	Total_Time = 0
        Last = (len(ToolUtil)) - 1
        Last_Time = ToolUtil[Last].created_on
        Start_Time = ToolUtil[0].created_on
        Status = ""
        for i in range(0,len(ToolUtil)-1):
            Status = ToolUtil[i].status
            TimeDiff = ToolUtil[i+1].created_on - ToolUtil[i].created_on
            print TimeDiff
            if(Status == "PR"):
                InUse_Time = ((InUse_Time + TimeDiff.total_seconds()))#/total_seconds_day
            elif(Status == "ID"):
                Idle_Time = ((Idle_Time + TimeDiff.total_seconds()))#/total_seconds_day
            elif(Status == "IN"):
                Installation_Time = ((Installation_Time + TimeDiff.total_seconds()))#/total_seconds_day
            else:
                Maintenance_Time = ((Maintenance_Time + TimeDiff.total_seconds()))#/total_seconds_day

        if Start_Time.date() != start_date.date():
            TimeDiff = Start_Time - start_date
            obj = Logging.objects.filter(created_on__lt = Start_Time, user=user).order_by('created_on')
            status = obj.last().status
            if(status == "PR"):
                InUse_Time +=  TimeDiff.total_seconds()
            elif(status == "ID"):
                Idle_Time += TimeDiff.total_seconds()
            elif(status == "IN"):
                Installation_Time += TimeDiff.total_seconds()
            else:
                Maintenance_Time += TimeDiff.total_seconds()



        status = ToolUtil.last().status
        remain_time = (today - ToolUtil.last().created_on).total_seconds()
        if(status == "PR"):
            InUse_Time += remain_time
        elif(status == "ID"):
            Idle_Time += remain_time
        elif(status == "IN"):
            Installation_Time += remain_time
        else:
            Maintenance_Time += remain_time
    except:
        pass
    if len(ToolUtil) ==0:
        obj = Logging.objects.filter(created_on__lt=start_date, user=user).order_by('created_on')
        Last = len(obj)
        if Last > 0:
            status = obj.last().status

        #Idle_Time = total_seconds
       	    if(tool.status == "PR"):
            	InUse_Time = total_seconds
            elif(tool.status == "ID"):
            	Idle_Time = total_seconds
            elif(tool.status == "IN"):
            	Installation_Time = total_seconds
            else:
            	Maintenance_Time = total_seconds

    print "---------------------->", total_seconds, start_date
    print "---------------------->", InUse_Time
    print "---------------------->", Idle_Time
    print "---------------------->", Installation_Time
    print "---------------------->", Maintenance_Time
    InUse_Time = (InUse_Time/3600)
    Idle_Time = (Idle_Time/3600)
    Installation_Time = (Installation_Time/3600)
    Maintenance_Time = (Maintenance_Time/3600)

    #utilization = Idle_Time + Installation_Time
    utilization = InUse_Time + Installation_Time

    return utilization
    #time = {"InUse_Time":InUse_Time,"Idle_Time":Idle_Time,"Maintenance_Time":Maintenance_Time,"Installation_Time":Installation_Time}    
    #return time


def export_user_xls(request):
    end = datetime.datetime.now()
    try:
        time_zone = pytz.timezone(settings.TIME_ZONE)
        start_time_str = request.GET.get("start_date",None)
        start_date = time_zone.localize(datetime.datetime.strptime(start_time_str,'%Y-%m-%d'))
    except:
        start_date = time_zone.localize(datetime.datetime.strptime('2017-2-18','%Y-%m-%d'))
    try:
        time_zone = pytz.timezone(settings.TIME_ZONE)
        end_date_str = request.GET.get("end_date",None)
        end_date = time_zone.localize(datetime.datetime.strptime(end_date_str,'%Y-%m-%d'))
        end_date = end_date# + datetime.timedelta(1)
    except:
        end_date = timezone.now()


    response = HttpResponse(content_type='application/ms-excel')
    filename = 'user_'+timezone.now().strftime("%Y_%m_%d_%H_%M")+'.xls'
    response['Content-Disposition'] = 'attachment; filename='+filename
    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet("Users Report")
    
    row_num = 0
    
    columns = [
        (u"User First Name", 2000),
        (u"User Last Name", 2000),
        (u"RFID", 6000),
        (u"Is Active", 8000),
        (u"Number of Projects", 8000),
        (u"Number of Tools assigned", 8000),
        (u"Start date", 8000),
        (u"End Date", 8000),
        (u"Production-Installation In hours ", 8000),    ]

    font_style = xlwt.XFStyle()
    font_style.font.bold = True

    for col_num in xrange(len(columns)):
        ws.write(row_num, col_num, columns[col_num][0], font_style)
        # set column width
        ws.col(col_num).width = columns[col_num][1]

    font_style = xlwt.XFStyle()
    font_style.alignment.wrap = 1
    
    queryset = BayUser.objects.all()

    for obj in queryset:
        utilization = 0
        for tool in obj.ToolUser.all():
		utilization += user_utilization(tool.id,obj,start_date,end_date)
        row_num += 1
        row = [
            obj.first_name,
            obj.last_name,
            obj.rfid,
            obj.is_active,
            len(obj.project_set.all()),
            len(obj.ToolUser.all()),
  	    start_date.strftime('%Y-%m-%d %H:%M') if start_date else obj.created_on.strftime('%Y-%m-%d %H:%M'),
            end.strftime('%Y-%m-%d %H:%M'),
	    utilization
	]
        for col_num in xrange(len(row)):
            ws.write(row_num, col_num, row[col_num], font_style)
            
    wb.save(response)
    return response


def export_user_raw_xls(request):
    end = datetime.datetime.now()
    try:
        time_zone = pytz.timezone(settings.TIME_ZONE)
        start_date_str = request.GET.get("start_date", None)
        start_date = time_zone.localize(datetime.datetime.strptime(start_date_str,'%Y-%m-%d'))
    except:
        start_date = time_zone.localize(datetime.datetime.strptime('2017-1-1','%Y-%m-%d'))
    try:
        time_zone = pytz.timezone(settings.TIME_ZONE)
        end_date_str = request.GET.get("end_date", None)
        end_date = time_zone.localize(datetime.datetime.strptime(end_date_str,'%Y-%m-%d'))
    except:
        end_date = timezone.now()

    response = HttpResponse(content_type='application/ms-excel')
    filename = 'user_raw_'+timezone.now().strftime("%Y_%m_%d_%H_%M")+'.xls'
    response['Content-Disposition'] = 'attachment; filename='+filename
    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet("Users Report")
    
    row_num = 0
    
    columns = [
        (u"User First Name", 2000),
        (u"User Last Name", 2000),
        (u"RFID", 6000),
        (u"Is Active", 8000),
        (u"project name", 8000),
        (u"Tool name", 8000),
        (u"Logged on", 8000),
        (u"status", 8000),

    ]

    font_style = xlwt.XFStyle()
    font_style.font.bold = True

    for col_num in xrange(len(columns)):
        ws.write(row_num, col_num, columns[col_num][0], font_style)
        # set column width
        ws.col(col_num).width = columns[col_num][1]

    font_style = xlwt.XFStyle()
    font_style.alignment.wrap = 1
    
    queryset = BayUser.objects.all()

    for obj in queryset:
        logging = Logging.objects.filter(created_on__gte=start_date, created_on__lte=end_date,user=obj)
        for log in logging:
            row_num += 1
            row = [
                obj.first_name,
                obj.last_name,
                obj.rfid,
                obj.is_active,
                log.project.name,
                log.tool.name,
                log.created_on.strftime('%Y-%m-%d %H:%M'),
                log.status,
            ]
            for col_num in xrange(len(row)):
                ws.write(row_num, col_num, row[col_num], font_style)
            
    wb.save(response)
    return response


def valid_date(pk,start_date=None,end_date=None):
	    if start_date == None:
	        start_date = datetime.datetime.now()+ datetime.timedelta(-30)
             	start_date = start_date.strftime("%Y-%m-%d")
            	time_zone = pytz.timezone(settings.TIME_ZONE)
            	start_date = time_zone.localize(datetime.datetime.strptime(start_date,'%Y-%m-%d'))

            #time_zone = pytz.timezone(settings.TIME_ZONE)
            #start_date = time_zone.localize(datetime.datetime.strptime(start_date,'%Y-%m-%d'))
            #time_zone = pytz.timezone(settings.TIME_ZONE)
            #end_date = time_zone.localize(datetime.datetime.strptime(end_date,'%Y-%m-%d'))
	    #end_date = timezone.now()
            
	    today_date = timezone.now()
	    if end_date > today_date:
	        end_date = today_date
            days = (end_date - start_date).days
            list_date = []
            list_date.append(start_date)
            for i in range(1, days+1):
                tmp_date = start_date + datetime.timedelta(i)
                list_date.append(tmp_date)
            trend_data = []
            for tmp_date in list_date:
                start_date = tmp_date
                previous_log = Logging.objects.filter(created_on__lt=start_date,tool_id=pk).order_by('created_on').last()
                second_date = start_date + datetime.timedelta(1)
                next_log = Logging.objects.filter(created_on__gt=second_date, tool_id=pk).order_by('created_on').first()
                data = {}
                data['date'] = start_date
                data[u'PR'] = 0
                data[u'IN'] = 0
                data[u'MA'] = 0
                data[u'ID'] = 0
                logging = Logging.objects.filter(created_on__gte=start_date,created_on__lt=second_date,tool_id=pk).order_by('created_on')
                for i in range(0,len(logging)):
                    log = logging[i]
                    if i>0:
                        previous_log = logging[i-1]
                        start_date = previous_log.created_on
                    if log.created_on > start_date:
                        first_time =  ((log.created_on - start_date).total_seconds())/3600
                        previous_status = previous_log.status if previous_log else 'ID'
                        data[previous_status] += first_time
                    if i == len(logging) -1:
                        second_time =  ((second_date - log.created_on).total_seconds())/3600
                        data[log.status] += second_time
                if len(logging)==0 and previous_log:
                    data[previous_log.status] = 24
                elif len(logging)==0 and previous_log == None:
                    data[u'ID'] = 24

            	trend_data.append(data)
	    return trend_data


from rest_framework.decorators import api_view


@api_view(('GET',))
def api_trends(request):
    """
            api for lab trends overall
    """
    try:
        time_zone = pytz.timezone(settings.TIME_ZONE)
        start_time_str = request.GET.get("start_date",None)
        start_date = time_zone.localize(datetime.datetime.strptime(start_time_str,'%Y-%m-%d'))
        start_date = start_date
    except:
        start_date = None
    try:
        time_zone = pytz.timezone(settings.TIME_ZONE)
        end_date_str = request.GET.get("end_date",None)
        end_date = time_zone.localize(datetime.datetime.strptime(end_date_str,'%Y-%m-%d'))
        #end_date = end_date + datetime.timedelta(1)
        end_date = end_date


    except:
        end_date = None

    out = []
    time = []
    overall_Pr=0
    overall_In =0
    overall_Id = 0
    overall_Ma= 0
    overallp_Pr=0
    overallp_In =0
    overallp_Id = 0
    overallp_Ma= 0

    tool = Tool.objects.all()
    val_tool = len(tool)
    print val_tool
    tool_cnt = 0
    for pk_val in tool:
	tool_pk = Tool.objects.get(id = pk_val.id)
	con = tool_pk.created_on
	if con > end_date:
	    break
        result = valid_date(pk_val,start_date,end_date)
      
	time = utilization(pk_val.id,start_date,end_date)
        overallp_Pr += time['InUse_percent']
        overallp_Id += time['Idle_percent']
        overallp_In += time['Installation_percent']
        overallp_Ma += time['Maintenance_percent']

        tool_cnt += 1
        for i in range(0,len(result)):
            overall_Pr += result[i][u'PR']
            overall_Id +=result[i][u'ID']
            overall_In += result[i][u'IN']
            overall_Ma += result[i][u'MA']
            try :
                if out[i]["date"] == result[i]["date"]:
                    out[i][u'PR'] += result[i][u'PR']
                    out[i][u'IN'] += result[i][u'IN']
                    out[i][u'ID'] += result[i][u'ID']
                    out[i][u'MA'] += result[i][u'MA']

                if val_tool == tool_cnt:
                    out[i][u'PR'] = (float(out[i][u'PR'])/tool_cnt)
                    out[i][u'IN'] = (float(out[i][u'IN'])/tool_cnt)
                    out[i][u'ID'] = (float(out[i][u'ID'])/tool_cnt)
                    out[i][u'MA'] = (float(out[i][u'MA'])/tool_cnt)
                else:
                    pass

            except:
                out.append(result[i])

    overall_Pr = (overallp_Pr/tool_cnt)
    overall_Id = (overallp_Id/tool_cnt)
    overall_In = (overallp_In/tool_cnt)
    overall_Ma = (overallp_Ma/tool_cnt)

    overall_Id = 100 - (overall_Pr + overall_Ma + overall_In)
    chart = {"Productive": overall_Pr,"Idle": overall_Id, "Maintainence": overall_Ma, "Installation":overall_In}
    return Response({'trend':out, 'Chart': chart}, status=status.HTTP_200_OK)


'''
def api_trends(request):
    """
            api for lab trends overall
    """
    try:
	time_zone = pytz.timezone(settings.TIME_ZONE)
	start_time_str = request.GET.get("start_date",None)
	start_date = time_zone.localize(datetime.datetime.strptime(start_time_str,'%Y-%m-%d'))
	start_date = start_date
    except:
	start_date = None
    try:
	time_zone = pytz.timezone(settings.TIME_ZONE)
	end_date_str = request.GET.get("end_date",None)
	end_date = time_zone.localize(datetime.datetime.strptime(end_date_str,'%Y-%m-%d'))
	#end_date = end_date + datetime.timedelta(1)
	end_date = end_date


    except:
	end_date = None
  
    out = []
    overall_Pr=0
    overall_In =0
    overall_Id = 0
    overall_Ma= 0

    tool = Tool.objects.all()
    val_tool = len(tool)
    print val_tool
    tool_cnt = 0
    for pk_val in tool:
	if start_date == None:
            result = valid_date(pk_val)
	else:
	    result = valid_date(pk_val,start_date,end_date)
        tool_cnt += 1      
        for i in range(0,len(result)):
            overall_Pr += result[i][u'PR']
            overall_Id +=result[i][u'ID']
            overall_In += result[i][u'IN']
            overall_Ma += result[i][u'MA']
            try :
                if out[i]["date"] == result[i]["date"]:
                    out[i][u'PR'] += result[i][u'PR']
                    out[i][u'IN'] += result[i][u'IN']
                    out[i][u'ID'] += result[i][u'ID']
                    out[i][u'MA'] += result[i][u'MA']
                 
                if val_tool == tool_cnt:
                    out[i][u'PR'] = (float(out[i][u'PR'])/tool_cnt)
                    out[i][u'IN'] = (float(out[i][u'IN'])/tool_cnt)
                    out[i][u'ID'] = (float(out[i][u'ID'])/tool_cnt)
                    out[i][u'MA'] = (float(out[i][u'MA'])/tool_cnt)
                else:
                    pass
                
            except:
                out.append(result[i])

    total_value = overall_Pr + overall_Id + overall_In + overall_Ma
    overall_Pr = (overall_Pr/total_value)*100 
    overall_Id = (overall_Id/total_value)*100
    overall_In = (overall_In/total_value)*100
    overall_Ma = (overall_Ma/total_value)*100
    #overall_Id = 100 - (overall_Pr + overall_Ma + overall_In) 
    chart = {"Productive": overall_Pr,"Idle": overall_Id, "Maintainence": overall_Ma, "Installation":overall_In}
    return Response({'trend':out, 'Chart': chart}, status=status.HTTP_200_OK)
'''


def tools_report(request,tool_id):
    try:
        time_zone = pytz.timezone(settings.TIME_ZONE)
        start_time_str = request.GET.get("start_date",None)
       
        start_date = time_zone.localize(datetime.datetime.strptime(start_time_str,'%Y-%m-%d'))
        start_date = start_date

        filename = 'Tools_report'+timezone.now().strftime("%Y_%m_%d_%H_%M")+'.xls'
    except:
        start_date =time_zone.localize(datetime.datetime.strptime('2017-2-18','%Y-%m-%d'))
        
        filename = 'RealTimeData__'+timezone.now().strftime("%Y_%m_%d_%H_%M")+'.xls'
    try:
        time_zone = pytz.timezone(settings.TIME_ZONE)
        end_date_str = request.GET.get("end_date",None)
        end_date = time_zone.localize(datetime.datetime.strptime(end_date_str,'%Y-%m-%d'))
        
        today_date = timezone.now()
        today_date=today_date.strftime("%Y-%m-%d")
        today_date = time_zone.localize(datetime.datetime.strptime(today_date,'%Y-%m-%d'))

        if end_date > today_date:
            end_date = today_date
    except:
        end_date = timezone.now()
        today_date=end_date.strftime("%Y-%m-%d")
        end_date = time_zone.localize(datetime.datetime.strptime(today_date,'%Y-%m-%d'))

    
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename='+filename
    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet("Tool Reports")
    
    row_num = 0
    
    columns = [
        (u"Tool Name", 2000),
        (u"Tool ID", 2000),
        (u"Start date", 8000),
        (u"End Date", 8000),
        (u"Production Time in hour", 8000),
        (u"Production Time %", 8000),
        (u"Maintenance Time in hour", 8000),
        (u"Maintenance Time %", 8000),
        (u"Idle Time in hour", 8000),
        (u"Idle Time %", 8000),
        (u"Installation Time in hour", 8000),
        (u"Installation Time %", 8000),
    ]

    font_style = xlwt.XFStyle()
    font_style.font.bold = True

    for col_num in xrange(len(columns)):
        ws.write(row_num, col_num, columns[col_num][0], font_style)
        # set column width
        ws.col(col_num).width = columns[col_num][1]

    font_style = xlwt.XFStyle()
    font_style.alignment.wrap = 1
    
    queryset = Tool.objects.get(id = tool_id)
    con = queryset.created_on
    if con > start_date:
	start_date = con
    date_range = (end_date - start_date).daysl
    print date_range
    for obj in range(0,date_range):
        start = start_date + datetime.timedelta(obj)
        end = start_date + datetime.timedelta(obj+1)

        time  = utilization_tool(queryset.id, start, end)
        row_num += 1
        row = [
            queryset.name,
            queryset.id,
            start.strftime('%Y-%m-%d %H:%M'),
            end.strftime('%Y-%m-%d %H:%M'),
            time["InUse_Time"] if time else None ,
            time["InUse_percent"],
            time["Maintenance_Time"] if time else None,
            time["Maintenance_percent"],
            time["Idle_Time"] if time else None,
            time["Idle_percent"],
            time["Installation_Time"] if time else None,
            time["Installation_percent"],
        ]
        for col_num in xrange(len(row)):
            ws.write(row_num, col_num, row[col_num], font_style)
            
    wb.save(response)
    return response 

def trend_pie_tool(pk,start_date=None,end_date=None):
     if start_date == None:
         start_date = datetime.datetime.now()+ datetime.timedelta(-30)
         start_date = start_date.strftime("%Y-%m-%d")
         time_zone = pytz.timezone(settings.TIME_ZONE)
         start_date = time_zone.localize(datetime.datetime.strptime(start_date,'%Y-%m-%d'))
         end_date = timezone.now()

     ToolUtil = Logging.objects.filter(tool_id=pk).order_by('created_on')
     tool = Tool.objects.get(id=pk)
     con = tool.created_on
     if con > start_date:
         start_date = con
     today = end_date
     start_date = start_date
     total_seconds = ((today - start_date).total_seconds())
     #InUse_Time = 0
     #Idle_Time = (ToolUtil.first().created_on - tool.created_on).total_seconds() if ToolUtil else 0
     #Idle_Time = (ToolUtil.first().created_on - start_date).total_seconds() if ToolUtil else 0
     #Maintenance_Time = 0
     #Installation_Time = 0
     #requested_time = int(request.query_params.get("hours", 8))
     total_seconds_day = 24 * 60 * 60
     

     try:
         Total_Time = 0
         Last = (len(ToolUtil)) - 1
         Last_Time = ToolUtil[Last].created_on
         Start_Time = ToolUtil[0].created_on
         Status = ""
         for i in range(0,len(ToolUtil)-1):
             Status = ToolUtil[i].status
             TimeDiff = ToolUtil[i+1].created_on - ToolUtil[i].created_on
             print TimeDiff
             if(Status == "PR"):
                 InUse_Time = ((InUse_Time + TimeDiff.total_seconds()))#/total_seconds_day
             elif(Status == "ID"):
                 Idle_Time = ((Idle_Time + TimeDiff.total_seconds()))#/total_seconds_day
             elif(Status == "IN"):
                 Installation_Time = ((Installation_Time + TimeDiff.total_seconds()))#/total_seconds_day
             else:
                 Maintenance_Time = ((Maintenance_Time + TimeDiff.total_seconds()))#/total_seconds_day

         status = ToolUtil.last().status
         remain_time = (today - ToolUtil.last().created_on).total_seconds()
         if(status == "PR"):
             InUse_Time += remain_time
         elif(status == "ID"):
             Idle_Time += remain_time
         elif(status == "IN"):
             Installation_Time += remain_time
         else:
             Maintenance_Time += remain_time
     except:
         pass 
     
     print "--------------------->",total_seconds
     InUse_Time = (InUse_Time/total_seconds)*100
     #Idle_Time = (InUse_Time/total_seconds)*100
     Installation_Time = (Installation_Time/total_seconds)*100
     Maintenance_Time = (Maintenance_Time/total_seconds)*100
     Idle_Time = 100 - (InUse_Time+Installation_Time+Maintenance_Time)
     time = {InUse_Time,Idle_Time,Maintenance_Time,Installation_Time}
     return time

@api_view(('GET',))
def trends_pie(request):
    try:
        time_zone = pytz.timezone(settings.TIME_ZONE)
        start_time_str = request.GET.get("start_date",None)
        start_date = time_zone.localize(datetime.datetime.strptime(start_time_str,'%Y-%m-%d'))
        start_date = start_date
    except:
        start_date = None
    try:
        time_zone = pytz.timezone(settings.TIME_ZONE)
        end_date_str = request.GET.get("end_date",None)
        end_date = time_zone.localize(datetime.datetime.strptime(end_date_str,'%Y-%m-%d'))
        end_date = end_date + datetime.timedelta(1)
    except:
        end_date = None

    out = []
    tool = Tool.objects.all()
    val_tool = len(tool)
    print val_tool
    tool_cnt = 0
    pr = 0.0
    ids = 0.0
    ma = 0.0
    ins = 0.0
    for pk_val in tool:
        result = trend_pie_tool(pk_val.id,start_date,end_date)
    	tool_cnt += 1
    	try:
           pr += float(result[0])
           ids += float(result[1])
           ma += float(result[2])
           ins += float(result[3])

           if val_tool == tool_cnt:
           	out[0] = (float (pr)/tool_cnt)
                out[1] = (float (ids)/tool_cnt)
                out[2] = (float (ma)/tool_cnt)
                out[3] = (float (ins)/tool_cnt)
           else:
                pass
	except:
	   pass
    
    return Response({'trend_pie':out}, status=status.HTTP_200_OK)






# New Views -- Arun

class NonActiveToolsView(viewsets.ModelViewSet):
    serializer_class = ToolSerializer
    queryset = Tool.objects.filter(is_active=False).order_by('-created_on')

    def get_permissions(self):
        if self.request.method == 'POST':
            return [AddToolPermission()]
        else:
            return [IsAuthenticated(),]

    def get_serializer_context(self):
        return {'request': self.request}


class ToolsView(viewsets.ModelViewSet):
    serializer_class = ToolSerializer
    queryset = Tool.objects.all().order_by('-created_on')

    def get_permissions(self):
        if self.request.method == 'POST':
            return [AddToolPermission()]
        else:
            return [IsAuthenticated(),]

    def get_serializer_context(self):
        return {'request': self.request}

    def utilization(tool_id, start_date=None,end_date=None):
        end_date = end_date
        tool_id = tool_id
        tool = Tool.objects.get(id=tool_id)
        start_date = start_date if start_date else tool.created_on
        today = end_date
        ToolUtil = Logging.objects.filter(created_on__gte=start_date, created_on__lte=end_date, tool_id=tool_id).order_by('created_on')
        print today
        InUse_Time = 0
        con = tool.created_on
        if con > start_date:
            start_date = con
            Idle_Time = (ToolUtil.first().created_on - tool.created_on).total_seconds() if ToolUtil else 0
        else:
            Idle_Time = (ToolUtil.first().created_on - start_date).total_seconds() if ToolUtil else 0
        total_seconds = ((today - start_date).total_seconds())
        ToolUtil = Logging.objects.filter(created_on__gte=start_date, created_on__lte=end_date, tool_id=tool_id).order_by('created_on')

        Maintenance_Time = 0
        Installation_Time = 0
        Idle_Time=0
        previous_log = Logging.objects.filter(created_on__lt=start_date,tool_id=tool_id).order_by('created_on').last()
        second_date = today
        next_log = Logging.objects.filter(created_on__gt=second_date, tool_id=tool_id).order_by('created_on').first()
        data = {}
        data['date'] = start_date
        data[u'PR'] = 0
        data[u'IN'] = 0
        data[u'MA'] = 0
        data[u'ID'] = 0
        logging = Logging.objects.filter(created_on__gte=start_date,created_on__lt=second_date,tool_id=tool_id).order_by('created_on')

        for i in range(0,len(logging)):
            log = logging[i]
            if i>0:
                previous_log = logging[i-1]
                start_date = previous_log.created_on
            if log.created_on > start_date:
                first_time =  ((log.created_on - start_date).total_seconds())/3600
                previous_status = previous_log.status if previous_log else 'ID'
                data[previous_status] += first_time
            if i == len(logging) -1:
                second_time =  ((second_date - log.created_on).total_seconds())/3600
                data[log.status] += second_time

        if len(logging)==0 and previous_log:
            data[previous_log.status] = total_seconds/3600
        elif len(logging)==0 and previous_log == None:
            data[u'ID'] = total_seconds/3600

        InUse_Time = data[u'PR']
        Idle_Time = data[u'ID']
        Installation_Time = data[u'IN']
        Maintenance_Time = data[u'MA']


        total_percent = InUse_Time + Idle_Time + Maintenance_Time + Installation_Time + 0.001

        InUse_percent = (InUse_Time/total_percent)*100
        Idle_percent = (Idle_Time/total_percent)*100
        Maintenance_percent = (Maintenance_Time/total_percent)*100
        Installation_percent = (Installation_Time/total_percent)*100

        time = {"InUse_Time":InUse_Time,"Idle_Time":Idle_Time,"Maintenance_Time":Maintenance_Time,"Installation_Time":Installation_Time,"InUse_percent":InUse_percent,"Idle_percent":Idle_percent,"Maintenance_percent":Maintenance_percent,"Installation_percent":Installation_percent}
        return time


    def tool_utilization_monthly(self, request,bid=None, pk=None):
        today = timezone.now()
        start_date = datetime.date.today()
        start_date = start_date.replace(day=1)
        time_zone = pytz.timezone(settings.TIME_ZONE)
        first_date = start_date.strftime('%Y-%m-%d')
        start_date = time_zone.localize(datetime.datetime.strptime(first_date,'%Y-%m-%d'))
    #pk = Tool.objects.get(bay_number=pk).id
        ToolUtil = Logging.objects.filter(created_on__gte=start_date, created_on__lte=today, tool_id=pk).order_by('created_on')
        tool = Tool.objects.get(id=pk)
        con = tool.created_on
        if con > start_date:
            start_date = con
            Idle_Time = (ToolUtil.first().created_on - tool.created_on).total_seconds() if ToolUtil else 0
        else:
            Idle_Time = (ToolUtil.first().created_on - start_date).total_seconds() if ToolUtil else 0
        total_seconds = ((today - start_date).total_seconds())
        print start_date
        ToolUtil = Logging.objects.filter(created_on__gte=start_date, created_on__lte=today, tool_id=pk).order_by('created_on')
        InUse_Time = 0
        Maintenance_Time = 0
        Installation_Time = 0
        total_seconds_day = 24 * 60 * 60
        previous_log = Logging.objects.filter(created_on__lt=start_date,tool_id=pk).order_by('created_on').last()
        second_date = today
        next_log = Logging.objects.filter(created_on__gt=second_date, tool_id=pk).order_by('created_on').first()
        data = {}
        data['date'] = start_date
        data[u'PR'] = 0
        data[u'IN'] = 0
        data[u'MA'] = 0
        data[u'ID'] = 0
        logging = Logging.objects.filter(created_on__gte=start_date,created_on__lt=second_date,tool_id=pk).order_by('created_on')
        for i in range(0,len(logging)):
            log = logging[i]
            if i>0:
                previous_log = logging[i-1]
                start_date = previous_log.created_on
            if log.created_on > start_date:
                first_time =  ((log.created_on - start_date).total_seconds())/3600
                previous_status = previous_log.status if previous_log else 'ID'
                data[previous_status] += first_time
            if i == len(logging) -1:
                second_time =  ((second_date - log.created_on).total_seconds())/3600
                data[log.status] += second_time
        if len(logging)==0 and previous_log:
            data[previous_log.status] = total_seconds/3600
        elif len(logging)==0 and previous_log == None:
            data[u'ID'] += total_seconds/3600

        InUse_Time = data[u'PR']
        Idle_Time = data[u'ID']
        Installation_Time = data[u'IN']
        Maintenance_Time = data[u'MA']


        total_percent = InUse_Time + Idle_Time + Maintenance_Time + Installation_Time + 0.001

        InUse_Time = (InUse_Time/total_percent)*100
        Idle_Time = (Idle_Time/total_percent)*100
        Maintenance_Time = (Maintenance_Time/total_percent)*100
        Installation_Time = (Installation_Time/total_percent)*100
        print tool.name
        print tool.tool_category
        #print tool.tool_category.percentage
        print InUse_Time
        print start_date
        print today
        if tool.tool_category is not None:
            if InUse_Time >= tool.tool_category.percentage:
                tool_efficiency = True
            else:
                tool_efficiency = False

            time = {"Tool_Name":tool.name,
                    "Tool_Category":tool.tool_category.category_name, 
                    "Productive":InUse_Time,
		            "Bay_number":tool.bay_number,
		            "Bay":tool.bay.name,
                    "Tool_Threshold" :tool.tool_category.percentage,
                    "Tool_start_date": start_date,
                    #"Bay_Assigned_date" :start_date,
                    "Tool_efficiency" :tool_efficiency }
        return Response(time)


    def tool_utilization_quarterly_list(self, request, bid=None, start_date=None, end_date=None):
        today_date = timezone.now()
        today_date = today_date.replace(month=5,day=1)
 	cfirst_date = today_date
        time_zone = pytz.timezone(settings.TIME_ZONE)
        pfirst_date = cfirst_date.strftime('%Y-%m-%d')
	pstart_date = pfirst_date
        #pstart_date = time_zone.localize(datetime.datetime.strptime(pfirst_date,'%Y-%m-%d'))
        today_date = today_date.replace(month=7,day=31)
        today_date = today_date.strftime('%Y-%m-%d')
	pend_date = today_date
        today_date = timezone.now()
        if request.GET.get("start_date"):
            time_zone = pytz.timezone(settings.TIME_ZONE)
            start_time_str = request.GET.get("start_date",None)
            start_date = time_zone.localize(datetime.datetime.strptime(start_time_str,'%Y-%m-%d'))
            start_date = start_date
        else:
            presentmonth = today_date.month
            if (presentmonth >=2 ) and ( presentmonth <= 4 ):
                today_date = today_date.replace(month=2,day=1)
            elif (presentmonth >=5 ) and ( presentmonth <= 7 ):
                today_date = today_date.replace(month=5,day=1)
            elif (presentmonth >=8 ) and ( presentmonth <= 10 ):
                today_date = today_date.replace(month=8,day=1)
            elif (presentmonth >=11 ) and ( presentmonth <= 1 ):
                today_date = today_date.replace(month=11,day=1)
 	    first_date = today_date
            time_zone = pytz.timezone(settings.TIME_ZONE)
            first_date = first_date.strftime('%Y-%m-%d')
            start_date = time_zone.localize(datetime.datetime.strptime(first_date,'%Y-%m-%d'))
            #start_date = None
        if request.GET.get("end_date"):
            time_zone = pytz.timezone(settings.TIME_ZONE)
            end_date_str = request.GET.get("end_date",None)
            end_date = time_zone.localize(datetime.datetime.strptime(end_date_str,'%Y-%m-%d'))
            today = end_date + datetime.timedelta(1)
        else:
            today = timezone.now()
            #end_date = None

        #today = timezone.now()
        #start_date = datetime.date.today()
        #start_date = start_date.replace(month = 2,day=18)
        #time_zone = pytz.timezone(settings.TIME_ZONE)
        #first_date = start_date.strftime('%Y-%m-%d')
        #start_date = time_zone.localize(datetime.datetime.strptime(first_date,'%Y-%m-%d'))
    #pk = Tool.objects.get(bay_number=pk).id
        time_list = []
        tools = Tool.objects.all()

        for tool in tools:
            print tool.name
	    #time1 = utilization(tool_id=tool.id,start_date,end_date)
	    time1 = utilization(tool.id,start_date,today)
            InUse_Time = time1["InUse_percent"]
	    print tool.name, "Printing tool name"
           # print tool.tool_category.category_name, "Printing tool category name"
	    print tool.tool_category, "printing tool category"
            print InUse_Time
            print start_date
            #print today
            if tool.tool_category is not None:
                if InUse_Time >= tool.tool_category.percentage:
                    tool_efficiency = True
                else:
                    tool_efficiency = False

                time = {"Tool_Name":tool.name,
                        "Tool_Category":tool.tool_category.category_name, 
                        "Productive":InUse_Time,
                        "Tool_Threshold" :tool.tool_category.percentage,
                        "Tool_efficiency" :tool_efficiency,
                        "Bay_number" :tool.bay_number,
                        "Bay": tool.bay.name,
                        #"Bay_Assigned_date": pfirst_date,

                        "Tool_start_date":start_date,

			#"Tool_Owner": tool.tool_owner.email
			#"Tool_Owner": tool.tool_owner.first_name tool.tool_owner.last_name
			"Tfirst_name": tool.tool_owner.first_name,
			"Tlast_name": tool.tool_owner.last_name,
			"Qstart_date": pstart_date,
			"Qend_date": pend_date,
            #"Start_Date"
		}
                print time, "XXXX"
                time_list.append(time)
                print time_list, "Printing time list"
        return Response(time_list)

    # Added for Angular5 cpu apr 21 2018

class TestToolsView(viewsets.ModelViewSet):
    serializer_class = TestToolSerializer
    queryset = Tool.objects.all()


    def create(self, request, *args, **kwargs):
        print request.data
        print request.data['bay'], "printing bay id"
        tool_count = Tool.objects.filter(bay=request.data['bay']).count()
        print tool_count, "Print tool_count"
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        print request.data, "printing request"
        if tool_count < 6:
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def perform_create(self, serializer):
        serializer.save()
    # def update(self, request, *args, **kwargs):
    #     partial = kwargs.pop('partial', False)
    #     instance = self.get_object()
    #     serializer = self.get_serializer(instance, data=request.data, partial=partial)
    #     serializer.is_valid(raise_exception=True)
    #     self.perform_update(serializer)
    #
    #     if getattr(instance, '_prefetched_objects_cache', None):
    #         # If 'prefetch_related' has been applied to a queryset, we need to
    #         # forcibly invalidate the prefetch cache on the instance.
    #         instance._prefetched_objects_cache = {}
    #
    #     return Response(serializer.data)
    #
    # def perform_update(self, serializer):
    #     serializer.save()
    #
    # def partial_update(self, request, *args, **kwargs):
    #     kwargs['partial'] = True
    #     return self.update(request, *args, **kwargs)


class GetConsoles(ListAPIView):
    queryset = Bay.objects.all()
    serializer_class= ConsoleSerializer


class GetTools(ListAPIView):
    queryset = Tool.objects.all()
    serializer_class = Tool2Serializer


# @api_view(['GET'])
# def getToolOwners(request):
#     b = BayUser.objects.all()
#     data = []
#     for x in b:
#         print x.get_mix_name()
#     # full =  b.get_mix_name()
#
#         data.append(x.get_mix_name())
#         # data = {'full_name': full}
#     print 'full',data
#     return  Response(data, status=200)


class GetToolOwners(ListAPIView):
    queryset = BayUser.objects.all()
    serializer_class = BayUserSerializer


class GetToolCategory(ListAPIView):
    queryset = ToolCategory.objects.all()
    serializer_class = ToolCategorySerializer1


@api_view(['POST'])
def addTools(request):
    print request.data
    serializer = AddToolSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response('data saved', status=status.HTTP_200_OK)
    else:
        return Response('save failed', status=status.HTTP_200_OK)


@api_view(['PUT'])
def tool_image_update(request):
    print 'file data',request.data['file'].content_type
    if 'file' in request.data:

        name = request.data['name']
        print 'zzzzzzz',name
        # request.data[name] = request.data['file']
        print 'yyyyyyyy', request.data['file']
        if request.data['file'].content_type == 'image/png':
            print "IS AN IMAGE",request.data['file']
            # imagedata = Tool.objects.filter(image = request.data['file'])
            serializer = AddImageSerializer(data=request.data['file'])
            if serializer.is_valid():
                serializer.save()
                data = "Successfully updated"
                resp = {"response": data}
                return Response(resp, status=status.HTTP_200_OK)
            else:
                data = "failed to upload image"
                print serializer.errors
                resp = {"response": data}
                return Response("failed to save", status=status.HTTP_400_BAD_REQUEST)


class UpdateBay(UpdateAPIView):
    queryset = Bay.objects.all()
    serializer_class= BayUpdateSerializer


class DeleteBay(RetrieveUpdateDestroyAPIView):
    queryset = Bay.objects.all()
    serializer_class = BayUpdateSerializer


class GetProjects(ListAPIView):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer

@api_view(['POST'])
def saveNewTools(request):
    print "saved data", request.data
    ui_data = request.data
    # Tool.objects.filter(bay = ui_data['bay'])
    # console_count = Tool.objects.filter(bay=ui_data['bay']).count()
    console_count = Tool.objects.filter(bay=ui_data['bay'], is_active=True).count()
    check_bay = Tool.objects.filter(bay_number=ui_data['bay_number'])
    if (ui_data['bay'] == 257) and (ui_data['is_active'] == False):
        print 'INSIDE NULL CONSOLE'
        if check_bay:
            print 'ALREADY BAY EXIST'
            return Response("Bay number already exists", status=status.HTTP_200_OK)
        else:
            serializer = NewToolSerializer(data=request.data)
            if serializer.is_valid():
                print 'VALID SERIALIZER'
                serializer.save()
                return Response("Successfully added to Null", status=status.HTTP_200_OK)
            else:
                return Response("Failed to add", status=status.HTTP_200_OK)
    else:
        if console_count == 6:
            print "COUNT IS 6--FULL"
            return Response("Console is already full", status=status.HTTP_200_OK)
        else:
            if ui_data['is_active'] == True:
                if check_bay:
                    print 'ALREADY BAY EXIST'
                    return Response("Bay number already exists", status=status.HTTP_200_OK)
                else:
                    serializer = NewToolSerializer(data=request.data)
                    if serializer.is_valid():
                        print 'VALID SERIALIZER'
                        serializer.save()
                        return Response("Successfully added", status=status.HTTP_200_OK)
                    else:
                        return Response("Failed to add", status=status.HTTP_200_OK)
            else:
                return Response("Failed to add since is_active is false", status=status.HTTP_200_OK)

                # b = Tool.objects.values('bay')
                # c = Tool.objects.filter(is_active = "True")
                # for x in b:
                #     print "bayssss", x['bay']
                #     nbr = x['bay']

#
# @api_view(['PUT'])
# def tool_image_update(request):
#     print 'file data',request.data['file'].content_type
#     if 'file' in request.data:
#
#         name = request.data['name']
#         print 'zzzzzzz',name
#         # request.data[name] = request.data['file']
#         print 'yyyyyyyy', request.data['file']
#         if request.data['file'].content_type == 'image/png':
#             print "IS AN IMAGE",request.data['file']
#             # imagedata = Tool.objects.filter(image = request.data['file'])
#             serializer = AddImageSerializer(data=request.data['file'])
#             if serializer.is_valid():
#                 serializer.save()
#                 data = "Successfully updated"
#                 resp = {"response": data}
#                 return Response(resp, status=status.HTTP_200_OK)
#             else:
#                 data = "failed to upload image"
#                 print serializer.errors
#                 resp = {"response": data}
#                 return Response("failed to save", status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT'])
def move_tools(request):
    print request.data
    front_data = request.data
    T = Tool.objects.get(id = front_data['id'])
    print 'CONSOLE NUMBER',front_data['bay']
    print 'FRONTDATA ID',front_data['id']
    print 'FRONTDATA BAY',front_data['bay']
    print 'FULL ROW',T.name
    if front_data['bay'] == 257:
        print 'INSIDE NULL CONSOLE'
        serializer = MoveToolSerializer(T, request.data)
        if serializer.is_valid():
            print 'VALID SERIALIZER'
            serializer.save()
            return Response("successfully updated", status=status.HTTP_200_OK)
        else:
            return Response("failed to update", status=status.HTTP_200_OK)
    else:
        console_count = Tool.objects.filter(bay = front_data['bay']).count()
        print 'CONSOLE COUNT',console_count
        if console_count >= 6:
            print 'CONSOLE IS FULL'
            return Response("Console is already full", status=status.HTTP_200_OK)
        else:
            serializer = MoveToolSerializer(T, request.data)
            if serializer.is_valid():
                serializer.save()
                return Response("updated successfully", status=status.HTTP_200_OK)
            else:
                return Response("failed to update", status=status.HTTP_200_OK)

@api_view(['PUT'])
def swapTools(request):
    print request.data
    ui_data = request.data
    print 'too1',ui_data['too1']
    tool1 = ui_data['too1']
    tool2 = ui_data['too2']

   # print 'TOOL2 ID', tool2['id']
    T1 = Tool.objects.get(id=tool1['id'])
    T2 = Tool.objects.get(id=tool2['id'])
   # print "T1OBJECT",T1.bay, T1.tool_users
    serializer1 = SwapToolSerializer(T1, request.data)
    serializer2 = SwapToolSerializer(T2, request.data)
    #swap = serializer1
    #serializer1 = serializer2
    #serializer2 = swap
    if serializer1.is_valid() and serializer2.is_valid():
        print 'VALID SERIALIZER1'
        serializer1.save()
        serializer2.save()
        print serializer1
        return Response("successfully updated", status=status.HTTP_200_OK)
    else:
         # print serializer1.errors
         print serializer1.errors
         print serializer2.errors
         return Response("failed to update1", status=status.HTTP_200_OK)
    # T2 = Tool.objects.get(id=tool2['id'])
    # serializer2 = SwapToolSerializer(T2. request.data)
    # if serializer2.is_valid():
    #     print 'VALID SERIALIZER2'
    #     serializer2.save()
    #     return Response("successfully updated", status=status.HTTP_200_OK)
    # else:
    #     return Response("failed to update2", status=status.HTTP_200_OK)




@api_view(['PUT'])
def changeStatus(request):
    print request.data
    front_id = request.data
    tool = Tool.objects.get(id = front_id['id'])
    serializer = ChangeStatusSerializer1(tool, request.data)
    if serializer.is_valid():
        print 'VALID SERIALIZER'
        serializer.save()
        return Response("successfully updated", status=status.HTTP_200_OK)
    else:
        return Response("failed to update", status=status.HTTP_200_OK)


@api_view(['PUT'])
def tool_image_upload(request):
    print request.data
    print request.data['id']
    img_id = request.data
    toolimage = Tool.objects.get(bay_number = img_id['id'])
    print 'TOOLOBJ',toolimage
    serializer = ImageOnlySerializer(toolimage, request.data)
    # print serializer
    if serializer.is_valid():
        serializer.save()
        return Response("Successfully uploaded", status=status.HTTP_200_OK)
    else:
        return Response('Failed to upload!.......Please upload a vaild image', status=status.HTTP_200_OK)

