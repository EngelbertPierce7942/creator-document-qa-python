from src.creator_qa import CreatorQuestionService, QuestionRequest


class DemoClient:
    def search(self, question: str, top_k: int = 3):
        return [{"id": "delivery-001", "metadata": {"text": "Digital downloads are delivered by signed link after payment.", "subscriber_tier": "free"}}]


if __name__ == "__main__":
    result = CreatorQuestionService(DemoClient()).answer(QuestionRequest("How are downloads delivered?"))
    print(result.text)
