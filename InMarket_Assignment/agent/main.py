import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agent import executor
from config import AGENT_TIMEOUT

app = FastAPI(title="Location Moment Trigger Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://0.0.0.0:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_thread_pool = ThreadPoolExecutor(max_workers=4)


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str
    tools_used: List[str]


def _run_agent(message: str) -> dict:
    return executor.invoke({"input": message})


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    loop = asyncio.get_event_loop()
    try:
        result = await asyncio.wait_for(
            loop.run_in_executor(_thread_pool, _run_agent, request.message),
            timeout=AGENT_TIMEOUT,
        )
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Agent timed out. Please retry.")

    tools_used = list(dict.fromkeys(
        step[0].tool
        for step in result.get("intermediate_steps", [])
        if hasattr(step[0], "tool")
    ))

    return ChatResponse(
        response=result["output"],
        tools_used=tools_used,
    )
