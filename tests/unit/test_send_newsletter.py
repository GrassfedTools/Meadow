import pytest

from handlers.handler import send_newsletter


def test_send_newsletter_happy_path(initialise):
    event = {
        "newsletter_slug": "20210421",
        "newsletter_subject": "Meadow Testing Newsletter",
    }
    response = send_newsletter(event, None)
    assert response == 0


def test_send_newsletter_cannot_load_slug_details_from_event(initialise):
    with pytest.raises(KeyError, match="newsletter_slug"):
        send_newsletter({"newsletter_subject": "Meadow Testing Newsletter"}, None)


def test_send_newsletter_cannot_load_subject_details_from_event(initialise):
    with pytest.raises(KeyError, match="newsletter_subject"):
        send_newsletter({"newsletter_slug": "20210421"}, None)


def test_send_newsletter_slug_is_empty(initialise):
    with pytest.raises(
        ValueError, match="Newsletter slug and newsletter subject cannot be empty."
    ):
        event = {
            "newsletter_slug": " ",
            "newsletter_subject": "Meadow Testing Newsletter",
        }
        send_newsletter(event, None)


def test_send_newsletter_subject_is_empty(initialise):
    with pytest.raises(
        ValueError, match="Newsletter slug and newsletter subject cannot be empty."
    ):
        event = {
            "newsletter_slug": "123456",
            "newsletter_subject": " ",
        }
        send_newsletter(event, None)


def test_send_newsletter_template_separate_is_incorrect(
    initialiseTemplateWithIncorrectSeperator,
):
    with pytest.raises(Exception, match="Template does not contain correct separator"):
        event = {
            "newsletter_slug": "20210421",
            "newsletter_subject": "Meadow Testing Newsletter",
        }
        send_newsletter(event, None)


def test_send_newsletter_template_body_is_empty(initialiseTemplateWithEmptyBody):
    with pytest.raises(Exception, match="Template does not contain correct separator"):
        event = {
            "newsletter_slug": "20210421",
            "newsletter_subject": "Meadow Testing Newsletter",
        }
        send_newsletter(event, None)
