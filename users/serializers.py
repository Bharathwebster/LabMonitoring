from rest_framework import serializers
from users.models import BayUser, Group


class BayUserSerializer(serializers.ModelSerializer):

    class Meta:
        model = BayUser
        fields = ('id','rfid', 'first_name', 'last_name', 'email', 'is_admin','is_owner',
                  'is_active', 'group')


class GroupSerializer(serializers.ModelSerializer):

    class Meta:
        model = Group
