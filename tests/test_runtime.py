import unittest
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock

from langchain_core.runnables import RunnableLambda
from pydantic import SecretStr
from sqlalchemy.orm import Session

from backend.app.core.config import Settings
from backend.app.core.exceptions import ResourceNotFoundError
from backend.app.models import Activity, Company, Opportunity, Task, User
from backend.app.models.enums import OpportunityStage, TaskStatus
from backend.app.agent import (
    CRMContext,
    CRMContextProvider,
    DealAnalysis,
    DealRuntime,
    NextAction,
    create_deepseek_model,
    initialize_runtime,
)


class CRMContextProviderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.provider = CRMContextProvider(
            MagicMock(spec=Session),
            activity_limit=1,
            task_limit=1,
        )
        self.provider.opportunities = MagicMock()

    def test_builds_bounded_context_with_recent_activity_and_open_task(self):
        now = datetime.now(UTC)
        owner = User(id=20, name="Owner", email="owner@example.test")
        company = Company(id=10, name="Customer", owner_id=20)
        opportunity = Opportunity(
            id=30,
            name="Deal",
            company_id=10,
            owner_id=20,
            amount=Decimal("12000.00"),
            stage=OpportunityStage.QUALIFIED,
            probability=45,
            expected_close_date=date.today() + timedelta(days=14),
            company=company,
            owner=owner,
        )
        opportunity.activities = [
            Activity(
                id=40,
                summary="Old call",
                occurred_at=now - timedelta(days=2),
                performed_by_id=20,
            ),
            Activity(
                id=41,
                summary="Recent demo",
                occurred_at=now - timedelta(days=1),
                performed_by_id=20,
            ),
        ]
        opportunity.tasks = [
            Task(
                id=50,
                title="Later task",
                assignee_id=20,
                status=TaskStatus.TODO,
                due_at=now + timedelta(days=2),
            ),
            Task(
                id=51,
                title="First task",
                assignee_id=20,
                status=TaskStatus.IN_PROGRESS,
                due_at=now + timedelta(days=1),
            ),
            Task(
                id=52,
                title="Completed task",
                assignee_id=20,
                status=TaskStatus.DONE,
                due_at=now,
            ),
        ]
        self.provider.opportunities.get_detail.return_value = opportunity

        context = self.provider.get(30)

        self.assertEqual(context.opportunity_id, 30)
        self.assertEqual(context.company_name, "Customer")
        self.assertEqual(context.owner_name, "Owner")
        self.assertEqual(context.recent_activities[0].summary, "Recent demo")
        self.assertEqual(context.open_tasks[0].title, "First task")
        self.assertEqual(len(context.recent_activities), 1)
        self.assertEqual(len(context.open_tasks), 1)

    def test_missing_opportunity_raises_domain_error(self):
        self.provider.opportunities.get_detail.return_value = None

        with self.assertRaises(ResourceNotFoundError):
            self.provider.get(30)


class DealRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.context = CRMContext(
            opportunity_id=30,
            opportunity_name="Deal",
            company_id=10,
            company_name="Customer",
            owner_id=20,
            owner_name="Owner",
            amount=Decimal("12000.00"),
            stage=OpportunityStage.QUALIFIED,
            probability=45,
            expected_close_date=None,
            recent_activities=(),
            open_tasks=(),
        )
        self.analysis = DealAnalysis(
            summary="商机仍需确认需求",
            health="at_risk",
            win_probability=40,
            strengths=["客户已完成初步沟通"],
            risks=["没有近期互动"],
            reasoning="现有信息不足以支持更高概率。",
        )
        self.action = NextAction(
            title="确认客户需求",
            description="与客户安排一次需求确认会议。",
            rationale="补齐关键信息后才能推进商机。",
            priority="high",
            due_in_days=2,
            suggested_owner_id=20,
        )

    def test_runtime_executes_the_fixed_flow_and_returns_typed_result(self):
        calls: list[str] = []

        def load_context(opportunity_id: int) -> CRMContext:
            calls.append(f"context:{opportunity_id}")
            return self.context

        def analyze(values: dict[str, str]) -> DealAnalysis:
            calls.append("analysis")
            self.assertIn('"opportunity_id":30', values["crm_context"])
            return self.analysis

        def recommend(values: dict[str, str]) -> NextAction:
            calls.append("action")
            self.assertIn('"health":"at_risk"', values["deal_analysis"])
            return self.action

        runtime = DealRuntime(
            context_loader=load_context,
            deal_analysis_chain=RunnableLambda(analyze),
            next_action_chain=RunnableLambda(recommend),
        )

        result = runtime.run(30)

        self.assertEqual(calls, ["context:30", "analysis", "action"])
        self.assertIs(result.crm_context, self.context)
        self.assertIs(result.deal_analysis, self.analysis)
        self.assertIs(result.next_action, self.action)

    def test_runtime_rejects_invalid_id_before_loading_context(self):
        loader = MagicMock()
        runtime = DealRuntime(
            context_loader=loader,
            deal_analysis_chain=RunnableLambda(lambda _: self.analysis),
            next_action_chain=RunnableLambda(lambda _: self.action),
        )

        with self.assertRaises(ValueError):
            runtime.run(0)
        loader.assert_not_called()

    def test_initialize_runtime_binds_both_structured_models(self):
        model = MagicMock()
        model.with_structured_output.side_effect = [
            RunnableLambda(lambda _: self.analysis),
            RunnableLambda(lambda _: self.action),
        ]

        runtime = initialize_runtime(MagicMock(spec=Session), model=model)
        runtime.context_loader = lambda _: self.context

        result = runtime.run(30)

        self.assertIs(result.deal_analysis, self.analysis)
        self.assertIs(result.next_action, self.action)
        self.assertEqual(
            [call.args[0] for call in model.with_structured_output.call_args_list],
            [DealAnalysis, NextAction],
        )

    def test_deepseek_model_is_created_lazily_from_settings(self):
        with self.assertRaisesRegex(RuntimeError, "DEEPSEEK_API_KEY"):
            create_deepseek_model(Settings(_env_file=None))

        model = create_deepseek_model(
            Settings(
                deepseek_api_key=SecretStr("test-secret"),
                deepseek_model="deepseek-reasoner",
                deepseek_base_url="https://deepseek.example.test",
                deepseek_temperature=0.2,
                _env_file=None,
            )
        )
        self.assertEqual(model.model_name, "deepseek-reasoner")
        self.assertEqual(model.openai_api_base, "https://deepseek.example.test")
        self.assertEqual(model.temperature, 0.2)


if __name__ == "__main__":
    unittest.main()
