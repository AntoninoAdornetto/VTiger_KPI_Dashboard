import requests, json, datetime, collections, time, pytz

class Vtiger_api:
    def __init__(self, username, access_key, host):

        self.username = username
        self.access_key = access_key
        self.host = host

        self.first_name, self.last_name, self.primary_email, self.utc_offset = self.get_user_personal_info()

    def api_call(self, url):
        '''
        Accepts a URL and returns the text
        '''
        r = requests.get(url, auth=(self.username, self.access_key))
        header_dict = r.headers

        #We're only allowed 60 API requests per minute. 
        #When we are close to reaching this limit,
        #We pause for the remaining time until it resets.
        if int(header_dict['X-FloodControl-Remaining']) <= 5:
            self.seconds_to_wait = abs(int(header_dict['X-FloodControl-Reset']) - int(time.time()))
            time.sleep(self.seconds_to_wait)
            self.seconds_to_wait = 0
        r_text = json.loads(r.text)
        return r_text

    def get_all_data(self):
        '''
        Returns data about all modules within VTiger
        '''
        data = self.api_call(f"{self.host}/listtypes?fieldTypeList=null")
        return data

    def get_module_data(self, module):
        '''
        Get information about a module's fields, Cases in this example
        url = f"{host}/describe?elementType=Cases"
        '''
        data = self.api_call(f"{self.host}/describe?elementType={module}")
        return data

    def get_user_personal_info(self):
        '''
        Retrieves the name, email and utc_offset of the user whose credentials are used to run this script
        '''
        data = self.api_call(f"{self.host}/me")
        first_name = data['result']['first_name']
        last_name = data['result']['last_name']
        email = data['result']['email1']
        
        #Time zone is presented as 'America/New_York'
        #pytz is used to determine the utc_offset based on the time zone
        timezone = data['result']['time_zone']
        current_time = datetime.datetime.now().astimezone(pytz.timezone(timezone))
        utc_offset = current_time.utcoffset().total_seconds()/60/60

        return first_name, last_name, email, utc_offset


    def get_users(self):    
        '''
        Accepts User List and returns a dictionary of the username, first, last and id
        '''
        user_list = self.api_call(f"{self.host}/query?query=Select * FROM Users;")
        
        num_of_users = len(user_list['result'])
        username_list = []
        for user in range(num_of_users):
            username_list.append(user_list['result'][user]['id'])
            
        #Creates a dictionary with every username as the key and an empty list as the value
        user_dict = {i : [] for i in username_list}

        #Assigns a list of the first name, last name and User ID to the username
        for username in range(num_of_users): 
            user_dict[username_list[username]] = [user_list['result'][username]['first_name'], user_list['result'][username]['last_name'], user_list['result'][username]['user_name'], user_list['result'][username]['user_primary_group']]       
        
        self.full_user_dict = user_dict
        return user_dict


    def get_groups(self):    
        '''
        Accepts Group List and returns a dictionary of the Group Name and ID
        '''
        group_list = self.api_call(f"{self.host}/query?query=Select * FROM Groups;")

        num_of_groups = len(group_list['result'])
        groupname_list = []
        for group in range(num_of_groups):
            groupname_list.append(group_list['result'][group]['groupname'])
            
        #Creates a dictionary with every group name as the key and an empty list as the value
        group_dict = {i : [] for i in groupname_list}

        #Assigns a list of the first name, last name and User ID to the username
        for groupname in range(num_of_groups): 
            group_dict[groupname_list[groupname]] = group_list['result'][groupname]['id']  
        return group_dict


    def case_count(self, group_id, case_type = 'all', date = ''):
        '''
        Returns an int equal to the number of cases requested by the specific URL.
        This count is used by self.get_all_open_cases() to retrieve the total number of cases,
        the number of cases opened this month and the number of cases closed this month.
        '''
        if case_type == 'all':
            case_amount = self.api_call(f"{self.host}/query?query=SELECT COUNT(*) FROM Cases WHERE group_id = {group_id} AND casestatus != 'closed' AND casestatus != 'resolved';")
        elif case_type == 'month_closed':
            case_amount = self.api_call(f"{self.host}/query?query=SELECT COUNT(*) FROM Cases WHERE group_id = {group_id} AND casestatus = 'closed' AND sla_actual_closureon >= '{date}' limit 0, 100;")
        elif case_type == 'month_resolved':
            case_amount = self.api_call(f"{self.host}/query?query=SELECT COUNT(*) FROM Cases WHERE group_id = {group_id} AND casestatus = 'resolved' AND sla_actual_closureon >= '{date}' limit 0, 100;")
        elif case_type == 'month_open':
            case_amount = self.api_call(f"{self.host}/query?query=SELECT COUNT(*) FROM Cases WHERE group_id = {group_id} AND  createdtime >= '{date}' limit 0, 100;")

        num_cases = case_amount['result'][0]['count']
        return num_cases

    def get_all_open_cases(self, group_id, case_type = 'all'):
        '''
        A module can only return a maximum of 100 results. To circumvent that, an offset can be supplied which starts returning data from after the offset.
        The amount must be looped through in order to retrieve all the results.
        For instance if there are 250 cases, first 100 is retrieved, then another 100, and then 50.
        A list is returned of each dictionary that was retrieved this way.
        This same method is used to return data for cases asked for in a specific time frame.
        '''
        if case_type =='all':
            num_cases = int(self.case_count(group_id))
        elif case_type == 'month_closed' or case_type == 'month_resolved' or case_type == 'month_open':
            first_of_month = self.beginning_of_month()
            num_cases = int(self.case_count(group_id, case_type, first_of_month))

        case_list = []
        offset = 0
        if num_cases > 100:
            while num_cases > 100:
                if case_type == 'all':
                    cases = self.api_call(f"{self.host}/query?query=Select * FROM Cases WHERE group_id = {group_id} AND casestatus != 'resolved' AND casestatus != 'closed' limit {offset}, 100;")
                elif case_type == 'month_closed':
                    cases = self.api_call(f"{self.host}/query?query=Select * FROM Cases WHERE group_id = {group_id} AND casestatus = 'closed' AND sla_actual_closureon >= '{first_of_month}' limit {offset}, 100;")
                elif case_type == 'month_resolved':
                    cases = self.api_call(f"{self.host}/query?query=Select * FROM Cases WHERE group_id = {group_id} AND casestatus = 'resolved' AND sla_actual_closureon >= '{first_of_month}' limit {offset}, 100;")
                elif case_type == 'month_open': 
                    cases = self.api_call(f"{self.host}/query?query=Select * FROM Cases WHERE group_id = {group_id} AND createdtime >= '{first_of_month}' limit {offset}, 100;")

                case_list.append(cases['result'])
                offset += 100
                num_cases = num_cases - offset
                if num_cases <= 100:
                    break
        if num_cases <= 100:
            if case_type == 'all':
                cases = self.api_call(f"{self.host}/query?query=Select * FROM Cases WHERE group_id = {group_id} AND casestatus != 'resolved' AND casestatus != 'closed' limit {offset}, 100;")
            elif case_type == 'month_closed':
                cases = self.api_call(f"{self.host}/query?query=Select * FROM Cases WHERE group_id = {group_id} AND casestatus = 'closed' AND sla_actual_closureon >= '{first_of_month}' limit {offset}, 100;")
            elif case_type == 'month_resolved':
                cases = self.api_call(f"{self.host}/query?query=Select * FROM Cases WHERE group_id = {group_id} AND casestatus = 'resolved' AND sla_actual_closureon >= '{first_of_month}' limit {offset}, 100;")
            elif case_type == 'month_open':
                cases = self.api_call(f"{self.host}/query?query=Select * FROM Cases WHERE group_id = {group_id} AND createdtime >= '{first_of_month}' limit {offset}, 100;")

            case_list.append(cases['result'])
        
        #Combine the multiple lists of dictionaries into one list
        #Before: [[{case1}, {case2}], [{case 101}, {case 102}]]
        #After: [{case1}, {case2}, {case 101}, {case 102}]
        full_case_list = []
        for caselist in case_list:
            full_case_list += caselist

        if case_type == 'month_closed':
            self.month_closed_case_list = full_case_list
        elif case_type == 'month_resolved':
            self.month_resolved_case_list = full_case_list
        elif case_type == 'month_open':
            self.month_open_case_list = full_case_list
        return full_case_list

    def beginning_of_week(self):
        '''
        For whichever day of the week it is, this past Monday at 12:00am is returned.
        Today = datetime.datetime(2019, 9, 5, 15, 31, 13, 134153)
        Returns: 2019-09-02 00:00:00
        '''
        today = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        #0 = monday, 5 = Saturday, 6 = Sunday 
        day = today.weekday()
        first_of_week = today + datetime.timedelta(days = -day)

        #Case created time is displayed in UTC, but VTiger is configured to display data in the user's
        #configured time zone. As an example:
        #A case might return a created time of '2019-12-02 01:00:44 UTC', 
        #but the created time displayed in VTiger is 12-01-2019 08:00 PM EST.
        #This case should not be part of the week's data since it appears to be from the previous week
        #according to the user. Therefore, we add the offset to the time.
        #If the user has an offset of -5 (EST), then the first of the week would now be 2019-12-02 05:00:00
        first_of_week = first_of_week - datetime.timedelta(hours = self.utc_offset)
        return first_of_week

    def beginning_of_month(self):
        '''
        For whichever day of the month it is, the first day of the month is returned.
        Today = 2019-11-25 17:50:53.445677
        Returns: 2019-11-01 00:00:00
        '''
        first_of_month = datetime.datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        #Case created time is displayed in UTC, but VTiger is configured to display data in the user's
        #configured time zone. As an example:
        #A case might return a created time of '2019-12-01 01:00:44 UTC', 
        #but the created time displayed in VTiger is 11-30-2019 08:00 PM EST.
        #This case should not be part of the month's data since it appears to be from the previous month
        #according to the user. Therefore, we add the offset to the time.
        #If the user has an offset of -5 (EST), then the first of the month would now be 2019-12-01 05:00:00
        first_of_month = first_of_month - datetime.timedelta(hours = self.utc_offset)
        return first_of_month

if __name__ == '__main__':
        with open('credentials.json') as f:
            data = f.read()
        credential_dict = json.loads(data)
        vtigerapi = Vtiger_api(credential_dict['username'], credential_dict['access_key'], credential_dict['host'])
        groupdict = vtigerapi.get_groups()
        data = vtigerapi.get_all_data()
        data = json.dumps(data,  indent=4, sort_keys=True)
        with open('all_data.json', 'w') as f:
            f.write(data)

        data = vtigerapi.get_module_data("PhoneCalls")
        data = json.dumps(data,  indent=4, sort_keys=True)
        with open('module_data.json', 'w') as f:
            f.write(data)     