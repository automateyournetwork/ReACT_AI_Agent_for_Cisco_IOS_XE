import streamlit as st
from pyats.topology import loader
from langchain_community.llms import Ollama
from langchain_core.tools import tool, render_text_description
from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate


# ============================================================
# Define the pyATS tools
# ============================================================

# Tool function to connect to the router and run 'show ip interface brief' using pyATS
def show_ip_interface_brief():
    try:
        # Load the testbed
        print("Loading testbed...")
        testbed = loader.load('testbed.yaml')
        
        # Access the device from the testbed
        device = testbed.devices['Cat8000V']
        
        # Connect to the device
        print("Connecting to device...")
        device.connect()

        # Execute the 'show ip interface brief' command and parse output using Genie (which returns JSON)
        print("Executing 'show ip interface brief'...")
        parsed_output = device.parse("show ip interface brief")
        
        # Close the connection
        print("Disconnecting from device...")
        device.disconnect()

        # Return parsed output (JSON)
        return parsed_output
    except Exception as e:
        # Handle exceptions and provide error information
        return {"error": str(e)}

# Tool function to connect to the router and run 'show ip route' using pyATS
def show_ip_route():
    try:
        # Load the testbed
        print("Loading testbed...")
        testbed = loader.load('testbed.yaml')
        
        # Access the device from the testbed
        device = testbed.devices['Cat8000V']
        
        # Connect to the device
        print("Connecting to device...")
        device.connect()

        # Execute the 'show ip route' command to get the running configuration
        print("Executing 'show ip route'...")
        running_config = device.parse("show ip route")
        
        # Close the connection
        print("Disconnecting from device...")
        device.disconnect()

        # Return running configuration (string)
        return running_config
    except Exception as e:
        # Handle exceptions and provide error information
        return {"error": str(e)}

# Tool function to connect to the router and run 'show ip route' using pyATS
def show_access_lists():
    try:
        # Load the testbed
        print("Loading testbed...")
        testbed = loader.load('testbed.yaml')
        
        # Access the device from the testbed
        device = testbed.devices['Cat8000V']
        
        # Connect to the device
        print("Connecting to device...")
        device.connect()

        # Execute the 'show access-lists' command to get the running configuration
        print("Executing 'show access-lists'...")
        running_config = device.parse("show access-lists")
        
        # Close the connection
        print("Disconnecting from device...")
        device.disconnect()

        # Return running configuration (string)
        return running_config
    except Exception as e:
        # Handle exceptions and provide error information
        return {"error": str(e)}

# Tool function to connect to the router and run 'show ip route' using pyATS
def show_version():
    try:
        # Load the testbed
        print("Loading testbed...")
        testbed = loader.load('testbed.yaml')
        
        # Access the device from the testbed
        device = testbed.devices['Cat8000V']
        
        # Connect to the device
        print("Connecting to device...")
        device.connect()

        # Execute the 'show version' command to get the running configuration
        print("Executing 'show version'...")
        running_config = device.parse("show version")
        
        # Close the connection
        print("Disconnecting from device...")
        device.disconnect()

        # Return running configuration (string)
        return running_config
    except Exception as e:
        # Handle exceptions and provide error information
        return {"error": str(e)}
    
# Define the custom tools using the langchain `tool` decorator
@tool
def show_ip_inteface_brief_tool(dummy_input: str = "default") -> dict:
    """Execute the 'show ip interface brief' command on the router using pyATS and return the parsed JSON output. The input is ignored."""
    return show_ip_interface_brief()

@tool
def show_ip_route_tool(dummy_input: str = "default") -> str:
    """Execute the 'show ip route' command on the router using pyATS and return the parsed JSON output. The input is ignored."""
    return show_ip_route()

@tool
def show_access_lists_tool(dummy_input: str = "default") -> str:
    """Execute the 'show_access_lists' command on the router using pyATS and return the parsed JSON output. The input is ignored."""
    return show_access_lists()

@tool
def show_version_tool(dummy_input: str = "default") -> str:
    """Execute the 'show_version' command on the router using pyATS and return the parsed JSON output. The input is ignored."""
    return show_version()

# ============================================================
# Define the agent with a custom prompt template
# ============================================================

# Initialize the Ollama LLM
llm = Ollama(model="llama3.1")

# Create a list of tools
tools = [show_ip_inteface_brief_tool, show_ip_route_tool, show_access_lists_tool, show_version_tool]

# Render text descriptions for the tools for inclusion in the prompt
tool_descriptions = render_text_description(tools)

template = """
Assistant is a large language model trained by OpenAI.

Assistant is designed to assist with a wide range of tasks, from answering simple questions to providing in-depth explanations and discussions on various topics. As a language model, Assistant can generate human-like text based on the input it receives, allowing it to engage in natural-sounding conversations and provide coherent and relevant responses.

Assistant is constantly learning and improving. It can process and understand large amounts of text and use this knowledge to provide accurate and informative responses to a wide range of questions. Additionally, Assistant can generate its text based on the input it receives, allowing it to engage in discussions and provide explanations and descriptions on various topics.

Overall, Assistant is a powerful tool that can help with a wide range of tasks and provide valuable insights and information. Whether you need help with a specific question or want to have a conversation about a particular topic, Assistant is here to assist.

NETWORK INSTRUCTIONS:

Assistant is a network assistant with the capability to run tools to gather information and provide accurate answers. You MUST ONLY use the provided tools for checking interface statuses or retrieving the running configuration.

To use a tool, please use the following format:

Thought: Do I need to use a tool? Yes  
Action: the action to take, should be one of [{tool_names}]  
Action Input: the input to the action (it will be ignored by the tool)  
Observation: the result of the action  
When you have a response to say to the Human, or if you do not need to use a tool, you MUST use the format:

Thought: Do I need to use a tool? No  
Action: Display [your response here]  

IMPORTANT GUIDELINES:

Tool Selection: Only use the tool that is necessary to answer the question. For example:

If the question is about IP addresses or interface status, start by using the show ip interface brief tool.
Use show run only if the question explicitly requires detailed configuration that show ip interface brief cannot provide.
Check After Each Tool Use: After using a tool, check if you already have enough information to answer the question. If yes, provide the final answer immediately and do not use another tool.

For example, if asked about the IP address of Loopback0, after retrieving the data from 'show ip interface brief', respond as follows:


Thought: Do I need to use a tool? No  
Final Answer: The IP address for Loopback0 is 10.0.0.1.  

Avoid Repetition: If you have already provided a final answer, do not repeat it or perform additional steps. The conversation should end there.

Correct Formatting is Essential: Make sure every response follows the format strictly to avoid errors. Use "Final Answer" to deliver the final output.

Handling Errors or Invalid Tool Usage: If an invalid action is taken or if there is an error, correct the thought process and provide the accurate answer directly without repeating unnecessary steps.

TOOLS:

Assistant has access to the following tools:

{tools}

Begin!

Previous conversation history:

{chat_history}

New input: {input}

{agent_scratchpad}
"""

# Define the input variables separately
input_variables = ["input", "tools", "tool_names", "agent_scratchpad", "chat_history"]

# Create the PromptTemplate using the complete template and input variables
prompt_template = PromptTemplate(
    template=template,
    input_variables=input_variables,
    partial_variables={"tools": tool_descriptions, "tool_names": ", ".join([t.name for t in tools])}
)

# Create the ReAct agent using the Ollama LLM, tools, and custom prompt template
agent = create_react_agent(llm, tools, prompt_template)

# ============================================================
# Streamlit App
# ============================================================

# Initialize the agent executor
agent_executor = AgentExecutor(agent=agent, tools=tools, handle_parsing_errors=True, verbose=True, format="json")

# Initialize Streamlit
st.title("ReAct AI Agent with pyATS and LangChain")
st.write("Ask your network questions and get insights using AI!")

# Input for user questions
user_input = st.text_input("Enter your question:")

# Session state to store chat history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = ""

if "conversation" not in st.session_state:
    st.session_state.conversation = []

# Button to submit the question
if st.button("Send"):
    if user_input:
        # Add the user input to the conversation history
        st.session_state.conversation.append({"role": "user", "content": user_input})

        # Invoke the agent with the user input and current chat history
        response = agent_executor.invoke({
            "input": user_input,
            "chat_history": st.session_state.chat_history,
            "agent_scratchpad": ""  # Initialize agent scratchpad as an empty string
        })

        # Extract the final answer
        final_answer = response.get('output', 'No answer provided.')

        # Display the question and answer
        st.write(f"**Question:** {user_input}")
        st.write(f"**Answer:** {final_answer}")

        # Add the response to the conversation history
        st.session_state.conversation.append({"role": "assistant", "content": final_answer})

        # Update chat history with the new conversation
        st.session_state.chat_history = "\n".join(
            [f"{entry['role'].capitalize()}: {entry['content']}" for entry in st.session_state.conversation]
        )

# Display the entire conversation history
if st.session_state.conversation:
    st.write("## Conversation History")
    for entry in st.session_state.conversation:
        st.write(f"**{entry['role'].capitalize()}:** {entry['content']}")
