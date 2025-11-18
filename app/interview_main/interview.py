import time, threading
import speech_recognition as sr 
import re
from prompts import get_level_prompt,type_prompt, FOLLOW_UP
from evaluator import evaluate_answer
from generator import generate_next_question
from config import LEVEL_DURATIONS

def run_interview(level, type,job_desc_text, resume_text):
    interview_duration = LEVEL_DURATIONS.get(level, 15 * 60)
    interview_end_flag = threading.Event()
    start_time = time.time()

    def end_interview_after_timeout():
        time.sleep(interview_duration)
        interview_end_flag.set()

    def get_time_left():
        elapsed = time.time() - start_time
        remaining = interview_duration - elapsed
        return remaining

    def process_candidate_input(user_input):
        text = user_input.lower()

        # ✅ Check for exit / end requests
        if any(phrase in text for phrase in [
            "end interview", "stop interview", "exit", "quit", "finish", "end preparation","end session","end now","stop now","finish now","quit now","exit now","end the interview","stop the interview","finish the interview","exit the interview","i am done","i'm done","that will be all","that is all","that is it","that will be it"
        ]):
            # print("🧑‍💼 Interviewer: Thank you for your time today. I hope this session helped with your preparation. Wishing you the best! 🙌")
            interview_end_flag.set()
            return None

        # ✅ Check for "X minutes"
        match_min = re.search(r'wait\s*for\s*(\d+)\s*minute', text)
        if match_min:
            minutes = int(match_min.group(1))
            # print(f"🧑‍💼 Interviewer: Sure, take your {minutes} minute(s).")
            time.sleep(minutes * 60)   # pause in seconds
            # print("🧑‍💼 Interviewer: Okay, hope you’re ready now! Let’s continue with the interview.")
            return None

        # ✅ Check for "X seconds"
        match_sec = re.search(r'wait\s*for\s*(\d+)\s*second', text)
        if match_sec:
            seconds = int(match_sec.group(1))
            # print(f"🧑‍💼 Interviewer: Sure, take your {seconds} second(s).")
            time.sleep(seconds)
            # print("🧑‍💼 Interviewer: Okay, hope you’re ready now! Let’s continue with the interview.")
            return None

        # ✅ Generic pause without time
        if "wait" in text or "pause" in text or "break" in text:
            # print("🧑‍💼 Interviewer: Sure, take your time. Let me know when you’re ready.")
            return None

        return user_input

    threading.Thread(target=end_interview_after_timeout, daemon=True).start()

    base_prompt = f"""
You are an AI Interview Preparation Assistant. Your role is to simulate a professional interview 
for the candidate, using the provided job description and resume. You must ask relevant, 
context-aware questions and give constructive feedback.
==============================
📌 Context
------------------------------
Interview Level: {get_level_prompt(level)}   
Interview Type: {type_prompt(type)}   
Job Description (JD): {job_desc_text}
Candidate Resume: {resume_text}
=================================
✅ Do’s (Guidelines for You)
---------------------------------
1. Always generate questions that are:
   - Aligned with the job description requirements.
   - Cover both *strength areas* (to test depth) and *missing skills* (to test adaptability).

2. Provide constructive feedback after each answer:
   - Highlight positives.
   - Suggest improvements (e.g., "Include metrics", "Use STAR format").
   -  Correct grammar, spelling mistakes, and vocabulary errors politely and briefly.  
      (e.g., "He explain me" → "He explained to me").

🎯 Examples (Follow This Style)
------------------------------------------------------------------
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

Example Feedback (Unclear Answer):
"I couldn’t fully understand your response. Could you please re-answer that question?"

Example Q (Behavioral): 
"Tell me about a time when you had to handle conflicting deadlines between two projects. 
How did you prioritize your tasks?"

Example:
Only provide corrections or suggestions when the user's message contains special symbols (! @ # $ % ^ & * ( ) _ + - =  [ ] : ; " ' < > , . / ?). If the message has no special symbols, simply acknowledge it and continue the conversation without giving feedback. 
Example: If the user says "I am a full stack developer" just accept it; do not correct to "full-stack developer."


🚫 Don’t use filler transitions, appreciations in beginning (“Okay, moving on…”,"That's Intresting...","You did a good job").
==================================================================
First, greet the candidate with a short, polite one-liner such as:
“ Hi #Candidate_name! I’m your Interview Prep Bot. Let’s begin—can you introduce yourself? ”
"""
    conversation_history = base_prompt + "\nInterviewer:"
    evaluation_log = []

    first_question = generate_next_question(conversation_history)
    # print("\n🧑‍💼 Interviewer:", first_question)
    conversation_history += f" {first_question}"
    interviewer_question = first_question

    recognizer = sr.Recognizer()
    mic = sr.Microphone()

    while not interview_end_flag.is_set():
        try:
            answer = input("\n🧑 Candidate (type your answer): ")

        except EOFError:
            break

        if not answer:
            # print("\n🛑 No response received. Ending the interview.")
            break

        processed = process_candidate_input(answer)
        if processed is None:
            continue  # skip the rest of loop, wait until candidate is ready
        else:
            answer = processed

        conversation_history += f"\nCandidate: {answer}\nInterviewer:"
        eval_data = evaluate_answer(answer, interviewer_question)
        eval_data["question"] = interviewer_question
        eval_data["answer"] = answer
        evaluation_log.append(eval_data)

        # ✅ Always show time left after each answer
        time_left = get_time_left()
        mins = int(time_left // 60)
        secs = int(time_left % 60)
        
        # ✅ If time is critically low, request final question from LLM
        if time_left < 0.2 * interview_duration or time_left <= 120:
            # print("\n🧑‍💼 Interviewer: We’re almost done with our session, so let’s end with one last question.")
            time.sleep( 0.03* 60)   # pause in seconds

            # Add instruction to conversation history
            final_prompt = conversation_history + "\nInterviewer: Just Ask one very simple wrap-up question to close the session, which do not need any feedback.No appreciation in beginning."
            interviewer_question = generate_next_question(final_prompt)
            # print("🧑‍💼 Interviewer:", interviewer_question)
            conversation_history += f" {interviewer_question}"

            # Candidate's final answer
            final_answer = input("\n🧑 Candidate (type your answer): ")

            eval_data = evaluate_answer(final_answer, interviewer_question)
            eval_data["question"] = interviewer_question
            eval_data["answer"] = final_answer
            evaluation_log.append(eval_data)

            # Conclude interview
            # print("\n🧑‍💼 Interviewer: Thank you for your responses! That concludes this interview prep session. Wishing you the best! 🙌")
            break

        next_question = generate_next_question(conversation_history)
        if not next_question:
            # print("🛑 Interview ended. No further questions.")
            break

        interviewer_question = next_question
        # print("\n🧑‍💼 Interviewer:", interviewer_question)
        conversation_history += f" {interviewer_question}"

    # print("\n🛑 Interview time completed or session ended.")
    
    # ✅ Generate the final report
    from report_generator import generate_report
    final_report = generate_report(level, type, evaluation_log)
    
    # Print or save
    
    return final_report
