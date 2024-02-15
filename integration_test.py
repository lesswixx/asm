import contextlib
import io
import os
import tempfile

import machine
import pytest
import translator


@pytest.mark.golden_test("golden/*.yml")
def test_translator_and_machine(golden, caplog):
    with tempfile.TemporaryDirectory() as tmpdirname:
        source = os.path.join(tmpdirname, "source")
        input_stream = os.path.join(tmpdirname, "input")
        target = os.path.join(tmpdirname, "target")

        with open(source, "w", encoding="utf-8") as file:
            file.write(golden["in_source"])
        with open(input_stream, "w", encoding="utf-8") as file:
            file.write(golden["in_stdin"])

        with contextlib.redirect_stdout(io.StringIO()) as stdout:
            with open(source, encoding="utf-8") as s, open(target, "w", encoding="utf-8") as t:
                translator.main(s, t)

            with open(target, encoding="utf-8") as t:
                assert t.read() == golden.out["out_code"]

            with open(target, encoding="utf-8") as t, open(input_stream, encoding="utf-8") as i:
                machine.main(t, i)

        assert stdout.getvalue() == golden.out["out_stdout"]
        assert caplog.text == golden.out["out_log"]
