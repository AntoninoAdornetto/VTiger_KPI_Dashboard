from django.shortcuts import render, HttpResponseRedirect
from django.utils import timezone
from django.utils.timezone import make_aware
from .models import Phone_call, Opportunities
import VTiger_Sales_API
import datetime

def home_view(request):
    '''
    The primary view for the Sales Dashboard where all the calculations take place.
    Celery populates the opportunities and phone calls from today periodically.
    '''
    date_request = request.GET.get('date_start')
    if date_request == '' or date_request == None:
        today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        today = make_aware(datetime.datetime.strptime(date_request, '%Y-%m-%d'))

    end_of_day = today.replace(hour=23, minute = 59, second = 59, microsecond = 0)

    all_sales_opps = Opportunities.objects.all().filter(assigned_groupname='Sales')
    all_sales_calls = Phone_call.objects.all().filter(assigned_groupname='Sales')

    sales_users = all_sales_opps.values('assigned_username').distinct()

    today_opps = all_sales_opps.filter(modifiedtime__gte=today, modifiedtime__lte=end_of_day).order_by('-modifiedtime')
    today_phone_calls = all_sales_calls.filter(modifiedtime__gte=today, modifiedtime__lte=end_of_day).order_by('-modifiedtime')

    #user_dict is the total score for both phone calls and opportunity stage changes
    user_total_score = {}
    #user_opp_dict is how many times each sales stage changed in the given time frame
    user_opp_dict = {}
    #User specific phone calls and opportunities
    user_opps = {}
    user_calls = {}

    for user in sales_users:
        user_total_score[user['assigned_username']] = 0
        user_opp_dict[user['assigned_username']] = {
            'Demo Scheduled':0,
            'Demo Given':0,
            'Quote Sent':0,
            'Pilot':0,
            'Needs Analysis':0,
            'Closed Won':0,
            'Closed Lost':0,
            'Phone Calls':0,
        }
        #If we want to display opp and phone call data per user
        #user_opps[user['assigned_username']] = today_opps.filter(assigned_username=user['assigned_username'])
        #user_calls[user['assigned_username']] = today_phone_calls.filter(assigned_username=user['assigned_username'])


    for opp in today_opps:
        #if opp.assigned_username in user_total_score:
        #    user_total_score[opp.assigned_username] += 1

        if opp.demo_scheduled_changed_at != None and opp.demo_scheduled_changed_at > today and opp.demo_scheduled_changed_at < end_of_day:
            user_opp_dict[opp.assigned_username]['Demo Scheduled'] += 1
            user_total_score[opp.assigned_username] += 5
        if opp.demo_given_changed_at != None and opp.demo_given_changed_at > today and opp.demo_given_changed_at < end_of_day:
            user_opp_dict[opp.assigned_username]['Demo Given'] += 1
            user_total_score[opp.assigned_username] += 10
        if opp.quote_sent_changed_at != None and opp.quote_sent_changed_at > today and opp.quote_sent_changed_at < end_of_day:
            user_opp_dict[opp.assigned_username]['Quote Sent'] += 1
        if opp.pilot_changed_at != None and opp.pilot_changed_at > today and opp.pilot_changed_at < end_of_day:
            user_opp_dict[opp.assigned_username]['Pilot'] += 1
        if opp.needs_analysis_changed_at != None and opp.needs_analysis_changed_at > today and opp.needs_analysis_changed_at < end_of_day:
            user_opp_dict[opp.assigned_username]['Needs Analysis'] += 1
        if opp.closed_won_changed_at != None and opp.closed_won_changed_at > today and opp.closed_won_changed_at < end_of_day:
            user_opp_dict[opp.assigned_username]['Closed Won'] += 1
        if opp.closed_lost_changed_at != None and opp.closed_lost_changed_at > today and opp.closed_lost_changed_at < end_of_day:
            user_opp_dict[opp.assigned_username]['Closed Lost'] += 1

    for call in today_phone_calls:
        if call.assigned_username in user_total_score:
            user_total_score[call.assigned_username] += 1
            user_opp_dict[call.assigned_username]['Phone Calls'] += 1

    context = {
        'user_total_score':user_total_score,
        'user_opp_dict': user_opp_dict,
        'user_opps':user_opps,
        'user_calls':user_calls,
        'today_opps':today_opps,
        'today_phone_calls':today_phone_calls,
        'today_date': today.strftime('%A, %B %d'),
    }

    return render(request, "dashboard/dashboard.html", context) 

def populate_db(request):
    '''
    Populates the opportunities and phone calls databases.
    '''
    from dashboard.tasks import get_opportunities
    get_opportunities()

    from dashboard.tasks import get_phonecalls
    get_phonecalls()

    return HttpResponseRedirect('/')

def populate_db_month(request):
    '''
    Populates the opportunities and phone calls databases from the past 3 months.
    '''
    from dashboard.tasks import get_opportunities
    get_opportunities(day='month')

    from dashboard.tasks import get_phonecalls
    get_phonecalls(day='month')

    return HttpResponseRedirect('/')

def delete_all_items(request):
    '''
    Delete all the items in the database from today only.
    Convenient to reset the day's data without deleting previous days' data.
    '''
    today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = timezone.now().replace(hour=23, minute=59, second=59, microsecond=0)
    today_opps = Opportunities.objects.all().filter(date_modified__gte=today_start, date_modified__lte=today_end)
    today_calls = Phone_call.objects.all().filter(date_modified__gte=today_start, date_modified__lte=today_end)

    today_opps.delete()
    today_calls.delete()

    #This deletes all items:
    #today_opps.objects.all().delete()
    #today_calls.objects.all().delete()
    return HttpResponseRedirect('/')

def test_method(request):
    '''
    localhost:8000/test
    Useful for testing functionality
    '''
    print('test!')
    return HttpResponseRedirect('/')