from django.conf.urls import include, url
from rest_framework.routers import SimpleRouter, DefaultRouter
from users.views import UserViewSet, GroupViewSet

router = SimpleRouter()

router.register('user_info', UserViewSet, base_name="users")


router.register('usergroup', GroupViewSet, base_name="group")

# router.register(
#     'temperature', TemperatureViewSet, base_name="temperatureviewset"
# )

urlpatterns = [
    url(r'', include(router.urls)),
    # url(r'^user/group', include(grouprouter.urls)),
]
