from django.db import models
from users.models import UserInfo

class PlanInfo(models.Model):
    """
    8) 플랜 정보
    서비스가 제공하는 다양한 구독 플랜의 상세 정보를 정의한다.
    """
    plan_id = models.BigAutoField(primary_key=True, db_column='PLAN_ID')
    plan_name = models.CharField(max_length=30, db_column='PLAN_NAME')
    price = models.BigIntegerField(db_column='PRICE')
    storage_limit = models.IntegerField(db_column='STORAGE_LIMIT', help_text="단위: KB")

    class Meta:
        db_table = 'PLAN_INFO'
        verbose_name = '플랜 정보'
        verbose_name_plural = '플랜 정보 목록'


class SubscribeHistory(models.Model):
    """
    7) 구독 이력
    회원이 특정 플랜을 구독한 모든 이력을 기록한다.
    """
    subscription_id = models.BigAutoField(primary_key=True, db_column='SUBSCRIPTION_ID')
    user = models.ForeignKey(UserInfo, on_delete=models.CASCADE, db_column='USER_ID')
    plan = models.ForeignKey(PlanInfo, on_delete=models.CASCADE, db_column='PLAN_ID')
    subscribe_start_dt = models.DateTimeField(db_column='SUBSCRIBE_START_DT')
    subscribe_end_dt = models.DateTimeField(null=True, blank=True, db_column='SUBSCRIBE_END_DT')

    class Meta:
        db_table = 'SUBSCRIBE_HISTORY'
        verbose_name = '구독 이력'
        verbose_name_plural = '구독 이력 목록'


class InvoiceInfo(models.Model):
    """
    9) 청구 정보
    구독 갱신 등 결제가 필요할 때마다 생성되는 청구 정보를 관리한다.
    """
    invoice_id = models.BigAutoField(primary_key=True, db_column='INVOICE_ID')
    subscription = models.ForeignKey(SubscribeHistory, on_delete=models.CASCADE, db_column='SUBSCRIPTION_ID')
    invoice_amount = models.BigIntegerField(db_column='INVOICE_AMOUNT')
    issue_date = models.DateField(db_column='ISSUE_DATE')

    class Meta:
        db_table = 'INVOICE_INFO'
        verbose_name = '청구 정보'
        verbose_name_plural = '청구 정보 목록'


class PaymentHistory(models.Model):
    """
    10) 결제 이력
    생성된 청구 정보에 대해 실제 결제를 시도한 모든 이력을 저장한다.
    """
    payment_id = models.BigAutoField(primary_key=True, db_column='PAYMENT_ID')
    invoice = models.ForeignKey(InvoiceInfo, on_delete=models.CASCADE, db_column='INVOICE_ID')
    transaction_id = models.CharField(max_length=100, db_column='TRANSACTION_ID')
    payment_amount = models.BigIntegerField(db_column='PAYMENT_AMOUNT')
    fail_reason = models.CharField(max_length=255, null=True, blank=True, db_column='FAIL_REASON')
    payment_date = models.DateTimeField(db_column='PAYMENT_DATE')

    class Meta:
        db_table = 'PAYMENT_HISTORY'
        verbose_name = '결제 이력'
        verbose_name_plural = '결제 이력 목록'