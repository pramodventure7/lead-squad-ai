import os
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.exceptions import OutputParserException
from dotenv import load_dotenv

load_dotenv()

class Chain:
    """
    A class to interact with the ChatGroq language model for extracting job postings and writing business emails.

    Attributes:
        llm (ChatGroq): The language model used for generating responses.
    """

    def __init__(self):
        """
        Initializes the Chain object with a ChatGroq language model.
        """
        self.llm = ChatGroq(temperature=0, groq_api_key=os.getenv("GROQ_API_KEY"), model_name="llama-3.3-70b-versatile")

    def extract_jobs(self, cleaned_text):
        """
        Extracts job postings from the cleaned text using the language model.

        Args:
            cleaned_text (str): The cleaned text data from which to extract job postings.

        Returns:
            list: A list of dictionaries containing job postings with keys: 'role', 'experience', 'skills', and 'description'.

        Raises:
            OutputParserException: If the response cannot be parsed into valid JSON.
        """
        prompt_extract = PromptTemplate.from_template(
            """
            ### SCRAPED TEXT FROM WEBSITE:
            {page_data}
            ### INSTRUCTION:
            The scraped text is from the career's page of a website.
            Your job is to extract the job postings and return them in JSON format containing the following keys: `role`, `experience`, `skills` and `description`.
            Only return the valid JSON.
            ### VALID JSON (NO PREAMBLE):
            """
        )
        chain_extract = prompt_extract | self.llm
        res = chain_extract.invoke(input={"page_data": cleaned_text})
        try:
            json_parser = JsonOutputParser()
            res = json_parser.parse(res.content)
        except OutputParserException:
            raise OutputParserException("Context too big. Unable to parse jobs.")
        return res if isinstance(res, list) else [res]

    def write_mail(self, job, links):
        """
        Writes a business email based on the job description and relevant links using the language model.

        Args:
            job (dict): A dictionary containing job details.
            links (list): A list of relevant links to include in the email.

        Returns:
            str: The generated business email content.
        """
        prompt_email = PromptTemplate.from_template(
            """
            ### JOB DESCRIPTION:
            {job_description}

            ### INSTRUCTION:
            You are Pramod Kumar, a business development executive at Venture7. Venture7 is an AI & Software Consulting company dedicated to facilitating
            the seamless integration of business processes through automated tools. 
            Over our experience, we have empowered numerous enterprises with tailored solutions, fostering scalability, 
            process optimization, cost reduction, and heightened overall efficiency. 
            Your job is to write a cold email to the client regarding the job mentioned above describing the capability of Venture7 
            in fulfilling their needs.
            Also add the most relevant ones from the following links to showcase Venture7's portfolio: {link_list}
            Remember you are Pramod Kumar, BDE at Venture7. 
            Do not provide a preamble.
            ### EMAIL (NO PREAMBLE):

            """
        )
        chain_email = prompt_email | self.llm
        res = chain_email.invoke({"job_description": str(job), "link_list": links})
        return res.content

if __name__ == "__main__":
    print(os.getenv("GROQ_API_KEY"))
    

    
