import os
import json
import difflib
import streamlit as st
from pyats.topology import loader
from langchain_community.llms import Ollama
from langchain_core.tools import tool, render_text_description
from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from genie.libs.parser.utils import get_parser

# Function to run any supported show command using pyATS
def run_show_command(command: str):
    try:
        # Disallowed modifiers
        disallowed_modifiers = ['|', 'include', 'exclude', 'begin', 'redirect', '>', '<']

        # Check for disallowed modifiers
        for modifier in disallowed_modifiers:
            if modifier in command:
                return {"error": f"Command '{command}' contains disallowed modifier '{modifier}'. Modifiers are not allowed."}

        # Load the testbed
        print("Loading testbed...")
        testbed = loader.load('testbed.yaml')

        # Access the device from the testbed
        device = testbed.devices['Cat8000V']

        # Connect to the device
        print("Connecting to device...")
        device.connect()

        # Check if a pyATS parser is available for the command
        print(f"Checking if a parser exists for the command: {command}")
        parser = get_parser(command, device)
        if parser is None:
            return {"error": f"No parser available for the command: {command}"}

        # Execute the command and parse the output using Genie
        print(f"Executing '{command}'...")
        parsed_output = device.parse(command)

        # Close the connection
        print("Disconnecting from device...")
        device.disconnect()

        # Return the parsed output (JSON)
        return parsed_output
    except Exception as e:
        # Handle exceptions and provide error information
        return {"error": str(e)}

# Function to load supported commands from a JSON file
def load_supported_commands():
    file_path = 'commands.json'  # Ensure the file is named correctly

    # Check if the file exists
    if not os.path.exists(file_path):
        return {"error": f"Supported commands file '{file_path}' not found."}

    try:
        # Load the JSON file with the list of commands
        with open(file_path, 'r') as f:
            data = json.load(f)

        # Extract the command strings into a list
        command_list = [entry['command'] for entry in data]
        return command_list
    except Exception as e:
        return {"error": f"Error loading supported commands: {str(e)}"}

# Function to check if a command is supported with fuzzy matching
def check_command_support(command: str) -> dict:
    command_list = load_supported_commands()

    if "error" in command_list:
        return command_list

    # Find the closest matches to the input command using difflib
    close_matches = difflib.get_close_matches(command, command_list, n=1, cutoff=0.6)

    if close_matches:
        closest_command = close_matches[0]
        return {"status": "supported", "closest_command": closest_command}
    else:
        return {"status": "unsupported", "message": f"The command '{command}' is not supported. Please check the available commands."}

# Function to process agent response and chain tools
def process_agent_response(response):
    if response.get("status") == "supported" and "next_tool" in response.get("action", {}):
        next_tool = response["action"]["next_tool"]
        command_input = response["action"]["input"]

        # Automatically invoke the next tool (run_show_command_tool)
        return agent_executor.invoke({
            "input": command_input,
            "chat_history": st.session_state.chat_history,
            "agent_scratchpad": "",
            "tool": next_tool
        })
    else:
        return response

# Define the custom tool using the langchain `tool` decorator
@tool
def run_show_command_tool(command: str) -> dict:
    """Execute a 'show' command on the router using pyATS and return the parsed JSON output."""
    return run_show_command(command)

# New tool for checking if a command is supported and chaining to run_show_command_tool
@tool
def check_supported_command_tool(command: str) -> dict:
    """Check if a command is supported by pyATS based on the command list and return the details."""
    result = check_command_support(command)

    if result.get('status') == 'supported':
        # Automatically run the show command if the command is valid
        closest_command = result['closest_command']
        return {
            "status": "supported",
            "message": f"The closest supported command is '{closest_command}'",
            "action": {
                "next_tool": "run_show_command_tool",
                "input": closest_command
            }
        }
    return result

# ============================================================
# Define the agent with a custom prompt template
# ============================================================

# Initialize the Ollama LLM
llm = Ollama(model="llama3.1")

# Create a list of tools
tools = [run_show_command_tool, check_supported_command_tool]

# Render text descriptions for the tools for inclusion in the prompt
tool_descriptions = render_text_description(tools)

template = """
Assistant is a large language model trained by OpenAI.

Assistant is designed to assist with a wide range of tasks, from answering simple questions to providing in-depth explanations and discussions on various topics. As a language model, Assistant can generate human-like text based on the input it receives, allowing it to engage in natural-sounding conversations and provide coherent and relevant responses.

Assistant is constantly learning and improving. It can process and understand large amounts of text and use this knowledge to provide accurate and informative responses to a wide range of questions. Additionally, Assistant can generate its text based on the input it receives, allowing it to engage in discussions and provide explanations and descriptions on various topics.

NETWORK INSTRUCTIONS:

Assistant is a network assistant with the capability to run tools to gather information and provide accurate answers. You MUST use the provided tools for checking interface statuses, retrieving the running configuration, or finding which commands are supported.

**Important Guidelines:**

1. **If you are certain of the command, use the 'run_show_command_tool' to execute it.**
2. **If you are unsure of the command or if there is ambiguity, use the 'check_supported_command_tool' to verify the command or get a list of available commands.**
3. **If the 'check_supported_command_tool' finds a valid command, automatically use 'run_show_command_tool' to run that command.**
4. **Do NOT use any command modifiers such as pipes (`|`), `include`, `exclude`, `begin`, `redirect`, or any other modifiers.**
5. **If the command is not recognized, always use the 'check_supported_command_tool' to clarify the command before proceeding.**

**Using the Tools:**

- If you are confident about the command, use the 'run_show_command_tool'.
- If there is any doubt or ambiguity, always check the command first with the 'check_supported_command_tool'.

To use a tool, follow this format:

Thought: Do I need to use a tool? Yes
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action

If the first tool provides a valid command, you MUST immediately run the 'run_show_command_tool' without waiting for another input. Follow the flow like this:

Example:

Thought: Do I need to use a tool? Yes
Action: check_supported_command_tool
Action Input: "show ip access-lists"
Observation: "The closest supported command is 'show ip access-list'."

Thought: Do I need to use a tool? Yes
Action: run_show_command_tool
Action Input: "show ip access-list"
Observation: [parsed output here]

When you have a response to say to the Human, or if you do not need to use a tool, you MUST use the format:

Thought: Do I need to use a tool? No
Final Answer: [your response here]

Correct Formatting is Essential: Ensure that every response follows the format strictly to avoid errors.

TOOLS:

Assistant has access to the following tools:

- check_supported_command_tool: Finds and returns the closest supported commands.
- run_show_command_tool: Executes a supported 'show' command on the network device and returns the parsed output.

Begin!

Previous conversation history:

{chat_history}

New input: {input}

{agent_scratchpad}
"""

# Define the input variables separately
input_variables = ["input", "agent_scratchpad", "chat_history"]

# Create the PromptTemplate using the complete template and input variables
prompt_template = PromptTemplate(
    template=template,
    input_variables=input_variables,
    partial_variables={
        "tools": tool_descriptions,
        "tool_names": ", ".join([t.name for t in tools])
    }
)

# Create the ReAct agent using the Ollama LLM, tools, and custom prompt template
agent = create_react_agent(llm, tools, prompt_template)

# ============================================================
# Streamlit App
# ============================================================

# Initialize the agent executor
agent_executor = AgentExecutor(agent=agent, tools=tools, handle_parsing_errors=True, verbose=True, max_iterations=5)

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

        # Check if chaining is needed (i.e., next tool)
        final_response = process_agent_response(response)

        # Extract the final answer
        final_answer = final_response.get('output', 'No answer provided.')

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
