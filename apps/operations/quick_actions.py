"""One-click status changes for staff workflow."""

from operations.models import Document, Transaction

DOCUMENT_STATUS_FLOW = (
    Document.Status.PENDING,
    Document.Status.RECEIVED,
    Document.Status.VERIFIED,
    Document.Status.NOTARIZED,
)


def next_document_status(current):
    try:
        idx = DOCUMENT_STATUS_FLOW.index(current)
    except ValueError:
        return None
    if idx >= len(DOCUMENT_STATUS_FLOW) - 1:
        return None
    return DOCUMENT_STATUS_FLOW[idx + 1]


def document_can_approve(document):
    return next_document_status(document.status) is not None
