from flask import Flask, request, redirect, flash, session, url_for
from flask_debugtoolbar import DebugToolbarExtension
from flask import render_template, make_response
from surveys import satisfaction_survey, personality_quiz


app = Flask(__name__)
app.debug = True
app.config["SECRET_KEY"] = "SECRET!"

toolbar = DebugToolbarExtension(app)

surveys = {
    "satisfaction": satisfaction_survey,
    "personality": personality_quiz,
}

responses = []


@app.route("/")
def home():
    return render_template("start.html")


@app.route('/begin/<survey_id>', methods=["POST"])
def start_survey(survey_id):
    # Check if user has already completed the survey based on the 'survey_done' cookie
    survey_done = request.cookies.get('survey_done')
    
    if survey_done:
        return redirect(url_for('already_done'))
    else:
            # Fetches the desired survey based on the provided survey_id
        survey = surveys.get(survey_id)
        if survey:
            # Resets the responses session variable to an empty list
            session['responses'] = []
            # Stores the chosen survey_id in the session
            session['survey_id'] = survey_id
            # Redirects to the first question page
            return redirect("/questions/0")
        else:
            # This handles the case when the survey is not found in the survey dictionary
            return "Error: survey not found", 404


@app.route("/questions/<int:id>")
def show_questions(id):
    survey_id = session.get('survey_id')
    survey = surveys[survey_id]
    responses = session.get('responses')

    if (responses is None):
    # trying to access question page too soon 
        return redirect("/begin")

    if (len(responses) == len(survey.questions)):
    # They've answered all the questions! Thank them.
        return redirect("/thankyou")

    if len(responses) > id:
        question = survey.questions[id]
        return render_template("question.html", question=question, id=id)
    
    if (len(responses) != id):
        flash(f"Invalid question id: {id}.")
        return redirect(f"/questions/{len(responses)}")
    
    question = survey.questions[id]
    return render_template("question.html", question=question, id=id)



@app.route("/answers/<int:id>", methods=["POST"])
def handle_answer(id):
    # Get the choice from the form data
    choice = request.form['choice']

    # We use dict.setdefault to initialize an empty list if 'responses' is not yet in the session
    responses = session.setdefault('responses', [])
    responses.append(choice)  # append the choice to the list
    session['responses'] = responses  # save the list back to the session
    session.modified = True

    next_question_id = id + 1
    return redirect(url_for('show_questions', id=next_question_id))


@app.route("/select-survey")
def select_survey():
    surveys_dict = {survey_id: survey for survey_id, survey in surveys.items()
                    if not request.cookies.get(f'survey_{survey_id}_done')}
    return render_template('select-survey.html', surveys=surveys_dict)


@app.route("/skip", methods=["POST"])
def skip_question():
    responses = session.get('responses', [])
    responses.append(None)
    session['responses'] = responses
    next_question_id = len(responses)
    if next_question_id >= len(surveys[session['survey_id']].questions):
        return redirect("/thankyou")
    return redirect(f"/questions/{next_question_id}")



@app.route("/thankyou")
def thankyou():
    survey_id = session.get('survey_id')
    survey = surveys[survey_id]
    responses = session['responses']
    # Create a response object so you can set cookies
    resp = make_response(render_template("thankyou.html", paired_data=zip(survey.questions, responses)))
    # Sets a cookie indicating that the survey has been done
    resp.set_cookie(f"survey_{survey_id}_done", "done", max_age=60*60*24*365*2) #expiration of cookie set to two years from now
    
    return resp



if __name__ == "__main__":
    app.run()