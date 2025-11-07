import os
import zipfile
from dotenv import load_dotenv


# .envファイルから環境変数を読み込む
load_dotenv()

def process_subdirectories(base_dir):
    # ベースディレクトリの直下にあるすべてのサブディレクトリを取得
    i=0
    for subdir in os.listdir(base_dir):
        subdir_path = os.path.join(base_dir, subdir)
        # サブディレクトリであることを確認
        if os.path.isdir(subdir_path):
            output_zip_path = os.path.join(subdir_path, 'output.zip')
            
            # output.zipが存在する場合
            if os.path.exists(output_zip_path):
                # output.zipを解凍
                with zipfile.ZipFile(output_zip_path, 'r') as zip_ref:
                    zip_ref.extractall(subdir_path)
                                   
                # output.zipを削除
                # os.remove(output_zip_path)

if __name__ == "__main__":
    base_dir = os.getenv('JSON_OUTPUT_PATH') # ベースディレクトリのパスを指定
    process_subdirectories(base_dir)