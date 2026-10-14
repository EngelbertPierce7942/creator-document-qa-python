from src.creator_qa import CreatorQuestionService, QuestionRequest


class FakeClient:
    def search(self, question: str, top_k: int = 3):
        return [
            {"id": "paid-note", "metadata": {"text": "Early access is for paid subscribers.", "subscriber_tier": "paid"}},
            {"id": "public-note", "metadata": {"text": "Downloads use a signed link.", "subscriber_tier": "free"}},
        ]


def test_free_reader_does_not_receive_paid_passage():
    answer = CreatorQuestionService(FakeClient()).answer(QuestionRequest("How do downloads work?", "free"))
    assert answer.sources == ["public-note"]
    assert answer.text == "Downloads use a signed link."
