import asyncio
import json, io, base64
from channels.generic.websocket import AsyncWebsocketConsumer
import speech_recognition as sr
import tempfile
from asgiref.sync import sync_to_async
from django.utils import timezone
from .models import ChatAccess
from .interview_main.updated_interview import InterviewSession
from .interview_main.pdf_utils import extract_text_from_pdf

class InterviewConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()

        # auth user
        user = self.scope["user"]
        if not user or user.is_anonymous:
            await self.send(text_data=json.dumps({
                "error": "Authentication required"
            }))
            await self.close()
            return
        
        # ensure user has ChatAccess
        self.access = await sync_to_async(lambda: ChatAccess.objects.filter(user=user).first())()
        if not self.access:
            await self.send(text_data=json.dumps({
                "error": "No demo/paid time record found. Please purchase or contact admin."
            }))
            await self.close()
            return
        
        self.remaining = await sync_to_async(self.access.total_remaining)()
        if self.remaining <= 0:
            await self.send(text_data=json.dumps({
                "error": "No demo/paid time available. Please purchase or contact admin."
            }))
            await self.close()
            return

        # mark when this connection started for bookkeeping
        self.last_active = timezone.now()
        self.session_active = True

        
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
            "question": first_question,
            "type": "time_update",
            "remaining_seconds": int(self.access.total_remaining())
        }))

        # Start background time updater
        self.loop_task = asyncio.create_task(self.time_tracker())

    async def disconnect(self, close_code):
        # when websocket disconnects, compute elapsed and deduct
        try:
            now = timezone.now()
            elapsed = (now - self.last_active).total_seconds()
            await sync_to_async(self.access.consume_seconds)(int(elapsed))
        except Exception:
            pass
        # nothing else special
        return

    async def receive(self, bytes_data=None, text_data=None):

        # Handle audio (bytes_data) and text (text_data)
        candidate_message = None

        if text_data:
            data = json.loads(text_data)
            print('aaaaa- ', data)
            

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

    async def time_tracker(self):
        while self.remaining > 0:
            await asyncio.sleep(1)
            self.remaining -= 1
            print("Remaining time:", self.remaining)
            await self.send(text_data=json.dumps({
                "type": "time_update",
                "remaining_seconds": self.remaining
            }))

        # Time expired – step 1: notify frontend
        await self.send(text_data=json.dumps({
            "type": "time_expired",
            "message": "Your demo/paid session has ended."
        }))

        # Step 2: Generate and send summary report before closing
        try:
            print("Generating session summary...")
            # Interview ended, return final report
            report = await sync_to_async(self.session.get_report)()
            await self.send(text_data=json.dumps({
                "type": "session_complete",
                "summary": report
            }))
        except Exception as e:
            print("Error generating summary:", e)
            await self.send(text_data=json.dumps({
                "type": "session_summary",
                "error": "Failed to generate session summary."
            }))

        # Step 3: close connection gracefully
        await self.close()
