"""Regression tests compile and execute generated code with a real JDK."""

from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from jack_parser import TranspileError
from jack_transpiler import transpile


ROOT = Path(__file__).resolve().parent
SAMPLES = ROOT.parent / "10_11_jack_compiler" / "sample"


class DiagnosticsTests(unittest.TestCase):
    def test_invalid_sources_do_not_create_partial_output(self):
        cases = [
            ("class Main {} trailing", "Expected eof"),
            ("class Main { /*", "Unterminated comment"),
            ('class Main { function void main() { do Output.printString("oops); } }', "Unterminated string"),
            ("class Main { function int f() { return 32768; } }", "Integer constant"),
            ("class Main { function int f() { return 12abc; } }", "cannot start with a digit"),
            ("class Main { function void f() { let missing = 0; return; } }", "Undefined variable"),
            ("class Main { field int x, x; }", "Duplicate variable"),
            ("class Main { function void f(int x) { var int x; return; } }", "Duplicate variable"),
            ("class Main { function void f() { return; } function void f() { return; } }", "Duplicate subroutine"),
            ("class Main { constructor int new() { return 0; } }", "constructor must return"),
            ("class Main { field int x; function int f() { return x; } }", "instance field"),
            ("class Main { function Main f() { return this; } }", "no 'this'"),
            ("class Main { method void f() { return; } function void g() { do Main.f(); return; } }", "requires an object"),
            ("class Main { function void f() { do Output.printInt(); return; } }", "Expected 1 arguments"),
            ("class Main { function void f() { do Output.typo(); return; } }", "Unknown subroutine"),
            ("class Main { function int f() { return Output.println(); } }", "void subroutine"),
            ("class Main { function int f() { return; } }", "Return value"),
            ("class Main { function void f() { return 1; } }", "Return value"),
        ]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, output = root / "Main.jack", root / "output"
            for text, message in cases:
                with self.subTest(message=message):
                    source.write_text(text, encoding="utf-8")
                    with self.assertRaisesRegex(TranspileError, message) as caught:
                        transpile(source, output)
                    self.assertRegex(str(caught.exception), r"Main\.jack:\d+:\d+:")
                    self.assertFalse(output.exists())

    def test_duplicate_classes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "First.jack").write_text("class Same {}", encoding="utf-8")
            (root / "Second.jack").write_text("class Same {}", encoding="utf-8")
            with self.assertRaisesRegex(TranspileError, "Duplicate class"):
                transpile(root, root / "output")

    def test_cli_reports_invalid_path_without_traceback(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "jack_transpiler.py"), str(ROOT / "missing.jack")],
            capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 1)
        self.assertIn("Specify an existing", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_default_output_uses_declared_class_name(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "DifferentName.jack"
            source.write_text("class Example {}", encoding="utf-8")
            generated = transpile(source)
            self.assertEqual([path.name for path in generated], ["Example.java", "JackRuntime.java"])
            self.assertTrue(all(path.is_file() for path in generated))


@unittest.skipUnless(shutil.which("javac") and shutil.which("java"), "A JDK is required")
class ExecutionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def compile(self, source: Path, label: str = "program") -> Path:
        output = self.root / label
        generated = transpile(source, output)
        result = subprocess.run(
            ["javac", "-encoding", "UTF-8", "-d", str(output)] + [str(path) for path in generated],
            capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        return output

    def execute(self, output: Path, stdin: str = "") -> str:
        result = subprocess.run(
            ["java", "-cp", str(output), "Main"], input=stdin,
            capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def program(self, main: str, extra=None) -> str:
        source = self.root / "source"
        source.mkdir()
        for name, text in {"Main.jack": main, **(extra or {})}.items():
            (source / name).write_text(text, encoding="utf-8")
        return self.execute(self.compile(source))

    def test_all_existing_sample_projects_compile(self):
        for source in sorted(SAMPLES.iterdir()):
            if source.is_dir():
                with self.subTest(project=source.name):
                    self.compile(source, source.name)

    def test_seven(self):
        self.assertEqual(self.execute(self.compile(SAMPLES / "Seven")), "7")

    def test_complex_arrays_preserve_object_addresses(self):
        expected = "".join(
            f"Test {index}: expected result: {value}; actual result: {value}\n"
            for index, value in enumerate((5, 40, 0, 77, 110), 1))
        self.assertEqual(self.execute(self.compile(SAMPLES / "ComplexArrays")), expected)

    def test_average_with_console_input(self):
        output = self.compile(SAMPLES / "Average")
        self.assertEqual(self.execute(output, "3\n10\n20\n30\n"),
                         "How many numbers? Enter a number: Enter a number: Enter a number: The average is 20")

    def test_word_arithmetic_precedence_and_evaluation_order(self):
        expressions = [
            ("2 + 3 * 4", 20), ("2 + (3 * 4)", 14),
            ("32767 + 1", -32768), ("-32767 - 2", 32767),
            ("300 * 300", 24464), ("-7 / 2", -3),
            ("~true", 0), ("(true & false) | true", -1),
            ("1 < 2", -1), ("2 > 3", 0), ("null = 0", -1),
            ("false & Main.bump()", 0), ("count", 1),
            ("Main.bump() + Main.bump()", 5), ("Main.factorial(6)", 720),
        ]
        statements = "\n".join(
            f"do Output.printInt({expression}); do Output.println();" for expression, _ in expressions)
        source = """
            class Main {
                static int count;
                function int bump() { let count = count + 1; return count; }
                function int factorial(int n) {
                    if (n < 2) { return 1; } else { return n * Main.factorial(n - 1); }
                }
                function void main() { BODY return; }
            }
        """.replace("BODY", statements)
        self.assertEqual(self.program(source), "".join(f"{value}\n" for _, value in expressions))

    def test_constructors_methods_static_fields_and_shadowing(self):
        main = """
            class Main {
                function void main() {
                    var Counter first, second;
                    let first = Counter.make(10);
                    let second = Counter.make(20);
                    do first.add(5);
                    do Output.printInt(first.get()); do Output.println();
                    do Output.printInt(second.get()); do Output.println();
                    do Output.printInt(first.shadow(99)); do Output.println();
                    do Output.printInt(Counter.total()); do Output.println();
                    do first.dispose(); do second.dispose();
                    return;
                }
            }
        """
        counter = """
            class Counter {
                field int value;
                static int count;
                constructor Counter make(int initial) {
                    let count = count + 1;
                    do set(initial);
                    return this;
                }
                method void set(int initial) { let value = initial; return; }
                method void add(int increment) { let value = value + increment; return; }
                method int get() { return value; }
                method int shadow(int value) { return value; }
                method void dispose() { do Memory.deAlloc(this); return; }
                function int total() { return count; }
            }
        """
        self.assertEqual(self.program(main, {"Counter.jack": counter}), "15\n20\n99\n2\n")

    def test_native_strings_heap_recycling_and_screen_memory(self):
        source = r'''
            class Main {
                function void main() {
                    var String text;
                    var Array first, second, block;
                    var int i;
                    let text = String.new(8);
                    do text.appendChar(45); do text.appendChar(55);
                    do Output.printInt(text.intValue()); do Output.println();
                    do text.setInt(-32767 - 1);
                    do Output.printString(text); do Output.println();
                    do Output.printInt(text.length()); do Output.println();
                    do text.eraseLastChar(); do text.setCharAt(1, 49);
                    do Output.printString(text); do Output.println();
                    do text.dispose();
                    let first = Memory.alloc(100);
                    let second = Memory.alloc(100);
                    do Memory.deAlloc(first); do Memory.deAlloc(second);
                    let block = Memory.alloc(200);
                    do Output.printInt(block = first); do Output.println();
                    do block.dispose();
                    while (i < 500) {
                        let block = Array.new(100); do block.dispose(); let i = i + 1;
                    }
                    do Screen.drawPixel(15, 0);
                    do Output.printInt(Memory.peek(16384)); do Output.println();
                    do Screen.setColor(false); do Screen.drawPixel(15, 0);
                    do Output.printInt(Memory.peek(16384)); do Output.println();
                    do Screen.setColor(true); do Screen.drawRectangle(0, 1, 15, 1);
                    do Output.printInt(Memory.peek(16416)); do Output.println();
                    do Output.printString("// text /* with comments */ and \ path");
                    return;
                }
            }
        '''
        self.assertEqual(self.program(source),
                         "-7\n-32768\n6\n-1276\n-1\n-32768\n0\n-1\n// text /* with comments */ and \\ path")

    def test_java_identifier_collisions(self):
        main = """
            class Main {
                function void main() {
                    var record switch;
                    let switch = record.new();
                    do Output.printInt(switch.yield());
                    return;
                }
            }
        """
        record = """
            class record {
                constructor record new() { return this; }
                method int yield() { return 42; }
            }
        """
        extra = {"record.jack": record, "Integer.jack": "class Integer {}",
                 "java.jack": "class java {}", "JackRuntime.jack": "class JackRuntime {}",
                 "J_record.jack": "class J_record {}"}
        self.assertEqual(self.program(main, extra), "42")

    def test_string_literals_use_supplied_string_class(self):
        source = """
            class Main {
                function void main() {
                    var String s;
                    let s = "abc";
                    do Output.printInt(s.length());
                    return;
                }
            }
        """
        string = """
            class String {
                field int count;
                constructor String new(int capacity) { let count = 0; return this; }
                method String appendChar(char c) { let count = count + 1; return this; }
                method int length() { return count; }
            }
        """
        self.assertEqual(self.program(source, {"String.jack": string}), "3")

    def test_sys_halt_returns_from_java_entry_point(self):
        source = """
            class Main {
                function void main() {
                    do Output.printInt(1); do Sys.halt(); do Output.printInt(2);
                    return;
                }
            }
        """
        self.assertEqual(self.program(source), "1")

    def test_jack_os_sources_compile(self):
        source = self.root / "os-source"
        source.mkdir()
        for path in (ROOT.parent / "12_jack_os").glob("*.jack"):
            shutil.copyfile(path, source / path.name)
        (source / "Main.jack").write_text(
            "class Main { function void main() { return; } }", encoding="utf-8")
        self.compile(source)


if __name__ == "__main__":
    unittest.main()
