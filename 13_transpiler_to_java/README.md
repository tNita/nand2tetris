# Jack → Java トランスパイラ

Jackのソースコードを、`javac`でコンパイルして実行できるJavaソースコードに変換します。
Pythonの標準ライブラリだけで動作し、既存のVMコンパイラには依存しません。

## 実行方法

Python 3.9以上とJDK 17以上を使用します。以下はリポジトリのルートで実行します。

```sh
python3 13_transpiler_to_java/jack_transpiler.py \
  10_11_jack_compiler/sample/Seven \
  -o 13_transpiler_to_java/build/Seven

javac -encoding UTF-8 13_transpiler_to_java/build/Seven/*.java
java -cp 13_transpiler_to_java/build/Seven Main
# 7
```

入力には`.jack`ファイルまたはディレクトリを指定します。ディレクトリの場合は、直下の
すべての`.jack`ファイルをまとめて変換します。サブディレクトリは探索しません。
複数クラスを使うプログラムでは、ディレクトリを指定してください。

`-o`（`--output-dir`）を省略すると、入力と同じディレクトリに出力します。
クラスごとの`.java`と、実行に必要な`JackRuntime.java`を生成します。
引数なしの`function main`を持つクラスにはJavaのエントリーポイントも生成します。

```sh
python3 13_transpiler_to_java/jack_transpiler.py \
  10_11_jack_compiler/sample/Average -o 13_transpiler_to_java/build/Average
javac -encoding UTF-8 13_transpiler_to_java/build/Average/*.java
printf '3\n10\n20\n30\n' | java -cp 13_transpiler_to_java/build/Average Main
```

## 変換の方針

Jackのクラス、変数宣言、コンストラクタ、関数、メソッド、およびすべての文と式に対応します。
演算子はJackと同じ優先順位で左から評価し、括弧を保持します。

Jackでは整数、真偽値、配列、オブジェクト参照がすべて16ビットの値です。
この性質を維持するため、生成するJavaでも値を`int`で表し、演算結果を16ビットに丸めます。
`true`は`-1`、`false`と`null`は`0`です。`&`と`|`は両辺を評価します。

オブジェクトのフィールドと配列はランタイムのRAMに格納します。これにより、
`ComplexArrays`のように配列に配列のアドレスを保存するコードや、`Memory.peek/poke`も動作します。
RAMは32,768ワードで、標準ランタイムのヒープ範囲は2048〜16383です。
`dispose`や`Memory.deAlloc`で解放した領域は再利用します。

Javaのメンバー名には`j_`を付け、Jackのメソッドは先頭引数に`j_this`を取る
`static`メソッドへ変換します。コンストラクタはメモリを確保して参照を返す関数です。
`void`関数もJavaでは`int`を返し、`return;`を`return 0;`へ変換します。
通常のクラス名はそのまま使用しますが、Javaの予約語、`java`、`JackRuntime`、
`J_`で始まる名前には`J_`を付けます。出力ファイル名は変換後のクラス名になります。

## 標準ライブラリ

`JackRuntime.java`には以下のJack OS互換APIを含みます。

| クラス | 動作 |
| --- | --- |
| `Array`, `Memory` | 配列、RAMの読み書き、領域の確保と解放 |
| `Math` | 16ビットの乗除算、絶対値、最大・最小値、平方根 |
| `String` | 文字列の作成・変更、文字の追加・削除、整数との変換 |
| `Output` | 標準出力への文字列・整数出力。カーソル移動はANSIエスケープシーケンス |
| `Keyboard` | 標準入力から文字・行・整数を取得 |
| `Screen` | RAMのスクリーン領域へのピクセル・線・長方形・円の描画 |
| `Sys` | 初期化、待機、終了、エラー通知 |

画面ウィンドウは表示しません。描画結果は`Memory.peek`で確認できます。
`Keyboard.keyPressed()`はRAM[24576]を読み、通常は`0`を返します。
リアルタイムのキー操作を使う`Square`や`Pong`はJavaにコンパイルできますが、
対話的に遊ぶためのGUIは含みません。コンソール入力には`readChar/readLine/readInt`を使用します。
改行とバックスペースのJack文字コードは、それぞれ128と129です。

通常の起動では生成した`main`を直接呼びます。標準ランタイムは読み込み時点で利用可能です。
`Sys.halt()`で正常終了し、`Sys.error()`や不正なRAMアクセスではJavaの例外を送出します。
入力にOSクラス自身を含めた場合は、そのクラスの実装を優先します。独自OSを使用するときは、
必要な初期化をJack側から呼び出してください。独自のメモリアロケータや文字列レイアウトを
使う場合は、それらを扱うOSクラスも一緒に用意してください。

構文エラー、未定義変数、重複定義、既知のサブルーチンの引数数や呼び方の誤りなどは、
入力ファイル名・行・列とともに報告します。完全な型検査は行いません。
別途変換するクラスへの参照は許可します。すべての入力を検査してからファイルを書き出します。

## テスト

```sh
bash 13_transpiler_to_java/run_regression_tests.sh
```

既存サンプルのJavaコンパイルに加え、`Seven`、`Average`、`ComplexArrays`の実行結果、
16ビット演算、評価順序、オブジェクト、文字列、メモリの再利用、画面RAM、診断を検証します。
生成物は一時ディレクトリに置き、テスト終了時に削除します。

## ファイル構成

- `jack_transpiler.py`: CLI、入力ファイルの収集、出力
- `jack_parser.py`: 字句解析、構文解析、構文木
- `java_writer.py`: 名前の解決、呼び出しの検査、Javaコード生成
- `runtime/JackRuntime.java`: Java上でJackの値とOS機能を扱うランタイム
- `test_transpiler.py`: Javaコードのコンパイル・実行を含む回帰テスト
