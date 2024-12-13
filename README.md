## 概要
棚卸作業の工数削減を目的としたツール群
## 環境
動作確認済み：WSL2（Ubuntu 20.04 LTS）
※ 上記以外の環境は未確認だが、Pythonを実行可能な環境であればどこでも使える想定
## 環境構築
### Python
動作確認済み：3.12.5
最小要件：3.10.0
→ match文を使用しているため
#### pyenv（任意）
特定のバージョンのPythonをインストールしたい場合はpyenvを使用する。
##### 1. pyenvのインストール
```
sudo apt install -y build-essential libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev libncursesw5-dev xz-utils tk-dev libffi-dev liblzma-dev python3-openssl git
curl https://pyenv.run | bash
```
##### 2. pyenvの環境設定
```
export PATH="$HOME/.pyenv/bin:$PATH"
eval "$(pyenv init --path)"
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"
```
##### 3. 環境設定の反映
```
source ~/.bashrc
```
##### 4. Pythonのインストール
```
pyenv install 3.12.5
```
##### 5. Pythonのバージョン設定
```
pyenv global 3.12.5
```
### poetry
動作確認済み：1.8.3, 1.8.5
#### 1. poetryのインストール
```
curl -sSL https://install.python-poetry.org | python3 -
```
#### 2. 仮想環境のセットアップ
```
inventory_tool/work> poetry install
```
## 利用方法
### 機能1：棚卸リストの自動記入
```
inventory_tool/work> poetry run python src/main.py -u <user_id> -p <password> -f <file_path> -s <sheet_name> -start <start_date> -end <end_date>
```
#### ヘルプの表示
コマンドライン引数について確認したい場合はヘルプで確認できる。
```
inventory_tool/work> poetry run python src/main.py -h
```
#### 仕様
- 棚卸リスト（Excel）と技術資産管理表の内容を比較し、棚卸リストに差分を上書きして保存する
- 上書き箇所は赤字にする　※「棚卸結果」を除く
- 棚卸リストの「棚卸結果」は、以下の条件（AND）を満たす場合は「〇」、満たさない場合は「×」で上書きする
    - 技術資産管理表の「存在確認」が「○」であること
    - 技術資産管理表の「最終棚卸確認日」が棚卸実施期間内（start_date <= x <= end_date）であること
### 機能2：棚卸の実施確認
```
inventory_tool/work> poetry run python src/checker.py -u <user_id> -p <password> -start <start_date> -end <end_date>
```
#### ヘルプの表示
コマンドライン引数について確認したい場合はヘルプで確認できる。
```
inventory_tool/work> poetry run python src/checker.py -h
```
#### 仕様
- 棚卸が未実施である資産情報をコンソールに表示する
- 以下の条件（AND）を満たす場合は棚卸実施済み、満たさない場合は棚卸未実施と判定する
    - 技術資産管理表の「存在確認」が「○」であること
    - 技術資産管理表の「最終棚卸確認日」が棚卸実施期間内（start_date <= x <= end_date）であること
- 以下の情報は非表示
    - 登録日
    - 登録者
    - 稟議（取得年月）
    - S/N
    - 用途
    - 保守情報
    - ライセンス情報
    - 管理部署
    - 棚卸し対象外理由