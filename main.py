
from pydantic import BaseModel
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pymupdf
import random
import re

# ==========================================
# APPLICATION SETUP
# ==========================================

app = FastAPI(
    title="AI Study Helper",
    description="Your Personal AI Learning Assistant",
    version="1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "null"
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==========================================
# TEMPORARY STORAGE
# ==========================================

uploaded_text = ""
generated_quiz = []
last_quiz_results = []
quiz_history = []


# ==========================================
# HOME ENDPOINT
# ==========================================

@app.get("/")
def home():

    return {
        "message": "Welcome to AI Study Helper!",
        "status": "Backend is running successfully"
    }


# ==========================================
# FEATURE 1: SMART NOTES UPLOAD
# ==========================================

@app.post("/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)):

    global uploaded_text, generated_quiz

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Please upload a PDF file."
        )

    contents = await file.read()

    try:

        document = pymupdf.open(
            stream=contents,
            filetype="pdf"
        )

        extracted_text = ""

        for page_number, page in enumerate(document, start=1):

            extracted_text += (
                f"\n--- Page {page_number} ---\n"
                + page.get_text()
            )

        page_count = len(document)

        document.close()

        if not extracted_text.strip():

            raise HTTPException(
                status_code=400,
                detail="No readable text found in this PDF."
            )

        uploaded_text = extracted_text
        generated_quiz = []

        return {
            "filename": file.filename,
            "total_pages": page_count,
            "message": "PDF uploaded and processed successfully!",
            "extracted_text": extracted_text
        }

    except HTTPException:
        raise

    except Exception:

        raise HTTPException(
            status_code=400,
            detail="Unable to process this PDF."
        )


# ==========================================
# FEATURE 2: BASIC DOUBT SOLVER
# ==========================================


# ==========================================
# FEATURE 2: IMPROVED DOUBT SOLVER
# ==========================================

class QuestionRequest(BaseModel):
    question: str


def get_keywords(text):

    stopwords = {
        "the", "is", "are", "was", "were", "what",
        "why", "how", "when", "where", "which",
        "who", "whom", "this", "that", "these",
        "those", "a", "an", "and", "or", "but",
        "in", "on", "at", "to", "of", "for",
        "from", "with", "by", "about", "explain",
        "tell", "me", "please", "can", "you",
        "does", "do", "did", "it", "its"
    }

    words = re.findall(r"\b[a-zA-Z0-9]+\b", text.lower())

    return [
        word for word in words
        if word not in stopwords and len(word) > 1
    ]



def find_relevant_sentences(question, document_text):

    question_words = set(get_keywords(question))

    if not question_words:
        return []

    # Normalize common singular/plural forms
    def normalize_word(word):
        if word.endswith("ies") and len(word) > 4:
            return word[:-3] + "y"
        if word.endswith("s") and not word.endswith("ss") and len(word) > 3:
            return word[:-1]
        return word

    question_words = {
        normalize_word(word) for word in question_words
    }

    # Split document into sentences
    sentences = re.split(
        r"(?<=[.!?])\s+|\n+",
        document_text
    )

    scored_sentences = []

    definition_phrases = [
        " is a ",
        " is an ",
        " refers to ",
        " defined as ",
        " is called ",
        " means "
    ]

    for sentence in sentences:

        sentence = sentence.strip()

        if len(sentence) < 25:
            continue

        sentence_words = {
            normalize_word(word)
            for word in get_keywords(sentence)
        }

        matches = question_words.intersection(sentence_words)

        if not matches:
            continue

        score = len(matches) / len(question_words)

        sentence_lower = " " + sentence.lower() + " "

        # Prioritize exact topic phrases
        normalized_sentence = " ".join(
            normalize_word(word)
            for word in get_keywords(sentence)
        )

        normalized_question = " ".join(sorted(question_words))

        if all(word in sentence_words for word in question_words):
            score += 1

        # Prioritize sentences that define a concept
        if any(phrase in sentence_lower for phrase in definition_phrases):
            score += 0.75

        scored_sentences.append({
            "sentence": sentence,
            "score": score
        })

    scored_sentences.sort(
        key=lambda item: item["score"],
        reverse=True
    )

    return [
        item["sentence"]
        for item in scored_sentences[:3]
        if item["score"] >= 0.5
    ]

@app.post("/ask")
def ask_question(request: QuestionRequest):

    if not uploaded_text.strip():

        raise HTTPException(
            status_code=400,
            detail="Please upload your notes PDF first."
        )

    question = request.question.strip()

    if not question:

        raise HTTPException(
            status_code=400,
            detail="Please enter a question."
        )

    relevant_sentences = find_relevant_sentences(
        question,
        uploaded_text
    )

    if not relevant_sentences:

        return {
            "question": question,
            "answer": (
                "I couldn't find sufficiently relevant information "
                "in your uploaded notes. Try using specific keywords "
                "from your topic."
            )
        }

    return {
        "question": question,
        "answer": (
            "I found these relevant passages in your notes:\n\n"
            + "\n\n".join(
                f"{index}. {sentence}"
                for index, sentence in enumerate(
                    relevant_sentences,
                    start=1
                )
            )
        )
    }

# ==========================================
# QUIZ REQUEST MODELS
# ==========================================

class QuizRequest(BaseModel):
    num_questions: int = 5


class QuizSubmission(BaseModel):
    answers: list[int]


# ==========================================
# FEATURE 3: TOPIC DETECTION
# ==========================================

def detect_topic(sentence):

    text = sentence.lower()

    topic_keywords = {

        "Inverted Files": [
            "inverted file",
            "inverted index"
        ],

        "Query Operations": [
            "query",
            "boolean operators"
        ],

        "Dictionary": [
            "dictionary",
            "encyclopedia"
        ],

        "B-Trees and Digital Trees": [
            "b-tree",
            "digital tree"
        ],

        "Substring Operations": [
            "substring",
            "characters"
        ],

        "Information Retrieval": [
            "information retrieval",
            "ir system"
        ],
    }

    for topic, keywords in topic_keywords.items():

        if any(keyword in text for keyword in keywords):
            return topic

    return "General Concepts"


# ==========================================
# FEATURE 4: INTELLIGENT QUIZ GENERATOR
# ==========================================

# ==========================================
# FEATURE 4: IMPROVED QUIZ GENERATOR
# ==========================================

def clean_quiz_text(text):

    # Remove page markers
    text = re.sub(r"--- Page \d+ ---", " ", text)

    # Remove common bullet symbols
    text = re.sub(r"[•▪■]", " ", text)

    # Normalize spaces
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def extract_definitions(text):

    cleaned_text = clean_quiz_text(text)

    # Split into individual sentences
    sentences = re.split(
        r"(?<=[.!?])\s+",
        cleaned_text
    )

    definitions = []

    patterns = [
        r"^(?:an?|the)\s+(.{2,70}?)\s+(?:is|are)\s+(.+)$",
        r"^(.{2,70}?)\s+(?:refers to|is defined as|means)\s+(.+)$"
    ]

    for sentence in sentences:

        sentence = sentence.strip()

        if len(sentence.split()) < 7:
            continue

        for pattern in patterns:

            match = re.search(
                pattern,
                sentence,
                re.IGNORECASE
            )

            if match:

                concept = match.group(1).strip(" ,:-")
                explanation = match.group(2).strip(" ,:-")

                # Avoid very long or invalid concepts
                if len(concept.split()) > 8:
                    continue

                if len(explanation.split()) < 4:
                    continue

                definitions.append({
                    "concept": concept,
                    "answer": explanation,
                    "full_sentence": sentence
                })

                break

    # Remove duplicate concepts
    unique_definitions = []
    seen = set()

    for item in definitions:

        key = item["concept"].lower()

        if key not in seen:
            seen.add(key)
            unique_definitions.append(item)

    return unique_definitions


def generate_definition_questions(definitions, count):

    questions = []

    selected_definitions = random.sample(
        definitions,
        min(count, len(definitions))
    )

    for index, definition in enumerate(
        selected_definitions,
        start=1
    ):

        correct_answer = definition["answer"]

        # Use other definitions as distractors
        other_answers = [
            item["answer"]
            for item in definitions
            if item["concept"].lower()
            != definition["concept"].lower()
            and item["answer"] != correct_answer
        ]

        if len(other_answers) < 3:
            continue

        distractors = random.sample(other_answers, 3)

        options = distractors + [correct_answer]

        random.shuffle(options)

        questions.append({

            "question_number": index,

            "topic": detect_topic(
                definition["concept"] + " " + correct_answer
            ),

            "question": (
                f"According to your notes, what is "
                f"{definition['concept']}?"
            ),

            "options": options,

            "correct_index": options.index(correct_answer)
        })

    return questions


@app.post("/generate-quiz")
def generate_quiz(request: QuizRequest):

    global generated_quiz

    if not uploaded_text.strip():

        raise HTTPException(
            status_code=400,
            detail="Please upload your notes PDF first."
        )

    count = max(1, min(request.num_questions, 10))

    definitions = extract_definitions(uploaded_text)

    if len(definitions) < 4:

        raise HTTPException(
            status_code=400,
            detail=(
                "Not enough clear definitions were found "
                "in your PDF to generate a reliable quiz. "
                "Please upload notes containing more definitions."
            )
        )

    generated_quiz = generate_definition_questions(
        definitions,
        count
    )

    if not generated_quiz:

        raise HTTPException(
            status_code=400,
            detail="Unable to generate questions from these notes."
        )

    return {

        "message": "Quiz generated successfully!",

        "total_questions": len(generated_quiz),

        "quiz": [
            {
                "question_number": q["question_number"],
                "question": q["question"],
                "options": q["options"]
            }
            for q in generated_quiz
        ]
    }

# ==========================================
# QUIZ SUBMISSION AND AUTOMATIC SCORING
# ==========================================

@app.post("/submit-quiz")

@app.post("/submit-quiz")
def submit_quiz(submission: QuizSubmission):

    global last_quiz_results, quiz_history

    if not generated_quiz:
        raise HTTPException(
            status_code=400,
            detail="Please generate a quiz first."
        )

    if len(submission.answers) != len(generated_quiz):
        raise HTTPException(
            status_code=400,
            detail="Please submit an answer for every question."
        )

    score = 0
    results = []

    for question, answer in zip(
        generated_quiz,
        submission.answers
    ):

        if answer < 0 or answer >= len(question["options"]):
            raise HTTPException(
                status_code=400,
                detail="Invalid option index."
            )

        correct_index = question["correct_index"]

        correct = answer == correct_index

        if correct:
            score += 1

        results.append({

            "question_number": question["question_number"],

            "topic": question["topic"],

            "question": question["question"],

            "your_answer": question["options"][answer],

            "correct_answer": question["options"][correct_index],

            "is_correct": correct,

            "explanation": question.get(
                "explanation",
                "Please refer to the relevant section of your uploaded notes."
            ),

            "feedback": (
                "Great job! Your answer is correct."
                if correct
                else "Not quite! Review the correct answer and explanation."
            )
        })

    total_questions = len(generated_quiz)

    percentage = (score / total_questions) * 100

    if percentage >= 80:
        feedback = "Excellent work! You understand these notes well."

    elif percentage >= 50:
        feedback = "Good effort! Revise a few topics and try again."

    else:
        feedback = "Keep practising! Review your notes and retry."

    last_quiz_results = results

    quiz_history.append(results)

    return {

        "total_questions": total_questions,

        "correct_answers": score,

        "wrong_answers": total_questions - score,

        "percentage": round(percentage, 2),

        "feedback": feedback,

        "results": results
    }


# ==========================================
# FEATURE 5: LEARNING GAP DETECTION
# ==========================================

@app.get("/learning-gaps")
def learning_gaps():

    if not last_quiz_results:

        raise HTTPException(
            status_code=400,
            detail="Please complete and submit a quiz first."
        )

    topic_performance = {}

    for result in last_quiz_results:

        topic = result["topic"]

        if topic not in topic_performance:

            topic_performance[topic] = {
                "correct": 0,
                "total": 0
            }

        topic_performance[topic]["total"] += 1

        if result["is_correct"]:
            topic_performance[topic]["correct"] += 1

    learning_gaps = []

    for topic, data in topic_performance.items():

        accuracy = (
            data["correct"] / data["total"]
        ) * 100

        if accuracy >= 80:

            status = "Strong"

        elif accuracy < 50:

            status = "Weak"

        else:

            status = "Needs Improvement"

        learning_gaps.append({

            "topic": topic,

            "accuracy": round(accuracy, 2),

            "status": status,

            "correct_answers": data["correct"],

            "total_questions": data["total"]
        })

    return {

        "message": "Learning gaps detected successfully!",

        "learning_gaps": learning_gaps
    }


# ==========================================
# FEATURE 6: PERSONALISED LEARNING ROADMAP
# ==========================================

@app.get("/learning-roadmap")
def learning_roadmap():

    if not last_quiz_results:

        raise HTTPException(
            status_code=400,
            detail="Please complete and submit a quiz first."
        )

    topic_performance = {}

    for result in last_quiz_results:

        topic = result["topic"]

        if topic not in topic_performance:

            topic_performance[topic] = {
                "correct": 0,
                "total": 0
            }

        topic_performance[topic]["total"] += 1

        if result["is_correct"]:
            topic_performance[topic]["correct"] += 1

    roadmap = []

    for topic, data in topic_performance.items():

        accuracy = (
            data["correct"] / data["total"]
        ) * 100

        if accuracy < 50:

            priority = "High"

            action = (
                "Study the basic concepts, revise your notes, "
                "and practise more questions."
            )

        elif accuracy < 80:

            priority = "Medium"

            action = (
                "Review this topic and solve additional "
                "practice questions."
            )

        else:

            priority = "Low"

            action = (
                "Continue practising advanced questions "
                "to maintain your performance."
            )

        roadmap.append({

            "topic": topic,

            "accuracy": round(accuracy, 2),

            "priority": priority,

            "action": action
        })

    # Show weakest topics first
    roadmap.sort(
        key=lambda item: item["accuracy"]
    )

    return {

        "message": "Personalised learning roadmap generated!",

        "roadmap": roadmap
    }


# ==========================================
# DASHBOARD STATISTICS
# ==========================================

@app.get("/dashboard-stats")
def get_dashboard_stats():

    total_quizzes = len(quiz_history)

    total_questions = 0
    correct_answers = 0
    topic_data = {}

    for attempt in quiz_history:

        total_questions += len(attempt)

        for result in attempt:

            topic = result["topic"]

            if topic not in topic_data:
                topic_data[topic] = {
                    "total": 0,
                    "correct": 0
                }

            topic_data[topic]["total"] += 1

            if result["is_correct"]:
                correct_answers += 1
                topic_data[topic]["correct"] += 1

    accuracy = 0

    if total_questions > 0:
        accuracy = round(
            (correct_answers / total_questions) * 100,
            2
        )

    strong_topics = 0
    topics_to_improve = 0
    topic_performance = []

    for topic, values in topic_data.items():

        topic_accuracy = round(
            (values["correct"] / values["total"]) * 100,
            2
        )

        if topic_accuracy >= 80:
            strong_topics += 1
            status = "Strong"

        else:
            topics_to_improve += 1

            if topic_accuracy < 50:
                status = "Weak"
            else:
                status = "Needs Improvement"

        topic_performance.append({
            "topic": topic,
            "accuracy": topic_accuracy,
            "status": status,
            "correct_answers": values["correct"],
            "total_questions": values["total"]
        })

    return {
        "total_quizzes": total_quizzes,
        "total_questions": total_questions,
        "correct_answers": correct_answers,
        "accuracy": accuracy,
        "strong_topics": strong_topics,
        "topics_to_improve": topics_to_improve,
        "topic_performance": topic_performance
    }
