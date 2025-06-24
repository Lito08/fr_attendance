# attendance/management/commands/train_recognizer.py

import os
import pickle
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from sklearn.preprocessing import LabelEncoder
from sklearn.svm import SVC

class Command(BaseCommand):
    help = "Train face‐recognition SVM: embeddings.pickle → recognizer.pickle + le.pickle"

    def add_arguments(self, parser):
        parser.add_argument(
            "--embeddings",
            default=os.path.join(settings.BASE_DIR, "output", "embeddings.pickle"),
            help="Path to embeddings.pickle",
        )
        parser.add_argument(
            "--recognizer",
            default=os.path.join(settings.BASE_DIR, "output", "recognizer.pickle"),
            help="Where to write recognizer.pickle",
        )
        parser.add_argument(
            "--le",
            default=os.path.join(settings.BASE_DIR, "output", "le.pickle"),
            help="Where to write label encoder (le.pickle)",
        )

    def handle(self, *args, **opts):
        emb_path = opts["embeddings"]
        rec_path = opts["recognizer"]
        le_path  = opts["le"]

        if not os.path.isfile(emb_path):
            raise CommandError(f"Embeddings file not found: {emb_path}")

        self.stdout.write("🔄 Loading embeddings…")
        with open(emb_path, "rb") as f:
            data = pickle.load(f)

        self.stdout.write("🏷 Encoding labels…")
        le = LabelEncoder()
        labels = le.fit_transform(data["names"])

        self.stdout.write("⚙️ Training SVM…")
        recognizer = SVC(C=1.0, kernel="linear", probability=True)
        recognizer.fit(data["embeddings"], labels)

        # ensure output dir exists
        os.makedirs(os.path.dirname(rec_path), exist_ok=True)

        self.stdout.write(f"💾 Saving recognizer to {rec_path}")
        with open(rec_path, "wb") as f:
            pickle.dump(recognizer, f)

        self.stdout.write(f"💾 Saving label encoder to {le_path}")
        with open(le_path, "wb") as f:
            pickle.dump(le, f)

        self.stdout.write(self.style.SUCCESS(
            f"✔️  Trained model written to {rec_path}\n"
            f"✔️  Label encoder written to {le_path}"
        ))
