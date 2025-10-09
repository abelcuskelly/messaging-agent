"""
Multi-modal capabilities for the messaging agent
- Image processing for ticket screenshots/QR codes
- Voice-to-text for phone support integration  
- Document parsing for ticket confirmations
"""

import os
import base64
import io
from typing import List, Dict, Optional, Any
from google.cloud import vision, speech, documentai
from vertexai.language_models import TextEmbeddingModel
import structlog

logger = structlog.get_logger()


class ImageProcessor:
    """Process images for ticket screenshots, QR codes, and document analysis."""
    
    def __init__(self, project_id: Optional[str] = None):
        self.project_id = project_id or os.getenv("PROJECT_ID")
        self.vision_client = vision.ImageAnnotatorClient()
    
    def extract_text_from_image(self, image_data: bytes) -> Dict[str, Any]:
        """Extract text from ticket screenshots using OCR."""
        try:
            image = vision.Image(content=image_data)
            
            # OCR for text extraction
            text_response = self.vision_client.text_detection(image=image)
            texts = text_response.text_annotations
            
            # Object detection for tickets/QR codes
            object_response = self.vision_client.object_localization(image=image)
            objects = object_response.localized_object_annotations
            
            # Label detection for context
            label_response = self.vision_client.label_detection(image=image)
            labels = label_response.label_annotations
            
            extracted_data = {
                "full_text": texts[0].description if texts else "",
                "text_blocks": [
                    {
                        "text": text.description,
                        "confidence": text.confidence,
                        "bounding_box": [
                            {"x": vertex.x, "y": vertex.y} 
                            for vertex in text.bounding_poly.vertices
                        ]
                    }
                    for text in texts[1:]  # Skip full text, get individual blocks
                ],
                "objects": [
                    {
                        "name": obj.name,
                        "confidence": obj.score,
                        "bounding_box": [
                            {"x": vertex.x, "y": vertex.y}
                            for vertex in obj.bounding_poly.normalized_vertices
                        ]
                    }
                    for obj in objects
                ],
                "labels": [
                    {
                        "description": label.description,
                        "confidence": label.score
                    }
                    for label in labels
                ]
            }
            
            logger.info("Image text extraction completed", 
                       text_length=len(extracted_data["full_text"]),
                       objects_count=len(extracted_data["objects"]))
            
            return extracted_data
            
        except Exception as e:
            logger.error("Image processing failed", error=str(e))
            return {"error": str(e)}
    
    def detect_qr_codes(self, image_data: bytes) -> List[Dict[str, Any]]:
        """Detect and decode QR codes in images."""
        try:
            image = vision.Image(content=image_data)
            response = self.vision_client.barcode_detection(image=image)
            
            qr_codes = []
            for barcode in response.barcodes:
                if barcode.format == vision.BarcodeFormat.QR_CODE:
                    qr_codes.append({
                        "data": barcode.raw_value,
                        "format": barcode.format.name,
                        "bounding_box": [
                            {"x": vertex.x, "y": vertex.y}
                            for vertex in barcode.bounding_poly.vertices
                        ]
                    })
            
            logger.info("QR code detection completed", qr_count=len(qr_codes))
            return qr_codes
            
        except Exception as e:
            logger.error("QR code detection failed", error=str(e))
            return []


class VoiceProcessor:
    """Process voice input for phone support integration."""
    
    def __init__(self, project_id: Optional[str] = None):
        self.project_id = project_id or os.getenv("PROJECT_ID")
        self.speech_client = speech.SpeechClient()
    
    def transcribe_audio(self, audio_data: bytes, language_code: str = "en-US") -> Dict[str, Any]:
        """Transcribe audio to text using Google Speech-to-Text."""
        try:
            audio = speech.RecognitionAudio(content=audio_data)
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,
                sample_rate_hertz=16000,
                language_code=language_code,
                enable_automatic_punctuation=True,
                enable_word_time_offsets=True,
            )
            
            response = self.speech_client.recognize(config=config, audio=audio)
            
            transcriptions = []
            for result in response.results:
                transcriptions.append({
                    "transcript": result.alternatives[0].transcript,
                    "confidence": result.alternatives[0].confidence,
                    "words": [
                        {
                            "word": word.word,
                            "start_time": word.start_time.total_seconds(),
                            "end_time": word.end_time.total_seconds()
                        }
                        for word in result.alternatives[0].words
                    ]
                })
            
            logger.info("Audio transcription completed", 
                       transcriptions_count=len(transcriptions))
            
            return {
                "transcriptions": transcriptions,
                "full_transcript": " ".join([t["transcript"] for t in transcriptions])
            }
            
        except Exception as e:
            logger.error("Audio transcription failed", error=str(e))
            return {"error": str(e)}
    
    def text_to_speech(self, text: str, voice_name: str = "en-US-Wavenet-D") -> bytes:
        """Convert text to speech for phone responses."""
        from google.cloud import texttospeech
        
        try:
            client = texttospeech.TextToSpeechClient()
            
            synthesis_input = texttospeech.SynthesisInput(text=text)
            voice = texttospeech.VoiceSelectionParams(
                language_code="en-US",
                name=voice_name,
                ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
            )
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3
            )
            
            response = client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )
            
            logger.info("Text-to-speech completed", text_length=len(text))
            return response.audio_content
            
        except Exception as e:
            logger.error("Text-to-speech failed", error=str(e))
            return b""


class DocumentProcessor:
    """Process documents for ticket confirmations and receipts."""
    
    def __init__(self, project_id: Optional[str] = None):
        self.project_id = project_id or os.getenv("PROJECT_ID")
        self.document_client = documentai.DocumentProcessorServiceClient()
    
    def parse_ticket_document(self, document_data: bytes, processor_id: str) -> Dict[str, Any]:
        """Parse ticket documents using Document AI."""
        try:
            # Use a general form parser or custom processor
            name = f"projects/{self.project_id}/locations/us/processors/{processor_id}"
            
            raw_document = documentai.RawDocument(
                content=document_data,
                mime_type="application/pdf"  # or "image/jpeg", "image/png"
            )
            
            request = documentai.ProcessRequest(
                name=name,
                raw_document=raw_document
            )
            
            result = self.document_client.process_document(request=request)
            document = result.document
            
            # Extract structured data
            extracted_data = {
                "text": document.text,
                "entities": [
                    {
                        "type": entity.type_,
                        "mention_text": entity.mention_text,
                        "confidence": entity.confidence,
                        "normalized_value": entity.normalized_value.text if entity.normalized_value else None
                    }
                    for entity in document.entities
                ],
                "pages": [
                    {
                        "page_number": page.page_number,
                        "dimension": {
                            "width": page.dimension.width,
                            "height": page.dimension.height
                        },
                        "text": page.text
                    }
                    for page in document.pages
                ]
            }
            
            logger.info("Document parsing completed", 
                       entities_count=len(extracted_data["entities"]),
                       pages_count=len(extracted_data["pages"]))
            
            return extracted_data
            
        except Exception as e:
            logger.error("Document parsing failed", error=str(e))
            return {"error": str(e)}


class MultimodalAgent:
    """Agent with multi-modal capabilities."""
    
    def __init__(self, endpoint, image_processor: ImageProcessor, voice_processor: VoiceProcessor, document_processor: DocumentProcessor):
        self.endpoint = endpoint
        self.image_processor = image_processor
        self.voice_processor = voice_processor
        self.document_processor = document_processor
    
    def process_multimodal_input(self, user_input: Dict[str, Any]) -> str:
        """Process multi-modal input (text, image, audio, document)."""
        try:
            # Extract different input types
            text_input = user_input.get("text", "")
            image_data = user_input.get("image")
            audio_data = user_input.get("audio")
            document_data = user_input.get("document")
            
            context_parts = []
            
            # Process text input
            if text_input:
                context_parts.append(f"User message: {text_input}")
            
            # Process image
            if image_data:
                image_bytes = base64.b64decode(image_data)
                image_info = self.image_processor.extract_text_from_image(image_bytes)
                
                if "full_text" in image_info:
                    context_parts.append(f"Image text: {image_info['full_text']}")
                
                qr_codes = self.image_processor.detect_qr_codes(image_bytes)
                if qr_codes:
                    qr_data = ", ".join([qr["data"] for qr in qr_codes])
                    context_parts.append(f"QR codes found: {qr_data}")
            
            # Process audio
            if audio_data:
                audio_bytes = base64.b64decode(audio_data)
                audio_info = self.voice_processor.transcribe_audio(audio_bytes)
                
                if "full_transcript" in audio_info:
                    context_parts.append(f"Voice transcript: {audio_info['full_transcript']}")
            
            # Process document
            if document_data:
                doc_bytes = base64.b64decode(document_data)
                doc_info = self.document_processor.parse_ticket_document(doc_bytes, "your-processor-id")
                
                if "text" in doc_info:
                    context_parts.append(f"Document text: {doc_info['text']}")
            
            # Build context
            context = "\n\n".join(context_parts)
            
            # Create system message
            system_message = f"""You are a helpful assistant for a sports ticketing service. 
The user has provided the following multi-modal input:

{context}

Please analyze all the information provided and respond appropriately. If you see ticket information, 
QR codes, or document details, help the user with their ticketing needs."""
            
            # Get response from model
            messages = [
                {"role": "system", "content": system_message},
                {"role": "user", "content": text_input or "Please help me with the information provided."}
            ]
            
            response = self.endpoint.predict(instances=[{"messages": messages}])
            return response.predictions[0]["response"]
            
        except Exception as e:
            logger.error("Multimodal processing failed", error=str(e))
            return "I'm sorry, I encountered an error processing your request. Please try again."


def create_multimodal_tools():
    """Create tools for multi-modal processing."""
    from agent.tools import registry
    
    @registry.register(
        name="process_image",
        description="Process uploaded images for ticket information, QR codes, or text extraction",
        parameters={
            "type": "object",
            "properties": {
                "image_data": {"type": "string", "description": "Base64 encoded image data"},
                "extract_text": {"type": "boolean", "description": "Extract text from image", "default": True},
                "detect_qr": {"type": "boolean", "description": "Detect QR codes", "default": True}
            },
            "required": ["image_data"]
        }
    )
    def process_image(image_data: str, extract_text: bool = True, detect_qr: bool = True) -> str:
        processor = ImageProcessor()
        image_bytes = base64.b64decode(image_data)
        
        results = []
        if extract_text:
            text_info = processor.extract_text_from_image(image_bytes)
            if "full_text" in text_info:
                results.append(f"Extracted text: {text_info['full_text']}")
        
        if detect_qr:
            qr_codes = processor.detect_qr_codes(image_bytes)
            if qr_codes:
                qr_data = ", ".join([qr["data"] for qr in qr_codes])
                results.append(f"QR codes: {qr_data}")
        
        return "\n".join(results) if results else "No information extracted from image"
    
    @registry.register(
        name="transcribe_audio",
        description="Transcribe audio input to text",
        parameters={
            "type": "object",
            "properties": {
                "audio_data": {"type": "string", "description": "Base64 encoded audio data"},
                "language_code": {"type": "string", "description": "Language code", "default": "en-US"}
            },
            "required": ["audio_data"]
        }
    )
    def transcribe_audio(audio_data: str, language_code: str = "en-US") -> str:
        processor = VoiceProcessor()
        audio_bytes = base64.b64decode(audio_data)
        result = processor.transcribe_audio(audio_bytes, language_code)
        
        if "full_transcript" in result:
            return f"Transcription: {result['full_transcript']}"
        return "Audio transcription failed"
    
    @registry.register(
        name="parse_document",
        description="Parse ticket documents and receipts",
        parameters={
            "type": "object",
            "properties": {
                "document_data": {"type": "string", "description": "Base64 encoded document data"},
                "processor_id": {"type": "string", "description": "Document AI processor ID"}
            },
            "required": ["document_data", "processor_id"]
        }
    )
    def parse_document(document_data: str, processor_id: str) -> str:
        processor = DocumentProcessor()
        doc_bytes = base64.b64decode(document_data)
        result = processor.parse_ticket_document(doc_bytes, processor_id)
        
        if "text" in result:
            return f"Document text: {result['text']}"
        return "Document parsing failed"
