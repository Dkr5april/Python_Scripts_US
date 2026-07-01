import os
import logging
import sys
from dotenv import load_dotenv
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import BaseMessage
from tools import get_balance

# 1. FORCED DEBUGGING: Enable detailed logs to terminal
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logger = logging.getLogger("langchain")
logger.setLevel(logging.DEBUG)

# 2. Load ENV and verify keys
load_dotenv()
print(f"DEBUG: GOOGLE_API_KEY present: {bool(os.getenv('GOOGLE_API_KEY'))}")
print(f"DEBUG: LANGCHAIN_API_KEY present: {bool(os.getenv('LANGCHAIN_API_KEY'))}")
print(f"DEBUG: LANGCHAIN_PROJECT: {os.getenv('LANGCHAIN_PROJECT')}")

# 3. Define State and LLM
class State(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash")
tools = [get_balance]
llm_with_tools = llm.bind_tools(tools)

# 4. Logic Node
def chatbot(state: State):
    print("DEBUG: Chatbot node invoked")
    response = llm_with_tools.invoke(state["messages"])
    return {"messages": [response]}

# 5. Build Graph
builder = StateGraph(State)
builder.add_node("chatbot", chatbot)
builder.add_node("tools", ToolNode(tools))
builder.add_edge(START, "chatbot")
builder.add_conditional_edges("chatbot", tools_condition)
builder.add_edge("tools", "chatbot")

agent = builder.compile()

# 6. Execution with test query
if __name__ == "__main__":
    print("DEBUG: Agent starting...")
    try:
        # Use a simple invoke to get the full final state, 
        # or iterate through the stream to see the progress
        final_state = agent.invoke({"messages": [("user", "What is my balance?")]})
        
        # The result is in the last message of the 'messages' list
        last_message = final_state["messages"][-1]
        
        print("\n" + "="*30)
        print("AGENT RESPONSE:")

        # The AI's response is a list of blocks; we want the text content
        # Note the indentation here:
        for block in last_message.content:
            if isinstance(block, dict) and 'text' in block:
                print(block['text'])

        print("="*30)
        
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")