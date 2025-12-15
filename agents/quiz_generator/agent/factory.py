from langchain_classic.agents import AgentExecutor

from agents.quiz_generator.config.llm import init_llm
from agents.quiz_generator.tools.registry import TOOLS

from langchain_core.prompts.prompt import PromptTemplate
from langgraph.prebuilt import create_react_agent

react_prompt = """Ты JSON-генератор квизов по C. Используй инструменты!

{tools}

ПРАВИЛА:
- Обязательно вызывай create_blitz_quiz или create_mini_quiz
- Final Answer = JSON из Observation
- Не создавай вручную, используй только tools

Доступные инструменты: {tool_names}

Формат ответа:
Question: {input}
Thought: что нужно сделать
Action: название_инструмента
Action Input: параметры
Observation: результат
Thought: проверяю результат
Final Answer: JSON результат

Question: {input}
{agent_scratchpad}"""


def build_agent():
    prompt = PromptTemplate.from_template(
        react_prompt
    )
    llm = init_llm()
    agent = create_react_agent(
        tools=TOOLS,
        model=llm
    )
    agent_executor = AgentExecutor(
        agent=agent,
        tools=TOOLS,
        prompt=prompt,
        verbose=True
    )
    return agent_executor
