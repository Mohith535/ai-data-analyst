"""
tests/test_conversation_memory.py — Unit Tests for Conversation Memory & Design Tokens (Phase 5)
"""

import sys
import os
import pytest
from unittest.mock import MagicMock, patch

# Add parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import ai_chat
from ui.theme import Toast, BG_CANVAS, ACCENT_PRIMARY


class TestConversationMemory:
    """Tests multi-turn conversation memory injection into the LLM context."""

    def test_generate_sql_injects_conversation_history(self):
        schema = [{'column': 'product', 'type': 'TEXT'}, {'column': 'region', 'type': 'TEXT'}]
        history = [
            {"question": "Show all sales", "sql": "SELECT * FROM `sales_data` LIMIT 25"},
            {"question": "Filter to North region", "sql": "SELECT * FROM `sales_data` WHERE `region` = 'North' LIMIT 25"}
        ]

        mock_client = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = "SELECT * FROM `sales_data` WHERE `region` = 'North' AND `category` = 'Electronics' LIMIT 25"
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response

        with patch("ai_chat.get_groq_client", return_value=mock_client), \
             patch("ai_chat.get_available_model", return_value="test-model"):
            
            sql, err, is_fallback = ai_chat.generate_sql(
                table_name="sales_data",
                schema=schema,
                user_question="Filter that to Electronics category",
                conversation_history=history
            )

            assert err is None
            assert is_fallback is False
            assert "Electronics" in sql

            # Inspect the messages sent to the LLM
            call_kwargs = mock_client.chat.completions.create.call_args[1]
            sent_messages = call_kwargs["messages"]

            # Must have system prompt + 2 user/assistant history turns (4 messages) + current user prompt (1) = 6 total
            assert len(sent_messages) == 6
            assert sent_messages[0]["role"] == "system"
            assert sent_messages[1]["role"] == "user"
            assert "Show all sales" in sent_messages[1]["content"]
            assert sent_messages[2]["role"] == "assistant"
            assert "SELECT * FROM `sales_data` LIMIT 25" in sent_messages[2]["content"]
            assert sent_messages[3]["role"] == "user"
            assert "Filter to North region" in sent_messages[3]["content"]
            assert sent_messages[4]["role"] == "assistant"
            assert sent_messages[5]["role"] == "user"
            assert "Filter that to Electronics category" in sent_messages[5]["content"]

    def test_generate_sql_without_history(self):
        schema = [{'column': 'product', 'type': 'TEXT'}]

        mock_client = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = "SELECT `product` FROM `sales_data` LIMIT 25"
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response

        with patch("ai_chat.get_groq_client", return_value=mock_client), \
             patch("ai_chat.get_available_model", return_value="test-model"):
            
            sql, err, is_fallback = ai_chat.generate_sql(
                table_name="sales_data",
                schema=schema,
                user_question="List all products"
            )

            call_kwargs = mock_client.chat.completions.create.call_args[1]
            sent_messages = call_kwargs["messages"]
            # System prompt + current prompt = 2 messages
            assert len(sent_messages) == 2


class TestThemeTokens:
    """Verifies that theme tokens and Toast helper are well-formed."""

    def test_theme_tokens_defined(self):
        assert BG_CANVAS.startswith("#")
        assert ACCENT_PRIMARY.startswith("#")

    def test_toast_class_exists(self):
        assert hasattr(Toast, "show")
