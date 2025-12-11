from django.db import models

class CommonCode(models.Model):
    """
    2) 공통 코드
    애플리케이션 전체에서 공통으로 사용되는 분류 코드 값을 관리한다.
    """
    common_code = models.BigAutoField(primary_key=True, db_column='COMMON_CODE')
    common_code_grp = models.CharField(max_length=100, db_column='COMMON_CODE_GRP')
    common_code_value = models.CharField(max_length=100, db_column='COMMON_CODE_VALUE')

    class Meta:
        db_table = 'COMMON_CODE'
        verbose_name = '공통 코드'
        verbose_name_plural = '공통 코드 목록'

    def __str__(self):
        return f"{self.common_code_grp} - {self.common_code_value}"


class UserInfo(models.Model):
    """
    1) 회원 정보
    서비스에 가입한 회원의 계정 정보를 관리한다.
    """
    user_id = models.CharField(max_length=40, primary_key=True, db_column='USER_ID', help_text="이메일로 UUID 생성")
    favorite_code = models.ForeignKey(CommonCode, on_delete=models.SET_NULL, null=True, blank=True, db_column='FAVORITE_CODE', related_name='users_favorite')
    email = models.CharField(max_length=254, db_column='EMAIL')
    password = models.CharField(max_length=64, db_column='PASSWORD', help_text="영소문자와 숫자 포함 10~16자, 암호화")
    storage_usage = models.IntegerField(default=0, db_column='STORAGE_USAGE', help_text="단위: KB")
    free_use_yn = models.BooleanField(default=False, db_column='FREE_USE_YN')

    class Meta:
        db_table = 'USER_INFO'
        verbose_name = '회원 정보'
        verbose_name_plural = '회원 정보 목록'

    def __str__(self):
        return self.user_id