import pandas as pd
import chromadb
import uuid


class Portfolio:
    """
    A class to manage a portfolio of tech stack information and associated links using ChromaDB.

    Attributes:
        file_path (str): The path to the CSV file containing the portfolio data.
        data (DataFrame): The data read from the CSV file.
        chroma_client (PersistentClient): The ChromaDB client for interacting with the database.
        collection (Collection): The ChromaDB collection for storing portfolio data.
    """

    def __init__(self, file_path="app/resource/v7_portfolio.csv"):
        """
        Initializes the Portfolio object with a default file path, reads the data from the CSV file,
        creates a connection to a ChromaDB client, and gets or creates a collection named "portfolio".

        Args:
            file_path (str): The path to the CSV file containing the portfolio data. Defaults to "app/resource/v7_portfolio.csv".
        """
        self.file_path = file_path
        self.data = pd.read_csv(file_path)
        self.chroma_client = chromadb.PersistentClient('vectorstore')
        self.collection = self.chroma_client.get_or_create_collection(name="portfolio")

    def load_portfolio(self):
        """
        Loads data into the ChromaDB collection if it's empty. Iterates over the rows of the data
        and adds documents to the collection with tech stack information, links, and unique IDs.
        """
        if not self.collection.count():
            for _, row in self.data.iterrows():
                self.collection.add(documents=row["Techstack"],
                                    metadatas={"links": row["Links"]},
                                    ids=[str(uuid.uuid4())])

    def query_links(self, skills):
        """
        Queries the ChromaDB collection with a list of skills and returns metadata for the top 2 results.

        Args:
            skills (list of str): A list of skills to query the collection.

        Returns:
            list of dict: A list of metadata dictionaries for the top 2 results.
        """
        return self.collection.query(query_texts=skills, n_results=2).get('metadatas', [])

