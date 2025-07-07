from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from cal_agent import agent 

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class Query(BaseModel):
    question: str

@app.post("/chat")
async def chat_endpoint(query: Query):
    try:
        result = agent.run(query.question)
        return {"response": result}
    except Exception as e:
        return {"error": str(e)}
