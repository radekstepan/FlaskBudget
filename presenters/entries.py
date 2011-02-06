# framework
from flaskext.sqlalchemy import Pagination

# utils
from utils import *

def index(model, date=None, category=None, page=1, items_per_page=10):
    '''A helper function listing expense/income entries as needed'''

    # fetch entries
    entries = model.get_entries()

    # categories
    categories = model.get_categories()
    # provided category?
    if category:
        # search for the slug
        category_id = model.is_category(slug=category)
        if category_id:
            entries = model.get_entries(category_id=category_id)

    # provided a date range?
    date_range = translate_date_range(date)
    if date_range:
        entries = model.get_entries(date_from=date_range['low'], date_to=date_range['high'])
    # date ranges for the template
    date_ranges = get_date_ranges()

    # build a paginator
    paginator = Pagination(entries, page, items_per_page, entries.count(),
                           entries.offset((page - 1) * items_per_page).limit(items_per_page))

    return locals()

def add_category(model, new_category_name):
    '''A helper function for adding expense/income categories'''

    error = None
    # blank name?
    if new_category_name:
        # already exists?
        if not model.is_category(name=new_category_name):

            # create category
            model.add_category(new_category_name)

        else: error = 'You already have a category under that name'
    else: error = 'You need to provide a name'

    return error