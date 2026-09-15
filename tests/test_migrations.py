import io
import unittest

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory


class MigrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = Config("alembic.ini")

    def test_revision_chain_has_one_head_and_base(self):
        scripts = ScriptDirectory.from_config(self.config)

        self.assertEqual(scripts.get_heads(), ["20260915_0001"])
        revision = scripts.get_revision("20260915_0001")
        self.assertIsNone(revision.down_revision)

    def test_initial_migration_renders_complete_offline_sql(self):
        output = io.StringIO()
        self.config.output_buffer = output

        command.upgrade(self.config, "head", sql=True)

        sql = output.getvalue()
        self.assertEqual(sql.count("CREATE TABLE"), 7)  # Six CRM tables + alembic_version.
        self.assertIn("CREATE TYPE opportunity_stage", sql)
        self.assertIn("CREATE TYPE task_status", sql)
        self.assertIn("CREATE TABLE activities", sql)
        self.assertIn("CREATE TABLE tasks", sql)
        self.assertIn("FOREIGN KEY(opportunity_id, company_id)", sql)
        self.assertIn("INSERT INTO alembic_version", sql)


if __name__ == "__main__":
    unittest.main()
