from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings


class ChromaService:

    def __init__(self):

        embeddings = OllamaEmbeddings(
            model="nomic-embed-text",
            base_url="http://ollama:11434"
        )

        self.vector_store = Chroma(
            collection_name="snrt_documents",
            embedding_function=embeddings,
            host="chroma",
            port=8000
        )

    async def search(
        self,
        question: str,
        k: int = 10
    ):

        print(
            "\n========== CHROMA SEARCH ==========",
            flush=True
        )

        print(
            f"Question : {question}",
            flush=True
        )

        print(
            f"K demandé : {k}",
            flush=True
        )

        try:

            # ========================================================
            # Recherche sémantique AVEC scores
            # ========================================================

            results = self.vector_store.similarity_search_with_score(
                query=question,
                k=k
            )

            print(
                f"Nombre de résultats Chroma : {len(results)}",
                flush=True
            )

            formatted_results = []

            # ========================================================
            # Affichage des résultats
            # ========================================================

            for index, (document, score) in enumerate(
                results,
                start=1
            ):

                metadata = (
                    document.metadata
                    if document.metadata
                    else {}
                )

                text = (
                    document.page_content
                    if document.page_content
                    else ""
                )

                print(
                    f"\n----- CHROMA RESULT {index} -----",
                    flush=True
                )

                print(
                    f"Score / Distance : {score}",
                    flush=True
                )

                print(
                    f"Metadata : {metadata}",
                    flush=True
                )

                print(
                    f"Text : {text[:1500]}",
                    flush=True
                )

                # ====================================================
                # Format utilisé par RagService
                # ====================================================

                formatted_results.append(
                    {
                        "text": text,
                        "metadata": metadata,
                        "score": float(score)
                    }
                )

            print(
                "\n========== FIN CHROMA SEARCH ==========\n",
                flush=True
            )

            return formatted_results

        except Exception as e:

            print(
                "\n❌ ERREUR CHROMA SEARCH",
                flush=True
            )

            print(
                f"Type : {type(e).__name__}",
                flush=True
            )

            print(
                f"Message : {e}",
                flush=True
            )

            print(
                "=====================================\n",
                flush=True
            )

            return []

    async def delete_by_document_id(
        self,
        document_id: str
    ):

        document_id = str(document_id)

        print(
            f"🗑️ ChromaDB : suppression du document {document_id}",
            flush=True
        )

        try:

            self.vector_store.delete(
                where={
                    "document_id": document_id
                }
            )

            print(
                f"✅ ChromaDB : document {document_id} supprimé",
                flush=True
            )

        except Exception as e:

            print(
                "❌ Erreur suppression ChromaDB",
                flush=True
            )

            print(
                f"{type(e).__name__}: {e}",
                flush=True
            )