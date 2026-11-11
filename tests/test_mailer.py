"""Tests du mailer SMTP (sans réseau)."""

from worker.mailer import build_message


def test_build_message_has_text_and_html_alternatives():
    message = build_message(
        sender="alertes@example.com",
        recipient="surfeur@example.com",
        subject="🏄 Test",
        text_body="Texte",
        html_body="<p>HTML</p>",
    )
    assert message["From"] == "alertes@example.com"
    assert message["To"] == "surfeur@example.com"
    assert message["Subject"] == "🏄 Test"
    body = message.get_body(preferencelist=("plain",))
    html = message.get_body(preferencelist=("html",))
    assert body is not None and body.get_content() == "Texte\n"
    assert html is not None and html.get_content() == "<p>HTML</p>\n"
