import json
import pprint
import re
from pydantic import BaseModel
from pdf_extractor.parse_pdf import parse
from core.openai_ import get_response_schema


def list_files(base_path="sal/raw_data/", ext="pdf"):
    pdf_range = range(1, 11)
    paths = []
    for i in pdf_range:
        if i != 3:
            paths.append(f"{base_path}{i}.{ext}")
            if i < 7:
                paths.append(f"{base_path}dv{i}.{ext}")
    return paths


data_processing_prompt = """You are an expert in the United Kingdom's grant / public funding landscape and you use your immense knowledge to consult with "music artists" to succesfully receive funding for 1 or more initiatives by:
    1) asking them basic questions upfront about them and the initiatives they are interested in so that you can filter the opportunities you know and come up with the subset they are eligible for;
    2) showing them the subset they are eligible for from your knowledge, with a summary about the organization and opportunity, the specific requirements they have, any restrictions or requirements of the funding, the dates and deadlines, and the total money the artist could receive based on their answers to your questions;
    3) allowing them to pick one at a time that they want to pursue, for which you ask questions to collect the information you need to craft the perfect application for them that guarantees success;
    4) write them the application based on this information and giving them a list of any other documents or information that is required for the opportunity, and for each piece of information a description of what exactly that is, and a list of requirements for what data must be in it.

We give the people you work with the label of "music artists" but this includes: musicians, songwriters, producers, audio engineers, singers, performers, dancers and other creatives and non-creatives that create, refine, market, distribute, reconstruct, listen, promote, study, recompose, analyse / evaluate, publish, sell, perform, and / or host performances of music. In terms of your expertise about the funding, you have a deep range of knowledge about: the opportunities available and the details about what information, criteria, rules, precedence, biases, project requirements, requirements about the person, and restrictions for who is eligible to apply, under what circumstances, for what projects / initiatives, and what must be contained within their applications. As part of this knowledge and to help you do so, you understand the organizations that offer these funding opportunities, the nuances between them, all of their peculiarities and requirements, biases, what they prefer and what they don't, and the style and contents of the application they must write.

Because you've worked in this space for so long, all of the questions you ask to identify the opportunities a given artist is elligble for, the information you then ask them for, and the applications you craft, are all a result of a recipe you've crafted that guarantees success based on the previous "music artists" you've worked with and managed to get funding for 100% of the time. This is so valuable, it makes you the best in the world.

The new season of funding has come in, and you have a ton of unstructured data about funding opportunities, application requirements, examples of applications, success or failure stories from artists in interviews explaining what they did and what worked, etc that you must gather all the key pieces of data from and the facts you need in order to provide your service to new music artists for this upcoming set of funding.

### Instructions ###
1. The user will provide you with context of a document of unstructured information and your job is to reconstruct it into a useful JSON formatted output where you categorize all of the information in the document.
2. You must extract every single fact, detail and important piece of information without leaving any detail or piece of information behind, even if you think it might be superficially unimportant as bullet point items or text that preserves every single detail and key piece of data and opinion and information in there.
3. Then, you must analyze that information and identify the different unique funding opportunities that are being mentioned, and for each opportunity separate the bullet points into each of the categories below.
4. Some points might mention multiple funding opportunities at a time or be broader; some organizations might offer multiple funding opportunities. If this is the case, you can duplicate the bullet point and put them in multiple categories if they overlap, multiple opportunities if they are across opportunities. For example, all the information related to the organization will need to be duplicated across opportunities if there are multiple opportunities offered by an organization.
5. Below are the following categories of information you must separate bullet points into for each of the opportunities.
        - "opportunities": for each opportunity you identify, create a list of opportunities each with the follwoing information:
            "opportunity":
            - Category 1.0: "name": The title or name of the funding opportunity. If you don't know the name, that is fine, just put unknown.
            - Category 1.1: "organization": All information relating to the organization and its mission, activities, success stories, projects, personnel, funding availability, what they care about, restrictions, biases, goals, commercial offerings, customers, previous funding, backers, story, values, news, etc.
                - Category 1.2: "details": All information about the funding opportunity available. Everything about the opportunity - this might include its goal, any details or facts related to its purpose, who is behind it, what the requirements are, how much money in total they are offering, how much money they offer to a single applicant, the kinds of projects they are looking to fund and the restrictions / requirements / criteria for what that must consist of, the kinds of music artists and specificty thereof they are willing to fund, timelines, timeline of project, type of funding and mapping of funding to type of opportunity, application requirements or restrictions and deadlines, the application process and any interviews / information / etc required along the way, the timelines for decision application deadline / submission time / when they revert / what they might request when they revert / what other steps in the process they are / when a decision will be made, and any information about what influences that decision ie criteria, what they value the most, etc. Then, any restrictions on the funding itself and what the funding can be used for - what types of projects, what aspects of projects, what activities or initiatives, any restrictions regarding geography or affiliates or products / services they use etc.
                - Category 1.3: "person_eligibility": All information related to restrictions and requirements on who can apply as a "music artist" - a genre they might be associated with, their level of success, their experience, what their job title / experience / roles must be or have been in the past or have never been, any requirements related to their age, gender, ethnicity, location or other demographic/individual information, restrictions regarding any other funding they've received in the past, people or companies they've worked with, their partners and affiliates, their brand or marketing message, etc.
                - Category 1.4: "project_eligibility": :All information related to the restrictions and requirements for each of the projects or initiatives they can apply for for that opportunity- this might include, for each project type, the start and end date of the initiative, the total cost, any descriptions of what the initiative might or must be, the categories or criteria of eligibility of an initiative whether its in terms of budget, activities, time period, partners, geography, what they can use the money to pay for, whether they need to match money or if its an open grant, if its a loan or some other funding mechanism, if there are any people that must be involved, any skills they might need to have, etc.
                - Category 1.5: "application_requirements": All information related to the application criteria and contents: specific documents they must produce above and beyond the application, what information they need to provide in the application / questions they need to answer, any testimonials or third party information they must provide about the project or themselves, any financial information requirements about themselves or their projects, their history / previous experience / current role / partners / online resources / actual music / testimonials / etc required for the application, criteria used to assess eligibility and therefore what information might be required to include, less tangible comments or opinions about what helps and what doesn't help, what they prefer in the application, etc.
                - Category 1.6: "other": Any other information that directly relates to the organization, the opportunity available, the application and application process, eligibility, the projects they want to fund, the organization behind it, and any success stories / example applications / testimonials about the funding or organization, opinions about the opportunity of others, any nice to haves or things to include as part of the application, any projects they particularly favour, etc.
        "other": Independently, any information provided that does not directly fit into relate to or describe anything about an opportunity, or any information you are unsure about.
5. Remember you must never, under any circumstances, exclude information you find. Every piece of information in the context the user provides you with should be categorized and present in the output.
6. You must output your response, once you've done this work, as a JSON object formatted in the following way:
    { "opportunities": [{ "name", "organization", "details", "eligibility_project", "eligibility_person", "application_requirements", "other" }, ... for each of the opportunities in your list], "other": ["<a list of text strings each containing the bullet point that didn't fit into one or more opportunities and categories thereof directly>" ]}
"""


class Opportunity(BaseModel):
    name: list[str]
    organization: list[str]
    details: list[str]
    eligibility_project: list[str]
    eligibility_person: list[str]
    application_requirements: list[str]
    other: list[str]


class ExtractFunding(BaseModel):
    opportunities: list[Opportunity]
    other: list[str]


def process_raw_data():
    files = list_files()
    for fs in files:
        print(f"Processing file {fs}")
        output_f = fs.replace(".pdf", ".json").replace("raw_", "etl_")
        text = parse(fs)
        if text and len(text):
            print("-- Got pdf extracted")
            user_prompt = f"Analyze and decompose the document in the context below as per your instructions, producing your output in the exact JSON format specified.\n\n### Context ###\n{text}"
            new_data = get_response_schema(
                data_processing_prompt, user_prompt, ExtractFunding)
            if new_data:
                try:
                    with open(output_f, "w") as f:
                        f.write(json.dumps(new_data, ensure_ascii=True))
                        print("-- Wrote to file")
                        continue
                except Exception as e:
                    print(f"--{e} - continuing to next file")
                    continue
            else:
                print(f"--Error getting response from GPT. Continuing to next file")
                continue
        else:
            print(f"--Error extracting from pdf - continuing to next file")
            continue


def get_ops_list():
    files = list_files("sal/etl_data/", "json")
    ops = []
    for fs in files:
        with open(fs) as f:
            f_data = json.loads(json.load(f))
            if "opportunities" in f_data and len(f_data.get("opportunities", [])):
                for o in f_data["opportunities"]:
                    clean_op = {}
                    for k, v in o.items():
                        vs = [i.strip() for i in v if i and len(i.strip())]
                        if vs and len(vs):
                            if k != "name":
                                clean_op[k] = vs
                            else:
                                clean_op[k] = ", ".join(vs)
                    if not len(list(clean_op.keys())):
                        continue
                    if "name" in clean_op:
                        name = ", ".join(clean_op["name"])
                        matches = [ops.index(o)
                                   for o in ops if "name" in o and (name in o["name"] or o["name"] in name)]
                        if len(matches):
                            op = ops[matches[0]]
                            combined = {}
                            for k, v in op.items():
                                if k in clean_op:
                                    combined[k] = v + clean_op[k]
                                else:
                                    combined[k] = v
                            left = [k for k in clean_op.keys()
                                    if not k in combined]
                            if len(left):
                                for l in left:
                                    combined[l] = clean_op[l]
                            ops[matches[0]] = combined
                        else:
                            ops.append(clean_op)
                    else:
                        ops.append(clean_op)
    return ops


class Question(BaseModel):
    question: str
    answers: list[str]


class Questions(BaseModel):
    music_artist: list[Question]
    project: list[Question]


general_prompt = """You are an expert in the United Kingdom's grant / public funding landscape and you use your immense knowledge to consult with "music artists" to succesfully receive funding for 1 or more initiatives by:
    1) asking them basic questions upfront about them and the initiatives they are interested in so that you can filter the opportunities you know and come up with the subset they are eligible for;
    2) showing them the subset they are eligible for from your knowledge, with a summary about the organization and opportunity, the specific requirements they have, any restrictions or requirements of the funding, the dates and deadlines, and the total money the artist could receive based on their answers to your questions;
    3) allowing them to pick one at a time that they want to pursue, for which you ask questions to collect the information you need to craft the perfect application for them that guarantees success;
    4) write them the application based on this information and giving them a list of any other documents or information that is required for the opportunity, and for each piece of information a description of what exactly that is, and a list of requirements for what data must be in it.

We give the people you work with the label of "music artists" but this includes: musicians, songwriters, producers, audio engineers, singers, performers, dancers and other creatives and non-creatives that create, refine, market, distribute, reconstruct, listen, promote, study, recompose, analyse / evaluate, publish, sell, perform, and / or host performances of music. In terms of your expertise about the funding, you have a deep range of knowledge about: the opportunities available and the details about what information, criteria, rules, precedence, biases, project requirements, requirements about the person, and restrictions for who is eligible to apply, under what circumstances, for what projects / initiatives, and what must be contained within their applications. As part of this knowledge and to help you do so, you understand the organizations that offer these funding opportunities, the nuances between them, all of their peculiarities and requirements, biases, what they prefer and what they don't, and the style and contents of the application they must write.

Because you've worked in this space for so long, all of the questions you ask to identify the opportunities a given artist is elligble for, the information you then ask them for, and the applications you craft, are all a result of a recipe you've crafted that guarantees success based on the previous "music artists" you've worked with and managed to get funding for 100% of the time. This is so valuable, it makes you the best in the world.\n\n"""

screening_qs_prompt = general_prompt + """
The new season of funding has come in, and you have found the list of funding opportunities available. You now need an easy way of screening "music artists" before you waste any time working with them, by asking them questions about themselves and the project / initative they are looking to do so that you can quickly assess whether or not they are eligible for any of the funding opportunities available.

### Instructions ###
1. What you need to do is examine all of the funding opportunities that are given to you in the context, and come up with two groups of questions with a predefined set of answers: 1) questions about the music artist; 2) questions about the project/initiative they want to get funded.
2. Each question must be concise, easy for the music artist to understand by being free of technical or financial jargon, and the predefined answers they must choose from should have wide coverage.
3. You must choose these questions and possible answers in such a way that all of the responses you acquire are sufficient information for you to select the grant that suits them best - so you must be really specific with your questions.
4. There is no limit on the number of answers you come up with that they must select from.
5. Output your response as a JSON object in the following format:
{ music_artist: [{ question, answers: [<list of answers as list of text strings>]}, <each question you come up with as a list of questions structured as per the example>], project: [{ question, answers: [<list of answers as list of text strings>]}, <each question you come up with as a list of questions structured as per the example>] }
"""

get_app_qs_prompt = """
The new season of funding has come in, and you have found the list of funding opportunities available. You also have created a list of screening questions and predefined answers you will use, when you work with a 'music artist', to create a shortlist of all the opportunities available. In the context below, you are given the details about one opportunity and all of the screening questions and possible answers you created previously. Your job is to create a list of questions that the 'music artist' must answer in order for you to generate the perfect application for them that will lead to 100% guaranteed succeesful funding so you can maintain your reputation by following the instructions below.
### Instructions ###
1. You must analyse the context about the opportunity below, and look at your screening questions and possible answers to ascertain what information you will already have.
2. Look at the opportunity in detail and come up with a list of the required information they must write as part of their written application, about themselves and / or about the project such that they prove they are eligible and a good candidate and can actually get the funding. You should also include any restrictions they must prove they do not breach, or any other eligiblity criteria they must prove.
3. From this, create a list of questions about the music artist, their project, and any other details from step 2 you need in order to write the perfect application that will have guaranteed success in receiving funding. You must ensure you get all of the information you need to create the application. Adding examples or key pieces of information you require to each of the questions is good - the more guidance the better. Your questions should cover everything you need to write the application.
4. Separately, produce a list of documents or other pieces of information only the 'music artist' has (that you can't create) such as financials, testimonials, passports, etc. Make sure you cover everything they must upload themselves as part of submitting the application you write for them if they pay you later - but they must know here what exactly you will need so they can start preparing.
5. Output your answer as a JSON response in the following format:
{ "questions": [<list of strings of each question and any examples / guidance you provided as part of coming up with the question>], "additional_docs": [<a list of strings each representing one of the required pieces of information they must create and submit alongside a written application>] }
"""


class ApplicationDetails(BaseModel):
    questions: list[str]
    additional_docs: list[str]


def build_opportunity_context(ops):
    all_keys = [[k for k in o.keys()] for o in ops]
    all_keys = list(set([x for xs in all_keys for x in xs]))
    table_header = "| " + " | ".join(all_keys) + " | \n"
    divider = "| " + " | ".join(["------" for k in all_keys]) + " | \n"
    table = table_header + divider
    for op in ops:
        op_row = "| "
        for k in all_keys:
            if k in op and op.get(k, None):
                val = ", ".join(op[k]) if isinstance(op[k], list) else op[k]
                op_row += val + " | "
            else:
                op_row += " n/a | "
        op_row += "\n"
        table += op_row
    return table


def get_questions():
    ops = get_ops_list()
    context = build_opportunity_context(ops)
    user_prompt = f"The list of opportunities is in the table in the context below. Produce two lists of questions as per the instructions you were given, one about the music artist and the other about their initiative / project they want funded, where each question has a predefined set of answers and the answers and questions are specific enough that if the music artist were to choose any combination of answers you would ascertain which of the opportunities in the table below were relevant. \n\n### Context ###\nOpportunities\n\n{context}"
    new_data = get_response_schema(
        screening_qs_prompt, user_prompt, Questions)
    if len(new_data):
        with open("sal/ui_data/q_n_a.json", "w") as f:
            f.write(json.dumps(new_data, ensure_ascii=True))


def create_op_context(op):
    context = ""
    for k, v in op.items():
        val = ", ".join(op[k]) if isinstance(op[k], list) else op[k]
        if k == "name":
            context = f"Description of Opportunity {val}\n" + context
        else:
            context += f"- The {k} is: {val}"
    return context


def get_all_qa_context():
    qa_raw = None
    context = ""
    with open("sal/ui_data/q_n_a.json") as f:
        qa_raw = json.loads(json.load(f))
    qas = qa_raw["music_artist"] + qa_raw["project"]
    for qa in qas:
        order = qas.index(qa) + 1
        q = qa["question"]
        a = ", ".join(qa["answers"])
        context += f"Question {order}: '{q}', and the list of predefined answers they can choose from are: {a}\n\n"
    return context


def gen_application_qs():
    qa = get_all_qa_context()
    ops = get_ops_list()
    app_details = []
    for op in ops:
        op_context = create_op_context(op)
        user_prompt = f"The context below has your screening questions and premade answers they can choose from for each of them so that you know what information you might already have. The context also has all the details about the opportunity you would select for them, depending on the answers to the questions, so that you can create questions as per the instructions above, and make sure you give enough guidance for each of them as part of the question, that will ensure you will receive enough information in order to write the perfect application for the 'music artist' and their project for the funding opportunity below - and list out any additional documents / data / information they must make themselves to submit alongside the application you would write with the answers to their questions, as per the instructions above. \n\n### Context ###\n\n#### \n\n#### Screening Questions and Answer Options ####\n\n{qa}\n\n\n#### Opportunity ####\n\n{op_context}"
        new_data = json.loads(get_response_schema(
            get_app_qs_prompt, user_prompt, ApplicationDetails))
        new_data["opportunity_name"] = op["name"] if "name" in op else "Unknown"
        app_details.append(new_data)
    return app_details
