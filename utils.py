import os

from linebot import LineBotApi
from linebot.models import ImageSendMessage, TextSendMessage, TemplateSendMessage, ButtonsTemplate, MessageTemplateAction


channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", None)


def send_text_message(reply_token, text):
    line_bot_api = LineBotApi(channel_access_token)
    line_bot_api.reply_message(reply_token, TextSendMessage(text=text))

    return "OK"

def send_text_message_cont(reply_token, text):
    line_bot_api = LineBotApi(channel_access_token)
    line_bot_api.reply_message(reply_token, [TextSendMessage(text=text), TextSendMessage(text="(輸入任意訊息以繼續)")])

    return "OK"

def send_text_message_end(reply_token, text):
    line_bot_api = LineBotApi(channel_access_token)
    if isinstance(text, list):
        msg = [TextSendMessage(text=t) for t in text]
        msg.append(TextSendMessage(text="(輸入任意訊息以重新開始)"))
        line_bot_api.reply_message(reply_token, msg)
    else:
        line_bot_api.reply_message(reply_token, [TextSendMessage(text=text), TextSendMessage(text="(輸入任意訊息以重新開始)")])

    return "OK"

def send_button_message(reply_token, question, selections, pre_text=None, pre_img=None):
    line_bot_api = LineBotApi(channel_access_token)
    buttons = TemplateSendMessage(
            alt_text='請用手機版開啟以顯示按鈕',
            template=ButtonsTemplate(
                title=question,
                text='請點擊一個選項',
                actions=[
                    MessageTemplateAction(
                        label=i,
                        text=i
                    ) for i in selections
                ]
            )
        )
    if pre_text != None:
        line_bot_api.reply_message(reply_token, [TextSendMessage(text=pre_text), buttons])
    elif pre_img != None:
        line_bot_api.reply_message(reply_token, [ImageSendMessage(original_content_url=pre_img, preview_image_url=pre_img), buttons])
    else:
        line_bot_api.reply_message(reply_token, buttons)

    return "OK"

def send_button_uri(reply_token, question, selections, uris, pre_text=None):
    line_bot_api = LineBotApi(channel_access_token)
    buttons = TemplateSendMessage(
            alt_text='請用手機版開啟以顯示按鈕',
            template=ButtonsTemplate(
                title=question,
                text='請點擊一個選項',
                actions=[
                    URITemplateAction(
                        label=sel,
                        uri=uris[i]
                    ) for i, sel in enumerate(selections)
                ]
            )
        )
    if pre_text == None:
        line_bot_api.reply_message(reply_token, buttons)
    else:
        line_bot_api.reply_message(reply_token, [TextSendMessage(text=pre_text), buttons])

    return "OK"

"""
def send_image_url(id, img_url):
    pass

def send_button_message(id, text, buttons):
    pass
"""
