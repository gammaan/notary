"""Workflow helpers for matter step-by-step UI."""

from operations.models import Matter
from operations.transaction_rules import finance_step_done


def matter_workflow_steps(matter):
    setup_done = bool(matter.title and matter.client_id and matter.service_type_id)
    documents_done = matter.documents.exists()
    finance_done = finance_step_done(matter)
    complete_done = matter.status == Matter.Status.COMPLETED

    steps = [
        {
            "number": 1,
            "slug": "setup",
            "label": "Setup",
            "description": "Client, service, and matter details",
            "done": setup_done,
            "url_name": "staff:matter_edit",
        },
        {
            "number": 2,
            "slug": "documents",
            "label": "Documents",
            "description": "Upload and track documents",
            "done": documents_done,
            "url_name": "staff:matter_documents",
        },
        {
            "number": 3,
            "slug": "finances",
            "label": "Finances",
            "description": "Record fees and payments",
            "done": finance_done,
            "url_name": "staff:matter_finances",
        },
        {
            "number": 4,
            "slug": "complete",
            "label": "Complete",
            "description": "Review and close the matter",
            "done": complete_done,
            "url_name": "staff:matter_complete",
        },
    ]

    current = 1
    for step in steps:
        if not step["done"]:
            current = step["number"]
            break
    else:
        current = 4 if complete_done else 3

    return steps, current


WIZARD_SESSION_KEY = "matter_wizard"


def get_wizard_data(session):
    return session.get(WIZARD_SESSION_KEY, {})


def set_wizard_data(session, data):
    session[WIZARD_SESSION_KEY] = data
    session.modified = True


def clear_wizard_data(session):
    session.pop(WIZARD_SESSION_KEY, None)
    session.modified = True
