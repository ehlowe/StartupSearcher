from core.database import models

def crunchbase_data_to_dict(data):
    return_data = []
    for row in data:
        return_data.append(crunchbase_row_to_dict(row))
    return return_data

def crunchbase_row_to_dict(row):
    row_dict={}
    keys=list(models.crunchbase_fields.keys())
    for i, value in enumerate(row):
        row_dict[keys[i]]=value
    return row_dict
