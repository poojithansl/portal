from django.core.management.base import BaseCommand

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from cities_light.models import City, Country

from django.utils.crypto import get_random_string
# from systers_portal.meetup.models import MeetupLocation, Meetup, Rsvp
# from systers_portal.users.models import SystersUser

from meetup.models import MeetupLocation, Meetup, Rsvp
from users.models import SystersUser

class Command(BaseCommand):
    args = '<foo bar ...>'
    help = 'our help string comes here'

    def _create_meetup_locations(self):
        #tlisp = Tag(name='Lisp')
        #tlisp.save()

        cities = City.objects.all()
        import random
        for x in range(500):
            city = random.choice(cities)
            print(city)
        print(len(cities))
        print(SystersUser)
        name = get_random_string(length=32)
        slug = get_random_string(length=10)
        location = city
        description = "despacito"
        organizers = get_random_string(length=4)
        meetup_table = MeetupLocation.objects.create(name=name,slug=slug,location=location,description\
                =description)
        print(meetup_table)
        meetup_table.save() 

        #tjava = Tag(name='Java')
        #tjava.save()

    def _create_meetups(self):
        pass

    def handle(self, *args, **options):
        self._create_meetup_locations()
        self._create_meetups()
