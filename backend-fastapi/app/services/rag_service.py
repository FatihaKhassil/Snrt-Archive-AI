from app.services.chroma_service import ChromaService
from app.services.llm_service import LLMService
from app.repositories.document_repository import DocumentRepository


class RagService:

    FALLBACK_ANSWER = "لم أجد هذه المعلومة في الأرشيف."

    # Nombre de résultats récupérés depuis ChromaDB
    RETRIEVAL_K = 10

    # Nombre maximum de chunks envoyés au LLM
    MAX_CHUNKS_FOR_LLM = 5

    # Taille maximale du contexte
    MAX_CONTEXT = 12000

    def __init__(self):

        self.chroma_service = ChromaService()
        self.llm_service = LLMService()
        self.document_repository = DocumentRepository()

    async def ask(self, question: str) -> dict:

        print("\n========== RAG REQUEST ==========")
        print(f"Question : {question}")

        # ============================================================
        # 1. RECHERCHE SEMANTIQUE DANS CHROMADB
        # ============================================================

        results = await self.chroma_service.search(
            question,
            k=self.RETRIEVAL_K
        )

        print(
            f"Chunks retournés par Chroma : {len(results)}"
        )

        # ============================================================
        # Aucun résultat
        # ============================================================

        if not results:

            print("❌ Aucun résultat trouvé dans ChromaDB.")

            return {
                "answer": self.FALLBACK_ANSWER,
                "chunks": 0,
                "sources": []
            }

        # ============================================================
        # 2. NETTOYAGE ET SUPPRESSION DES DOUBLONS
        # ============================================================

        unique_results = []
        seen_texts = set()

        for index, result in enumerate(
            results,
            start=1
        ):

            # --------------------------------------------------------
            # Récupération du texte
            # --------------------------------------------------------

            if isinstance(result, dict):

                text = (
                    result.get("text")
                    or result.get("page_content")
                    or result.get("content")
                    or ""
                )

                metadata = (
                    result.get("metadata")
                    or {}
                )

                # On récupère éventuellement le score
                score = (
                    result.get("score")
                    if result.get("score") is not None
                    else result.get("similarity")
                )

                distance = result.get("distance")

            else:

                text = getattr(
                    result,
                    "page_content",
                    ""
                )

                metadata = (
                    getattr(
                        result,
                        "metadata",
                        {}
                    )
                    or {}
                )

                score = getattr(
                    result,
                    "score",
                    None
                )

                distance = getattr(
                    result,
                    "distance",
                    None
                )

            text = str(text).strip()

            # --------------------------------------------------------
            # Résultat vide
            # --------------------------------------------------------

            if not text:
                continue

            # --------------------------------------------------------
            # DEBUG : afficher CHAQUE résultat Chroma
            # --------------------------------------------------------

            print(
                f"\n----- RESULTAT CHROMA {index} -----"
            )

            print(
                f"Score    : {score}"
            )

            print(
                f"Distance : {distance}"
            )

            print(
                f"Metadata : {metadata}"
            )

            print(
                f"Text     : {text[:1500]}"
            )

            # --------------------------------------------------------
            # Suppression des doublons
            # --------------------------------------------------------

            if text in seen_texts:
                continue

            seen_texts.add(text)

            item = {
                "text": text,
                "metadata": metadata
            }

            if score is not None:
                item["score"] = score

            if distance is not None:
                item["distance"] = distance

            unique_results.append(item)

            # On conserve maximum 5 chunks
            if (
                len(unique_results)
                >= self.MAX_CHUNKS_FOR_LLM
            ):
                break

        # ============================================================
        # 3. VÉRIFICATION
        # ============================================================

        print(
            "\n========== CHUNKS RETENUS =========="
        )

        print(
            f"Nombre de chunks utilisés : "
            f"{len(unique_results)}"
        )

        if not unique_results:

            print(
                "❌ Aucun chunk exploitable."
            )

            return {
                "answer": self.FALLBACK_ANSWER,
                "chunks": 0,
                "sources": []
            }

        # ============================================================
        # 4. IDENTIFICATION DES DOCUMENTS
        # ============================================================

        document_ids = []

        for index, item in enumerate(
            unique_results,
            start=1
        ):

            text = item["text"]
            metadata = item["metadata"]

            print(
                f"\n----- CHUNK FINAL {index} -----"
            )

            print(
                f"Metadata : {metadata}"
            )

            print(
                f"Text : {text}"
            )

            document_id = metadata.get(
                "document_id"
            )

            if document_id:

                document_id = str(
                    document_id
                )

                if document_id not in document_ids:

                    document_ids.append(
                        document_id
                    )

        print(
            "\n========== DOCUMENT IDS =========="
        )

        print(
            document_ids
        )

        # ============================================================
        # 5. CONSTRUCTION DU CONTEXTE
        # ============================================================

        context_parts = []
        current_length = 0

        for index, item in enumerate(
            unique_results,
            start=1
        ):

            text = item["text"]

            passage = (
                f"\n"
                f"================ PASSAGE {index} ================\n"
                f"{text}\n"
                f"============== FIN PASSAGE {index} ==============\n"
            )

            remaining = (
                self.MAX_CONTEXT
                - current_length
            )

            if remaining <= 0:
                break

            # --------------------------------------------------------
            # Si le passage dépasse la limite
            # --------------------------------------------------------

            if len(passage) > remaining:

                # Si aucun passage n'a encore été ajouté,
                # on coupe exceptionnellement.
                if not context_parts:

                    passage = passage[:remaining]

                else:

                    # On évite de couper un chunk pertinent
                    break

            context_parts.append(
                passage
            )

            current_length += len(
                passage
            )

        context = "\n".join(
            context_parts
        )

        print(
            "\n========== CONTEXT =========="
        )

        print(
            f"Taille du contexte : "
            f"{len(context)} caractères"
        )

        print(context)

        # ============================================================
        # 6. PROMPT RAG
        # ============================================================

        prompt = f"""
أنت مساعد ذكي متخصص في البحث داخل أرشيف SNRT.

مهمتك هي الإجابة عن سؤال المستخدم اعتماداً حصراً على المعلومات
الموجودة في المقاطع المسترجعة من أرشيف SNRT.

========================
قواعد مهمة جداً
========================

1. اقرأ جميع المقاطع قبل الإجابة.

2. حلل السؤال أولاً وحدد الكلمات والعبارات الأساسية فيه.

3. ابحث عن المعلومة المطلوبة داخل جميع المقاطع.

4. إذا وجدت عبارة مطابقة أو قريبة جداً من الكلمات الأساسية
   في السؤال، استخدم المعلومات المرتبطة بها للإجابة.

5. إذا كان السؤال عن "موضوع" برنامج أو فقرة، ابحث عن السطر
   الذي يحتوي على "الموضوع" المرتبط بذلك البرنامج أو الفقرة.

6. إذا كان السؤال عن شخص، ابحث عن اسمه ودوره أو صفته.

7. إذا كان السؤال عن وقت، ابحث عن التوقيت المرتبط بالبرنامج.

8. إذا كان السؤال عن حلقة، ابحث عن رقم الحلقة.

9. قد تكون بعض المقاطع غير مرتبطة بالسؤال.
   تجاهل المقاطع غير المرتبطة.

10. لا تعتمد على مقطع واحد فقط إذا كانت المعلومة المطلوبة
    يمكن العثور عليها في مقطع آخر.

11. لا تضف أي معلومة من معرفتك الخاصة.

12. لا تخترع أسماء أو أحداثاً أو تواريخ أو تفاصيل.

13. إذا كانت الإجابة موجودة بوضوح في المقاطع،
    أجب عنها مباشرة.

14. لا تقل "لم أجد هذه المعلومة في الأرشيف" إذا كانت
    المعلومة موجودة في أحد المقاطع.

15. إذا كانت المعلومة موجودة بشكل جزئي، استخدم الجزء الموجود
    فقط ولا تخترع الجزء الناقص.

16. أجب بجملة كاملة وواضحة ومباشرة.

17. لا تكرر السؤال في الإجابة.

18. لا تذكر أرقام المقاطع أو كلمة "المقطع" في الإجابة.

19. لا تبدأ الإجابة بعبارات مثل:
    "وفقاً للمقطع"
    أو
    "حسب الوثيقة"
    إلا إذا كان ذلك ضرورياً.

20. أجب بنفس لغة السؤال.

21. إذا كان السؤال باللغة العربية، أجب باللغة العربية.

22. إذا كان السؤال باللغة الفرنسية، أجب باللغة الفرنسية.

23. إذا كانت المعلومة المطلوبة غير موجودة فعلاً في جميع
    المقاطع، أجب فقط:

    "لم أجد هذه المعلومة في الأرشيف."

24. لا تستخدم أي معلومات خارج المقاطع المقدمة.

========================
المقاطع المسترجعة من الأرشيف
========================

{context}

========================
سؤال المستخدم
========================

{question}

========================
تعليمات نهائية
========================

حلل السؤال أولاً، ثم ابحث عن المعلومات المتعلقة به داخل
جميع المقاطع.

إذا وجدت المعلومة المطلوبة، قدم إجابة واضحة ومباشرة وكاملة.

لا تذكر المقاطع أو أرقامها في الإجابة.

إذا لم تجد المعلومة فعلاً، أجب:

"لم أجد هذه المعلومة في الأرشيف."

الإجابة:
"""

        # ============================================================
        # 7. AFFICHAGE DU PROMPT
        # ============================================================

        print(
            "\n========== PROMPT ENVOYÉ AU LLM ==========\n"
        )

        print(prompt)

        print(
            "\n========== FIN PROMPT ==========\n"
        )

        # ============================================================
        # 8. APPEL DU LLM
        # ============================================================

        answer = await self.llm_service.generate(
            prompt
        )

        if answer is None:
            answer = ""

        answer = str(
            answer
        ).strip()

        print(
            "\n========== LLM ANSWER =========="
        )

        print(
            answer
        )

        # ============================================================
        # 9. SOURCES
        # ============================================================

        sources = []

        # ------------------------------------------------------------
        # Tous les documents correspondant aux chunks retenus
        # ------------------------------------------------------------

        display_document_ids = []

        for item in unique_results:

            metadata = item["metadata"]

            document_id = metadata.get(
                "document_id"
            )

            if not document_id:
                continue

            document_id = str(
                document_id
            )

            if document_id not in display_document_ids:

                display_document_ids.append(
                    document_id
                )

        print(
            "\n========== SOURCE IDS AFFICHÉS =========="
        )

        print(
            display_document_ids
        )

        # ============================================================
        # 10. RÉCUPÉRATION DES DOCUMENTS MONGODB
        # ============================================================

        if display_document_ids:

            try:

                documents = await (
                    self.document_repository
                    .get_documents(
                        display_document_ids
                    )
                )

                print(
                    f"Documents MongoDB récupérés : "
                    f"{len(documents)}"
                )

                documents_by_id = {

                    str(document.get("_id")):
                    document

                    for document in documents
                }

                # ----------------------------------------------------
                # Une source par document
                # ----------------------------------------------------

                added_sources = set()

                for item in unique_results:

                    metadata = item["metadata"]

                    document_id = metadata.get(
                        "document_id"
                    )

                    if not document_id:
                        continue

                    document_id = str(
                        document_id
                    )

                    if document_id in added_sources:
                        continue

                    document = (
                        documents_by_id.get(
                            document_id
                        )
                    )

                    if not document:

                        print(
                            f"⚠️ Document MongoDB "
                            f"introuvable : "
                            f"{document_id}"
                        )

                        continue

                    filename = (
                        document.get(
                            "original_filename"
                        )
                        or document.get(
                            "filename"
                        )
                        or document.get(
                            "file_name"
                        )
                        or document.get(
                            "name"
                        )
                        or ""
                    )

                    title = (
                        document.get(
                            "title"
                        )
                        or filename
                        or ""
                    )

                    source = {

                        "document_id":
                            document_id,

                        "title":
                            title,

                        "filename":
                            filename,

                        "file_type":
                            document.get(
                                "file_type"
                            ) or "",

                        "excerpt":
                            item["text"]
                    }

                    if document.get(
                        "mime_type"
                    ):

                        source["mime_type"] = (
                            document[
                                "mime_type"
                            ]
                        )

                    if document.get(
                        "file_size"
                    ) is not None:

                        source["file_size"] = (
                            document[
                                "file_size"
                            ]
                        )

                    if document.get(
                        "created_at"
                    ):

                        source["created_at"] = str(
                            document[
                                "created_at"
                            ]
                        )

                    sources.append(
                        source
                    )

                    added_sources.add(
                        document_id
                    )

            except Exception as e:

                print(
                    "❌ Erreur récupération MongoDB source:"
                )

                print(
                    f"{type(e).__name__}: {e}"
                )

        # ============================================================
        # 11. RÉPONSE FINALE
        # ============================================================

        result = {

            "answer":
                answer,

            "chunks":
                len(unique_results),

            "sources":
                sources
        }

        print(
            "\n========== SOURCES AFFICHÉES =========="
        )

        print(
            sources
        )

        print(
            "\n========== RAG RESPONSE =========="
        )

        print(
            result
        )

        print(
            "==================================\n"
        )

        return result