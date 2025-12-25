
# Streamlit Community Cloud デプロイ仕様書（推奨・完全無料）

本ドキュメントは、「Mk1paperSlide（1枚スライド生成アプリ）」を **Streamlit Community Cloud** へデプロイするための手順書です。
これが最も推奨される方法であり、無料で安定した動作が可能です。

---

## 1. 準備されているファイル

以下のファイルが自動生成済みです。これらはデプロイに必須です。

* `requirements.txt`: アプリが使用するライブラリ一覧（streamlit, python-pptx, google-generativeai）。
* `.gitignore`: 不要なファイルをアップロードしないための設定。

## 2. GitHubへの保存（プッシュ）

まず、ローカルのコードにGitを設定し、GitHubへ保存します。

1. **Project Rootに移動**
    * ターミナルで `Mk1paperSlide` フォルダを開きます。

2. **Gitの初期化とコミット**

    ```bash
    git init
    git add .
    git commit -m "First commit for Streamlit Cloud"
    ```

3. **GitHubリポジトリの作成**
    * GitHubの「New repository」からリポジトリを作成します。
    * **Repository name**: 例 `mk1-paper-slide`
    * **Public/Private**: **Public（公開）** を推奨します。
        * *※Community Cloudの無料枠は、原則としてPublicリポジトリに対して無制限です。Privateも可能ですが制限がある場合があります。*

4. **GitHubへのプッシュ**

    ```bash
    git branch -M main
    git remote add origin https://github.com/YourUsername/mk1-paper-slide.git
    git push -u origin main
    ```

---

## 3. Streamlit Community Cloud でのデプロイ

ブラウザで行う作業です。

1. **アクセスとログイン**
    * [Streamlit Community Cloud](https://streamlit.io/cloud) にアクセスします。
    * 「Sign up」または「Log in」から、**GitHubアカウント**でログインします。

2. **アプリの新規作成**
    * 右上の「New app」ボタンをクリックします。
    * **Repository**: 先ほど作成した `mk1-paper-slide` を選択します。
    * **Branch**: `main`
    * **Main file path**: `app.py`
    * 「Deploy!」をクリックします。

    これだけでアプリのビルドと起動が始まります（初回は2〜3分かかります）。

---

## 4. 環境変数の設定 (APIキー)

アプリがGemini APIを使用するため、APIキーを安全に設定します。

1. デプロイされたアプリの右下にある「Manage app」（または右上の「Settings」）を開きます。
2. 「Secrets」タブを選択します。
3. 以下の形式でAPIキーを入力し、「Save」を押します。

```toml
GEMINI_API_KEY = "ここに取得したGeminiのAPIキーを貼り付け"
```

> **自動連携について**
> 上記のSecrets設定を行うと、アプリ側で自動的にキーが読み込まれ、毎回入力する手間が省けます（コード改修済み）。

## 5. 完了

これで世界中どこからでもアプリにアクセスできるようになります。
URL（例: `https://mk1-paper-slide.streamlit.app`）を共有すれば、誰でも利用可能です。
