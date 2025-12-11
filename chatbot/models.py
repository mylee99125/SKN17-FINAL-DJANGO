from django.db import models

class Chatbot(models.Model):
    """
    11) 룰베이스 챗봇 데이터
    """
    chatbot_id = models.AutoField(primary_key=True)
    rule = models.CharField(max_length=30, help_text="유저 질문에 포함된 핵심 키워드")
    response = models.CharField(max_length=500, help_text="챗봇의 답변")
    
    def __str__(self):
        return f"[{self.keyword}] -> {self.response[:20]}..."

    class Meta:
        db_table = 'CHATBOT'
        verbose_name = '챗봇'