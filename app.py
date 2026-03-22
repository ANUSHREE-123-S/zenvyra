from flask import Flask, render_template, request
import requests

app = Flask(__name__)
import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
HINDSIGHT_API_KEY = os.getenv("HINDSIGHT_API_KEY")

# 🔗 Hindsight URLs
HINDSIGHT_STORE_URL = "https://ui.hindsight.vectorize.io/api/memory"
HINDSIGHT_GET_URL = "https://api.hindsight.vectorize.io/v1/documents"

# 🧠 Local memory (for UI)
local_memory = []
user_tasks = []

# =========================
# 🧠 STORE MEMORY
# =========================
def store_memory(content):
    headers = {
        "Authorization": f"Bearer {HINDSIGHT_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {"text": content}

    try:
        requests.post(HINDSIGHT_STORE_URL, json=data, headers=headers)
    except Exception as e:
        print("STORE ERROR:", e)


# =========================
# 🧠 GET MEMORY
# =========================
def get_memory():
    headers = {
        "Authorization": f"Bearer {HINDSIGHT_API_KEY}"
    }

    try:
        res = requests.get(HINDSIGHT_GET_URL, headers=headers)
        result = res.json()

        memories = []
        for item in result.get("documents", []):
            memories.append(item.get("text", ""))

        return ", ".join(memories)

    except Exception as e:
        print("GET ERROR:", e)
        return ""


# =========================
# 📄 PRACTICE PAGE
# =========================
@app.route("/practice", methods=["GET", "POST"])
def practice():
    feedback = ""
    hint = ""
    problem = "Maximum Subarray"

    url = "https://api.groq.com/openai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    if request.method == "POST":

        # 🟢 HANDLE HINT SYSTEM
        hint_level = request.form.get("hint_level")

        if hint_level:
            prompt = f"""
            Give Level {hint_level} hint for Maximum Subarray problem.

            Level 1 → small hint only
            Level 2 → approach idea
            Level 3 → near solution

            Do NOT give full answer.
            """

            data = {
                "model": "llama-3.1-8b-instant",
                "messages": [{"role": "user", "content": prompt}]
            }

            res = requests.post(url, headers=headers, json=data)
            result = res.json()

            hint = result["choices"][0]["message"]["content"]

        # 🔵 HANDLE SOLUTION EVALUATION
        elif request.form.get("solution"):
            solution = request.form.get("solution")

            prompt = f"""
            You are a DSA interviewer.

            Problem: {problem}

            Candidate Solution:
            {solution}

            Evaluate based on:
            - Logic
            - Time Complexity
            - Clarity

            Give output:

            Score: X/10
            Correct:
            Missing:
            Improve:
            """

            data = {
                "model": "llama-3.1-8b-instant",
                "messages": [{"role": "user", "content": prompt}]
            }

            res = requests.post(url, headers=headers, json=data)
            result = res.json()

            feedback = result["choices"][0]["message"]["content"]

    return render_template("practice.html", feedback=feedback, hint=hint)

# =========================
# 🧠 MAIN ROUTE
# =========================
@app.route("/", methods=["GET", "POST"])
def index():
    response_text = ""
    memory_list = local_memory
    interaction_count = len(local_memory)

    if request.method == "POST":
        question = request.form["question"]
        q_lower = question.lower()

        if not question.strip():
            return render_template("index.html", response="Please enter a question", memory=memory_list, count=interaction_count)

        # 🔁 GET MEMORY
        memory_context = get_memory()

        # =========================
        # 🎯 HINT SYSTEM (FIXED)
        # =========================
        if "level 1 hint" in q_lower:
            prompt = """
            You are a coding mentor.

            Problem: Maximum Subarray

            Give ONLY a small hint.
            Do NOT give solution.
            Keep it very short.
            """

        elif "level 2 hint" in q_lower:
            prompt = """
            You are a coding mentor.

            Problem: Maximum Subarray

            Give the approach to solve.
            Do NOT give full solution or code.
            """

        elif "level 3 hint" in q_lower:
            prompt = """
            You are a coding mentor.

            Problem: Maximum Subarray

            Explain almost full solution but leave final step.
            Do NOT give complete code.
            """

        elif "hint" in q_lower:
            prompt = """
            You are a coding mentor.

            Problem: Maximum Subarray

            Give a hint only, not full solution.
            """

        # =========================
        # 🧠 NORMAL AI RESPONSE
        # =========================
        else:
            prompt = f"""
            You are an AI Study Assistant.

            User weak areas:
            {memory_context}

            Answer in structured format:

            1. 📘 Explanation
            2. 💡 Example
            3. ⚠️ Weak Area Insight
            4. 🚀 Personalized Suggestion

            Question: {question}
            """

        # =========================
        # 🔗 GROQ API
        # =========================
        url = "https://api.groq.com/openai/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }

        data = {
            "model": "llama-3.1-8b-instant",
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }

        try:
            res = requests.post(url, headers=headers, json=data)
            result = res.json()

            if "choices" in result:
                response_text = result["choices"][0]["message"]["content"]
            else:
                response_text = "⚠️ API Error:\n" + str(result)

        except Exception as e:
            response_text = f"⚠️ Error: {str(e)}"

        # =========================
        # 🧠 STORE MEMORY
        # =========================
        if "recursion" in q_lower:
            store_memory("Weak in Recursion")
            local_memory.append("Weak in Recursion")

        elif "array" in q_lower:
            store_memory("Needs practice in Arrays")
            local_memory.append("Needs practice in Arrays")

        elif "dp" in q_lower or "dynamic programming" in q_lower:
            store_memory("Weak in Dynamic Programming")
            local_memory.append("Needs practice in DP")

        elif "tree" in q_lower:
            store_memory("Weak in Trees")
            local_memory.append("Needs practice in Trees")

        memory_list = local_memory
        interaction_count = len(local_memory)

    return render_template("index.html", response=response_text, memory=memory_list, count=interaction_count)

@app.route("/interview", methods=["GET", "POST"])
def interview():
    feedback = ""
    question = "Explain time complexity of binary search"

    if request.method == "POST":
        answer = request.form["answer"]

        prompt = f"""
        You are a DSA interviewer.

        Evaluate based on:
        - Concept clarity
        - Time complexity
        - Explanation

        Question: {question}
        Answer: {answer}

        Give structured output:

        Score: X/10  
        Correct:  
        Missing:  
        Improve:
        """

        url = "https://api.groq.com/openai/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }

        data = {
            "model": "llama-3.1-8b-instant",
            "messages": [{"role": "user", "content": prompt}]
        }

        res = requests.post(url, headers=headers, json=data)
        result = res.json()

        feedback = result["choices"][0]["message"]["content"]

    return render_template("interview.html", question=question, feedback=feedback)

def generate_plan(memory):
    plan = []

    if any("Recursion" in m for m in memory):
        plan.append("Practice Recursion problems")

    if any("Arrays" in m for m in memory):
        plan.append("Solve Array problems")

    if any("DP" in m for m in memory):
        plan.append("Revise Dynamic Programming")

    if not plan:
        plan.append("Solve basic problems")

    return plan
@app.route("/core-interview", methods=["GET", "POST"])
def core_interview():
    feedback = ""

    questions = {
        "python": "What is list vs tuple in Python?",
        "os": "What is process vs thread?",
        "cn": "What is TCP vs UDP?"
    }

    selected_domain = "python"  # default

    if request.method == "POST":
        selected_domain = request.form.get("domain")
        action = request.form.get("action")

        question = questions[selected_domain]

        # ✅ ONLY evaluate when button clicked
        if action == "evaluate":
            answer = request.form.get("answer")

            if answer and answer.strip():

                prompt = f"""
                You are a technical interviewer.

                Domain: {selected_domain.upper()}

                Question: {question}

                Candidate Answer:
                {answer}

                Evaluate based on:
                - Concept clarity
                - Reasoning
                - Communication

                Give structured output:

                Score: X/10
                Correct:
                Missing:
                Improve:
                """

                url = "https://api.groq.com/openai/v1/chat/completions"

                headers = {
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json"
                }

                data = {
                    "model": "llama-3.1-8b-instant",
                    "messages": [{"role": "user", "content": prompt}]
                }

                res = requests.post(url, headers=headers, json=data)
                result = res.json()

                feedback = result["choices"][0]["message"]["content"]

                # 🧠 update weak area
                ans_lower = answer.lower()

                if selected_domain == "python" and "tuple" not in ans_lower:
                    local_memory.append("Weak in Python Basics")

                elif selected_domain == "os" and "thread" not in ans_lower:
                    local_memory.append("Weak in OS Concepts")

                elif selected_domain == "cn" and "tcp" not in ans_lower:
                    local_memory.append("Weak in Computer Networks")

    # 🔥 always update question
    question = questions[selected_domain]

    return render_template(
        "core_interview.html",
        question=question,
        feedback=feedback,
        domain=selected_domain
    )

@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    global user_tasks

    if request.method == "POST":

    # 🔥 CLEAR TASKS
        if request.form.get("action") == "clear":
            user_tasks.clear()

        else:
            task = request.form.get("task")
            if task:
                user_tasks.append(task)

    plan = generate_plan(local_memory)

    return render_template(
        "dashboard.html",
        plan=plan,
        memory=local_memory,
        tasks=user_tasks
    )
# =========================
# 🚀 RUN
# =========================
if __name__ == "__main__":
    app.run(debug=True)