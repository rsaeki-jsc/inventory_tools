import argparse

from lib.log import LOG
from lib.checksheet import Checksheet
from lib.util import Util

def main(
    args: argparse.Namespace
    ) -> None:
    """
    機能2（棚卸の実施確認）のメイン関数

    Args:
        args (argparse.Namespace): コマンドライン引数
    """

    Util.init("info", args.start_date, args.end_date)

    # 技術検証機管理表（管理者用ページ）から資産データを取得します。
    LOG.info("Attempt to fetch asset data.")
    asset_data = Util.fetch_asset_data(args.user_id, args.password)
    if asset_data is None:
        return
    else:
        LOG.info("Successfully fetch asset data.")

    targets = 0
    unconfirmed = 0
    for mng_no in asset_data.keys():
        is_target = True
        if asset_data[mng_no]["管理部署"] != args.department:
            is_target = False
        if args.where != "everywhere":
            if args.where not in asset_data[mng_no]["使用場所"]:
                is_target = False
        if asset_data[mng_no]["棚卸対象外"] not in args.targets:
            is_target = False
        
        if is_target:
            targets += 1
            if not Checksheet.exist(
                asset_data[mng_no]["存在確認"],
                asset_data[mng_no]["最終棚卸確認日"],
                args.start_date,
                args.end_date
                ):
                unconfirmed += 1
                LOG.warning(f"Unconfirmed asset information.\n"
                            f"管理番号: {mng_no}\n"
                            # f"登録日: {asset_data[mng_no]["登録日"]}\n"
                            # f"登録者: {asset_data[mng_no]["登録者"]}\n"
                            # f"稟議（取得年月）: {asset_data[mng_no]["稟議（取得年月）"]}\n"
                            f"メーカ: {asset_data[mng_no]["メーカ"]}\n"
                            f"製品名型番: {asset_data[mng_no]["製品名型番"]}\n"
                            # f"S/N: {asset_data[mng_no]["S/N"]}\n"
                            f"カテゴリ: {asset_data[mng_no]["カテゴリ"]}\n"
                            # f"用途: {asset_data[mng_no]["用途"]}\n"
                            # f"保守情報: {asset_data[mng_no]["保守情報"]}\n"
                            # f"ライセンス情報: {asset_data[mng_no]["ライセンス情報"]}\n"
                            # f"管理部署: {asset_data[mng_no]["管理部署"]}\n"
                            f"管理者: {asset_data[mng_no]["管理者"]}\n"
                            f"使用場所: {asset_data[mng_no]["使用場所"]}\n"
                            f"使用者: {asset_data[mng_no]["使用者"]}\n"
                            f"貸出状況: {asset_data[mng_no]["貸出状況"]}\n"
                            f"棚卸対象外: {asset_data[mng_no]["棚卸対象外"]}\n"
                            # f"棚卸し対象外理由: {asset_data[mng_no]["棚卸し対象外理由"]}\n"
                            f"存在確認: {asset_data[mng_no]["存在確認"]}\n"
                            f"最終棚卸確認日: {asset_data[mng_no]["最終棚卸確認日"]}\n"
                            f"最終棚卸確認者: {asset_data[mng_no]["最終棚卸確認者"]}\n"
                            f"備考、廃棄（年月): {asset_data[mng_no]["備考、廃棄（年月)"]}\n")
    
    if unconfirmed == 0:
        LOG.info("The inventory of all assets has been completed!")
    else:
        LOG.info(f"Not checked {unconfirmed}/{targets}.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Show assets that have not been inventoried.")
    parser.add_argument("-u", "--user_id", type=str, required=True, help="技術検証機管理表のユーザーID")
    parser.add_argument("-p", "--password", type=str, required=True, help="技術検証機管理表のパスワード")
    parser.add_argument("-start", "--start_date", type=str, required=True, help="棚卸開始日 例）2024/12/01")
    parser.add_argument("-end", "--end_date", type=str, required=True, help="棚卸終了日 例）2024/12/31")
    parser.add_argument("-d", "--department", type=str, required=False, default="RevoWorks BU 開発部",
                        help="フィルター（type: is）：技術資産管理表の「管理部署」 例）RevoWorks BU 開発部")
    parser.add_argument("-w", "--where", type=str, required=False, default="everywhere",
                        help="フィルター（type: include）：技術資産管理表の「使用場所」 例）9F")
    parser.add_argument("-t", "--targets", nargs="*", required=False, default="対象 未確認",
                        help="フィルター（type: is）：技術資産管理表の「棚卸対象外」 例）対象 未確認 〇")

    args = parser.parse_args()
    main(args)