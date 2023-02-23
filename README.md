# Smart intercom

A computer vision based project to open the front door if the camera recognized the resident.

## Which types of intercoms can be used

This app was done for interacting with [Tattelecom intercoms](https://letai.ru/domofon/) only. <br/>
However, with modification of urls (and probably method signatures) in [intercome](intercom.py) file the list of available intercoms can be extended.

## How to use:

- Create folder "known_faces" and add images with your face (better to take it directly from intercom)
- Create folder "faces_encodings"
- Enter phone number in [intercom_config](intercom_config.json)
- run the app ```python main.py```
- Enter code from sms
