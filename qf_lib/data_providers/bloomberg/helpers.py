import datetime
import logging

from qf_lib.common.enums.frequency import Frequency
from qf_lib.data_providers.bloomberg.bloomberg_names import *
from qf_lib.data_providers.bloomberg.exceptions import BloombergError


def set_tickers(request, tickers):
    """
    Sets requested tickers in the Bloomberg's request.

    Parameters
    ----------
    request
        request to be sent
    tickers: List[str]
        required tickers

    """
    securities = request.getElement(SECURITIES)
    for ticker in tickers:
        securities.appendValue(ticker)


def set_fields(request, field_names):
    requested_fields = request.getElement(FIELDS)
    for field in field_names:
        requested_fields.appendValue(field)


def convert_to_bloomberg_freq(frequency: Frequency) -> str:
    return frequency.name


def convert_to_bloomberg_date(date: datetime) -> str:
    return date.strftime('%Y%m%d')


def check_event_for_errors(event):
    logger = logging.getLogger(__name__)

    num_of_messages = count_messages(event)
    if num_of_messages != 1:
        error_message = "Number of messages != 1"
        logger.error(error_message)
        raise BloombergError(error_message)

    first_msg = blpapi.event.MessageIterator(event).next()

    if first_msg.asElement().hasElement(RESPONSE_ERROR):
        error_message = "Response error: " + str(first_msg.asElement())
        logger.error(error_message)
        raise BloombergError(error_message)


def extract_security_data(event):
    first_msg = blpapi.event.MessageIterator(event).next()
    return first_msg.getElement(SECURITY_DATA)


def count_messages(event):
    num_of_messages = 0
    for _ in event:
        num_of_messages += 1

    return num_of_messages


def get_response_events(session):
    response_events = []
    while True:
        event = session.nextEvent()
        if event.eventType() == blpapi.event.Event.PARTIAL_RESPONSE:
            response_events.append(event)
        elif event.eventType() == blpapi.event.Event.RESPONSE:
            response_events.append(event)
            break

    return response_events


def check_security_data_for_errors(security_data):
    logger = logging.getLogger(__name__)
    if security_data.hasElement(FIELD_EXCEPTIONS):
        field_exceptions = security_data.getElement(FIELD_EXCEPTIONS)
        if field_exceptions.numValues() > 0:
            error_message = "Response contains field exceptions:\n" + str(security_data)
            logger.error(error_message)
            raise BloombergError(error_message)

    if security_data.hasElement(SECURITY_ERROR):
        error_message = "Response contains security error:\n" + str(security_data)
        logger.error(error_message)
        raise BloombergError(error_message)