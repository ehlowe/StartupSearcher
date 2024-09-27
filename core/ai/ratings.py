import os

from openai import OpenAI
import psycopg2

from core.database import models
from core.ai import providers



def stream_data_processing_thread(shared_data_dict, companies_context_prompt, user_input):
    prompt=[
        {
        "role": "system",
        "content":  "You are to give a rating 0-5 for a each company given to you. Format your response as follows 'ID: 0 | Thoughts on company in relation to user's message | Rating: 5\nID: 1 | Thoughts on company in relation to user's message | Rating: 4\n...' where 0 is the ID of the company and 5 is the rating you give the company." 
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
                    print(rating_list[-1])
                temp_string=""
        else:
            print("LAST STRING")
            print(temp_string)
            rating_list.append(int(temp_string.split("Rating:")[-1].strip()))
            shared_data_dict["ratings"]=rating_list
            print(rating_list[-1])


def get_companies_prompt():
    conn = psycopg2.connect(
        dbname="startup_database",
        user="postgres",
        password=os.getenv("DB_PASSWORD"),
        host="localhost",
        port="5432"
    )
    cur = conn.cursor()
    cur.execute("SELECT * FROM crunchbase ORDER BY CB_Rank LIMIT 200")
    records = cur.fetchall()
    # print(records)
    cur.close()
    conn.close()

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