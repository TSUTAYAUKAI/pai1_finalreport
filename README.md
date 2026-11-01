# Physical AI 応用1 最終課題 — Windows + Dockerで最短実行

これは講義第4回・第5回で使用したDockerイメージを再利用する手順です。
講義で使用されたイメージ: `airobotbook/ros2-desktop-ai-robot-book-humble:latest`
ROS 2 Humble、turtlesim、GUI(VNC)を含む講義用デスクトップ環境を使用します。

## 1. 事前準備

- Windowsに Docker Desktop をインストール・起動
- Docker Desktop の **Settings > General > Use WSL 2 based engine** を使用（環境によって設定が見えない場合もあります）
- コンテナは Linux containers モードで実行
- PowerShell で次のコマンドを実行し、Docker Engineが起動していることを確認

```powershell
docker --version
docker compose version
docker info
```

※ WSL 2 は Docker Desktop のバックエンドです。WSL側にROS 2を直接インストールする必要はありません。

## 2. 起動

このフォルダ（`compose.yaml`と`ai_spiral_turtle.py`がある場所）を展開し、
エクスプローラーで開き、アドレスバーに `powershell` と入力してEnter。

```powershell
docker compose up -d
```

Docker image の初回ダウンロードは大きい場合があります。
画面が開かない場合は `docker compose ps` と `docker compose logs` で状態を確認します。

## 3. ブラウザでデスクトップを開く

Chrome / Edge から次にアクセス。

http://localhost:6080/

画面の「接続」ボタンがあれば押す。パスワードを求められたら `ubuntu`（上記イメージの公開READMEに記載）。
画面内のTerminalを2つ開く。

## 4. ROS 2 を起動

**ブラウザのデスクトップ内ターミナルA:**

```bash
source /opt/ros/humble/setup.bash
ros2 run turtlesim turtlesim_node
```

**ブラウザのデスクトップ内ターミナルB:**

```bash
source /opt/ros/humble/setup.bash
cd /workspace
python3 ai_spiral_turtle.py
```

亀が動き、四角い渦巻きが描かれたら成功。`DONE!` と表示されます。

## 5. 再撮影

実行をもう一度やりたい場合、ターミナルBで Ctrl+C、ターミナルAで Ctrl+C を押し、
ターミナルAで再び `ros2 run turtlesim turtlesim_node` を実行してから、
ターミナルBで再び `python3 ai_spiral_turtle.py` を実行します。

## 6. 動画・提出

- Windowsの画面録画機能などでturtlesimのブラウザ画面を録画
- 動画の長さは1〜3分（最終課題指定）。倍速にしたときは倍速明記
- 本フォルダのPythonコードを公開GitHubリポジトリへ置く
- レポートPDFの内容を実際の試行結果に合わせて確認・修正し、OmniCampusアカウント名/IDでリネームする
- 自分の氏名・所属・メールアドレスなどの個人情報をPDF/コード/動画に含めない
- YouTubeに最低「限定公開」で投稿し、OmniCampusで指定情報を提出

## 7. 終了

PowerShellで（このフォルダ内から）:

```powershell
docker compose down
```

## トラブル対応

- `docker: command not found` → Docker Desktopをインストールして起動
- `Cannot connect to Docker daemon` → Docker Desktopが起動しているか確認
- `port is already allocated` → 別のコンテナが6080を使っている。`docker ps`で確認。既存コンテナは無断削除しない。
- `ros2: command not found` → `source /opt/ros/humble/setup.bash` を実行
- `ModuleNotFoundError: rclpy` → コンテナのターミナルで実行しているかを確認
- `No such file` → `ls -l /workspace/ai_spiral_turtle.py` でマウント確認
- 動画撮影前にAIが完走した → デスクトップ内のターミナルBは手動実行なので、録画開始後に再実行

## 出典

- 講義第4回「今回の講義の準備」：VNC付きROS 2イメージの起動
- 講義第5回「演習環境の準備」：デスクトップ表示、turtlesim、Dockerボリューム・ポート
- https://github.com/AI-Robot-Book-Humble/docker-ros2-desktop-ai-robot-book-humble
- https://docs.docker.com/desktop/features/wsl/
