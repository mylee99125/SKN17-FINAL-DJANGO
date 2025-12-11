import os
from django.db import models
from users.models import CommonCode, UserInfo

class FileInfo(models.Model):
    """
    3) 파일 정보
    시스템에 업로드된 모든 원본 파일(영상, 썸네일 이미지 등)의 물리적인 정보를 관리한다.
    """
    file_id = models.BigAutoField(primary_key=True, db_column='FILE_ID')
    file_path = models.FileField(upload_to='videos/%Y/%m/%d/',max_length=500, db_column='FILE_PATH')

    class Meta:
        db_table = 'FILE_INFO'
        verbose_name = '파일 정보'
        verbose_name_plural = '파일 정보 목록'

    def __str__(self):
        return os.path.basename(self.file_path.name)


class UserUploadVideo(models.Model):
    """
    4) 유저 업로드 영상
    회원이 직접 업로드한 원본 영상의 메타데이터를 저장한다.
    Note: UPLOAD_FILE_ID가 PK이자 FK이므로 OneToOneField 사용
    """
    upload_file = models.OneToOneField(FileInfo, on_delete=models.CASCADE, primary_key=True, db_column='UPLOAD_FILE_ID')
    user = models.ForeignKey(UserInfo, on_delete=models.CASCADE, db_column='USER_ID')
    upload_status_code = models.ForeignKey(CommonCode, on_delete=models.SET_NULL, null=True, db_column='UPLOAD_STATUS_CODE')
    upload_title = models.CharField(max_length=100, db_column='UPLOAD_TITLE')
    download_count = models.IntegerField(default=0, db_column='DOWNLOAD_COUNT')
    upload_date = models.DateField(db_column='UPLOAD_DATE')
    use_yn = models.BooleanField(default=True, db_column='USE_YN')

    class Meta:
        db_table = 'USER_UPLOAD_VIDEO'
        verbose_name = '유저 업로드 영상'
        verbose_name_plural = '유저 업로드 영상 목록'


class HighlightVideo(models.Model):
    """
    5) 하이라이트 영상
    원본 영상으로부터 생성된 하이라이트 영상의 정보를 관리한다.
    Note: VIDEO_FILE_ID가 PK이자 FK이므로 OneToOneField 사용
    """
    video_file = models.OneToOneField(FileInfo, on_delete=models.CASCADE, primary_key=True, db_column='VIDEO_FILE_ID')
    highlight_title = models.CharField(max_length=100, db_column='HIGHLIGHT_TITLE')
    match_date = models.DateField(db_column='MATCH_DATE')
    video_category = models.ForeignKey(CommonCode, on_delete=models.SET_NULL, null=True, db_column='VIDEO_CATEGORY')

    class Meta:
        db_table = 'HIGHLIGHT_VIDEO'
        verbose_name = '하이라이트 영상'
        verbose_name_plural = '하이라이트 영상 목록'


class SubtitleInfo(models.Model):
    """
    6) 자막 정보
    유저 업로드 영상 및 하이라이트 영상의 자막 데이터를 저장한다.
    """
    subtitle_id = models.BigAutoField(primary_key=True, db_column='SUBTITLE_ID')
    upload_file = models.ForeignKey(UserUploadVideo, on_delete=models.CASCADE, null=True, blank=True, db_column='UPLOAD_FILE_ID')
    video_file = models.ForeignKey(HighlightVideo, on_delete=models.CASCADE, null=True, blank=True, db_column='VIDEO_FILE_ID')
    commentator_code = models.ForeignKey(CommonCode, on_delete=models.SET_NULL, null=True, db_column='COMMENTATOR_CODE')
    subtitle = models.BinaryField(db_column='SUBTITLE')

    class Meta:
        db_table = 'SUBTITLE_INFO'
        verbose_name = '자막 정보'
        verbose_name_plural = '자막 정보 목록'