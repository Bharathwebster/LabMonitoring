import xlwt
import datetime
from django.contrib import admin
from django.http import HttpResponse
from bay.models import Bay, Tool, Logging, Project , ToolCategory
from users.models import BayUser

def utilization(tool_id):
    tool_id = tool_id
    ToolUtil = Logging.objects.filter(tool_id=tool_id).order_by('created_on')
    if ToolUtil:
        InUse_Time = 0
        Idle_Time = 0
        Maintenance_Time = 0
        Installation_Time = 0

        Total_Time = 0
        Last = (len(ToolUtil)) - 1
        Last_Time = ToolUtil[Last].created_on
        Start_Time = ToolUtil[0].created_on
        Epoch = datetime.datetime(1970,1,1)

        Status = ""
        for i in range(0,len(ToolUtil)-1):
            Status = ToolUtil[i].status
            TimeDiff = ToolUtil[i+1].created_on - ToolUtil[i].created_on
            if(Status == "PR"):
                InUse_Time = InUse_Time + TimeDiff.total_seconds() 
            elif(Status == "ID"):
                Idle_Time = Idle_Time + TimeDiff.total_seconds()
            elif(Status == "IN"):
                Installation_Time = Installation_Time + TimeDiff.total_seconds()
            else:
                Maintenance_Time = Maintenance_Time + TimeDiff.total_seconds() 

        time = {"InUse_Time":InUse_Time,"Idle_Time":Idle_Time,"Maintenance_Time":Maintenance_Time,'Installation_Time':Installation_Time}
        return time

def export_console_xls(modeladmin, request, queryset):
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
    
export_console_xls.short_description = u"Export Console XLS"

class ConsoleAdmin(admin.ModelAdmin):
    actions = [export_console_xls]


def export_tool_xls(modeladmin, request, queryset):
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename=Tools.xls'
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
        (u"Production Time in hours", 8000),
        (u"Maintenance Time in hours", 8000),
        (u"Idle Time in hours", 8000),
        (u"Installation Time in hours", 8000),
    ]

    font_style = xlwt.XFStyle()
    font_style.font.bold = True

    for col_num in xrange(len(columns)):
        ws.write(row_num, col_num, columns[col_num][0], font_style)
        # set column width
        ws.col(col_num).width = columns[col_num][1]

    font_style = xlwt.XFStyle()
    font_style.alignment.wrap = 1
    
    for obj in queryset:
        time  = utilization(obj.id)
        row_num += 1
        row = [
            obj.name,
            obj.bay.name,
            obj.bay_number,
            len(obj.projects.all()),
            len(obj.tool_users.all()),
            obj.current_project.name if obj.current_project else "No project currently running",
            obj.get_status_display(),
            str(datetime.timedelta(seconds=time["InUse_Time"])) if time else None ,
            str(datetime.timedelta(seconds=time["Maintenance_Time"])) if time else None,
            str(datetime.timedelta(seconds=time["Idle_Time"])) if time else None,
            str(datetime.timedelta(seconds=time["Installation_Time"])) if time else None,
        ]
        for col_num in xrange(len(row)):
            ws.write(row_num, col_num, row[col_num], font_style)
            
    wb.save(response)
    return response
    
export_tool_xls.short_description = u"Export Tool XLS"

from xlsxwriter.workbook import Workbook 
import xlsxwriter 
import StringIO


def export_tool_chart(modeladmin, request, queryset):
    output = StringIO.StringIO()
    book = Workbook(output)
    worksheet = book.add_worksheet()
    chart1 = book.add_chart({'type': 'pie'})      
    chart1.add_series({
        'name':       'Pie sales data',
        'categories': ['Sheet1', 1, 0, 3, 0],
        'values':     ['Sheet1', 1, 1, 3, 1],
    })
    chart1.set_title({'name': 'Tool Report Chart'})
    chart1.set_style(10)
    worksheet.insert_chart('C2', chart1, {'x_offset': 25, 'y_offset': 10})
    book.close()
    output.seek(0)
    response = HttpResponse(output.read(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response['Content-Disposition'] = "attachment; filename=chart_pie.xlsx"

    return response
    
export_tool_chart.short_description = u"Export Tool chart XLSX"

class ToolAdmin(admin.ModelAdmin):
    actions = [export_tool_xls, export_tool_chart]


def export_project_xls(modeladmin, request, queryset):
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename=projects.xls'
    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet("Projects Report")
    
    row_num = 0
    
    columns = [
        (u"Project Name", 2000),
        (u"Number of Tools", 6000),
        (u"Number of User working", 8000),
    ]

    font_style = xlwt.XFStyle()
    font_style.font.bold = True

    for col_num in xrange(len(columns)):
        ws.write(row_num, col_num, columns[col_num][0], font_style)
        # set column width
        ws.col(col_num).width = columns[col_num][1]

    font_style = xlwt.XFStyle()
    font_style.alignment.wrap = 1
    
    for obj in queryset:
        row_num += 1
        row = [
            obj.name,
            len(obj.toolproject_set.all()),
            len(obj.users.all()),
        ]
        for col_num in xrange(len(row)):
            ws.write(row_num, col_num, row[col_num], font_style)
            
    wb.save(response)
    return response
    
export_project_xls.short_description = u"Export Project Report XLS" 

class ProjectAdmin(admin.ModelAdmin):
    actions = [export_project_xls]   

def export_user_xls(modeladmin, request, queryset):
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename=users.xls'
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
    ]

    font_style = xlwt.XFStyle()
    font_style.font.bold = True

    for col_num in xrange(len(columns)):
        ws.write(row_num, col_num, columns[col_num][0], font_style)
        # set column width
        ws.col(col_num).width = columns[col_num][1]

    font_style = xlwt.XFStyle()
    font_style.alignment.wrap = 1
    
    for obj in queryset:
        row_num += 1
        row = [
            obj.first_name,
            obj.last_name,
            obj.rfid,
            obj.is_active,
            len(obj.project_set.all()),
            len(obj.ToolUser.all()),
        ]
        for col_num in xrange(len(row)):
            ws.write(row_num, col_num, row[col_num], font_style)
            
    wb.save(response)
    return response
    
export_user_xls.short_description = u"Export User Report XLS" 

class UserAdmin(admin.ModelAdmin):
    actions = [export_user_xls]  


admin.site.register(Bay, ConsoleAdmin)
admin.site.register(Tool, ToolAdmin)
admin.site.register(ToolCategory)
admin.site.register(Project, ProjectAdmin) 
admin.site.register(BayUser, UserAdmin)

