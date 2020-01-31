from django.shortcuts import render, HttpResponseRedirect
from django.db.models import Sum
from .models import Sales_stats
import VTiger_Sales_API
import json, os

# Create your views here.
def home_view(request):
    '''
    Loads the main page. 
    If there is no data in the database, then the populate url is called
    Which automatically pulls data from the database.
    '''
    try:
        sales_stats = Sales_stats
        stats = sales_stats.objects.all()
        user_stat_dict, user_score_dict = sales_stats.user_totals()

        return render(request, 'dashboard/dashboard.html', {'stats':stats, 'stat_total':user_stat_dict, 'score_total':user_score_dict,})
    except TypeError:
        return HttpResponseRedirect('/populate/')

def populate_db(request):
    '''
    Populates the database with stats from vtigerapi.db_update()
    demo_scheduled, demo_given, quote_sent, pilot, needs_analysis, closed_won, closed_lost, phone_calls, date, user
    {james_frinkle:[0, 1, 15, 0, 0, 3, 6, '215', '2020-01-28 21:30:00', 'james_frinkle']}
    '''
    user_stat_dict = retrieve_stats()
    for value in user_stat_dict.values():
        stat = Sales_stats()
        stat.demo_scheduled = value[0]
        stat.demo_given = value[1]
        stat.quote_sent = value[2]
        stat.pilot = value[3]
        stat.needs_analysis = value[4]
        stat.closed_won = value[5]
        stat.closed_lost = value[6]
        stat.phone_calls = value[7]
        stat.date = value[8]
        stat.user = value[9]
        stat.save()
    return HttpResponseRedirect('/')

def retrieve_stats():
    '''
    Create a file named 'credentials.json' with VTiger credentials
    and put it in the main sales_dashboard directory.
    It should have the following format:
    {"username": "(user)", "access_key": "(access_key)", "host": "(host)"}
    '''
    credentials_file = 'credentials.json'
    credentials_path = os.path.join(os.path.abspath('.'), credentials_file)
    with open(credentials_path) as f:
        data = f.read()
    credential_dict = json.loads(data)
    vtigerapi = VTiger_Sales_API.Vtiger_api(credential_dict['username'], credential_dict['access_key'], credential_dict['host'])
    user_stat_dict = vtigerapi.retrieve_data()

    return user_stat_dict