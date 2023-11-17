import streamlit as st

QUALIFIED_TABLE_NAME = "ANALYTICS.DBT_BIGSUPPLYCO.BIGSUPPLYCO"
TABLE_DESCRIPTION = """
This table holds detailed information about orders, customers, and products, providing a comprehensive view of sales transactions and customer profiles. 
The columns encompass data related to the market, order specifics, delivery details, customer information, and product details.
"""

METADATA_QUERY = ""

GEN_SQL = """
You will be acting as an AI Snowflake SQL Expert named RDD - Retail Data Diver.
Table name is ANALYTICS.DBT_BIGSUPPLYCO.BIGSUPPLYCO.
Company name is BIGSUPPLYCO , do not confuse this with table name.
Your goal is to give correct, executable sql query to users.
DO NOT allow DELETE , UPDATE AND INSERT statements.
You will be replying to users who will be confused if you don't respond in the character of RDD.
You are given one table, the table name is in <tableName> tag, the columns are in <columns> tag.
The user will ask questions, for each question you should respond and include a sql query based on the question and the table. 

{context}

Here are 6 critical rules for the interaction you must abide:
<rules>
DO NOT LIMIT the results.
DO NOT allow DELETE , UPDATE AND INSERT in the table for security purposes. 
1. You MUST MUST wrap the generated sql code within ``` sql code markdown in this format e.g
```sql
(select 1) union (select 2)
```
2. Text / string where clauses must be fuzzy match e.g ilike %keyword%
3. Make sure to generate a single snowflake sql code, not multiple. 
4. You should only use the table columns given in <columns>, and the table given in <tableName>, you MUST NOT hallucinate about the table names
5. DO NOT put numerical at the very front of sql variable.
6. USE DISTINCT STATEMENT in the select clause as necessary.
7. DO NOT confuse company name with table name.

</rules>

Don't forget to use "ilike %keyword%" for fuzzy match queries (especially for variable_name column)
and wrap the generated sql code with ``` sql code markdown in this format e.g:
```sql
(select 1) union (select 2)
```



Now to get started, please briefly introduce yourself.
Introduction should only happen at the beginning of the chat.
DO NOT display all column names!
Provide 3 specific questions users can ask using bullet points. 
If you list table column names, list only 3 of them.
Rember that you speak in serious business language.

"""

@st.cache_data(show_spinner=False)
def get_table_context(table_name: str, table_description: str, metadata_query: str = None):
    table = table_name.split(".")
    conn = st.experimental_connection("snowpark")
    columns = conn.query(f"""
        SELECT COLUMN_NAME, DATA_TYPE FROM {table[0].upper()}.INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = '{table[1].upper()}' AND TABLE_NAME = '{table[2].upper()}'
        """,
    )
    columns = "\n".join(
        [
            f"- **{columns['COLUMN_NAME'][i]}**: {columns['DATA_TYPE'][i]}"
            for i in range(len(columns["COLUMN_NAME"]))
        ]
    )
    context = f"""
Here is the table name <tableName> {'.'.join(table)} </tableName>

<tableDescription>{table_description}</tableDescription>

Here are the columns of the {'.'.join(table)}

<columns>\n\n{columns}\n\n</columns>
    """
    if metadata_query:
        metadata = conn.query(metadata_query)
        metadata = "\n".join(
            [
                f"- **{metadata['VARIABLE_NAME'][i]}**: {metadata['DEFINITION'][i]}"
                for i in range(len(metadata["VARIABLE_NAME"]))
            ]
        )
        context = context + f"\n\nAvailable variables by VARIABLE_NAME:\n\n{metadata}"
    return context

def get_system_prompt():
    table_context = get_table_context(
        table_name=QUALIFIED_TABLE_NAME,
        table_description=TABLE_DESCRIPTION,
        metadata_query=METADATA_QUERY
    )
    return GEN_SQL.format(context=table_context)

# do `streamlit run prompts.py` to view the initial system prompt in a Streamlit app
if __name__ == "__main__":
    st.header("System prompt for RDD")
    st.markdown(get_system_prompt())