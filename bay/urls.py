from django.conf.urls import include, url
from rest_framework.routers import SimpleRouter, DefaultRouter
from bay.views import BayViewSet, ToolViewSet, ProjectViewSet, ImageViewSet, MailerView, LoggingView, logging_view, utilization, ToolPDFView, export_console_xls, export_tool_xls,export_tool_qtr_xls, export_project_xls, export_user_xls, export_user_raw_xls,api_trends, tools_report, trends_pie,ToolsView,NonActiveToolsView,GetConsoles, addTools, tool_image_update, UpdateBay, DeleteBay, GetTools, GetProjects, GetToolOwners, saveNewTools, TestToolsView, GetToolCategory, move_tools,changeStatus,swapTools,tool_image_upload

router = SimpleRouter()
router.register('bay', BayViewSet, base_name="bay")

'''
router = SimpleRouter()
router.register('tool', ToolViewSet, base_name="tools")
'''
toolrouter = SimpleRouter()
toolrouter.register('', ToolViewSet, base_name="tools")

# router.register(
#     'temperature', TemperatureViewSet, base_name="temperatureviewset"
# )

projectrouter = SimpleRouter()
projectrouter.register('', ProjectViewSet, base_name="tools")

toolimage = SimpleRouter()
toolimage.register('', ImageViewSet, base_name="image")

urlpatterns = [
    url(r'', include(router.urls)),
    url(r'^bayinfo/', BayViewSet.as_view({'get': 'get_bay_info'}), name='get_bay_info'),
    url(r'^bay/(?P<bid>[0-9]+)/tools', include(router.urls)),
    url(r'^bay/257/', include(router.urls)),
    url(r'^tools', include(toolrouter.urls)),
    url(r'^projects', include(projectrouter.urls)),
    url(r'^image', include(toolimage.urls)),
    url(r'mailsend/$',MailerView.as_view(),name="sasa"),
    url(r'log/$',LoggingView.as_view(),name="log"),
    url(r'logging_view/$',logging_view,name="logging_view"),
    url(r'tool-utilization/$',utilization,name="tool_utilization"),
    url(r'export-tools/$',ToolPDFView.as_view(),name="export_tools"),
    url(r"^export_console_xls/$", export_console_xls, name="export_console_xls"),
    url(r"^export_tool_xls/$", export_tool_xls, name="export_tool_xls"),
    url(r"^export_project_xls/$", export_project_xls, name="export_project_xls"),
    url(r"^export_user_xls/$", export_user_xls, name="export_user_xls"),
    url(r"^export_user_raw_xls/$", export_user_raw_xls, name="export_user_raw_xls"),
    url(r"^api_trends_overall/$", api_trends, name="api_trends"),
    url(r"^export_tools/(?P<tool_id>[0-9]+)/", tools_report, name="too_reports"),
    url(r"^export_tool_qtr_xls/$", export_tool_qtr_xls, name="export_tool_qtr_xls"),


     # new urls -- Arun

    url(r'^tool_list/nonactivetools/', NonActiveToolsView.as_view({'get': 'list'}), name='nonactivetools'),
    url(r'^tool_list/', ToolsView.as_view({'get': 'list', 'post': 'create'}), name='tool_list'),
     # url for showing all tools utilization
    url(r'^tool_category_list/', ToolsView.as_view(
        {'get': 'tool_utilization_quarterly_list', 'post': 'create'}), name='tool_category_list'),
    url(r'^tool_detail/(?P<pk>[0-9]+)/$', ToolsView.as_view(
        {'get': 'retrieve',
         'put': 'update',
         'patch': 'partial_update'}), name='tool_detail'),
   
    url(r'^tool_category_data/(?P<pk>[0-9]+)/$', ToolsView.as_view(
        {'get': 'tool_utilization_monthly',
         'put': 'update',
         'patch': 'partial_update'}), name='tool_detail'),

    # new url for angular5 cpu apr 21 2018

    url(r'^test_tool_list/', TestToolsView.as_view(
        {'get': 'list', 'post': 'create'}), name='test_tool_list'),

    url(r'^test_tool_detail/(?P<pk>[0-9]+)/', TestToolsView.as_view(
        {'get': 'retrieve',
         'put': 'update',
         'patch': 'partial_update'}), name='test_tool_detail'),

    url(r'^getconsoles/$', GetConsoles.as_view()),
    url(r'^gettoolowners/$', GetToolOwners.as_view()),
    url(r'^addtools/$', addTools),
    url(r'^uploadtoolimage/$', tool_image_update),
    url(r'^updatebay/(?P<pk>\w+)/$$', UpdateBay.as_view()),
    url(r'^deletebay/(?P<pk>\w+)/$', DeleteBay.as_view()),
    url(r'^gettools/$', GetTools.as_view()),
    url(r'^getprojects/$', GetProjects.as_view()),
    url(r'^savenewtools/$', saveNewTools),
    url(r'^gettoolcat/$', GetToolCategory.as_view()),
    url(r'^movebaytools/$', move_tools),
    url(r'^changestatus/$', changeStatus),

    url(r'^test_tool_detail/(?P<pk>[0-9]+)/', TestToolsView.as_view(
        {'get': 'retrieve',
         'put': 'update',
         'patch': 'partial_update'}), name='test_tool_detail'),
    url(r"swaptools/$", swapTools,name ='swap_tools' ),
    url(r'^toolimageupload/$',tool_image_upload)
]



