from src.llm.embedder import Embedder, cosine_similarity
from src.misc.logger import logged


class EmbeddingClassifier:
    embedder = Embedder()

    def __init__(self, classes: list[str]) -> None:
        self.classes = classes
        self.class_embeddings = []

        for cls in classes:
            class_embedding = EmbeddingClassifier.embedder.embed(cls)
            self.class_embeddings.append(class_embedding)

        
    @logged
    def predict(self, texts: list[str]) -> list[str]:
        predictions = []

        for text in texts:
            txt_embedding = EmbeddingClassifier.embedder.embed(text)

            best_score = 0
            best_class = None

            for id, cls_embedding in enumerate(self.class_embeddings):
                similarity = cosine_similarity(txt_embedding, cls_embedding)
                
                print(f"{text=} and {self.classes[id]=} similarity={similarity}")
                if similarity > best_score:
                    best_score = similarity
                    best_class = self.classes[id]

            predictions.append(best_class)

        return predictions