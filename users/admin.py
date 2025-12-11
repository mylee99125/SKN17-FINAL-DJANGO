import json
from django.contrib import admin
from videos.forms import SubtitleAdminForm
from users.models import CommonCode, UserInfo
from videos.models import FileInfo, UserUploadVideo, HighlightVideo, SubtitleInfo
from payments.models import PlanInfo, SubscribeHistory, PaymentHistory, InvoiceInfo

# [1] 파일 정보 관리 (개별 업로드용)
@admin.register(FileInfo)
class FileInfoAdmin(admin.ModelAdmin):
    list_display = ('file_id', 'file_path') 
    search_fields = ('file_path',)


# [2] 하이라이트 영상 관리 
@admin.register(HighlightVideo)
class HighlightVideoAdmin(admin.ModelAdmin):
    list_display = ('highlight_title', 'match_date', 'video_category')
    search_fields = ('highlight_title',)
    autocomplete_fields = [] 


# [3] 자막정보 관리
@admin.register(SubtitleInfo)
class SubtitleInfoAdmin(admin.ModelAdmin):
    form = SubtitleAdminForm
    list_display = ('subtitle_id', 'video_file', 'commentator_code', 'preview_subtitle')

    def save_model(self, request, obj, form, change):
        uploaded_file = form.cleaned_data.get('json_file')
        
        if uploaded_file:
            try:
                file_content = uploaded_file.read().decode('utf-8')
                raw_data = json.loads(file_content)
                
                processed_data = []

                for item in raw_data:
                    start = round(float(item.get('set_start_sec', 0)), 2)
                    end = round(float(item.get('set_end_sec', 0)), 2)
                    
                    text_parts = []
                    if item.get('caster_text'):
                        text_parts.append(f"{item['caster_text']}")
                    
                    if item.get('analyst_text'):
                        text_parts.append(f"{item['analyst_text']}")
                    
                    full_text = " ".join(text_parts)

                    if full_text.strip():
                        processed_data.append({
                            "start": start,
                            "end": end,
                            "text": full_text
                        })

                json_string = json.dumps(processed_data, ensure_ascii=False)
                binary_data = json_string.encode('utf-8')

                obj.subtitle = binary_data

            except Exception as e:
                print(f"JSON 변환 중 에러 발생: {e}")

        super().save_model(request, obj, form, change)

    def preview_subtitle(self, obj):
        if not obj.subtitle:
            return "데이터 없음"
        try:
            text_data = obj.subtitle.decode('utf-8')
            json_data = json.loads(text_data)
            if json_data:
                return f"{json_data[0]['text'][:30]}..." 
            return "빈 데이터"
        except:
            return "디코딩 오류"
    
    preview_subtitle.short_description = "자막 내용 미리보기"


# [4] 나머지 모델들은 반복문으로 등록
models_to_register = [UserUploadVideo, UserInfo, CommonCode, PlanInfo, SubscribeHistory, InvoiceInfo, PaymentHistory]

for model in models_to_register:
    try:
        admin.site.register(model)
    except admin.sites.AlreadyRegistered:
        pass