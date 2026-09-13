"""Resumable workflow stage boundary."""


async def run_source_workflow(
    session, source, ingestion_runner, match_runner=None, notify_runner=None
):
    result = {"source_id": source.id, "ingestion": await ingestion_runner(session, source)}
    if match_runner is not None:
        result["matching"] = await match_runner(session, source)
    if notify_runner is not None:
        result["notifications"] = await notify_runner(session, source)
    return result
