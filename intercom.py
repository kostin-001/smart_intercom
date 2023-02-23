import logging
import sys
import uuid

import httpx

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(stream=sys.stdout)
logger.addHandler(handler)


class Intercom:
    HOST = "https://domofon.tattelecom.ru"
    SIGN_IN = "/v1/subscriber/signin"
    SMS_CONFIRM = "/v1/subscriber/smsconfirm"
    REGISTRATION_CONFIRM = "/v1/subscriber/registration-confirm"
    OPEN_DOOR = "/v1/subscriber/open-intercom"
    SIP_SETTINGS = "/v1/subscriber/sipsettings"
    AVAILABLE_INTERCOMS = "/v1/subscriber/available-intercoms"
    AVAILABLE_STREAMS = "/v2/subscriber/available-streams"

    HEADERS = {
        "Accept":          "application/json",
        "User-Agent":      "TTC Intercom/17",
        "Accept-Encoding": "gzip",
    }


    def __init__(self, phone: str, device_code: str | None = None, token: str | None = None):
        self._phone = phone
        self._token = token
        self._device_os = "2"
        self._urls = {}
        uu = device_code if device_code else str(uuid.uuid4())
        self._device_code = uu.upper()
        self._base_data = {"phone": self._phone, "device_code": self._device_code}
        if token:
            self.HEADERS["Access-Token"] = token


    def get_access_token(self):
        """
            Method for receiving access token
        :return:
            token: str - access-token
            device_code: str - device id
        """
        res = httpx.post(f"{self.HOST}{self.SIGN_IN}", json=self._base_data, headers=self.HEADERS)
        if res.status_code == 200:
            sms_code = input("Enter code from sms:\n")
            data = self._base_data.copy()
            data["sms_code"] = sms_code
            res = httpx.post(f"{self.HOST}{self.SMS_CONFIRM}", json=data, headers=self.HEADERS)
            if res.status_code == 200:
                reg_res = httpx.post(f"{self.HOST}{self.REGISTRATION_CONFIRM}", json=self._base_data, headers=self.HEADERS)
                token = res.json()["access_token"]
                self.HEADERS["Access-Token"] = token
                self._token = token
                logger.info("Access token received.")
            else:
                logger.error(f"Sms confirmation failed. Response: {res.text}")
        else:
            logger.error(f"Sign in failed. Response: {res.text}")
        return self._token, self._base_data["device_code"]


    def get_stream_urls(self):
        """
            Method for retrieving urls of live streams and corresponding intercom ids
        :return: urls:dict - dict, where key is url, and value is intercom id
        """
        if self._urls:
            return self._urls
        urls = {}
        res = httpx.post(f"{self.HOST}{self.AVAILABLE_INTERCOMS}", params=self._base_data, headers=self.HEADERS)
        if res.status_code == 200:
            res = res.json()
            if res["addresses"] and res["success"]:
                for addr in res["addresses"].values():
                    for d in addr:
                        urls[d["stream_url_mpeg"]] = d["id"]
        self._urls = urls
        logger.info(f"Found {len(urls)} stream urls.")
        return urls


    def open_door(self, intercom_id):
        """
            Method for opening door
        :param intercom_id: int - door id to open
        :return: status: bool - operation status
        """
        status = False
        txt = f"Door {intercom_id} failed to open."
        data = self._base_data.copy()
        data["intercom_id"] = intercom_id
        res = httpx.post(f"{self.HOST}{self.OPEN_DOOR}", json=self._base_data, headers=self.HEADERS)
        if res.status_code == 200:
            txt = f"Door {intercom_id} opened."
            status = True
        logger.info(txt)
        return status


    def get_sip_settings(self):
        """
            Method for getting sip settings
        :return: dict of sip settings
        """
        res = httpx.post(f"{self.HOST}{self.SIP_SETTINGS}", params=self._base_data, headers=self.HEADERS)
        if res.status_code == 200:
            res = res.json()
        return res
