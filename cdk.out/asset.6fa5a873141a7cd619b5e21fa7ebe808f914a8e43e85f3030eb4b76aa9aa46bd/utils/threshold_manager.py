"""
Dynamic Threshold Manager
Quản lý ngưỡng similarity động từ Parameter Store/Secrets Manager (báo cáo 4.3)
"""

import os
import json
import boto3
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from functools import lru_cache

# AWS clients
ssm = boto3.client('ssm')
secrets_manager = boto3.client('secretsmanager')
cloudwatch = boto3.client('cloudwatch')

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Cache TTL
CACHE_TTL_SECONDS = 300  # 5 minutes

class ThresholdManager:
    """
    Quản lý ngưỡng similarity động theo use case
    - Attendance (điểm danh): >=90%
    - Access Control (kiểm soát truy cập): >=95%
    - Financial Transaction (giao dịch tài chính): >=98%
    """
    
    def __init__(self):
        self.parameter_prefix = os.environ.get(
            'PARAMETER_STORE_PREFIX',
            '/face-recognition/thresholds'
        )
        self.cache = {}
        self.cache_timestamps = {}
    
    def get_threshold(self, use_case: str) -> float:
        """
        Lấy threshold từ Parameter Store với caching
        
        Args:
            use_case: 'attendance', 'access_control', 'financial', 'default'
        
        Returns:
            Similarity threshold (0.0-1.0)
        """
        
        # Check cache
        if self._is_cache_valid(use_case):
            logger.info(f"Using cached threshold for {use_case}")
            return self.cache[use_case]
        
        # Fetch from Parameter Store
        parameter_name = f"{self.parameter_prefix}/{use_case}"
        
        try:
            response = ssm.get_parameter(
                Name=parameter_name,
                WithDecryption=True
            )
            
            threshold = float(response['Parameter']['Value'])
            
            # Validate range
            if not (0.0 <= threshold <= 1.0):
                logger.warning(f"Invalid threshold {threshold}, using default")
                threshold = self._get_default_threshold(use_case)
            
            # Update cache
            self.cache[use_case] = threshold
            self.cache_timestamps[use_case] = datetime.utcnow()
            
            logger.info(f"Loaded threshold for {use_case}: {threshold}")
            return threshold
            
        except ssm.exceptions.ParameterNotFound:
            logger.warning(f"Parameter {parameter_name} not found, using default")
            threshold = self._get_default_threshold(use_case)
            
            # Create parameter with default value
            try:
                ssm.put_parameter(
                    Name=parameter_name,
                    Value=str(threshold),
                    Type='String',
                    Description=f'Similarity threshold for {use_case}',
                    Overwrite=False
                )
                logger.info(f"Created default parameter for {use_case}")
            except Exception as e:
                logger.error(f"Failed to create parameter: {str(e)}")
            
            return threshold
            
        except Exception as e:
            logger.error(f"Error fetching threshold: {str(e)}")
            return self._get_default_threshold(use_case)
    
    def update_threshold(self, use_case: str, new_threshold: float) -> bool:
        """
        Cập nhật threshold trong Parameter Store
        
        Args:
            use_case: Use case name
            new_threshold: New threshold value (0.0-1.0)
        
        Returns:
            Success status
        """
        
        # Validate
        if not (0.0 <= new_threshold <= 1.0):
            logger.error(f"Invalid threshold: {new_threshold}")
            return False
        
        parameter_name = f"{self.parameter_prefix}/{use_case}"
        
        try:
            ssm.put_parameter(
                Name=parameter_name,
                Value=str(new_threshold),
                Type='String',
                Overwrite=True
            )
            
            # Invalidate cache
            if use_case in self.cache:
                del self.cache[use_case]
                del self.cache_timestamps[use_case]
            
            # Log metric
            cloudwatch.put_metric_data(
                Namespace='FaceRecognition/Thresholds',
                MetricData=[{
                    'MetricName': 'ThresholdUpdate',
                    'Value': new_threshold,
                    'Unit': 'None',
                    'Dimensions': [{'Name': 'UseCase', 'Value': use_case}]
                }]
            )
            
            logger.info(f"Updated threshold for {use_case}: {new_threshold}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update threshold: {str(e)}")
            return False
    
    def get_all_thresholds(self) -> Dict[str, float]:
        """Lấy tất cả thresholds hiện tại"""
        
        use_cases = ['attendance', 'access_control', 'financial', 'default']
        thresholds = {}
        
        for use_case in use_cases:
            thresholds[use_case] = self.get_threshold(use_case)
        
        return thresholds
    
    def _is_cache_valid(self, use_case: str) -> bool:
        """Kiểm tra cache còn valid không"""
        
        if use_case not in self.cache:
            return False
        
        cache_time = self.cache_timestamps.get(use_case)
        if not cache_time:
            return False
        
        age = (datetime.utcnow() - cache_time).total_seconds()
        return age < CACHE_TTL_SECONDS
    
    def _get_default_threshold(self, use_case: str) -> float:
        """
        Default thresholds theo báo cáo
        - attendance: 0.90 (90%)
        - access_control: 0.95 (95%)
        - financial: 0.98 (98%)
        - default: 0.90
        """
        
        defaults = {
            'attendance': 0.90,
            'access_control': 0.95,
            'financial': 0.98,
            'default': 0.90
        }
        
        return defaults.get(use_case, 0.90)


# Global instance
threshold_manager = ThresholdManager()


def lambda_handler(event, context):
    """
    Lambda handler cho threshold management
    
    Operations:
    - GET: Lấy threshold
    - POST: Cập nhật threshold
    - LIST: Lấy tất cả thresholds
    """
    
    try:
        operation = event.get('operation', 'GET')
        use_case = event.get('use_case', 'default')
        
        if operation == 'GET':
            threshold = threshold_manager.get_threshold(use_case)
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'use_case': use_case,
                    'threshold': threshold
                })
            }
        
        elif operation == 'POST':
            new_threshold = event.get('threshold')
            if new_threshold is None:
                return {
                    'statusCode': 400,
                    'body': json.dumps({'error': 'threshold is required'})
                }
            
            success = threshold_manager.update_threshold(use_case, float(new_threshold))
            
            return {
                'statusCode': 200 if success else 500,
                'body': json.dumps({
                    'success': success,
                    'use_case': use_case,
                    'threshold': new_threshold
                })
            }
        
        elif operation == 'LIST':
            thresholds = threshold_manager.get_all_thresholds()
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'thresholds': thresholds
                })
            }
        
        else:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': f'Unknown operation: {operation}'})
            }
    
    except Exception as e:
        logger.error(f"Handler error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


def get_threshold_for_identification(confidence: float, context: str = 'default') -> bool:
    """
    Helper function để sử dụng trong identification service
    
    Args:
        confidence: Rekognition similarity score (0-100)
        context: Use case context
    
    Returns:
        True if confidence meets threshold
    """
    
    threshold = threshold_manager.get_threshold(context)
    normalized_confidence = confidence / 100.0
    
    result = normalized_confidence >= threshold
    
    # Log metric
    try:
        cloudwatch.put_metric_data(
            Namespace='FaceRecognition/Matching',
            MetricData=[
                {
                    'MetricName': 'ConfidenceScore',
                    'Value': normalized_confidence,
                    'Unit': 'None',
                    'Dimensions': [
                        {'Name': 'UseCase', 'Value': context},
                        {'Name': 'Result', 'Value': 'Pass' if result else 'Fail'}
                    ]
                }
            ]
        )
    except Exception as e:
        logger.error(f"Failed to log metric: {str(e)}")
    
    return result
