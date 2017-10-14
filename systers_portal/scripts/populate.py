from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from cities_light.models import City, Country

from systers_portal.meetup.models import MeetupLocation, Meetup, Rsvp
from systers_portal.users.models import SystersUser

print(SystersUser)
