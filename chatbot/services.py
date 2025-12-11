from .models import Chatbot

def get_chatbot_response(user_msg: str) -> str:
    default_response = "죄송합니다. 제가 답변할 수 없는 내용입니다. 다른 질문을 해주세요."

    exact_match = Chatbot.objects.filter(rule=user_msg).first()
    if exact_match:
        return exact_match.response

    rules = Chatbot.objects.all()
    sorted_rules = sorted(rules, key=lambda x: len(x.rule), reverse=True)

    for r in sorted_rules:
        if r.rule in user_msg:
            return r.response

    return default_response