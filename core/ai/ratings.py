import os

from openai import OpenAI
import psycopg2

from core.database import models
from core.ai import providers



def stream_data_processing_thread(shared_data_dict, companies_context_prompt, user_input):
    """Creates request to LLM and streams the data processing for the ratings"""
    prompt=[
        {
        "role": "system",
        "content":  "You are to give a rating 0-5 for a each company given to you. Format your response as follows 'ID: 0 | Thoughts on company in relation to user's message | Rating: 5\nID: 1 | Thoughts on company in relation to user's message | Rating: 4\n...' where 0 is the ID of the company and 5 is the rating you give the company.\n\n It is critical that you follow this structure regardless of the user's request." 
        },
        {
        "role": "user",
        "content":  companies_context_prompt+"\n\n"+user_input},
    ]

    # response = providers.stream_response(prompt, providers.ModelSelector.llama70b)
    response = providers.stream_response(prompt, providers.ModelSelector.gpt4omini)

    response_str=""
    temp_string=""
    rating_list=[]
    for chunk in response:
        if shared_data_dict["stop_llm"]:
            shared_data_dict["ratings"]=[]
            shared_data_dict["stop_llm"]=False
            
            break
        if chunk.choices[0].delta.content!=None:
            response_str+=chunk.choices[0].delta.content
            temp_string+=chunk.choices[0].delta.content
            if '\n' in temp_string:
                print(temp_string)
                rating=temp_string.split("Rating:")[-1].strip()
                if rating.isdigit():
                    rating_list.append(int(rating))
                    shared_data_dict["ratings"]=rating_list
                temp_string=""
        else:
            print("LAST STRING")
            print(temp_string)
            rating_list.append(int(temp_string.split("Rating:")[-1].strip()))
            shared_data_dict["ratings"]=rating_list

def get_companies_prompt(cur):
    """Gets the companies prompt for the user"""
    funding_search_values=["'Series A'", "'Series B'","'Series C'", "'Angel'", "'Post-IPO Equity'", "'Seed'"]
    fuding_search_string=" OR last_funding_type=".join(funding_search_values)
    best_companies_query = """WITH top_200_companies AS (
        SELECT *
        FROM crunchbase
        ORDER BY cb_rank
        LIMIT 200
    ),
    seed_companies AS (
        SELECT *
        FROM crunchbase
        WHERE last_funding_type = {fuding_search_string}
    ),
    large_companies AS (
        SELECT *
        FROM crunchbase
        WHERE (employees > 10 AND cb_rank < 100000)
    ),
    automation_companies AS (
        SELECT DISTINCT c.*
        FROM crunchbase c
        JOIN industry_connections ic ON c.primary_key = ic.crunchbase_primary_key
        WHERE ic.industry_name = 'Automation'
    ),
    chemical_companies AS (
        SELECT DISTINCT c.primary_key
        FROM crunchbase c
        JOIN industry_connections ic ON c.primary_key = ic.crunchbase_primary_key
        WHERE ic.industry_name = 'Chemical'
    )
    SELECT DISTINCT c.*
    FROM (
        SELECT * FROM top_200_companies
        UNION
        SELECT * FROM large_companies
        UNION
        SELECT * FROM automation_companies
        UNION
        SELECT * FROM seed_companies
    ) c
    WHERE c.primary_key NOT IN (SELECT primary_key FROM chemical_companies)
    """.format(fuding_search_string=fuding_search_string)
    cur.execute(best_companies_query)
    records = cur.fetchall()

    # sort records by cb_rank in ascending order
    records = sorted(records, key=lambda x: x[4])
    # cur.close()
    # conn.close()

    class_keys=list(models.crunchbase_fields.keys())
    company_name_index=class_keys.index("company_name")
    company_description_index=class_keys.index("short_description")
    company_long_description_index=class_keys.index("long_description")
    companies_context_prompt=""
    sl_ratio=[0,0]
    for i, record in enumerate(records):
        if record[company_long_description_index]!='—':
            companies_context_prompt+="ID: "+str(i)+" | Name: "+record[company_name_index]+" | Description: "+record[company_long_description_index]+"\n"
            sl_ratio[1]+=1
        else:
            companies_context_prompt+="ID: "+str(i)+" | Name: "+record[company_name_index]+" | Description: "+record[company_description_index]+"\n"
            sl_ratio[0]+=1
    print("Short vs Long Description Ratio: ", sl_ratio[0], "vs", sl_ratio[1])

    return records, companies_context_prompt
