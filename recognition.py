import logging
import os
import pickle as pkl
import sys
import threading

import cv2
import face_recognition

from intercom import Intercom

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(stream=sys.stdout)
logger.addHandler(handler)


class FaceRecognition:

    def __init__(self, intercom: Intercom, face_distance_threshold, video_check_period, faces_folder_path, face_encodings_folder_path):
        self._intercom = intercom
        self._faces_folder_path = faces_folder_path
        self._face_encodings_folder_path = face_encodings_folder_path
        self._face_distance_threshold = face_distance_threshold
        self._video_check_period = video_check_period
        self._known_face_encodings = []


    def save_face_encodings(self):
        """
            Method for creating face encodings from known faces
        """
        for filename in os.scandir(self._faces_folder_path):
            if filename.is_file():
                face = face_recognition.load_image_file(filename.path)
                face_encoding = face_recognition.face_encodings(face)[0]
                with open(os.path.join(self._face_encodings_folder_path, filename.name.split('.')[0]), "wb+") as f:
                    pkl.dump(face_encoding, f)
                os.remove(filename)


    def load_face_encodings(self):
        """
            Method for loading face encodings
        """
        encodings_list = []
        for filename in os.scandir(self._face_encodings_folder_path):
            if filename.is_file():
                with open(filename.path, "rb") as f:
                    encodings_list.append(pkl.load(f))
        self._known_face_encodings = encodings_list
        return encodings_list


    def _check_if_known_face_on_frame(self, frame):
        """
            Method for check if known face on frame
        :param frame: video frame (image)
        :return: bool - flag if known face on frame
        """
        known_face_on_frame = False
        small_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
        for face_encoding in face_encodings:
            matches = face_recognition.compare_faces(self._known_face_encodings, face_encoding, self._face_distance_threshold)
            if any(matches):
                logger.info("Found match")
                known_face_on_frame = True
                break
        return known_face_on_frame


    def run_recognition(self, stream_url, intercom_id):
        """
            Method for running loop in separate thread (if there are multiple intercoms)
        :param stream_url: url of live stream
        :param intercom_id: id of intercom for opening door
        """
        cap = cv2.VideoCapture(stream_url)
        try:
            fps = int(cap.get(cv2.CAP_PROP_FPS))
            if not cap.isOpened():
                raise Exception(f"Video source: {stream_url} not found...")
            frame_count = 0
            while cap.isOpened():
                ret, frame = cap.read()
                if ret:
                    frame_count += 1
                    if frame_count % (fps * self._video_check_period) == 0:
                        frame_count = 0
                        if self._check_if_known_face_on_frame(frame):
                            self._intercom.open_door(intercom_id)
                            logger.info(f"Door {intercom_id} opened.")

        except Exception as e:
            logger.error(f"Exception: {e}")
        finally:
            cap.release()


    def run_main_loop(self):
        urls = self._intercom.get_stream_urls()
        for u in urls.items():
            t = threading.Thread(target=self.run_recognition, args=[u[0], u[1]], daemon=True)
            t.start()
