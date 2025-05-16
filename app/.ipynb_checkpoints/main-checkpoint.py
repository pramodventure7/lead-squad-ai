import streamlit as st
from langchain_community.document_loaders import WebBaseLoader
from email.mime.text import MIMEText
import smtplib
import re

st.write("Debug: Job data", job_data)
print("DEBUG:", some_variable)


from chains import Chain
from portfolio import Portfolio
from utils import clean_text
from company_scraper import extract_company_info, find_job_links

# 📧 Gmail credentials from Streamlit secrets
GMAIL_USER = st.secrets["GMAIL_USER"]
GMAIL_APP_PASSWORD = st.secrets["GMAIL_APP_PASSWORD"]

def send_email_via_gmail(recipient_email, subject, body):
    msg = MIMEText(body, "plain")
    msg["Subject"] = subject
    msg["From"] = GMAIL_USER
    msg["To"] = recipient_email

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            smtp.send_message(msg)
        return True
    except Exception as e:
        return f"❌ Failed to send: {e}"

def extract_subject_and_body(email_text):
    """
    Extract subject line if present, then clean from body.
    Looks for lines like: Subject: XYZ
    """
    subject_match = re.search(r"^Subject:\s*(.+)$", email_text, re.MULTILINE)
    subject = subject_match.group(1).strip() if subject_match else "Job Application"

    # Remove the subject line from email body
    cleaned_email = re.sub(r"^Subject:.*\n?", "", email_text, flags=re.MULTILINE).strip()
    return subject, cleaned_email

def create_streamlit_app(llm, portfolio, clean_text):
    st.title("📧 Business Email Assistant")
    st.markdown("Generate tailored business emails from job descriptions with smart company insights.")

    # Step 1: Company info input
    company_url = st.text_input("🔗 Enter Company Website URL")
    if company_url and st.button("🔍 Scrape Company Info"):
        try:
            with st.spinner("Scraping homepage and career page..."):
                info = extract_company_info(company_url)
                career_url, job_links = find_job_links(company_url)

                st.session_state.company_info = info
                st.session_state.career_url = career_url
                st.session_state.job_links = job_links
        except Exception as e:
            st.error(f"An error occurred while scraping: {e}")

    # Display company info
    if st.session_state.get("company_info"):
        st.subheader("🏢 Company Information")
        st.markdown(f"**Title:** {st.session_state.company_info.get('title', '')}")
        st.markdown(f"**Description:** {st.session_state.company_info.get('description', '')}")
        if st.session_state.company_info.get("services"):
            st.markdown("**Services:**")
            for s in st.session_state.company_info["services"]:
                st.markdown(f"- {s}")
        if st.session_state.get("career_url"):
            st.markdown(f"**Career Page:** [Visit here]({st.session_state.career_url})", unsafe_allow_html=True)

    # Display job links
    if st.session_state.get("job_links"):
        st.subheader("📌 Available Jobs from Career Page")
        for title, link in st.session_state.job_links:
            st.markdown(f"- [{title}]({link})", unsafe_allow_html=True)

    st.divider()

    # Step 2: Job URL input
    job_url = st.text_input("📄 Enter a Job URL (e.g., https://career.infosys.com/jobdesc?jobReferenceCode=...)")
    generate_btn = st.button("✉️ Generate Business Emails")

    if generate_btn and job_url:
        try:
            with st.spinner("Fetching job data and generating emails..."):
                loader = WebBaseLoader([job_url])
                data = clean_text(loader.load().pop().page_content)
                portfolio.load_portfolio()
                jobs = llm.extract_jobs(data)

                st.session_state.generated_emails = []
                for job in jobs:
                    skills = job.get('skills', [])
                    links = portfolio.query_links(skills)
                    raw_email = llm.write_mail(job, links)
                    subject, cleaned_email = extract_subject_and_body(raw_email)
                    st.session_state.generated_emails.append({
                        "title": job.get("title", "Job Email"),
                        "subject": subject,
                        "email": cleaned_email
                    })
        except Exception as e:
            st.error(f"❌ An Error Occurred: {e}")

    # Step 3: Show generated emails
    if st.session_state.get("generated_emails"):
        st.subheader("📬 Generated Email(s)")
        for idx, email_obj in enumerate(st.session_state.generated_emails):
            title = email_obj["title"]
            subject = email_obj["subject"]
            email_text = email_obj["email"]

            st.markdown(f"#### ✉️ {title}")
            subject_input = st.text_input("📌 Subject Line", value=subject, key=f"subject_{idx}")
            edited_email = st.text_area("✏️ Edit your email:", value=email_text, height=300, key=f"editable_email_{idx}")

            st.download_button(
                label="💾 Download Email (.md)",
                data=edited_email,
                file_name=f"{title.replace(' ', '_')}.md",
                mime="text/markdown",
                key=f"download_{idx}"
            )

            with st.expander("📤 Send via Gmail"):
                recipient = st.text_input("Recipient Email", key=f"recipient_{idx}")
                if st.button("📧 Send Email Now", key=f"send_{idx}"):
                    if recipient:
                        result = send_email_via_gmail(recipient, subject_input, edited_email)
                        if result is True:
                            st.success("✅ Email sent successfully!")
                        else:
                            st.error(result)
                    else:
                        st.warning("⚠️ Please enter the recipient email.")

if __name__ == "__main__":
    chain = Chain()
    portfolio = Portfolio()
    st.set_page_config(layout="wide", page_title="Business Email Assistant", page_icon="📧")
    create_streamlit_app(chain, portfolio, clean_text)
