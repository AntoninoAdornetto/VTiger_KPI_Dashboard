from django.shortcuts import render, HttpResponseRedirect
from django.utils import timezone
from django.db.models import Q

from .tasks import populate_db_celery_cases
from .models import Cases

def main_dashboard(request):
    '''
    Send all cases from the Cases db to the html template to be used in the html table.
    Send all unique group names in the context so that it can be used in a dropdown.
    Get the data from the form inputs like "group name" and filter the cases to be displayed.
    '''
    #Returns all cases with the most recently modified first if no filter is applied
    full_cases = Cases.objects.all().order_by('-modifiedtime')
    #Returns dictionary with "assigned_groupname" as key, and the actual name as the value.
    #We pass these groups to the html to populate the drop down menu for filtering
    case_groups = Cases.objects.values('assigned_groupname').distinct()

    #We get the form submission from the drop down and use it to then filter the "full_case"
    #query set to only return and display the cases which match that group.
    group_request = request.GET.get('group_dropdown')
    if group_request != '' and group_request is not None and group_request != '--Select Group--':
        full_cases = full_cases.filter(assigned_groupname=group_request)

    date_start_request = request.GET.get('date_start')
    date_end_request = request.GET.get('date_end')

    if date_start_request != '' and date_start_request is not None:
        full_cases = full_cases.filter(modifiedtime__gte=date_start_request)

    if date_end_request != '' and date_end_request is not None:
        full_cases = full_cases.filter(modifiedtime__lt=date_end_request)

    #Prepare calculated data to present as a simple summary overview of the cases
    case_stats_dict = {}
    case_stats = full_cases
    case_stats_closed = case_stats.filter(Q(casestatus="Resolved") | Q(casestatus="Closed"))
    case_stats_dict['closed'] = len(case_stats_closed)
    if date_start_request != '' and date_start_request is not None and date_end_request != '' and date_end_request is not None:
        try:
            case_stats_opened = case_stats.filter(createdtime__gte=date_start_request, createdtime__lte=date_end_request)
            case_stats_dict['opened'] = len(case_stats_opened)
        except ValueError:
            case_stats_dict['opened'] = 0

    #After returning the request, return the html file to go to, and the context to send to the html
    return render(request, "dashboard/case_dashboard.html", {"full_cases":full_cases, "case_groups":case_groups, "case_stat_dict":case_stats_dict})

def populate_cases(request):
    populate_db_celery_cases()
    return HttpResponseRedirect("/cases")

def delete_all_cases(request):
    '''
    Delete all the cases in the database from today only.
    Convenient to reset the day's data without deleting previous days' data.
    '''
    today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = timezone.now().replace(hour=23, minute=59, second=59, microsecond=0)
    cases = Cases.objects.all().filter(date_modified__gte=today_start, date_modified__lte=today_end)

    cases.delete()

    #This deletes all items:
    #Cases.objects.all().delete()
    return HttpResponseRedirect('/cases')