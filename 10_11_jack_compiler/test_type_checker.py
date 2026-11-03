import contextlib
import io
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from compilation_engine import CompilationEngine
from jack_analyzer import compile_file, process_files
from jack_tokenizer import JackTokenizer
from type_checker import TypeCheckError


class TypeCheckingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def source(self, name, text):
        path = self.root / f"{name}.jack"
        path.write_text(text)
        return path

    def compile(self, source):
        path = self.source("Main", source)
        compile_file(str(path))
        return path.with_suffix(".vm").read_text()

    def test_assignment_types(self):
        invalid = [
            ("int", "true"), ("char", "false"), ("boolean", "1"),
            ("int", '"hello"'), ("String", "123"), ("String", "true"),
            ("Main", '"hello"'), ("int", "null"), ("boolean", "null"),
        ]
        for type_name, expression in invalid:
            with self.subTest(type=type_name, expression=expression):
                with self.assertRaisesRegex(TypeCheckError, "assignment to x: expected"):
                    self.compile(f"""class Main {{ function void main() {{
                        var {type_name} x; let x = {expression}; return;
                    }} }}""")

    def test_expression_types(self):
        invalid = [
            "true + 1", "false - 1", "1 * true", "true / 1", '"a" < 2',
            "false > true", "true & 1", "1 | false", "-true", '-"a"',
            '~"a"', "true = 0", '"a" = false', "null + 1", '"a" = 1',
        ]
        for expression in invalid:
            with self.subTest(expression=expression):
                with self.assertRaisesRegex(TypeCheckError, "operator"):
                    self.compile(f"""class Main {{ function void main() {{
                        var Array sink; let sink[0] = {expression}; return;
                    }} }}""")

    def test_boolean_conditions(self):
        for statement in ("if", "while"):
            for expression in ("1", '"a"', "null", "1 & 2"):
                with self.subTest(statement=statement, expression=expression):
                    with self.assertRaisesRegex(TypeCheckError, f"{statement} condition"):
                        self.compile(f"""class Main {{ function void main() {{
                            {statement} ({expression}) {{ return; }} return;
                        }} }}""")

    def test_array_access_requires_array(self):
        for statement in ("let x[0] = 1;", "let x = x[0];"):
            with self.subTest(statement=statement):
                with self.assertRaisesRegex(TypeCheckError, "array access: expected Array"):
                    self.compile(f"""class Main {{ function void main() {{
                        var int x; {statement} return;
                    }} }}""")

    def test_array_index_requires_numeric_type(self):
        for statement in ("let a[true] = 1;", 'let x = a["a"];'):
            with self.subTest(statement=statement):
                with self.assertRaisesRegex(TypeCheckError, "array index: expected int"):
                    self.compile(f"""class Main {{ function void main() {{
                        var Array a; var int x; {statement} return;
                    }} }}""")

    def test_return_types(self):
        for type_name, statement in [
            ("int", "return;"), ("int", "return true;"),
            ("void", "return 1;"), ("String", "return 1;"),
            ("boolean", "return null;"),
        ]:
            with self.subTest(type=type_name, statement=statement):
                with self.assertRaisesRegex(TypeCheckError, "return: expected"):
                    self.compile(f"class Main {{ function {type_name} f() {{ {statement} }} }}")

    def test_constructor_return_declaration(self):
        for type_name in ("void", "int", "String"):
            with self.subTest(type=type_name):
                with self.assertRaisesRegex(TypeCheckError, "constructor must return Main"):
                    self.compile(f"class Main {{ constructor {type_name} new() {{ return; }} }}")

    def test_void_calls_only_allowed_in_do_statements(self):
        for statement in (
            "let x = Output.println();", "let a[0] = Output.println();",
            "do Output.printInt(Output.println());", "if (Output.println()) { return; }",
            "return Output.println();",
        ):
            with self.subTest(statement=statement):
                with self.assertRaisesRegex(TypeCheckError, "void subroutine"):
                    self.compile(f"""class Main {{ function void main() {{
                        var int x; var Array a; {statement} return;
                    }} }}""")

    def test_os_call_arguments(self):
        for call, message in [
            ("Output.printInt(true)", "argument 1: expected int, got boolean"),
            ("Screen.setColor(1)", "argument 1: expected boolean, got int"),
            ("String.new(false)", "argument 1: expected int, got boolean"),
            ("Output.printString(1)", "argument 1: expected String, got int"),
            ("Output.printInt()", "expected 1 arguments, got 0"),
            ("Output.println(1)", "expected 0 arguments, got 1"),
            ("Output.missing()", "Unknown subroutine: Output.missing"),
        ]:
            with self.subTest(call=call):
                with self.assertRaisesRegex(TypeCheckError, message):
                    self.compile(f"class Main {{ function void main() {{ do {call}; return; }} }}")

    def test_forward_calls_and_recursion_are_checked(self):
        for call in ("Main.later(true)", "later(true)"):
            with self.subTest(call=call):
                with self.assertRaisesRegex(TypeCheckError, "Main.later argument 1"):
                    self.compile(f"""class Main {{
                        function void main() {{ do {call}; return; }}
                        function int later(int n) {{ return later(n - 1); }}
                    }}""")
        vm = self.compile("""class Main {
            function int main() { return later(1); }
            function int later(int n) {
                if (n = 0) { return 0; } return later(n - 1);
            }
        }""")
        self.assertEqual(vm.count("call Main.later 1\n"), 2)
        self.assertNotIn("push pointer 0", vm)

    def test_call_result_type_is_propagated(self):
        with self.assertRaisesRegex(TypeCheckError, "expected boolean, got int"):
            self.compile("""class Main {
                function void main() { var boolean b; let b = Main.number(); return; }
                function int number() { return 1; }
            }""")

    def test_call_receiver(self):
        for declarations, call, message in [
            ("var int x;", "x.f()", "cannot call a method on int"),
            ("", "String.length()", "method requires an instance"),
            ("var String s;", "s.new(1)", "requires a class receiver"),
            ("", "f()", "method requires an instance"),
        ]:
            with self.subTest(call=call):
                with self.assertRaisesRegex(TypeCheckError, message):
                    self.compile(f"""class Main {{
                        function void main() {{ {declarations} do {call}; return; }}
                        method void f() {{ return; }}
                    }}""")

    def test_instance_calls_include_receiver(self):
        vm = self.compile("""class Main {
            field String s;
            constructor Main new() { do f(1); return this; }
            method void f(int n) { do s.setCharAt(n, 65); return; }
        }""")
        self.assertIn("push pointer 0\npush constant 1\ncall Main.f 2\n", vm)
        self.assertIn("call String.setCharAt 3\n", vm)

    def test_instance_argument_types(self):
        with self.assertRaisesRegex(TypeCheckError, "String.setCharAt argument 2"):
            self.compile("""class Main { function void main() {
                var String s; do s.setCharAt(0, true); return;
            } }""")

    def test_this_and_fields_require_instance_context(self):
        for statement in ("do Memory.deAlloc(this);", "let x = 1;"):
            with self.subTest(statement=statement):
                with self.assertRaisesRegex(TypeCheckError, "not available in a function"):
                    self.compile(f"""class Main {{ field int x;
                        function void main() {{ {statement} return; }}
                    }}""")

    def test_numeric_null_array_and_boolean_compatibility(self):
        self.compile("""class Main {
            function void main() {
                var int n; var char c; var boolean b; var Array a;
                var String s; var Main object;
                let c = 65; let n = c; let c = n;
                let n = (n + c) * (3 - 1) / 2;
                let n = -n; let n = ~n; let n = (n & c) | 1;
                let b = (n < c) | (n > 0); let b = ~b & true;
                let b = (s = null) & (null = s);
                let b = (c = n); let b = (b = false);
                let s = null; let object = null; let a = null;
                let a = 2048; let n = a; let a = s; let object = a;
                let a[0] = s; let a[1] = b; let a[2] = null;
                let s = a[0]; let b = a[1]; let n = a[a[2]];
                let b = a[1] & a[2]; let b = ~a[1];
                let n = a[1] | a[2]; let n = ~a[1];
                do Output.printInt(a); do Output.printChar(c);
                if (b) { let n = 1; } while (false) { let n = 0; }
                return;
            }
            function String empty() { return null; }
        }""")

    def test_local_variables_shadow_fields(self):
        self.compile("""class Main { field boolean x;
            function void main() { var int x; let x = 1; return; }
        }""")

    def test_cross_file_calls(self):
        self.source("Other", """class Other {
            function boolean accept(String s) { return true; }
        }""")
        path = self.source("Main", """class Main {
            function void main() { do Other.accept(false); return; }
        }""")
        for compile_files in (lambda: compile_file(str(path)),
                              lambda: process_files(str(p) for p in self.root.glob("*.jack"))):
            with self.subTest(compile_files=compile_files):
                with self.assertRaisesRegex(TypeCheckError, "Other.accept argument 1"):
                    with contextlib.redirect_stdout(io.StringIO()):
                        compile_files()
        path.write_text("""class Main {
            function boolean main() { return Other.accept("hello"); }
        }""")
        compile_file(str(path))
        self.assertIn("call Other.accept 1", path.with_suffix(".vm").read_text())

    def test_supplied_os_source_overrides_builtin_signatures(self):
        self.source("Math", """class Math {
            function boolean custom(boolean b) { return b; }
        }""")
        self.compile("""class Main {
            function boolean main() { return Math.custom(true); }
        }""")

    def test_external_classes_can_be_compiled_separately(self):
        self.compile("""class Main { function void main() {
            var External e; var int n; let e = External.new(1);
            let n = e.value(); do e.dispose(); return;
        } }""")

    def test_duplicate_declarations_are_rejected(self):
        for source, message in [
            ("class Main { function void f() { return; } function void f() { return; } }",
             "duplicate subroutine"),
            ("class Main { function void f(int x, char x) { return; } }",
             "duplicate variable"),
            ("class Main { field int x, x; }", "duplicate variable"),
        ]:
            with self.subTest(source=source):
                with self.assertRaisesRegex(TypeCheckError, message):
                    self.compile(source)

    def test_diagnostic_and_failed_output(self):
        path = self.source("Main", """class Main {
    function void main() {
        var int n;
        let n = true;
        return;
    }
}
""")
        output = path.with_suffix(".vm")
        with self.assertRaisesRegex(TypeCheckError, r"Main\.jack:4:\d+: Main\.main:.*int.*boolean"):
            compile_file(str(path))
        self.assertFalse(output.exists())
        output.write_text("existing VM\n")
        with self.assertRaises(TypeCheckError):
            compile_file(str(path))
        self.assertEqual(output.read_text(), "existing VM\n")
        self.assertEqual(sorted(p.name for p in self.root.iterdir()), ["Main.jack", "Main.vm"])

    def test_cli_reports_type_errors_without_traceback(self):
        path = self.source("Main", """class Main {
            function int main() { return false; }
        }""")
        result = subprocess.run(
            [sys.executable, str(Path(__file__).with_name("jack_analyzer.py")), str(path)],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("expected int, got boolean", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_direct_engine_use_checks_types(self):
        path = self.source("Main", "class Main { function int f() { return true; } }")
        engine = CompilationEngine(JackTokenizer(str(path)), str(path.with_suffix(".vm")))
        try:
            with self.assertRaisesRegex(TypeCheckError, "return: expected int"):
                engine.compileClass()
        finally:
            engine.vmWriter.close()


if __name__ == "__main__":
    unittest.main()
