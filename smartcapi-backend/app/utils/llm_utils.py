"""
LLM Utilities untuk SmartCAPI
Integrasi dengan OpenAI API untuk ekstraksi jawaban dari transkrip wawancara
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from openai import OpenAI
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)


class LLMUtils:
    """Utility class untuk integrasi dengan LLM (OpenAI)"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4"):
        """
        Initialize LLM Utils
        
        Args:
            api_key: OpenAI API key (ambil dari env jika None)
            model: Model name (default: gpt-4)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)
        else:
            logger.warning("OpenAI API key not found")
            self.client = None
    
    
    def extract_answers_from_transcript(
        self,
        transcript: str,
        questions: List[str],
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Ekstraksi jawaban dari transkrip berdasarkan daftar pertanyaan
        
        Args:
            transcript: Transkrip lengkap wawancara
            questions: List pertanyaan dalam kuesioner
            context: Konteks tambahan (optional)
            
        Returns:
            Dict dengan extracted answers
        """
        try:
            if not self.client:
                raise ValueError("OpenAI client not initialized")
            
            # Build prompt
            prompt = self._build_extraction_prompt(transcript, questions, context)
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Anda adalah asisten yang ahli dalam mengekstrak informasi dari transkrip wawancara survei. Ekstrak jawaban dengan akurat sesuai pertanyaan yang diberikan."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2000,
                response_format={"type": "json_object"}
            )
            
            # Parse response
            result = json.loads(response.choices[0].message.content)
            
            logger.info(f"Answers extracted for {len(questions)} questions")
            
            return {
                "success": True,
                "extracted_answers": result.get("answers", {}),
                "confidence_scores": result.get("confidence_scores", {}),
                "metadata": {
                    "model": self.model,
                    "timestamp": datetime.now().isoformat(),
                    "tokens_used": response.usage.total_tokens
                }
            }
            
        except Exception as e:
            logger.error(f"Error extracting answers: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "extracted_answers": {}
            }
    
    
    def _build_extraction_prompt(
        self,
        transcript: str,
        questions: List[str],
        context: Optional[str] = None
    ) -> str:
        """
        Build prompt untuk ekstraksi jawaban
        
        Args:
            transcript: Transkrip wawancara
            questions: List pertanyaan
            context: Konteks tambahan
            
        Returns:
            Prompt string
        """
        prompt = f"""Berikut adalah transkrip wawancara survei:

TRANSKRIP:
{transcript}

PERTANYAAN KUESIONER:
"""
        
        for i, q in enumerate(questions, 1):
            prompt += f"{i}. {q}\n"
        
        if context:
            prompt += f"\nKONTEKS TAMBAHAN:\n{context}\n"
        
        prompt += """
TUGAS:
Ekstrak jawaban untuk setiap pertanyaan dari transkrip di atas. Untuk setiap pertanyaan, berikan:
1. Jawaban yang diekstrak dari transkrip
2. Confidence score (0-1) yang menunjukkan seberapa yakin Anda dengan jawaban tersebut
3. Quote/kutipan dari transkrip yang mendukung jawaban (jika ada)

Format output dalam JSON:
{
    "answers": {
        "1": "jawaban untuk pertanyaan 1",
        "2": "jawaban untuk pertanyaan 2",
        ...
    },
    "confidence_scores": {
        "1": 0.95,
        "2": 0.80,
        ...
    },
    "supporting_quotes": {
        "1": "kutipan dari transkrip",
        "2": "kutipan dari transkrip",
        ...
    }
}

CATATAN:
- Jika jawaban tidak ditemukan dalam transkrip, isi dengan "TIDAK DITEMUKAN"
- Confidence score 0 jika jawaban tidak ditemukan
- Ekstrak jawaban persis seperti yang diucapkan responden, jangan interpretasi berlebihan
"""
        
        return prompt
    
    
    def summarize_interview(
        self,
        transcript: str,
        max_length: int = 500
    ) -> Dict[str, Any]:
        """
        Generate ringkasan wawancara
        
        Args:
            transcript: Transkrip lengkap
            max_length: Panjang maksimal ringkasan (words)
            
        Returns:
            Dict dengan summary
        """
        try:
            if not self.client:
                raise ValueError("OpenAI client not initialized")
            
            prompt = f"""Buat ringkasan singkat dari transkrip wawancara berikut (maksimal {max_length} kata):

TRANSKRIP:
{transcript}

RINGKASAN:"""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Anda adalah asisten yang membuat ringkasan wawancara yang concise dan informatif."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=1000
            )
            
            summary = response.choices[0].message.content.strip()
            
            return {
                "success": True,
                "summary": summary,
                "word_count": len(summary.split()),
                "metadata": {
                    "model": self.model,
                    "timestamp": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error summarizing interview: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "summary": ""
            }
    
    
    def validate_extracted_answers(
        self,
        extracted_answers: Dict[str, str],
        questions: List[str],
        validation_rules: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Validasi hasil ekstraksi jawaban
        
        Args:
            extracted_answers: Dict jawaban yang diekstrak
            questions: List pertanyaan
            validation_rules: Rules untuk validasi (optional)
            
        Returns:
            Dict dengan validation results
        """
        try:
            validation_results = {}
            
            for i, question in enumerate(questions, 1):
                q_id = str(i)
                answer = extracted_answers.get(q_id, "")
                
                validation = {
                    "is_valid": True,
                    "errors": [],
                    "warnings": []
                }
                
                # Check if answer exists
                if not answer or answer == "TIDAK DITEMUKAN":
                    validation["is_valid"] = False
                    validation["errors"].append("Jawaban tidak ditemukan")
                
                # Check answer length
                if len(answer.split()) < 2:
                    validation["warnings"].append("Jawaban terlalu pendek")
                
                # Apply custom validation rules
                if validation_rules and q_id in validation_rules:
                    rule = validation_rules[q_id]
                    
                    # Check answer type
                    if rule.get("type") == "numeric":
                        if not answer.replace(".", "").replace(",", "").isdigit():
                            validation["errors"].append("Jawaban harus berupa angka")
                            validation["is_valid"] = False
                    
                    # Check choices
                    if "choices" in rule:
                        if answer not in rule["choices"]:
                            validation["warnings"].append(f"Jawaban tidak ada dalam pilihan: {rule['choices']}")
                
                validation_results[q_id] = validation
            
            # Overall validation
            all_valid = all(v["is_valid"] for v in validation_results.values())
            
            return {
                "is_valid": all_valid,
                "validation_results": validation_results,
                "total_questions": len(questions),
                "valid_answers": sum(1 for v in validation_results.values() if v["is_valid"]),
                "invalid_answers": sum(1 for v in validation_results.values() if not v["is_valid"])
            }
            
        except Exception as e:
            logger.error(f"Error validating answers: {str(e)}")
            return {"is_valid": False, "error": str(e)}
    
    
    def improve_transcription_quality(
        self,
        raw_transcript: str,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Perbaiki kualitas transkrip (grammar, punctuation, dll)
        
        Args:
            raw_transcript: Transkrip mentah dari Whisper
            context: Konteks (e.g., topik survei)
            
        Returns:
            Dict dengan improved transcript
        """
        try:
            if not self.client:
                raise ValueError("OpenAI client not initialized")
            
            prompt = f"""Perbaiki transkrip berikut dengan menambahkan tanda baca yang tepat, memperbaiki grammar, dan membuat lebih mudah dibaca. Jangan ubah isi atau makna dari ucapan asli.

TRANSKRIP MENTAH:
{raw_transcript}
"""
            
            if context:
                prompt += f"\nKONTEKS: {context}\n"
            
            prompt += "\nTRANSKRIP YANG DIPERBAIKI:"
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Anda adalah editor profesional yang memperbaiki transkrip audio tanpa mengubah makna asli."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            improved = response.choices[0].message.content.strip()
            
            return {
                "success": True,
                "improved_transcript": improved,
                "original_length": len(raw_transcript),
                "improved_length": len(improved),
                "metadata": {
                    "model": self.model,
                    "timestamp": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error improving transcription: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "improved_transcript": raw_transcript
            }
    
    
    async def extract_answers_async(
        self,
        transcript: str,
        questions: List[str],
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Async version of extract_answers_from_transcript
        
        Args:
            transcript: Transkrip wawancara
            questions: List pertanyaan
            context: Konteks tambahan
            
        Returns:
            Dict dengan extracted answers
        """
        return await asyncio.to_thread(
            self.extract_answers_from_transcript,
            transcript,
            questions,
            context
        )
    
    
    def batch_extract_answers(
        self,
        transcripts: List[str],
        questions: List[str],
        context: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Ekstraksi jawaban dari multiple transcripts
        
        Args:
            transcripts: List transkrip
            questions: List pertanyaan
            context: Konteks tambahan
            
        Returns:
            List hasil ekstraksi
        """
        try:
            results = []
            
            for i, transcript in enumerate(transcripts):
                logger.info(f"Processing transcript {i+1}/{len(transcripts)}")
                result = self.extract_answers_from_transcript(
                    transcript,
                    questions,
                    context
                )
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Error in batch extraction: {str(e)}")
            return []
    
    
    def classify_question_type(
        self,
        question: str
    ) -> Dict[str, Any]:
        """
        Klasifikasi tipe pertanyaan (open-ended, multiple choice, numeric, dll)
        
        Args:
            question: Pertanyaan
            
        Returns:
            Dict dengan classification result
        """
        try:
            if not self.client:
                raise ValueError("OpenAI client not initialized")
            
            prompt = f"""Klasifikasikan tipe pertanyaan berikut:

PERTANYAAN: {question}

Tentukan tipe pertanyaan dari pilihan berikut:
- "open_ended": Pertanyaan terbuka yang membutuhkan jawaban naratif
- "multiple_choice": Pertanyaan dengan pilihan jawaban
- "numeric": Pertanyaan yang jawabannya berupa angka
- "yes_no": Pertanyaan ya/tidak
- "scale": Pertanyaan dengan skala rating

Format output JSON:
{{
    "question_type": "tipe_pertanyaan",
    "reasoning": "alasan klasifikasi",
    "expected_answer_format": "format jawaban yang diharapkan"
}}
"""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Anda adalah classifier yang menganalisis tipe pertanyaan survei."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=300,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            
            return {
                "success": True,
                "classification": result
            }
            
        except Exception as e:
            logger.error(f"Error classifying question: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    
    def detect_inconsistencies(
        self,
        extracted_answers: Dict[str, str],
        questions: List[str]
    ) -> Dict[str, Any]:
        """
        Deteksi inkonsistensi atau kontradiksi dalam jawaban
        
        Args:
            extracted_answers: Dict jawaban yang diekstrak
            questions: List pertanyaan
            
        Returns:
            Dict dengan detected inconsistencies
        """
        try:
            if not self.client:
                raise ValueError("OpenAI client not initialized")
            
            # Build answers text
            answers_text = ""
            for i, question in enumerate(questions, 1):
                answer = extracted_answers.get(str(i), "TIDAK DITEMUKAN")
                answers_text += f"Q{i}: {question}\nA{i}: {answer}\n\n"
            
            prompt = f"""Analisis jawaban berikut untuk menemukan inkonsistensi atau kontradiksi:

{answers_text}

Identifikasi:
1. Jawaban yang saling bertentangan
2. Jawaban yang tidak logis
3. Informasi yang missing atau tidak lengkap

Format output JSON:
{{
    "has_inconsistencies": true/false,
    "inconsistencies": [
        {{
            "question_ids": ["1", "3"],
            "description": "Deskripsi inkonsistensi",
            "severity": "high/medium/low"
        }}
    ],
    "overall_quality_score": 0.85
}}
"""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Anda adalah quality checker yang mendeteksi inkonsistensi dalam data survei."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            
            return {
                "success": True,
                "analysis": result
            }
            
        except Exception as e:
            logger.error(f"Error detecting inconsistencies: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    
    def generate_follow_up_questions(
        self,
        question: str,
        answer: str
    ) -> List[str]:
        """
        Generate follow-up questions berdasarkan jawaban
        
        Args:
            question: Pertanyaan original
            answer: Jawaban dari responden
            
        Returns:
            List follow-up questions
        """
        try:
            if not self.client:
                raise ValueError("OpenAI client not initialized")
            
            prompt = f"""Berdasarkan pertanyaan dan jawaban berikut, buat 2-3 follow-up questions untuk menggali informasi lebih dalam:

PERTANYAAN: {question}
JAWABAN: {answer}

Format output JSON:
{{
    "follow_up_questions": [
        "pertanyaan follow-up 1",
        "pertanyaan follow-up 2",
        "pertanyaan follow-up 3"
    ]
}}
"""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Anda adalah interviewer berpengalaman yang membuat follow-up questions yang relevan."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            return result.get("follow_up_questions", [])
            
        except Exception as e:
            logger.error(f"Error generating follow-up questions: {str(e)}")
            return []


# Instance untuk digunakan
llm_utils = LLMUtils()