""" Contains all the data models used in inputs/outputs """

from .audio_blob_reference import AudioBlobReference
from .audio_blob_reference_type import AudioBlobReferenceType
from .audio_upload import AudioUpload
from .audio_upload_type import AudioUploadType
from .blob_source import BlobSource
from .detect_language_files_body import DetectLanguageFilesBody
from .error_detail import ErrorDetail
from .error_detail_details import ErrorDetailDetails
from .error_response import ErrorResponse
from .get_available_voices_response_200 import GetAvailableVoicesResponse200
from .get_available_voices_response_200_voices_item import GetAvailableVoicesResponse200VoicesItem
from .get_available_voices_response_200_voices_item_gender import GetAvailableVoicesResponse200VoicesItemGender
from .health_check_response_200 import HealthCheckResponse200
from .health_check_response_200_components import HealthCheckResponse200Components
from .health_check_response_200_status import HealthCheckResponse200Status
from .job_status_response import JobStatusResponse
from .job_status_response_job_type import JobStatusResponseJobType
from .job_status_response_status import JobStatusResponseStatus
from .jobs_list import JobsList
from .language_detection_request import LanguageDetectionRequest
from .language_detection_response import LanguageDetectionResponse
from .language_detection_response_languages_item import LanguageDetectionResponseLanguagesItem
from .language_detection_response_status import LanguageDetectionResponseStatus
from .list_jobs_job_type import ListJobsJobType
from .list_jobs_status import ListJobsStatus
from .text_to_speech_request import TextToSpeechRequest
from .text_to_speech_request_audio_format import TextToSpeechRequestAudioFormat
from .text_to_speech_response import TextToSpeechResponse
from .text_to_speech_response_status import TextToSpeechResponseStatus
from .transcribe_audio_files_body import TranscribeAudioFilesBody
from .transcribe_audio_files_body_model import TranscribeAudioFilesBodyModel
from .transcribe_audio_files_body_output_format import TranscribeAudioFilesBodyOutputFormat
from .transcription_request import TranscriptionRequest
from .transcription_request_config import TranscriptionRequestConfig
from .transcription_request_config_diarization import TranscriptionRequestConfigDiarization
from .transcription_request_config_model import TranscriptionRequestConfigModel
from .transcription_request_config_output_format import TranscriptionRequestConfigOutputFormat
from .transcription_request_config_translation import TranscriptionRequestConfigTranslation
from .transcription_response import TranscriptionResponse
from .transcription_response_segments_item import TranscriptionResponseSegmentsItem
from .transcription_response_status import TranscriptionResponseStatus
from .transcription_response_translations import TranscriptionResponseTranslations
from .translation_request import TranslationRequest
from .translation_response import TranslationResponse
from .translation_response_status import TranslationResponseStatus
from .translation_response_translations import TranslationResponseTranslations
from .translation_response_translations_additional_property import TranslationResponseTranslationsAdditionalProperty
from .translation_response_translations_additional_property_segments_item import TranslationResponseTranslationsAdditionalPropertySegmentsItem

__all__ = (
    "AudioBlobReference",
    "AudioBlobReferenceType",
    "AudioUpload",
    "AudioUploadType",
    "BlobSource",
    "DetectLanguageFilesBody",
    "ErrorDetail",
    "ErrorDetailDetails",
    "ErrorResponse",
    "GetAvailableVoicesResponse200",
    "GetAvailableVoicesResponse200VoicesItem",
    "GetAvailableVoicesResponse200VoicesItemGender",
    "HealthCheckResponse200",
    "HealthCheckResponse200Components",
    "HealthCheckResponse200Status",
    "JobsList",
    "JobStatusResponse",
    "JobStatusResponseJobType",
    "JobStatusResponseStatus",
    "LanguageDetectionRequest",
    "LanguageDetectionResponse",
    "LanguageDetectionResponseLanguagesItem",
    "LanguageDetectionResponseStatus",
    "ListJobsJobType",
    "ListJobsStatus",
    "TextToSpeechRequest",
    "TextToSpeechRequestAudioFormat",
    "TextToSpeechResponse",
    "TextToSpeechResponseStatus",
    "TranscribeAudioFilesBody",
    "TranscribeAudioFilesBodyModel",
    "TranscribeAudioFilesBodyOutputFormat",
    "TranscriptionRequest",
    "TranscriptionRequestConfig",
    "TranscriptionRequestConfigDiarization",
    "TranscriptionRequestConfigModel",
    "TranscriptionRequestConfigOutputFormat",
    "TranscriptionRequestConfigTranslation",
    "TranscriptionResponse",
    "TranscriptionResponseSegmentsItem",
    "TranscriptionResponseStatus",
    "TranscriptionResponseTranslations",
    "TranslationRequest",
    "TranslationResponse",
    "TranslationResponseStatus",
    "TranslationResponseTranslations",
    "TranslationResponseTranslationsAdditionalProperty",
    "TranslationResponseTranslationsAdditionalPropertySegmentsItem",
)
