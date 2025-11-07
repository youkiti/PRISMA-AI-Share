#pip install -q pdfservices-sdk

#Copyright 2024 Adobe
#All Rights Reserved.

#NOTICE: Adobe permits you to use, modify, and distribute this file in
#accordance with the terms of the Adobe license agreement accompanying it.
import sys
import logging
import os
import json
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

from adobe.pdfservices.operation.auth.credentials import Credentials
from adobe.pdfservices.operation.auth.service_principal_credentials import ServicePrincipalCredentials
from adobe.pdfservices.operation.exception.exceptions import ServiceApiException, ServiceUsageException, SdkException
from adobe.pdfservices.operation.io.cloud_asset import CloudAsset
from adobe.pdfservices.operation.io.stream_asset import StreamAsset
from adobe.pdfservices.operation.pdf_services import PDFServices
from adobe.pdfservices.operation.pdf_services_media_type import PDFServicesMediaType
from adobe.pdfservices.operation.pdfjobs.jobs.extract_pdf_job import ExtractPDFJob
from adobe.pdfservices.operation.pdfjobs.params.extract_pdf.extract_element_type import ExtractElementType
from adobe.pdfservices.operation.pdfjobs.params.extract_pdf.extract_pdf_params import ExtractPDFParams
from adobe.pdfservices.operation.pdfjobs.params.extract_pdf.extract_renditions_element_type import \
    ExtractRenditionsElementType
from adobe.pdfservices.operation.pdfjobs.result.extract_pdf_result import ExtractPDFResult

# .envファイルから環境変数を読み込む
load_dotenv()

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# 環境変数からパスを取得
pdf_list_path = os.getenv('PDF_LIST_PATH')
if pdf_list_path is None:
    logger.error("エラー: 環境変数 'PDF_LIST_PATH' が設定されていません。")
    sys.exit(1)

raw_dir = os.getenv('PRISMA_AI_DRIVE_PATH_SUDA')
if raw_dir is None:
    logger.error("エラー: 環境変数 'PRISMA_AI_DRIVE_PATH_SUDA' が設定されていません。")
    sys.exit(1)

output_dir = os.getenv('JSON_OUTPUT_PATH')
if output_dir is None:
    logger.error("エラー: 環境変数 'JSON_OUTPUT_PATH' が設定されていません。")
    sys.exit(1)

# 出力ディレクトリが存在しない場合は作成
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Initial setup, create credentials instance
credentials = ServicePrincipalCredentials(
    client_id=str(os.getenv('PDF_SERVICES_CLIENT_ID')),
    client_secret=str(os.getenv('PDF_SERVICES_CLIENT_SECRET')))

# Creates a PDF Services instance
pdf_services = PDFServices(credentials=credentials)

def read_pdf_list(file_path):
    """
    PDFリストファイルを読み込む
    
    Args:
        file_path (str): PDFリストのパス
        
    Returns:
        list: PDFファイルパスのリスト
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            # テキストファイルから行ごとに読み込み、空行を除外
            #return [line.strip() for line in f if line.strip()]
            #途中からの場合、listとして保存されている
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"ファイル {file_path} が見つかりません")
        sys.exit(1)
    except Exception as e:
        logger.error(f"PDFリスト読み込み中にエラーが発生しました: {e}")
        sys.exit(1)

def update_pdf_list(file_path, pdf_list):
    """
    処理済みのPDFをリストから削除して更新する
    
    Args:
        file_path (str): PDFリストのパス
        pdf_list (list): 更新されたPDFリスト
    """
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(pdf_list, f, ensure_ascii=False, indent=2, default=str)
        logger.info(f"PDFリストを更新しました。残り {len(pdf_list)} 件")
    except Exception as e:
        logger.error(f"PDFリスト更新中にエラーが発生しました: {e}")
        sys.exit(1)

def convert_pdf(pdf_path, output_dir=output_dir):
    try:
        file = open(pdf_path, 'rb')
        input_stream = file.read()
        file.close()

                # Creates an asset(s) from source file(s) and upload
        input_asset = pdf_services.upload(input_stream=input_stream, mime_type=PDFServicesMediaType.PDF)

        # Create parameters for the job
        extract_pdf_params = ExtractPDFParams(
            elements_to_extract=[ExtractElementType.TEXT, ExtractElementType.TABLES],
            elements_to_extract_renditions=[ExtractRenditionsElementType.TABLES, ExtractRenditionsElementType.FIGURES],
        )

        # Creates a new job instance
        extract_pdf_job = ExtractPDFJob(input_asset=input_asset, extract_pdf_params=extract_pdf_params)

        # Submit the job and gets the job result
        location = pdf_services.submit(extract_pdf_job)
        pdf_services_response = pdf_services.get_job_result(location, ExtractPDFResult)

        # Get content from the resulting asset(s)
        result_asset: CloudAsset = pdf_services_response.get_result().get_resource()
        stream_asset: StreamAsset = pdf_services.get_content(result_asset)
        
        # ファイル名（拡張子付き）を取得
        filename_with_ext = os.path.basename(pdf_path)

        # 拡張子を除いたファイル名だけ取得
        filename_without_ext = os.path.splitext(filename_with_ext)[0]

        os.makedirs(output_dir + "/" + filename_without_ext+'_output', exist_ok=True)
        # Creates an output stream and copy stream asset's content to it
        output_file_path = output_dir + "/" + filename_without_ext + '_output/output.zip'
        with open(output_file_path, "wb") as file:
            file.write(stream_asset.get_input_stream())
        now = datetime.now()
        return f"Completed {pdf_path}"


    except (ServiceApiException, ServiceUsageException, SdkException) as e:
        logging.exception(f'Exception encountered while executing operation: {e}')
        print(f"Could not extract {pdf_path} \n The reason is {e}")
        sys.exit(1) 

def main():
    """
    PDFリストに含まれるPDFを処理し、リストを更新する
    """
    # PDFリストを読み込む
    pdf_list = read_pdf_list(pdf_list_path)
    logger.info(f"処理対象のPDF: {len(pdf_list)} 件")
    
    if not pdf_list:
        logger.info("処理対象のPDFがありません")
        return
    
    # 各PDFを処理
    for i, pdf_path in enumerate(pdf_list[:]):  # リストのコピーを使用して反復処理
        logger.info(f"処理中 ({i+1}/{len(pdf_list)}): {pdf_path}")
        
        # PDFを処理
        result = convert_pdf(raw_dir + "/" + pdf_path)
        logger.info(result)
        
        # 処理が完了したPDFをリストから削除し、リストを更新
        pdf_list.remove(pdf_path)
        update_pdf_list(pdf_list_path, pdf_list)
        logger.info(f"PDF {pdf_path} を処理し、リストから削除しました。")
    
    logger.info("すべてのPDF処理が完了しました")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("処理が中断されました")
        sys.exit(1)
    except Exception as e:
        logger.error(f"予期せぬエラーが発生しました: {e}")
        sys.exit(1)
