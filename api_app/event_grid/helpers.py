from azure.eventgrid import EventGridEvent
from providers.factory import get_event_publisher


async def publish_event(event: EventGridEvent, topic_endpoint: str):
    """
    Publish an event to Event Grid using the provider factory.

    :param event: The Event Grid event to publish
    :param topic_endpoint: The Event Grid topic endpoint URL
    """
    event_publisher = get_event_publisher()
    await event_publisher.publish(
        topic_endpoint=topic_endpoint,
        event_type=event.event_type,
        subject=event.subject,
        data=event.data,
        event_id=event.id
    )
