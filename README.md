# ReAct AI Agent for Cisco IOS XE using Cisco pyATS
Talk to your network using a ReAct agentic approach 

## Install 
Please make a virtual environment and install the requirements.txt 

```console 
~/ReACT_AI_Agent_for_Cisco_IOS_XE$ python3 -m venv REACTAGENT
~/ReACT_AI_Agent_for_Cisco_IOS_XE$ source REACTAGENT/bin/activate 
(REACTAGENT) ~/ReACT_AI_Agent_for_Cisco_IOS_XE$ pip install -r requirements.txt
```

## Usage 
(For now before I turn this into a streamlit app)
Adjust line 237 - the input question 

```python
# Define the input question
input_question = "What Cisco IOS-XE version am I running?"
```

To the question you want to ask then just run 
(REACTAGENT) ~/ReACT_AI_Agent_for_Cisco_IOS_XE$ python3 reacti_ai_agent_cisco_ios_xe.py

### Please add more 'tools' / functions / parsed pyATS commands! 

### It Hates a lot of JSON 
Something like show interfaces returns a LOT of JSON which sort of breaks the agent - happy for suggestions here on how to handle that



