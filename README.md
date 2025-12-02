# Nand2Tetris

[Nand2Tetris](https://www.nand2tetris.org/)（『[コンピュータシステムの理論と実装 第2版](https://www.oreilly.co.jp/books/9784814400874/)』）の自分なりの実装です。

## プロジェクトレイアウト

- `01_boolean_logic` – 第1章 ブール論理。基本の論理ゲートをHDLで作っています。
- `02_boolean_arithmetic` – 第2章 ブール算術。加算器やALUなど、計算に使う部品です。
- `03_memory` – 第3章 メモリ。レジスタやカウンタ、RAMを積み上げています。
- `04_machine_language` – 第4章 機械語。アセンブリで動作確認用のプログラムを書いています。
- `05_computer_architecture` – 第5章 コンピュータアーキテクチャ。CPUとメモリを組み合わせてHackコンピュータを完成させます。
- `06_assembler` – 第6章 アセンブラ。アセンブリをマシンコードに変換します。
- `07_08_vm` – 第7〜8章 VMトランスレータ。仮想マシンコードをアセンブリに変換します。
- `10_11_jack_compiler` – 第10〜11章 Jackコンパイラ。Jack言語をVMコードに変換します。
- `12_jack_os` – 第12章 Jack標準ライブラリ。

第6〜8章（アセンブラとVMトランスレータ）と第10〜11章（Jackコンパイラ）はPythonで書いてあります。
