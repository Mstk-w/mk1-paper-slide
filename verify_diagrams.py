from generate_slide import create_a3_slide

test_data = {
    "theme": "図解・アイコン機能検証用スライド",
    "department": "システム開発部",
    "content": [
        {
            "column": "left",
            "label": "📉 01. 現状 (Text)",
            "text": "・従来の箇条書きスタイルです。\n・絵文字がラベルに含まれています。\n・ここは通常のテキストボックスとして描画されます。",
            "layout_type": "text"
        },
        {
            "column": "left",
            "label": "⚠️ 02. 課題 (Text)",
            "text": "・アイコンによる視認性の向上を確認します。\n・複数行のテキストも問題なく表示されるべきです。",
            "layout_type": "text"
        },
        {
            "column": "right",
            "label": "🚀 03. 導入プロセス (Flow)",
            "text": "・ステップ1: 企画\n・ステップ2: 開発\n・ステップ3: テスト\n・ステップ4: リリース",
            "layout_type": "flow_horizontal"
        },
        {
            "column": "right",
            "label": "✅ 04. 期待効果 (Flow - Fallback Test)",
            "text": "・もしステップが多すぎる場合やテキストが長すぎる場合の挙動を確認します。\n・このセクションはフローではなくテキストで表示される可能性があります（ロジックによる）。\n・ただし今回はステップがないので、普通に表示されるか、エラーにならないか確認。",
            "layout_type": "flow_horizontal"
        }
    ]
}

create_a3_slide(test_data, "verify_diagram_slide.pptx")
