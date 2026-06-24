HARD_DISABLED_TABLES: dict[str, set[str]] = {
    "async_request": set(),
    "disabled_tables": set(),
    "alembic_version": set(),
    "usages": set(),
    "consumption_limits": set(),
    "push_subscriptions": set(),
    "notifications": set(),
}
