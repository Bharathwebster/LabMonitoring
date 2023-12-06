from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.views import APIView
from bay.models import Bay, Tool, Project, ToolProject, ToolImage, Logging
from users.models import BayUser
from bay.serializers import BaySerializer, ToolSerializer , ProjectSerializer, ToolProjectSerializer,ToolImageSerializer, LoggingSerializer
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import list_route, detail_route
from users.serializers import BayUserSerializer, GroupSerializer
from django.http import HttpResponse
from django.utils import timezone

import xlwt
import datetime
import pytz
from django.conf import settings


from rest_framework.permissions import BasePermission
from rest_framework.permissions import IsAuthenticated, AllowAny
from easy_pdf.views import PDFTemplateView

class AddToolPermission(BasePermission):

    def has_permission(self, request, view):
        try:
            bid = int(view.kwargs.get('bid'))
            bay_obj = Bay.objects.get(id=bid)
            if bay_obj.tool_set.count() >=6:
                return False
        except:
            return True
        return True

def home(request):
    return render(request, 'home.html')


class ToolViewSet(viewsets.ModelViewSet):
    queryset = Tool.objects.all()
    serializer_class = ToolSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [AddToolPermission()]
        else:
            return [AllowAny(),]

    def get_serializer_context(self):
        return {'request': self.request}

    def get_queryset(self):
        if self.kwargs.has_key('bid'):
            return Tool.objects.filter(bay_id=self.kwargs['bid']).order_by('-created_on')
        # employee = Employee.objects.get(user__id=int(self.kwargs['uid']))
        return Tool.objects.all().order_by('-created_on')

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
        serializer = self.get_serializer(self.get_object(),
                                         data=request.data, partial=True)
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
            Tool.objects.filter(id__in=tool_ids).delete()
            return Response({'status':'Deleted'}, status=status.HTTP_200_OK)
        else:
            return Response({'status':'No tool ids'}, status=status.HTTP_200_OK)

    @detail_route(methods=['post','get'], url_path='utilization')
    def utilization(self, request,bid=None, pk=None):
        ToolUtil = Logging.objects.filter(tool_id=pk).order_by('created_on')
        tool = Tool.objects.get(id=pk)
        today = timezone.now()
        start_date = tool.created_on
        total_seconds = ((today - start_date).total_seconds())
        InUse_Time = 0
        Idle_Time = (ToolUtil.first().created_on - tool.created_on).total_seconds() if ToolUtil else 0
        Maintenance_Time = 0
        Installation_Time = 0
        requested_time = int(request.query_params.get("hours", 8))
        total_seconds_day = requested_time * 60 * 60
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
        time = {"Productive":InUse_Time,"Idle":Idle_Time,"Maintenance":Maintenance_Time,"Installation":Installation_Time}
        return Response(time)



    @detail_route(methods=['post','get'], url_path='user_utilization')
    def user_utilization(self, request,bid=None, pk=None):
        tool = Tool.objects.get(id=pk)
        users= tool.tool_users.all()
        response_data = []
        for user in users:
            ToolUtil = Logging.objects.filter(tool_id=pk,user=user).order_by('created_on')
            # today = timezone.now()
            # start_date = tool.created_on
            # total_seconds = (today - start_date).total_seconds()
            InUse_Time = 0
            Idle_Time = 0
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
            except:
                pass
            utilization = InUse_Time + Idle_Time + Installation_Time + Maintenance_Time
            utilzation_data= {}
            utilzation_data['first_name'] = user.first_name
            utilzation_data['last_name'] = user.last_name
            utilzation_data['utilization'] = utilization/3600
            response_data.append(utilzation_data)
            
        return Response(response_data)
  
    @detail_route(methods=['post','get'], url_path='project_utilization')
    def project_utilization(self, request,bid=None, pk=None):
        tool = Tool.objects.get(id=pk)
        projects = tool.projects.all()
        response_data = []
        for project in projects:
            ToolUtil = Logging.objects.filter(tool_id=pk,project=project).order_by('created_on')
            # today = timezone.now()
            # start_date = tool.created_on
            # total_seconds = (today - start_date).total_seconds()
            InUse_Time = 0
            Idle_Time = 0
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
            except:
                pass
            utilization = InUse_Time + Idle_Time + Installation_Time + Maintenance_Time
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
            ToolUtil = Logging.objects.filter(tool_id=tool.id).order_by('created_on')
            today = timezone.now()
            start_date = tool.created_on
            total_seconds = ((today - start_date).total_seconds())
            InUse_Time = 0
            Idle_Time = (ToolUtil.first().created_on - tool.created_on).total_seconds() if ToolUtil else 0
            Maintenance_Time = 0
            Installation_Time = 0
            requested_time = int(request.query_params.get("hours", 8))
            total_seconds_day = requested_time * 60 * 60
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
            total_inuse += InUse_Time 
            total_idle += Idle_Time 
            total_installation += Installation_Time 
            total_maintenance += Maintenance_Time
            # tool_total_seconds = InUse_Time + Idle_Time + Installation_Time + total_maintenance
            total_seconds_console += total_seconds 

        print "---------------------", total_inuse

        InUse_Time = (total_inuse/total_seconds_console)*100
        Idle_Time = (total_idle/total_seconds_console)*100
        Installation_Time = (total_installation/total_seconds_console)*100
        Maintenance_Time = (total_maintenance/total_seconds_console)*100
        Idle_Time = 100 - (InUse_Time+Installation_Time+Maintenance_Time)
        time = {"Productive_Time":InUse_Time,"Idle_Time":Idle_Time,"Maintenance_Time":Maintenance_Time,"Installation_Time":Installation_Time}
        return Response(time)


    @list_route(methods=['get','put','delete'], url_path='monthlylab_utilization')
    def monthlylab_utilization(self, request, *args, **kwargs):
        tools = Tool.objects.all()
        total_inuse = 0
        total_idle = 0
        total_installation = 0
        total_maintenance = 0
        total_seconds_console = 0
        for tool in tools:
            
            today = timezone.now()
            end_date = today
            today_date = datetime.date.today()
            if today_date.day > 25:
                today_date += datetime.timedelta(7)
            first_date = today_date.replace(day=1)
            time_zone = pytz.timezone(settings.TIME_ZONE)
            first_date = first_date.strftime('%Y-%m-%d')
            start_date = time_zone.localize(datetime.datetime.strptime(first_date,'%Y-%m-%d'))
            ToolUtil = Logging.objects.filter(tool_id=tool.id,created_on__gte = start_date, created_on__lte= end_date ).order_by('created_on')
            total_seconds = ((today - start_date).total_seconds())
            InUse_Time = 0
            Idle_Time = (ToolUtil.first().created_on - start_date).total_seconds() if ToolUtil else 0
            Maintenance_Time = 0
            Installation_Time = 0
            requested_time = int(request.query_params.get("hours", 8))
            total_seconds_day = requested_time * 60 * 60
            try:
                Total_Time = 0
                Last = (len(ToolUtil)) - 1
                Last_Time = ToolUtil[Last].created_on
                Start_Time = ToolUtil[0].created_on
                Status = ""
                for i in range(0,len(ToolUtil)-1):
                    Status = ToolUtil[i].status
                    TimeDiff = ToolUtil[i+1].created_on - ToolUtil[i].created_on
                    
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
            if len(ToolUtil) == 0:
                #Idle_Time = total_seconds
                if(tool.status == "PR"):
                    InUse_Time = total_seconds
                elif(tool.status == "ID"):
                    Idle_Time = total_seconds
                elif(tool.status == "IN"):
                    Installation_Time = total_seconds
                else:
                    Maintenance_Time = total_seconds

            total_inuse += InUse_Time
            total_idle += Idle_Time 
            total_installation += Installation_Time 
            total_maintenance += Maintenance_Time
            print total_inuse+ total_idle + total_installation + total_maintenance
            print total_seconds_console
            # tool_total_seconds = InUse_Time + Idle_Time + Installation_Time + total_maintenance
            total_seconds_console += total_seconds

        print "---------------------", total_inuse

        InUse_Time = (total_inuse/total_seconds_console)*100
        Idle_Time = (total_idle/total_seconds_console)*100
        Installation_Time = (total_installation/total_seconds_console)*100
        Maintenance_Time = (total_maintenance/total_seconds_console)*100
        Idle_Time = 100 - (InUse_Time+Installation_Time+Maintenance_Time)
        time = {"Productive_Time":InUse_Time,"Idle_Time":Idle_Time,"Maintenance_Time":Maintenance_Time,"Installation_Time":Installation_Time}
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
            start_date = time_zone.localize(datetime.datetime.strptime('2017-3-1','%Y-%m-%d'))
        try:
            time_zone = pytz.timezone(settings.TIME_ZONE)
            end_date_str = request.GET.get("end_date", None)
            end_date = time_zone.localize(datetime.datetime.strptime(end_date_str,'%Y-%m-%d'))
        except:
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
        return Response({'trend':trend_data}, status=status.HTTP_200_OK)




class BayViewSet(viewsets.ModelViewSet):
    queryset = Bay.objects.all().order_by('-created_on')
    serializer_class = BaySerializer

    def create(self, request, *args, **kwargs):
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
        data = {}
        user = BayUser.objects.get(rfid =rfid)
        data['user'] = BayUserSerializer(user).data
        data['bay_id'] = Bay.objects.get(mac_id=mac_id).id
        return Response(data, status=status.HTTP_200_OK)

    @list_route(methods=['get','put','delete'], url_path='delete')
    def bay_delete(self, request, *args, **kwargs):
        bay_ids = request.data.get('bay_ids')
        if bay_ids:
            Bay.objects.filter(id__in=bay_ids).delete()
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
            Project.objects.filter(id__in=project_ids).delete()
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

def utilization(request):
    tool_id = request.GET.get('tool-id' )
    ToolUtil = Logging.objects.filter(tool_id=tool_id).order_by('created_on')
    InUse_Time = 0
    Idle_Time = 0
    Installation_Time = 0
    Maintenance_Time = 0

    Total_Time = 0
    Last = (len(ToolUtil)) - 1
    Last_Time = ToolUtil[Last].created_on
    Start_Time = ToolUtil[0].created_on
    Epoch = datetime.datetime(1970,1,1)

    print str(Start_Time)
    print str(Last_Time)
    print str(Last_Time-Start_Time)

    Status = ""
    for i in range(0,len(ToolUtil)-1):
        print "yessssssssssssss"
        Status = ToolUtil[i].status
        TimeDiff = ToolUtil[i+1].created_on - ToolUtil[i].created_on
        print TimeDiff
        if(Status == "PR"):
            InUse_Time = InUse_Time + TimeDiff.total_seconds() 
        elif(Status == "ID"):
            Idle_Time = Idle_Time + TimeDiff.total_seconds()
        elif(Status == "IN"):
            Installation_Time = Installation_Time + TimeDiff.total_seconds()
        else:
            Maintenance_Time = Maintenance_Time + TimeDiff.total_seconds() 

    time = {"InUse_Time":InUse_Time,"Idle_Time":Idle_Time,"Maintenance_Time":Maintenance_Time,"Installation_Time":Installation_Time}
    print time
    return HttpResponse(time)

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


def export_console_xls(request):
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename=Console.xls'
    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet("Console Report")
    
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
    for obj in queryset:
        row_num += 1
        row = [
            obj.name,
            obj.mac_id,
            len(obj.tool_set.all()),
            obj.created_on.strftime('%Y-%m-%d %H:%M'),
            obj.is_active,
        ]
        for col_num in xrange(len(row)):
            ws.write(row_num, col_num, row[col_num], font_style)
            
    wb.save(response)
    return response 


def utilization(tool_id, start_date=None,end_date=None):
    end_date = end_date 
    tool_id = tool_id
    tool = Tool.objects.get(id=tool_id)
    start_date = start_date if start_date else tool.created_on
    today = end_date
    ToolUtil = Logging.objects.filter(created_on__gte=start_date, created_on__lte=end_date, tool_id=tool_id).order_by('created_on')
    #today = timezone.now()
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
	
#        status = ToolUtil.last().status
#        remain_time = (today - ToolUtil.last().created_on).total_seconds()
#        if(status == "PR"):
#            InUse_Time += remain_time
#        elif(status == "ID"):
#            Idle_Time += remain_time 
#        elif(status == "IN"):
#            Installation_Time += remain_time
#        else:
#            Maintenance_Time += remain_time
    except:
        pass
    if len(ToolUtil) ==0:
        #Idle_Time = total_seconds
	obj = Logging.objects.filter(created_on__lt=start_date, tool_id =tool.id).order_by('created_on')
	tool = obj.last()
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
    # Idle_Time = 100 - (InUse_Time+Installation_Time+Maintenance_Time)
    
    total_percent = InUse_Time + Idle_Time + Maintenance_Time + Installation_Time
    print "Total percent %s" %(total_percent)
    InUse_percent = (InUse_Time/total_percent)*100
    Idle_percent = (Idle_Time/total_percent)*100
    Maintenance_percent = (Maintenance_Time/total_percent)*100
    Installation_percent = (Installation_Time/total_percent)*100
    #Installation_percent = 5.7182

    time = {"InUse_Time":InUse_Time,"Idle_Time":Idle_Time,"Maintenance_Time":Maintenance_Time,"Installation_Time":Installation_Time,"InUse_percent":InUse_percent,"Idle_percent":Idle_percent,"Maintenance_percent":Maintenance_percent,"Installation_percent":Installation_percent}    
    return time


def utilization_RT(tool_id, start_date=None,end_date=None):             # Real Time Report
    end_date = end_date 
    tool_id = tool_id
    tool = Tool.objects.get(id=tool_id)
    start_date = start_date if start_date else tool.created_on
    today = end_date
    ToolUtil = Logging.objects.filter(created_on__gte=start_date, created_on__lte=end_date, tool_id=tool_id).order_by('created_on')
    #today = timezone.now()
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
    # Idle_Time = 100 - (InUse_Time+Installation_Time+Maintenance_Time)
    
    total_percent = InUse_Time + Idle_Time + Maintenance_Time + Installation_Time
    print "Total percent %s" %(total_percent)
    InUse_percent = (InUse_Time/total_percent)*100
    Idle_percent = (Idle_Time/total_percent)*100
    Maintenance_percent = (Maintenance_Time/total_percent)*100
    Installation_percent = (Installation_Time/total_percent)*100

    time = {"InUse_Time":InUse_Time,"Idle_Time":Idle_Time,"Maintenance_Time":Maintenance_Time,"Installation_Time":Installation_Time,"InUse_percent":InUse_percent,"Idle_percent":Idle_percent,"Maintenance_percent":Maintenance_percent,"Installation_percent":Installation_percent}    
    return time


def export_tool_xls(request):
    try:
        time_zone = pytz.timezone(settings.TIME_ZONE)
        start_time_str = request.GET.get("start_date",None)
        start_date = time_zone.localize(datetime.datetime.strptime(start_time_str,'%Y-%m-%d'))
        start_date = start_date 
        filename = 'Tools_'+timezone.now().strftime("%Y_%m_%d_%H_%M")+'.xls'
    except:
        start_date = None
        filename = 'RealTimeData__'+timezone.now().strftime("%Y_%m_%d_%H_%M")+'.xls'
    try:
        time_zone = pytz.timezone(settings.TIME_ZONE)
        end_date_str = request.GET.get("end_date",None)
        end_date = time_zone.localize(datetime.datetime.strptime(end_date_str,'%Y-%m-%d'))
        end_date = end_date + datetime.timedelta(1)
    except:
        end_date = timezone.now()

    today = timezone.now()
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename='+filename
    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet("Tools Report")
    
    row_num = 0
    
    columns = [
        (u"Tool Name", 2000),
        (u"Console Name", 6000),
        (u"Bay Number", 8000),
        (u"Number of project assigned", 8000),
        (u"Number of user assigned", 8000),
        (u"Current Project", 8000),
        (u"Current Status", 8000),
        (u"Bay Start date", 8000),
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
    
    queryset = Tool.objects.all()

    for obj in queryset:
	if start_date == None:
	        time  = utilization_RT(obj.id, start_date, end_date)
	else:
		time = utilization(obj.id,start_date,end_date)
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
            ws.write(row_num, col_num, row[col_num], font_style)
            
    wb.save(response)
    return response 

def project_utilization(project, start_date=None,end_date=None):
    #tool_id = tool_id
    #tool = Tool.objects.get(id=tool_id)
    #start_date = start_date if start_date else tool.created_on
    end_date = end_date 
    today = end_date
    ToolUtil = Logging.objects.filter(created_on__gte=start_date, created_on__lte=end_date, project=project).order_by('created_on')
    #today = timezone.now()
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
    '''if len(ToolUtil) ==0:
        #Idle_Time = total_seconds
	obj = Logging.objects.filter(created_on__lt=start_date, tool_id =tool.id).order_by('created_on') #added cpu
	tool = obj.last() #added cpu
        if(tool.status == "PR"):
            InUse_Time = total_seconds
        elif(tool.status == "ID"):
            Idle_Time = total_seconds
        elif(tool.status == "IN"):
            Installation_Time = total_seconds
        else:
            Maintenance_Time = total_seconds'''

    print "---------------------->", total_seconds, start_date
    print "---------------------->", InUse_Time
    print "---------------------->", Idle_Time
    print "---------------------->", Installation_Time
    print "---------------------->", Maintenance_Time
    InUse_Time = (InUse_Time/3600)
    Idle_Time = (Idle_Time/3600)
    Installation_Time = (Installation_Time/3600)
    Maintenance_Time = (Maintenance_Time/3600)

    utilization = InUse_Time + Installation_Time

    return utilization



def export_project_xls(request):
    try:
        time_zone = pytz.timezone(settings.TIME_ZONE)
        start_time_str = request.GET.get("start_date",None)
        start_date = time_zone.localize(datetime.datetime.strptime(start_time_str,'%Y-%m-%d'))
    except:
        start_date = time_zone.localize(datetime.datetime.strptime('2017-3-1','%Y-%m-%d'))
    try:
        time_zone = pytz.timezone(settings.TIME_ZONE)
        end_date_str = request.GET.get("end_date",None)
        end_date = time_zone.localize(datetime.datetime.strptime(end_date_str,'%Y-%m-%d'))
        end_date = end_date+datetime.timedelta(1)
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
        (u"Tool utilization in hours", 8000),


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
        utilization += project_utilization(obj,start_date,end_date)
        row_num += 1
        row = [
            obj.name,
            
            str(obj.ToolProject.all().values_list('name',flat=True)),

            len(obj.users.all()),
            start_date.strftime('%Y-%m-%d %H:%M') if start_date else obj.created_on.strftime('%Y-%m-%d %H:%M'),
            end_date.strftime('%Y-%m-%d %H:%M'),

            utilization,
        ]
        for col_num in xrange(len(row)):
            ws.write(row_num, col_num, row[col_num], font_style)
            
    wb.save(response)
    return response      

def user_utilization(tool_id, user, start_date=None,end_date=None):
    end_date = end_date
    tool_id = tool_id
    tool = Tool.objects.get(id=tool_id)
    start_date = start_date if start_date else tool.created_on
    today = end_date
    ToolUtil = Logging.objects.filter(created_on__gte=start_date, created_on__lte=end_date, tool_id=tool_id, user=user).order_by('created_on')
    #today = timezone.now()
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
    '''if len(ToolUtil) ==0:
        #Idle_Time = total_seconds
        if(tool.status == "PR"):
            InUse_Time = total_seconds
        elif(tool.status == "ID"):
            Idle_Time = total_seconds
        elif(tool.status == "IN"):
            Installation_Time = total_seconds
        else:
            Maintenance_Time = total_seconds'''

    print "---------------------->", total_seconds, start_date
    print "---------------------->", InUse_Time
    print "---------------------->", Idle_Time
    print "---------------------->", Installation_Time
    print "---------------------->", Maintenance_Time
    InUse_Time = (InUse_Time/3600)
    Idle_Time = (Idle_Time/3600)
    Installation_Time = (Installation_Time/3600)
    Maintenance_Time = (Maintenance_Time/3600)

    utilization = InUse_Time + Installation_Time

    return utilization

def export_user_xls(request):
    try:
        time_zone = pytz.timezone(settings.TIME_ZONE)
        start_time_str = request.GET.get("start_date",None)
        start_date = time_zone.localize(datetime.datetime.strptime(start_time_str,'%Y-%m-%d'))
    except:
        start_date = None
    try:
        time_zone = pytz.timezone(settings.TIME_ZONE)
        end_date_str = request.GET.get("end_date",None)
        end_date = time_zone.localize(datetime.datetime.strptime(end_date_str,'%Y-%m-%d'))
        end_date = end_date+datetime.timedelta(1)
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
        (u"Start Date", 8000),
        (u"End Date", 8000),
        (u"Number of Projects", 8000),
        (u"Number of Tools assigned", 8000),
        
        (u"Tool Utilization in hour", 8000),


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
        utilization = 0
        for tool in obj.ToolUser.all():
	    utilization += user_utilization(tool.id,obj,start_date,end_date)
        row_num += 1
        row = [
            obj.first_name,
            obj.last_name,
            obj.rfid,
            obj.is_active,
            start_date.strftime('%Y-%m-%d %H:%M') if start_date else obj.created_on.strftime('%Y-%m-%d %H:%M'),
            end_date.strftime('%Y-%m-%d %H:%M'),
            len(obj.project_set.all()),
            len(obj.ToolUser.all()),
            
            utilization
        ]
        for col_num in xrange(len(row)):
            ws.write(row_num, col_num, row[col_num], font_style)
            
    wb.save(response)
    return response


def export_user_raw_xls(request):
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
        end_date = end_date + datetime.timedelta(1)
    except:
        end_date = None

    out = []
    tool = Tool.objects.all()
    val_tool = len(tool)
    print val_tool
    tool_cnt = 0
    for pk_val in tool:
        if start_date==None:
		result = valid_date(pk_val)
	else:
		result = valid_date(pk_val,start_date,end_date)		
        tool_cnt += 1      
        for i in range(0,len(result)):
           
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

    return Response({'trend':out}, status=status.HTTP_200_OK)






def tools_report(request,tool_id):
    try:
        time_zone = pytz.timezone(settings.TIME_ZONE)
        start_time_str = request.GET.get("start_date",None)
       
        start_date = time_zone.localize(datetime.datetime.strptime(start_time_str,'%Y-%m-%d'))
        start_date = start_date

        filename = 'Tools_report'+timezone.now().strftime("%Y_%m_%d_%H_%M")+'.xls'
    except:
        start_date =time_zone.localize(datetime.datetime.strptime('2017-3-1','%Y-%m-%d'))
        
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
    date_range = (end_date - start_date).days
    print date_range
    for obj in range(0,date_range):
        start = start_date + datetime.timedelta(obj)
        end = start_date + datetime.timedelta(obj+1)

        time  = utilization(queryset.id, start, end)
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




@api_view(('GET',))
def api_test(request):
    """
            api for lab trends overall
    """
    return Response({'message':"hello"})
