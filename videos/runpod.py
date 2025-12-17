import boto3
import requests
import time
import json
import logging
import os
import tempfile
import sys
from botocore.config import Config
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from urllib.parse import urlparse
from django.conf import settings
from users.models import CommonCode
from .models import SubtitleInfo

logger = logging.getLogger(__name__)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
formatter = logging.Formatter('[%(asctime)s] %(levelname)s [%(name)s] %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

class RunPodClient:
    def __init__(self):
        s3_config = Config(
            connect_timeout=120,    
            read_timeout=120,       
            retries={
                'max_attempts': 10,
                'mode': 'adaptive' 
            },
            signature_version='s3v4'
        )
        self.s3_client = boto3.client(
            's3',
            region_name=settings.AWS_S3_REGION_NAME,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            config=s3_config
        )
        self.bucket_name = settings.AWS_STORAGE_BUCKET_NAME
        self.runpod_url = settings.RUNPOD_API_URL
        self.session = self._create_resilient_session()
        self.ANALYST_MAPPING = {
            17: 3,
            18: 2,
            19: 1
        }

    def _create_resilient_session(self):
        session = requests.Session()
        retry = Retry(total=10, backoff_factor=2, status_forcelist=[429, 500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def _get_common_code(self, code_val, group_name):
        try:
            return CommonCode.objects.get(common_code=code_val, common_code_grp=group_name)
        except CommonCode.DoesNotExist:
            return None
        
    def _update_status(self, user_upload_instance, code_val):
        code_obj = self._get_common_code(code_val, 'STATUS')
        if code_obj:
            user_upload_instance.upload_status_code = code_obj
            user_upload_instance.save()
            logger.info(f"💾 DB 상태 업데이트: {code_val} (ID: {user_upload_instance.pk})")

    def upload_video_to_s3(self, django_file_field):
        try:
            filename = os.path.basename(django_file_field.name)
        except Exception:
            filename = f"video_{int(time.time())}.mp4"
            
        s3_key = f"inputs/{filename}"
        
        logger.info(f"📤 S3 업로드 시작 (Key: {s3_key})...")

        with tempfile.NamedTemporaryFile(delete=True) as tmp:
            for chunk in django_file_field.chunks():
                tmp.write(chunk)
            tmp.flush()
            tmp.seek(0)
            
            self.s3_client.upload_file(
                tmp.name,
                self.bucket_name,
                s3_key,
                ExtraArgs={'ContentType': 'video/mp4'}
            )
            
        logger.info(f"✅ S3 업로드 완료: s3://{self.bucket_name}/{s3_key}")
        return s3_key

    def generate_public_urls(self, input_s3_key):
        download_url = self.s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': self.bucket_name, 'Key': input_s3_key},
            ExpiresIn=3600
        )
        
        timestamp = int(time.time())
        output_key = f"outputs/result_{timestamp}.mp4"
        output_script_key = f"outputs/script_{timestamp}.json"
        
        upload_url = self.s3_client.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': self.bucket_name, 
                'Key': output_key,
                'ContentType': 'video/mp4'
            },
            ExpiresIn=3600
        )

        script_upload_url = self.s3_client.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': self.bucket_name, 
                'Key': output_script_key,
                'ContentType': 'application/json'
            },
            ExpiresIn=3600
        )
        
        return {
            'download_url': download_url,
            'upload_url': upload_url,
            'script_upload_url': script_upload_url,
            'output_key': output_key
        }

    def submit_job(self, download_url, upload_url, script_upload_url, analyst_id):
        payload = {
            's3_video_url': download_url,
            's3_upload_url': upload_url,
            's3_script_url': script_upload_url,
            'analyst_select': int(analyst_id)
        }
        endpoint = f"{self.runpod_url}/process_video"
        
        logger.info(f"🚀 RunPod 작업 제출 중... (Analyst: {analyst_id})")
        
        response = self.session.post(endpoint, json=payload, timeout=30)
        response.raise_for_status()
        
        job_id = response.json()['job_id']
        logger.info(f"✅ 작업 제출 완료 (Job ID: {job_id})")
        return job_id

    def process_and_monitor(self, user_upload_instance, _, db_analyst_id):
        try:
            self._update_status(user_upload_instance, 21)
            runpod_analyst_id = self.ANALYST_MAPPING.get(db_analyst_id, 1)

            s3_input_key = self.upload_video_to_s3(user_upload_instance.upload_file.file_path)
            urls = self.generate_public_urls(s3_input_key)
            job_id = self.submit_job(urls['download_url'], urls['upload_url'], urls['script_upload_url'], runpod_analyst_id)
            self._monitor_loop(user_upload_instance, job_id, db_analyst_id, urls['output_key'])

        except Exception as e:
            logger.error(f"❌ 프로세스 실패: {e}")
            self._update_status(user_upload_instance, 23)

    def _monitor_loop(self, user_upload_instance, job_id, db_analyst_id, output_s3_key):
        poll_interval = 5
        max_wait_time = 20 * 60 
        start_time = time.time()

        while True:
            elapsed_time = time.time() - start_time
            if elapsed_time > max_wait_time:
                logger.error(f"⏰ 타임아웃 발생! ({max_wait_time}초 초과)")
                self._update_status(user_upload_instance, 23)
                break

            try:
                response = self.session.get(f"{self.runpod_url}/status/{job_id}", timeout=15)
                status_data = response.json()
                raw_status = status_data.get('status', '').upper()
                
                step = status_data.get('step', '')
                if step:
                     progress = status_data.get('progress', 0)
                     logger.info(f"Job Status: {raw_status} | Progress: {progress}% | Step: {step}")

                if raw_status in ['COMPLETED', 'SUCCESS']:
                    logger.info("✅ RunPod 작업 완료! 결과 처리 시작...")
                    
                    try:
                        file_info = user_upload_instance.upload_file
                        file_info.file_path.name = output_s3_key 
                        file_info.save()
                        logger.info(f"💾 영상 경로 연결 완료: {output_s3_key}")
                        
                        output_data = status_data.get('output', {})
                        script_url = output_data.get('script') 

                        if script_url:
                            try:
                                parsed_url = urlparse(script_url)
                                script_s3_key = parsed_url.path.lstrip('/') 

                                logger.info(f"📜 자막 다운로드 시도 (Key: {script_s3_key})")
                                
                                s3_obj = self.s3_client.get_object(Bucket=self.bucket_name, Key=script_s3_key)
                                script_content = s3_obj['Body'].read().decode('utf-8')
                                json.loads(script_content)
                                script_bytes = script_content.encode('utf-8')
                                
                                commentator_code_obj = self._get_common_code(db_analyst_id, 'COMMENTATOR')

                                subtitle_info, created = SubtitleInfo.objects.update_or_create(
                                    upload_file=user_upload_instance,
                                    commentator_code=commentator_code_obj,
                                    defaults={
                                        'subtitle': script_bytes,
                                        'video_file': None
                                    }
                                )
                                logger.info(f"💾 자막 데이터 저장 완료 ({'생성' if created else '수정'})")

                            except Exception as script_error:
                                logger.error(f"❌ 자막 처리 중 오류 발생 (URL: {script_url}): {script_error}")

                        self._update_status(user_upload_instance, 22)
                        
                    except Exception as e:
                        logger.error(f"❌ DB 저장/처리 중 치명적 오류: {e}")
                        self._update_status(user_upload_instance, 23)
                    
                    break 
                
                elif raw_status == 'FAILED':
                    logger.error(f"❌ RunPod 작업 실패: {status_data.get('error')}")
                    self._update_status(user_upload_instance, 23)
                    break
                
                time.sleep(poll_interval)
            
            except Exception as e:
                logger.error(f"⚠️ 모니터링 중 에러 발생: {e}")
                time.sleep(poll_interval)

runpod_client = RunPodClient()