import io
import sys
import json
import traceback
from contextlib import redirect_stdout
from flask import Flask, render_template, request

# Import test cases from tests.py
from tests import TEST_CASES

app = Flask(__name__)

def load_question():
    with open("questions.json", "r", encoding="utf-8") as f:
        return json.load(f)

def run_user_code(user_code: str, stdin_data: str) -> str:
    """
    Run user's Python code with given stdin_data and capture stdout output.
    Warning: This executes code directly; only use this project locally and never expose to untrusted users.
    """
    old_stdin = sys.stdin
    sys.stdin = io.StringIO(stdin_data)
    stdout_buffer = io.StringIO()

    try:
        local_namespace = {}
        with redirect_stdout(stdout_buffer):
            exec(user_code, {}, local_namespace)
    except Exception:
        output = "ERROR:\n" + traceback.format_exc()
        sys.stdin = old_stdin
        return output
    finally:
        sys.stdin = old_stdin

    return stdout_buffer.getvalue()

def check_code_against_tests(user_code: str):
    """
    Run user code on all test cases and gather results.
    """
    results = []
    all_passed = True

    for idx, case in enumerate(TEST_CASES, start=1):
        input_data = case["input"]
        expected_output = case["expected_output"]

        actual_output = run_user_code(user_code, input_data)

        norm_expected = expected_output.strip()
        norm_actual = actual_output.strip()

        passed = (norm_actual == norm_expected)
        if not passed:
            all_passed = False

        results.append({
            "id": idx,
            "input": input_data,
            "expected_output": expected_output,
            "actual_output": actual_output,
            "passed": passed,
        })

    return all_passed, results

@app.route("/", methods=["GET", "POST"])
def index():
    question = load_question()
    user_code = ""
    sample_run_output = None
    result_data = None

    if request.method == "POST":
        user_code = request.form.get("code", "")
        sample_input = question.get("sample_input", "")
        if sample_input:
            sample_run_output = run_user_code(user_code, sample_input)

        all_passed, test_results = check_code_against_tests(user_code)
        result_data = {
            "all_passed": all_passed,
            "test_results": test_results
        }

        return render_template("result.html",
                               question=question,
                               user_code=user_code,
                               sample_run_output=sample_run_output,
                               result_data=result_data)
    return render_template("index.html", question=question, user_code=user_code)

if __name__ == "__main__":
    # Run Flask app in debug mode
    app.run(debug=True)
