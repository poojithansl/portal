from django.core.management.base import BaseCommand
from cities_light.models import City
from meetup.models import MeetupLocation, Meetup
from slugify import slugify
from optparse import make_option
import random
import time
import datetime


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
    t = strTimeProp(start, end, format_str, prop)
    return datetime.datetime.strptime(t, format_str)


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--locations', type=int,
                    help="Number of meetup locations to seed with"),
        make_option('--meetups', type=int,
                    help="Number of meetups to seed with"))

    def _get_fancy_title_and_slug(self, city):
        def _aux():
            period = ["annual", "weekly", "monthly"]
            meeting_type = ["release party", "hackathon",
                            "conference", "workshop", "meeting"]
            second = random.choice(period)
            third = random.choice(meeting_type)
            return "%s %s %s" % (city.name, second, third)

        while True:
            value = _aux()
            if value not in self.used_name:
                self.used_name.add(value)
                return (value, slugify(value))

    def _create_meetup_locations(self, **kw):
        cities = City.objects.all()
        MeetupLocation.objects.all().delete()
        self.used_city = set()

        for x in range(kw['count']):
            city = None
            while True:
                city = random.choice(cities)
                if city.name not in self.used_city:
                    self.used_city.add(city.name)
                    break
            print(city)
            kwargs = {
                "name": city.name,
                "slug": slugify(city.name),
                "location": city,
                "description": "Bazinga!",
                # "organizers" : get_random_string(length=4),
            }
            meetup_table = MeetupLocation.objects.create(**kwargs)
            meetup_table.save()

    def _create_meetups(self, **kw):
        Meetup.objects.all().delete()
        meetup_locations = MeetupLocation.objects.all()
        self.used_name = set()
        for x in range(kw['count']):
            datetime_obj = randomDate("2008-12-11 00:00:00",
                                      "2017-12-11 00:00:00", random.random())

            # Possible bug - duct tape workaround
            city = None
            title, slug = '-' * 51, '-' * 51
            while len(title) > 50 and len(slug) > 50:
                city = random.choice(meetup_locations)
                title, slug = self._get_fancy_title_and_slug(city.location)
            print(title, slug)
            kwargs = {
                "title": title,
                "slug": slug,
                "description": "saturday",
                "meetup_location": city,
                "date": datetime_obj.date(),
                "time": datetime_obj.time(),
            }

            meetup = Meetup.objects.create(**kwargs)
            meetup.save()

    def handle(self, *args, **options):
        self._create_meetup_locations(count=options['locations'])
        self._create_meetups(count=options['meetups'])
