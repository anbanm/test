#!/usr/bin/env python3
"""CLI for testing inbound/outbound SMS on an Infobip long number.

Reads credentials from environment variables so nothing sensitive is
hardcoded or committed:

    INFOBIP_BASE_URL   e.g. nd2vj2.api.infobip.com
    INFOBIP_API_KEY    your Infobip API key
    INFOBIP_FROM       your long number, international format, no '+' (e.g. 447860004919)

Usage:
    python infobip_sms.py balance
    python infobip_sms.py number
    python infobip_sms.py send --to 447700900000 --text "hello"
    python infobip_sms.py inbox
"""
import argparse
import os
import sys

import requests


def get_config():
    base_url = os.environ.get("INFOBIP_BASE_URL")
    api_key = os.environ.get("INFOBIP_API_KEY")
    from_number = os.environ.get("INFOBIP_FROM")

    missing = [
        name
        for name, value in [
            ("INFOBIP_BASE_URL", base_url),
            ("INFOBIP_API_KEY", api_key),
        ]
        if not value
    ]
    if missing:
        sys.exit(f"Missing required environment variable(s): {', '.join(missing)}")

    return base_url, api_key, from_number


def headers(api_key, json_body=False):
    h = {"Authorization": f"App {api_key}", "Accept": "application/json"}
    if json_body:
        h["Content-Type"] = "application/json"
    return h


def balance(base_url, api_key):
    resp = requests.get(
        f"https://{base_url}/account/1/balance", headers=headers(api_key)
    )
    print(resp.status_code)
    print(resp.text)


def number_info(base_url, api_key, number):
    resp = requests.get(
        f"https://{base_url}/sms/1/numbers",
        params={"number": number},
        headers=headers(api_key),
    )
    print(resp.status_code)
    print(resp.text)


def send(base_url, api_key, from_number, to, text):
    if not from_number:
        sys.exit("INFOBIP_FROM is not set; required to send a message.")
    payload = {
        "messages": [
            {
                "from": from_number,
                "destinations": [{"to": to}],
                "text": text,
            }
        ]
    }
    resp = requests.post(
        f"https://{base_url}/sms/2/text/advanced",
        json=payload,
        headers=headers(api_key, json_body=True),
    )
    print(resp.status_code)
    print(resp.text)


def inbox(base_url, api_key):
    resp = requests.get(
        f"https://{base_url}/sms/1/inbox/reports", headers=headers(api_key)
    )
    print(resp.status_code)
    print(resp.text)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("balance", help="Check account balance (verifies credentials)")
    sub.add_parser("number", help="Check number capability/config")

    send_parser = sub.add_parser("send", help="Send a test outbound SMS")
    send_parser.add_argument("--to", required=True, help="Destination number, international format, no '+'")
    send_parser.add_argument("--text", required=True, help="Message text")

    sub.add_parser("inbox", help="Poll for inbound message reports")

    args = parser.parse_args()
    base_url, api_key, from_number = get_config()

    if args.command == "balance":
        balance(base_url, api_key)
    elif args.command == "number":
        number_info(base_url, api_key, from_number)
    elif args.command == "send":
        send(base_url, api_key, from_number, args.to, args.text)
    elif args.command == "inbox":
        inbox(base_url, api_key)


if __name__ == "__main__":
    main()
