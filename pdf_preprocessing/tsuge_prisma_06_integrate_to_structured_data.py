import re
import json
import pandas as pd
import os
from dotenv import load_dotenv

import base64
from mimetypes import guess_type

# .envファイルから環境変数を読み込む
load_dotenv()

# directoryの名前
sr_name = os.getenv('SR_NAME')

# 環境変数からパスを取得
raw_dir = os.getenv('PRISMA_AI_DRIVE_PATH_TSUGE')
if raw_dir is None:
    raise ValueError("環境変数 'PRISMA_AI_DRIVE_PATH_TSUGE' が設定されていません。")

# 出力先のディレクトリパス
output_dir = os.getenv('STRUCTURED_OUTPUT_PATH')
if output_dir is None:
    raise ValueError("環境変数 'STRUCTURED_OUTPUT_PATH' が設定されていません。")

# jsonが格納されているディレクトリパス
json_dir = os.getenv('JSON_OUTPUT_PATH')
if json_dir is None:
    raise ValueError("環境変数 'JSON_OUTPUT_PATH' が設定されていません。")


def extract_sentence(pdf_name):
  # Construct the path to the JSON file associated with the given PDF
  json_name=pdf_name+"/structuredData.json"

  a = open(json_name)# Open and load the JSON file
  j = json.load(a)
  extracted_sentence=""# Initialize a string to store the extracted sentences
  previous_item_class=0# To track the class of the previous item and determine if a newline is needed

  # Iterate through each element in the JSON file
  for item in j["elements"] :
    # Check if the item is a heading
    if ("//Document/H" in item['Path']) or (re.search(r"//Document/Sect.*/H", item['Path'])) or (re.search(r"//Document/Aside.*/H", item['Path'])):
      if previous_item_class!=1:
        extracted_sentence+="\n"
        previous_item_class=1
      if "Text" in item:
        if ("reference" == item["Text"].strip().lower()) or ("references" == item["Text"].strip().lower()) or ("appendix" == item["Text"].strip().lower()):
          extracted_sentence+="\n"
          break;
        extracted_sentence+=item["Text"]
        extracted_sentence+="\n"

    # Check if the item is a table and convert table data to text
    elif (re.search("//Document/Table.*" ,item['Path'])) or (re.search(r"//Document/Sect.*/Table", item['Path'])) or (re.search(r"//Document/Aside.*/Table", item['Path'])):#表データを文章に置き換える
      if previous_item_class!=2:
        extracted_sentence+="\n"
        previous_item_class=2
      if "filePaths" in item:
        for t in item["filePaths"]:
          if ".xlsx" in t:
            extracted_sentence+=t.replace(".xlsx", "").split("/")[-1]
            extracted_sentence+="\n"
            t=pdf_name+"/"+t
            # Load the Excel file
            df_t = pd.read_excel(t)
            # Remove carriage returns from column names and data
            df_t.columns = [col.replace('_x000D_', '') for col in df_t.columns]
            df_t = df_t.replace('_x000D_', '', regex=True)

            extracted_sentence+=df_t.to_csv(index=False)
            extracted_sentence+="\n"

    # Check if the item is a footnote
    elif (re.search("//Document/Footnote\.*",item['Path'])) or (re.search(r"//Document/Sect.*/Footnote", item['Path'])) or (re.search(r"//Document/Aside.*/Footnote", item['Path'])):
      if previous_item_class!=5:
        extracted_sentence+="\n"
        previous_item_class=5
      if "Text" in item:
        extracted_sentence+=item["Text"]
        extracted_sentence+="\n"

    # Check if the item is a paragraph
    elif ("//Document/P" in item['Path']) or (re.search(r"//Document/Sect.*/P", item['Path'])) or (re.search(r"//Document/Aside.*/P", item['Path'])):
      if previous_item_class!=3:
        extracted_sentence+="\n"
        previous_item_class=3
      if not("/Figure" in item["Path"]):
        if "Text" in item:
          extracted_sentence+=item["Text"]

    # Check if the item is a list
    elif ("//Document/L" in item['Path']) or (re.search(r"//Document/Sect.*/L", item['Path'])) or (re.search(r"//Document/Aside.*/L", item['Path'])):
      if previous_item_class!=4:
        extracted_sentence+="\n"
        previous_item_class=4
      if "/Lbl" in item["Path"]:
        extracted_sentence+="\n"
      if "Text" in item:
        extracted_sentence+=item["Text"]


  # Close the JSON file
  a.close()
  return extracted_sentence


# Function to encode a local image into data URL
def local_image_to_data_url(image_path):
    # Guess the MIME type of the image based on the file extension
    mime_type, _ = guess_type(image_path)
    if mime_type is None:
        mime_type = 'application/octet-stream'  # Default MIME type if none is found

    # Read and encode the image file
    with open(image_path, "rb") as image_file:
        base64_encoded_data = base64.b64encode(image_file.read()).decode('utf-8')

    # Construct the data URL
    return f"data:{mime_type};base64,{base64_encoded_data}"


# 拡張子の優先順位マップ（小さいほど優先）
ext_order = {'pdf': 0, 'docx': 1, 'xlsx': 2}
def sort_key(filename):
    """
    ファイル名を拡張子とsupplの有無でソートするためのキーを生成する関数
    1. 拡張子順：pdf → docx → xlsx → その他（任意の順）
    2. 各拡張子内で：
      - "suppl" を含まないファイルが先
      - "suppl" を含む場合：suppl1 < suppl2 < supplA（数値順優先）
    """
    # ファイル名と拡張子を分割
    parts = filename.lower().rsplit('.', 1)
    name_part = parts[0]
    ext = parts[1] if len(parts) > 1 else ''
    
    # 拡張子の順位（未知の拡張子は大きな値に）
    ext_rank = ext_order.get(ext, 99)

    # supplの順位（supplなし: 0、suppl1: 1、suppl2: 2、supplX: 100など）
    match = re.search(r'suppl(\d+)?', name_part)
    if match:
        if match.group(1):
            suppl_rank = int(match.group(1))  # suppl1, suppl2, ...
        else:
            suppl_rank = 100  # "suppl" だけのとき
    else:
        suppl_rank = -1  # supplがついていない

    return (ext_rank, suppl_rank, filename)

def main():
    """
    1. raw_dirに格納されているファイル番号を取得
    2. 各ファイル番号に合致するファイルを取得
    3-1. PDFファイルであればstructuredData.jsonを取得して統合
    3-2. PDFファイルでなければ、_docx.pdfとして検索をかける
    3-3. PDFファイルが見つかれば、structuredData.jsonを取得して統合
    3-4. 検索して見つからない場合、excel, imageに応じて統合
    """
    ## 1. raw_dirに格納されているファイル番号を取得
    # ファイル一覧を取得（ファイルのみ、かつ"."で始まらないもの）
    filenames = [
        f for f in os.listdir(raw_dir)
        if os.path.isfile(os.path.join(raw_dir, f)) and not f.startswith(".")
    ]
    # "_" でsplitして0番目の要素を抽出 → intに変換
    prefixes = [int(f.split("_")[0]) for f in filenames]
    # ユニークにして昇順にソート
    unique_prefixes = sorted(set(prefixes))

    ## 2. 各ファイル番号に合致するファイルを取得
    for file_num in unique_prefixes:

        file_name = sr_name + "_" + str(file_num)
        # 格納するデータ
        data = {}

        matching_files = [
            f for f in os.listdir(raw_dir)
            if os.path.isfile(os.path.join(raw_dir, f))
            and not f.startswith(".")
            and f.startswith(str(file_num) + "_")  # file_numで始まる
        ]

        # 並び替え
        matching_files_sorted = sorted(matching_files, key=sort_key)
        first_flag = True  # 最初のファイルフラグ
        for file in matching_files_sorted:
            # PDFファイルであればstructuredData.jsonを取得して統合
            if file.endswith(".pdf"):
                if first_flag:
                    save_name = file_name
                    first_flag = False
                else:
                    save_name = file
                data[save_name] = {}
                pdf_name = os.path.splitext(file)[0]
                target_dir = os.path.join(json_dir, pdf_name + "_output")
                # ディレクトリが存在すれば関数を呼び出す
                if os.path.isdir(target_dir):
                    data[save_name]["text"] = extract_sentence(target_dir)
                    if os.path.isdir(target_dir + "/figures"):
                        # 画像をdata_url形式に変換
                        for img in os.listdir(target_dir + "/figures"):
                            img_path = os.path.join(target_dir + "/figures", img)
                            data[save_name][img] = local_image_to_data_url(img_path)
            
            # PDFファイルでなければ、_docx.pdfとして検索をかける
            else:
                # ファイルがexcelファイルであれば
                if file.endswith(".xlsx"):
                    target_path = os.path.join(raw_dir, file)
                    # Excelファイルを複数シートとして読み込み
                    xl = pd.read_excel(target_path, sheet_name=None)  # 辞書で返る（{sheet_name: DataFrame}）

                    data[file] = {}  # このファイル用の辞書を初期化

                    for sheet_name, df_t in xl.items():
                        # 改行コードの除去（列名・データ両方）
                        df_t.columns = [col.replace('_x000D_', '') for col in df_t.columns]
                        df_t = df_t.replace('_x000D_', '', regex=True)

                        # 各シートをCSV文字列に変換して格納
                        data[file][sheet_name] = df_t.to_csv(index=False)

                # ファイルが画像ファイルであれば
                elif file.endswith(('.jpg', '.jpeg', '.png', '.gif')):
                    img_path = os.path.join(raw_dir, file)
                    data[file] = local_image_to_data_url(img_path)

                else: 
                    pdf_name = os.path.splitext(file)[0]
                    target_dir = os.path.join(json_dir, pdf_name + "_docx_output")
                    # ディレクトリが存在すれば関数を呼び出す
                    if os.path.isdir(target_dir):
                        data[file] = {}
                        data[file]["text"] = extract_sentence(target_dir)
                        if os.path.isdir(target_dir + "/figures"):
                            # 画像をdata_url形式に変換
                            for img in os.listdir(target_dir + "/figures"):
                                img_path = os.path.join(target_dir + "/figures", img)
                                data[file][img] = local_image_to_data_url(img_path)
                    

        # 結果をJSONファイルに保存
        output_file = os.path.join(output_dir, file_name + ".json")
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)

        print(f"JSONファイルを保存しました: {output_file}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("処理が中断されました")
    except Exception as e:
        print(f"予期せぬエラーが発生しました: {e}")
