#!/usr/bin/env python
# coding: utf-8

import requests
import re

from .exceptions import BadResponse
from .utils import check_status_code


LOGIN_ENDPOINT = "http://login.mts.ru/amserver/UI/Login"


def get_balance(number, password):
    session = requests.Session()

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:81.0) Gecko/20100101 Firefox/81.0",
    }

    response = session.get(LOGIN_ENDPOINT, headers=headers)
    check_status_code(response, 200)

    csrf_token, csrf_ts_token = get_tokens(response)

    headers["Referer"] = LOGIN_ENDPOINT

    response = session.post(
        LOGIN_ENDPOINT,
        data={
            "IDToken1": number,
            "IDButton": "Submit",
            "encoded": "false",
            "loginURL": "?service=default",
            "csrf.sign": csrf_token,
            "csrf.ts": csrf_ts_token,
        },
        headers=headers,
    )
    check_status_code(response, 200)

    csrf_token, csrf_ts_token = get_tokens(response)

    response = session.post(
        LOGIN_ENDPOINT,
        data={
            "IDToken2": '{"screen":{"screenWidth":1920,"screenHeight":1080,"screenColourDepth":24},"platform":"Win32","language":"ru","timezone":{"timezone":-180},"plugins":{"installedPlugins":""},"fonts":{"installedFonts":"cursive;monospace;serif;sans-serif;default;Arial;Arial Black;Arial Narrow;Bookman Old Style;Bradley Hand ITC;Century;Century Gothic;Comic Sans MS;Courier;Courier New;Georgia;Impact;Lucida Console;Papyrus;Tahoma;Times;Times New Roman;Trebuchet MS;Verdana;"},"userAgent":"Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:94.0) Gecko/20100101 Firefox/94.0","appName":"Netscape","appCodeName":"Mozilla","appVersion":"5.0 (Windows)","buildID":"20181001000000","oscpu":"Windows NT 6.1; Win64; x64","product":"Gecko","productSub":"20100101"}',
            "csrf.sign": csrf_token,
            "csrf.ts": csrf_ts_token,
        },
        headers=headers,
    )
    check_status_code(response, 200)

    csrf_token, csrf_ts_token = get_tokens(response)

    response = session.post(
        LOGIN_ENDPOINT,
        data={
            "IDToken1": number,
            "IDToken2": password,
            "IDButton": "Check",
            "encoded": "false",
            "loginURL": "?service=default",
            "csrf.sign": csrf_token,
            "csrf.ts": csrf_ts_token,
        },
        headers=headers,
        allow_redirects=False,
    )
    check_status_code(response, 200)

    csrf_token, csrf_ts_token = get_tokens(response)

    response = session.post(
        LOGIN_ENDPOINT,
        data={
            "IDButton": "Login",
            "encoded": "false",
            "csrf.sign": csrf_token,
            "csrf.ts": csrf_ts_token,
        },
        headers=headers,
        allow_redirects=False,
    )
    check_status_code(response, 302)

    response = session.get("https://login.mts.ru/amserver/api/profile")
    check_status_code(response, 200)

    data = response.json()
    balance = data["mobile:balance"]

    if balance is None:
        raise BadResponse("Unable to get balance from JSON", response)

    return float(balance)


def get_tokens(response):
    csrf_token = re.search(r'name="csrf.sign" value="(.*?)"', response.text)
    csrf_ts_token = re.search(
        r'name="csrf.ts" value="(.*?)"', response.text
    )

    if csrf_token is None:
        raise BadResponse("CSRF token not found", response)

    return csrf_token.group(1), csrf_ts_token.group(1)
