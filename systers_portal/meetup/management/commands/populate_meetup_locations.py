from django.core.management.base import BaseCommand

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from cities_light.models import City, Country

from django.utils.crypto import get_random_string
from meetup.models import MeetupLocation, Meetup, Rsvp
from users.models import SystersUser
import random
import time
import datetime 
from pprint import pprint

def strTimeProp(start, end, format, prop):

    """Get a time at a proportion of a range of two formatted times.

    start and end should be strings specifying times formated in the
    given format (strftime-style), giving an interval [start, end].
    prop specifies how a proportion of the interval to be taken after
    start.  The returned time will be in the specified format.
    """

    stime = time.mktime(time.strptime(start, format))
    etime = time.mktime(time.strptime(end, format))

    ptime = stime + prop * (etime - stime)

    return time.strftime(format, time.localtime(ptime))


def randomDate(start, end, prop):
    format_str = '%Y-%m-%d %H:%M:%S'
    #t =  strTimeProp(start, end, '%m/%d/%Y %I:%M %p', prop)
    t =  strTimeProp(start, end, format_str, prop)
    return datetime.datetime.strptime(t, format_str)



class Command(BaseCommand):
    args = '<foo bar ...>'
    help = 'our help string comes here'



    def _get_fancy_name_and_slug(self, city):
        def _aux():
            period = ["annual", "weekly", "monthly"]
            meeting_type = ["release party", "hackathon", "conference"]

            second = random.choice(period)
            third = random.choice(meeting_type)
            return "%s %s %s"%(city.name, second, third)

        def slugify(v):
            return '-'.join(v.split(' ')).lower()


        while True:
            value = _aux()
            if value not in self.used_name:
                self.used_name.add(value)
                return (value, slugify(value))

    def _create_meetup_locations(self, **kw):
        cities = City.objects.all()
        MeetupLocation.objects.all().delete()
        self.used_name = set()

        for x in range(kw['count']):
            city = random.choice(cities)
            name, slug = self._get_fancy_name_and_slug(city) 
            print(name, slug)
            kwargs = {
                #"city" : city,
                "name" : name,
                "slug" : slug,
                "location" : city,
                "description" : "Bazinga!",
                #"organizers" : get_random_string(length=4),
            }
            meetup_table = MeetupLocation.objects.create(**kwargs)
            meetup_table.save() 

    def _create_meetups(self, **kw):
        Meetup.objects.all().delete()
        meetup_locations = MeetupLocation.objects.all()
        for x in range(kw['count']):

            datetime_obj =  randomDate("2008-12-11 00:00:00", 
                    "2017-12-11 00:00:00", random.random())

            kwargs = {
                "title" : get_random_string(length=32),
                "slug" : get_random_string(length=10),
                "description" : "saturday",
                "meetup_location" : random.choice(meetup_locations),
                "date" : datetime_obj.date(),
                "time" : datetime_obj.time(),
            }

            meetup = Meetup.objects.create(**kwargs)
            meetup.save()
    

    def handle(self, *args, **options):
        count = 500
        self._create_meetup_locations(count=count)
        self._create_meetups(count=count)

