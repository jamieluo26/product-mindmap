import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("build_map", ROOT / "scripts/build_map.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class BuildMapTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((ROOT / "evals/fixtures/synthetic-map.json").read_text(encoding="utf-8"))

    def test_valid_synthetic_tree_builds_without_unresolved_tokens(self):
        self.assertEqual(module.validate(self.data), 10)
        rendered = module.build(self.data)
        self.assertNotIn("__MAP_", rendered)
        self.assertNotIn("__MINDMAP_", rendered)
        self.assertIn("reading-plan-demo", rendered)
        self.assertIn('"status":"pending"', rendered)
        self.assertIn('"status":"suggested"', rendered)
        self.assertIn('"status":"confirmed"', rendered)

    def test_large_synthetic_tree_preserves_nodes(self):
        data = copy.deepcopy(self.data)
        branch = data["root"]["children"][0]
        branch["children"] = [
            {"id": f"item-{i}", "title": f"Synthetic item {i}", "status": "suggested", "facts": [], "children": []}
            for i in range(40)
        ]
        self.assertEqual(module.validate(data), 48)
        rendered = module.build(data)
        self.assertIn('"id":"item-39"', rendered)

    def test_script_termination_and_html_title_are_escaped(self):
        self.data["root"]["facts"] = [["payload", "</script><script>alert(1)</script>\u2028\u2029"]]
        self.data["root"]["title"] = "<Demo & review>"
        rendered = module.build(self.data, standalone=True)
        self.assertNotIn("</script><script>alert(1)", rendered)
        self.assertIn("\\u003c/script>", rendered)
        self.assertIn("&lt;Demo &amp; review&gt;", rendered)
        self.assertTrue(rendered.lower().startswith("<!doctype html>"))

    def test_duplicate_ids_and_missing_status_are_rejected(self):
        duplicate = copy.deepcopy(self.data)
        duplicate["root"]["children"][1]["id"] = "scope"
        with self.assertRaises(ValueError):
            module.build(duplicate)
        del self.data["root"]["children"][0]["status"]
        with self.assertRaises(ValueError):
            module.build(self.data)

    def test_unknown_initial_state_and_nested_side_are_rejected(self):
        bad = copy.deepcopy(self.data)
        bad["initialSelected"] = "missing-node"
        with self.assertRaises(ValueError):
            module.validate(bad)
        bad = copy.deepcopy(self.data)
        bad["root"]["children"][0]["children"][0]["side"] = "left"
        with self.assertRaises(ValueError):
            module.validate(bad)

    def test_excessive_depth_is_rejected(self):
        branch = self.data["root"]["children"][0]
        branch["children"] = []
        for i in range(11):
            child = {"id": f"deep-{i}", "title": "Synthetic depth", "status": "pending", "facts": [], "children": []}
            branch["children"] = [child]
            branch = child
        with self.assertRaises(ValueError):
            module.validate(self.data)

    def test_node_and_main_branch_limits(self):
        data = copy.deepcopy(self.data)
        branch = data["root"]["children"][0]
        data["root"]["children"] = [branch]
        branch["children"] = [
            {"id": f"limit-{i}", "title": "Synthetic limit", "status": "pending", "facts": [], "children": []}
            for i in range(198)
        ]
        data["initialExpanded"] = ["root", "scope"]
        self.assertEqual(module.validate(data), 200)
        branch["children"].append({"id": "limit-extra", "title": "Too many", "status": "pending", "facts": [], "children": []})
        with self.assertRaises(ValueError):
            module.validate(data)
        data = copy.deepcopy(self.data)
        data["root"]["children"] = []
        with self.assertRaises(ValueError):
            module.validate(data)
        data["root"]["children"] = [
            {"id": f"branch-{i}", "title": "Synthetic branch", "status": "pending", "facts": [], "children": []}
            for i in range(9)
        ]
        with self.assertRaises(ValueError):
            module.validate(data)

    def test_cli_check_has_success_and_failure_paths(self):
        with tempfile.TemporaryDirectory() as task_dir:
            output = Path(task_dir) / "map.html"
            command = [sys.executable, "-B", str(ROOT / "scripts/build_map.py"), str(ROOT / "evals/fixtures/synthetic-map.json"), str(output), "--standalone"]
            created = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(created.returncode, 0, created.stderr)
            check = subprocess.run(command + ["--check"], capture_output=True, text=True)
            self.assertEqual(check.returncode, 0, check.stderr)
            output.write_text("changed", encoding="utf-8")
            mismatch = subprocess.run(command + ["--check"], capture_output=True, text=True)
            self.assertNotEqual(mismatch.returncode, 0)
            self.assertEqual(output.read_text(encoding="utf-8"), "changed")


if __name__ == "__main__":
    unittest.main()
