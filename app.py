import os
import sys

from flask import Flask, request, abort, send_file
from dotenv import load_dotenv
from linebot import LineBotApi, WebhookParser
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

from fsm import TocMachine
from utils import send_text_message

load_dotenv()


machine = TocMachine(
    states=["init", "started",
            "nonmsg_error", "compile_error", "runtime_error",
            "gdb_tutorial", "logic_error",
            "common_syntax_error", "ok_google", "google_result",
            "divide_by_0", "seg_fault",
            "seg_fault_pt", "seg_fault_str", "seg_fault_other", "error_solve",
            "country_machine"
            ],
    transitions=[
        # start
        {
            "trigger": "advance",
            "source": "init",
            "dest": "started",
            "conditions": "always_cont",
        },
        # 三種error
        {
            "trigger": "advance",
            "source": "started",
            "dest": "nonmsg_error",
            "conditions": "is_going_to_nonmsg_error",
        },
        {
            "trigger": "advance",
            "source": "started",
            "dest": "compile_error",
            "conditions": "is_going_to_compile_error",
        },
        {
            "trigger": "advance",
            "source": "started",
            "dest": "runtime_error",
            "conditions": "is_going_to_runtime_error",
        },
        # 沒有error訊息的問題：是否有warning
        {
            "trigger": "advance",
            "source": "nonmsg_error",
            "dest": "ok_google",
            "conditions": "is_user_replying_yes",
        },
        {
            "trigger": "advance",
            "source": "nonmsg_error",
            "dest": "logic_error",
            "conditions": "is_user_replying_no"
        },
        # 編譯問題：是否為常見語法問題
        {
            "trigger": "advance",
            "source": "compile_error",
            "dest": "error_solve",
            "conditions": "is_user_replying_yes",
        },
        {
            "trigger": "advance",
            "source": "compile_error",
            "dest": "ok_google",
            "conditions": "is_user_replying_no"
        },
        # 執行期問題：問題選擇
        {
            "trigger": "advance",
            "source": "runtime_error",
            "dest": "divide_by_0",
            "conditions": "is_floating_point",
        },
        {
            "trigger": "advance",
            "source": "runtime_error",
            "dest": "seg_fault",
            "conditions": "is_seg_fault"
        },
        # (common_syntax_error)
        # Seg fault
        {
            "trigger": "advance",
            "source": "seg_fault",
            "dest": "seg_fault_pt",
            "conditions": "check_seg_pt"
        },
        {
            "trigger": "advance",
            "source": "seg_fault",
            "dest": "seg_fault_str",
            "conditions": "check_seg_str"
        },
        {
            "trigger": "advance",
            "source": "seg_fault",
            "dest": "seg_fault_other",
            "conditions": "check_seg_other"
        },
        {
            "trigger": "advance",
            "source": "seg_fault",
            "dest": "gdb_tutorial",
            "conditions": "is_seg_uncommon"
        },
        {
            "trigger": "advance",
            "source": ["seg_fault_pt", "seg_fault_str", "seg_fault_other"],
            "dest": "seg_fault",
            "conditions": "is_user_replying_no"
        },
        {
            "trigger": "advance",
            "source": ["seg_fault_pt", "seg_fault_str", "seg_fault_other"],
            "dest": "error_solve",
            "conditions": "is_user_replying_yes"
        },
        # gdb
        {
            "trigger": "advance",
            "source": "logic_error",
            "dest": "gdb_tutorial",
            "conditions": "always_cont",
        },
        # google
        {
            "trigger": "advance",
            "source": "ok_google",
            "dest": "google_result",
            "conditions": "always_cont",
        },
        # 介於有和沒有之間
        {
            "trigger": "advance",
            "source": ["nonmsg_error", "compile_error"],
            "dest": "country_machine",
            "conditions": "is_user_replying_half",
        },
        # 回到初始狀態
        {
            "trigger": "go_init",
            "source": ["country_machine", "gdb_tutorial", "divide_by_0", "google_result", "error_solve"],
            "dest": "init"
        }
    ],
    initial="init",
    auto_transitions=False,
    show_conditions=True,
)

app = Flask(__name__, static_url_path="")


# get channel_secret and channel_access_token from your environment variable
channel_secret = os.getenv("LINE_CHANNEL_SECRET", None)
channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", None)
if channel_secret is None:
    print("Specify LINE_CHANNEL_SECRET as environment variable.")
    sys.exit(1)
if channel_access_token is None:
    print("Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.")
    sys.exit(1)

line_bot_api = LineBotApi(channel_access_token)
parser = WebhookParser(channel_secret)


@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # parse webhook body
    try:
        events = parser.parse(body, signature)
    except InvalidSignatureError:
        abort(400)

    # if event is MessageEvent and message is TextMessage, then echo text
    for event in events:
        if not isinstance(event, MessageEvent):
            continue
        if not isinstance(event.message, TextMessage):
            continue

        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text=event.message.text)
        )

    return "OK"


@app.route("/webhook", methods=["POST"])
def webhook_handler():
    signature = request.headers["X-Line-Signature"]
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info(f"Request body: {body}")

    # parse webhook body
    try:
        events = parser.parse(body, signature)
    except InvalidSignatureError:
        abort(400)

    # if event is MessageEvent and message is TextMessage, then echo text
    for event in events:
        if not isinstance(event, MessageEvent):
            continue
        if not isinstance(event.message, TextMessage):
            continue
        if not isinstance(event.message.text, str):
            continue
        print(f"\nFSM STATE: {machine.state}")
        print(f"REQUEST BODY: \n{body}")
        response = machine.advance(event)
        if response == False:
            send_text_message(event.reply_token, "Not Entering any State")

    return "OK"


@app.route("/show-fsm", methods=["GET"])
def show_fsm():
    machine.get_graph().draw("fsm.png", prog="dot", format="png")
    return send_file("fsm.png", mimetype="image/png")


if __name__ == "__main__":
    port = os.environ.get("PORT", 8000)
    app.run(host="0.0.0.0", port=port, debug=True)
