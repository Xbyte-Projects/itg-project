# [2506] n8
#
import os, sys

import pandas as pd
import pandas_gbq
import datetime
import json
import uuid
from dataclasses import dataclass, asdict

from google.cloud import bigquery
import google.auth

from google import genai
from google.genai.types import HttpOptions


# Predefined prompts
predefined_prompts = {
    "py_docstring": ("you write concise and readable python.\n "
                      "please write a docstring for the following python code :\n "),
    "py_codecheck":  ("you write concise and readable python.\n "
                     "if there is an error in the following code please suggest corrections :\n "),
    "py_functionlist": ("you write concise and readable python.\n "
                        "Provide a listing of all classes and their methods and any functions "
                        "and provide a one-sentence description of each method and function :\n "),
    "doc_title": ("you write clear, concise and informative titles for government documents.\n"
                  "for the following document provide a single title formatted as a JSON object "
                  "where the key is 'title' and the value is the corresponding title :\n" )

}



@dataclass
class ResponseLog:
    query: str = ""
    response: str = ""
    app: str = "response_logger"
    version: str = "2506"
    ai: str = "gemini-2.0-flash-001"
    agent: str = ""
    comments: str = "testing response logger"
    location: str = "logs.ai_responses"




class ResponseLogger:


    def __init__(self, **kwargs):

        # Set parameters
        self.schema_path = ''
        self.schema_file = 'schema-ai_response.json'

        # Minimum content length
        self.min_prompt_content_len = 5

        # Update any key word args
        self.__dict__.update(kwargs)

        # Authenticate
        self.credentials, self.project = google.auth.default()

    def to_bq(self, rlog):
        """
        Logs an AI response to Google BigQuery.

        Args:
            rlog: An object containing the response data to be logged.  It is expected to have the following attributes:
                - query (str): The user query that generated the response.
                - response (str): The AI's response to the query.
                - app (str): The name of the application that generated the response.
                - version (str): The version of the application.
                - ai (str): The specific AI model used.
                - agent (str): The agent responsible for the response.
                - comments (str):  Any additional comments or notes about the response.
                - location (str): The BigQuery table location (e.g., 'your-project.your_dataset.your_table').

        Raises:
            FileNotFoundError: If 'schema-ai_response.json' is not found.
            google.auth.exceptions.GoogleAuthError: If authentication with Google Cloud fails.
            Exception:  For any other errors during the process, such as issues writing to BigQuery.

        Note:
            This function reads the BigQuery table schema from 'schema-ai_response.json'.  It then constructs a Pandas DataFrame from the provided response data and appends it to the specified BigQuery table.  It uses Google Cloud authentication to authorize the write operation.
        """

        # Look for BigQuery table schema
        try:
            with open(os.path.join(self.schema_path, self.schema_file), 'r') as f:
                self.schema = json.load(f)
        except:
            # Set to None - meaning infer from dataframe
            self.schema = None

        df = pd.DataFrame({ 'uuid':      [str(uuid.uuid4())],
                            'timestamp': [pd.to_datetime(datetime.datetime.now())],
                            'query':     [rlog.query],
                            'response':  [rlog.response],
                            'app':       [rlog.app],
                            'version':   [rlog.version],
                            'ai':        [rlog.ai],
                            'agent':     [rlog.agent],
                            'comments':  [rlog.comments] })

        pandas_gbq.to_gbq(df,
                          rlog.location,
                          project_id=self.project,
                          table_schema=self.schema,
                          if_exists='append')


    def ai_to_bq(self,
                 prompt: str,
                 content: str,
                 file_name: str,
                 rlog_params: dict = None):
        """
        Reads content from a file, prepends an introduction, sends it to a
        generative AI model, and logs the query, response, and comments to BigQuery.

        Args:
            prompt (str): Prefix prompt that will be a prefix to the content and form the LLM
                query. If prompt equals one of the predefined_prompts keys, the prompt will be
                the associated value. Current keys are 'py_docstring', 'py_codechek', 'doc_title'.
                If the prompt does not match one of the predefined keys, the passed prompt will
                be used/
            content (str): Query content. If the file_name argument is blank, the method will expect
                content in the content flag. Otherwise, it will look for content in the file-name.
            file_name (str): The path to the file containing the content
                to send to the AI model.
            rlog_parmas (Dict): Response log values in a dictionary with keys corresponding
                to response log fields.

        Returns:
            None.  The function sends data to BigQuery but doesn't return a value.

        Raises:
            FileNotFoundError: If the specified file does not exist.
            google.auth.exceptions.GoogleAuthError: If there are issues
            authenticating with Google Cloud.
            Exception: If there are errors interacting with the generative
            AI model or BigQuery.  (Exception type is not explicitly handled
            so a generic Exception is described)
        """

        # Create a response log instance
        rlog = ResponseLog()

        # Get prompt - first check if the prompt argument matches
        # a predefined key - otherwise we're using the prompt
        for key in predefined_prompts.keys():
            if prompt == key:
                prompt = predefined_prompts[key]
                break

        # Get content based on source flag
        if file_name == None or len(file_name) < 1:
            # Expect content in the content flag
            pass
        else:
            with open(file_name, "r") as f:
                content = f.read()

        # Check if the prompt and content are long enough
        if len(prompt) < self.min_prompt_content_len:
            msg = ("The prompt length is less than {} characters and insufficient"
                   "to construct an AI model query. Please review.")
            raise ValueError

        if len(content) < self.min_prompt_content_len:
            msg = ("The content length is less than {} characters and insufficient"
                   "to construct an AI model query. Please review.")
            raise ValueError

        # Create a query
        query = ( prompt + content )

        # Try to call the AI model
        try:
            client = genai.Client(http_options=HttpOptions(api_version="v1"))
        except:
            client = genai.Client(http_options=HttpOptions(api_version="v1"),
                                  api_key=os.environ["GOOGLE_API_KEY"])

        # Generate a response
        response = client.models.generate_content(
            model=rlog.ai,
            contents=query
        )

        # Construct a response log instance
        # if rlog_params is default of None skip
        if not rlog_params:
            pass

        # check if dictionary
        elif not type(rlog_params) == dict:
            msg = ("If the rlogs_param is present it must be a dictionary. "
                   "Please review.")
            raise ValueError

        # Update rlog
        else:

            # Convert the current rlog to a dictionary
            rlog_up = asdict(rlog)

            # Update parameters
            for key in rlog_params.keys():
                rlog_up[key] = rlog_params[key]

            # Create a new rlog
            rlog = ResponseLog(**rlog_up)

        # Add query and response text
        rlog.query = query
        rlog.response = response.text

        # Save to BigQuery
        self.to_bq(rlog)

        return {"query": rlog.query,
                "response": rlog.response}

    def response_to_bq(self,
                       rlog_params: dict = None):
        """
        Processes a response and transforms it into a format suitable for BigQuery ingestion. It
        is used when the AI response is generated outside the response logger object, but
        the response logger is used to save the query and AI response to BigQuery.

        In this method the rlog_params are converted to a rlog object with updated parameter
        values.

        Args:
            rlog_parmas (Dict): Response log values in a dictionary with keys corresponding
                to response log fields.

        Returns
        -------
        None
        """

        # Create a response log instance
        rlog = ResponseLog()

        # if rlog_params is default of None skip
        if not rlog_params:
            msg = ("This method requires a rlogs_param dictionary object with values to be saved to BigQuery. "
                   "Please review.")
            raise ValueError

        # check if dictionary
        elif not type(rlog_params) == dict:
            msg = ("If the rlogs_param is present it must be a dictionary. "
                   "Please review.")
            raise ValueError

        # Update rlog
        else:

            # Convert the current rlog to a dictionary
            rlog_up = asdict(rlog)

            # Update parameters
            for key in rlog_params.keys():
                rlog_up[key] = rlog_params[key]

            # Create a new rlog
            rlog = ResponseLog(**rlog_up)

        # Save to BigQuery
        self.to_bq(rlog)


# # [x] rfr example one as its own application (read python from file)
# # [ ] more examples . . . [ ] python coding questions
# # [ ] summarization application
# # [ ] as a separate project / 15 or 30dc?  - - - ai_to_bq
# #
#
