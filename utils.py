#!/usr/bin/python
# -*- coding: utf -*-

# utils
def is_float(value):
    try:
        float(value)
        return True
    except ValueError:
        return False

def is_percentage(value):
    if is_float(value):
        value = float(value)
        return True if (value > 0 and value < 100) else False
    return False

def is_date(value):
    import time

    try:
        time.strptime(value, '%Y-%m-%d')
        return True
    except ValueError:
        return False

def get_date_ranges():
    return [
        {'name':'Today', 'slug':'today'},
        {'name':'This week', 'slug':'this-week'},
        {'name':'Last 14 days', 'slug':'last-14-days'},
        {'name':'This month', 'slug':'this-month'},
        {'name':'Last 3 months', 'slug':'last-3-months'},
    ]

def translate_date_range(value):
    from datetime import date, timedelta

    today = date.today()
    if not value:
        return None
    elif value == 'today':
        return {'low':today, 'high':today}
    elif value == 'this-week':
        return {'low':today - timedelta(7), 'high':today}
    elif value == 'last-two_weeks' or value == 'last-2-weeks' or value == 'last-14-days':
        return {'low':today - timedelta(14), 'high':today}
    elif value == 'this-month':
        return {'low':today - timedelta(30), 'high':today}
    elif value == 'last-3-months':
        return {'low':today - timedelta(90), 'high':today}
    else:
        return {'low':'', 'high':''}

def slugify(value):
    import unicodedata, re

    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore')
    value = unicode(re.sub('[^\w\s-]', '', value).strip().lower())
    return re.sub('[-\s]+', '-', value)

def generate_random_key():
    import base64, hashlib, random

    return base64.b64encode(hashlib.sha256(str(random.getrandbits(256))).digest(),
                     random.choice(['rA','aZ','gQ','hH','hG','aR','DD'])).rstrip('==')

def today_date():
    from datetime import date

    return date.today()

def today_timestamp():
    import time

    return time.time()

def tomorrow_timestamp():
    return today_timestamp() + (60*60*24)

def date_difference(begin, end, separator='-'):
    '''Get the time difference in days between two dates'''
    import datetime
    
    def parse(date, separator):
        '''Deal with dates that are already in datetime format or parse them from string'''
        if type(date).__name__ == 'date': return date
        a, b, c = (int(x) for x in date.split(separator))
        return datetime.date(a, b, c)

    return (parse(end, separator) - parse(begin, separator)).days