import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv
import google.generativeai as genai

# Load env before importing app modules
load_dotenv()

from app.modules.conversation.service import ConversationService
from app.modules.conversation.models import ChatRequest

# Configure GenAI for the "Judge"
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
judge_model = genai.GenerativeModel("gemini-2.0-flash")

TEST_CASES = [
    {
        "question": "How can I transfer money using the mobile app?",
        "expected_topic": "Mobile banking transfer steps, Amedenda app",
        "language": "en"
    },
    {
        "question": "ገንዘብ እንዴት ማስተላለፍ እችላለሁ?",  # How to transfer money (Amharic)
        "expected_topic": "Transfer money instructions in Amharic",
        "language": "am"
    },
    {
        "question": "What is the capital of France?",
        "expected_topic": "Refusal to answer (out of scope)",
        "language": "en"
    }
]

async def run_evaluation():
    service = ConversationService()
    print(f"--- Starting RAG Evaluation on {len(TEST_CASES)} cases ---\n")

    for i, case in enumerate(TEST_CASES):
        print(f"Test #{i+1}: {case['question']} ({case['language']})")
        
        # 1. Get AI Response
        req = ChatRequest(
            session_id="test-eval-session",
            message=case['question'],
            language=case['language']
        )
        try:
            response = await service.handle_chat(req)
            ai_reply = response.reply
            source_docs = response.metadata.sourceDocs or []
            
            print(f"   -> Response: {ai_reply[:100]}...")
            print(f"   -> Sources: {len(source_docs)} docs")

            # 2. Judge the Response
            # We ask the Judge to evaluate if the answer is grounded and helpful
            prompt = f"""
            You are an expert AI evaluator. Grade the following AI response.
            
            User Question: "{case['question']}"
            Expected Topic: "{case['expected_topic']}"
            AI Response: "{ai_reply}"
            
            Criteria:
            1. Is the language correct? (Expected: {case['language']})
            2. Is the answer relevant to the expected topic?
            3. If it's an out-of-scope question (like Capital of France), did the AI politely refuse?
            
            Output strictly in this format:
            SCORE: [1-5]
            REASON: [Short explanation]
            """
            
            judge_res = await asyncio.to_thread(judge_model.generate_content, prompt)
            grade = judge_res.text.strip()
            print(f"   -> JUDGE: {grade}\n")
            
        except Exception as e:
            print(f"   -> ERROR: {e}\n")

if __name__ == "__main__":
    asyncio.run(run_evaluation())
