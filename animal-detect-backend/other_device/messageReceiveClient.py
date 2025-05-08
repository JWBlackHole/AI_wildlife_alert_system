
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTShadowClient, AWSIoTMQTTClient
import os
import time
import json

from constants import *
from led_control import turn_on_light, turn_off_light

class MessageReceiveClient:
    def __init__(self):
        """
        Initializes the MQTT client and connects to AWS IoT Core.
        """
        turn_off_light()
        self.client_id = "LedDeviceClient"
        self.endpoint = "a2rwg7fxsn0b1i-ats.iot.us-east-1.amazonaws.com"
        self.port = 8883
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Cert file path
        self.cert_files =     {
            "root_ca": os.path.join(self.base_dir, "root-CA.crt"),
            "private_key": os.path.join(self.base_dir, "Hack_Rpi.private.key"),
            "cert": os.path.join(self.base_dir, "Hack_Rpi.cert.pem")
        }
        
        self.shadow_client = AWSIoTMQTTShadowClient("ledShadowClient")

        self.shadow_client.configureEndpoint(self.endpoint, self.port)
        self.shadow_client.configureCredentials(
            self.cert_files["root_ca"],
            self.cert_files["private_key"],
            self.cert_files["cert"]
        )
        # Initialize MQTT client
        # self.mqtt_client = self.shadow_client.getMQTTConnection()
        self.mqtt_client = AWSIoTMQTTClient(self.client_id)
        self.mqtt_client.configureEndpoint(self.endpoint, self.port)
        self.mqtt_client.configureCredentials(
            self.cert_files["root_ca"],
            self.cert_files["private_key"],
            self.cert_files["cert"]
        )
        self.mqtt_client.connect()
        self.subscribe(LED_STATE_TOPIC)
        

        # Connect to AWS IoT Core
        try:
            self.shadow_client.connect()
            print("[LED] 已連線到 AWS IoT Core")
        except Exception as e:
            print("[MessageReceive] Connection failed:", e)
            raise
        self.device_shadow = self.shadow_client.createShadowHandlerWithName(THING_NAME, True)
        self.device_shadow.shadowRegisterDeltaCallback(self.shadow_delta_callback)
        print("[LED] 已註冊 delta callback,等待 Shadow 狀態變更...")
        

    def subscribe(self, topic):
        """
        Subscribes to a given topic and prints received messages.
        """
        self.mqtt_client.subscribe(topic, 1, message_callback)
        try:
            print(f"[MessageReceiveClient] Subscribed to topic `{topic}`")
        except Exception as e:
            print(f"[MessageReceiveClient] Failed to subscribe to topic `{topic}`:", e)
            
    def shadow_delta_callback(self, payload, a, b):
        print("\n[Shadow Delta] 收到 Shadow delta 通知")
        try:
            data = json.loads(payload)
            desired_state = data["state"]["led"]
            print(f"想要的狀態是：{desired_state}")
            
            control_led(desired_state)

            # 回報目前狀態（更新 reported）
            reported_payload = {
                "state": {
                    "reported": {
                        "led": desired_state
                    }
                }
            }
            self.device_shadow.shadowUpdate(json.dumps(reported_payload), None, 5)
            print("[LED] 已回報目前狀態至 Shadow (reported)")
        except Exception as e:
            print("無法處理 delta 訊息：", e)

    
def message_callback(client, userdata, message):
    print("\n[MQTT Message] 收到訊息")
    payload = message.payload.decode()
    print(f"Payload: {payload}")

    # print(f"  message: {message.json()}")
    # print(f"  Payload: {message.payload.decode('utf-8')}")
    
    
def control_led(desired_state):
    if desired_state == "on":
        turn_on_light()
    else:
        turn_off_light()
  
# driver
if __name__ == "__main__":
    try:
        # Initialize the MessageReceiveClient
        message_receiver = MessageReceiveClient()

        print("[MessageReceiveClient] Listening for shadow delta notifications... Press Ctrl+C to exit.")

        # Keep the program running to listen for shadow delta updates
        while True:
            time.sleep(1)  # Sleep to prevent high CPU usage
    except KeyboardInterrupt:
        print("[MessageReceiveClient] Stopping...")
    except Exception as e:
        print("[MessageReceiveClient] Error:", e)
