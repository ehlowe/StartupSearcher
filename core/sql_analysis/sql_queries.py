def industry_counts(cur):
    """Returns the count of companies in each industry"""
    cur.execute("""WITH top_companies AS (
        SELECT primary_key
        FROM crunchbase
        ORDER BY cb_rank
        LIMIT 200
    )
    SELECT ic.industry_name, COUNT(*) as company_count
    FROM industry_connections ic
    JOIN top_companies tc ON ic.crunchbase_primary_key = tc.primary_key
    GROUP BY ic.industry_name
    ORDER BY company_count DESC
    LIMIT 100;""")

    return cur.fetchall()

def best_companies(cur):
    """Returns top 200 crunchbase, automation industries, and seed funding companies"""
    cur.execute("""WITH top_companies AS (
        SELECT primary_key, cb_rank, company_name, last_funding_type
        FROM crunchbase
        ORDER BY cb_rank
        LIMIT 200
    )
    SELECT tc.company_name, tc.last_funding_type, ic.industry_name
    FROM industry_connections ic
    LEFT JOIN top_companies tc ON ic.crunchbase_primary_key = tc.primary_key
    WHERE ic.industry_name = 'Automation'
    OR tc.last_funding_type = 'Seed'
    ORDER BY tc.cb_rank DESC
    """)
    return cur.fetchall()

def best_companies_with_counts(cur):
    """Get the counts for where the best companies come from"""
    cur.execute("""
    WITH relevant_companies AS (
        SELECT DISTINCT c.primary_key, c.cb_rank, c.company_name, c.last_funding_type, c.employees
        FROM crunchbase c
        LEFT JOIN industry_connections ic ON c.primary_key = ic.crunchbase_primary_key
        WHERE ic.industry_name = 'Automation'
           OR c.last_funding_type = 'Seed'
    ),
    all_companies AS (
        SELECT *, 
               ROW_NUMBER() OVER (ORDER BY cb_rank ASC) AS rank_within_set
        FROM relevant_companies
    ),
    combined_data AS (
        SELECT 
            ac.company_name,
            ac.last_funding_type,
            ic.industry_name,
            ac.cb_rank,
            CASE WHEN ac.rank_within_set <= 200 THEN 1 ELSE 0 END AS is_top_200,
            CASE WHEN ic.industry_name = 'Automation' THEN 1 ELSE 0 END AS is_automation,
            CASE WHEN ac.last_funding_type = 'Seed' THEN 1 ELSE 0 END AS is_seed_funding,
            CASE WHEN ac.last_funding_type = 'Early Stage Venture' THEN 1 ELSE 0 END AS is_venture_funding,
            CASE WHEN ac.employees = 101 then 1 else 0 end as is_large_company,
            ROW_NUMBER() OVER (PARTITION BY ac.company_name ORDER BY 
                CASE WHEN ic.industry_name = 'Automation' THEN 0 ELSE 1 END, 
                ic.industry_name
            ) AS row_num
        FROM all_companies ac
        LEFT JOIN industry_connections ic ON ac.primary_key = ic.crunchbase_primary_key
    ),
    deduplicated_data AS (
        SELECT *
        FROM combined_data
        WHERE row_num = 1
    )
    SELECT 
        company_name,
        last_funding_type,
        industry_name,
        SUM(is_top_200) OVER () AS total_top_200,
        SUM(is_automation) OVER () AS total_automation,
        SUM(is_seed_funding) OVER () AS total_seed_funding,
        SUM(is_venture_funding) OVER () AS total_venture_funding,
        SUM(is_large_company) OVER () AS total_large_companies

    FROM deduplicated_data
    ORDER BY cb_rank ASC NULLS LAST
    """)
    return cur.fetchall()

def best_companies_counts(cur):
    """"""
    cur.execute("""
    WITH relevant_companies AS (
        SELECT DISTINCT c.primary_key, c.cb_rank, c.company_name, c.last_funding_type, c.employees
        FROM crunchbase c
        LEFT JOIN industry_connections ic ON c.primary_key = ic.crunchbase_primary_key
        WHERE ic.industry_name = 'Automation'
        OR c.last_funding_type = 'Seed'
    ),
    all_companies AS (
        SELECT *, 
            ROW_NUMBER() OVER (ORDER BY cb_rank ASC) AS rank_within_set
        FROM relevant_companies
    ),
    combined_data AS (
        SELECT 
            ac.company_name,
            ac.last_funding_type,
            ic.industry_name,
            ac.cb_rank,
            CASE WHEN ac.rank_within_set <= 200 THEN 1 ELSE 0 END AS is_top_200,
            CASE WHEN ic.industry_name = 'Automation' THEN 1 ELSE 0 END AS is_automation,
            CASE WHEN ac.last_funding_type = 'Seed' THEN 1 ELSE 0 END AS is_seed_funding,
            CASE WHEN ac.last_funding_type = 'Early Stage Venture' THEN 1 ELSE 0 END AS is_venture_funding,
            CASE WHEN ac.employees = 11 then 1 else 0 end as is_large_company,
            ROW_NUMBER() OVER (PARTITION BY ac.company_name ORDER BY 
                CASE WHEN ic.industry_name = 'Automation' THEN 0 ELSE 1 END, 
                ic.industry_name
            ) AS row_num
        FROM all_companies ac
        LEFT JOIN industry_connections ic ON ac.primary_key = ic.crunchbase_primary_key
    ),
    deduplicated_data AS (
        SELECT *
        FROM combined_data
        WHERE row_num = 1
    )
    SELECT 
        SUM(is_top_200) AS total_top_200,
        SUM(is_automation) AS total_automation,
        SUM(is_seed_funding) AS total_seed_funding,
        SUM(is_venture_funding) AS total_venture_funding,
        SUM(is_large_company) AS total_large_companies
    FROM deduplicated_data
    """)
    return cur.fetchall()



def pull_all_with_seed_funding(cur):
    """Returns all companies with seed funding"""
    cur.execute("""SELECT *
    FROM crunchbase
    WHERE last_funding_type = 'Seed'
    ORDER BY cb_rank DESC""")
    return cur.fetchall()


def pull_all_automations(cur):
    """Returns all companies in the automation industry"""
    cur.execute("""SELECT *
    FROM crunchbase
    JOIN industry_connections ic ON crunchbase.primary_key = ic.crunchbase_primary_key
    WHERE ic.industry_name = 'Artificial Intelligence (AI)'
    ORDER BY cb_rank DESC""")
    return cur.fetchall()

def pull_all_early_stage_venture(cur):
    """Returns all companies with early stage venture funding"""
    cur.execute("""
    SELECT *
    FROM crunchbase
    WHERE TRIM(LOWER(REPLACE(last_funding_type, ' ', '_'))) = 'early_stage_venture'
    ORDER BY cb_rank DESC
    """)
    return cur.fetchall()

def pull_all_crunchbase(cur):
    """Returns all companies in the crunchbase table"""
    cur.execute("""SELECT *
    FROM crunchbase
    ORDER BY cb_rank ASC""")
    return cur.fetchall()

    # #    WHERE last_funding_type = 'Early_Stage_Venture'

    # cur.execute("""SELECT *
    # FROM crunchbase
    # WHERE last_funding_type = 'Early Stage Venture'
    # ORDER BY cb_rank DESC""")
    # return cur.fetchall()
                
    