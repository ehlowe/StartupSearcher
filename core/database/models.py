from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum

# row_categories=['Short Description', 'Employees','Industries','CB Rank', 'Company Name','Founded Date','Long Description','Headquarters Location','Last Funding Type','Most Recent Valuation','Funding Status','Industry Groups', 'Acquisition Status', 'Actively Hiring', 'Linkedin', 'Estimated Revenue','Website','Total Funding Ammount']
# row_types = [
#     'TEXT', 'INTEGER', 'TEXT', 'INTEGER', 'TEXT',
#     'DATE', 'TEXT', 'TEXT', 'TEXT',
#     'TEXT', 'TEXT', 'TEXT', 'TEXT',
#     'TEXT', 'TEXT', 'TEXT', 'TEXT', 'REAL'
# ]

"""Data Structure for crunchbase Table"""
crunchbase_fields = {
    "primary_key": "SERIAL PRIMARY KEY",
    "short_description": "TEXT",
    "employees": "INTEGER",
    "industries": "TEXT",
    "cb_rank": "INTEGER",
    "company_name": "TEXT",
    "founded_date": "DATE",
    "long_description": "TEXT",
    "headquarters_location": "TEXT",
    "last_funding_type": "TEXT",
    "most_recent_valuation": "TEXT",
    "funding_status": "TEXT",
    "acquisition_status": "TEXT",
    "actively_hiring": "TEXT",
    "linkedin": "TEXT",
    "estimated_revenue": "TEXT",
    "website": "TEXT",
    "total_funding_amount": "DECIMAL(15, 2)"
}    

"""Data Structure for industry_connections Table"""
industry_connections_fields = {
    "crunchbase_primary_key": "INTEGER",
    "industry_name": "TEXT",
}


def dict_to_sql_fields(fields):
    field_definitions = [f"{name} {dtype}" for name, dtype in fields.items()]
    fields_str = ',\n    '.join(field_definitions)
    return fields_str