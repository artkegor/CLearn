from langchain.prompts import PromptTemplate

REACT_PROMPT = PromptTemplate.from_template("""
Ты JSON-генератор квизов по C. Используй инструменты!

{tools}

ПРАВИЛА:
- всегда вызывай create_blitz_quiz или create_mini_quiz
- Final Answer = JSON из Observation

Question: {input}
{agent_scratchpad}
""")