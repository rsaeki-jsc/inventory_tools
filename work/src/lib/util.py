import re
from datetime import datetime

from lib.log import LOG, set_level
from lib.checksheet import Checksheet

class Util():
    @staticmethod
    def __is_date_format_valid(
            date: str
            ) -> bool:
        """
        棚卸開始日/棚卸終了日のフォーマットが有効であるかを確認します。

        Args:
            date (str): 棚卸開始日or棚卸終了日

        Returns:
            bool: 棚卸開始日/棚卸終了日のフォーマットが有効であればTrue、無効であればFalse
        """

        pattern = re.compile(r"[0-9]{4}/[0-9]{2}/[0-9]{2}")
        if re.search(pattern, date):
            return True
        else:
            return False
    
    @staticmethod
    def __are_valid_date(
            start_date: str,
            end_date: str
            ) -> bool:
        """
        棚卸実施期間のバリデーションチェックを行います。

        Args:
            start_date (str): 棚卸開始日
            end_date (str): 棚卸終了日

        Returns:
            bool: 問題がなければTrue、問題があればFalse
        """

        # フォーマット確認
        is_date_format_valid = True
        if not Util.__is_date_format_valid(start_date):
            LOG.error("Start date(" + start_date +") is invalid format.")
            is_date_format_valid = False
        if not Util.__is_date_format_valid(end_date):
            LOG.error("End date(" + end_date +") is invalid format.")
            is_date_format_valid = False
        if not is_date_format_valid:
            return False
        
        # 日付の有効性確認
        date_fomat = "%Y/%m/%d"
        try:
            start_datetime = datetime.strptime(start_date, date_fomat)
            end_datetime = datetime.strptime(end_date, date_fomat)
        except Exception:
            LOG.exception("Invalid date.")
            return False

        # 開始日と終了日の整合性確認
        if start_datetime <= end_datetime:
            return True
        else:
            LOG.error("Invalid date range.")
            return False

    @staticmethod
    def init(
            log_level: str,
            start_date: str,
            end_date: str
            ) -> bool:
        """
        初期処理\n
        ・ログレベルの設定\n
        ・棚卸実施期間のバリデーションチェック

        Args:
            log_level (str): ログレベル
            start_date (str): 
            end_date (str): _description_

        Returns:
            bool: _description_
        """
        if not set_level(log_level):
            LOG.error("Failed to set log level.")
            return False

        if not Util.__are_valid_date(start_date, end_date):
            return False
    
    @staticmethod
    def fetch_asset_data(
        user_id: str,
        password: str
        ) -> dict[str, dict[str, str]] | None:
        """
        資産データを取得します。
        資産データの取得に失敗した場合はNoneを返します。

        Args:
            user_id (str): 管理者用ページのログイン情報（ユーザ名）
            password (str): 管理者用ページのログイン情報（パスワード）

        Returns:
            dict[str, dict[str, str]] | None: 技術検証機管理表（管理者用ページ）の資産データ
        """

        checksheet = Checksheet()
        if checksheet.login(user_id, password):
            asset_list = checksheet.fetch_asset_data()
            if asset_list is not None:
                return asset_list
            else:
                LOG.error("There was an issue with the results of the table integrity check.")
                return None
        else:
            LOG.error("Failed to login to the administrator's page.")
            return None
        