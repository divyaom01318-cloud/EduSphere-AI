import streamlit as st
import os
import json
from google import genai
from google.genai import types
from google.genai.errors import APIError
from pydantic import BaseModel, Field
from typing import List
import PyPDF2
# ==========================================
# PAGE CONFIGURATION & THEME
# ==========================================
st.set_page_config(
    page_title="EduSphere AI - Your Study Companion",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)
# Custom CSS for Premium Glassmorphism and Modern Aesthetics
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');
    
    /* Global Styles */
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    /* Main App Container */
    .stApp {
        background-color: #0b0f19;
        color: #e2e8f0;
    }
    
    /* Glassmorphic Header & Banner */
    .hero-container {
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.15) 0%, rgba(168, 85, 247, 0.15) 100%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 20px;
        padding: 40px;
        margin-bottom: 30px;
        text-align: center;
        backdrop-filter: blur(10px);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
    }
    
    .hero-title {
        background: linear-gradient(90deg, #818cf8 0%, #c084fc 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem;
        font-weight: 700;
        margin-bottom: 10px;
    }
    
    .hero-subtitle {
        color: #94a3b8;
        font-size: 1.2rem;
        font-weight: 300;
    }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #0f172a !important;
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    /* Styled Cards */
    .card {
        background: rgba(30, 41, 59, 0.4);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 20px;
        backdrop-filter: blur(8px);
    }
    
    /* Flip Card Styles */
    .flip-card {
        background-color: transparent;
        width: 100%;
        height: 280px;
        perspective: 1000px;
        margin: 20px auto;
        cursor: pointer;
    }
    .flip-card-inner {
        position: relative;
        width: 100%;
        height: 100%;
        text-align: center;
        transition: transform 0.8s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        transform-style: preserve-3d;
    }
    /* We trigger flip on a class. Storing state in Streamlit allows toggling this class */
    .flip-card.flipped .flip-card-inner {
        transform: rotateY(180deg);
    }
    .flip-card-front, .flip-card-back {
        position: absolute;
        width: 100%;
        height: 100%;
        -webkit-backface-visibility: hidden;
        backface-visibility: hidden;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-direction: column;
        padding: 30px;
        border-radius: 20px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.3);
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    .flip-card-front {
        background: linear-gradient(135deg, #1e1b4b 0%, #312e81 100%);
        color: #e0e7ff;
    }
    .flip-card-back {
        background: linear-gradient(135deg, #311042 0%, #581c87 100%);
        color: #fae8ff;
        transform: rotateY(180deg);
    }
    
    .card-label {
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 2px;
        color: #a5b4fc;
        margin-bottom: 15px;
    }
    
    .card-content {
        font-size: 1.4rem;
        font-weight: 500;
        line-height: 1.5;
    }
    
    .hint-text {
        font-size: 0.8rem;
        color: #64748b;
        margin-top: 20px;
    }
    /* Buttons and Inputs */
    .stButton>button {
        background: linear-gradient(90deg, #4f46e5 0%, #7c3aed 100%);
        color: white;
        border: none;
        padding: 10px 24px;
        border-radius: 10px;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(79, 70, 229, 0.3);
    }
    
    .stButton>button:hover {
        background: linear-gradient(90deg, #6366f1 0%, #8b5cf6 100%);
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(79, 70, 229, 0.4);
    }
    
    /* Quiz styling */
    .quiz-question {
        background: rgba(15, 23, 42, 0.6);
        padding: 20px;
        border-radius: 12px;
        border-left: 5px solid #6366f1;
        margin-bottom: 20px;
    }
    
    .explanation-box {
        background: rgba(16, 185, 129, 0.1);
        border: 1px solid rgba(16, 185, 129, 0.3);
        border-radius: 8px;
        padding: 15px;
        margin-top: 10px;
    }
    
    .explanation-box-error {
        background: rgba(239, 68, 68, 0.1);
        border: 1px solid rgba(239, 68, 68, 0.3);
        border-radius: 8px;
        padding: 15px;
        margin-top: 10px;
    }
</style>
""", unsafe_allow_html=True)
# ==========================================
# PYDANTIC SCHEMAS FOR STRUCTURED AI OUTPUT
# ==========================================
class Flashcard(BaseModel):
    front: str = Field(description="The term, concept, or question to display on the front of the flashcard")
    back: str = Field(description="The explanation, answer, or definition to display on the back of the flashcard")
class FlashcardDeck(BaseModel):
    cards: List[Flashcard]
class QuizQuestion(BaseModel):
    question: str = Field(description="The quiz question text")
    options: List[str] = Field(description="Exactly 4 multiple choice options")
    correct_answer: str = Field(description="The exact string matching the correct option")
    explanation: str = Field(description="Detailed explanation of why this answer is correct")
class Quiz(BaseModel):
    questions: List[QuizQuestion]
# ==========================================
# HELPER FUNCTIONS
# ==========================================
def extract_text_from_pdf(pdf_file) -> str:
    """Extracts text from an uploaded PDF file."""
    try:
        reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in reader.pages:
            content = page.extract_text()
            if content:
                text += content + "\n"
        return text
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
        return ""
def get_gemini_client(api_key: str):
    """Initializes and returns the Google GenAI client."""
    if not api_key:
        return None
    return genai.Client(api_key=api_key)
# ==========================================
# SIDEBAR / SETTINGS
# ==========================================
with st.sidebar:
    st.image("https://img.icons8.com/color/144/graduation-cap.png", width=80)
    st.title("EduSphere Settings")
    st.markdown("---")
    
    # API Key Input
    # Check if API Key exists in environment variables first
    env_api_key = os.environ.get("GEMINI_API_KEY", "")
    api_key_input = st.text_input(
        "Enter Gemini API Key",
        value=env_api_key,
        type="password",
        help="Get a free key from Google AI Studio (aistudio.google.com)"
    )
    
    # Provide helpful link to get API key
    if not api_key_input:
        st.info("🔑 [Get a Free Gemini API Key here](https://aistudio.google.com/)")
        
    st.markdown("---")
    st.markdown("### Navigation")
    menu = st.radio(
        "Go to:",
        ["✨ Concept Explainer", "📝 Note Summarizer", "🗂️ Interactive Flashcards", "✍️ Smart Quizzes"]
    )
    
    st.markdown("---")
    st.markdown("### About EduSphere")
    st.caption(
        "EduSphere is an AI-powered learning environment designed to simplify student learning using "
        "advanced Gemini 2.5 models. Generate summaries, explanations, flashcards, and quizzes in seconds."
    )
# Establish Client
client = get_gemini_client(api_key_input)
# Check if client is initialized
if not client:
    st.markdown("""
    <div class="hero-container">
        <div class="hero-title">🎓 EduSphere AI</div>
        <div class="hero-subtitle">Your Ultimate Personal Study Assistant</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.warning("⚠️ **Gemini API Key Required**")
    st.markdown("""
    To start using EduSphere, please obtain an API key from Google AI Studio and paste it in the sidebar.
    
    **How to get started:**
    1. Go to [Google AI Studio](https://aistudio.google.com/).
    2. Click on **Create API Key**.
    3. Copy the key and paste it into the **Enter Gemini API Key** input in the left sidebar.
    """)
    st.stop()
# ==========================================
# APP BANNER (When API key is present)
# ==========================================
st.markdown(f"""
<div class="hero-container">
    <div class="hero-title">🎓 EduSphere AI</div>
    <div class="hero-subtitle">Topic: Active | Navigation: {menu[2:]}</div>
</div>
""", unsafe_allow_html=True)
# ==========================================
# MENU 1: CONCEPT EXPLAINER
# ==========================================
if menu == "✨ Concept Explainer":
    st.markdown("### ✨ Simplify Complex Concepts")
    st.markdown("Type in any topic, select your learning stage, and let EduSphere explain it clearly with helpful analogies.")
    col1, col2 = st.columns([2, 1])
    with col1:
        concept_input = st.text_input(
            "What topic do you want to learn today?",
            placeholder="e.g., Quantum Computing, Photosynthesis, Neural Networks, Inflation"
        )
        
    with col2:
        learning_stage = st.selectbox(
            "Target Audience Level",
            [
                "👶 Like I'm 5 (Super Simple)",
                "🎒 High School Student",
                "🎓 College Undergraduate",
                "🧠 Industry Expert (Advanced)"
            ]
        )
    # Advanced styling/configuration toggles
    with st.expander("🛠️ Advanced Settings"):
        col_adv1, col_adv2 = st.columns(2)
        with col_adv1:
            tone = st.selectbox("Tone of explanation", ["Friendly & Encouraging", "Highly Technical", "Humorous", "Socratic / Inquiry-based"])
        with col_adv2:
            include_analogy = st.checkbox("Force creation of a real-world analogy", value=True)
    if st.button("Explain Concept"):
        if not concept_input:
            st.error("Please enter a concept or topic.")
        else:
            with st.spinner("Decoding topic and building explanations..."):
                prompt = f"""
                Explain the topic/concept: "{concept_input}"
                Target Audience: {learning_stage}
                Tone: {tone}
                Real-world Analogy Required: {include_analogy}
                
                Please structure the explanation with:
                1. A high-level overview in simple terms.
                2. A creative real-world analogy.
                3. Key components or ideas simplified.
                4. A 'Quick Takeaway' section.
                """
                
                try:
                    response = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=prompt
                    )
                    
                    st.markdown("### 💡 Explanation")
                    st.markdown(f"<div class='card'>{response.text}</div>", unsafe_allow_html=True)
                except APIError as e:
                    st.error(f"Gemini API Error: {e}")
                except Exception as e:
                    st.error(f"An unexpected error occurred: {e}")
# ==========================================
# MENU 2: NOTE SUMMARIZER
# ==========================================
elif menu == "📝 Note Summarizer":
    st.markdown("### 📝 Smart Note Summarizer")
    st.markdown("Paste your study notes or upload a PDF chapter. EduSphere will distill the contents into structured, easy-to-read study guides.")
    input_mode = st.radio("Choose input format:", ["Paste Text", "Upload PDF"])
    notes_text = ""
    if input_mode == "Paste Text":
        notes_text = st.text_area(
            "Paste your notes/lecture transcripts here:",
            height=250,
            placeholder="Paste your study materials, lecture scripts, or articles..."
        )
    else:
        uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])
        if uploaded_file is not None:
            with st.spinner("Extracting text from PDF..."):
                notes_text = extract_text_from_pdf(uploaded_file)
                if notes_text:
                    st.success("Successfully extracted text from PDF!")
                    with st.expander("Preview Extracted Text"):
                        st.text(notes_text[:1000] + "...")
    # Options
    summary_type = st.select_slider(
        "Summary Detail Level",
        options=["Bullet Points Only", "Standard Summary", "Comprehensive Guide"]
    )
    if st.button("Generate Summary"):
        if not notes_text.strip():
            st.error("Please provide text or upload a PDF to summarize.")
        else:
            with st.spinner("Distilling notes..."):
                prompt = f"""
                Analyze and summarize the following study notes.
                Format Style: {summary_type}
                
                Generate a response containing:
                1. Executive Summary: A 3-sentence summary of the core message.
                2. Key Takeaways: Bulleted list of the most important concepts.
                3. Glossary: Definitions of key terms/vocabulary found in the text.
                4. Action Items/Study Questions: 3 self-reflection questions to test understanding.
                
                Notes Content:
                {notes_text}
                """
                
                try:
                    response = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=prompt
                    )
                    st.markdown("### 📓 Study Summary Guide")
                    st.markdown(f"<div class='card'>{response.text}</div>", unsafe_allow_html=True)
                except APIError as e:
                    st.error(f"Gemini API Error: {e}")
                except Exception as e:
                    st.error(f"An unexpected error occurred: {e}")
# ==========================================
# MENU 3: INTERACTIVE FLASHCARDS
# ==========================================
elif menu == "🗂️ Interactive Flashcards":
    st.markdown("### 🗂️ Smart Flashcard Generator")
    st.markdown("Generate interactive digital flashcards from any topic or document to boost active recall.")
    flashcard_source = st.radio("Source material:", ["Specific Topic/Keyword", "Custom Study Notes / PDF Text"])
    source_content = ""
    if flashcard_source == "Specific Topic/Keyword":
        source_content = st.text_input("Enter topic for flashcards:", placeholder="e.g., Mitosis, World War I Causes, Python Decorators")
    else:
        source_content = st.text_area("Paste text to extract flashcards from:", height=150, placeholder="Paste text here...")
    num_cards = st.slider("Number of flashcards to generate", 3, 10, 5)
    # State management for card deck
    if "flashcards" not in st.session_state:
        st.session_state.flashcards = []
        st.session_state.card_index = 0
        st.session_state.card_flipped = False
        st.session_state.last_source = ""
    if st.button("Generate Flashcards"):
        if not source_content.strip():
            st.error("Please enter a topic or paste study text.")
        else:
            with st.spinner("Creating your custom flashcard deck..."):
                prompt = f"""
                Generate a list of exactly {num_cards} flashcards from this input: "{source_content}".
                For each flashcard, provide a front (term, prompt, or question) and a back (clear, concise answer or explanation).
                Keep the back contents brief and easy to memorize.
                """
                
                try:
                    response = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            response_schema=FlashcardDeck,
                        )
                    )
                    
                    data = json.loads(response.text)
                    st.session_state.flashcards = data.get("cards", [])
                    st.session_state.card_index = 0
                    st.session_state.card_flipped = False
                    st.session_state.last_source = source_content
                except APIError as e:
                    st.error(f"Gemini API Error: {e}")
                except Exception as e:
                    st.error(f"An unexpected error occurred: {e}")
    # Render Deck if it exists
    if st.session_state.flashcards:
        cards = st.session_state.flashcards
        idx = st.session_state.card_index
        total_cards = len(cards)
        
        st.markdown(f"**Card {idx + 1} of {total_cards}**")
        
        # HTML/CSS representation of the card
        # Using a st.session_state variable to add the 'flipped' class
        flipped_class = "flipped" if st.session_state.card_flipped else ""
        
        card_html = f"""
        <div class="flip-card {flipped_class}">
            <div class="flip-card-inner">
                <div class="flip-card-front">
                    <div class="card-label">Front (Question / Concept)</div>
                    <div class="card-content">{cards[idx]['front']}</div>
                    <div class="hint-text">💡 Click 'Flip Card' below to see the answer</div>
                </div>
                <div class="flip-card-back">
                    <div class="card-label">Back (Answer / Definition)</div>
                    <div class="card-content">{cards[idx]['back']}</div>
                    <div class="hint-text">🔄 Click 'Flip Card' to see the question again</div>
                </div>
            </div>
        </div>
        """
        st.markdown(card_html, unsafe_allow_html=True)
        
        # Controls
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            if st.button("⬅️ Previous Card", disabled=(idx == 0)):
                st.session_state.card_index -= 1
                st.session_state.card_flipped = False
                st.rerun()
                
        with col2:
            if st.button("🔄 Flip Card"):
                st.session_state.card_flipped = not st.session_state.card_flipped
                st.rerun()
                
        with col3:
            if st.button("Next Card ➡️", disabled=(idx == total_cards - 1)):
                st.session_state.card_index += 1
                st.session_state.card_flipped = False
                st.rerun()
                
        # Reset deck helper
        st.markdown("---")
        if st.button("Clear Deck"):
            st.session_state.flashcards = []
            st.session_state.card_index = 0
            st.session_state.card_flipped = False
            st.rerun()
# ==========================================
# MENU 4: SMART QUIZZES
# ==========================================
elif menu == "✍️ Smart Quizzes":
    st.markdown("### ✍️ AI-Generated Practice Quizzes")
    st.markdown("Generate dynamic multiple-choice quizzes to test your understanding. Get immediate feedback with clear explanations.")
    quiz_source = st.radio("Generate quiz from:", ["A Specific Topic", "Paste Notes / PDF text"])
    source_content = ""
    if quiz_source == "A Specific Topic":
        source_content = st.text_input("Enter quiz topic:", placeholder="e.g., Cellular Respiration, Newton's Laws, SQL Joins")
    else:
        source_content = st.text_area("Paste text to generate questions from:", height=150, placeholder="Paste text here...")
    num_questions = st.slider("Select number of questions", 3, 10, 5)
    # State management for quizzes
    if "quiz" not in st.session_state:
        st.session_state.quiz = None
        st.session_state.quiz_submitted = False
        st.session_state.user_answers = {}
    if st.button("Generate Quiz"):
        if not source_content.strip():
            st.error("Please provide a topic or study notes.")
        else:
            with st.spinner("Generating custom questions and validating keys..."):
                prompt = f"""
                Create a quiz with exactly {num_questions} multiple choice questions from this topic or text: "{source_content}".
                For each question:
                - Formulate a clear question.
                - Create exactly 4 options.
                - Select the correct answer (matching one of the options exactly).
                - Write a detailed explanation of why it is correct.
                """
                
                try:
                    response = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            response_schema=Quiz,
                        )
                    )
                    
                    st.session_state.quiz = json.loads(response.text)
                    st.session_state.quiz_submitted = False
                    st.session_state.user_answers = {}
                except APIError as e:
                    st.error(f"Gemini API Error: {e}")
                except Exception as e:
                    st.error(f"An unexpected error occurred: {e}")
    # Display Quiz
    if st.session_state.quiz:
        questions = st.session_state.quiz.get("questions", [])
        
        st.markdown("---")
        st.markdown("### 📋 Practice Quiz")
        
        # Form for submission
        for i, q in enumerate(questions):
            st.markdown(f"<div class='quiz-question'><strong>Question {i+1}:</strong> {q['question']}</div>", unsafe_allow_html=True)
            
            # Use radio button for options
            options = q['options']
            
            # Store answer state
            key = f"q_{i}"
            selected_option = st.radio(
                "Select your answer:",
                options,
                key=key,
                index=None if key not in st.session_state.user_answers else options.index(st.session_state.user_answers[key])
            )
            
            if selected_option:
                st.session_state.user_answers[key] = selected_option
                
            # If submitted, show feedback
            if st.session_state.quiz_submitted:
                correct_ans = q['correct_answer']
                user_ans = st.session_state.user_answers.get(key, None)
                
                if user_ans == correct_ans:
                    st.success("✅ **Correct!**")
                    st.markdown(f"<div class='explanation-box'><strong>Explanation:</strong> {q['explanation']}</div>", unsafe_allow_html=True)
                else:
                    st.error(f"❌ **Incorrect.** The correct answer is: *{correct_ans}*")
                    st.markdown(f"<div class='explanation-box-error'><strong>Explanation:</strong> {q['explanation']}</div>", unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
        # Submit / Score calculation
        if not st.session_state.quiz_submitted:
            if st.button("Submit Answers"):
                # Check if all questions are answered
                if len(st.session_state.user_answers) < len(questions):
                    st.warning("Please answer all questions before submitting.")
                else:
                    st.session_state.quiz_submitted = True
                    st.rerun()
        else:
            # Calculate score
            score = 0
            for i, q in enumerate(questions):
                key = f"q_{i}"
                if st.session_state.user_answers.get(key) == q['correct_answer']:
                    score += 1
            
            st.markdown(f"### 🎉 Quiz Finished! Your Score: **{score} / {len(questions)}**")
            
            if st.button("Retake Quiz / New Quiz"):
                st.session_state.quiz = None
                st.session_state.quiz_submitted = False
                st.session_state.user_answers = {}
                st.rerun()