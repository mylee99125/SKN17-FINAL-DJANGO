from django import forms
from .models import SubtitleInfo

class SubtitleAdminForm(forms.ModelForm):
    json_file = forms.FileField(
        label='자막 JSON 파일',
        help_text='* vocals_timeline...json 파일을 업로드하세요.',
        required=True
    )

    class Meta:
        model = SubtitleInfo
        exclude = ['subtitle']