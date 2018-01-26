import datetime

from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404
from django.views.generic import DeleteView, TemplateView, RedirectView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView, FormView
from django.views.generic.list import ListView
from braces.views import LoginRequiredMixin, PermissionRequiredMixin, StaffuserRequiredMixin
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.contenttypes.models import ContentType

from meetup.forms import (AddMeetupForm, EditMeetupForm, AddMeetupLocationMemberForm,
                          AddMeetupLocationForm, EditMeetupLocationForm, AddMeetupCommentForm,
                          EditMeetupCommentForm, RsvpForm, AddSupportRequestForm,
                          EditSupportRequestForm, AddSupportRequestCommentForm,
                          EditSupportRequestCommentForm, RequestMeetupForm)
from meetup.mixins import MeetupLocationMixin
from meetup.models import Meetup, MeetupLocation, Rsvp, SupportRequest, RequestMeetup
from meetup.constants import (OK, SUCCESS_MEETUP_MSG, SLUG_ALREADY_EXISTS, SLUG_ALREADY_EXISTS_MSG)
from users.models import SystersUser
from common.models import Comment


class RequestMeetupView(LoginRequiredMixin, MeetupLocationMixin, CreateView):
    """View to Request a new meetup"""
    template_name = "meetup/request_new_meetup.html"
    model = RequestMeetup
    form_class = RequestMeetupForm
    raise_exception = True

    def get_success_url(self):
        """Supply the redirect URL in case of successful submit"""
        message = "Your request for a new meetup is successfully submitted. "\
                  "Please wait until someone reviews your request. "
        messages.add_message(self.request, messages.SUCCESS, message)
        return reverse('about_meetup_location', kwargs={'slug': self.meetup_location.slug})

    def get_form_kwargs(self):
        """Add request user, meetup location to the form kwargs.
        Used to autofill form fields with requestor without
        explicitly filling them up in the form."""
        kwargs = super(RequestMeetupView, self).get_form_kwargs()
        self.meetup_location = get_object_or_404(MeetupLocation, slug=self.kwargs['slug'])
        kwargs.update({'meetup_location': self.meetup_location})
        kwargs.update({'created_by': self.request.user})
        return kwargs

    def get_meetup_location(self):
        """Add MeetupLocation object to the context"""
        self.meetup_location = get_object_or_404(MeetupLocation, slug=self.kwargs['slug'])
        return self.meetup_location


class NewMeetupRequestsListView(LoginRequiredMixin, PermissionRequiredMixin, MeetupLocationMixin,
                                ListView):
    """List of New Meetup Requests"""
    template_name = "meetup/new_meetup_requests.html"
    model = RequestMeetup
    raise_exception = True
    paginate_by = 10
    
    def get_queryset(self, **kwargs):
        """Set ListView queryset to all the unapproved meetup requests"""
        request_meetups_list = RequestMeetup.objects.filter(
            meetup_location=self.meetup_location, is_approved=False).order_by('date', 'time')
        return request_meetups_list 

    def get_meetup_location(self):
        """Add MeetupLocation object to the context"""
        return self.meetup_location

    def check_permissions(self, request):
        """Check if the request user has the permission to view the meetup requests.
        The permission holds true for superusers."""
        self.meetup_location = get_object_or_404(MeetupLocation, slug=self.kwargs['slug'])
        return self.request.user.has_perm("view_meetup_location_meetuprequest", self.meetup_location)


class ViewMeetupRequestView(LoginRequiredMixin, PermissionRequiredMixin, MeetupLocationMixin,
                            FormView):
    """View the meetup request"""
    template_name = "meetup/view_new_meetup_request.html"
    form_class = RequestMeetupForm
    raise_exception = True

    def get_context_data(self, **kwargs):
        """Add RequestMeetup object and it's verbose fields to the context."""
        context = super(ViewMeetupRequestView,
                        self).get_context_data(**kwargs)
        self.meetup_request = get_object_or_404(
            RequestMeetup, meetup_location=self.meetup_location, slug=self.kwargs['meetup_slug'])
        context['meetup_request'] = self.meetup_request
        context['meetup_request_fields'] = \
            self.meetup_request.get_verbose_fields()
        return context

    def get_form_kwargs(self):
        """Add request user, meetup  to the form kwargs.
        Used to autofill form fields with requestor without
        explicitly filling them up in the form."""
        kwargs = super(ViewMeetupRequestView, self).get_form_kwargs()
        kwargs.update({'meetup_location': self.meetup_location})
        kwargs.update({'created_by': self.request.user})
        return kwargs    

    def check_permissions(self, request):
        """Check if the request user has the permission to view meetup request in meetup location.
        The permission holds true for superusers."""
        self.meetup_location = get_object_or_404(MeetupLocation, slug=self.kwargs['slug'])
        return self.request.user.has_perm("view_meetup_location_meetuprequest", self.meetup_location)


class ApproveRequestMeetupView(LoginRequiredMixin, PermissionRequiredMixin, MeetupLocationMixin,
                               RedirectView):
    """Approve the new meetup request"""
    model = RequestMeetup
    permanent = False
    raise_exception = True

    def get_redirect_url(self, *args, **kwargs):
        """Supply the redirect URL in case of successful approval.
        * Creates a new RequestMeetup object and copy fields,
            values from RequestMeetup object
        * Adds the requestor as the meetup location organizer
        * Sets the RequestMeetup object's is_approved field to True.
        """
        meetup_request = get_object_or_404(
            RequestMeetup, slug=self.kwargs['meetup_slug'], meetup_location=self.meetup_location)
        new_meetup = Meetup()
        new_meetup.title = meetup_request.title
        new_meetup.slug = meetup_request.slug
        new_meetup.date = meetup_request.date
        new_meetup.time = meetup_request.time
        new_meetup.venue = meetup_request.venue
        new_meetup.description = meetup_request.description
        new_meetup.meetup_location = meetup_request.meetup_location
        systersuser = get_object_or_404(
            SystersUser, user=meetup_request.created_by)

        meetup_request.approved_by = get_object_or_404(
            SystersUser, user=self.request.user)
        meetup_request.is_approved = True
        self.slug_meetup_request = meetup_request.slug
        status, message, level = self.process_request()
        messages.add_message(self.request, level, message)
        organizers = self.meetup_location.organizers.all()
        if status == OK:
            new_meetup.save()
            if systersuser not in organizers:
                self.meetup_location.organizers.add(systersuser)
            meetup_request.save()
            return reverse('view_meetup', kwargs={'slug': self.meetup_location.slug,\
             'meetup_slug': new_meetup.slug})
        else:
            return reverse('new_meetup_requests', kwargs={'slug':self.meetup_location.slug})

    def process_request(self):
        """If an error occurs during the creation of a new meetup, this method returns the
        status and message."""
        self.slug_meetup_values = Meetup.objects.all(
        ).values_list('slug', flat=True)
        if self.slug_meetup_request in self.slug_meetup_values:
            STATUS = SLUG_ALREADY_EXISTS
            return STATUS, SLUG_ALREADY_EXISTS_MSG.format(self.slug_meetup_request),\
                messages.WARNING
        else:
            STATUS = OK
        return STATUS, SUCCESS_MEETUP_MSG, messages.INFO

    def check_permissions(self, request):
        """Check if the request user has the permission to add a meetup to the meetup location.
        The permission holds true for superusers."""
        self.meetup_location = get_object_or_404(MeetupLocation, slug=self.kwargs['slug'])
        return self.request.user.has_perm("approve_meetup_location_meetuprequest", self.meetup_location)


class RejectMeetupRequestView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """Reject the new meetup request"""
    model = RequestMeetup
    template_name = "meetup/confirm_reject_request_meetup.html"
    raise_exception = True

    def get_success_url(self, *args, **kwargs):
        """Supply the success URL in case of a successful submit"""
        messages.add_message(self.request, messages.INFO,
                             "Meetup request successfullly rejected!")
        self.meetup_request = get_object_or_404(RequestMeetup, slug=self.kwargs['meetup_slug'],
                                                meetup_location=self.meetup_location)
        self.meetup_request.delete()
        return reverse('new_meetup_requests', kwargs={'slug':self.kwargs['slug']})

    def get_object(self, queryset=None):
        """Returns the RequestMeetup object"""
        self.meetup_request = get_object_or_404(RequestMeetup, slug=self.kwargs['meetup_slug'],
                                                meetup_location=self.meetup_location)
        return self.meetup_request

    def check_permissions(self, request):
        """Check if the request user has the permission to reject a meetup in the meetup location.
        The permission holds true for superusers."""
        self.meetup_location = get_object_or_404(MeetupLocation, slug=self.kwargs['slug'])
        return self.request.user.has_perm("reject_meetup_location_meetuprequest", self.meetup_location)


class MeetupLocationAboutView(MeetupLocationMixin, TemplateView):
    """Meetup Location about view, show about description of Meetup Location"""
    model = MeetupLocation
    template_name = "meetup/about.html"

    def get_meetup_location(self):
        """Add MeetupLocation object to the context"""
        return get_object_or_404(MeetupLocation, slug=self.kwargs['slug'])


class MeetupLocationList(ListView):
    """List all Meetup Locations"""
    template_name = "meetup/list_location.html"
    model = MeetupLocation
    paginate_by = 20

    def get_context_data(self, **kwargs):
        context = super(MeetupLocationList, self).get_context_data(**kwargs)
        context['meetup_list'] = Meetup.objects.filter(
            date__gte=datetime.date.today()).order_by('date', 'time')
        return context


class MeetupView(MeetupLocationMixin, DetailView):
    """View details of a meetup, including date, time, venue, description, number of users who
    rsvp'd and comments."""
    template_name = "meetup/meetup.html"
    model = MeetupLocation

    def get_context_data(self, **kwargs):
        """Add Meetup object, number of users who rsvp'd and comments to the context"""
        context = super(MeetupView, self).get_context_data(**kwargs)
        self.meetup = get_object_or_404(Meetup, slug=self.kwargs['meetup_slug'],
                                        meetup_location=self.object)
        context['meetup'] = self.meetup
        context['comments'] = Comment.objects.filter(
            content_type=ContentType.objects.get(app_label='meetup', model='meetup'),
            object_id=self.meetup.id,
            is_approved=True).order_by('date_created')
        coming_list = Rsvp.objects.filter(meetup=self.meetup, coming=True)
        plus_one_list = Rsvp.objects.filter(meetup=self.meetup, plus_one=True)
        not_coming_list = Rsvp.objects.filter(meetup=self.meetup, coming=False)
        context['coming_no'] = len(coming_list) + len(plus_one_list)
        context['not_coming_no'] = len(not_coming_list)
        context['share_message'] = self.meetup.title + " @systers_org " + \
            self.meetup.meetup_location.name
        return context

    def get_meetup_location(self):
        """Add MeetupLocation object to the context"""
        return self.object


class MeetupLocationMembersView(MeetupLocationMixin, DetailView):
    """Meetup Location members view, show members list of Meetup Location"""
    model = MeetupLocation
    template_name = "meetup/members.html"
    paginate_by = 50

    def get_context_data(self, **kwargs):
        """Add list of members and organizers to the context"""
        context = super(MeetupLocationMembersView, self).get_context_data(**kwargs)
        organizer_list = self.meetup_location.organizers.all()
        context['organizer_list'] = organizer_list
        context['member_list'] = self.meetup_location.members.exclude(id__in=organizer_list)
        return context

    def get_meetup_location(self):
        """Add MeetupLocation object to the context"""
        self.meetup_location = get_object_or_404(MeetupLocation, slug=self.kwargs['slug'])
        return self.meetup_location


class AddMeetupView(LoginRequiredMixin, PermissionRequiredMixin, MeetupLocationMixin, CreateView):
    """Add new meetup"""
    template_name = "meetup/add_meetup.html"
    model = Meetup
    form_class = AddMeetupForm
    raise_exception = True

    def get_success_url(self):
        """Redirect to meetup view page in case of successful submit"""
        return reverse("view_meetup", kwargs={"slug": self.meetup_location.slug,
                                              "meetup_slug": self.object.slug})

    def get_form_kwargs(self):
        """Add request user and meetup location object to the form kwargs.
        Used to autofill form fields with created_by and meetup_location without
        explicitly filling them up in the form."""
        kwargs = super(AddMeetupView, self).get_form_kwargs()
        self.meetup_location = get_object_or_404(MeetupLocation, slug=self.kwargs['slug'])
        kwargs.update({'created_by': self.request.user})
        kwargs.update({'meetup_location': self.meetup_location})
        return kwargs

    def get_meetup_location(self):
        """Add MeetupLocation object to the context"""
        return self.meetup_location

    def check_permissions(self, request):
        """Check if the request user has the permission to add a meetup to the meetup location.
        The permission holds true for superusers."""
        return request.user.has_perm('meetup.add_meetup')


class DeleteMeetupView(LoginRequiredMixin, PermissionRequiredMixin, MeetupLocationMixin,
                       DeleteView):
    """Delete existing Meetup"""
    template_name = "meetup/meetup_confirm_delete.html"
    model = Meetup
    slug_url_kwarg = "meetup_slug"
    raise_exception = True

    def get_success_url(self):
        """Redirect to meetup location's about page in case of successful deletion"""
        self.get_meetup_location()
        return reverse("about_meetup_location",
                       kwargs={"slug": self.meetup_location.slug})

    def get_meetup_location(self):
        """Add MeetupLocation object to the context"""
        self.meetup_location = get_object_or_404(MeetupLocation, slug=self.kwargs['slug'])
        return self.meetup_location

    def check_permissions(self, request):
        """Check if the request user has the permission to delete a meetup from the meetup
        location. The permission holds true for superusers."""
        return request.user.has_perm('meetup.delete_meetup')


class EditMeetupView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """Edit an existing meetup"""
    template_name = "meetup/edit_meetup.html"
    model = Meetup
    slug_url_kwarg = "meetup_slug"
    form_class = EditMeetupForm
    raise_exception = True

    def get_success_url(self):
        """Redirect to meetup view page in case of successful submit"""
        return reverse("view_meetup", kwargs={"slug": self.object.meetup_location.slug,
                       "meetup_slug": self.object.slug})

    def get_context_data(self, **kwargs):
        """Add Meetup and MeetupLocation objects to the context"""
        context = super(EditMeetupView, self).get_context_data(**kwargs)
        self.meetup = get_object_or_404(Meetup, slug=self.kwargs['meetup_slug'])
        context['meetup'] = self.meetup
        context['meetup_location'] = self.meetup.meetup_location
        return context

    def check_permissions(self, request):
        """Check if the request user has the permission to edit a meetup from the meetup location.
        The permission holds true for superusers."""
        return request.user.has_perm('meetup.change_meetup')


class UpcomingMeetupsView(MeetupLocationMixin, ListView):
    """List upcoming meetups of a meetup location"""
    template_name = "meetup/upcoming_meetups.html"
    model = Meetup
    paginate_by = 10

    def get_queryset(self, **kwargs):
        """Set ListView queryset to all the meetups whose date is equal to or greater than the
        current date"""
        self.meetup_location = get_object_or_404(MeetupLocation, slug=self.kwargs['slug'])
        meetup_list = Meetup.objects.filter(
            meetup_location=self.meetup_location,
            date__gte=datetime.date.today()).order_by('date', 'time')
        return meetup_list

    def get_meetup_location(self):
        """Add MeetupLocation object to the context"""
        return self.meetup_location


class PastMeetupListView(MeetupLocationMixin, ListView):
    """List past meetups of a meetup location"""
    template_name = "meetup/past_meetups.html"
    model = Meetup
    paginate_by = 10

    def get_queryset(self, **kwargs):
        """Set ListView queryset to all the meetups whose date is less than the current date"""
        self.meetup_location = get_object_or_404(MeetupLocation, slug=self.kwargs['slug'])
        meetup_list = Meetup.objects.filter(
            meetup_location=self.meetup_location,
            date__lt=datetime.date.today()).order_by('date', 'time')
        return meetup_list

    def get_meetup_location(self):
        """Add MeetupLocation object to the context"""
        return self.meetup_location


class MeetupLocationSponsorsView(MeetupLocationMixin, DetailView):
    """View sponsors of a meetup location"""
    template_name = "meetup/sponsors.html"
    model = MeetupLocation

    def get_meetup_location(self):
        """Add MeetupLocation object to the context"""
        return get_object_or_404(MeetupLocation, slug=self.kwargs['slug'])


class RemoveMeetupLocationMemberView(LoginRequiredMixin, PermissionRequiredMixin,
                                     MeetupLocationMixin, RedirectView):
    """Remove a member from a meetup location"""
    model = MeetupLocation
    permanent = False
    raise_exception = True

    def get_redirect_url(self, *args, **kwargs):
        """Remove the member from 'member' and 'organizer' lists and redirect to the members page
        of the meetup location"""
        user = get_object_or_404(User, username=self.kwargs.get('username'))
        systersuser = get_object_or_404(SystersUser, user=user)
        organizers = self.meetup_location.organizers.all()
        if systersuser in organizers and len(organizers) > 1:
            self.meetup_location.organizers.remove(systersuser)
        if systersuser not in self.meetup_location.organizers.all():
            self.meetup_location.members.remove(systersuser)
        return reverse('members_meetup_location', kwargs={'slug': self.meetup_location.slug})

    def get_meetup_location(self):
        """Add MeetupLocation object to the context"""
        return self.meetup_location

    def check_permissions(self, request):
        """Check if the request user has the permission to remove a member from the meetup
        location. The permission holds true for superusers."""
        self.meetup_location = get_object_or_404(MeetupLocation, slug=self.kwargs['slug'])
        return request.user.has_perm('delete_meetup_location_member', self.meetup_location)


class AddMeetupLocationMemberView(LoginRequiredMixin, PermissionRequiredMixin, MeetupLocationMixin,
                                  UpdateView):
    """Add new member to meetup location"""
    template_name = "meetup/add_member.html"
    model = MeetupLocation
    form_class = AddMeetupLocationMemberForm
    raise_exception = True

    def get_success_url(self):
        """Redirect to the members page of the meetup location in case of successful addition"""
        return reverse('members_meetup_location', kwargs={'slug': self.meetup_location.slug})

    def get_meetup_location(self):
        """Add MeetupLocation object to the context"""
        return self.meetup_location

    def check_permissions(self, request):
        """Check if the request user has the permission to add a member to the meetup location.
        The permission holds true for superusers."""
        self.meetup_location = get_object_or_404(MeetupLocation, slug=self.kwargs['slug'])
        return request.user.has_perm('add_meetup_location_member', self.meetup_location)


class RemoveMeetupLocationOrganizerView(LoginRequiredMixin, PermissionRequiredMixin,
                                        MeetupLocationMixin, RedirectView):
    """Remove the 'organizer' status of a meetup location member"""
    model = MeetupLocation
    permanent = False
    raise_exception = True

    def get_redirect_url(self, *args, **kwargs):
        """Remove the member from the 'organizer' list and redirect to the members page of the
        meetup location"""
        user = get_object_or_404(User, username=self.kwargs.get('username'))
        systersuser = get_object_or_404(SystersUser, user=user)
        organizers = self.meetup_location.organizers.all()
        if systersuser in organizers and len(organizers) > 1:
            self.meetup_location.organizers.remove(systersuser)
        return reverse('members_meetup_location', kwargs={'slug': self.meetup_location.slug})

    def get_meetup_location(self):
        """Add MeetupLocation object to the context"""
        return self.meetup_location

    def check_permissions(self, request):
        """Check if the request user has the permission to remove an organizer from the meetup
        location. The permission holds true for superusers."""
        self.meetup_location = get_object_or_404(MeetupLocation, slug=self.kwargs['slug'])
        return request.user.has_perm('delete_meetup_location_organizer', self.meetup_location)


class MakeMeetupLocationOrganizerView(LoginRequiredMixin, PermissionRequiredMixin,
                                      MeetupLocationMixin, RedirectView):
    """Make a meetup location member an organizer of the location"""
    model = MeetupLocation
    permanent = False
    raise_exception = True

    def get_redirect_url(self, *args, **kwargs):
        """Add the member to the 'organizer' list and send her a notification email. Redirect to
        the members page of the meetup location"""
        user = get_object_or_404(User, username=self.kwargs.get('username'))
        systersuser = get_object_or_404(SystersUser, user=user)
        organizers = self.meetup_location.organizers.all()
        if systersuser not in organizers:
            self.meetup_location.organizers.add(systersuser)
        return reverse('members_meetup_location', kwargs={'slug': self.meetup_location.slug})

    def get_meetup_location(self):
        """Add MeetupLocation object to the context"""
        return self.meetup_location

    def check_permissions(self, request):
        """Check if the request user has the permission to add an organizer to the meetup
        location. The permission holds true for superusers."""
        self.meetup_location = get_object_or_404(MeetupLocation, slug=self.kwargs['slug'])
        return request.user.has_perm('add_meetup_location_organizer', self.meetup_location)


class JoinMeetupLocationView(LoginRequiredMixin, MeetupLocationMixin, RedirectView):
    """Send a join request for a meetup location"""
    model = MeetupLocation
    permanent = False
    raise_exception = True

    def get_redirect_url(self, *args, **kwargs):
        """Redirect to meetup location's about page."""
        return reverse('about_meetup_location', kwargs={'slug': self.meetup_location.slug})

    def get(self, request, *args, **kwargs):
        """Display messages to the user as per the following conditions:

        * if the user is not a meetup location member and has not requested to join the location
          before, add the user's join request, display the corresponding message and send a
          notification to all organizers
        * if the user is not a meetup location member and has requested to join the location
          before, display the corresponding message
        * if the user is aleady a member of the meetup location, display the corresponding message
        """
        self.meetup_location = get_object_or_404(MeetupLocation, slug=self.kwargs['slug'])
        user = get_object_or_404(User, username=self.kwargs.get('username'))
        systersuser = get_object_or_404(SystersUser, user=user)

        join_requests = self.meetup_location.join_requests.all()
        members = self.meetup_location.members.all()

        if systersuser not in join_requests and systersuser not in members:
            self.meetup_location.join_requests.add(systersuser)
            msg = "Your request to join meetup location {0} has been sent. In a short while " \
                  "someone will review your request."
            messages.add_message(request, messages.SUCCESS, msg.format(self.meetup_location))
        elif systersuser in join_requests:
            msg = "You have already requested to join meetup location {0}. Please wait until " \
                  "someone reviews your request."
            messages.add_message(request, messages.WARNING, msg.format(self.meetup_location))
        elif systersuser in members:
            msg = "You are already a member of meetup location {0}."
            messages.add_message(request, messages.WARNING, msg.format(self.meetup_location))
        return super(JoinMeetupLocationView, self).get(request, *args, **kwargs)

    def get_meetup_location(self):
        """Add MeetupLocation object to the context"""
        return self.meetup_location


class MeetupLocationJoinRequestsView(LoginRequiredMixin, MeetupLocationMixin, DetailView):
    """View all join requests for a meetup location"""
    model = MeetupLocation
    template_name = "meetup/join_requests.html"
    paginated_by = 20

    def get_context_data(self, **kwargs):
        """Add all join requests to the context"""
        context = super(MeetupLocationJoinRequestsView, self).get_context_data(**kwargs)
        context['requests'] = self.object.join_requests.all()
        return context

    def get_meetup_location(self):
        """Add MeetupLocation object to the context"""
        return self.object


class ApproveMeetupLocationJoinRequestView(LoginRequiredMixin, PermissionRequiredMixin,
                                           MeetupLocationMixin, RedirectView):
    """Approve a join request for a meetup location"""
    model = MeetupLocation
    permanent = False
    raise_exception = True

    def get_redirect_url(self, *args, **kwargs):
        """Add the user to the members of the meetup location, send the user a notification and
        redirect to meetup location's join request page"""
        user = get_object_or_404(User, username=self.kwargs.get('username'))
        systersuser = get_object_or_404(SystersUser, user=user)
        self.meetup_location.members.add(systersuser)
        self.meetup_location.join_requests.remove(systersuser)
        return reverse('join_requests_meetup_location', kwargs={'slug': self.meetup_location.slug})

    def get_meetup_location(self):
        """Add MeetupLocation object to the context"""
        return self.meetup_location

    def check_permissions(self, request):
        """Check if the request user has the permission to approve a join request for the meetup
        location. The permission holds true for superusers."""
        self.meetup_location = get_object_or_404(MeetupLocation, slug=self.kwargs['slug'])
        return request.user.has_perm('approve_meetup_location_joinrequest', self.meetup_location)


class RejectMeetupLocationJoinRequestView(LoginRequiredMixin, PermissionRequiredMixin,
                                          MeetupLocationMixin, RedirectView):
    """Reject a join request for a meetup location"""
    model = MeetupLocation
    permanent = False
    raise_exception = True

    def get_redirect_url(self, *args, **kwargs):
        """Delete the user's join request and redirect to meetup location's join request page"""
        user = get_object_or_404(User, username=self.kwargs.get('username'))
        systersuser = get_object_or_404(SystersUser, user=user)
        self.meetup_location.join_requests.remove(systersuser)
        return reverse('join_requests_meetup_location', kwargs={'slug': self.meetup_location.slug})

    def get_meetup_location(self):
        """Add MeetupLocation object to the context"""
        return self.meetup_location

    def check_permissions(self, request):
        """Check if the request user has the permission to reject a join request for the meetup
        location. The permission holds true for superusers."""
        self.meetup_location = get_object_or_404(MeetupLocation, slug=self.kwargs['slug'])
        return request.user.has_perm('reject_meetup_location_joinrequest', self.meetup_location)


class AddMeetupLocationView(LoginRequiredMixin, PermissionRequiredMixin, MeetupLocationMixin,
                            CreateView):
    """Add new meetup location"""
    template_name = "meetup/add_meetup_location.html"
    model = MeetupLocation
    slug_url_kwarg = "slug"
    form_class = AddMeetupLocationForm
    raise_exception = True

    def get_success_url(self):
        """Add the request user to the meetup location's members and organizers and redirect to
        the about page in case of successful addition"""
        self.object.members.add(self.systersuser)
        self.object.organizers.add(self.systersuser)
        return reverse("about_meetup_location", kwargs={"slug": self.object.slug})

    def get_meetup_location(self):
        """Add MeetupLocation object to the context"""
        return self.object

    def check_permissions(self, request):
        """Check if the request user has the permission to add a meetup location.
        The permission holds true for superusers."""
        self.systersuser = get_object_or_404(SystersUser, user=request.user)
        return request.user.has_perm('meetup.add_meetuplocation')


class EditMeetupLocationView(LoginRequiredMixin, PermissionRequiredMixin, MeetupLocationMixin,
                             UpdateView):
    """Edit an existing meetup location"""
    template_name = "meetup/edit_meetup_location.html"
    model = MeetupLocation
    form_class = EditMeetupLocationForm
    raise_exception = True

    def get_success_url(self):
        """Redirect to the meetup location's about page in case of successful submission"""
        self.get_meetup_location()
        return reverse("about_meetup_location", kwargs={"slug": self.meetup_location.slug})

    def get_meetup_location(self, **kwargs):
        """Add MeetupLocation object to the context"""
        return self.meetup_location

    def check_permissions(self, request):
        """Check if the request user has the permission to edit a meetup location.
        The permission holds true for superusers."""
        self.meetup_location = get_object_or_404(MeetupLocation, slug=self.kwargs['slug'])
        return request.user.has_perm('meetup.change_meetuplocation')


class DeleteMeetupLocationView(LoginRequiredMixin, PermissionRequiredMixin, MeetupLocationMixin,
                               DeleteView):
    """Delete an existing meetup location"""
    template_name = "meetup/meetup_location_confirm_delete.html"
    model = MeetupLocation
    raise_exception = True

    def get_success_url(self):
        """Redirect to the list of meetup locations in case of successful deletion"""
        return reverse("list_meetup_location")

    def get_meetup_location(self):
        """Add MeetupLocation object to the context"""
        return self.object

    def check_permissions(self, request):
        """Check if the request user has the permission to delete a meetup location.
        The permission holds true for superusers."""
        self.meetup_location = get_object_or_404(MeetupLocation, slug=self.kwargs['slug'])
        return request.user.has_perm('meetup.delete_meetuplocation')


class AddMeetupCommentView(LoginRequiredMixin, MeetupLocationMixin, CreateView):
    """Add a comment to a Meetup"""
    template_name = "meetup/add_comment.html"
    model = Comment
    form_class = AddMeetupCommentForm
    raise_exception = True

    def get_success_url(self):
        """Redirect to the meetup view page in case of successful addition"""
        return reverse("view_meetup", kwargs={"slug": self.meetup_location.slug,
                                              "meetup_slug": self.meetup.slug})

    def get_form_kwargs(self):
        """Add meetup object and request user to the form kwargs. Used to autofill form fields with
        content_object and author without explicitly filling them up in the form."""
        kwargs = super(AddMeetupCommentView, self).get_form_kwargs()
        self.meetup_location = get_object_or_404(MeetupLocation, slug=self.kwargs['slug'])
        self.meetup = get_object_or_404(Meetup, slug=self.kwargs['meetup_slug'])
        kwargs.update({'content_object': self.meetup})
        kwargs.update({'author': self.request.user})
        return kwargs

    def get_context_data(self, **kwargs):
        """Add Meetup object to the context"""
        context = super(AddMeetupCommentView, self).get_context_data(**kwargs)
        context['meetup'] = self.meetup
        return context

    def get_meetup_location(self):
        """Add MeetupLocation object to the context"""
        return self.meetup_location


class EditMeetupCommentView(LoginRequiredMixin, PermissionRequiredMixin, MeetupLocationMixin,
                            UpdateView):
    """Edit a meetup's comment"""
    template_name = "meetup/edit_comment.html"
    model = Comment
    pk_url_kwarg = "comment_pk"
    form_class = EditMeetupCommentForm
    raise_exception = True

    def get_success_url(self):
        """Redirect to the meetup view page in case of successful submission"""
        self.get_meetup_location()
        return reverse("view_meetup", kwargs={"slug": self.meetup_location.slug,
                       "meetup_slug": self.object.content_object.slug})

    def get_context_data(self, **kwargs):
        """Add Meetup object to the context"""
        context = super(EditMeetupCommentView, self).get_context_data(**kwargs)
        context['meetup'] = get_object_or_404(Meetup, slug=self.kwargs['meetup_slug'])
        return context

    def get_meetup_location(self):
        """Add MeetupLocation object to the context"""
        self.meetup_location = get_object_or_404(MeetupLocation, slug=self.kwargs['slug'])
        return self.meetup_location

    def check_permissions(self, request):
        """Check if the request user has the permission to edit a meetup comment."""
        self.comment = get_object_or_404(Comment, pk=self.kwargs['comment_pk'])
        systersuser = get_object_or_404(SystersUser, user=request.user)
        return systersuser == self.comment.author


class DeleteMeetupCommentView(LoginRequiredMixin, PermissionRequiredMixin, MeetupLocationMixin,
                              DeleteView):
    """Delete a meetup's comment"""
    template_name = "meetup/comment_confirm_delete.html"
    model = Comment
    pk_url_kwarg = "comment_pk"
    raise_exception = True

    def get_success_url(self):
        """Redirect to the meetup view page in case of successful submission"""
        self.get_meetup_location()
        return reverse("view_meetup", kwargs={"slug": self.meetup_location.slug,
                       "meetup_slug": self.object.content_object.slug})

    def get_context_data(self, **kwargs):
        """Add Meetup object to the context"""
        context = super(DeleteMeetupCommentView, self).get_context_data(**kwargs)
        context['meetup'] = get_object_or_404(Meetup, slug=self.kwargs['meetup_slug'])
        return context

    def get_meetup_location(self):
        """Add MeetupLocation object to the context"""
        self.meetup_location = get_object_or_404(MeetupLocation, slug=self.kwargs['slug'])
        return self.meetup_location

    def check_permissions(self, request):
        """Check if the request user has the permission to delete a meetup comment."""
        self.comment = get_object_or_404(Comment, pk=self.kwargs['comment_pk'])
        systersuser = get_object_or_404(SystersUser, user=request.user)
        return systersuser == self.comment.author


class RsvpMeetupView(LoginRequiredMixin, PermissionRequiredMixin, MeetupLocationMixin, CreateView):
    """RSVP for a meetup"""
    template_name = "meetup/rsvp_meetup.html"
    model = Rsvp
    form_class = RsvpForm
    raise_exception = True

    def get_success_url(self):
        """Redirect to the meetup view page in case of successful submission"""
        return reverse("view_meetup", kwargs={"slug": self.meetup_location.slug,
                                              "meetup_slug": self.object.meetup.slug})

    def get_form_kwargs(self):
        """Add request user and meetup object to the form kwargs. Used to autofill form fields
        with user and meetup without explicitly filling them up in the form."""
        kwargs = super(RsvpMeetupView, self).get_form_kwargs()
        self.meetup_location = get_object_or_404(MeetupLocation, slug=self.kwargs['slug'])
        self.meetup = get_object_or_404(Meetup, slug=self.kwargs['meetup_slug'])
        kwargs.update({'user': self.request.user})
        kwargs.update({'meetup': self.meetup})
        return kwargs

    def get_context_data(self, **kwargs):
        """Add Meetup object to the context"""
        context = super(RsvpMeetupView, self).get_context_data(**kwargs)
        context['meetup'] = self.meetup
        return context

    def get_meetup_location(self):
        """Add MeetupLocation object to the context"""
        return self.meetup_location

    def check_permissions(self, request):
        """Check if the request user has the permission to RSVP for a meetup. The permission
        holds true for superusers."""
        self.meetup_location = get_object_or_404(MeetupLocation, slug=self.kwargs['slug'])
        return request.user.has_perm('add_meetup_rsvp', self.meetup_location)


class RsvpGoingView(LoginRequiredMixin, MeetupLocationMixin, ListView):
    """List of members whose rsvp status is 'coming'"""
    template_name = "meetup/rsvp_going.html"
    model = Rsvp
    paginated_by = 30

    def get_queryset(self, **kwargs):
        """Set ListView queryset to all rsvps whose 'coming' attribute is set to True"""
        self.meetup_location = get_object_or_404(MeetupLocation, slug=self.kwargs['slug'])
        self.meetup = get_object_or_404(Meetup, slug=self.kwargs['meetup_slug'],
                                        meetup_location=self.meetup_location)
        rsvp_list = Rsvp.objects.filter(meetup=self.meetup, coming=True)
        return rsvp_list

    def get_context_data(self, **kwargs):
        """Add Meetup object to the context"""
        context = super(RsvpGoingView, self).get_context_data(**kwargs)
        context['meetup'] = self.meetup
        return context

    def get_meetup_location(self):
        """Add MeetupLocation object to the context"""
        return self.meetup_location


class AddSupportRequestView(LoginRequiredMixin, PermissionRequiredMixin, MeetupLocationMixin,
                            CreateView):
    """Add a Support Request for a meetup"""
    template_name = "meetup/add_support_request.html"
    model = SupportRequest
    form_class = AddSupportRequestForm
    raise_exception = True

    def get_success_url(self):
        """Redirect to the support request view page in case of successful submission"""
        return reverse("view_support_request", kwargs={"slug": self.meetup_location.slug,
                       "meetup_slug": self.meetup.slug, "pk": self.object.pk})

    def get_form_kwargs(self):
        """Add request user and meetup object to the form kwargs. Used to autofill form fields
        with volunteer and meetup without explicitly filling them up in the form."""
        kwargs = super(AddSupportRequestView, self).get_form_kwargs()
        self.meetup_location = get_object_or_404(MeetupLocation, slug=self.kwargs['slug'])
        self.meetup = get_object_or_404(Meetup, slug=self.kwargs['meetup_slug'])
        kwargs.update({'volunteer': self.request.user})
        kwargs.update({'meetup': self.meetup})
        return kwargs

    def get_context_data(self, **kwargs):
        """Add Meetup object to the context"""
        context = super(AddSupportRequestView, self).get_context_data(**kwargs)
        context['meetup'] = self.meetup
        return context

    def get_meetup_location(self):
        """Add MeetupLocation object to the context"""
        return self.meetup_location

    def check_permissions(self, request):
        """Check if the request user has the permission to add a Support Request for a meetup.
        The permission holds true for superusers."""
        return request.user.has_perm('meetup.add_supportrequest')


class EditSupportRequestView(LoginRequiredMixin, PermissionRequiredMixin, MeetupLocationMixin,
                             UpdateView):
    """Edit an existing support request"""
    template_name = "meetup/edit_support_request.html"
    model = SupportRequest
    form_class = EditSupportRequestForm
    raise_exception = True

    def get_success_url(self):
        """Redirect to the support request view page in case of successful submission"""
        self.get_meetup_location()
        return reverse("view_support_request", kwargs={"slug": self.meetup_location.slug,
                       "meetup_slug": self.object.meetup.slug, "pk": self.object.pk})

    def get_context_data(self, **kwargs):
        """Add Meetup object to the context"""
        context = super(EditSupportRequestView, self).get_context_data(**kwargs)
        self.meetup = get_object_or_404(Meetup, slug=self.kwargs['meetup_slug'])
        context['meetup'] = self.meetup
        return context

    def get_meetup_location(self):
        """Add MeetupLocation object to the context"""
        self.meetup_location = get_object_or_404(MeetupLocation, slug=self.kwargs['slug'])
        return self.meetup_location

    def check_permissions(self, request):
        """Check if the request user has the permission to edit a Support Request for a meetup.
        The permission holds true for superusers."""
        return request.user.has_perm('meetup.change_supportrequest')


class DeleteSupportRequestView(LoginRequiredMixin, PermissionRequiredMixin, MeetupLocationMixin,
                               DeleteView):
    """Delete existing Support Request"""
    template_name = "meetup/support_request_confirm_delete.html"
    model = SupportRequest
    raise_exception = True

    def get_success_url(self):
        """Redirect to the meetup view page in case of successful submission"""
        self.get_meetup_location()
        return reverse("view_meetup", kwargs={"slug": self.meetup_location.slug,
                       "meetup_slug": self.object.meetup.slug})

    def get_meetup_location(self):
        """Add MeetupLocation object to the context"""
        self.meetup_location = get_object_or_404(MeetupLocation, slug=self.kwargs['slug'])
        return self.meetup_location

    def check_permissions(self, request):
        """Check if the request user has the permission to delete a Support Request for a meetup.
        The permission holds true for superusers."""
        return request.user.has_perm('meetup.delete_supportrequest')


class SupportRequestView(MeetupLocationMixin, DetailView):
    """View a support request"""
    template_name = "meetup/support_request.html"
    model = SupportRequest

    def get_context_data(self, **kwargs):
        """Add Meetup object, SupportRequest object and approved comments to the context"""
        context = super(SupportRequestView, self).get_context_data(**kwargs)
        context['meetup'] = get_object_or_404(Meetup, slug=self.kwargs['meetup_slug'])
        context['support_request'] = self.object
        context['comments'] = Comment.objects.filter(
            content_type=ContentType.objects.get(app_label='meetup', model='supportrequest'),
            object_id=self.object.id,
            is_approved=True).order_by('date_created')
        return context

    def get_meetup_location(self):
        """Add MeetupLocation object to the context"""
        return get_object_or_404(MeetupLocation, slug=self.kwargs['slug'])


class SupportRequestsListView(MeetupLocationMixin, ListView):
    """List support requests for a meetup"""
    template_name = "meetup/list_support_requests.html"
    model = SupportRequest
    paginate_by = 10

    def get_queryset(self, **kwargs):
        """Set ListView queryset to all approved support requests of the meetup"""
        self.meetup = get_object_or_404(Meetup, slug=self.kwargs['meetup_slug'])
        supportrequest_list = SupportRequest.objects.filter(meetup=self.meetup, is_approved=True)
        return supportrequest_list

    def get_context_data(self, **kwargs):
        """Add Meetup object to the context"""
        context = super(SupportRequestsListView, self).get_context_data(**kwargs)
        context['meetup'] = self.meetup
        return context

    def get_meetup_location(self):
        """Add MeetupLocation object to the context"""
        return get_object_or_404(MeetupLocation, slug=self.kwargs['slug'])


class UnapprovedSupportRequestsListView(LoginRequiredMixin, PermissionRequiredMixin,
                                        MeetupLocationMixin, ListView):
    """List unapproved support requests for a meetup"""
    template_name = "meetup/unapproved_support_requests.html"
    model = SupportRequest
    paginate_by = 10

    def get_queryset(self, **kwargs):
        """Set ListView queryset to all unapproved support requests of the meetup"""
        self.meetup = get_object_or_404(Meetup, slug=self.kwargs['meetup_slug'])
        supportrequest_list = SupportRequest.objects.filter(
            meetup=self.meetup, is_approved=False)
        return supportrequest_list

    def get_context_data(self, **kwargs):
        """Add Meetup object to the context"""
        context = super(UnapprovedSupportRequestsListView, self).get_context_data(**kwargs)
        context['meetup'] = self.meetup
        return context

    def get_meetup_location(self):
        """Add MeetupLocation object to the context"""
        return self.meetup_location

    def check_permissions(self, request):
        """Check if the request user has the permission to approve a support request."""
        self.meetup_location = get_object_or_404(MeetupLocation, slug=self.kwargs['slug'])
        return request.user.has_perm('approve_support_request', self.meetup_location)


class ApproveSupportRequestView(LoginRequiredMixin, PermissionRequiredMixin, MeetupLocationMixin,
                                RedirectView):
    """Approve a support request for a meetup"""
    model = SupportRequest
    permanent = False
    raise_exception = True

    def get_redirect_url(self, *args, **kwargs):
        """Approve the support request, send the user a notification and redirect to the unapproved
        support requests' page"""
        self.meetup = get_object_or_404(Meetup, slug=self.kwargs['meetup_slug'])
        support_request = get_object_or_404(SupportRequest, pk=self.kwargs['pk'])
        support_request.is_approved = True
        support_request.save()
        return reverse('unapproved_support_requests', kwargs={'slug': self.meetup_location.slug,
                       'meetup_slug': self.meetup.slug})

    def get_meetup_location(self):
        """Add MeetupLocation object to the context"""
        return self.meetup_location

    def check_permissions(self, request):
        """Check if the request user has the permission to approve a support request."""
        self.meetup_location = get_object_or_404(MeetupLocation, slug=self.kwargs['slug'])
        return request.user.has_perm('approve_support_request', self.meetup_location)


class RejectSupportRequestView(LoginRequiredMixin, PermissionRequiredMixin, MeetupLocationMixin,
                               RedirectView):
    """Reject a support request for a meetup"""
    model = SupportRequest
    permanent = False
    raise_exception = True

    def get_redirect_url(self, *args, **kwargs):
        """Delete the support request and redirect to the unapproved support requests' page"""
        self.meetup = get_object_or_404(Meetup, slug=self.kwargs['meetup_slug'])
        support_request = get_object_or_404(SupportRequest, pk=self.kwargs['pk'])
        support_request.delete()
        return reverse('unapproved_support_requests', kwargs={'slug': self.meetup_location.slug,
                       'meetup_slug': self.meetup.slug})

    def get_meetup_location(self):
        """Add MeetupLocation object to the context"""
        return self.meetup_location

    def check_permissions(self, request):
        """Check if the request user has the permission to reject a support request."""
        self.meetup_location = get_object_or_404(MeetupLocation, slug=self.kwargs['slug'])
        return request.user.has_perm('reject_support_request', self.meetup_location)


class AddSupportRequestCommentView(LoginRequiredMixin, PermissionRequiredMixin,
                                   MeetupLocationMixin, CreateView):
    """Add a comment to a Support Request"""
    template_name = "meetup/add_comment.html"
    model = Comment
    form_class = AddSupportRequestCommentForm
    raise_exception = True

    def get_success_url(self):
        """Redirect to the support request view page in case of successful submission"""
        return reverse('view_support_request', kwargs={'slug': self.meetup_location.slug,
                       'meetup_slug': self.meetup.slug, 'pk': self.support_request.pk})

    def get_form_kwargs(self):
        """Add support request object and request user to the form kwargs. Used to autofill form
        fields with content_object and author without explicitly filling them up in the form."""
        kwargs = super(AddSupportRequestCommentView, self).get_form_kwargs()
        self.meetup = get_object_or_404(Meetup, slug=self.kwargs['meetup_slug'])
        self.support_request = get_object_or_404(SupportRequest, pk=self.kwargs['pk'])
        kwargs.update({'content_object': self.support_request})
        kwargs.update({'author': self.request.user})
        return kwargs

    def get_context_data(self, **kwargs):
        """Add Meetup and SupportRequest objects to the context"""
        context = super(AddSupportRequestCommentView, self).get_context_data(**kwargs)
        context['meetup'] = self.meetup
        context['support_request'] = self.support_request
        return context

    def get_meetup_location(self):
        """Add MeetupLocation object to the context"""
        return self.meetup_location

    def check_permissions(self, request):
        """Check if the request user has the permission to add a comment to a Support Request.
        The permission holds true for superusers."""
        self.meetup_location = get_object_or_404(MeetupLocation, slug=self.kwargs['slug'])
        return request.user.has_perm('add_support_request_comment', self.meetup_location)


class EditSupportRequestCommentView(LoginRequiredMixin, PermissionRequiredMixin,
                                    MeetupLocationMixin, UpdateView):
    """Edit a support request's comment"""
    template_name = "meetup/edit_comment.html"
    model = Comment
    pk_url_kwarg = "comment_pk"
    form_class = EditSupportRequestCommentForm
    raise_exception = True

    def get_success_url(self):
        """Redirect to the support request view page in case of successful submission"""
        self.get_meetup_location()
        return reverse("view_support_request", kwargs={"slug": self.meetup_location.slug,
                                                       "meetup_slug": self.meetup.slug,
                                                       "pk": self.support_request.pk})

    def get_context_data(self, **kwargs):
        """Add Meetup and SupportRequest objects to the context"""
        context = super(EditSupportRequestCommentView, self).get_context_data(**kwargs)
        context['meetup'] = self.meetup
        context['support_request'] = self.support_request
        return context

    def get_meetup_location(self):
        """Add MeetupLocation object to the context"""
        self.meetup_location = get_object_or_404(MeetupLocation, slug=self.kwargs['slug'])
        self.meetup = get_object_or_404(Meetup, slug=self.kwargs['meetup_slug'])
        self.support_request = get_object_or_404(SupportRequest, pk=self.kwargs['pk'])
        return self.meetup_location

    def check_permissions(self, request):
        """Check if the request user has the permission to edit a comment to a Support Request"""
        self.comment = get_object_or_404(Comment, pk=self.kwargs['comment_pk'])
        systersuser = get_object_or_404(SystersUser, user=request.user)
        return systersuser == self.comment.author


class DeleteSupportRequestCommentView(LoginRequiredMixin, PermissionRequiredMixin,
                                      MeetupLocationMixin, DeleteView):
    """Delete a support request's comment"""
    template_name = "meetup/comment_confirm_delete.html"
    model = Comment
    pk_url_kwarg = "comment_pk"
    raise_exception = True

    def get_success_url(self):
        """Redirect to the support request view page in case of successful submission"""
        self.get_meetup_location()
        return reverse("view_support_request", kwargs={"slug": self.meetup_location.slug,
                                                       "meetup_slug": self.meetup.slug,
                                                       "pk": self.support_request.pk})

    def get_context_data(self, **kwargs):
        """Add Meetup and SupportRequest objects to the context"""
        context = super(DeleteSupportRequestCommentView, self).get_context_data(**kwargs)
        context['meetup'] = self.meetup
        context['support_request'] = self.support_request
        return context

    def get_meetup_location(self):
        """Add MeetupLocation object to the context"""
        self.meetup_location = get_object_or_404(MeetupLocation, slug=self.kwargs['slug'])
        self.meetup = get_object_or_404(Meetup, slug=self.kwargs['meetup_slug'])
        self.support_request = get_object_or_404(SupportRequest, pk=self.kwargs['pk'])
        return self.meetup_location

    def check_permissions(self, request):
        """Check if the request user has the permission to edit a Support Request for a meetup"""
        self.comment = get_object_or_404(Comment, pk=self.kwargs['comment_pk'])
        systersuser = get_object_or_404(SystersUser, user=request.user)
        return systersuser == self.comment.author
