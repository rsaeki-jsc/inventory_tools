import re
from datetime import datetime

import bs4
import requests

from lib.log import LOG

class Checksheet():
    # __ALLPRODUCTS_PAGE = "http://10.3.223.251/Checksheet/AllProducts"  # 技術検証機管理表
    __LOGIN_PAGE = "http://10.3.223.251/Checksheet/login.jsp"  # ログイン画面
    __FORM_DATA_DST = "http://10.3.223.251/Checksheet/LogIn"  # 認証情報の送信先
    __MAIN_PAGE = "http://10.3.223.251/Checksheet/Main"  # 技術検証機管理表（管理者用ページ）
    __COLUMN_NAMES = [  # 技術検証機管理表（管理者用ページ）の列名
            "管理番号",
            "登録日",
            "登録者",
            "稟議（取得年月）",
            "メーカ",
            "製品名型番",
            "S/N",
            "カテゴリ",
            "用途",
            "保守情報",
            "ライセンス情報",
            "管理部署",
            "管理者",
            "使用場所",
            "使用者",
            "貸出状況",
            "棚卸対象外",
            "棚卸し対象外理由",
            "存在確認",
            "最終棚卸確認日",
            "最終棚卸確認者",
            "備考、廃棄（年月)"
            ]
    __session: requests.Session = None  # セッション
    __main_page_html: str = None  # 管理者用ページのHTMLテキスト

    def __access_login_page(
            self
            ) -> bool:
        """
        ログイン画面にアクセスします。

        Returns:
            bool: アクセスに成功した場合はTrue、失敗した場合はFalseを返します。
        """

        LOG.debug(f"Attempt to access '{self.__LOGIN_PAGE}'.")
        res = self.__session.get(self.__LOGIN_PAGE)
        LOG.debug(f"Status code: {res.status_code}")
        LOG.debug(f"Current URL: {res.url}")
        return True if res.ok else False
        
    def __send_auth_info(
            self,
            user_id: str,
            password: str
            ) -> bool:
        LOG.debug(f"Attempt to access '{self.__FORM_DATA_DST}'.")
        res = self.__session.post(
            url=self.__FORM_DATA_DST,  # formタグのaction属性
            data={
                "LogIn_ID": user_id,
                "Password": password
            }
        )
        LOG.debug(f"Status code: {res.status_code}")
        LOG.debug(f"Current URL: {res.url}")

        return True if res.ok else False
        
    def __access_main_page(
            self
            ) -> bool:
        """
        __send_auth_info()で送信した認証情報を使用して管理者用ページにアクセスします。

        Returns:
            bool: 管理者用ページへのアクセスに成功した場合はTrue、失敗した場合はFalseを返します。
        """

        # 認証情報が正しければ、技術検証機管理表（管理者用ページ）にアクセスできます。
        # 間違っていれば、技術検証機管理表にリダイレクトされます。
        LOG.debug(f"Attempt to log in to '{self.__MAIN_PAGE}'.")
        res = self.__session.get(self.__MAIN_PAGE)
        LOG.debug(f"Status code: {res.status_code}")
        LOG.debug(f"Current URL: {res.url}")
        
        if res.url == self.__MAIN_PAGE:
            self.__main_page_html = res.text
            return True
        else:            
            return False

    def login(
            self,
            user_id: str,
            password: str
            ) -> bool:
        """
        技術検証機管理表の管理者用ページへのログインを試みます。

        Args:
            user_id (str): ユーザーID
            password (str): パスワード

        Returns:
            bool: ログインに成功した場合はTrue、失敗した場合はFalseを返します。
        """

        # Seleniumを使用せずに管理者用ページにアクセスするためには、
        # セッション（requests.Session）を使用して以下の手順を踏む必要があります。
        # 1．ログイン画面にアクセスします。
        # 2．ログイン画面のformタグのaction属性で指定されているURLに対して、
        # 認証情報（ユーザーIDとパスワード）を送信します。
        # 3．管理者用ページにアクセスします。

        self.__session = requests.Session()
        try:
            if not self.__access_login_page():
                LOG.error(f"Failed to access '{self.__LOGIN_PAGE}'.")
                return False

            if not self.__send_auth_info(user_id, password):
                LOG.error(f"Failed to send authentication info to '{self.__FORM_DATA_DST}'.")
                return False

            if not self.__access_main_page():
                LOG.error(f"Failed to access '{self.__MAIN_PAGE}'.")
                return False
        except Exception:
            LOG.exception("Unexpected error occurred.")
            return False
        finally:
            self.__session.close()
        return True

    def __are_column_names_vaild(
            self,
            column_name_lst: list[str]
            ) -> bool:
        """
        表の列名が想定通りであるか、整合性を確認します。

        Args:
            column_name_lst (list): 列名のリスト

        Returns:
            bool: 列名が想定通りであればTrue、想定通りでない場合はFalseを返します。
        """

        result = True
        for expected_column_name in self.__COLUMN_NAMES:
            try:
                index = self.__COLUMN_NAMES.index(expected_column_name)
                actual_column_name = column_name_lst[index]
            except IndexError:
                LOG.exception("Unexpected error occurred.")
                result = False

            if actual_column_name != expected_column_name:
                LOG.error(f"The column name was expected to be '{expected_column_name}', "
                          f"but it was '{actual_column_name}'.")
                result = False

        return result

    def fetch_asset_data(
            self
            ) -> dict[str, dict[str, str]] | None:
        """
        管理者用ページの表から資産データを取得します。
        表の整合性が欠けている場合はNoneを返します。

        Returns:
            dict[str, dict[str, str]] | None: 資産データ
        """
        
        assert self.__main_page_html != None

        soup = bs4.BeautifulSoup(self.__main_page_html, "lxml")
        table = soup.find("table")

        # 表の列名を取得します。
        th_rs = table.find("thead").find_all("th")
        column_name_lst = [th_tag.get_text() for th_tag in th_rs]
        LOG.debug(f"Column names: {column_name_lst}")
        del th_rs

        # 列名の整合性を確認します。
        if not self.__are_column_names_vaild(column_name_lst):
            LOG.error(f"'{self.__MAIN_PAGE}' is not in the expected format.")
            return None

        # 表のデータを取得します。
        asset_data = {}
        tr_rs = table.find("tbody").find_all("tr")
        for tr_tag in tr_rs:
            td_rs = tr_tag.find_all("td")

            # 列数の整合性を確認します。
            expected_length = len(column_name_lst)
            actual_length = len(td_rs)
            if actual_length != expected_length:
                LOG.error(f"The number of columns was expected to be '{expected_length}', "
                          f"but it was '{actual_length}'.")
                return None

            # 各列の値を取得します。
            mng_no = None
            row_data = {}
            for column_name, td_tag in zip(self.__COLUMN_NAMES, td_rs):
                # 管理番号は、asset_dataのキーにします。
                if column_name == self.__COLUMN_NAMES[0]:
                    # 管理番号は、1つ目のaタグのテキストノードに記載されています。
                    # 注意：「管理番号」の列名が複数ある場合、最終列の値で上書きされます。
                    mng_no = td_tag.find("a").get_text()
                # 管理番号以外は、asset_dataの値にします。
                else:
                    row_data[column_name] = td_tag.get_text()

            if mng_no is not None:
                asset_data[mng_no] = row_data
            else:
                LOG.error(f"Failed to get the management number from the folloing td tag.\n{td_tag}")
                return None
            
        return asset_data
    
    @staticmethod
    def extract_approval_number(
        approval_value: str
        ) -> str | None:
        """
        技術資産管理表の「稟議（取得年月）」列から稟議番号を抽出します。

        Args:
            approval_value (str):  技術資産管理表の「稟議（取得年月）」列の値

        Returns:
            str | None: 稟議番号
        """

        if approval_value == "":
            return approval_value
        
        pattern = r"R-[0-9]{6,8}"
        match = re.search(pattern, approval_value)
        if match:
            return match.group()
        else:
            LOG.warning(f"Failed to find approval value from '{approval_value}'.")
            return None
        
    @staticmethod
    def __compare_date(
        last_checked_date: str,
        start_date: str,
        end_date: str
        ) -> bool:
        """
        最終棚卸確認日が棚卸期間内であるかを確認します。

        Args:
            date (str): 最終棚卸確認日
            start_date (str): 棚卸開始日
            end_date (str): 棚卸終了日

        Returns:
            bool: 最終棚卸棚卸確認日が棚卸期間内であればTrue、棚卸期間外であればFalse
        """
        date_format = "%Y/%m/%d"  # 日付のフォーマットを指定します

        # 文字列をdatetimeオブジェクトに変換します
        last_checked_datetime = datetime.strptime(last_checked_date, date_format)
        start_datetime = datetime.strptime(start_date, date_format)
        end_datetime = datetime.strptime(end_date, date_format)

        # 日付を比較します
        if start_datetime <= last_checked_datetime <= end_datetime:
            return True
        else:
            LOG.debug(f"The last checked date({last_checked_datetime.strftime("%Y/%m/%d")}) "
                        "is outside the inventory period.")
            return False

    @staticmethod
    def exist(
        exist_value: str,
        last_checked_date: str,
        start_date: str,
        end_date: str
        ) -> bool:
        """
        棚卸結果を判定します。
        棚卸結果が〇となる条件は、存在確認が〇でかつ最終棚卸確認日が指定した期間内のときです。
        それ以外は×になります。

        Args:
            exist_value (str): 技術資産管理表の「存在確認」列の値
            last_checked_date (str): 技術資産管理表の「最終棚卸確認日」列の値
            start_date (str): 棚卸の開始日
            end_date (str): 棚卸の終了日

        Returns:
            bool: 棚卸結果
        """
        
        if exist_value in ["○"] and Checksheet.__compare_date(last_checked_date, start_date, end_date):
            return True
        else:
            return False
        