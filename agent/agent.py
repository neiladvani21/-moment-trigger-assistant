from langchain_groq import ChatGroq
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from config import GROQ_API_KEY, LLM_MODEL
from database import load_history, save_messages
from tools import TOOLS

SYSTEM_PROMPT = (
    "You are a location-based marketing assistant for a retail activation platform. "
    "The current local time is: {local_time}.\n\n"
    "Given a user request, use your tools to gather weather, find nearby POIs, and "
    "suggest a moment-based marketing activation with a recommended geofence radius. "
    "Always return a structured activation plan with:\n"
    "- Weather context\n"
    "- Time-of-day context\n"
    "- List of nearby POIs\n"
    "- Suggested offer copy\n"
    "- Recommended geofence radius and reasoning\n\n"
    "TIME-BASED ACTIVATION RULES — tailor your offer copy based on the current time:\n"
    "- Morning (6am–11am): Focus on commute, breakfast, energy boost, productivity angles\n"
    "- Lunch (11am–2pm): Focus on quick meal deals, midday break, lunch crowd angles\n"
    "- Afternoon (2pm–6pm): Focus on afternoon slump, snack breaks, recharge angles\n"
    "- Evening (6pm–10pm): Focus on after-work wind-down, social meetups, dinner angles\n"
    "- Night (10pm–6am): Focus on late-night study, night shift workers, quiet time angles\n\n"
    "STRICT RULES:\n"
    "1. Always call geocode_location FIRST to get coordinates, then use EXACTLY those lat/lon values for search_pois. Never use coordinates from memory or previous turns.\n"
    "2. Always call get_weather and suggest_geofence on every request.\n"
    "3. Never assume, guess, or hallucinate POI data.\n"
    "4. If search_pois returns 'No ... locations found', tell the user clearly: no venues of that type exist "
    "in that area according to OpenStreetMap, and suggest trying a larger radius or nearby city.\n"
    "5. If search_pois returns 'unavailable' or an error, tell the user the POI service is temporarily unavailable and suggest retrying.\n"
    "6. Never generate geofence or offer copy if POI search returned no results or failed.\n"
    "7. If any tool fails, report honestly and suggest retry.\n"
    "6. When generating suggested offer copy, always mention at least one specific POI name from the search results. "
    "For example, if Whole Foods is in the results, say 'Visit Whole Foods today' instead of 'visit our nearby stores'.\n"
    "7. You have access to conversation history. Use it to understand follow-up questions and references "
    "to previous searches (e.g. 'what about in summer?' refers to the last location discussed).\n"
    "8. Always reference the time of day in your offer copy. For example: "
    "'Beat the morning rush at Starbucks' or 'Perfect for your lunch break at Shake Shack'."
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


def run_with_history(session_id: str, message: str, local_time: str = "unknown") -> dict:
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
        "local_time": local_time,
    })

    save_messages(session_id, message, result["output"])

    return result


async def stream_with_history(session_id: str, message: str, local_time: str = "unknown"):
    """Async generator that yields text tokens then a final metadata dict."""
    raw_history = load_history(session_id)

    chat_history = []
    for entry in raw_history:
        if entry["role"] == "human":
            chat_history.append(HumanMessage(content=entry["content"]))
        else:
            chat_history.append(AIMessage(content=entry["content"]))

    full_output = []
    intermediate_steps = []

    async for event in executor.astream_events(
        {"input": message, "chat_history": chat_history, "local_time": local_time},
        version="v2",
    ):
        kind = event["event"]

        # Stream final LLM response tokens
        if kind == "on_chat_model_stream":
            chunk = event["data"].get("chunk")
            if chunk and hasattr(chunk, "content") and chunk.content:
                full_output.append(chunk.content)
                yield {"type": "token", "content": chunk.content}

        # Collect intermediate tool steps for map/POI data
        elif kind == "on_tool_end":
            tool_name = event.get("name", "")
            output = event["data"].get("output", "")
            # Reconstruct a minimal step tuple for _extract_map_data
            class _FakeAction:
                def __init__(self, tool): self.tool = tool
            intermediate_steps.append((_FakeAction(tool_name), output))

    final_output = "".join(full_output)
    save_messages(session_id, message, final_output)

    yield {
        "type": "done",
        "output": final_output,
        "intermediate_steps": intermediate_steps,
    }