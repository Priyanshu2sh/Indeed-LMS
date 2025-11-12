import json, io, base64
from channels.generic.websocket import AsyncWebsocketConsumer
import speech_recognition as sr
import tempfile
from asgiref.sync import sync_to_async
from .interview_main.updated_interview import InterviewSession
from .interview_main.pdf_utils import extract_text_from_pdf

class InterviewConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()

        # Load user + files from DB
        user = self.scope["user"]

        if not user or user.is_anonymous:
            await self.send(text_data=json.dumps({
                "error": "Authentication required"
            }))
            await self.close()
            return
        
        # Example: assume you have stored file paths in DB
        resume_text = extract_text_from_pdf(user.resume_file.path)
        job_desc_text = extract_text_from_pdf(user.jd_file.path)

        # Initialize InterviewSession and store on self
        self.session = InterviewSession(
            user.interview_difficulty,
            user.interview_type,
            job_desc_text,
            resume_text
        )

        # Send the first question to the candidate
        first_question = await sync_to_async(self.session.get_question)()
        await self.send(text_data=json.dumps({
            "type": "question",
            "question": first_question
        }))

    async def disconnect(self, close_code):
        pass

    async def receive(self, bytes_data=None):
        # Handles both audio (bytes_data) and text (text_data) messages
        
        candidate_message = None

        if bytes_data:
            # Transcribe audio using SpeechRecognition
            try:
                with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp:
                    tmp.write(bytes_data)
                    tmp.flush()
                    tmp_path = tmp.name

                # Convert WebM to WAV (SpeechRecognition needs this)
                import subprocess
                wav_path = tmp_path.replace(".webm", ".wav")
                subprocess.run(
                    ["ffmpeg", "-y", "-i", tmp_path, "-ar", "16000", "-ac", "1", wav_path],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )

                recognizer = sr.Recognizer()
                with sr.AudioFile(wav_path) as source:
                    audio = recognizer.record(source)
                try:
                    candidate_message = recognizer.recognize_google(audio)
                except sr.UnknownValueError:
                    question = "Sorry, I couldn't understand that."
                    await self.send(text_data=json.dumps({"question": question}))
                    return

            except Exception as e:
                question = f"Audio processing error: {e}"
                await self.send(text_data=json.dumps({"question": question}))
                return

        if not candidate_message:
            await self.send(text_data=json.dumps({"question": "Sorry, I didn't received any answer."}))
            return

        await self.send(text_data=json.dumps({"answer": candidate_message}))

        # Pass the candidate answer to InterviewSession, get next question or end
        next_question = await sync_to_async(self.session.take_answer)(candidate_message)
        if next_question is None:
            # Interview ended, return final report
            report = await sync_to_async(self.session.get_report)()
            await self.send(text_data=json.dumps({
                "type": "session_complete",
                "summary": report
            }))
        else:
            await self.send(text_data=json.dumps({
                "type": "question",
                "question": next_question
            }))