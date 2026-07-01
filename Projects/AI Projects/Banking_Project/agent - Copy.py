from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from dotenv import load_dotenv
load_dotenv()
from langchain_google_genai import ChatGoogleGenerativeAI # Changed this
from langchain_core.messages import BaseMessage

# Import your custom tool from the tools.py file
from tools import get_balance 

# 1. Define the "Memory"
class State(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

# 2. Setup the LLM (Using Gemini)
# Ensure your GOOGLE_API_KEY is set in your environment variables
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash") # Changed this
tools = [get_balance]
llm_with_tools = llm.bind_tools(tools)

# 3. Create the Logic Node
def chatbot(state: State):
    return {"messages": [llm_with_tools.invoke(state["messages"])]}

# 4. Build the Graph
builder = StateGraph(State)
builder.add_node("chatbot", chatbot)
builder.add_node("tools", ToolNode(tools))

# 5. Define the Flow
builder.add_edge(START, "chatbot")
builder.add_conditional_edges("chatbot", tools_condition)
builder.add_edge("tools", "chatbot")

# Compile
agent = builder.compile()