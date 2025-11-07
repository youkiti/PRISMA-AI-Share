# PDF Preprocessing Scripts

このディレクトリには、PDFファイルおよび関連ファイルを処理し、構造化データ（JSON）に変換するための一連のPythonスクリプトが含まれています。スクリプトは、特定のデータソース（`suda_`, `tsuge_other_`, `tsuge_prisma_`）ごとにプレフィックスが付けられており、番号順（01から06）に実行されることを想定しています。

## 依存関係

- Python 3.x
- 必要なライブラリ:
  - `python-dotenv`
  - `docx2pdf`
  - `pdfservices-sdk` (Adobe PDF Services SDK)
  - `pandas`
  - `openpyxl` (pandasがExcelファイルを読み書きするために必要)
- `.env` ファイル: ルートディレクトリに配置し、以下の環境変数を設定する必要があります。
  - `PRISMA_AI_DRIVE_PATH_SUDA`: 須田先生のデータが格納されているディレクトリパス
  - `PRISMA_AI_DRIVE_PATH_OTHER`: 柘植先生のその他データが格納されているディレクトリパス
  - `PRISMA_AI_DRIVE_PATH_TSUGE`: 柘植先生のPRISMAデータが格納されているディレクトリパス
  - `DATA_OUTPUT_PATH`: 中間ファイル（PDF以外のファイルリスト、変換後PDFなど）の出力先ディレクトリパス
  - `NOT_PDF_LIST_PATH`: PDF以外のファイルリストのパス (`DATA_OUTPUT_PATH` 内を推奨)
  - `PDF_LIST_PATH`: 処理対象PDFリストのパス (`DATA_OUTPUT_PATH` 内を推奨)
  - `JSON_OUTPUT_PATH`: Adobe PDF ServicesによるJSON変換結果（zipファイルおよび解凍後データ）の出力先ディレクトリパス
  - `STRUCTURED_OUTPUT_PATH`: 最終的な構造化データ（JSON）の出力先ディレクトリパス
  - `SR_NAME`: 最終的なJSONファイル名のプレフィックス（例: `suda2025`, `tsuge_other2025`, `tsuge_prisma2025`）
  - `PDF_SERVICES_CLIENT_ID`: Adobe PDF Services API クライアントID
  - `PDF_SERVICES_CLIENT_SECRET`: Adobe PDF Services API クライアントシークレット
  - `PDF_SERVICES_CLIENT_ID_TT_2`: (tsuge_prisma用) Adobe PDF Services API クライアントID
  - `PDF_SERVICES_CLIENT_SECRET_TT_2`: (tsuge_prisma用) Adobe PDF Services API クライアントシークレット

## 実行順序

各プレフィックス（`suda_`, `tsuge_other_`, `tsuge_prisma_`）ごとに、以下の順序でスクリプトを実行します。

1.  `01_search_not_pdf.py`
2.  `02_convert_and_update_list.py` (注意: `tsuge_other` は手動処理)
3.  `03_search_pdf.py`
4.  `04_pdf_to_json.py`
5.  `05_unzip.py`
6.  `06_integrate_to_structured_data.py`

## スクリプトの説明

-   **`01_search_not_pdf.py`**: 指定されたデータディレクトリ（例: `PRISMA_AI_DRIVE_PATH_SUDA`）を検索し、PDF形式以外のファイル名をリストアップして `NOT_PDF_LIST_PATH` に保存します。
-   **`02_convert_and_update_list.py`**: `NOT_PDF_LIST_PATH` に記載されたファイルのうち、`.docx` または `.doc` ファイルをPDF形式に変換し、`DATA_OUTPUT_PATH` に保存します。変換に成功したファイルは `NOT_PDF_LIST_PATH` から削除されます。
    -   **注意**: `tsuge_other_02_convert_and_update_list.py` は、Google Drive APIの複雑さから手動処理に置き換えられています。GoogleドキュメントはPDFに、Googleスプレッドシートはxlsxに手動で変換し、指定のサブディレクトリ（`docx_to_pdf`, `tables`）に配置する必要があります。
-   **`03_search_pdf.py`**: 指定されたデータディレクトリおよび `docx_to_pdf` サブディレクトリを検索し、PDFファイルのリストを作成して `PDF_LIST_PATH` に保存します。ただし、`JSON_OUTPUT_PATH` に既に処理済みのJSONデータが存在するPDFは除外されます。
-   **`04_pdf_to_json.py`**: `PDF_LIST_PATH` に記載されたPDFファイルをAdobe PDF Services APIに送信し、テキスト、表、図などの要素を抽出した構造化データ（JSON形式）を含むzipファイルを `JSON_OUTPUT_PATH` 内の各PDFに対応するサブディレクトリ（例: `*_output/`）にダウンロードします。処理済みのPDFは `PDF_LIST_PATH` から削除されます（中断・再開のため）。
-   **`05_unzip.py`**: `JSON_OUTPUT_PATH` 内の各 `*_output/` サブディレクトリにある `output.zip` ファイルを解凍します。
-   **`06_integrate_to_structured_data.py`**: 各論文・資料に対応するファイル（元のPDF、変換されたPDF、Excel、画像など）の情報を統合します。
    -   `05`で解凍された `structuredData.json` からテキスト情報を抽出します。
    -   元のデータディレクトリにあるExcelファイル（`.xlsx`, `.xls`）の内容をCSV形式でテキストに含めます。
    -   元のデータディレクトリにある画像ファイル（`.jpg`, `.png` など）や、JSON抽出時に生成された図（figures）をBase64エンコードされたData URL形式で埋め込みます。
    -   ファイル名（拡張子、`suppl`の有無など）に基づいて適切な順序で情報を整理します。
    -   最終的な結果を `STRUCTURED_OUTPUT_PATH` に `{SR_NAME}_{ファイル番号}.json` という形式で保存します。

## 出力ファイル形式

`06_integrate_to_structured_data.py` スクリプトは、各論文・資料に対応する情報を統合し、`STRUCTURED_OUTPUT_PATH` に `{SR_NAME}_{ファイル番号}.json` という名前のJSONファイルとして出力します。

各JSONファイルは、一つの論文・資料セット（例：主論文PDF、補足資料Word、補足資料Excel、図ファイルなど）を表す辞書形式です。

-   **キー**:
    -   主要なPDFファイル（通常、ファイル番号のみで始まるPDF）の情報は、`{SR_NAME}_{ファイル番号}` というキー（例: `suda2025_1`）の下に格納されます。
    -   その他の関連ファイル（補足資料のPDF、Word/Excelファイル、画像ファイルなど）の情報は、**元のファイル名**（例: `1_suppl_document.docx`, `1_suppl_table.xlsx`, `1_figure.jpg`）をキーとして格納されます。ファイル名は `sort_key` 関数に基づいてソートされた順序で処理されますが、JSON内での順序は保証されません。
-   **値**:
    -   **PDFまたはWord/Docファイルの場合**: 値はさらに辞書となり、以下のキーを持ちます。
        -   `"text"`: Adobe PDF Servicesによって抽出・整形されたテキストコンテンツ（本文、見出し、リスト、表（CSV形式に変換）などを含む）。
        -   `{図ファイル名}` (例: `"figure1.png"`): 抽出された図がBase64エンコードされたData URL形式で格納されます。キーは抽出時の図ファイル名です。
    -   **Excelファイルの場合 (`.xlsx`, `.xls`)**: 値はさらに辞書となり、各シート名がキーになります。各シートの値は、そのシートの内容をCSV形式に変換した文字列です。
    -   **画像ファイルの場合 (`.jpg`, `.png` など)**: 値は、その画像ファイルをBase64エンコードしたData URL形式の文字列です。

**JSON構造の例 (`suda2025_1.json`)**:

```json
{
  "suda2025_1": {
    "text": "主論文PDFから抽出されたテキスト...\n表1\n列A,列B\n値1,値2\n...",
    "figure1.png": "data:image/png;base64,..."
  },
  "1_suppl_document.docx": {
    "text": "補足Word文書から抽出されたテキスト...",
    "figureA.jpg": "data:image/jpeg;base64,..."
  },
  "1_suppl_table.xlsx": {
    "Sheet1": "列X,列Y\nデータX1,データY1\nデータX2,データY2",
    "データシート": "項目,値\n項目A,100\n項目B,200"
  },
  "1_figure.jpg": "data:image/jpeg;base64,..."
}
```

---

## Output File Format (English)

The `06_integrate_to_structured_data.py` script integrates information corresponding to each paper/document and outputs it as a JSON file named `{SR_NAME}_{file_number}.json` in the `STRUCTURED_OUTPUT_PATH`.

Each JSON file is a dictionary representing a single set of papers/documents (e.g., main paper PDF, supplementary Word document, supplementary Excel file, figure files, etc.).

-   **Keys**:
    -   Information from the main PDF file (usually the PDF starting only with the file number) is stored under the key `{SR_NAME}_{file_number}` (e.g., `suda2025_1`).
    -   Information from other related files (supplementary PDFs, Word/Excel files, image files, etc.) is stored using the **original filename** as the key (e.g., `1_suppl_document.docx`, `1_suppl_table.xlsx`, `1_figure.jpg`). Filenames are processed in the order determined by the `sort_key` function, but the order within the JSON is not guaranteed.
-   **Values**:
    -   **For PDF or Word/Doc files**: The value is another dictionary containing the following keys:
        -   `"text"`: The text content extracted and formatted by Adobe PDF Services (including body text, headings, lists, tables converted to CSV format, etc.).
        -   `{figure_filename}` (e.g., `"figure1.png"`): Extracted figures are stored as Base64-encoded Data URLs. The key is the figure filename from the extraction process.
    -   **For Excel files (`.xlsx`, `.xls`)**: The value is another dictionary where each sheet name is a key. The value for each sheet is a string containing the sheet's content converted to CSV format.
    -   **For image files (`.jpg`, `.png`, etc.)**: The value is a string containing the Base64-encoded Data URL of the image file.

**Example JSON Structure (`suda2025_1.json`)**:

```json
{
  "suda2025_1": {
    "text": "Text extracted from the main PDF...\nTable 1\nColumnA,ColumnB\nValue1,Value2\n...",
    "figure1.png": "data:image/png;base64,..."
  },
  "1_suppl_document.docx": {
    "text": "Text extracted from the supplementary Word document...",
    "figureA.jpg": "data:image/jpeg;base64,..."
  },
  "1_suppl_table.xlsx": {
    "Sheet1": "ColumnX,ColumnY\nDataX1,DataY1\nDataX2,DataY2",
    "DataSheet": "Item,Value\nItemA,100\nItemB,200"
  },
  "1_figure.jpg": "data:image/jpeg;base64,..."
}
```

## プレフィックス

-   **`suda_`**: 須田先生関連のデータ処理用スクリプト。
-   **`tsuge_other_`**: 柘植先生のその他データ（PRISMA以外）処理用スクリプト。
-   **`tsuge_prisma_`**: 柘植先生のPRISMA関連データ処理用スクリプト。

## 注意点

-   実行前に `.env` ファイルに必要な環境変数をすべて設定してください。
-   Adobe PDF Services APIの認証情報（クライアントID、クライアントシークレット）が必要です。無料利用枠には制限があります。
-   `tsuge_other_02` の処理は手動で行う必要があります。詳細はスクリプト内のコメントを参照してください。
-   ファイルパスに日本語が含まれる場合があるため、OSや環境によっては文字コードの問題が発生する可能性があります。`pathlib` の使用やUTF-8エンコーディングの指定などで対策されていますが、注意が必要です。
