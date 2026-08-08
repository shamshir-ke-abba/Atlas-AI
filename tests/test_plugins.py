from plugins.system.time import TimePlugin
from plugins.system.calculator import CalculatorPlugin
from core.plugin_manager import PluginManager
from core.intent import IntentRouter
from ai.planner import Planner


def test_planner_time():

    manager = PluginManager()
    router = IntentRouter(manager.plugins)
    planner = Planner(router)

    plan = planner.plan(
        "What time is it?"
    )

    assert plan.action == Planner.TOOL
    assert plan.plugin.name == "time"
    assert plan.arguments == ""


def test_planner_calculator():

    manager = PluginManager()
    router = IntentRouter(manager.plugins)
    planner = Planner(router)

    plan = planner.plan(
        "calculate 25 * 37"
    )

    assert plan.action == Planner.TOOL
    assert plan.plugin.name == "calculator"
    assert plan.arguments == "25 * 37"

def test_planner_direct():
    manager = PluginManager()
    router = IntentRouter(manager.plugins)
    planner = Planner(router)

    plan = planner.plan(
        "Explain gravity"
    )

    assert plan.action == Planner.DIRECT
    assert plan.plugin is None

def test_time_plugin():
    plugin = TimePlugin()

    assert plugin.can_handle("What time is it?")
    assert plugin.can_handle("what's the time")
    assert plugin.can_handle("time")

    result = plugin.run()

    assert result
    assert isinstance(result, str)


def test_calculator_plugin():
    plugin = CalculatorPlugin()

    assert plugin.can_handle("calculate 25 * 37")

    result = plugin.run(
        expression="25 * 37"
    )

    assert result == "925"


def test_router_time():
    manager = PluginManager()
    router = IntentRouter(manager.plugins)

    plugin = router.match(
        "What time is it?"
    )

    assert plugin is not None
    assert plugin.name == "time"


def test_router_calculator():
    manager = PluginManager()
    router = IntentRouter(manager.plugins)

    plugin = router.match(
        "calculate 25 * 37"
    )

    assert plugin is not None
    assert plugin.name == "calculator"
