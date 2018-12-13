from abc import abstractmethod, ABCMeta

import talib

from qf_lib.backtesting.alpha_model.exposure_enum import Exposure
from qf_lib.backtesting.alpha_model.signal import Signal
from qf_lib.backtesting.data_handler.data_handler import DataHandler
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import Ticker


class AlphaModel(object, metaclass=ABCMeta):

    def __init__(self, risk_estimation_factor: float, data_handler: DataHandler):
        self.risk_estimation_factor = risk_estimation_factor
        self.data_handler = data_handler

    def get_signal(self, ticker: Ticker, current_exposure: Exposure) -> Signal:
        """
        Returns the Signal calculated for a specific AlphaModel and a set of data for a specified Ticker

        Parameters
        ----------
        ticker
            A ticker of an asset for which the Signal should be generated
        current_exposure
            The actual exposure, based on which the AlphaModel should return its Signal. Can be different from previous
            Signal suggestions, but it should correspond with the current trading position

        Returns
        -------
            Signal being the suggestion for the next trading period
        """
        suggested_exposure = self.calculate_exposure(ticker, current_exposure)
        fraction_at_risk = self.calculate_fraction_at_risk(ticker)

        signal = Signal(ticker, suggested_exposure, fraction_at_risk, alpha_model=self)
        return signal

    @abstractmethod
    def calculate_exposure(self, ticker: Ticker, current_exposure: Exposure) -> Exposure:
        """
        Returns the expected Exposure, which is the key part of a generated Signal. Exposure suggests the trend
        direction for managing the trading position.
        Uses DataHandler and num_of_rows_needed both passed when the AlphaModel (child) is initialized - all required
        data is provided in the child class.

        Parameters
        ----------
        ticker
            Ticker for which suggested signal exposure is calculated.
        current_exposure
            The actual exposure, based on which the AlphaModel should return its Signal. Can be different from previous
            Signal suggestions, but it should correspond with the current trading position

        """
        pass

    def calculate_fraction_at_risk(self, ticker: Ticker) -> float:
        """
        Returns the float value which determines the risk factor for an AlphaModel and a specified Ticker,
        may be used to calculate the position size.

        For example: Value of 0.02 means that we should place a Stop Loss 2% below the latest available
        price of the instrument. This value should always be positive

        Parameters
        ----------
        ticker
            Ticker for which the calculation should be made
        risk_estimation_factor
            float value which estimates the risk level of the specific AlphaModel
        data_handler
            DataHandler which provides the data for the ticker

        Returns
        -------
            percentage_at_risk value for an AlphaModel and a Ticker, calculated as Normalized Average True Range
            multiplied by the risk_estimation_factor, being a property of each AlphaModel:
            fraction_at_risk = ATR / last_close * risk_estimation_factor

        """
        fields = [PriceField.High, PriceField.Low, PriceField.Close]
        time_period = 20

        num_of_bars_needed = time_period + 1
        prices_df = self.data_handler.historical_price(ticker, fields, num_of_bars_needed)

        high = prices_df[PriceField.High]
        low = prices_df[PriceField.Low]
        close = prices_df[PriceField.Close]

        fraction_at_risk = talib.ATR(high, low, close, time_period) / close[-1] * self.risk_estimation_factor

        return fraction_at_risk[-1]