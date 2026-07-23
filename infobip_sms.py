#!/usr/bin/env python3
"""CLI for testing inbound/outbound SMS on an Infobip long number.

Reads credentials from environment variables so nothing sensitive is
hardcoded or committed:

    INFOBIP_BASE_URL       e.g. nd2vj2.api.infobip.com
    INFOBIP_API_KEY        your Infobip API key
    INFOBIP_FROM           your long number, international format, no '+' (e.g. 447860004919)
    INFOBIP_ENTITY_ID      optional; binds the send to a specific Entity so
                           the platform routes through your number instead
                           of a shared/generic one
    INFOBIP_APPLICATION_ID optional; binds the send to a specific Application
                           (used together with INFOBIP_ENTITY_ID)

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
    entity_id = os.environ.get("INFOBIP_ENTITY_ID")
    application_id = os.environ.get("INFOBIP_APPLICATION_ID")

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

    return base_url, api_key, from_number, entity_id, application_id


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


def send(base_url, api_key, from_number, to, text, entity_id=None, application_id=None):
    if not from_number:
        sys.exit("INFOBIP_FROM is not set; required to send a message.")
    message = {
        "from": from_number,
        "destinations": [{"to": to}],
        "text": text,
    }
    if entity_id:
        message["entityId"] = entity_id
    if application_id:
        message["applicationId"] = application_id
    payload = {"messages": [message]}
    resp = requests.post(
        f"https://{base_url}/sms/2/text/advanced",
        json=payload,
        headers=headers(api_key, json_body=True),
    )
    print(resp.status_code)
    print(resp.text)

    try:
        sent_messages = resp.json().get("messages", [])
    except ValueError:
        sent_messages = []
    for m in sent_messages:
        message_id = m.get("messageId")
        status = m.get("status", {})
        if message_id:
            print(f"\nmessageId: {message_id}  status: {status.get('groupName')}/{status.get('name')}")


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
    base_url, api_key, from_number, entity_id, application_id = get_config()

    if args.command == "balance":
        balance(base_url, api_key)
    elif args.command == "number":
        number_info(base_url, api_key, from_number)
    elif args.command == "send":
        send(base_url, api_key, from_number, args.to, args.text, entity_id, application_id)
    elif args.command == "inbox":
        inbox(base_url, api_key)


if __name__ == "__main__":
    main()
