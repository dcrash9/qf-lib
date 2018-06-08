from qf_lib.backtesting.qstrader.events.empty_queue_event.empty_queue_event_notifier import EmptyQueueEventNotifier
from qf_lib.backtesting.qstrader.events.end_trading_event.end_trading_event_notifier import EndTradingEventNotifier
from qf_lib.backtesting.qstrader.events.event_base import AllEventNotifier
from qf_lib.backtesting.qstrader.events.signal_event.signal_event_notifier import SignalEventNotifier
from qf_lib.backtesting.qstrader.events.time_event.scheduler import Scheduler
from qf_lib.common.utils.dateutils.timer import Timer


class Notifiers(object):
    """
    Convenience class grouping all notifiers together.
    """

    def __init__(self, timer: Timer):
        """
        When an Event of certain type is being dispatched by EventManager then what EventManger
        does is it finds the EventNotifier which corresponds to this type of Event. Then the EventNotifier
        notifies all its EventListeners about an Event which occurred. However there might be some EventListeners
        which are listening to the more general type of Event (super-type of the event) and they should also be
        notified.

        That's why the EventNotifier will also call an EventNotifier specific to a more general type of Events
        which will then notify all its EventListeners. The chain of calls on different
        EventNotifiers goes on until the AllEventNotifier is called. That one corresponds to the most general
        type of Events (the Event). When EventListeners subscribed to the Event are notified in the end
        the process of notifications is over.

        Because of the fact that each EventNotifier also calls the EventNotifier for Events of more general type,
        each EventNotifier must have a reference to this "more general" EventNotifier. Most of Events inherit
        directly from the Event type. That's why most of notifiers will need a reference to AllEventNotifier.
        """
        self.all_event_notifier = AllEventNotifier()
        self.empty_queue_event_notifier = EmptyQueueEventNotifier(self.all_event_notifier)
        self.end_trading_event_notifier = EndTradingEventNotifier(self.all_event_notifier)
        self.signal_event_notifier = SignalEventNotifier(self.all_event_notifier)
        self.scheduler = Scheduler(timer)
