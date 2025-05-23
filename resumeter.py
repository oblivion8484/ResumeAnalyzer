import fitz  # PyMuPDF
import spacy
import json
import re
import string
from flask import Flask, request, jsonify

app = Flask(__name__)

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

# Job titles and their associated skills
tech_jobs_skills = {
    "Data Engineer": ["Python", "SQL", "ETL", "Apache Spark", "AWS", "Data Warehousing", "Airflow"],
    "Web Developer": ["HTML", "CSS", "JavaScript", "React", "Node.js", "REST APIs", "Git"],
    "Data Scientist": ["Python", "Pandas", "Machine Learning", "scikit-learn", "Statistics", "Jupyter", "SQL"],
    "Machine Learning Engineer": ["Python", "TensorFlow", "PyTorch", "scikit-learn", "ML algorithms", "Docker"],
    "Backend Developer": ["Python", "Node.js", "Java", "SQL", "MongoDB", "REST APIs", "Docker"],
    "Frontend Developer": ["HTML", "CSS", "JavaScript", "React", "Vue.js", "UI/UX", "Figma"],
    "DevOps Engineer": ["Linux", "Docker", "Kubernetes", "CI/CD", "AWS", "Terraform", "Python"],
    "Cloud Engineer": ["AWS", "Azure", "GCP", "Terraform", "Docker", "Networking", "Linux"],
    "Database Administrator": ["SQL", "MySQL", "PostgreSQL", "Oracle", "Backup & Recovery", "Indexing"],
    "Full Stack Developer": ["HTML", "CSS", "JavaScript", "React", "Node.js", "MongoDB", "Express"],
    "AI Engineer": ["Python", "Machine Learning", "Deep Learning", "TensorFlow", "NLP", "OpenCV"],
    "Software Engineer": ["Java", "C++", "Python", "OOP", "Algorithms", "Git", "Agile"],
    "Cybersecurity Analyst": ["Networking", "Firewalls", "Python", "Risk Assessment", "Penetration Testing", "SIEM"],
    "Mobile App Developer": ["Kotlin", "Swift", "Flutter", "React Native", "Java", "UI/UX"],
    "UI/UX Designer": ["Figma", "Adobe XD", "Sketch", "Wireframing", "Prototyping", "User Research"],
    "Systems Analyst": ["Requirements Gathering", "SQL", "System Design", "Problem Solving", "Documentation"],
    "QA Engineer": ["Selenium", "Python", "Test Cases", "Bug Tracking", "JIRA", "Automation"],
    "Product Manager": ["Roadmapping", "Agile", "JIRA", "Wireframing", "Analytics", "Communication"],
    "Blockchain Developer": ["Solidity", "Ethereum", "Smart Contracts", "Web3.js", "Cryptography", "DApps"],
    "Technical Support Engineer": ["Troubleshooting", "Linux", "Windows", "Networking", "Customer Support", "Scripting"]
}

HEADINGS = {
    "skill": 17,
    "experience": 17,
    "language": 17,
    "education": 17,
    "contact": 17
}

LENGTH_MAX_POINTS = 15
TOKEN_LOWER_THRESHOLD = 150
TOKEN_UPPER_THRESHOLD = 600

def extract_text_from_pdf(pdf_file):
    text = ""
    with fitz.open(stream=pdf_file.read(), filetype="pdf") as doc:
        for page in doc:
            text += page.get_text()
    return text

def simple_tokenize(text):
    translator = str.maketrans(string.punctuation, ' '*len(string.punctuation))
    text_no_punct = text.translate(translator)
    tokens = text_no_punct.strip().split()
    return tokens

def contains_contact_info(text):
    email_pattern = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
    phone_pattern = re.compile(r"(\+?\d{1,3}[-.\s]?)?(\(?\d{3}\)?[-.\s]?){1,2}\d{3,4}")
    keywords = ["phone", "email", "contact"]

    if email_pattern.search(text):
        return True
    if phone_pattern.search(text):
        return True
    lowered_text = text.lower()
    for kw in keywords:
        if kw in lowered_text:
            return True
    return False

def score_length_by_tokens(tokens):
    token_count = len(tokens)
    if TOKEN_LOWER_THRESHOLD <= token_count <= TOKEN_UPPER_THRESHOLD:
        return LENGTH_MAX_POINTS, "Ideal token length for ATS parsing.", token_count
    else:
        if token_count < TOKEN_LOWER_THRESHOLD:
            diff = TOKEN_LOWER_THRESHOLD - token_count
            max_diff = TOKEN_LOWER_THRESHOLD
            penalty = (diff / max_diff) * LENGTH_MAX_POINTS
            score = max(LENGTH_MAX_POINTS - penalty, 0)
            return score, f"Token length too short by {diff} tokens; score reduced.", token_count
        else:
            diff = token_count - TOKEN_UPPER_THRESHOLD
            max_diff = TOKEN_UPPER_THRESHOLD
            penalty = (diff / max_diff) * LENGTH_MAX_POINTS
            score = max(LENGTH_MAX_POINTS - penalty, 0)
            return score, f"Token length too long by {diff} tokens; score reduced.", token_count

def split_sections_by_headings(text, headings):
    pattern = '|'.join([fr'(?P<{h}>{h})(:)?' for h in headings])
    regex = re.compile(pattern, flags=re.IGNORECASE)

    indices = []
    for match in regex.finditer(text):
        indices.append((match.start(), match.lastgroup.lower()))
    indices.append((len(text), None))

    sections = {}
    for i in range(len(indices) - 1):
        start_idx = indices[i][0]
        heading = indices[i][1]
        end_idx = indices[i+1][0]
        section_text = text[start_idx:end_idx].strip()
        heading_regex = re.compile(fr'^{heading}(:)?', re.IGNORECASE)
        section_text = heading_regex.sub('', section_text).strip()
        if heading:
            if heading not in sections:
                sections[heading] = section_text
            else:
                sections[heading] += '\n' + section_text
    return sections

def analyze_section_content(heading, content):
    messages = []
    score = 0
    content_lower = content.lower()

    if heading == "skill":
        skills_found = [sk for sk in tech_jobs_skills["Software Engineer"] if sk.lower() in content_lower]
        if len(skills_found) == 0:
            messages.append("No recognized skills found in skills section.")
            score = 0
        else:
            coverage = len(skills_found) / len(tech_jobs_skills["Software Engineer"])
            score = coverage
            if coverage < 0.5:
                messages.append("Limited skill diversity; consider adding more relevant skills.")
            if coverage < 1.0:
                missing_skills = set(tech_jobs_skills["Software Engineer"]) - set(skills_found)
                messages.append(f"Consider adding skills: {', '.join(missing_skills)}")
    elif heading == "experience":
        years_pattern = re.compile(r'(\d{4}|\d+-\d+ years?|present)', re.IGNORECASE)
        if years_pattern.search(content):
            score = 1.0
        else:
            score = 0.5
            messages.append("Experience section found but lacks details like dates or duration.")
    elif heading == "language":
        languages = {"english", "spanish", "french", "german", "mandarin", "hindi", "c++", "python", "java", "javascript"}
        found_langs = [lang for lang in languages if lang in content_lower]
        if len(found_langs) > 0:
            score = min(1.0, len(found_langs)/3)
        else:
            score = 0
            messages.append("No languages detected in language section.")
    elif heading == "education":
        degree_keywords = ["bachelor", "master", "phd", "degree", "university", "college", "graduation"]
        year_pattern = re.compile(r'\b(19|20)\d{2}\b')
        degree_found = any(kw in content_lower for kw in degree_keywords)
        year_found = bool(year_pattern.search(content))
        if degree_found and year_found:
            score = 1.0
        elif degree_found or year_found:
            score = 0.5
            messages.append("Education section is partially detailed; consider adding graduation years or degree type.")
        else:
            score = 0
            messages.append("Education section missing key details.")
    elif heading == "contact":
        if contains_contact_info(content):
            score = 17.0
        else:
            score = 0
            messages.append("Contact section missing email or phone number.")
    else:
        score = 0
        messages.append(f"No analysis rule defined for heading '{heading}'.")
    return score, messages

def extract_job_title(full_text):
    lines = full_text.splitlines()
    for line in lines:
        clean_line = line.strip()
        if clean_line:
            return clean_line
    return ""

def clean_job_title(job_title: str) -> str:
    words_to_remove = {"professional", "intern"}
    words = job_title.lower().split()
    filtered_words = [word for word in words if word not in words_to_remove]
    cleaned_title = " ".join(filtered_words).title()
    return cleaned_title

def analyze_resume(full_text):
    total_points = 100
    heading_points_total = sum(HEADINGS.values())
    results_msgs = []

    job_title_raw = extract_job_title(full_text)
    job_title = clean_job_title(job_title_raw)

    tokens = simple_tokenize(full_text)
    length_score, length_msg, token_count = score_length_by_tokens(tokens)

    sections = split_sections_by_headings(full_text, HEADINGS.keys())

    heading_scores = {}
    total_heading_score_weighted = 0

    for heading, max_points in HEADINGS.items():
        section_content = sections.get(heading, "")
        if section_content:
            partial_score, msgs = analyze_section_content(heading, section_content)
            heading_scores[heading] = partial_score * max_points
            if msgs:
                results_msgs.extend(msgs)
        else:
            heading_scores[heading] = 0
            results_msgs.append(f"Missing heading or content: {heading}")

        total_heading_score_weighted += heading_scores[heading]

    if job_title and job_title in tech_jobs_skills:
        required_skills = tech_jobs_skills[job_title]
        skills_section = sections.get("skill", "").lower() if "skill" in sections else ""
        skills_found = [sk for sk in required_skills if sk.lower() in skills_section]
        missing_skills = set(required_skills) - set(skills_found)
        for skill in missing_skills:
            total_heading_score_weighted -= 2
            results_msgs.append(f"Missing required skill for {job_title}: {skill}")
    else:
        skill_points = HEADINGS.get("skill", 0)
        total_heading_score_weighted -= skill_points
        total_heading_score_weighted += 14

    total_heading_score_weighted = max(min(total_heading_score_weighted, heading_points_total), 0)

    final_score = total_heading_score_weighted + length_score
    final_score = max(min(final_score, total_points), 0)

    results_msgs.append(length_msg)

    return json.dumps({
        "score": round(final_score, 2),
        "suggestions": results_msgs
    }, indent=4)

@app.route("/upload", methods=["POST"])
def upload_pdf():
    if "resume" not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files["resume"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400
    try:
        full_text = extract_text_from_pdf(file)
        result = analyze_resume(full_text)
        return jsonify(json.loads(result))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
