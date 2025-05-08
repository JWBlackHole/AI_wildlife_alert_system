from flask import Blueprint, request, jsonify
import logging
import base64  # Import base64 for encoding the image
# import snsService as sns  # 👈 加在頂部

import backend.services.snsService as sns
import backend.services.rekognition as rk
import backend.services.messagePublishService as mpub
from backend.threat_labels import * 

routes = Blueprint('routes', __name__)


METHOD="rek"  # Change this to "rek" for AWS Rekognition or "yolo" for YOLOv5

image_recognition = rk.ImageDetection(method=METHOD)
messagePublisher = mpub.MessagePublish()

@routes.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint to verify the server is running.
    """
    return jsonify({'status': 'OK', 'message': 'Animal Detect Backend is running!'}), 200

'''
exmaple:
with open(image_path, "rb") as image_file:
        files = {"image": image_file}
        response = requests.post(API_URL, files=files)
'''
@routes.route("/detect_photo", methods=["POST"])
def handle_photo():
    print("Handling")
    if "image" not in request.files:
        return jsonify({"error": "No image part"}), 400

    image_bytes = request.files["image"].read()
    try:
        if METHOD =="openai":
            b64_image = base64.b64encode(request.files["image"].read()).decode("utf-8")
            detected_labels = image_recognition.detect_labels(b64_image)

        detected_labels = image_recognition.detect_labels(image_bytes)
        logging.info("Labels: %s", detected_labels)

        threat = list(detected_labels)
        status = 200
        message = {}

        if threat:
            logging.warning("[Route] Threat detected: %s", threat)
            message = {"success": True, "danger": True, "threat": threat}
            # use messagePublishService to publish message
            sns.publish_threat_alert("Warning: A potential threat has been detected nearby. Details: " + str(message))
            messagePublisher.publish_threat(message)
            return jsonify(message), status
        else:
            message = {"success": True, "danger": False}
            messagePublisher.publish_safe(message)
            logging.info("[Route] No threat detected.")
            return jsonify(message), status

   
    except Exception as e:
        logging.exception("Rekognition failed: %s", e)
        return jsonify({"success": False, "error": "Internal error"}), 500


@routes.route('/mock_detect_photo', methods=['POST'])
def handle_mock_photo():
    if 'image' not in request.files:
        return jsonify({'error': 'No image part'}), 400

    image_file = request.files['image']
    # check file extension to check if is .jpg
    if not image_file.filename.lower().endswith('.jpg'):
        return jsonify({'error': 'Uploaded file is not a valid JPG image'}), 400

    try:
        # Mock response
        logging.info("Mock mode: Processing image as a valid JPG.")
        dummy_labels = {'Tiger', 'Elephant'}  # Example dummy labels
        threat_detected = THREAT_LABELS.intersection(dummy_labels)

        if threat_detected:
            threat = list(threat_detected)
            logging.warning(f"[Route] Threat detected (mock): {threat_detected}")
            threat_message = {"success": True, "danger": True, "threat": threat}
            messagePublisher.publish_threat(threat_message)
            return jsonify(threat_message), 200
            
        else:
            safe_message = {"success": True, "danger": False}
            messagePublisher.publish_safe(safe_message)
            return jsonify({'threat': []}), 200

    except IOError:
        return jsonify({'error': 'Uploaded file is not a valid image'}), 400


if __name__ == "__main__":
    pass