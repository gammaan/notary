from django.db.models import Q
from django.utils.dateparse import parse_date

from operations.models import Client, Document, Matter, Transaction


def filter_clients(queryset, params):
    q = params.get("q", "").strip()
    if q:
        queryset = queryset.filter(
            Q(full_name__icontains=q)
            | Q(email__icontains=q)
            | Q(phone__icontains=q)
            | Q(id_number__icontains=q)
        )

    active = params.get("active", "").strip()
    if active == "yes":
        queryset = queryset.filter(is_active=True)
    elif active == "no":
        queryset = queryset.filter(is_active=False)

    has_matters = params.get("has_matters", "").strip()
    if has_matters == "yes":
        queryset = queryset.filter(matters__isnull=False).distinct()
    elif has_matters == "no":
        queryset = queryset.filter(matters__isnull=True)

    date_from = parse_date(params.get("date_from", "") or "")
    if date_from:
        queryset = queryset.filter(created_at__date__gte=date_from)

    date_to = parse_date(params.get("date_to", "") or "")
    if date_to:
        queryset = queryset.filter(created_at__date__lte=date_to)

    return queryset


def filter_matters(queryset, params):
    q = params.get("q", "").strip()
    if q:
        queryset = queryset.filter(
            Q(reference_number__icontains=q)
            | Q(title__icontains=q)
            | Q(client__full_name__icontains=q)
            | Q(service_type__name__icontains=q)
        )

    status = params.get("status", "").strip()
    if status in Matter.Status.values:
        queryset = queryset.filter(status=status)

    service = params.get("service", "").strip()
    if service.isdigit():
        queryset = queryset.filter(service_type_id=int(service))

    client = params.get("client", "").strip()
    if client:
        queryset = queryset.filter(
            Q(client__full_name__icontains=client)
            | Q(client__email__icontains=client)
        )

    date_from = parse_date(params.get("date_from", "") or "")
    if date_from:
        queryset = queryset.filter(created_at__date__gte=date_from)

    date_to = parse_date(params.get("date_to", "") or "")
    if date_to:
        queryset = queryset.filter(created_at__date__lte=date_to)

    scheduled_from = parse_date(params.get("scheduled_from", "") or "")
    if scheduled_from:
        queryset = queryset.filter(scheduled_at__date__gte=scheduled_from)

    scheduled_to = parse_date(params.get("scheduled_to", "") or "")
    if scheduled_to:
        queryset = queryset.filter(scheduled_at__date__lte=scheduled_to)

    return queryset


def filter_documents(queryset, params):
    q = params.get("q", "").strip()
    if q:
        queryset = queryset.filter(
            Q(title__icontains=q)
            | Q(document_type__icontains=q)
            | Q(matter__reference_number__icontains=q)
            | Q(matter__title__icontains=q)
            | Q(matter__client__full_name__icontains=q)
        )

    status = params.get("status", "").strip()
    if status in Document.Status.values:
        queryset = queryset.filter(status=status)

    matter = params.get("matter", "").strip()
    if matter:
        queryset = queryset.filter(matter__reference_number__icontains=matter)

    date_from = parse_date(params.get("date_from", "") or "")
    if date_from:
        queryset = queryset.filter(created_at__date__gte=date_from)

    date_to = parse_date(params.get("date_to", "") or "")
    if date_to:
        queryset = queryset.filter(created_at__date__lte=date_to)

    return queryset


def filter_transactions(queryset, params):
    q = params.get("q", "").strip()
    if q:
        queryset = queryset.filter(
            Q(description__icontains=q)
            | Q(matter__reference_number__icontains=q)
            | Q(matter__title__icontains=q)
            | Q(matter__client__full_name__icontains=q)
            | Q(category__icontains=q)
        )

    source = params.get("source", "").strip()
    if source == "matter":
        queryset = queryset.filter(matter__isnull=False)
    elif source == "general":
        queryset = queryset.filter(matter__isnull=True)

    category = params.get("category", "").strip()
    if category in Transaction.Category.values:
        queryset = queryset.filter(category=category)

    status = params.get("status", "").strip()
    if status in Transaction.Status.values:
        queryset = queryset.filter(status=status)

    txn_type = params.get("type", "").strip()
    if txn_type in Transaction.Type.values:
        queryset = queryset.filter(transaction_type=txn_type)

    matter = params.get("matter", "").strip()
    if matter:
        queryset = queryset.filter(matter__reference_number__icontains=matter)

    payment_method = params.get("payment_method", "").strip()
    if payment_method in Transaction.PaymentMethod.values:
        queryset = queryset.filter(payment_method=payment_method)

    date_from = parse_date(params.get("date_from", "") or "")
    if date_from:
        queryset = queryset.filter(transaction_date__gte=date_from)

    date_to = parse_date(params.get("date_to", "") or "")
    if date_to:
        queryset = queryset.filter(transaction_date__lte=date_to)

    return queryset
