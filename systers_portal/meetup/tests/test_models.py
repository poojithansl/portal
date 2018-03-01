from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from cities_light.models import City, Country

from meetup.models import MeetupLocation, Meetup, Rsvp, SupportRequest, RequestMeetupLocation
from users.models import SystersUser


class MeetupBaseTestCase():
    def setUp(self):
        country = Country.objects.create(name='Bar', continent='AS')
        self.location = City.objects.create(name='Foo', display_name='Foo',
                                            country=country)
        self.user = User.objects.create(username='foo', password='foobar')
        self.systers_user = SystersUser.objects.get(user=self.user)
        self.meetup_location = MeetupLocation.objects.create(
            name="Foo Systers", slug="foo", location=self.location,
            description="It's a test location", sponsors="BarBaz", leader=self.systers_user)
        self.meetup_location_request = RequestMeetupLocation.objects.create(
            name="Bar Systers", slug="bar", location=self.location,
            description="This is a test meetup location request",
            user=self.systers_user)


class MeetupLocationModelTestCase(MeetupBaseTestCase, TestCase):
    def test_str(self):
        """Test MeetupLocation object str/unicode representation"""
        self.assertEqual(str(self.meetup_location), "Foo Systers")


class RequestMeetupLocationModelTestCase(MeetupBaseTestCase, TestCase):
    def test_str(self):
        """Test MeetupLocation object str/unicode representation"""
        self.assertEqual(str(self.meetup_location_request), "Bar Systers")


class MeetupTestCase(MeetupBaseTestCase, TestCase):
    def setUp(self):
        super(MeetupTestCase, self).setUp()
        self.meetup = Meetup.objects.create(title="Test Meetup", slug="baz",
                                            date=timezone.now().date(), time=timezone.now().time(),
                                            venue="FooBar colony",
                                            description="This is a testing meetup.",
                                            meetup_location=self.meetup_location,
                                            created_by=self.systers_user)

    def test_str(self):
        """Test Meetup object str/unicode representation"""
        self.assertEqual(str(self.meetup), "Test Meetup")


class RsvpTestCase(MeetupBaseTestCase, TestCase):
    def setUp(self):
        super(RsvpTestCase, self).setUp()
        self.meetup = Meetup.objects.create(title="Test Meetup", slug="baz",
                                            date=timezone.now().date(), time=timezone.now().time(),
                                            venue="FooBar colony",
                                            description="This is a testing meetup.",
                                            meetup_location=self.meetup_location,
                                            created_by=self.systers_user)
        self.rsvp = Rsvp.objects.create(user=self.systers_user, meetup=self.meetup)

    def test_str(self):
        self.assertEqual(str(self.rsvp), "foo RSVP for meetup Test Meetup")


class SupportRequestTestCase(MeetupBaseTestCase, TestCase):
    def setUp(self):
        super(SupportRequestTestCase, self).setUp()
        self.meetup = Meetup.objects.create(title="Test Meetup", slug="baz",
                                            date=timezone.now().date(), time=timezone.now().time(),
                                            venue="FooBar colony",
                                            description="This is a testing meetup.",
                                            meetup_location=self.meetup_location,
                                            created_by=self.systers_user)
        self.support_request = SupportRequest.objects.create(volunteer=self.systers_user,
                                                             meetup=self.meetup,
                                                             description="Support Request")

    def test_str(self):
        self.assertEqual(str(self.support_request), "foo volunteered for meetup Test Meetup")
