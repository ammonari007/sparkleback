import streamlit as st
from sal.src.user_qs import get_matches, gen_app
from sal.app.fns import get_survey_qs, get_app_qs
import re
import time
import json


def state_1():
    if not st.session_state and not len(list(st.session_state.keys())):
        st.session_state.submitted_screening_qs = False
        st.session_state.screening_qas = []
        st.session_state.all_screening_qs = get_survey_qs()

        st.session_state.matches_shown = False
        st.session_state.matches = None
        st.session_state.matched_ops = []

        st.session_state.selected_op_app = False
        st.session_state.active_op = None

        st.session_state.app_qs_shown = False
        st.session_state.app_qs = []
        st.session_state.app_reqs = []

        st.session_state.submitted_app_qs = False
        st.session_state.app_qas = []

        st.session_state.app_shown = False
        st.session_state.app = None

        st.session_state.state = 1
        screening_form()


def page_title():
    st.title('UK Public Grant Funding for Music Industry Creatives')
    st.text("An AI designed to match UK creatives and their project amibitions to publicly available grant funding opportunities by asking them a series of questions to identify the best matched funding opportunity available for their needs, write them the perfect application, and list all of the other documentation requirements they must provide in order to submit the full application.")
    st.divider()


def screening_form():
    survey_qas = st.session_state.all_screening_qs
    main = st.empty()
    with main.container():
        page_title()
        with st.form("screening"):
            st.header("Opportunity Screening Survey")
            st.text("Select the most suitable answer from the options available for each of the questions below. When you've completed the survey, click the 'Submit' button so that the AI can match you to the best funding opportunity!")
            for qa in survey_qas["music_artist"]:
                ans = st.radio(
                    qa["question"].strip(),
                    qa["answers"])
                st.session_state["screening_qas"].append({
                    "question": qa["question"].strip(),
                    "answer": ans.strip()})
            for qa in survey_qas["project"]:
                ans = st.radio(
                    qa["question"].strip(),
                    qa["answers"])
                st.session_state["screening_qas"].append({
                    "question": qa["question"].strip(),
                    "answer": ans.strip()})
            st.form_submit_button(
                "Submit", on_click=state_2)


def state_2():
    st.session_state.state = 2
    st.session_state.submitted_screening_qs = True
    screening_qs_data = st.session_state.screening_qas
    if len(screening_qs_data) > 0:
        main = st.empty()
        with main.container():
            page_title()
            with st.spinner('Now matching you to funding opportunities, please wait...'):
                matched, matched_ops = get_matches(screening_qs_data)
                st.session_state.matches = matched
                st.session_state.matched_ops = matched_ops
            state_3()
    else:
        st.session_state.state = 1


def matches():
    ops = st.session_state.matched_ops
    matched = st.session_state.matches
    main = st.empty()
    with main.container():
        build_ops_section_headings(matched, ops)
        for i in range(0, len(ops)):
            op = ops[i]
            idx = i
            with st.container():
                st.subheader(op["Name"])
                for k, v in op.items():
                    col1, col2 = st.columns([0.25, 0.75])
                    if not k == "Name":
                        with col1:
                            st.markdown(f"**{k}**")
                        with col2:
                            st.text(f"{v}")
                st.text(op["Match Reasoning"])
            if matched:
                col1, col2 = st.columns([0.5, 0.5])
                with col1:
                    st.markdown("**Interested in applying?**")
                with col2:
                    st.button(
                        "Write Application with AI", key=f"curr_op_{idx}", on_click=state_4)
            st.divider()
        if not matched:
            col1, col2 = st.columns([0.5, 0.5])
            with col1:
                st.markdown("**Want to Restart?**")
            with col2:
                clicked = st.button("Restart")
                if clicked:
                    state_4()


def state_3():
    if len(st.session_state.matched_ops) and st.session_state.matches in [True, False]:
        st.session_state.matches_shown = True
        st.session_state.state = 3
        matches()
    else:
        st.session_state.state = 1


def state_4():
    if st.session_state.matches:
        st.session_state.state = 4
        st.session_state.selected_op_app = True
        op_idx = [k for k in st.session_state.keys() if "curr_op_" in k]
        idx = int(op_idx[0].replace("curr_op_", ""))
        st.session_state.active_op = st.session_state.matched_ops[idx]
        app_qs, app_reqs = get_app_qs(st.session_state.active_op["Name"])
        if len(app_qs):
            st.session_state.app_qs, st.session_state.app_reqs = app_qs, app_reqs
            state_5()
        else:
            st.session_state.state = 3
    else:
        st.session_state.state = 1


def app_qs_form():
    main = st.empty()
    with main.container():
        page_title()
        st.header(
            "Fill in the following questions so our AI can write you an application.")
        with st.form("fill_app_qs"):
            questions = st.session_state.app_qs
            st.session_state["app_qas"] = []
            for q in questions:
                txt = st.text_area(q, "")
                st.session_state["app_qas"].append(
                    {"question": q, "answer": txt})
            st.form_submit_button("Submit", on_click=state_6)


def state_5():
    if len(st.session_state.app_qs):
        st.session_state.app_qs_shown = True
        st.session_state.state = 5
        app_qs_form()
    else:
        st.session_state.state = 3


def state_6():
    st.session_state.submitted_app_qs = True
    st.session_state.state = 6
    if len(st.session_state.app_qas):
        screening_qs = st.session_state.screening_qas
        app_qs = st.session_state.app_qas
        op = st.session_state.active_op
        main = st.empty()
        ai_app = None
        with main.container():
            with st.spinner('Generating your application...'):
                ai_app = gen_app(app_qs, screening_qs, op)
                if ai_app and len(ai_app):
                    st.session_state.app = ai_app
            st.empty()
            st.heading(f"Your Application for Funding Opportunity {op_name}")
            st.markdown(ai_app)
            st.divider()
    else:
        st.session_state.state = 5


def build_app_page():
    main = st.empty()
    with main.container():
        op_name = st.session_state.active_op["Name"]
        st.heading(f"Your Application for Funding Opportunity {op_name}")
        st.markdown(st.session_state.app)
        st.divider()


def state_7():
    if st.session_state.app and len(st.session_state.app):
        st.session_state.app_shown = True
        st.session_state = 7
        build_app_page()
    else:
        st.session_state.state = 5


def build_ops_section_headings(matched, ops):
    if matched:
        st.text(
            f"Congratulations! You've been matched with {len(ops)} opportunities!")
        st.subheader("Your Matched Opportunities")
    else:
        st.text(
            f"Unfortunately, we couldn't match you to any opportunities based on your responses. However, we have compiled some feedback for what you could change in order to be eligible for {len(ops)} opportunities.")
        st.subheader("Opportunity Eligibility Advice")


state_1()
st.divider()
