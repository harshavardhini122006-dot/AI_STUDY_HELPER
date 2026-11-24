
const API_URL = "http://127.0.0.1:8000";

let currentQuiz = [];


// ==========================================
// COMMON BUTTON LOADING EFFECT
// ==========================================

function setButtonLoading(button, loadingText) {

    if (!button) return () => {};

    const originalText = button.textContent;

    button.disabled = true;
    button.textContent = loadingText;
    button.classList.add("is-loading");

    return function restoreButton() {
        button.disabled = false;
        button.textContent = originalText;
        button.classList.remove("is-loading");
    };
}


// ==========================================
// FEATURE 1: SMART NOTES UPLOAD
// ==========================================

async function uploadPDF() {

    const fileInput = document.getElementById("pdfFile");
    const status = document.getElementById("uploadStatus");
    const button = document.querySelector("#smart-notes .feature-button");

    if (fileInput.files.length === 0) {
        status.textContent = "Please select a PDF file.";
        return;
    }

    const formData = new FormData();
    formData.append("file", fileInput.files[0]);

    const restoreButton = setButtonLoading(button, "Uploading...");

    status.textContent = "Please wait while your PDF is uploaded.";

    try {

        const response = await fetch(`${API_URL}/upload-pdf`, {
            method: "POST",
            body: formData
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Upload failed.");
        }

        status.textContent = "✓ " + data.message;

        document.getElementById("quizOutput").innerHTML = "";
        document.getElementById("quizResult").textContent = "";

        currentQuiz = [];

    } catch (error) {

        status.textContent = "Unable to upload: " + error.message;

    } finally {

        restoreButton();

    }
}


// ==========================================
// FEATURE 2: AI DOUBT SOLVER
// ==========================================

async function askQuestion() {

    const question = document.getElementById("questionInput").value.trim();
    const output = document.getElementById("answerOutput");
    const button = document.querySelector("#doubt-solver .feature-button");

    if (!question) {
        output.textContent = "Please enter a question.";
        return;
    }

    const restoreButton = setButtonLoading(button, "Finding answer...");

    output.textContent = "Searching your uploaded notes...";

    try {

        const response = await fetch(`${API_URL}/ask`, {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                question: question
            })

        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Could not get an answer.");
        }

        output.textContent = data.answer;

    } catch (error) {

        output.textContent = "Unable to get an answer: " + error.message;

    } finally {

        restoreButton();

    }
}


// ==========================================
// FEATURE 3: QUIZ GENERATOR
// ==========================================

async function generateQuiz() {

    const numQuestions = document.getElementById("numQuestions").value;

    const quizOutput = document.getElementById("quizOutput");
    const quizResult = document.getElementById("quizResult");

    const button = document.querySelector("#quiz-generator .feature-button");

    const restoreButton = setButtonLoading(button, "Generating...");

    quizOutput.textContent = "Preparing your questions...";
    quizResult.textContent = "";

    currentQuiz = [];

    try {

        const response = await fetch(`${API_URL}/generate-quiz`, {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                num_questions: Number(numQuestions)
            })

        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Quiz generation failed.");
        }

        if (!Array.isArray(data.quiz) || data.quiz.length === 0) {
            throw new Error("No quiz questions were generated.");
        }

        currentQuiz = data.quiz;

        quizOutput.innerHTML = "";

        currentQuiz.forEach((question, index) => {

            const questionDiv = document.createElement("div");
            questionDiv.className = "quiz-question";

            const heading = document.createElement("h4");

            heading.textContent =
                `Q${question.question_number}. ${question.question}`;

            questionDiv.appendChild(heading);

            question.options.forEach((option, optionIndex) => {

                const label = document.createElement("label");
                label.className = "quiz-option";

                const radio = document.createElement("input");

                radio.type = "radio";
                radio.name = `question-${index}`;
                radio.value = optionIndex;

                label.appendChild(radio);

                label.appendChild(
                    document.createTextNode(" " + option)
                );

                questionDiv.appendChild(label);

            });

            quizOutput.appendChild(questionDiv);

        });

        const submitButton = document.createElement("button");

        submitButton.textContent = "Submit Quiz";
        submitButton.className = "feature-button";
        submitButton.onclick = submitQuiz;

        quizOutput.appendChild(submitButton);

        quizResult.textContent =
            "Your quiz is ready! Answer all questions and submit.";

    } catch (error) {

        currentQuiz = [];

        quizOutput.textContent = "Unable to generate quiz: " + error.message;

    } finally {

        restoreButton();

    }
}


// ==========================================
// QUIZ SUBMISSION AND AUTOMATIC SCORING
// ==========================================

async function submitQuiz() {

    const answers = [];

    for (let index = 0; index < currentQuiz.length; index++) {

        const selected = document.querySelector(
            `input[name="question-${index}"]:checked`
        );

        if (!selected) {

            alert(`Please answer question ${index + 1}.`);

            return;
        }

        answers.push(Number(selected.value));

    }

    const quizResult = document.getElementById("quizResult");

    const submitButton = document.querySelector(
        "#quiz-generator #quizOutput button"
    );

    const restoreButton = setButtonLoading(
        submitButton,
        "Checking answers..."
    );

    quizResult.textContent = "Evaluating your answers...";

    try {

        const response = await fetch(`${API_URL}/submit-quiz`, {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                answers: answers
            })

        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Quiz submission failed.");
        }

        quizResult.textContent =
            `🎉 Quiz Completed!

Score: ${data.correct_answers}/${data.total_questions}

Percentage: ${data.percentage}%

Feedback: ${data.feedback}`;

        await loadDashboardStats();

    } catch (error) {

        quizResult.textContent = "Unable to submit quiz: " + error.message;

    } finally {

        restoreButton();

    }
}


// ==========================================
// FEATURE 4: LEARNING GAP DETECTION
// ==========================================

async function getLearningGaps() {

    const output = document.getElementById("learningGapOutput");

    const button = document.querySelector(
        "#learning-gaps .feature-button"
    );

    const restoreButton = setButtonLoading(button, "Analysing...");

    output.textContent = "Analysing your quiz performance...";

    try {

        const response = await fetch(`${API_URL}/learning-gaps`);

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Analysis failed.");
        }

        const gaps = data.learning_gaps;

        if (!Array.isArray(gaps)) {
            throw new Error("Invalid learning gap data received.");
        }

        output.innerHTML = "";

        const heading = document.createElement("h4");
        heading.textContent = "📊 Your Learning Gap Analysis";

        output.appendChild(heading);

        if (gaps.length === 0) {

            output.textContent =
                "Complete a quiz to discover your learning gaps.";

            return;
        }

        gaps.forEach(topic => {

            const topicDiv = document.createElement("div");
            topicDiv.className = "quiz-question";

            const name = document.createElement("h4");
            name.textContent = topic.topic;

            const accuracy = document.createElement("p");
            accuracy.textContent = `Accuracy: ${topic.accuracy}%`;

            const status = document.createElement("p");
            status.textContent = `Status: ${topic.status}`;

            const answers = document.createElement("p");
            answers.textContent =
                `Correct Answers: ${topic.correct_answers}/${topic.total_questions}`;

            const recommendation = document.createElement("p");

            if (topic.status === "Weak") {

                recommendation.textContent =
                    "Recommendation: Revise basic concepts and practise more questions.";

            } else if (topic.status === "Needs Improvement") {

                recommendation.textContent =
                    "Recommendation: Review your notes and solve additional practice questions.";

            } else {

                recommendation.textContent =
                    "Recommendation: Great work! Continue practising to maintain your performance.";

            }

            topicDiv.appendChild(name);
            topicDiv.appendChild(accuracy);
            topicDiv.appendChild(status);
            topicDiv.appendChild(answers);
            topicDiv.appendChild(recommendation);

            output.appendChild(topicDiv);

        });

    } catch (error) {

        output.textContent = "Unable to analyse performance: " + error.message;

        console.error("Learning Gaps Error:", error);

    } finally {

        restoreButton();

    }
}


// ==========================================
// FEATURE 5: PERSONALISED LEARNING ROADMAP
// ==========================================

async function getLearningRoadmap() {

    const output = document.getElementById("roadmapOutput");

    const button = document.querySelector(
        "#learning-roadmap .feature-button"
    );

    const restoreButton = setButtonLoading(button, "Creating roadmap...");

    output.textContent = "Preparing your personalised study plan...";

    try {

        const response = await fetch(`${API_URL}/learning-roadmap`);

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Roadmap generation failed.");
        }

        if (!Array.isArray(data.roadmap)) {
            throw new Error("Invalid roadmap data received.");
        }

        output.innerHTML = "";

        const heading = document.createElement("h4");
        heading.textContent = "🎯 Your Personalised Roadmap";

        output.appendChild(heading);

        if (data.roadmap.length === 0) {

            output.textContent =
                "Complete a quiz to receive your personalised roadmap.";

            return;
        }

        data.roadmap.forEach((item, index) => {

            const topicDiv = document.createElement("div");
            topicDiv.className = "quiz-question";

            const topic = document.createElement("h4");
            topic.textContent = `${index + 1}. ${item.topic}`;

            const priority = document.createElement("p");
            priority.textContent = `Priority: ${item.priority}`;

            const accuracy = document.createElement("p");
            accuracy.textContent = `Accuracy: ${item.accuracy}%`;

            const action = document.createElement("p");
            action.textContent = `Action: ${item.action}`;

            topicDiv.appendChild(topic);
            topicDiv.appendChild(priority);
            topicDiv.appendChild(accuracy);
            topicDiv.appendChild(action);

            output.appendChild(topicDiv);

        });

    } catch (error) {

        output.textContent = "Unable to create roadmap: " + error.message;

        console.error("Roadmap Error:", error);

    } finally {

        restoreButton();

    }
}


// ==========================================
// DASHBOARD STATISTICS
// ==========================================

async function loadDashboardStats() {

    const status = document.getElementById("dashboardStatus");

    try {

        if (status) {
            status.textContent = "Loading your learning statistics...";
        }

        const response = await fetch(`${API_URL}/dashboard-stats`);

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Unable to load statistics.");
        }

        document.getElementById("totalQuizzes").textContent =
            data.total_quizzes;

        document.getElementById("averageAccuracy").textContent =
            data.accuracy + "%";

        document.getElementById("strongTopics").textContent =
            data.strong_topics;

        document.getElementById("topicsToImprove").textContent =
            data.topics_to_improve;

        if (status) {
            status.textContent = "✓ Your dashboard is up to date!";
        }

    } catch (error) {

        if (status) {
            status.textContent =
                "Unable to load dashboard: " + error.message;
        }

        console.error("Dashboard Error:", error);

    }
}


// ==========================================
// LOAD DASHBOARD WHEN WEBSITE OPENS
// ==========================================

document.addEventListener("DOMContentLoaded", function () {

    loadDashboardStats();

});
