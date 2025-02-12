import json


def get_survey_qs():
    survey_qas = None
    with open("salford/ui_data/q_n_a.json") as f:
        survey_qas = json.loads(json.load(f))
    return survey_qas


def get_all_app_qs():
    qs = None
    with open("salford/ui_data/app_question.json") as f:
        qs = json.loads(json.load(f))
    return qs


def easy_matched_op_name(app_qs, op_name):
    ops = [o for o in app_qs if o["opportunity_name"].strip().lower() == op_name.strip(
    ).lower()]
    if len(ops) == 1:
        op = ops[0]
        app_reqs = op["additional_docs"]
        qs = op["questions"]
        return (qs, app_reqs)
    else:
        return (None, None)


def contained_matched_op_name(app_qs, op_name):
    ops = [o for o in app_qs if o["opportunity_name"].strip().lower() in op_name.strip(
    ).lower() or op_name.strip().lower() in o["opportunity_name"].strip().lower()]
    if len(ops) == 1:
        op = ops[0]
        app_reqs = op["additional_docs"]
        qs = op["questions"]
        return (qs, app_reqs)
    else:
        return (None, None)


def word_matched_op_name(app_qs, op_name):
    clean_op_name = re.subn(
        r"[^a-z0-9]+", " ", op_name.strip().lower())[0]
    clean_op_name = re.subn(r"\s+", " ", clean_op_name)[0].split(" ")
    names = [o["opportunity_name"].strip().lower() for o in app_qs]
    max_match = 0
    max_match_idx = None
    for name in names:
        clean = re.subn(r"[^a-z0-9]+", " ", name)[0]
        clean = re.subn(r"\s+", " ", clean)[0].split(" ")
        match_count = 0
        for word in clean:
            if word in clean_op_name:
                match_count += 1
        if match_count > max_match:
            max_match = match_count
            max_match_idx = names.index(name)
    if max_match_idx:
        op = app_qs[max_match_idx]
        app_reqs = op["additional_docs"]
        qs = op["questions"]
        return (qs, app_reqs)
    else:
        return (None, None)


def get_app_qs(op_name):
    qs, app_reqs = None, None
    app_qs = get_all_app_qs()
    qs, app_reqs = easy_matched_op_name(app_qs, op_name)
    if not qs:
        qs, app_reqs = contained_matched_op_name(app_qs, op_name)
        if not qs:
            qs, app_reqs = word_matched_op_name(app_qs, op_name)
    return (qs, app_reqs)


"""
States:
1. State 1: Nothing Filled, New session
State Variables = submitted_screening_qs = False, matches = False, matches_shown = False, selected_op_app = False, st.session_state.app_qs_shown = False, submitted_app_qs = False, app_shown = False
Data Variables = screening_qs = [], matched_ops = [], active_op = None, app_qs = [], app_reqs = [], app_qas = [], app = None
Elems visible: screening_qs_form
Function calls: None

2. State 2: Screening Qs Submitted | Transition to getting opportunities
State Variables = submitted_screening_qs = True, matches = True, matches_shown = False, selected_op_app = False, st.session_state.app_qs_shown = False, submitted_app_qs = False, app_shown = False
Data Variables = len(screening_qs) > 0, matched_ops = [], active_op = None, app_qs = [], app_reqs = [], app_qas = [], app = None
Elems visible: Loading screen = "Now matching you to funding opportunities, please wait..."
Function calls: get_matches(screening_qs)


3 State 3: Screening Qs Submitted | Matches loaded and shown
State Variables = submitted_screening_qs = True, matches = True, matches_shown = True, selected_op_app = False, st.session_state.app_qs_shown = False, submitted_app_qs = False, app_shown = False
Data Variables = len(screening_qs) > 0, len(matched_ops) > 0, active_op = None, app_qs = [], app_reqs = [], app_qas = [], app = None
Elems visible: List of opportunity matches each with button for create app

4. State 4: Opportunity Selected for Application | Transition to showing application qs form
State Variables = submitted_screening_qs = True, matches = True, matches_shown = True, selected_op_app = True, st.session_state.app_qs_shown = False, submitted_app_qs = False, app_shown = False
Data Variables = len(screening_qs) > 0, len(matched_ops) > 0, active_op != None, app_qs = [], app_reqs = [], app_qas = [], app = None
Elems visible: Loading screen = "Generating application questions, please wait..."
Function calls: get_app_qs(active_op)

5. State 5: Opportunity Selected for Application |  Application qs form shown
State Variables = submitted_screening_qs = True, matches = True, matches_shown = True, selected_op_app = True, st.session_state.app_qs_shown = True, submitted_app_qs = False, app_shown = False
Data Variables = len(screening_qs) > 0, len(matched_ops) > 0, active_op != None, len(app_qs) > 0, len(app_reqs) > 0, app_qas = [], app = None
Elems visible: app_qs_form

6. State 6: Application Qs Submitted | Transition to showing application generated
State Variables = submitted_screening_qs = True, matches = True, matches_shown = True, selected_op_app = True, st.session_state.app_qs_shown = True, submitted_app_qs = True, app_shown = False
Data Variables = len(screening_qs) > 0, len(matched_ops) > 0, active_op != None, len(app_qs) > 0, len(app_reqs) > 0, len(app_qas) > 0, app = None
Elems visible: Loading screen = "Writing your application, please wait...
Function calls: gen_app(screening_qs, app_qs, active_op)

7. State 7: Application Qs Submitted | Application Generated shown
State Variables = submitted_screening_qs = True, matches = True, matches_shown = True, selected_op_app = True, st.session_state.app_qs_shown = True, submitted_app_qs = True, app_shown = True
Data Variables = len(screening_qs) > 0, len(matched_ops) > 0, active_op != None, len(app_qs) > 0, len(app_reqs) > 0, len(app_qas) > 0, app != None
Elems visible: Written application and additional application requirements
"""
