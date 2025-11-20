"""Step Functions Workflow for Face Recognition Pipeline.

Implements the workflow described in the report:
1. Validate input
2. Detect faces
3. Extract embeddings
4. Match against database
5. Log results

This provides orchestration for complex, multi-step processing.
"""

import json
from typing import Dict, Any


def create_identification_workflow_definition() -> Dict[str, Any]:
    """Create Step Functions workflow for face identification.

    Returns:
        Workflow definition in ASL (Amazon States Language)
    """
    return {
        "Comment": "Face Recognition Identification Pipeline",
        "StartAt": "ValidateInput",
        "States": {
            "ValidateInput": {
                "Type": "Task",
                "Resource": "arn:aws:states:::lambda:invoke",
                "Parameters": {
                    "FunctionName": "${ValidateLambdaArn}",
                    "Payload": {
                        "input.$": "$"
                    }
                },
                "ResultPath": "$.validation",
                "Next": "CheckValidation",
                "Catch": [
                    {
                        "ErrorEquals": ["States.ALL"],
                        "ResultPath": "$.error",
                        "Next": "ValidationFailed"
                    }
                ]
            },
            "CheckValidation": {
                "Type": "Choice",
                "Choices": [
                    {
                        "Variable": "$.validation.Payload.valid",
                        "BooleanEquals": True,
                        "Next": "DetectFaces"
                    }
                ],
                "Default": "ValidationFailed"
            },
            "DetectFaces": {
                "Type": "Task",
                "Resource": "arn:aws:states:::lambda:invoke",
                "Parameters": {
                    "FunctionName": "${DetectLambdaArn}",
                    "Payload": {
                        "image.$": "$.image",
                        "validation.$": "$.validation.Payload"
                    }
                },
                "ResultPath": "$.detection",
                "Next": "CheckDetection",
                "Retry": [
                    {
                        "ErrorEquals": ["States.TaskFailed"],
                        "IntervalSeconds": 2,
                        "MaxAttempts": 3,
                        "BackoffRate": 2.0
                    }
                ],
                "Catch": [
                    {
                        "ErrorEquals": ["States.ALL"],
                        "ResultPath": "$.error",
                        "Next": "DetectionFailed"
                    }
                ]
            },
            "CheckDetection": {
                "Type": "Choice",
                "Choices": [
                    {
                        "Variable": "$.detection.Payload.faces_detected",
                        "NumericGreaterThan": 0,
                        "Next": "SearchFaces"
                    }
                ],
                "Default": "NoFacesDetected"
            },
            "SearchFaces": {
                "Type": "Task",
                "Resource": "arn:aws:states:::lambda:invoke",
                "Parameters": {
                    "FunctionName": "${SearchLambdaArn}",
                    "Payload": {
                        "image.$": "$.image",
                        "detection.$": "$.detection.Payload",
                        "threshold.$": "$.threshold"
                    }
                },
                "ResultPath": "$.search",
                "Next": "CheckMatches",
                "Retry": [
                    {
                        "ErrorEquals": ["States.TaskFailed"],
                        "IntervalSeconds": 2,
                        "MaxAttempts": 3,
                        "BackoffRate": 2.0
                    }
                ],
                "Catch": [
                    {
                        "ErrorEquals": ["States.ALL"],
                        "ResultPath": "$.error",
                        "Next": "SearchFailed"
                    }
                ]
            },
            "CheckMatches": {
                "Type": "Choice",
                "Choices": [
                    {
                        "Variable": "$.search.Payload.matches",
                        "IsPresent": True,
                        "Next": "GetUserMetadata"
                    }
                ],
                "Default": "NoMatchesFound"
            },
            "GetUserMetadata": {
                "Type": "Task",
                "Resource": "arn:aws:states:::lambda:invoke",
                "Parameters": {
                    "FunctionName": "${MetadataLambdaArn}",
                    "Payload": {
                        "matches.$": "$.search.Payload.matches"
                    }
                },
                "ResultPath": "$.metadata",
                "Next": "LogAccessEvent",
                "Catch": [
                    {
                        "ErrorEquals": ["States.ALL"],
                        "ResultPath": "$.error",
                        "Next": "LogAccessEvent"
                    }
                ]
            },
            "LogAccessEvent": {
                "Type": "Task",
                "Resource": "arn:aws:states:::lambda:invoke",
                "Parameters": {
                    "FunctionName": "${LogLambdaArn}",
                    "Payload": {
                        "event_type": "identification",
                        "detection.$": "$.detection.Payload",
                        "search.$": "$.search.Payload",
                        "metadata.$": "$.metadata.Payload",
                        "timestamp.$": "$$.State.EnteredTime"
                    }
                },
                "ResultPath": "$.log",
                "Next": "IdentificationSuccess"
            },
            "IdentificationSuccess": {
                "Type": "Pass",
                "Parameters": {
                    "success": True,
                    "message": "Identification completed successfully",
                    "result.$": "$"
                },
                "End": True
            },
            "ValidationFailed": {
                "Type": "Pass",
                "Parameters": {
                    "success": False,
                    "error": "validation_failed",
                    "message": "Input validation failed",
                    "details.$": "$.validation"
                },
                "End": True
            },
            "DetectionFailed": {
                "Type": "Pass",
                "Parameters": {
                    "success": False,
                    "error": "detection_failed",
                    "message": "Face detection failed",
                    "details.$": "$.error"
                },
                "End": True
            },
            "NoFacesDetected": {
                "Type": "Pass",
                "Parameters": {
                    "success": False,
                    "error": "no_faces",
                    "message": "No faces detected in image",
                    "detection.$": "$.detection.Payload"
                },
                "End": True
            },
            "SearchFailed": {
                "Type": "Pass",
                "Parameters": {
                    "success": False,
                    "error": "search_failed",
                    "message": "Face search failed",
                    "details.$": "$.error"
                },
                "End": True
            },
            "NoMatchesFound": {
                "Type": "Pass",
                "Parameters": {
                    "success": True,
                    "message": "No matching faces found",
                    "search.$": "$.search.Payload"
                },
                "End": True
            }
        }
    }


def create_enrollment_workflow_definition() -> Dict[str, Any]:
    """Create Step Functions workflow for face enrollment.

    Returns:
        Workflow definition in ASL
    """
    return {
        "Comment": "Face Recognition Enrollment Pipeline",
        "StartAt": "ValidateEnrollmentInput",
        "States": {
            "ValidateEnrollmentInput": {
                "Type": "Task",
                "Resource": "arn:aws:states:::lambda:invoke",
                "Parameters": {
                    "FunctionName": "${ValidateLambdaArn}",
                    "Payload": {
                        "input.$": "$",
                        "mode": "enrollment"
                    }
                },
                "ResultPath": "$.validation",
                "Next": "CheckDuplicates",
                "Catch": [
                    {
                        "ErrorEquals": ["States.ALL"],
                        "ResultPath": "$.error",
                        "Next": "EnrollmentFailed"
                    }
                ]
            },
            "CheckDuplicates": {
                "Type": "Task",
                "Resource": "arn:aws:states:::lambda:invoke",
                "Parameters": {
                    "FunctionName": "${DuplicateCheckLambdaArn}",
                    "Payload": {
                        "image.$": "$.image",
                        "threshold": 95.0
                    }
                },
                "ResultPath": "$.duplicate_check",
                "Next": "EvaluateDuplicates",
                "Catch": [
                    {
                        "ErrorEquals": ["States.ALL"],
                        "ResultPath": "$.error",
                        "Next": "UploadToS3"
                    }
                ]
            },
            "EvaluateDuplicates": {
                "Type": "Choice",
                "Choices": [
                    {
                        "Variable": "$.duplicate_check.Payload.duplicate_found",
                        "BooleanEquals": True,
                        "Next": "DuplicateFound"
                    }
                ],
                "Default": "UploadToS3"
            },
            "UploadToS3": {
                "Type": "Task",
                "Resource": "arn:aws:states:::lambda:invoke",
                "Parameters": {
                    "FunctionName": "${UploadLambdaArn}",
                    "Payload": {
                        "image.$": "$.image",
                        "user_id.$": "$.user_id"
                    }
                },
                "ResultPath": "$.upload",
                "Next": "IndexFace",
                "Retry": [
                    {
                        "ErrorEquals": ["States.TaskFailed"],
                        "IntervalSeconds": 2,
                        "MaxAttempts": 3,
                        "BackoffRate": 2.0
                    }
                ]
            },
            "IndexFace": {
                "Type": "Task",
                "Resource": "arn:aws:states:::lambda:invoke",
                "Parameters": {
                    "FunctionName": "${IndexLambdaArn}",
                    "Payload": {
                        "s3_path.$": "$.upload.Payload.s3_path",
                        "user_id.$": "$.user_id"
                    }
                },
                "ResultPath": "$.index",
                "Next": "SaveMetadata",
                "Retry": [
                    {
                        "ErrorEquals": ["States.TaskFailed"],
                        "IntervalSeconds": 2,
                        "MaxAttempts": 3,
                        "BackoffRate": 2.0
                    }
                ]
            },
            "SaveMetadata": {
                "Type": "Task",
                "Resource": "arn:aws:states:::lambda:invoke",
                "Parameters": {
                    "FunctionName": "${MetadataLambdaArn}",
                    "Payload": {
                        "user_id.$": "$.user_id",
                        "face_id.$": "$.index.Payload.face_id",
                        "s3_path.$": "$.upload.Payload.s3_path",
                        "quality.$": "$.validation.Payload.quality"
                    }
                },
                "ResultPath": "$.metadata",
                "Next": "EnrollmentSuccess"
            },
            "EnrollmentSuccess": {
                "Type": "Pass",
                "Parameters": {
                    "success": True,
                    "message": "Enrollment completed successfully",
                    "result.$": "$"
                },
                "End": True
            },
            "DuplicateFound": {
                "Type": "Pass",
                "Parameters": {
                    "success": False,
                    "error": "duplicate_found",
                    "message": "Duplicate face detected",
                    "duplicate.$": "$.duplicate_check.Payload"
                },
                "End": True
            },
            "EnrollmentFailed": {
                "Type": "Pass",
                "Parameters": {
                    "success": False,
                    "error": "enrollment_failed",
                    "message": "Enrollment process failed",
                    "details.$": "$.error"
                },
                "End": True
            }
        }
    }
