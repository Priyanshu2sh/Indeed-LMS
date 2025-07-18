import os
import requests


def send_otp_to_email(email, var1, var2):
    url = "https://control.msg91.com/api/v5/email/send"

    payload = {
        "to": [
            {
                "name": f"{var1}",
                "email": f"{email}"
            }
        ],
        "from": {
            "name": "IndeedInspiring Dashboard",
            "email": "otp@mail.indeedinspiring.com"
        },
        "domain": "mail.indeedinspiring.com",
        "mail_type_id": "1",
        "template_id": "OTP_Dashboard",
        "variables": {
            "VAR1": f"{var1}",
            "VAR2": f"{var2}"
        }
    }
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authkey": "392023Ah8auuoo640826d6P1"
    }

    response = requests.post(url, json=payload, headers=headers)

    return response