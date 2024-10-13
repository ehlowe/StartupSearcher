import os
import json
from datetime import datetime

def process_raw_row_data(input_row_data):
    """Converts raw data to a dictionary"""
    row_categories = [
        None, 'short_description', 'employees', 'industries', 'cb_rank', 'company_name', 
        'founded_date', 'long_description', 'headquarters_location', 'last_funding_type', 
        'most_recent_valuation', 'funding_status', 'industry_groups', 'acquisition_status', 
        'actively_hiring', 'linkedin', 'estimated_revenue', 'website', 'total_funding_amount'
    ]
    try:
        row_processed={}
        for i, item in enumerate(input_row_data):
            if item=='â€”':
                item=None
            if item=='':
                item=None

            if item!=None:
                if row_categories[i]=='Employees':
                    try:
                        item=(int(item.split('-')[0].strip()))
                    except:
                        item=0
                elif row_categories[i]=='CB Rank':
                    try:
                        item=int(item.replace(",",""))
                    except:
                        pass
                elif row_categories[i]=='Founded Date':
                    item = convert_date_for_sqlite(item)
                row_processed[row_categories[i]]=item
    except Exception as e:
        raise e

    return prepare_data(row_processed)

def prepare_data(input_data):
    """Converts raw dictionary to a database ready dictionary"""
    return {
        'short_description': input_data.get('short_description', ''),
        'employees': input_data.get('employees', None),
        'industries': input_data.get('industries', ''),
        'cb_rank': input_data.get('cb_rank', None),
        'company_name': input_data.get('company_name', ''),
        'founded_date': input_data.get('founded_date', None),
        'long_description': input_data.get('long_description', ''),
        'headquarters_location': input_data.get('headquarters_location', ''),
        'last_funding_type': input_data.get('last_funding_type', ''),
        'most_recent_valuation': input_data.get('most_recent_valuation', ''),
        'funding_status': input_data.get('funding_status', ''),
        'acquisition_status': input_data.get('acquisition_status', ''),
        'actively_hiring': input_data.get('actively_hiring', ''),
        'linkedin': input_data.get('linkedin', ''),
        'estimated_revenue': input_data.get('estimated_revenue', ''),
        'website': input_data.get('website', ''),
        'total_funding_amount': input_data.get('total_funding_amount', None)
    }


def convert_date_for_sqlite(day):
    """figure out which format the date is in then convert it to ISO8601"""
    day = day.replace(',', '')
    try:
        date_object = datetime.strptime(day, '%b %d %Y')
    except ValueError:
        try:
            date_object = datetime.strptime(day, '%b %Y')
        except ValueError:
            date_object = datetime.strptime(day, '%Y')

    sqlite_date = date_object.strftime('%Y-%m-%d')

    return sqlite_date

def raw_database_to_sql_database_converter(data_file_path='raw_crunchbase_data.json'):
    """Load the raw data from the json file"""
    raw_crunchbase_data=json.loads(open(data_file_path).read())
    sql_ready_data=[]
    for key, value in raw_crunchbase_data.items(): 
        processed_row=process_raw_row_data(value)
        sql_ready_data.append(processed_row)

    return sql_ready_data