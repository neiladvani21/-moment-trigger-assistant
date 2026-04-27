from langchain_groq import ChatGroq
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from config import GROQ_API_KEY, LLM_MODEL
from database import load_history, save_messages
from tools import TOOLS

SYSTEM_PROMPT = (
    "You are a location-based marketing assistant for a retail activation platform. "
    "Given a user request, use your tools to gather weather, find nearby POIs, and "
    "suggest a moment-based marketing activation with a recommended geofence radius. "
    "Always return a structured activation plan with:\n"
    "- Weather context\n"
    "- List of nearby POIs\n"
    "- Suggested offer copy\n"
    "- Recommended geofence radius and reasoning\n\n"
    "STRICT RULES:\n"
    "1. Always call get_weather and suggest_geofence on every request\n"
    "2. Never assume, guess, or hallucinate POI data\n"
    "3. If search_pois fails say: POI search unavailable, please try again\n"
    "4. Never generate geofence if POI search failed\n"
    "5. If any tool fails, report honestly and suggest retry\n"
    "6. When generating suggested offer copy, always mention at least one specific POI name from the search results. "
    "For example, if Whole Foods is in the results, say 'Visit Whole Foods today' instead of 'visit our nearby stores'.\n"
    "7. You have access to conversation history. Use it to understand follow-up questions and references "
    "to previous searches (e.g. 'what about in summer?' refers to the last location discussed)."
)

_llm = ChatGroq(
    api_key=GROQ_API_KEY,
    model=LLM_MODEL,
)

_prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

_agent = create_tool_calling_agent(llm=_llm, tools=TOOLS, prompt=_prompt)

executor = AgentExecutor(
    agent=_agent,
    tools=TOOLS,
    return_intermediate_steps=True,
    verbose=True,
)


def run_with_history(session_id: str, message: str) -> dict:
    raw_history = load_history(session_id)

    chat_history = []
    for entry in raw_history:
        if entry["role"] == "human":
            chat_history.append(HumanMessage(content=entry["content"]))
        else:
            chat_history.append(AIMessage(content=entry["content"]))

    result = executor.invoke({
        "input": message,
        "chat_history": chat_history,
    })

    save_messages(session_id, message, result["output"])

    return result
