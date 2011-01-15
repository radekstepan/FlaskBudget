import time

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
    try:
        time.strptime(value, '%Y-%m-%d')
        return True
    except ValueError:
        return False