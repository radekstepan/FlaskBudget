# utils
def is_float(value):
    try:
        num = float(value)
        return True
    except ValueError:
        return False