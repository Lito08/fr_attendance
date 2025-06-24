import os
import pickle
import cv2
import numpy as np
from imutils import paths
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):
    help = (
        "Walks through a dataset folder of subfolders==labels, "
        "extracts OpenFace embeddings, and dumps to a pickle."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "dataset_dir",
            help="Path to root dataset (each subdirectory is a person label)",
        )
        parser.add_argument(
            "output_file",
            help="Path where embeddings.pickle will be written",
        )
        parser.add_argument(
            "--min-conf",
            type=float,
            default=0.5,
            help="Minimum face‐detector confidence (default=0.5)",
        )

        # You can override these if your models live elsewhere:
        parser.add_argument(
            "--proto",
            default=os.path.join(settings.BASE_DIR, "face_recognition", "face_detection_model", "deploy.prototxt"),
            help="Path to Caffe deploy.prototxt",
        )
        parser.add_argument(
            "--model",
            default=os.path.join(settings.BASE_DIR, "face_recognition", "face_detection_model", "res10_300x300_ssd_iter_140000.caffemodel"),
            help="Path to Caffe .caffemodel",
        )
        parser.add_argument(
            "--embedder",
            default=os.path.join(settings.BASE_DIR, "face_recognition", "openface_nn4.small2.v1.t7"),
            help="Path to OpenFace embedding .t7",
        )

    def handle(self, *args, **opts):
        dataset_dir = opts["dataset_dir"]
        output_file = opts["output_file"]
        min_conf    = opts["min_conf"]
        protoPath   = opts["proto"]
        modelPath   = opts["model"]
        embedPath   = opts["embedder"]

        if not os.path.isdir(dataset_dir):
            raise CommandError(f"Dataset directory not found: {dataset_dir}")

        self.stdout.write("🔎 Loading face detector…")
        detector = cv2.dnn.readNetFromCaffe(protoPath, modelPath)

        self.stdout.write("🔗 Loading embedding model…")
        embedder = cv2.dnn.readNetFromTorch(embedPath)

        imagePaths = list(paths.list_images(dataset_dir))
        self.stdout.write(f"🗂️  Found {len(imagePaths)} images under {dataset_dir}")

        knownEmbeddings = []
        knownNames      = []
        total = 0

        for (i, imagePath) in enumerate(imagePaths):
            if i and i % 50 == 0:
                self.stdout.write(f"  • processing image {i}/{len(imagePaths)}…")

            name = os.path.basename(os.path.dirname(imagePath))
            image = cv2.imread(imagePath)
            if image is None:
                self.stderr.write(f"⚠️  cannot read: {imagePath}")
                continue

            # resize to width=600
            h, w = image.shape[:2]
            if w != 600:
                image = cv2.resize(image, (600, int(600*h/w)))
                h, w = image.shape[:2]

            # face detect
            blob = cv2.dnn.blobFromImage(
                cv2.resize(image, (300,300)),
                1.0, (300,300),
                (104.0,177.0,123.0),
                swapRB=False, crop=False
            )
            detector.setInput(blob)
            detections = detector.forward()

            if detections.shape[2] == 0:
                continue

            # pick the highest‐confidence detection
            idx       = np.argmax(detections[0,0,:,2])
            confidence= detections[0,0,idx,2]
            if confidence < min_conf:
                continue

            # extract ROI
            box = detections[0,0,idx,3:7] * np.array([w,h,w,h])
            (startX, startY, endX, endY) = box.astype("int")
            face = image[startY:endY, startX:endX]
            fH, fW = face.shape[:2]
            if fW < 20 or fH < 20:
                continue

            # embedding
            faceBlob = cv2.dnn.blobFromImage(
                face, 1.0/255, (96,96), (0,0,0), swapRB=True, crop=False
            )
            embedder.setInput(faceBlob)
            vec = embedder.forward()

            knownNames.append(name)
            knownEmbeddings.append(vec.flatten())
            total += 1

        self.stdout.write(f"[✅] Extracted {total} face embeddings, serializing…")
        data = {"embeddings": knownEmbeddings, "names": knownNames}
        with open(output_file, "wb") as f:
            pickle.dump(data, f)

        self.stdout.write(self.style.SUCCESS(f"✔️  Wrote embeddings to {output_file}"))
