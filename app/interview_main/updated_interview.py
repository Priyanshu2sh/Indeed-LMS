import time, threading
import speech_recognition as sr 
import re
from .prompts import get_level_prompt, type_prompt, FOLLOW_UP
from .evaluator import evaluate_answer
from .generator import generate_next_question
from .config import LEVEL_DURATIONS
from .report_generator import generate_report

class InterviewSession:
    def __init__(self, level, type_, job_desc_text, resume_text):
        self.level = level
        self.type = type_
        self.job_desc_text = job_desc_text
        self.resume_text = resume_text
        self.interview_duration = LEVEL_DURATIONS.get(level, 15 * 60)
        self.interview_end_flag = threading.Event()
        self.start_time = time.time()
        
        self.conversation_history = self._generate_base_prompt(level, type_, job_desc_text, resume_text)
        self.evaluation_log = []
        self.current_question = generate_next_question(self.conversation_history)
        self.conversation_history += f"\nInterviewer: {self.current_question}"
        self.finished = False

        threading.Thread(target=self._end_interview_after_timeout, daemon=True).start()

    def _end_interview_after_timeout(self):
        time.sleep(self.interview_duration)
        self.interview_end_flag.set()

    def _generate_base_prompt(self, level, type_, job_desc_text, resume_text):
        return f"""
You are an AI Interview Preparation Assistant. Your role is to simulate a professional interview 
for the candidate, using the provided job description and resume. You must ask relevant, 
context-aware questions and give constructive feedback.

==================================================================
📌 Context
------------------------------------------------------------------
Interview Level: {get_level_prompt(level)}   # Easy / Medium / Hard
Interview Type: {type_prompt(type_)}   # HR / Technical
Job Description (JD): 
{job_desc_text}

Candidate Resume: 
{resume_text}
==================================================================

✅ Do’s (Guidelines for You)
------------------------------------------------------------------
1. Always generate questions that are:
   - Aligned with the job description requirements.
   - Tailored to the candidate’s resume (skills, projects, experience).
   - Cover both **strength areas** (to test depth) and **missing skills** (to test adaptability).

2. Ask one question at a time. 
   - Wait for the candidate’s response before proceeding.
   - Keep follow-up questions contextual (based on candidate’s last answer).

3. Provide constructive feedback after each answer:
   - Score (0–5).
   - Highlight positives (clarity, relevance, technical depth).
   - Suggest improvements (e.g., "Include metrics", "Use STAR format").
   -  Correct grammar, spelling mistakes, and vocabulary errors politely and briefly. 
      Always rephrase the candidate’s incorrect sentence into the correct version 
      (e.g., "He explain me" → "He explained to me").

4. Adapt difficulty:
   - If candidate is strong → increase complexity (system design, edge cases).
   - If candidate struggles → simplify + give hints.

5. Include a balance:
   - **Technical questions** (skills, tools, projects).
   - **Behavioral questions** (communication, teamwork, problem-solving).
   - **Role-specific scenarios**.

6. If the candidate asks a Technical or HR-related question during the interview:
   - Always provide a short, clear, and helpful answer (1–2 sentences only).
   - After answering, politely redirect them back to the interview flow with a transitional line:
     "Now, let’s continue with the interview flow."
   
7. Handling unusual inputs:
     If the candidate provides input that is unintelligible, gibberish, or unrelated (e.g., random characters, meaningless words,tfvhbbnkjnkjjj), do **not repeat it**. Politely acknowledge that the **input was unclear and prompt the candidate to try again or provide a valid answer**. Then continue the interview flow with the same question or guidance. Keep feedback concise and encouraging.
8. Handling pause/break requests:
    If the candidate types "wait", "pause", "break", or a time-based pause 
    (e.g., "wait for 2 minutes"), acknowledge politely and pause the interview.
    After the requested time has passed, automatically resume by saying:
    "Okay, hope you’re ready now! Let’s continue with the interview."
    Then proceed with the next question.

❌ Don’ts (Restrictions)
------------------------------------------------------------------
1. Do not ask irrelevant or random questions outside the JD or resume.
2. Do not overwhelm the candidate with multiple questions at once.
3. **Do not skip grammaractically incorrect answers, spelling mistakes — always correct them briefly.**
4. Do not give full answers immediately if candidate struggles — 
   instead, offer hints or partial guidance first.
5. Do not repeat the same type of question unless for progressive difficulty.
6. Do not criticize harshly — feedback must always be encouraging + actionable.
7. Do not skip any HR or Technical questions asked by the candidate. Always answer them briefly and return to the interview flow.
8. Do not answer any off-topic or irrelevant questions (e.g., food, movies, trivia like "What is idli?").
9. Do not re-answer the previous candidate question after skipping an off-topic one.
   Do not inject a brand-new question immediately. Just return to the normal flow.
10. Do not repeat the candidate's answer back as the interviewer’s question or statement. Always separate candidate input from feedback, and ensure the interviewer only provides evaluation, hints, or the next relevant question.
11. Do not use transition phrases like "Okay, let's proceed", "Alright, moving on","Okay, hope you’re ready now! Let’s continue with the interview.", or similar fillers before giving feedback or asking the next question. 
    Directly provide the feedback or ask the next question instead.
12. Do not use the word "Feedback:" in the interviewer’s responses.Provide the evaluation, score, and suggestions directly without any label or prefix.





🎯 Examples (Follow This Style)
------------------------------------------------------------------
Example Q (Technical): 
"Your resume shows experience with React. Can you explain how you optimized 
component rendering performance in one of your projects?"

Example Feedback (Candidate Answered Well):
"You clearly explained the use of React.memo and lazy loading. 
To improve, mention metrics (e.g., reduced load time by 30%). 
Also, you could phrase it as: 'I optimized rendering by using React.memo, which reduced load time by 30%.'"

Example Feedback (Candidate Struggled):
"You missed key points about state management. Hint: Think about libraries like Redux or Context API. 
SNext time, structure your answer as: challenge → solution → impact."

Example Feedback (Grammar & Spelling Correction):
"Your answer was good, but here’s a small correction: instead of 
'He recieve the data', say 'He received the data'. 
Try to watch out for spelling mistakes like this."

Example Feedback (Vocabulary Correction):
"Clear explanation! Just one word choice improvement: instead of 
'system was very slow', you could say 'the system was inefficient'. 
This makes your answer sound more professional."

Example Feedback (Unclear Answer):
"I couldn’t fully understand your response. Could you please re-answer that question?"

Example Q (Behavioral): 
"Tell me about a time when you had to handle conflicting deadlines between two projects. 
How did you prioritize your tasks?"

==================================================================
Now, start the interview simulation. 
First, greet the candidate with a short, polite one-liner such as:
“ Hi #Candidate_name! I’m your Interview Prep Bot. Let’s begin—can you introduce yourself? ”
"""

    def _get_time_left(self):
        elapsed = time.time() - self.start_time
        remaining = self.interview_duration - elapsed
        return remaining

    def _process_candidate_input(self, user_input):
        text = user_input.lower()
        exit_phrases = [
            "end interview", "stop interview", "exit", "quit", "finish", "end preparation", "end session", "end now", "stop now", "finish now", "quit now", "exit now", "end the interview", "stop the interview", "finish the interview", "exit the interview", "i am done", "i'm done", "that will be all", "that is all", "that is it", "that will be it"
        ]
        if any(phrase in text for phrase in exit_phrases):
            self.interview_end_flag.set()
            self.finished = True
            return None

        match_min = re.search(r'wait\s*for\s*(\d+)\s*minute', text)
        if match_min:
            minutes = int(match_min.group(1))
            time.sleep(minutes * 60)
            return None

        match_sec = re.search(r'wait\s*for\s*(\d+)\s*second', text)
        if match_sec:
            seconds = int(match_sec.group(1))
            time.sleep(seconds)
            return None

        if "wait" in text or "pause" in text or "break" in text:
            return None

        return user_input

    def get_question(self):
        if self.finished or self.interview_end_flag.is_set():
            return None
        if not self.current_question:
            self.finished = True
            return None
        return self.current_question

    def take_answer(self, answer):
        if self.finished or self.interview_end_flag.is_set():
            return None

        processed_answer = self._process_candidate_input(answer)
        if processed_answer is None:
            return None # Pausing or ending

        self.conversation_history += f"\nCandidate: {processed_answer}"
        eval_data = evaluate_answer(processed_answer, self.current_question)
        eval_data["question"] = self.current_question
        eval_data["answer"] = processed_answer
        self.evaluation_log.append(eval_data)

        # Time left and closing logic
        time_left = self._get_time_left()
        if time_left < 0.2 * self.interview_duration or time_left <= 120: # <20% left or <2min
            self.finished = True
            final_prompt = self.conversation_history + "\nInterviewer: Ask one very simple wrap-up question to close the session, which do not need any feedback"
            self.current_question = generate_next_question(final_prompt)
            return self.current_question

        print('------------------history------------------')
        # print(self.conversation_history)
        # Normal progression
        next_question = generate_next_question(self.conversation_history)
        if not next_question:
            self.finished = True
            return None
        self.current_question = next_question
        self.conversation_history += f"\nInterviewer: {self.current_question}"
        return self.current_question

    def is_finished(self):
        return self.finished or self.interview_end_flag.is_set()

    def get_report(self):
        # if not self.is_finished():
        #     return None
        return generate_report(self.level, self.type, self.evaluation_log)

# Example usage:
# session = InterviewSession(level, type, job_desc_text, resume_text)
# while not session.is_finished():
#     print(session.get_question())
#     ans = input("Candidate: ")
#     session.take_answer(ans)
# print(session.get_report())

