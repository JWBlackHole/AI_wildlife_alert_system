import boto3
import logging
import torch
from PIL import Image
import io
import os
# import openai

from backend.threat_labels import * 

logging.basicConfig(
    level=logging.INFO,  # Set the logging level (e.g., DEBUG, INFO, WARNING, ERROR)
    handlers=[
        logging.StreamHandler()  # Output logs to the console
    ]
)

class ImageDetection:
    def __init__(self, method="rek"):
        """
        Initializes the ObjectDetection class.
        :param method: A string to determine which detection method to use ("rekognition" or "yolo").
        """
        self.method = method.lower()
        self.rekognition_client = None
        self.yolo_model = None
        self.aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
        self.aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if self.method == "rek":
            # Initialize Rekognition client
            self.rekognition_client = boto3.client('rekognition', 
                                                   region_name='us-east-1',
                                                    aws_access_key_id=self.aws_access_key_id,
                                                    aws_secret_access_key=self.aws_secret_access_key
                                                   )
            logging.info("AWS Rekognition client initialized.")
        elif self.method == "yolo":
            # Load YOLOv5 model
            self.yolo_model = torch.hub.load('ultralytics/yolov5', 'yolov5n', pretrained=True)
            logging.info("YOLOv5 model loaded.")
        elif self.method == "openai":
            if not self.openai_api_key:
                raise ValueError("OpenAI API key not found. Please set it in the .env file.")
            openai.api_key = self.openai_api_key
            logging.info("OpenAI API initialized.")
        else:
            raise ValueError("Invalid method. Choose 'rekognition' or 'yolo'.")
        logging.info("[ImageDetection] Model Ready.")
        
    def detect_labels(self, image_bytes):
        """
        Detects labels in an image using the specified method (Rekognition, YOLO, or OpenAI).
        :param image_bytes: The image data in bytes.
        :return: A set of threat labels
        """
        if self.method == "rek":
            return self.detect_labels_by_aws_rek(image_bytes)
        elif self.method == "yolo":
            return self.detect_objects_by_yolo(image_bytes)
        elif self.method == "openai":
            return self.detect_labels_by_openai(image_bytes)
        else:
            raise RuntimeError("Invalid detection method.")

    def detect_labels_by_aws_rek(self, image_bytes):
        """
        Calls AWS Rekognition to detect labels in the given image bytes.
        Returns a set of detected label names.
        """
        if self.method != "rek":
            raise RuntimeError("Rekognition detection is not enabled. Initialize with method='rekognition'.")

        try:
            response = self.rekognition_client.detect_labels(
                Image={'Bytes': image_bytes},
                MaxLabels=10,
                MinConfidence=70  # Adjust based on tests
            )
            logging.info("Rekognition response:")
            logging.info(response)
            detected_labels = {label['Name'] for label in response['Labels']}
            logging.info(f"Rekognition result: {detected_labels}")

            # Check for threats
            threats = THREAT_LABELS.intersection(detected_labels)
            if threats:
                logging.warning(f"⚠️ Threat detected by Rekognition: {threats}")
            return threats
        except Exception as e:
            logging.error(f"Error during Rekognition call: {e}")
            raise

    def detect_objects_by_yolo(self, image_bytes):
        """
        Detects objects in an image using YOLOv5 locally.
        Accepts image bytes as input.
        Returns a list of detected objects with their labels, confidence scores, and bounding boxes.
        """
        if self.method != "yolo":
            raise RuntimeError("YOLO detection is not enabled. Initialize with method='yolo'.")

        try:
            # Convert image bytes to a PIL Image
            image = Image.open(io.BytesIO(image_bytes))

            # Run YOLO detection
            results = self.yolo_model(image)

            # Extract detection results
            detected_objects = []
            for *box, conf, cls in results.xyxy[0]:
                x1, y1, x2, y2 = box
                label = self.yolo_model.names[int(cls)]
                detected_objects.append({
                    'label': label,
                    'confidence': float(conf),
                    'box': [int(x1), int(y1), int(x2), int(y2)]
                })

            logging.info(f"YOLO detection result: {detected_objects}")

            # Check for threats
            detected_labels = {obj['label'] for obj in detected_objects}
            threats = THREAT_LABELS.intersection(detected_labels)
            if threats:
                logging.warning(f"⚠️ Threat detected by YOLO: {threats}")
            return detected_objects
        except Exception as e:
            logging.error(f"Error during YOLO detection: {e}")
            raise

    def detect_labels_by_openai(self, image_bytes):
        """
        Uses OpenAI API (Chat API) to generate a text description of the image and checks for threats.
        :param image_bytes: The image data in bytes.
        :return: A text description of the image and any detected threats.
        """
        if self.method != "openai":
            raise RuntimeError("OpenAI detection is not enabled. Initialize with method='openai'.")

        try:
            # Optional: save image if you want to use it somewhere else or debug

            # New Chat API call
            prompt = "Describe the objects and scene in the image."

            response = openai.chat.completions.create(
                model="gpt-4",  # or "gpt-3.5-turbo"
                messages=[
                    {"role": "system", "content": "You are an image analysis assistant."},
                    {"role": "user", "content": prompt},
                    {"role": "user","type": "input_image", "image_url": f"data:image/png;base64,{image_bytes}"},
                ],
                max_tokens=100,
            )
            print("response\n=======")
            print(response)
            print("===========")
            description = response.choices[0].message.content
            logging.info(f"OpenAI description: {description}")
            print(description)

            # Check for threats
            threats = [label for label in THREAT_LABELS if label.lower() in description.lower()]
            if threats:
                logging.warning(f"⚠️ Threat detected by OpenAI: {threats}")
            return {"description": description, "threats": threats}

        except Exception as e:
            logging.error(f"Error during OpenAI detection: {e}")
            raise


if __name__ == "__main__":
    import sys

    # Set the image path
    image_path = '../imgs/mock_tiger.jpg'

    # Initialize the ObjectDetection class
    method = "rek"  # Change to "yolo" to use YOLOv5
    detector = ImageDetection(method=method)

    try:
        with open(image_path, "rb") as image_file:
            image_bytes = image_file.read()

            if method == "rek":
                print("Running AWS Rekognition detection...")
                results = detector.detect_labels_by_aws_rek(image_bytes)
                print("AWS Rekognition Detection Results:", results)
            elif method == "yolo":
                print("Running YOLOv5 detection...")
                results = detector.detect_objects_by_yolo(image_bytes)
                print("YOLOv5 Detection Results:", results)
            elif method == "openai":
                print("Running OpenAI detection...")
                results = detector.detect_labels_by_openai(image_bytes)
                print("OpenAI Detection Results:", results)
    except FileNotFoundError:
        print(f"Error: File not found at {image_path}")
    except Exception as e:
        print(f"Error during detection: {e}")