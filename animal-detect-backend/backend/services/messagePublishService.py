import os
import json
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient, AWSIoTMQTTShadowClient

from backend.constants import *


class MessagePublish:
    def __init__(self):
        """
        Initializes the MQTT and shadow clients for publishing messages.
        """
        self.client_id = "publisher_client"
        self.shadow_client_id = "test_shadow_client"
        self.thing_name = THING_NAME
        self.endpoint = IOT_CORE_ENDPOINT
        self.port = 8883
        self.topic = LED_STATE_TOPIC
        
        base_dir = os.path.dirname(os.path.abspath(__file__))
        # Initialize certificate file paths
        self.cert_files =     {
            "root_ca": os.path.join(base_dir, "root-CA.crt"),
            "private_key": os.path.join(base_dir, "Hack_Rpi.private.key"),
            "cert": os.path.join(base_dir, "Hack_Rpi.cert.pem")
        }


        # Initialize MQTT client
        self.mqtt_client = AWSIoTMQTTClient(self.client_id)
        self.mqtt_client.configureEndpoint(self.endpoint, self.port)
        self.mqtt_client.configureCredentials(
            self.cert_files["root_ca"],
            self.cert_files["private_key"],
            self.cert_files["cert"]
        )

        # Initialize shadow client
        self.shadow_client = AWSIoTMQTTShadowClient(self.shadow_client_id)
        self.shadow_client.configureEndpoint(self.endpoint, self.port)
        self.shadow_client.configureCredentials(
            self.cert_files["root_ca"],
            self.cert_files["private_key"],
            self.cert_files["cert"]
        )

        # Connect to AWS IoT Core
        try:
            self.mqtt_client.connect()
            self.shadow_client.connect()
            print("[MessagePublish] Connected to AWS IoT Core")
            self.device_shadow = self.shadow_client.createShadowHandlerWithName(self.thing_name, True)
            self.update_led_state('off')
        except Exception as e:
            print("[MessagePublish] Connection failed:", e)
            raise
    
    
    def publish_threat(self, message):
        """
        Publishes an alert message to the specified MQTT topic and updates the shadow state.
        """
        try:
            # Publish the message to the MQTT topic
            self.mqtt_client.publish(self.topic, json.dumps(message), 1)
            print(f"[MessagePublish] Message published to topic: {self.topic}")

            # Update the shadow's desired state
            self.update_led_state("on")
        except Exception as e:
            print("[MessagePublish] Failed to publish message or update shadow:", e)

    def publish_safe(self, message):
        try:
            # # Publish the message to the MQTT topic
            self.mqtt_client.publish(self.topic, json.dumps(message), 1)
            print(f"[MessagePublish] Message published to topic: {self.topic}")

            # # Update the shadow's desired state
            # self.update_led_state("off")
        except Exception as e:
            print("[MessagePublish] Failed to publish message or update shadow:", e)

    def update_led_state(self, target_state):
        """
        Updates the LED state in the shadow's desired state.
        """
        desired_payload = {"state": {"desired": {"led": target_state}}}
        try:
            self.device_shadow.shadowUpdate(json.dumps(desired_payload), None, 5)
            print(f"[MessagePublish] Shadow LED state updated to: {target_state}")
        except Exception as e:
            print("[MessagePublish] Failed to update shadow state:", e)


# Example usage
if __name__ == "__main__":
    # Configuration
    base_dir = os.path.dirname(os.path.abspath(__file__))
    CERT_FILES = {
        "root_ca": os.path.join(base_dir, "root-CA.crt"),
        "private_key": os.path.join(base_dir, "Hack_Rpi.private.key"),
        "cert": os.path.join(base_dir, "Hack_Rpi.cert.pem")
    }

    # Initialize the MessagePublish class
    message_publisher = MessagePublish()

    # Publish an alert
    message_publisher.publish_threat({"message": "Test alert message"})