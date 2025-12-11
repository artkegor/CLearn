from agents.tutor.agent_setup import create_c_agent
from langchain_core.messages import HumanMessage
from html import escape

agent = create_c_agent()


def answer_question(question: str, user_id: str):
    """
    Answer a C programming question.
    """
    config = {"configurable": {"thread_id": user_id}}
    response = agent.invoke(
        {"messages": [HumanMessage(content=question)]},
        config=config
    )
    print(response)
    for message in response['messages']:
        if message.__class__.__name__ == 'AIMessage':
            return escape(message.content)

    return ""
