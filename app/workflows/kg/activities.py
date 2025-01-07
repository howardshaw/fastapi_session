from typing import Any

from langchain_community.document_loaders import PyPDFLoader
from langchain_community.graphs.graph_document import GraphDocument
from langchain_core.documents import Document
from langchain_core.language_models import BaseChatModel
from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_neo4j import GraphCypherQAChain, Neo4jGraph
from langchain_neo4j.graphs.graph_store import GraphStore
from langchain_text_splitters import RecursiveCharacterTextSplitter
from temporalio import activity


class LoaderActivity:
    @activity.defn
    async def run(self) -> list[Document]:
        loader = PyPDFLoader("example_data/layout-parser-paper.pdf")
        return loader.load()


class SplitterActivity:
    @activity.defn
    async def run(self, documents: list[Document]) -> list[Document]:
        text_splitter = RecursiveCharacterTextSplitter()
        return text_splitter.split_documents(documents)


class TransformerActivity:
    def __init__(self, llm: BaseChatModel):
        self._llm = llm

    @activity.defn
    async def run(self, documents: list[Document]) -> list[GraphDocument]:
        llm_transformer = LLMGraphTransformer(
            llm=self._llm,
            allowed_nodes=["Person", "Country", "Organization"],
            allowed_relationships=["NATIONALITY", "LOCATED_IN", "WORKED_AT", "SPOUSE"],
        )
        graph_documents = llm_transformer.convert_to_graph_documents(
            documents
        )

        return graph_documents


class IndexActivity:
    def __init__(self, url: str, username: str, password: str):
        self._graph = Neo4jGraph(
            url=url,
            username=username,
            password=password,
        )

    @activity.defn
    async def run(self, graph_documents: list[GraphDocument]) -> GraphStore:
        self._graph.add_graph_documents(
            graph_documents,
            baseEntityLabel=True,
            include_source=True
        )
        return self._graph


class RetrieveActivity:
    def __init__(self, llm: BaseChatModel):
        self._llm = llm

    @activity.defn
    async def run(self, graph: GraphStore, query: str) -> dict[str, Any]:
        chain = GraphCypherQAChain.from_llm(
            graph=graph,
            llm=self._llm,
            verbose=True,
            allow_dangerous_requests=True
        )
        response = await chain.ainvoke({"query": query})
        return response




