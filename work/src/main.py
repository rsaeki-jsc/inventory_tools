
import argparse
import re

from lib.log import LOG
from lib.util import Util
from lib.checksheet import Checksheet
from lib.excel import Excel


def __load_inventory_data(
        excel: Excel,
        file_path: str,
        sheet_name: str
        ) -> dict[str, dict[str, str]] | None:
    """
    棚卸リストを取得します。
    取得に失敗した場合はNoneを返します。

    Args:
        file_path (str): Excelファイルのファイルパス
        sheet_name (str): Excelのシート名

    Returns:
        list[dict]: 棚卸リスト
    """

    if not excel.load(file_path, sheet_name):
        LOG.error("Failed to load an excel file or worksheet.")
        return None
    if not excel.is_worksheet_vaild():
        LOG.error(f"The '{sheet_name}' sheet is not in the expected format.")
        return None

    try:
        return excel.load_inventory_data()
    except Exception:
        LOG.exception("Unexpected error occurred.")
        return None
    
def __normalize(
        value: str
        ) -> str:
    """
    細かすぎる差分の検出を抑制するために、値を正規化します。

    Args:
        value (str): Excelまたは技術資産管理表の値

    Returns:
        str: 改行と空白文字がすべて削除された値
    """

    value_removed_cr = value.replace("_x000D_", "")  # 強制改行コード（CR）の削除
    return re.sub(r"\s+", "", value_removed_cr)

def __get_diff(
        diff: dict,
        row_num: str,
        column_name: str,
        excel_value: str,
        checksheet_value: str
        ):
    """
    Excelと技術資産管理表の差分をdiffに保持します。
    dict型は参照渡しのため、diffを返す必要はありません。

    Args:
        diff (dict): Excelと技術資産管理表の差分のコレクション
        row_num (str): ワークシートの行番号
        column_name (str): ワークシートの列名
        excel_value (str): ワークシートの値
        checksheet_value (str): 技術資産管理表の値
    """

    normalized_excel_value = __normalize(excel_value)
    normalized_checksheet_value = __normalize(checksheet_value)
    if normalized_excel_value != normalized_checksheet_value:
        diff[row_num][column_name] = {
            "Before": excel_value,
            "After": checksheet_value
            }

def compare(
        inventory_data: dict[str, dict[str, str]],
        asset_data: dict[str, dict[str, str]],
        start_date: str,
        end_date: str
        ) -> dict[str, dict[str, str]]:
    """
    Excelと技術資産管理表を比較します。

    Args:
        inventory_data (dict[str, dict[str, str]]): Excel
        asset_data (dict[str, dict[str, str]]): 技術資産管理表

    Returns:
        dict[str, dict[str, str]]: Excelと技術資産管理表の差分
    """

    diff = {}
    for row_num, row_data in inventory_data.items():
        diff[row_num] = {}
        mng_no = row_data["管理番号"]
        if mng_no == "":
            LOG.warning(f"Not found the management number for row {row_num} of the worksheet.")
            continue
        for column_name, excel_value in row_data.items():
            match column_name:
                case "ステータス":
                    # 記入済みで上書き不要の想定です。
                    # TODO: 棚卸対象のみ差分チェックするオプションを追加しても良いかも
                    pass

                case "棚卸結果":
                    # 比較はしませんが、技術資産管理表から棚卸結果を自動判定します。
                    if Checksheet.exist(
                        asset_data[mng_no]["存在確認"],
                        asset_data[mng_no]["最終棚卸確認日"],
                        start_date,
                        end_date
                        ):
                        diff[row_num][column_name] = {"After": "〇"}
                    else:
                        diff[row_num][column_name] = {"After": "×"}

                case "備考":
                    # 上書き対象ですが、「備考（前回以前）」で実施します。
                    pass
                
                case "備考（前回以前）":
                    # 「備考（前回以前）」とchecksheetを比較して、差分があれば「備考」に記載する。 ※「備考（前回以前）」は上書き対象外
                    checksheet_value = asset_data[mng_no]["備考、廃棄（年月)"]
                    __get_diff(diff, row_num, "備考", excel_value, checksheet_value)
                    pass

                case "管理部門":
                    # 上書き不要で比較不要です。
                    pass

                case "管理番号":
                    checksheet_value = mng_no
                    __get_diff(diff, row_num, column_name, excel_value, checksheet_value)

                case "シリアル（参考）":
                    checksheet_value = asset_data[mng_no]["S/N"]
                    __get_diff(diff, row_num, column_name, excel_value, checksheet_value)

                case "稟議番号":
                    checksheet_value = Checksheet.extract_approval_number(
                        asset_data[mng_no]["稟議（取得年月）"]
                    )
                    if excel_value != "" and checksheet_value == "":
                        # 稟議番号を空で上書きするのはNGなのでExcelの値をそのまま適用します。
                        LOG.warning(f"Excel({mng_no}) has approval number but asset data does not. "
                                    f"Applay excel value({excel_value}).")
                    elif checksheet_value is not None:
                        __get_diff(diff, row_num, column_name, excel_value, checksheet_value)

                case "管理者":
                    checksheet_value = asset_data[mng_no]["管理者"]
                    __get_diff(diff, row_num, column_name, excel_value, checksheet_value)
                
                case "使用場所":
                    checksheet_value = asset_data[mng_no]["使用場所"]
                    __get_diff(diff, row_num, column_name, excel_value, checksheet_value)

                case "使用者":
                    checksheet_value = asset_data[mng_no]["使用者"]
                    __get_diff(diff, row_num, column_name, excel_value, checksheet_value)
                
                case _:
                    LOG.error(f"There is an Unexpected column name({column_name}).")
        
        if len(diff[row_num]) == 0:
            diff.pop(row_num)
    
    return diff

def main(
    args: argparse.Namespace
    ) -> None:
    """
    機能1（棚卸リストの自動記入）のメイン関数

    Args:
        args (argparse.Namespace): コマンドライン引数
    """

    Util.init(args.log_level, args.start_date, args.end_date)

    # 棚卸リスト（Excelのワークシート）を読み込みます。
    excel = Excel()
    LOG.info("Attempt to load worksheet.")
    inventory_data = __load_inventory_data(excel, args.file_path, args.sheet_name)
    if inventory_data is None:
        return
    else:
        LOG.info("Successfully load worksheet.")

    # 技術検証機管理表（管理者用ページ）から資産データを取得します。
    LOG.info("Attempt to fetch asset data.")
    asset_data = Util.fetch_asset_data(args.user_id, args.password)
    if asset_data is None:
        return
    else:
        LOG.info("Successfully fetch asset data.")

    # 差分チェックを行います。
    diff = compare(inventory_data, asset_data, args.start_date, args.end_date)
    LOG.debug(f"Differences: {diff}")
    LOG.info(f"There are {len(diff)} differences between worksheet and asset data.")

    # Excelファイルを更新して新規作成します。
    excel.overwrite(diff, args.file_path)
    excel.WORKBOOK.close()  # リソース解放

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export inventory data from the webpage")
    parser.add_argument("-u", "--user_id", type=str, required=True, help="技術検証機管理表のユーザーID")
    parser.add_argument("-p", "--password", type=str, required=True, help="技術検証機管理表のパスワード")
    parser.add_argument("-f", "--file_path", type=str, required=True, help="Excel (実棚リスト) のファイルパス")
    parser.add_argument("-s", "--sheet_name", type=str, required=True, help="Excelのシート名")
    parser.add_argument("-start", "--start_date", type=str, required=True, help="棚卸開始日 例）2024/12/01")
    parser.add_argument("-end", "--end_date", type=str, required=True, help="棚卸終了日 例）2024/12/31")
    parser.add_argument("-l", "--log_level", type=str, required=False, default="info", choices=["debug", "info", "warning", "error"], help="ログレベル")

    args = parser.parse_args()
    main(args)