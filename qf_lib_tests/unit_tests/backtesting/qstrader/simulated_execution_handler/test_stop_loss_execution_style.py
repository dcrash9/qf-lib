from datetime import datetime
from unittest import TestCase

import pandas as pd
from mockito import mock, verify, spy, when, verifyZeroInteractions

from qf_lib.backtesting.contract.contract import Contract
from qf_lib.backtesting.contract_to_ticker_conversion.bloomberg_mapper import DummyBloombergContractTickerMapper
from qf_lib.backtesting.execution_handler.simulated.commission_models.fixed_commission_model import FixedCommissionModel
from qf_lib.backtesting.execution_handler.simulated.simulated_execution_handler import SimulatedExecutionHandler
from qf_lib.backtesting.monitoring.abstract_monitor import AbstractMonitor
from qf_lib.backtesting.order.execution_style import StopOrder
from qf_lib.backtesting.order.order import Order
from qf_lib.backtesting.order.time_in_force import TimeInForce
from qf_lib.backtesting.transaction import Transaction
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import BloombergTicker
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.common.utils.dateutils.timer import SettableTimer
from qf_lib.testing_tools.containers_comparison import assert_lists_equal


class _MonitorMock(AbstractMonitor):
    def __init__(self):
        # noinspection PyTypeChecker
        super().__init__(None)
        self.transactions = []

    def real_time_update(self, timestamp: datetime):
        raise NotImplementedError

    def end_of_day_update(self, timestamp: datetime):
        raise NotImplementedError

    def end_of_trading_update(self, timestamp: datetime):
        raise NotImplementedError

    def record_transaction(self, transaction: Transaction):
        self.transactions.append(transaction)

    def get_recorded_transactions(self):
        return list(self.transactions)


class TestStopLossExecutionStyle(TestCase):
    MSFT_TICKER_STR = "MSFT US Equity"

    def setUp(self):
        self.start_date = str_to_date("2018-02-04")
        self.msft_contract = Contract(self.MSFT_TICKER_STR, security_type='SEK', exchange='TEST')
        self.msft_ticker = BloombergTicker(self.MSFT_TICKER_STR)

        self.contracts_to_tickers_mapper = DummyBloombergContractTickerMapper()
        timer = SettableTimer(initial_time=self.start_date)

        self.data_handler = mock(strict=True)

        self.scheduler = mock()

        self.commission_model = FixedCommissionModel(commission=0.0)
        self.monitor = _MonitorMock()
        self.spied_monitor = spy(self.monitor)
        self.portfolio = mock()

        self.exec_hanlder = SimulatedExecutionHandler(self.data_handler, timer, self.scheduler, self.spied_monitor,
                                                      self.commission_model, self.contracts_to_tickers_mapper,
                                                      self.portfolio)

        self._set_current_msft_price(100.0)
        self.stop_loss_order = Order(self.msft_contract, quantity=-1, execution_style=StopOrder(95.00),
                                     time_in_force=TimeInForce.DAY)
        self.exec_hanlder.accept_orders([self.stop_loss_order])

    def test_no_market_orders_executed_because_non_were_made(self):
        self.exec_hanlder.on_market_open(...)
        verifyZeroInteractions(self.portfolio, self.spied_monitor)

        actual_orders = self.exec_hanlder.get_open_orders()
        expected_orders = [self.stop_loss_order]
        assert_lists_equal(expected_orders, actual_orders)

    def test_order_not_executed_when_stop_price_not_hit(self):
        self._set_bar_for_today(open=105.0, high=110.0, low=100.0, close=105.0, volume=100000000.0)
        self.exec_hanlder.on_market_close(...)
        verifyZeroInteractions(self.portfolio, self.spied_monitor)

        actual_orders = self.exec_hanlder.get_open_orders()
        exoected_orders = [self.stop_loss_order]
        assert_lists_equal(exoected_orders, actual_orders)

    def test_order_not_executed_when_bar_for_today_is_incomplete(self):
        self._set_bar_for_today(open=None, high=110.0, low=100.0, close=105.0, volume=100000000.0)
        self.exec_hanlder.on_market_close(...)
        verifyZeroInteractions(self.portfolio, self.spied_monitor)

        actual_orders = self.exec_hanlder.get_open_orders()
        exoected_orders = [self.stop_loss_order]
        assert_lists_equal(exoected_orders, actual_orders)

    def test_order_executed_when_stop_price_hit(self):
        self._set_bar_for_today(open=100.0, high=110.0, low=94.0, close=105.0, volume=100000000.0)
        self.exec_hanlder.on_market_close(...)

        assert_lists_equal([], self.exec_hanlder.get_open_orders())
        verify(self.spied_monitor, times=1).record_transaction(...)
        verify(self.portfolio, times=1).transact_transaction(...)

        self.assertEquals(1, len(self.monitor.transactions))
        actual_transaction = self.monitor.transactions[0]

        self.assertEquals(self.msft_contract, actual_transaction.contract)
        self.assertEquals(-1, actual_transaction.quantity)
        self.assertEquals(self.stop_loss_order.execution_style.stop_price, actual_transaction.price)
        self.assertEquals(0.0, actual_transaction.commission)

    def _set_current_msft_price(self, price):
        when(self.data_handler).get_last_available_price([self.msft_ticker]).thenReturn(
            pd.Series(data=[price], index=pd.DatetimeIndex([self.start_date]))
        )

    def _set_bar_for_today(self, open, high, low, close, volume):
        when(self.data_handler).get_bar_for_today([self.msft_ticker]).thenReturn(
            pd.DataFrame(
                index=pd.Index([self.msft_ticker]), columns=PriceField.ohlcv(),
                data=[[open, high, low, close, volume]]
            )
        )