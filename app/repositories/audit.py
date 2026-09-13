class AuditRepository:
    async def create(self, session, event):
        session.add(event)
        await session.commit()
        await session.refresh(event)
        return event
