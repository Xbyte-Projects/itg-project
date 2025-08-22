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

# Import BigQuery modules
bq_path = "BQ/"
sys.path.insert(0, bq_path)
try:
    from BQ.db.table_router_agent import TableRouter
    from BQ.db.table_factory import table_factory
    from BQ.db.agent import dynamic_get_data
    BQ_AVAILABLE = True
except ImportError as e:
    st.error(f"Failed to import BigQuery modules: {e}")
    BQ_AVAILABLE = False

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


    tab1, tab2, tab3 = st.tabs(["Example Questions", "Useful Links", "Database Operations"])
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
    
    with tab3:
        st.header("Database Operations")
        st.text("Ask questions about the data in natural language. The system automatically finds the right table and shows you the answer.")
        
        # Database Status
        if BQ_AVAILABLE:
            st.success("✅ BigQuery module loaded successfully")

            
            # Initialize BQ components
            if "table_router" not in st.session_state:
                try:
                    st.session_state.table_router = TableRouter()
                except Exception as e:
                    st.error(f"Failed to initialize TableRouter: {e}")
                    st.session_state.table_router = None
            
            if "table_factory" not in st.session_state:
                try:
                    st.session_state.table_factory = table_factory
                except Exception as e:
                    st.error(f"Failed to initialize TableFactory: {e}")
                    st.session_state.table_factory = None
            
            # Check if components are available
            if st.session_state.table_router and st.session_state.table_factory:
                # Example questions
                st.subheader("💡 Example Questions")
                example_questions = [
                    "Show me the top 10 colleges by enrollment",
                    "Which colleges have the highest graduation rates?",
                    "Show me the number of colleges in each district",
                    "How are library funds allocated?"
                ]
                
                # Create columns for example questions
                cols = st.columns(2)
                for i, question in enumerate(example_questions):
                    col_idx = i % 2
                    if cols[col_idx].button(f"Example {i+1}", key=f"example_{i}", help=question):
                        st.session_state.example_question = question
                
                # User question input
                user_question = st.text_area("Enter your question about the data:", 
                                           value=st.session_state.get("example_question", ""),
                                           placeholder="e.g., Show me the top 10 colleges by enrollment, Which colleges have the highest graduation rates?, What are the enrollment trends by state?")
                
                # Query button
                if st.button("Run Query") and user_question:
                    with st.spinner("Finding the most relevant table and generating SQL query..."):
                        try:
                            # Automatically find the most relevant table using TableRouter
                            table_router = st.session_state.table_router
                            relevant_tables = table_router.find_relevant_tables(user_question, top_k=3)
                            
                            if relevant_tables and len(relevant_tables) > 0:
                                try:
                                    # Automatically use the most relevant table (first in the list)
                                    selected_table = relevant_tables[0]["table_name"]
                                    
                                    # Show which table is being used
                                    st.success(f"🔍 Using table: **{selected_table}**")
                                    
                                    # Use the dynamic_get_data function
                                    result = dynamic_get_data(selected_table, user_question)
                                    
                                    if result.get("status") == "error":
                                        st.error(f"Error: {result.get('error')}")
                                    else:
                                        st.success("Query executed successfully!")
                                        
                                        # Display results
                                        if "data" in result and result["data"]:
                                            st.subheader("Query Results")
                                            st.dataframe(result["data"])
                                            
                                            # Show result count
                                            st.info(f"Found {len(result['data'])} records")
                                            
                                            # Store query in session state for history
                                            if "query_history" not in st.session_state:
                                                st.session_state.query_history = []
                                            
                                            query_record = {
                                                "question": user_question,
                                                "table": selected_table,
                                                "results_count": len(result["data"]),
                                                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                                            }
                                            st.session_state.query_history.append(query_record)
                                        else:
                                            st.warning("No data returned from query")
                                except (KeyError, TypeError, IndexError) as e:
                                    st.error(f"Error processing table selection: {str(e)}")
                                    st.error("Please try rephrasing your question.")
                            else:
                                st.error("Could not find a relevant table for your question. Please try rephrasing.")
                                
                        except Exception as e:
                            st.error(f"An error occurred: {str(e)}")
                            st.exception(e)
            else:
                st.warning("Database components not properly initialized. Please check your environment variables and credentials.")
            
            # Show query history
            if "query_history" in st.session_state and st.session_state.query_history:
                st.subheader("📝 Recent Queries")
                with st.expander("View Query History"):
                    for i, query_record in enumerate(reversed(st.session_state.query_history[-5:])):  # Show last 5 queries
                        st.markdown(f"**Query {i+1}** ({query_record['timestamp']})")
                        st.text(f"Question: {query_record['question']}")
                        st.text(f"Table: {query_record['table']}")
                        st.text(f"Results: {query_record['results_count']} records")
                        st.divider()
                
                # Clear history button
                if st.button("Clear Query History"):
                    st.session_state.query_history = []
                    st.rerun()
            
            # Helpful Tips
            st.subheader("💡 How to Use")
            with st.expander("Tips for Better Queries"):
                st.markdown("""
                **Best Practices:**
                - Be specific about what you want to see
                - Mention the type of data you're interested in
                - Use natural language (e.g., "Show me colleges with high graduation rates")
                
                **Example Questions:**
                - "Which colleges have the highest enrollment?"
                - "Show me graduation rates by district"
                - "What are the trends in student-faculty ratios?"
                - "Compare funding across different regions"
                
                **What Happens:**
                1. Your question is analyzed using AI
                2. The system finds the most relevant table
                3. SQL is automatically generated
                4. Results are displayed in a table format
                """)
            
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
    with st.spinner("I'm generating a report in response to your query. "):
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

# Database Overview Section
# st.divider()
# st.header("📊 Database Overview")

# if BQ_AVAILABLE:
#     # Initialize BQ components for main area if not already done
#     if "table_factory_main" not in st.session_state:
#         st.session_state.table_factory_main = get_table_factory()

#     if st.session_state.table_factory_main:
#         available_tables = st.session_state.table_factory_main.get_all_table_names()
        
#         col1, col2, col3 = st.columns(3)
        
#         # with col1:
#             # st.metric("Available Tables", len(available_tables))
        
#         # with col2:
#         #     # st.metric("Database Status", "Connected")
        
#         with col3:
#             st.metric("Query Engine", "BigQuery")
        
#         # Quick query examples
#         st.subheader("💡 Quick Query Examples")
        
#         example_queries = [
#             "Show me the top 10 colleges by enrollment",
#             "What are the average graduation rates by state?",
#             "Which colleges have the highest student-faculty ratios?",
#             "Show enrollment trends over the last 5 years"
#         ]
        
#         for i, query in enumerate(example_queries):
#             if st.button(f"Example {i+1}: {query[:50]}...", key=f"quick_query_{i}"):
#                 st.info(f"Copy this query to the Database Operations tab: {query}")
        
#         st.info("💡 **Tip**: Use the 'Database Operations' tab in the sidebar to run custom queries on any available table.")
#     else:
#         st.warning("⚠️ Database connection not available. Check your environment variables and credentials.")
# else:
#     st.warning("⚠️ BQ module is not available. Database functionality is disabled.")

