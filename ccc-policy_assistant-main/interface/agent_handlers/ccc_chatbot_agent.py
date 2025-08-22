# © 2025 Numantic Solutions LLC
# MIT License
#
# CCC chatbot agent synthesizing responses of sub agents


import os, sys
import json

import vertexai
from vertexai import agent_engines

from ccc_subagent_parser import getSubAgentResults

class cccChatBot:
    '''
    Class to synthesize input of searchs and respond to a user's query
    '''

    def __init__(self,
                 user_id: str,
                 **kwargs):
        '''
        Initialize class
        '''

        # Parameters - Maximum number of search URIs to return
        self.max_va_uris = 5
        self.max_gs_uris = 5

        # Update any key word args
        self.__dict__.update(kwargs)

        # Users's query
        self.user_id = user_id

        # Synthesis agent resouce
        self.synthesis_resource_name = "projects/1062597788108/locations/us-central1/reasoningEngines/3177122411342462976"

        # Authenticate
        ########### Adjust for production deployments
        # self.authenticate()

        # Retrieve agent
        self.agent_engine = agent_engines.get(self.synthesis_resource_name)

        # Establish session
        self.session = self.agent_engine.create_session(user_id=self.user_id)


    def authenticate(self):
        '''
        Authenticate with Google AI servvices
        '''

        # Import authentication object
        utils_path = "utils/"
        sys.path.insert(0, utils_path)
        from authentication import ApiAuthentication
        api_configs = ApiAuthentication(client="CCC")

        # Initialize Vertex AI API once per session
        vertexai.init(project=os.environ["GOOGLE_CLOUD_PROJECT"],
                      location=os.environ["GOOGLE_CLOUD_LOCATION"],
                      staging_bucket=os.environ["STAGING_BUCKET"])

    def stream_and_parse_query(self,
                               query: str):
        '''
        Method to respond to a user's query
        '''

        # # Authenticate
        # self.authenticate()
        #
        # # Retrieve agent
        # self.agent_engine = agent_engines.get(self.synthesis_resource_name)
        #
        # # Establish session
        # self.session = self.agent_engine.create_session(user_id=self.user_id)

        ### Step 1. Get RAG Vertex AI search results of web text
        self.va_results = getSubAgentResults(query=query,
                                             rag_agent="rag_webtext",
                                             user_id=self.user_id)

        ### Step 2. Get Google search results
        self.gs_results = getSubAgentResults(query=query,
                                             rag_agent="search",
                                             user_id=self.user_id)

        # Step 3. Create full-context query using search results
        self.context = " ".join(self.va_results.contents + self.gs_results.contents)
        q_wrp = ("Use the following search results to synthesize an answer "
                 "in the context of California community colleges "
                 "to this user query: {}?  "
                 "Search results: {}.")
        self.full_context_query = q_wrp.format(query,
                                               self.context)

        # Step 4. Call the synthesis agent
        self.result = self.agent_engine.stream_query(message=self.full_context_query,
                                                     session_id=self.session["id"],
                                                     user_id=self.user_id)

        # Step 5. Parse response
        self.parse_synthesis_response()

        # Step 6. Call the IPEDS search
        self.ip_results = getSubAgentResults(query=query,
                                             rag_agent="rag_ipeds",
                                             user_id=self.user_id)

    def parse_synthesis_response(self):
        '''
        Method to synthesize the search results into a predefined summary output format
        (as specified in the JSON output schema format)

        '''

        # Put results into a dictionary for later access
        self.events = []
        for event in self.result:
            self.events.append(event)

        # Create an output dictionary
        contents = []

        # Get text results
        for event in self.events:
            if type(event) == dict:
                for key in event.keys():
                    if type(event[key]) == dict and key == "content":
                        for txt_dict in event[key]["parts"]:
                            contents.append(txt_dict["text"])

        # Convert the output JSON to a dictionary
        contstr = contents[0].replace("```json\n", "")
        contstr = contstr.replace("\n```", "")

        try:
            self.report_dict = json.loads(contstr)
        except:
            self.report_dict = {}

        # Add reference URIs from search results
        ref_uris = []
        for uri_dict in self.va_results.uris[:self.max_va_uris] + self.gs_results.uris[:self.max_gs_uris]:
            md_formatted = "[{}]({})".format(uri_dict["uri_text"],
                                             uri_dict["uri"])
            ref_uris.append(md_formatted)

        # Add these to report dictionary
        self.report_dict["reference_uris"] = ref_uris

    def parse_ipeds_search_results(self):
        '''
        Method to parse the IPEDS rag agent to determine if there are relevant IPEDS to query
        '''


        try:
            res_text = self.ip_results.contents[0]
            res_text = res_text[res_text.find("{"): res_text.rfind("}") + 1]

            self.ipeds_report_dict = json.loads(res_text)

        except:
            self.ipeds_report_dict = dict(relevant_data_yes_or_no=False)

        if self.ipeds_report_dict["relevant_data_yes_or_no"] == True:
            msg = ("I did a search of the Integrated Postsecondary Education Data System (IPEDS) "
                   "datasets from the U.S. Department of Education and found data relevant to "
                   "your query. \n\n"
                   "Here's are my findings: {}").format(self.ipeds_report_dict["description_of_relevant_data"])

            self.ipeds_result = msg

        else:
            msg = ("I did a search of the Integrated Postsecondary Education Data System (IPEDS) "
                   "datasets from the U.S. Department of Education but did not find data relevant to "
                   "your query. ")

            self.ipeds_result = msg



