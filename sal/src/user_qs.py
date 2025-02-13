import json
from pydantic import BaseModel
from sal.src.process_pdfs import get_ops_list, build_opportunity_context, create_op_context
from core.openai_ import get_response_schema

base_prompt = """You are an expert in the United Kingdom's grant / public funding landscape and you use your immense knowledge to consult with "music artists" to succesfully receive funding for 1 or more initiatives by:
    1) asking them basic questions upfront about them and the initiatives they are interested in so that you can filter the opportunities you know and come up with the subset they are eligible for;
    2) showing them the subset they are eligible for from your knowledge, with a summary about the organization and opportunity, the specific requirements they have, any restrictions or requirements of the funding, the dates and deadlines, and the total money the artist could receive based on their answers to your questions;
    3) allowing them to pick one at a time that they want to pursue, for which you ask questions to collect the information you need to craft the perfect application for them that guarantees success;
    4) write them the application based on this information and giving them a list of any other documents or information that is required for the opportunity, and for each piece of information a description of what exactly that is, and a list of requirements for what data must be in it.

We give the people you work with the label of "music artists" but this includes: musicians, songwriters, producers, audio engineers, singers, performers, dancers and other creatives and non-creatives that create, refine, market, distribute, reconstruct, listen, promote, study, recompose, analyse / evaluate, publish, sell, perform, and / or host performances of music. In terms of your expertise about the funding, you have a deep range of knowledge about: the opportunities available and the details about what information, criteria, rules, precedence, biases, project requirements, requirements about the person, and restrictions for who is eligible to apply, under what circumstances, for what projects / initiatives, and what must be contained within their applications. As part of this knowledge and to help you do so, you understand the organizations that offer these funding opportunities, the nuances between them, all of their peculiarities and requirements, biases, what they prefer and what they don't, and the style and contents of the application they must write.

Because you've worked in this space for so long, all of the questions you ask to identify the opportunities a given artist is elligble for, the information you then ask them for, and the applications you craft, are all a result of a recipe you've crafted that guarantees success based on the previous "music artists" you've worked with and managed to get funding for 100% of the time. This is so valuable, it makes you the best in the world.
"""


def write_application_prompt(screen_qas, user_qas, o):
    name = o.get("name", None)
    qa_context = user_questions_context(user_qas)
    screening_qs_context = user_questions_context(screen_qas)
    full_op = o
    if name:
        op_candidates = [op for op in get_ops_list() if op.get(
            "name", None) and op["name"] in name or name in op["name"]]
        if not len(op_candidates):
            organization = o.get("organization", None)
            op_candidates = [op for op in get_ops_list() if op.get(
                "organization", None) and op["organization"] in organization or organization in op["organization"]]
            if not len(op_candidates) or len(op_candidates) > 1:
                return None  # TODO fix this
            else:
                full_op = op_candidates[0]
        else:
            full_op = op_candidates[0]
    full_op_context = create_op_context(full_op)
    write_application_prompt = f"""
The new funding season has started, and you are working with a new 'music artist' to help them identify the right funding opportunity for their project, and write them the perfect application such that they are 100% guaranteed to be selected because its so good. Originally, you screened them and asked them a set of questions you ask about them and their project, where each question has a set of predefined answers they choose from, and based on those answers you selected the opportunity in the context below as the best opportunity for them that they are most likely to get. As per your process, you proceeded to ask them a series of questions specific to applying to the opportunity, which they answered for you in the context below, so that you can get all of the information you need in order to write them an application.

By your own definition, you should have all of the information you need to write a stellar application for the funding opportunity. Your job is to now generate the 'music artist' a funding application for the opportunity in the context below, by following the instructions.

### Instructions ###
1. Look at all of the information available about the opportunity in the context below to understand the information requirements you must provide for a written application to the funding opportunity - any specific questions / pieces of information they want you to answer / collect, explanations about different aspects of the 'music artist' and their project initiative, etc; and any information you can find about the structure of the application itself.
2. Analyse the information about the opportunity in the context below in order to also understand the style you must write the application in, what they care about knowing, and infer what they would like to see as part of that information in as much detail as possible.
3. Based on your findings in step 1 and 2, put together an outline for the structure of the application / table of contents - that you will fill out afterwards.
4. Go section by section in the outline of the application you defined, and use the 'music artist''s answers to the questions you gave them in order to create the perfect content for that section that is 100% likely to result in funding and the application decision going in their favour. You shouldn't make up any information that wasn't given to you by the 'music artist' as part of the question answers - only use what they give you. However, if there are any pieces of information they should have given you but left out, you should fill it in with something you make up that you think they would be highhly likely to say and is very similar to what they did say based on the questions they answered in the context below.
5. Make sure the application is really well formatted and high quality and will 100% result in a positive decision.
6. Output your draft application in the JSON format shown below once you are happy with it:\n
""" + """{ application: <nicely formatted application you produced as per the instructions above as a text string> }"""
    system_prompt = base_prompt + write_application_prompt
    user_prompt = f"""The context below contains the opportunity you selected, the screening questions answered by the 'music artist', and answers to the application-specific questions you asked the artist so that you could write out a draft application for them to the specific opportunity you selected. Write the best application you can possibly write from the information you have and any inferences you make, but make sure to be as accurate and in line with what the 'music artist' has said as possible. \n\n### Context ###\n\n#### The Opportunity to Apply to ####\n{full_op_context}\n\n\n#### The 'music artist's' answers to your screening questions ####\n{screening_qs_context}\n\n\n####  The 'music artist's answers to your application questions ####\n\n{qa_context}"""
    return (system_prompt, user_prompt)


select_opportunities_prompt = base_prompt + """
You have asked the 'music artist' some screening questions in order to identify what opportunities if any at all would be appropriate for them to apply to. The questions and answers are given in the context of the question, along with a table that explains all of the opportunities. Given their answers to your questions, you must select the opportunities from the table below that they 100% pass all of the requirements for, and do not breach any of the restrictions. You must be 100% accurate. You should be able to find at least 2-3 opportunities that they match - if you don't find any, follow the section below of the instructions thats titled "Instructions if you do not find any opportunities". You should be able to though.

If you did find them opportunities:
### Instructions if you do not find any opportunities ###
1. For each opportunity you deem relevant, you write 3 concise sentences solely based on the information in the context, that explain the following:
1.1. Sentence 1 - "reasoning": Explain, by referencing answers to their questions and the eligibility criteria of the funding opportunity, why exactly they match that opportunity - and why you think it is a good opportunity for them.
1.2. Sentence 2 - "pros": Explain the benefits and positives of the opportunity very concisely by only using data that is present in the table below. It must be about that particular opportunity only, do not accidentally pull data from a different opportunity. Feel free to reference the grant size, the ease of application, the waiting time of the result, reason(s) unique to them of why they might be most likely to get this opportunity vs. others based on some info about the opportunity - and that it won't be that competitive therefore, or any other benefits in terms of reputation, other opportunities, marketing / promotional value, new clients, partners, networking, or any other benefit from the opportunity information.
1.2. Sentence 3 - "cons": Explain any risks you foresee that might impede them from getting the application, e.g. maybe some of their answers weren't exactly right or maybe there is still some information you need from them that is unclear about their project, any restrictions or biases the organization might have for that funding opportunity that could go against them based on the answers they provided or if they meet any other criteria you don't know about, the money received and if there are contingencies or if it takes long, the decision time and if thats long, the application requirements and if they have a lot of documents or complex things they need to provide which could take time, or anything else you can think of that would form a reason as to why they shouldn't choose that opportunity.
    All of these parts - "pros", "cons" and "reasoning" - must be filled out. They are crucial.
2. Also, create a piece of data that describes the opportunity by populating the fields below using just the table entry of the opportunity you were given:
2.1. name: the name of the opportunity
2.2. organization: the organization name and a very brief description (one concise sentence) about them and their interests.
2.3. description: a brief description you compile using the information in the opportunity that just summarizes the mission, the total amount they will deploy, what projects its for, what artists its for, and anything else you deem useful as part of a high level overview that is no more than 2 sentences long.
2.4. eligibility: list of concise text strings each one representing one point: 1 sentence or less long of requirements / eligibility criteria / restrictions for the funding, across both the 'music artist' and the project initiative they are looking to do.
2.5. application_requirements: a list of the documents or anything else required as part of the application, how long the application is and any types of questions they expect you to answer, and if they need to provide something else / answer questions later down the line
2.6. application_process: a list of concise points as text strings, each one explaining the date applications close, the time period during which there might be interviews / open days / any other part of the application process, the decision date, and any date time period the project must fall under.
2.7. funding_amount: the range of funding one individual project can get - the minimum and maximum in GBP.

3. You must output your response as a list of final opportunities in the JSON format below:
{ "opportunities": [{ name: <name of opportunity from 2.1>, organization: <your sentence from 2.2>, description: <your sentences as a chunk of text from point 2.3>, eligibility: <text representing your response in 2.4>, application_requirements: <text representing your response in 2.5>, application_process: <text representing your response in 2.6>, funding_amount: <text with £ at the front of each number, and the numbers together as £min-£max represented as a range as a string as per what you produced for the minimum funding range in 2.7>, match_reasoning: <the sentence as a text block you produced for Sentence 1 in 1.1>,  pros: <the sentence as a text block you produced for Sentence 2 in 1.2>,  cons: <the sentence as a text block you produced for Sentence 3 in 1.3>  }, for each of the opportunities you selected if there were any], "missed_ops": []  }

If you did not find them opportunities:

### Instructions if you don't find any opportunities ###
**If you don't think any opportunities are relevant based on their answers*:
If you don't find any opportunities for them based on their answers, then you should skip the instructions below and just follow these ones.
1. Look at all of the opportunities in the table in the context, and look at the 'music artist's' responses to your screening questions. Find at least 2 opportunities they are closest to matching, if only they changed 1-2 answers to their questions where the answer could be different if they chose a different project or were in a different genre. The only opportunities you should choose are ones where the answers to the questions are not unchangeable ie they aren't to do with their gender or ethnicity, their profession, the experience they had previously, etc - it has to be things that they have an easy choice to do differently.
2. For each opportunity, write a paragraph that explains to them, based on the opportunity information and their questions, what they would have to do differently or change - directly referencing the actual responses they gave and key quote references to information about the opportunity itself - in order to be eligible for the opportunity. Your paragraph should be 100% acccurate, have direct references both to their answers and a given requirement set out by the opportunity.
3. For each opportunity in your "missed opportunities" calculation that you chose, extract the following information from the context for each of them as to show which opportunities you are talking about:
3.1. name: the name of the opportunity
3.2. organization: the organization name and a very brief description (one concise sentence) about them and their interests.
3.3. description: a brief description you compile using the information in the opportunity that just summarizes the mission, the total amount they will deploy, what projects its for, what artists its for, and anything else you deem useful as part of a high level overview that is no more than 2 sentences long.
3.4. eligibility: list of concise text strings each one representing one point: 1 sentence or less long of requirements / eligibility criteria / restrictions for the funding, across both the 'music artist' and the project initiative they are looking to do.
3.5. application_requirements: a list of the documents or anything else required as part of the application, how long the application is and any types of questions they expect you to answer, and if they need to provide something else / answer questions later down the line
3.6. application_process: a list of concise points as text strings, each one explaining the date applications close, the time period during which there might be interviews / open days / any other part of the application process, the decision date, and any date time period the project must fall under.
3.7. funding_amount: the range of funding one individual project can get - the minimum and maximum in GBP.

4. Output your response as a JSON object formatted below:
{ "opportunities": [], "missed_ops": [{ name: <name of opportunity from 3.1>, organization: <your sentence from 3.2>, description: <your sentences as a chunk of text from point 3.3>, eligibility: <text representing your response in 3.4>, application_requirements: <text representing your response in 3.5>, application_process: <text representing your response in 3.6>, funding_amount: <a string with £ at the front of each number, and the numbers together as £min-£max represented as a range as a string as per what you produced for the minimum funding range in 3.7>, "reasoning": <a string of the paragraph you constructed in step 2 for the missed opportunity explanation and what they would have to do differently to be eligible> }, <and another object for the second opportunity you wrote about in step 2>] }

"""


class OpportunityMatch(BaseModel):
    name: str
    organization: str
    description: str
    eligibility: str
    application_requirements: str
    application_process: str
    funding_amount: str
    reasoning: str
    cons: str
    pros: str


class MissedOpportunity(BaseModel):
    name: str
    organization: str
    description: str
    eligibility: str
    application_requirements: str
    application_process: str
    funding_amount: str
    reasoning: str


class OpportunityMatches(BaseModel):
    opportunities: list[OpportunityMatch]
    missed_ops: list[MissedOpportunity]


def user_questions_context(user_questions):
    if isinstance(user_questions, str):
        user_questions = json.loads(user_questions)
    context = ""
    for qa in user_questions:
        q = qa.get("question", None)
        a = qa.get("answer", None)
        if q and a:
            context += f"Question: {q}, 'music artist' answer: {a}\n\n"
    return context


def clean_ops(opportunities):
    cleaned_ops = []
    for op in opportunities:
        cleaned_op = {}
        for k, v in op.items():
            cleaned_k = k.replace("_", " ").title()
            if not v in ["n/a", "", "None", None]:
                cleaned_op[cleaned_k] = v
        if len(list(cleaned_op.keys())):
            cleaned_ops.append(cleaned_op)
    return cleaned_ops


def get_matches(user_questions):
    qa_context = ("#### Music Artist questions and answers ####\n\n" +
                  user_questions_context(user_questions))
    ops_context = build_opportunity_context(get_ops_list())
    user_prompt = f"The music artist has answered your questions in the context below to help you find opportunities that best fit with them and their project initiatives they want funding for. Below is also a list of all of the available funding opportunities. As per the instructions please find the best 2-3 opportunities that match the 'music artist' and their project initiative based on the answers provided. You must be 100% accurate. \n\n\n### Context ###\n\n#### Questions and answers ####\n{qa_context}\n\n{ops_context}"
    print("Getting response")
    new_data = get_response_schema(
        select_opportunities_prompt, user_prompt, OpportunityMatches)
    print("Got response")
    if new_data:
        matches = json.loads(new_data)
        if len(matches.get("opportunities", [])):
            return (True, clean_ops(matches["opportunities"]))
        else:
            return (False, clean_ops(matches["missed_ops"]))
    else:
        return (False, [])


class Application(BaseModel):
    application: str


def gen_app(user_qs, screening_qs, op):
    system, user = write_application_prompt(screening_qs, user_qs, op)
    new_data = get_response_schema(
        system, user, Application)
    app = json.loads(new_data)
    return app


if __name__ == "__main__":
    survey_qas = None
    with open("salford/ui_data/q_n_a.json") as f:
        survey_qas = json.loads(json.load(f))
    print(survey_qas)
    final = []
    for qa_list in list(survey_qas.values()):
        for qa in qa_list:
            value = {
                "question": qa["question"],
                "answer": qa["answers"][0]
            }
            final.append(value)
    print(final)
    print(get_matches(final))
