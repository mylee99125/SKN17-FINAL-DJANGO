import os
import pandas as pd
from django.core.management.base import BaseCommand
from chatbot.models import Chatbot
from django.conf import settings

class Command(BaseCommand):
    help = '엑셀 파일에서 챗봇 규칙을 가져와 DB에 저장합니다.'

    def handle(self, *args, **kwargs):
        file_path = os.path.join(settings.BASE_DIR, 'static', 'data', 'word_rag.xlsx')

        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f'파일을 찾을 수 없습니다: {file_path}'))
            return

        try:
            df = pd.read_excel(file_path)
            
            count = 0
            for _, row in df.iterrows():
                rule = str(row['rule']).strip()
                response = str(row['response']).strip()

                obj, created = Chatbot.objects.get_or_create(
                    rule=rule,
                    defaults={'response': response}
                )
                if created:
                    count += 1
            
            self.stdout.write(self.style.SUCCESS(f'총 {count}개의 새로운 규칙이 등록되었습니다!'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'에러 발생: {str(e)}'))