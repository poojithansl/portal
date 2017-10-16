from django.core.management import call_command
from django.test import TestCase
from django.utils.six import StringIO

class PopulateMeetupTest(TestCase):
    def test_command_output(self):
        options = { "meetups": 500, "locations": 450}
        call_command('cities_light', '--force-all')
        #call_command('populate_meetup_locations', **options)
        call_command('populate_meetup_locations', **options)

