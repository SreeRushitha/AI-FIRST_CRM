from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END
from typing import TypedDict, Optional
import os
import json
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

app = FastAPI(title="AI First CRM")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE_URL = f"postgresql://{os.getenv('DATABASE_USER')}:{os.getenv('DATABASE_PASSWORD')}@{os.getenv('DATABASE_HOST')}:{os.getenv('DATABASE_PORT')}/{os.getenv('DATABASE_NAME')}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

llm = ChatGroq(
    api_key=os.getenv("GROQ_API_KEY"),
    model="llama-3.1-8b-instant",
    temperature=0
)

class Interaction(Base):
    __tablename__ = "interactions"

    id = Column(Integer, primary_key=True, index=True)
    hcp_name = Column(String(200))
    interaction_type = Column(String(100))
    date = Column(String(50))
    time = Column(String(50))
    location = Column(String(200))
    discussion = Column(Text)
    summary = Column(Text)
    materials = Column(Text)
    samples = Column(Text)
    sentiment = Column(String(100))
    outcome = Column(Text)
    followup = Column(Text)

Base.metadata.create_all(bind=engine)

class ChatRequest(BaseModel):
    message:str

class EditRequest(BaseModel):
    summary:Optional[str]=None
    sentiment:Optional[str]=None
    outcome:Optional[str]=None
    followup:Optional[str]=None

class GraphState(TypedDict):
    user_input:str
    tool:str
    response:dict
    
def log_interaction(state: GraphState):

    prompt = f"""
    You are an AI CRM assistant.

    Extract the following fields from the conversation.

    Return ONLY valid JSON.

    {{
      "hcp_name":"",
      "interaction_type":"",
      "date":"",
      "time":"",
      "location":"",
      "discussion":"",
      "summary":"",
      "materials":"",
      "samples":"",
      "sentiment":"",
      "outcome":"",
      "followup":""
    }}

    Conversation:
    {state["user_input"]}
    """

    result = llm.invoke(prompt)

    try:
        
        content = result.content.replace("```json", "").replace("```", "").strip()
        data = json.loads(content)
        
    except:
        data = {
            "hcp_name":"",
            "interaction_type":"",
            "date":"",
            "time":"",
            "location":"",
            "discussion":state["user_input"],
            "summary":"",
            "materials":"",
            "samples":"",
            "sentiment":"",
            "outcome":"",
            "followup":""
        }

    db = SessionLocal()

    interaction = Interaction(**data)

    db.add(interaction)
    db.commit()
    db.refresh(interaction)
    db.close()

    state["response"] = {
        "tool":"log_interaction",
        "data":data
    }

    return state


def edit_interaction(interaction_id:int,data:EditRequest):

    db = SessionLocal()

    interaction = db.query(Interaction).filter(
        Interaction.id==interaction_id
    ).first()

    if not interaction:
        db.close()
        raise HTTPException(status_code=404,detail="Interaction not found")

    payload = data.model_dump(exclude_none=True)

    for key,value in payload.items():
        setattr(interaction,key,value)

    db.commit()
    db.refresh(interaction)
    db.close()

    return {
        "message":"Interaction updated"
    }
def get_history(hcp_name:str):

    db = SessionLocal()

    interactions = db.query(Interaction).filter(
        Interaction.hcp_name.ilike(f"%{hcp_name}%")
    ).all()

    db.close()

    return [
        {
            "id":i.id,
            "hcp_name":i.hcp_name,
            "interaction_type":i.interaction_type,
            "date":i.date,
            "time":i.time,
            "location":i.location,
            "discussion":i.discussion,
            "summary":i.summary,
            "materials":i.materials,
            "samples":i.samples,
            "sentiment":i.sentiment,
            "outcome":i.outcome,
            "followup":i.followup
        }
        for i in interactions
    ]


def followup_recommendation(state:GraphState):

    prompt = f"""
    You are a pharmaceutical CRM assistant.

    Based on the interaction below, suggest practical follow-up actions.

    Interaction:
    {state["user_input"]}

    Return only JSON.

    {{
        "followup":[]
    }}
    """

    result = llm.invoke(prompt)

    try:
        
        content = result.content.replace("```json", "").replace("```", "").strip()
        data = json.loads(content)
        
        
    except:
        data = {"followup":[result.content]}

    state["response"] = {
        "tool":"followup_recommendation",
        "data":data
    }

    return state


def product_recommendation(state:GraphState):

    prompt = f"""
    You are a pharmaceutical AI assistant.

    Recommend products, brochures, samples or clinical materials relevant to this interaction.

    Interaction:
    {state["user_input"]}

    Return only JSON.

    {{
        "recommendations":[]
    }}
    """

    result = llm.invoke(prompt)

    try:

        content = result.content.replace("```json", "").replace("```", "").strip()           
        data = json.loads(content)
          
    except:
        data = {"recommendations":[result.content]}

    state["response"] = {
        "tool":"product_recommendation",
        "data":data
    }

    return state
def route_tool(state:GraphState):

    prompt = f"""
    You are an AI router.

    Select exactly one tool.

    log_interaction
    followup_recommendation
    product_recommendation

    User:
    {state["user_input"]}

    Return only one tool name.
    """

    tool = llm.invoke(prompt).content.strip().lower()

    if "followup" in tool:
        state["tool"] = "followup_recommendation"
    elif "product" in tool:
        state["tool"] = "product_recommendation"
    else:
        state["tool"] = "log_interaction"

    return state


def tool_executor(state:GraphState):

    if state["tool"] == "log_interaction":
        return log_interaction(state)

    if state["tool"] == "followup_recommendation":
        return followup_recommendation(state)

    if state["tool"] == "product_recommendation":
        return product_recommendation(state)

    return state


graph = StateGraph(GraphState)

graph.add_node("router", route_tool)
graph.add_node("executor", tool_executor)

graph.set_entry_point("router")

graph.add_edge("router", "executor")
graph.add_edge("executor", END)

agent = graph.compile()

@app.get("/")
def home():
    return {
        "message":"AI First CRM Backend",
        "status":"running"
    }


@app.post("/chat")
def chat(request:ChatRequest):

    state = {
        "user_input":request.message,
        "tool":"",
        "response":{}
    }

    result = agent.invoke(state)

    return result["response"]


@app.put("/edit/{interaction_id}")
def edit(interaction_id:int,data:EditRequest):

    return edit_interaction(interaction_id,data)


@app.get("/history/{hcp_name}")
def history(hcp_name:str):

    return get_history(hcp_name)


@app.get("/interaction/{interaction_id}")
def interaction(interaction_id:int):

    db = SessionLocal()

    interaction = db.query(Interaction).filter(
        Interaction.id==interaction_id
    ).first()

    db.close()

    if not interaction:
        raise HTTPException(
            status_code=404,
            detail="Interaction not found"
        )

    return {
        "id":interaction.id,
        "hcp_name":interaction.hcp_name,
        "interaction_type":interaction.interaction_type,
        "date":interaction.date,
        "time":interaction.time,
        "location":interaction.location,
        "discussion":interaction.discussion,
        "summary":interaction.summary,
        "materials":interaction.materials,
        "samples":interaction.samples,
        "sentiment":interaction.sentiment,
        "outcome":interaction.outcome,
        "followup":interaction.followup
    }


@app.post("/log")
def log(request:ChatRequest):

    state = {
        "user_input":request.message,
        "tool":"log_interaction",
        "response":{}
    }

    result = log_interaction(state)

    return result["response"]


if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "app:app",
        host=os.getenv("APP_HOST"),
        port=int(os.getenv("APP_PORT")),
        reload=True
    )