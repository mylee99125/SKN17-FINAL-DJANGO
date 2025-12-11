from django.shortcuts import redirect, render
from django.http import JsonResponse
from . import services

def subscription_ready(request):
    """ [GET] 카카오페이 결제 준비 요청 """
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('/')
    
    plan_code = request.GET.get('plan', 'BASIC')

    try:
        next_url, session_data = services.prepare_kakao_payment(user_id, plan_code)
        
        for key, value in session_data.items():
            request.session[key] = value

        return redirect(next_url)

    except ValueError as e:
        return JsonResponse({'message': str(e)}, status=400)
    except Exception as e:
        return JsonResponse({'message': f'오류 발생: {str(e)}'}, status=500)


def subscription_approve(request):
    """ [GET] 카카오페이 결제 승인 요청 (Redirect URL) """
    pg_token = request.GET.get("pg_token")
    
    required_keys = ['tid', 'partner_order_id', 'partner_user_id', 'plan_id', 'total_amount']
    session_data = {k: request.session.get(k) for k in required_keys}

    if not pg_token or not all(session_data.values()):
        return redirect('videos/home')

    is_success, success_data, error_msg = services.approve_kakao_payment(pg_token, session_data)

    for k in required_keys:
        if k in request.session: del request.session[k]

    if is_success:
        context = {
            'user': success_data['user'],  
            'payment_success': True, 
            'plan_name': success_data['plan_name'],
            'payment_date': success_data['payment_date'], 
            'payment_amount': success_data['payment_amount'], 
            'show_plan_modal': False
        }
        return render(request, 'home.html', context)
    else:
        reason = error_msg if error_msg else '데이터 처리 중 오류'
        return JsonResponse({'message': '결제 승인 실패', 'reason': reason}, status=400)


def cancel_subscription(request):
    """ [POST] 구독 해지 """
    if request.method == 'POST':
        user_id = request.session.get('user_id')
        if not user_id:
            return JsonResponse({'success': False, 'message': '로그인이 필요합니다.'})

        try:
            date_str = services.cancel_subscription_logic(user_id)
            return JsonResponse({
                'success': True, 
                'message': '해지가 완료되었습니다.', 
                'date': date_str
            })
        except ValueError as e:
            return JsonResponse({'success': False, 'message': str(e)})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'서버 오류: {str(e)}'})

    return JsonResponse({'success': False, 'message': '잘못된 요청'})


def renew_subscription(request):
    """ [POST] 구독 갱신 """
    if request.method == 'POST':
        user_id = request.session.get('user_id')
        if not user_id:
            return JsonResponse({'success': False, 'message': '로그인이 필요합니다.'})

        try:
            services.renew_subscription_logic(user_id)
            return JsonResponse({'success': True, 'message': '구독이 성공적으로 갱신되었습니다.'})
        except ValueError as e:
            return JsonResponse({'success': False, 'message': str(e)})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'서버 오류: {str(e)}'})

    return JsonResponse({'success': False, 'message': '잘못된 요청'})


