# © 2025 Numantic Solutions LLC
# MIT License
#

#
# A retrieval-centric interface for CCC-PA Version 2
#

import sys, os
import json
import time
import traceback
import streamlit as st
import vertexai

# Import authentication object
utils_path = "utils/"
sys.path.insert(0, utils_path)
from authentication import ApiAuthentication
import response_logger as rl
import random_questions as rq

# Import chatbot
chatbot_path = "agent_handlers/"
sys.path.insert(0, chatbot_path)
from ccc_chatbot_agent import cccChatBot
from dotenv import load_dotenv
load_dotenv()

# Initialize Vertex AI API once per session
# try:
#     # Get get credentials and set envirvonment variables
#     api_configs = ApiAuthentication(client="CCC")
#
# except:
#     pass
#
# # Check that we have necessary environment variables
# req_env_vars = ["GOOGLE_CLOUD_PROJECT", "GOOGLE_CLOUD_LOCATION",
#                 "STAGING_BUCKET", "GOOGLE_APPLICATION_CREDENTIALS"]
# for rqv in req_env_vars:
#     if rqv not in os.environ:
#         msg = ("The following environment variables are required but seem to be missing; "
#                "Please review: {}").format(req_env_vars)
#         raise ValueError(msg)

# Initialize Vertex AI
vertexai.init(project=os.environ["GOOGLE_CLOUD_PROJECT"],
              location=os.environ["GOOGLE_CLOUD_LOCATION"],
              staging_bucket=os.environ["STAGING_BUCKET"])

########## Set up Streamlit
st.set_page_config(page_title="CCC-PA")
font_url = ("https://fonts.googleapis.com/css2?family=Lato:ital,wght"
            "@0,100;0,300;0,400;0,700;0,900;1,100;1,300;1,400;1,700;1,900&display=swap")
streamlit_style = """
			<style>
			@import url({font_url});
			html, body, [class*="css"]  {{
			font-family: 'Roboto', sans-serif;
			}}
			</style>
			"""
st.markdown(streamlit_style, unsafe_allow_html=True)

st.markdown(
    """
    <style>
    /* Target the container that holds the chat input */
    .stBottom {
        padding-bottom: 50px; /* Adjust this value to increase or decrease the margin */
    }
    </style>
    """,
    unsafe_allow_html=True
)

# images_path = "data/images"
# logo_file = "Numantic Solutions_Logotype_light.png"
# st.image(os.path.join(images_path, logo_file), width=600)
st.title("California Community College Policy Assistant")
bot_summary = ("This an experimental chatbot employing Artificial Intelligence tools "
               "to help users easily improve their understanding of policy topics related "
               "to California's community colleges. "
               "The bot's target audience are stakeholders who would like to participate "
               "in community college decision making and would benefit from curated and detailed "
               "information related to community colleges. "
               "Note that all chat content is logged for evaluation purposes. Please do "
               "not provide confidential, proprietary or other resctricted data. Thank you.\n")

# Some examples might include board members,
# administrators, staff, students, community activists or legislators.

st.text(bot_summary)
st.divider()

########## Handle conversations in Streamlit
# Build session components if needed
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "questions" not in st.session_state:
    st.session_state.questions = rq.generate_questions()

if "bot" not in st.session_state:
    # Create a chatbot for this user
    user_id = "u_123"
    try:
        st.session_state["bot"] = cccChatBot(user_id=user_id)
    except:
        time.sleep (5)
        msg = ("TRY BOT: We're having trouble starting the CCC Policy Assistant. We're going to try again, but if that "
               "doesn't work, please refresh this web page and try again. ")
        st.markdown(msg)
        st.markdown(traceback.format_exc())
        st.session_state["bot"] = cccChatBot(user_id=user_id)


if "messages" not in st.session_state:
    st.session_state.messages = []

# display function
def format_agent_output(report_dict: dict):
    """
    Function to format agent's output into Markdown for interface display
    """
    # Display results
    for key in report_dict.keys():
        if key == "report_title":
            st.markdown("## {}\n\n".format(report_dict[key]))

        elif key == "report_executive_summary":
            st.markdown("### Summary: \n{}\n".format(report_dict[key]))

        elif key == "report_body":
            st.markdown("### Report: \n{}\n".format(report_dict[key]))

        elif key == "report_references":
            st.markdown("### References: \n{}\n".format(report_dict[key]))

        elif key == "reference_uris":
            # Convert URLs to markdown list
            ref_uris_md = ["- {}\n".format(u) for u in report_dict["reference_uris"]]
            st.markdown("### Reference URLs \n")
            st.markdown(" ".join(ref_uris_md))

        elif key == "relevant_data_yes_or_no" and report_dict["relevant_data_yes_or_no"] == True:
            msg = ("I did a search of the Integrated Postsecondary Education Data System (IPEDS) "
                   "datasets from the U.S. Department of Education and found data relevant to "
                   "your query. \n\nHere's are my findings: {}").format(report_dict["description_of_relevant_data"])
            st.markdown(msg)

        elif key == "relevant_data_yes_or_no" and report_dict["relevant_data_yes_or_no"] == False:
            msg = ("I did a search of the Integrated Postsecondary Education Data System (IPEDS) "
                   "datasets from the U.S. Department of Education but did not find data relevant to "
                   "your query. ")
            st.markdown(msg)


with st.sidebar:
    sidebar_msg = ("Overview")

    st.header(sidebar_msg)
    st.text("\n\n\n")

    # invite = ("By making this tool available, we hope to demonstrate "
    #           "how policy advocacy can be supported through the use of technology. ")
    # invite2 = ("If you want to learn more or have thoughts about this application, similar "
    #           "tools or the underlying technology, please reach out to Steve or Nathan at "
    #           ":primary[info@numanticsolutions.com] ")

    # st.markdown(invite)
    # st.markdown(invite2)
    # st.text("\n\n\n")


    tab1, tab2 = st.tabs(["Example Questions", "Useful Links"])
    with tab1:
        st.header("Example Questions")
        for question in st.session_state.questions:
            st.text("• "+question)
    with tab2:
        links = ("- [Example Reports](https://eternal-bongo-435614-b9.uc.r.appspot.com/example_reports)\n"
                 "- [CCC-Bot Analytics](https://eternal-bongo-435614-b9.uc.r.appspot.com/home)\n"
                #  "- [GitHub](https://github.com/NumanticSolutions/ccc-policy_assistant)\n"
                #  "- [Numantic Solutions](https://numanticsolutions.com)\n\n"
                #  "- [Terms of Use](https://numanticsolutions.com/#terms)\n"
                #  "- [Privacy Policy](https://numanticsolutions.com/#privacy)\n"
                 )
        st.text("\n")
        st.markdown(links)

        st.text("\n")
        ### ??? st.session_state["bot"].version
        version_msg = ("Version deployed : " + "July 31, 2025")
        st.markdown(version_msg)

# Reset button
columns = st.columns(4)
reset_button = columns[3].button("Clear Chat")

# Object to hold content so screen can be cleared
chat_placeholder = st.empty()

# Input box for user's query
user_input = st.chat_input("Your message")

######## Chat stuff
if user_input:

    # Empty the screen
    # chat_placeholder.empty()

    # show previous chat history
    with chat_placeholder.container():
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):

                if message["role"] == "user":
                    st.markdown(message["content"])

                elif message["role"] == "data_assistant":
                    st.markdown("### Data Analysis Assistant")
                    st.markdown(
                        "Here's what my search of the IPEDS data found; Do you want me to run an IPEDS query?")
                    st.markdown(message["content"])

                else:
                    format_agent_output(report_dict=message["content"])

    # Display user's message
    with st.chat_message("user"):
        st.markdown(user_input)

    # Store user's query in the chat history
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Query the agent
    with st.spinner("I'm generating a report in response to your query; this can take 30 to 90 seconds. "):
        user_id = "u_123"
        try:
            st.session_state["bot"].stream_and_parse_query(query=user_input)
        except:
            time.sleep(5)
            msg = ("We're having trouble submitting queries to the CCC Policy Assistant. We're going to try again, but if that "
                   "doesn't work, please refresh this web page and try again. ")
            st.markdown(msg)
            st.markdown(traceback.format_exc())
            st.session_state["bot"].stream_and_parse_query(query=user_input)

    # Add agent results to session messages
    st.session_state.messages.append({"role": "assistant",
                                      "content": st.session_state["bot"].report_dict})

    # Display report results
    format_agent_output(report_dict=st.session_state["bot"].report_dict)

    # Add to BigQuery
    # Create response logger object parameters
    rlog_params = {"query": user_input,
                   "response": json.dumps(st.session_state["bot"].report_dict),
                   "app": "ccc_policy_assist",
                   "version": "2507",
                   "ai": "gemini-2.0-flash-001",
                   "agent": "synthesis",
                   "comments": "testing ccc streamlit app"}

    bq_logger = rl.ResponseLogger()
    bq_logger.response_to_bq(rlog_params=rlog_params)

    ################################ Data Agent
    # # Display IPEDS search results
    # st.markdown("### Data Analysis Assistant")
    #
    # # Parse IPEDS
    # st.session_state["bot"].parse_ipeds_search_results()
    #
    # # Format and display IPEDS repot Dict
    # format_agent_output(report_dict=st.session_state["bot"].ipeds_report_dict)
    #
    # # Add IPEDS
    # st.session_state.messages.append({"role": "data_assistant",
    #                                   "content": st.session_state["bot"].ipeds_result})
    #
    # # Add to BigQuery
    # # Create response logger object parameters
    # rlog_params = {"query": user_input,
    #                "response": st.session_state["bot"].ip_results.contents[0],
    #                "app": "ccc_policy_assist",
    #                "version": "2507",
    #                "ai": "gemini-2.0-flash-001",
    #                "agent": "rag_ipeds",
    #                "comments": "testing ccc streamlit app"}
    #
    # bq_logger = rl.ResponseLogger()
    # bq_logger.response_to_bq(rlog_params=rlog_params)
    #
    #######################

# Option to clear chat history
if reset_button:
    st.session_state.messages = []
    st.session_state.chat_history = []
    # st.session_state["bot"] = None
    # memory.clear()
    st.rerun()
    st.cache_data.clear()
    # rest_button = False
