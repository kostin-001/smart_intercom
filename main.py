import json
import logging
import os
import sys
import time

from intercom import Intercom
from recognition import FaceRecognition

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(stream=sys.stdout)
logger.addHandler(handler)

FACE_ENCODINGS_FOLDER = os.path.join(os.getcwd(), "faces_encodings")
FACES_FOLDER = os.path.join(os.getcwd(), "known_faces")
INTERCOM_CONFIG_FILE = "intercom_config.json"
FACE_RECOGNITION_CONFIG_FILE = "face_recognition_config..json"


def read_config(file_name):
    with open(file_name) as f:
        config = json.load(f)
    return config


def update_intercom_config(phone_to_save, device_code_to_save, token_to_save):
    to_save = {"phone": phone_to_save, "device_code": device_code_to_save, "token": token_to_save}
    with open(INTERCOM_CONFIG_FILE, "w") as f:
        json.dump(to_save, f, indent=4)
    logger.info(f"Config updated.")


if __name__ == '__main__':
    """ Entry point """
    intercom_config = read_config(INTERCOM_CONFIG_FILE)
    if "phone" not in intercom_config:
        raise AttributeError("Phone number not in config.")
    phone = intercom_config.get("phone")
    device_code = intercom_config.get("device_code", None)
    token = intercom_config.get("token", None)
    intercom = Intercom(phone, device_code, token)

    if token is None:
        token, device_code = intercom.get_access_token()
        if token is None:
            raise ValueError(f"Failed to get access token.")
        update_intercom_config(phone, device_code, token)
    urls = intercom.get_stream_urls()
    if not urls:
        raise ValueError(f"Stream urls is empty.")

    face_recognition_config = read_config(FACE_RECOGNITION_CONFIG_FILE)
    face_distance_threshold = face_recognition_config.get("face_distance_threshold", .45)
    video_check_period = face_recognition_config.get("video_check_period", 2)

    face_recognizer = FaceRecognition(intercom, face_distance_threshold, video_check_period, FACES_FOLDER, FACE_ENCODINGS_FOLDER)
    face_recognizer.save_face_encodings()
    known_faces_encodings = face_recognizer.load_face_encodings()
    if not known_faces_encodings:
        raise ValueError(f"Face encodings list empty.")
    face_recognizer.run_main_loop()
    logger.info("Main started.")

    while True:  # to keep main program alive, since recognition threads are daemons
        time.sleep(300)
