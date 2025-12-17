import json
import traceback
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from . import services
from .models import UserInfo, UserUploadVideo 

def home(request):
    user_id = request.session.get('user_id')
    if not user_id: return redirect('/')

    try:
        search_query = request.GET.get('q', '').strip()
        req_team = request.GET.get('team', '').strip().upper()
        
        sort_option = request.GET.get('sort', 'latest')
        context = services.get_home_context(user_id, search_query, req_team, sort_option)
        
        return render(request, 'home.html', context)

    except UserInfo.DoesNotExist:
        request.session.flush()
        return redirect('/')

def get_video_list_api(request):
    try:
        section_type = request.GET.get('type')
        page = int(request.GET.get('page', 1))
        target_code = request.GET.get('team', 'LG')
        search_query = request.GET.get('q', '')
        sort_option = request.GET.get('sort', 'latest')

        videos, has_next = services.get_video_list_api_logic(
            section_type, page, target_code, search_query, sort_option
        )

        return JsonResponse({'videos': videos, 'has_next': has_next})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def play(request, video_id):
    user_id = request.session.get('user_id')
    if not user_id: return redirect('/')
    
    try:
        context = services.get_play_context(user_id, video_id)
        return render(request, 'play.html', context)

    except PermissionError:
        # 무료 체험 만료 시 처리
        return HttpResponse("""
            <script>
                alert('무료 체험이 종료되었습니다.\\n무제한 시청을 위해 플랜을 구독해주세요.');
                location.href = '/videos/home'; 
            </script>
        """)
    except UserInfo.DoesNotExist:
        request.session.flush()
        return redirect('/')

def my_videos(request):
    user_id = request.session.get('user_id')
    if not user_id: return redirect('/')
    
    try:
        context = services.get_my_videos_context(user_id)
        return render(request, 'my_videos.html', context)

    except PermissionError:
        return redirect('videos:home')
    except UserInfo.DoesNotExist:
        request.session.flush()
        return redirect('/')
    except Exception as e:
        print("\n" + "="*50)
        print("🔥 [500 에러 원인 잡았다 요놈] 🔥")
        print(f"에러 메시지: {e}")
        print("상세 위치:")
        traceback.print_exc()
        print("="*50 + "\n")
        raise e

def upload_video(request):
    user_id = request.session.get('user_id')

    if request.method == 'POST' and user_id:
        try:
            uploaded_file = request.FILES.get('video_file')
            title = request.POST.get('video_title')
            commentator = request.POST.get('commentator')
            
            if not uploaded_file:
                return JsonResponse({'status': 'error', 'message': '파일이 없습니다.'}, status=400)

            result = services.process_upload_video(
                user_id=user_id, 
                uploaded_file=uploaded_file, 
                title=title, 
                commentator_name=commentator
            )

            return JsonResponse({
                'status': 'success', 
                'message': '업로드 완료!',
                'file_id': result.get('file_id')
            })
            
        except ValueError as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
        except Exception as e:
            print(f"업로드 에러: {e}")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
            
    return JsonResponse({'status': 'error', 'message': '잘못된 접근입니다.'}, status=400)

@require_POST
def process_download(request, video_id):
    user_id = request.session.get('user_id')
    if not user_id:
        return JsonResponse({'status': 'error', 'message': '로그인이 필요합니다.'}, status=401)

    try:
        result = services.process_download_logic(user_id, video_id)
        result['status'] = 'success'
        return JsonResponse(result)

    except PermissionError:
        return JsonResponse({
            'status': 'limit_exceeded', 
            'message': '다운로드 허용 횟수(10회)를 초과하였습니다.\n추가 다운로드가 필요한 경우 관리자에게 문의해주세요.'
        }, status=403)
    except UserUploadVideo.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': '영상을 찾을 수 없습니다.'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': '서버 오류가 발생했습니다.'}, status=500)

@require_POST
def delete_video(request, video_id):
    user_id = request.session.get('user_id')
    if not user_id:
        return JsonResponse({'status': 'error', 'message': '로그인이 필요합니다.'}, status=401)

    try:
        services.delete_video_logic(user_id, video_id)
        return JsonResponse({'status': 'success', 'message': '영상이 삭제되었습니다.'})

    except UserUploadVideo.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': '삭제할 영상을 찾을 수 없습니다.'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

def play_user_video(request, video_id):
    user_id = request.session.get('user_id')
    if not user_id: return redirect('/')
    
    try:
        context = services.get_user_play_context(user_id, video_id)
        return render(request, 'play.html', context)

    except UserInfo.DoesNotExist:
        request.session.flush()
        return redirect('/')