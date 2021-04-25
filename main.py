from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, ImageSendMessage,
)

import psycopg2

import os
import sys

app = Flask(__name__)

# LINE Botのチャネルシークレットを設定
YOUR_CHANNEL_SECRET = "XXXXX"
# LINE Botのチャネルアクセストークンを設定
YOUR_CHANNEL_ACCESS_TOKEN = "XXXXX"
# データベースのホスト名
DB_HOST = "XXXXX"
# データベースのデータベース名
DB_DATABASE = "XXXXX"
# データベースのユーザー名
DB_USER = "XXXXX"
# データベースのポート番号
DB_PORT = "XXXXX"
# データベースのパスワード
DB_PASSWORD = "XXXXX"

# LINE Botに接続
line_bot_api = LineBotApi(YOUR_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(YOUR_CHANNEL_SECRET)

# データベースに接続
db = psycopg2.connect(
    dbname=DB_DATABASE,
    user=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=DB_PORT
)
cur = db.cursor()

# https://example.herokuapp.com/callback にアクセスされたら以下の関数を実行する
@app.route("/callback", methods=['POST'])
def callback():
    # アクセス時に送られてきたデータ「X-Line-Signature」を代入
    signature = request.headers['X-Line-Signature']

    # アクセス時に送られてきたデータの主な部分を代入
    body = request.get_data(as_text=True)

    # try 内でエラーが発生したら except の文を実行
    try:
        # ハンドラーに定義されている関数を呼び出す
        handler.handle(body, signature)
    # もし「InvalidSigunatureError」というエラーが発生したら、以下のプログラムを実行
    except InvalidSignatureError:
        # リクエストを送った側に400番(悪いリクエストですよー！)を返す
        abort(400)

    # すべて順調にいけば、リクエストを送った側に「OK」と返す
    return "OK"

# ハンドラーに定義されている関数
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    # ここにメッセージの内容による処理を書いていこう

    # メッセージの種類が「テキスト」なら
    if event.type == "message":
        response_message = ""

        # 「○○ ×× △△」みたいなスペースで区切られた文章が来るかもしれないので、スペース区切りのリストにする
        splited = event.message.text.split(" ")

        # event.message.text という変数にメッセージの内容が入っている
        if splited[0] == "天気記録":
            if len(splited) == 3:
                # データベースに天気を記録
                result = database_insert(splited[1], splited[2])

                if result == "OK":
                    response_message = "記録しました！"
                else:
                    response_message = "エラーが発生しました…"
            else:
                response_message = "「天気記録 [地域] [天気]」という形で送信してください。"

        elif splited[0] == "天気教えて":
            if len(splited) == 2:
                # データベースから天気を取得
                weather = database_select(splited[1])

                if weather == "sunny":
                    response_message = "{}の天気は晴れです！".format(splited[1])
                elif weather == "cloudy":
                    response_message = "{}の天気は曇りです！".format(splited[1])
                elif weather == "rainny":
                    response_message = "{}の天気は雨です！".format(splited[1])
                elif weather == "snowy":
                    response_message = "{}の天気は雪です！".format(splited[1])
                elif weather == "none":
                    response_message = "{}の天気はまだ記録されていません…".format(splited[1])
                else:
                    response_message = "エラーが発生しました…"
            else:
                response_message = "「天気教えて [地域]」という形で送信してください。"

        elif event.message.text == "おはようございます":
            response_message = "Good morning!"

        elif event.message.text == "こんにちは":
            response_message = "Good afternoon!"

        elif event.message.text == "こんばんは":
            response_message = "Good evening!"

        else:
            response_message = "その言葉はわかりません。"

        # 返信文を送信
        # response_message の中に入っている文を返す
        line_bot_api.reply_message(
            event.reply_token,
            [
                TextSendMessage(text=response_message)
            ]
        )

# データベースに天気を記録する関数
def database_insert(location, weather):
    # 処理でエラーが発生したら、「error」と返す
    try:
        # executeメソッドの引数に、C言語のprintfのような感じにSQL文を入れる
        cur.execute("INSERT INTO weathers VALUES (%s, %s)", (location, weather))
        # データベースに内容を適応
        db.commit()
        return "OK"

    except:
        print("エラーが発生しました:", sys.exc_info()[0])
        return "error"

# データベースから天気を取得する関数
def database_select(location):
    # 処理でエラーが発生したら、「error」と返す
    try:
        # executeメソッドの引数に、C言語のprintfのような感じにSQL文を入れる
        # 要素数が1のタプルは、最後にコンマを付けないとタプルが自動的に外されるので注意
        cur.execute("SELECT weather FROM weathers WHERE location = %s LIMIT 1", (location,))
        # 結果を一行だけ取り出す（タプルで返ってくるが、天気のみ取得しているので要素数は1）
        data = cur.fetchone()

        # 当てはまるデータが見つからなかった場合、タプルではなく、Noneが返ってくる
        if data == None:
            return "none"
        # 結果のタプルの0番目の要素を返す（要素数が一つだけでもタプルはタプルなので、しっかりと指定する必要がある）
        return data[0]

    except:
        print("エラーが発生しました:", sys.exc_info()[0])
        return "error"

# ポート番号を環境変数から取得
port = os.getenv("PORT")
app.run(host="0.0.0.0", port=port)