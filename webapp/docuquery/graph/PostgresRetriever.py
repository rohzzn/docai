import ast
import os
import sys

from langchain.chains import create_sql_query_chain
from langchain.chains.sql_database.prompt import PROMPT_SUFFIX
from langchain_community.utilities import SQLDatabase

from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from docuquery.constants.app import DEFAULT_MODEL_NAME
from docuquery.constants.psql import (
    POSTGRES_DB,
    POSTGRES_HOST,
    POSTGRES_PASSWORD,
    POSTGRES_PORT,
    POSTGRES_USER,
)

TABLES_TO_USE = [
    "api_consortium",
    "api_consortiumsite",
    "api_contact",
    "api_disease",
    "api_diseasecategory",
    "api_enrollmentstatus",
    "api_fundingopportunity",
    "api_gard",
    "api_irbapprovalstatus",
    "api_pag",
    "api_publication",
    "api_researchtype",
    "api_site",
    "api_status",
    "api_study",
    "api_studycontact",
    "api_studytype"
]

_postgres_prompt = '''You are a PostgreSQL expert. Given an input question, first create a syntactically correct PostgreSQL query to run, then look at the results of the query and return the answer to the input question.
Unless the user specifies in the question a specific number of examples to obtain, query for at most {top_k} results using the LIMIT clause as per PostgreSQL. You can order the results to return the most informative data in the database.
Never query for all columns from a table. You must query only the columns that are needed to answer the question. Wrap each column name in double quotes (") to denote them as delimited identifiers.
Pay attention to use only the column names you can see in the tables below. Be careful to not query for columns that do not exist. Also, pay attention to which column is in which table.
Pay attention to use CURRENT_DATE function to get the current date, if the question involves "today".
When filtering text data, avoid strict equality checks unless the user mentions it in the query or specifies the exact value in quotes. Use pattern matching operators like LIKE or ILIKE to perform flexible matching and retrieve relevant data even if there are slight differences in the text.
Use the following format:

Question: Question here
SQLQuery: SQL Query to run
SQLResult: Result of the SQLQuery
Answer: Final answer here

OUTPUT: Only the SQLQuery without any triple quotes.
Example Output: SELECT "content" FROM "documents" WHERE "title" LIKE '%title%' LIMIT 1

'''

class PostgresRetriever:
    def __init__(self, db, llm):
        self.db = db
        self.llm = llm

    def get_chain(self):
        prompt = PromptTemplate(
            input_variables=["input", "table_info", "top_k"],
            template=_postgres_prompt + PROMPT_SUFFIX,
        )
        write_query = create_sql_query_chain(
            llm=self.llm,
            db=self.db,
            prompt=prompt
        )
        execute_query = QuerySQLDataBaseTool(db=self.db)
        return write_query | execute_query

    @staticmethod
    def to_list(str_rows):
        str_list = []
        if not str_rows:
            return str_list

        try:
            data = ast.literal_eval(str_rows)
            str_list = ['\n\n'.join(map(str, tup)) for tup in data]
        except Exception as err:
            print(err)
        return str_list


if __name__ == '__main__':
    connection_string = f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    db = SQLDatabase.from_uri(connection_string)

    llm = ChatOpenAI(temperature=0, model_name=DEFAULT_MODEL_NAME)
    # chain = PostgresRetriever(db, llm).get_chain()
    #
    # q = "What's the treatment for cancer?"
    q = "How to gain access to box?"
    # # q = "How many tables?"
    # result = chain.invoke({"question": q, "table_names_to_use": TABLES_TO_USE})
    # result = PostgresRetriever.to_list(result)
    # print(result)

    prompt = PromptTemplate(
        input_variables=["input", "table_info", "top_k"],
        template=_postgres_prompt + PROMPT_SUFFIX,
    )

    write_query = create_sql_query_chain(
        llm=llm,
        db=db,
        prompt=prompt
    )
    result = write_query.invoke({"question": q})
    print(result)
