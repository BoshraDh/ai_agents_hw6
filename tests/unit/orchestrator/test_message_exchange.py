from cop_thief_mcp.orchestrator.message_exchange import MessageExchange


def test_defaults_to_empty_messages():
    exchange = MessageExchange()

    assert exchange.cop_message == ""
    assert exchange.thief_message == ""


def test_fields_are_independently_mutable():
    exchange = MessageExchange()

    exchange.cop_message = "hello"

    assert exchange.cop_message == "hello"
    assert exchange.thief_message == ""
