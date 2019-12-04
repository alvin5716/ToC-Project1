from transitions.extensions import GraphMachine

from utils import send_text_message, send_button_message, send_text_message_cont, send_text_message_end
from bs4 import BeautifulSoup
import urllib
import requests

started_sel = ["編譯時有錯誤訊息", "執行時有錯誤訊息", "執行成果和想要的不同"]
yes_no_sel = ["有", "沒有"]
runtime_sel = ["Floating", "Segmentation"]
seg_fault_sel = ["陣列、指標", "字串處理", "其他", "這些選項都沒有幫助"]

class TocMachine(GraphMachine):
    def __init__(self, **machine_configs):
        self.machine = GraphMachine(model=self, **machine_configs)

    def is_going_to_compile_error(self, event):
        text = event.message.text
        return text == started_sel[0]

    def is_going_to_runtime_error(self, event):
        text = event.message.text
        return text == started_sel[1]

    def is_going_to_nonmsg_error(self, event):
        text = event.message.text
        return text == started_sel[2]

    def is_user_replying_yes(self, event):
        text = event.message.text
        return text == yes_no_sel[0]

    def is_user_replying_no(self, event):
        text = event.message.text
        return text == yes_no_sel[1]

    def is_floating_point(self, event):
        text = event.message.text
        return text == runtime_sel[0]

    def is_seg_fault(self, event):
        text = event.message.text
        return text == runtime_sel[1]

    def check_seg_pt(self, event):
        text = event.message.text
        return text == seg_fault_sel[0]

    def check_seg_str(self, event):
        text = event.message.text
        return text == seg_fault_sel[1]

    def check_seg_other(self, event):
        text = event.message.text
        return text == seg_fault_sel[2]

    def is_seg_uncommon(self, event):
        text = event.message.text
        return text == seg_fault_sel[3]

    def is_user_replying_half(self, event):
        text = event.message.text
        secret_sel = ["介於有和沒有", "介於有跟沒有", "介於有與沒有"]
        for i in secret_sel:
            if i in text:
                return True
        else:
            return False

    def always_cont(self, event):
        text = event.message.text
        return True

    def on_enter_started(self, event):
        reply_token = event.reply_token
        send_button_message(reply_token, "您遇到了什麼問題呢？", started_sel)

    def on_enter_compile_error(self, event):
        reply_token = event.reply_token
        send_button_message(reply_token,
            pre_text="這種錯誤屬於「編譯錯誤(Compilation Error)」，代表語法出錯、有變數未宣告等。請再檢查一次：",
            question="你有沒有「漏打分號，或不小心用了全形符號」？",
            selections=yes_no_sel
            )

    def on_enter_runtime_error(self, event):
        reply_token = event.reply_token
        send_button_message(reply_token,
            pre_text="這種錯誤屬於「執行時期錯誤(Run-time Error)」，通常是編譯器管不到的地方出錯了。",
            question="你看到的錯誤訊息是？",
            selections=runtime_sel
            )

    def on_enter_divide_by_0(self, event):
        reply_token = event.reply_token
        send_text_message_end(reply_token, "診斷結果：Floating Point Exception 代表你的程式在執行過程中出現了「除以零」的狀況，例如：1/0、2%0。請檢查你所有的「除法」和「取餘數」的計算過程。")
        self.go_init()

    def on_enter_seg_fault(self, event):
        reply_token = event.reply_token
        send_button_message(reply_token,
            pre_text="診斷結果：Segmentation Fault(記憶體區段錯誤)，是最常見的一種Run-time Error。通常是用到了不能用的記憶體空間，我來帶您檢查以下幾種常見的出錯點：",
            question="請依序點擊以下按鈕",
            selections=seg_fault_sel
            )

    def on_enter_seg_fault_pt(self, event):
        reply_token = event.reply_token
        send_button_message(reply_token,
            pre_img="https://i.imgur.com/7STxewL.png",
            question="問題解決了嗎？",
            selections=yes_no_sel
            )

    def on_enter_seg_fault_str(self, event):
        reply_token = event.reply_token
        send_button_message(reply_token,
            pre_img="https://i.imgur.com/cP9gNkd.png",
            question="問題解決了嗎？",
            selections=yes_no_sel
            )

    def on_enter_seg_fault_other(self, event):
        reply_token = event.reply_token
        send_button_message(reply_token,
            pre_img="https://i.imgur.com/C80b6NI.png",
            question="問題解決了嗎？",
            selections=yes_no_sel
            )

    def on_enter_error_solve(self, event):
        reply_token = event.reply_token
        send_text_message_end(reply_token, "恭喜你找到問題了！")
        self.go_init()

    def on_enter_nonmsg_error(self, event):
        reply_token = event.reply_token
        send_button_message(reply_token, "請問您有在編譯時看到任何warning訊息嗎？", yes_no_sel)

    def on_enter_ok_google(self, event):
        reply_token = event.reply_token
        send_text_message(reply_token, "有warning或error訊息通常不會太難搞定，因為很容易找到和您發生一樣問題的人。請輸入訊息，我會幫您在stackoverflow上搜尋幾個頁面。")

    def on_enter_google_result(self, event):
        reply_token = event.reply_token
        f = {'q' : event.message.text}
        url = "https://stackoverflow.com/search?" + urllib.parse.urlencode(f)
        req = requests.get(url)
        if req.status_code!=200:
            send_text_message(reply_token, "查詢失敗")
            return
        soup = BeautifulSoup(req.text,'html.parser')
        titles = soup.find_all('a', class_='question-hyperlink')
        title_str = []
        for i, item in enumerate(titles):
            if i >= 3:
                break
            title_str.append(item.text.strip() + "\nhttps://stackoverflow.com" + (item.get("href")).strip())
        send_text_message_end(reply_token, title_str)
        self.go_init()

    def on_enter_logic_error(self, event):
        reply_token = event.reply_token
        send_text_message_cont(reply_token, "診斷結果：這種錯誤屬於「邏輯錯誤(Logic Error)」，代表程式的邏輯或流程有誤，也就是您沒有完全理解自己的程式，所以只能靠您自己了。")

    def on_enter_gdb_tutorial(self, event):
        reply_token = event.reply_token
        send_text_message_end(reply_token, "雖然幫不上您，但我可以推薦您使用自由軟體「GDB」來幫助您debug。使用GDB就可以看到發生Run-time Error的行數和類型、也能讓程式一行一行地逐步執行、甚至在途中印出指定的變數，非常實用。")
        self.go_init()

    def on_enter_country_machine(self, event):
        reply_token = event.reply_token
        send_text_message_end(reply_token, "診斷結果：肯定是有心人士想要卡你，導致編譯器動得非常厲害。")
        self.go_init()

    '''
    
    def on_exit_state2(self):
        print("Leaving state2")

    def on_exit_state1(self):
        print("Leaving state1")
    '''
