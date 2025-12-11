import json
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from . import services  

@require_POST  
def chat_api(request):
    try:
        data = json.loads(request.body)
        user_msg = data.get('message', '').strip()
        
        if not user_msg:
            return JsonResponse({'response': '질문 내용을 입력해주세요.'})

        best_response = services.get_chatbot_response(user_msg)
        return JsonResponse({'response': best_response})

    except json.JSONDecodeError:
        return JsonResponse({'response': '잘못된 데이터 형식입니다.'}, status=400)
    
    except Exception as e:
        return JsonResponse({'response': f'서버 오류: {str(e)}'}, status=500)