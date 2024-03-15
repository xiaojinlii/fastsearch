import asyncio
from typing import List

import httpx
from langchain_core.embeddings import Embeddings
from langchain_core.pydantic_v1 import BaseModel, Field


class LangchainEmbeddings(BaseModel, Embeddings):
    base_url: str = Field()

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed search docs."""
        url = f"{self.base_url}/worker_embed_documents"
        response = httpx.post(url, json=texts)
        result = response.json()
        return result

    def embed_query(self, text: str) -> List[float]:
        """Embed query text."""
        url = f"{self.base_url}/worker_embed_query"
        response = httpx.post(url, json=text)
        result = response.json()
        return result

    async def aembed_documents(self, texts: List[str]) -> List[List[float]]:
        """Asynchronous Embed search docs."""
        url = f"{self.base_url}/worker_embed_documents"
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=texts)
        result = response.json()
        return result

    async def aembed_query(self, text: str) -> List[float]:
        """Asynchronous Embed query text."""
        url = f"{self.base_url}/worker_embed_query"
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=text)
        result = response.json()
        return result


async def main():
    embeddings = LangchainEmbeddings(base_url="http://127.0.0.1:21021")
    print(embeddings.embed_query("哈喽"))
    print(embeddings.embed_documents(["哈喽", "嗨"]))
    print(await embeddings.aembed_query("哈喽"))
    print(await embeddings.aembed_documents(["哈喽", "嗨"]))


if __name__ == "__main__":
    asyncio.run(main())
