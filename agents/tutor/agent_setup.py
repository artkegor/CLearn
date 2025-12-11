from langchain.agents import create_agent
from langchain.agents.middleware import SummarizationMiddleware, LLMToolSelectorMiddleware, ModelCallLimitMiddleware, ToolRetryMiddleware
from langchain_deepseek import ChatDeepSeek
from langgraph.checkpoint.memory import InMemorySaver
from agents.tutor.config import MODEL_NAME, TEMPERATURE
from agents.tutor.system_prompt import system_prompt
from agents.tutor.tools.syntax_tool import syntax_search
from agents.tutor.tools.control_flow_tool import control_flow_search
from agents.tutor.tools.data_structures_tool import data_structures_search
from agents.tutor.tools.functions_tool import functions_search
from agents.tutor.tools.memory_files_tool import memory_files_search


tools = [syntax_search, control_flow_search, data_structures_search, functions_search, memory_files_search]

checkpointer = InMemorySaver()
model = ChatDeepSeek(model=MODEL_NAME, temperature=TEMPERATURE)

def create_c_agent():
    agent = create_agent(
        model=model,
        tools=tools,
        checkpointer=checkpointer,
        system_prompt=system_prompt,
        middleware=[
            SummarizationMiddleware(
                model=ChatDeepSeek(model="deepseek-chat", temperature=0.1),
                trigger=("tokens", 4000),
                keep=("messages", 10),
            ),
            LLMToolSelectorMiddleware(
                model=ChatDeepSeek(model="deepseek-chat", temperature=0.0),
                system_prompt="""🎯 Выбери оптимальное количество RAG tools (1-3): ...""",
                max_tools=3
            ),
            ModelCallLimitMiddleware(run_limit=3),
            ToolRetryMiddleware(max_retries=3, on_failure='continue', backoff_factor=2.0, initial_delay=1.0, jitter=True)
        ]
    )
    return agent