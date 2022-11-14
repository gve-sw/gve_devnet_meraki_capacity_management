from datetime import datetime, timedelta, date
import dateutil.parser
from dateutil.relativedelta import relativedelta
import calendar


'''
Returns the current date as string or datetime object
'''
def get_today(frmt='%Y-%m-%d %H:%M:%S', string=True): 
    date = datetime.now()
    if string:
        return date.strftime(frmt)
    return date


'''
Returns the current date - x days as string or datetime object
'''
def get_today_minus_x_day(delta, frmt='%Y-%m-%d %H:%M:%S', string=True):
    date = datetime.now() - timedelta(delta)
    if string:
        return date.strftime(frmt)
    return date


'''
Returns the first day of the current month as string or datetime object
'''
def get_first_day_of_current_month(frmt='%Y-%m-%d %H:%M:%S', string=True):
    date = datetime.today().replace(day=1)
    if string:
        return date.strftime(frmt)
    return date


'''
Returns the first day of a provided month as string or datetime object
'''
def get_first_day_of_selected_month(month, frmt='%Y-%m-%d %H:%M:%S', string=True):
    month_date = string_to_date(month)
    first_day_date = month_date.replace(day=1)
    if string:
        return first_day_date.strftime(frmt)
    return first_day_date


'''
Returns the last day of a provided month as string or datetime object
'''
def get_last_day_of_selected_month(month, frmt='%Y-%m-%d %H:%M:%S', string=True):
    month_date = string_to_date(month)
    last_day_date = date(month_date.year, month_date.month, calendar.monthrange(month_date.year, month_date.month)[-1])
    if string:
        return last_day_date.strftime(frmt)
    return last_day_date


'''
Returns the current month
'''
def get_month():
    month = datetime.now().month
    return month


'''
Returns the current year
'''
def get_year():
    year = datetime.now().year
    return year


'''
Converts a string to a datetime object
'''
def string_to_date(string_date):
    date = dateutil.parser.parse(string_date)
    return date


'''
Converts a datetime object to string
'''
def date_to_string(date, frmt='%Y-%m-%d %H:%M:%S'):
    return date.strftime(frmt)


'''
Returns a list of strings with the format yyyy-mm for the last x months
'''
def get_last_x_month_year_strings(months_count):
    list_of_months_year_strings = []
    today = get_today(string=False)
    for x in range(months_count):
        previous_month = today + relativedelta(months=-x)
        previous_month_string = date_to_string(previous_month, frmt='%Y-%m')
        list_of_months_year_strings.append(previous_month_string)
    
    return list_of_months_year_strings


'''
Check if a date (format: yyyy-mm) is in the current month
'''
def date_is_current_month(compare_year_month_string):
    current_month = get_month()
    compare_month = compare_year_month_string.split("-")[1]
    return int(current_month) == int(compare_month)