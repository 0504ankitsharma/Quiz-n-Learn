import streamlit as st
from generate import generate_mcqs, setup_qa_chain
from export import export_to_doc
from utils import extract_text_from_pdf, calculate_score, get_grade

# Set page configuration at the top of the script
st.set_page_config(
    page_title="MCQ Generator & Document QA",
    layout="wide",
    page_icon="📚",
)

# Custom CSS for better UI
def load_custom_css():
    st.markdown("""
        <style>
        /* Background and font styling */
        body {
            background-color: #f4f8fb;
            font-family: 'Arial', sans-serif;
            color: #333;
        }

        /* Title styling */
        .title {
            color: #2d87bb;
            font-weight: 700;
            text-align: center;
        }

        /* Sidebar styling */
        [data-testid="stSidebar"] {
            background-color: #2d87bb;
            color: white;
        }
        [data-testid="stSidebar"] .block-container {
            padding-top: 2rem;
        }

        /* Button effects */
        button {
            background-color: #2d87bb;
            border: none;
            color: white;
            padding: 10px 20px;
            font-size: 16px;
            border-radius: 5px;
            cursor: pointer;
        }
        button:hover {
            background-color: #1e5c86;
        }

        /* Form styling */
        .stForm {
            background-color: white;
            border: 1px solid #ddd;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
        }

        /* Metrics */
        .metric-container {
            display: flex;
            justify-content: space-between;
        }

        /* Chat history styling */
        .chat-history {
            margin-top: 20px;
            padding: 15px;
            border: 1px solid #ddd;
            border-radius: 10px;
            background: #f9f9f9;
        }
        .chat-history p {
            margin: 0;
        }
        .chat-history .question {
            font-weight: bold;
            color: #2d87bb;
        }
        .chat-history .answer {
            color: #444;
        }

        /* Tabs styling */
        .stTabs [role="tab"] {
            background-color: #2d87bb;
            color: white;
            font-weight: bold;
            border-radius: 5px;
            margin-right: 5px;
        }
        .stTabs [role="tab"]:hover {
            background-color: #1e5c86;
        }
        .stTabs [role="tab"][aria-selected="true"] {
            background-color: #1e5c86;
        }
        </style>
    """, unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables."""
    if 'user_answers' not in st.session_state:
        st.session_state.user_answers = [None] * 5
    if 'submitted' not in st.session_state:
        st.session_state.submitted = False
    if 'qa_chain' not in st.session_state:
        st.session_state.qa_chain = None
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'mcqs' not in st.session_state:
        st.session_state.mcqs = []

def display_mcq(mcqs):
    """Display multiple-choice questions and handle submission."""
    st.markdown("### 📝 Multiple Choice Questions")
    
    if not mcqs:
        st.info("No MCQs available. Generate some using the sidebar!")
        return

    # Ensure session state user_answers matches the number of MCQs
    if len(st.session_state.user_answers) != len(mcqs):
        st.session_state.user_answers = [None] * len(mcqs)

    with st.form("mcq_form", clear_on_submit=False):
        for idx, mcq in enumerate(mcqs):
            st.markdown(f"**{idx + 1}. {mcq['question']}**")
            options = ["Select an answer"] + mcq['choices']  # Add placeholder option
            choice = st.radio(
                f"Question {idx + 1}:",
                options,
                index=0 if st.session_state.user_answers[idx] is None else mcq['choices'].index(st.session_state.user_answers[idx]) + 1,
                key=f"q_{idx}"
            )
            
            # Update session state only if a valid answer is selected
            st.session_state.user_answers[idx] = choice if choice != "Select an answer" else None
            
            st.markdown("---")
        
        # Submit and Reset Buttons
        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button("Submit Answers", use_container_width=True)
        with col2:
            reset = st.form_submit_button("Reset", use_container_width=True)

        # Handle form submission
        if submitted:
            st.session_state.submitted = True
        if reset:
            st.session_state.user_answers = [None] * len(mcqs)
            st.session_state.submitted = False
            st.experimental_rerun()

    # Display results if submitted
    if st.session_state.submitted:
        st.markdown("### 📊 Results")
        earned_points, total_points, percentage = calculate_score(mcqs, st.session_state.user_answers)
        grade, message = get_grade(percentage)

        # Display summary metrics
        col1, col2, col3 = st.columns(3)
        col1.metric("Points", f"{earned_points}/{total_points}")
        col2.metric("Percentage", f"{percentage:.1f}%")
        col3.metric("Grade", grade)
        
        st.markdown(f"### {message}")
        
        # Detailed question-wise feedback
        for idx, mcq in enumerate(mcqs):
            correct_answer = mcq['answer']
            user_answer = st.session_state.user_answers[idx]
            if user_answer == correct_answer:
                st.success(f"Q{idx + 1}: ✅ Correct! ({correct_answer})")
            else:
                st.error(f"Q{idx + 1}: ❌ Your answer: {user_answer or 'Not answered'}")
                st.info(f"Correct answer: {correct_answer}")


def display_qa_interface():
    st.markdown('<h2 class="title">💭 Document Q&A</h2>', unsafe_allow_html=True)
    if st.session_state.qa_chain is None:
        st.info("Please upload a document first to enable Q&A.")
        return

    user_question = st.text_input("Ask a question about the document:")
    if user_question:
        with st.spinner("Fetching answer..."):
            result = st.session_state.qa_chain({"question": user_question})
            st.session_state.chat_history.append((user_question, result['answer']))

    if st.session_state.chat_history:
        st.markdown('<div class="chat-history">', unsafe_allow_html=True)
        for q, a in st.session_state.chat_history:
            st.markdown(f'<p class="question">Q: {q}</p>', unsafe_allow_html=True)
            st.markdown(f'<p class="answer">A: {a}</p>', unsafe_allow_html=True)
            st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

def main():
    """Main function to handle the app's layout and functionality."""
    load_custom_css()
    initialize_session_state()

    with st.sidebar:
        st.title("📚 Quiz and Learn")
        st.markdown("Upload a PDF to generate MCQs and ask questions about it.")
        uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

    if uploaded_file:
        pdf_text = extract_text_from_pdf(uploaded_file)
        if st.sidebar.button("Generate Questions"):
            with st.spinner("Processing..."):
                st.session_state.mcqs = generate_mcqs(pdf_text)
                st.session_state.qa_chain = setup_qa_chain(pdf_text)

    if uploaded_file:
        tabs = st.tabs(["📝 Quiz", "❓ Q&A"])
        with tabs[0]:
            display_mcq(st.session_state.mcqs)
        with tabs[1]:
            display_qa_interface()

if __name__ == "__main__":
    main()
