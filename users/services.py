import hashlib
import uuid
import random
import string
import re
from datetime import timedelta
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from django.db.models import Q
from django.core.cache import cache
from .models import UserInfo, CommonCode
from payments.models import SubscribeHistory, PaymentHistory

TEAM_META_DATA = {
    'LG': {'full': 'LG 트윈스', 'mascot': '수타'},
    'HANWHA': {'full': '한화 이글스', 'mascot': '술이'},
    'SSG': {'full': 'SSG 랜더스', 'mascot': '란디'},
    'SAMSUNG': {'full': '삼성 라이온즈', 'mascot': '볼래요'},
    'NC': {'full': 'NC 다이노스', 'mascot': '반비'},
    'KT': {'full': 'KT 위즈', 'mascot': '똘이'},
    'LOTTE': {'full': '롯데 자이언츠', 'mascot': '눌이'},
    'KIA': {'full': 'KIA 타이거즈', 'mascot': '호거리'},
    'DOOSAN': {'full': '두산 베어스', 'mascot': '철'},
    'KIWOOM': {'full': '키움 히어로즈', 'mascot': '턱도리'},
}


def generate_code(length: int = 6) -> str:
    characters = string.ascii_letters + string.digits
    return ''.join(random.choices(characters, k=length))


def send_code_email_logic(email: str) -> str:
    """인증번호 생성 및 이메일 발송 로직"""
    if UserInfo.objects.filter(email=email).exists():
        raise ValueError("DUPLICATE")

    code = generate_code()
    subject = "[BAIS] 이메일 인증번호 안내"
    message = (
        f"안녕하세요.\n\n"
        f"요청하신 인증번호는 {code} 입니다.\n"
        f"유효시간: 5분\n\n"
        f"본인이 요청하지 않았다면 이 메일을 무시하셔도 됩니다."
    )
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email], fail_silently=False)
    return code


def verify_code_logic(input_code, session_code):
    """인증번호 검증 로직"""
    if not session_code:
        raise TimeoutError("인증 시간이 만료되었습니다.")
    if input_code != session_code:
        raise ValueError("인증번호가 일치하지 않습니다.")
    return True


def validate_password_logic(password):
    """비밀번호 유효성 검사 및 해싱"""
    password_regex = r'^(?=.*[a-z])(?=.*\d).{10,16}$'
    if not re.match(password_regex, password):
        raise ValueError("비밀번호 양식이 올바르지 않습니다.")
    
    return hashlib.sha256(password.encode('utf-8')).hexdigest()


def create_user_logic(email, hashed_password, team_str):
    """회원가입 완료(DB생성) 로직"""
    team_mapping = {
        'LG': 1, 'HANHWA': 2, 'SSG': 3, 'SAMSUNG': 4, 'NC': 5,
        'KT': 6, 'LOTTE': 7, 'KIA': 8, 'DOOSAN': 9, 'KIWOOM': 10
    }
    
    fav_team_code = team_mapping.get(team_str)
    if not fav_team_code:
        raise ValueError("잘못된 구단 정보입니다.")

    try:
        favorite_team_instance = CommonCode.objects.get(pk=fav_team_code)
    except CommonCode.DoesNotExist:
        raise ValueError("존재하지 않는 구단 코드입니다.")

    user_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, email)
    new_user = UserInfo(
        user_id=str(user_uuid),
        favorite_code=favorite_team_instance,
        email=email,
        password=hashed_password,
    )
    new_user.save()


def login_user_logic(email, password):
    """로그인 검증 로직"""
    lock_key = f"login_lock_{email}"
    if cache.get(lock_key):
        raise PermissionError("LOCKED")

    try:
        user = UserInfo.objects.get(email=email)
    except UserInfo.DoesNotExist:
        raise ValueError("존재하지 않는 이메일입니다.")

    input_hashed = hashlib.sha256(password.encode('utf-8')).hexdigest()

    if user.password == input_hashed:
        cache.delete(f"login_fail_{email}")
        return user.user_id
    else:
        fail_key = f"login_fail_{email}"
        current_fail = cache.get(fail_key, 0) + 1
        cache.set(fail_key, current_fail, timeout=600)

        if current_fail >= 5:
            cache.set(lock_key, 'LOCKED', timeout=600)
            cache.delete(fail_key)
            raise PermissionError("LOCKED_5")
        
        raise ValueError("FAIL")


def send_reset_code_logic(email):
    """비밀번호 재설정 코드 발송"""
    if not UserInfo.objects.filter(email=email).exists():
        raise ValueError("존재하지 않는 이메일입니다.")

    code = generate_code()
    subject = "[BAIS] 비밀번호 재설정 인증번호"
    message = f"인증번호: {code}\n유효시간: 5분"
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email], fail_silently=False)
    return code


def reset_password_logic(email, new_password):
    """비밀번호 재설정 로직"""
    hashed_new = validate_password_logic(new_password)
    
    try:
        user = UserInfo.objects.get(email=email)
        if user.password == hashed_new:
            raise ValueError("기존에 사용하던 비밀번호입니다.")
        
        user.password = hashed_new
        user.save()
    except UserInfo.DoesNotExist:
        raise ValueError("사용자를 찾을 수 없습니다.")


def get_setting_context(user_id):
    """설정 페이지 데이터 조회 로직"""
    user = UserInfo.objects.get(user_id=user_id)
    
    # 1. 팀 정보
    team_full_name = "KBO 리그"
    team_mascot = "마스코트"
    if user.favorite_code and user.favorite_code.common_code_value in TEAM_META_DATA:
        meta = TEAM_META_DATA[user.favorite_code.common_code_value]
        team_full_name = meta['full']
        team_mascot = meta['mascot']

    # 2. 구독 정보
    now = timezone.now()
    current_sub = SubscribeHistory.objects.filter(
        user=user, 
        subscribe_start_dt__lte=now
    ).filter(
        Q(subscribe_end_dt__gte=now) | Q(subscribe_end_dt__isnull=True)
    ).order_by('-subscribe_start_dt').first()

    future_sub = SubscribeHistory.objects.filter(
        user=user, subscribe_start_dt__gt=now 
    ).order_by('subscribe_start_dt').first()

    target_sub = future_sub if future_sub else current_sub

    # 기본 컨텍스트 구조
    sub_context = {
        'has_sub': False, 'is_canceled': False, 'plan_code': 'FREE', 'plan_name': '',
        'next_pay_date': '', 'expire_date': '', 'has_reserved': False,
        'reserved_plan': '', 'reserved_start_date': '', 'reserved_next_pay': '', 'modal_expire_date': ''
    }

    if current_sub:
        sub_context['has_sub'] = True
        p_name = current_sub.plan.plan_name.upper()
        if 'PREMIUM' in p_name:
            sub_context['plan_code'] = 'PREMIUM'
            sub_context['plan_name'] = '프리미엄 플랜'
        elif 'BASIC' in p_name:
            sub_context['plan_code'] = 'BASIC'
            sub_context['plan_name'] = '베이직 플랜'
        
        last_pay = PaymentHistory.objects.filter(invoice__subscription=current_sub).order_by('-payment_date').first()
        base_date = last_pay.payment_date if last_pay else current_sub.subscribe_start_dt
        current_cycle_end = base_date + timedelta(days=30)
        sub_context['expire_date'] = (current_cycle_end - timedelta(days=1)).strftime('%Y.%m.%d')

        if future_sub:
            sub_context['has_reserved'] = True
            f_plan = "프리미엄" if "PREMIUM" in future_sub.plan.plan_name.upper() else "베이직"
            sub_context['reserved_plan'] = f"{f_plan} 플랜"
            sub_context['reserved_start_date'] = future_sub.subscribe_start_dt.strftime('%Y.%m.%d')
            sub_context['reserved_next_pay'] = (future_sub.subscribe_start_dt + timedelta(days=30)).strftime('%Y.%m.%d')

        if target_sub:
            if target_sub.subscribe_end_dt:
                sub_context['is_canceled'] = True
                sub_context['modal_expire_date'] = target_sub.subscribe_end_dt.strftime('%Y.%m.%d')
            else:
                expected_end = target_sub.subscribe_start_dt + timedelta(days=30) if target_sub == future_sub else current_cycle_end
                sub_context['modal_expire_date'] = (expected_end - timedelta(days=1)).strftime('%Y.%m.%d')
        
        if not sub_context['is_canceled'] and not sub_context['has_reserved']:
            sub_context['next_pay_date'] = current_cycle_end.strftime('%Y.%m.%d')

    # 3. 결제 내역
    raw_payments = PaymentHistory.objects.filter(invoice__subscription__user=user).order_by('-payment_date')[:5]
    payment_list = []
    for pay in raw_payments:
        pay.amount_str = f"{int(pay.payment_amount):,}"
        payment_list.append(pay)

    return {
        'user': user,
        'team_full_name': team_full_name,
        'team_mascot': team_mascot,
        'sub_info': sub_context,
        'payment_list': payment_list
    }


def update_team_logic(user_id, new_team_code):
    """구단 변경 로직"""
    try:
        code_instance = CommonCode.objects.get(common_code_value=new_team_code)
    except CommonCode.DoesNotExist:
        raise ValueError("존재하지 않는 구단 코드입니다.")

    user = UserInfo.objects.get(user_id=user_id)
    user.favorite_code_id = code_instance
    user.save()


def update_password_logic(user_id, current_pw, new_pw, confirm_pw):
    """비밀번호 변경 로직"""
    if new_pw != confirm_pw:
        raise ValueError("새 비밀번호가 일치하지 않습니다.")

    hashed_new = validate_password_logic(new_pw)
    user = UserInfo.objects.get(user_id=user_id)
    
    hashed_current = hashlib.sha256(current_pw.encode('utf-8')).hexdigest()
    if user.password != hashed_current:
        raise ValueError("기존 비밀번호가 일치하지 않습니다.")
    
    if user.password == hashed_new:
        raise ValueError("기존 비밀번호와 다르게 설정해주세요.")

    user.password = hashed_new
    user.save()


def delete_account_logic(user_id, password):
    """회원 탈퇴 로직"""
    user = UserInfo.objects.get(user_id=user_id)
    input_hashed = hashlib.sha256(password.encode('utf-8')).hexdigest()
    
    if user.password != input_hashed:
        raise ValueError("비밀번호가 올바르지 않습니다.")
    
    user.delete()