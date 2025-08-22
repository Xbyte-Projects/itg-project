# © 2025 Numantic Solutions LLC
# MIT License
#
# CCC subagent wrapper to parser subagent responses

import os, sys
import re
import json

# import vertexai
from vertexai import agent_engines

# Text cleaning
utils_path = "../utils/"
sys.path.insert(0, utils_path)
import text_cleaning_tools as tct


class getSubAgentResults:
    '''
    Class to read and parse Google AI Search agent App results

    '''

    def __init__(self,
                 rag_agent: str,
                 query: str,
                 user_id: str,
                 **kwargs):
        '''
        Initialize class
        '''

        # Update any key word args
        self.__dict__.update(kwargs)

        # Get the agent resource name
        if rag_agent == "rag_webtext":
            self.resource_name = "projects/1062597788108/locations/us-central1/reasoningEngines/7423647424045907968"

        elif rag_agent == "rag_ipeds":
            # self.resource_name = "projects/1062597788108/locations/us-central1/reasoningEngines/59136133388304384"
            self.resource_name = "projects/1062597788108/locations/us-central1/reasoningEngines/1676772824544444416"

        elif rag_agent == "search":
            self.resource_name = "projects/eternal-bongo-435614-b9/locations/us-central1/reasoningEngines/8448585775179628544"

        # Users's query
        self.query = query
        self.user_id = user_id

        # Call the API
        self.call_agent()

        # Parse the response
        if rag_agent in ["rag_webtext", "rag_ipeds"]:
            self.parse_rag_response()

        elif rag_agent in ["search"]:
            self.parse_search_response()

    def call_agent(self):
        '''
        Call the API to get search results for user's query
        '''

        # Retrieve agent
        self.agent_engine = agent_engines.get(self.resource_name)

        # Establish session
        self.session = self.agent_engine.create_session(user_id=self.user_id)

        # Get agent response
        self.result = self.agent_engine.stream_query(message=self.query,
                                                     session_id=self.session["id"],
                                                     user_id=self.user_id)

        # Put results into a dictionary for later access
        self.events = []
        for event in self.result:
            self.events.append(event)


    def parse_rag_response(self):
        '''
        Method to parse response into the elements of interest
        '''

        self.organizations = []
        self.uris = []
        self.contents = []
        self.transcripts = []
        dorgs = []

        # Get text results
        for event in self.events:
            if type(event) == dict:
                for key in event.keys():
                    if type(event[key]) == dict and key == "content":
                        for txt_dict in event[key]["parts"]:
                            self.contents.append(tct.clean_contents(intext=txt_dict["text"]))

            # Find domains and URIs from grounding_metadata
            try:
                for i, gc in enumerate(event["grounding_metadata"]["grounding_chunks"]):
                    if type(gc) == dict:
                        for key in gc.keys():
                            if type(gc[key]) == dict and key == "retrieved_context":

                                # Get organizations and transcripts
                                pat_org = r"organizations:"
                                pat_src = r"source_index:"
                                pat_trs = r"transcript:"

                                fl_txt = gc["retrieved_context"]["text"]

                                # Find organization
                                tores = re.search(pat_org, fl_txt)
                                # Find source_index
                                tsires = re.search(pat_src, fl_txt)
                                # Find transcript
                                ttsres = re.search(pat_trs, fl_txt)

                                # Get organization
                                if tores and tsires:
                                    os = tores.start() + len(pat_org)
                                    ss = tsires.start()
                                    dorg = json.loads(json.loads(fl_txt[os:ss]))
                                    dorgs.append(dorg)

                                # Get transcript
                                if ttsres:
                                    transcript = fl_txt[ttsres.start() + len(pat_trs):]
                                else:
                                    transcript = ""

                                # get a list of organizations without duplicates
                                for org_name in set([org["name"] for org in dorgs]):
                                    for dorg in dorgs:
                                        if dorg["name"] == org_name and dorg not in self.organizations:
                                            self.organizations.append(dorg)

                                # Add transcripts
                                self.transcripts.append(transcript)

                                # Get the title
                                if "title" in gc["retrieved_context"].keys() and len(
                                        gc["retrieved_context"]["title"]) > 0:
                                    title = gc["retrieved_context"]["title"]
                                else:
                                    title = dorg["name"]

                                # Add a URI
                                self.uris.append(dict(uri_index=i,
                                                      uri=gc["retrieved_context"]["uri"],
                                                      uri_text=title
                                                      )
                                                 )

            except:
                pass

    def parse_search_response(self):
        '''
        Method to parse response into the elements of interest
        '''

        self.domains = []
        self.uris = []
        self.contents = []

        # Get text results
        for event in self.events:
            if type(event) == dict:
                for key in event.keys():
                    if type(event[key]) == dict and key == "content":
                        for txt_dict in event[key]["parts"]:
                            self.contents.append(tct.clean_contents(intext=txt_dict["text"]))

            # Find domains and URIs from grounding_metadata
            uri_index = 0
            for gc in event["grounding_metadata"]["grounding_chunks"]:
                for key in gc.keys():
                    if key == "web":
                        self.domains.append(gc["web"]["domain"])
                        self.uris.append(dict(uri_index=uri_index,
                                              uri=gc["web"]["uri"],
                                              uri_text=gc["web"]["domain"])
                                         )
                        uri_index += 1

        self.domains = list(set(self.domains))


