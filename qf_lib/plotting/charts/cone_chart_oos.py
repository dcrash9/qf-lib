import matplotlib as mpl
from itertools import cycle
from typing import Sequence, List

from qf_lib.common.utils.returns.analytical_cone import AnalyticalCone
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.plotting.charts.chart import Chart
from qf_lib.plotting.decorators.data_element_decorator import DataElementDecorator


class ConeChartOOS(Chart):
    """
    While using a simple cone (e.g. LineChart with Cone decorator) the results of the evaluation may be very different
    depending on the live_start_date. To be immune to this, ConeChart plots only the ends of simple cones which start
    at 1 periods, 2 periods, ..., n periods before the end of the backtested series. The period length depends
    on the frequency of the data provided for the chart. If it has daily frequency, then the length of one period
    will be 1 day.
    """

    def __init__(self, oos_series: QFSeries, is_mean_return: float, is_sigma: float, cone_opacity: float=0.3,
                 cone_stds: Sequence[float]=(1.0, 2.0)):
        """
        Parameters
        ----------
        oos_series
            data to be plotted using ConeChartOOS - only the Out of sample data
        is_mean_return:
            mean daily return of the strategy In Sample
        is_sigma:
            std of daily returns of the strategy In Sample
        cone_opacity
            opacity of the cone
        cone_stds
            list/tuple of different standard deviations for which cones should be drawn
        """
        super().__init__()
        self.assert_is_qfseries(oos_series)
        self.oos_series = oos_series

        self.is_mean_return = is_mean_return
        self.is_sigma = is_sigma

        self.cone_opacity = cone_opacity
        self.cone_stds = cone_stds

    def plot(self, figsize=None):
        self._setup_axes_if_necessary(figsize)

        cone = AnalyticalCone()
        cone_data_frame = cone.calculate_aggregated_cone_oos_only(
            self.oos_series, self.is_mean_return, self.is_sigma, 0)

        strategy_tms = cone_data_frame['Strategy']
        mean_tms = cone_data_frame['Expectation']

        ax = self.axes
        ax.plot(strategy_tms)
        ax.plot(mean_tms)

        cone_colors = cycle(Chart.get_axes_colors()[2:4])

        # fill areas for every standard deviation
        for cone_std in self.cone_stds:
            upper_df = cone.calculate_aggregated_cone_oos_only(
                self.oos_series, self.is_mean_return, self.is_sigma, cone_std)
            lower_df = cone.calculate_aggregated_cone_oos_only(
                self.oos_series, self.is_mean_return, self.is_sigma, -cone_std)

            upper_bound = upper_df['Expectation']
            lower_bound = lower_df['Expectation']
            ax.fill_between(cone_data_frame.index, lower_bound, upper_bound,
                            color=next(cone_colors), alpha=self.cone_opacity)

        ax.set_xlabel('Days in the past')
        ax.set_ylabel('Current valuation')
        ax.set_title('Performance vs. Expectation')
        ax.set_xlim(0, self.oos_series.size)

        # add text box with average expectation over 20 days and overall horizon
        one_sigma_df = cone.calculate_aggregated_cone_oos_only(self.oos_series, self.is_mean_return, self.is_sigma, 1)
        one_sigma_tms = one_sigma_df['Expectation']
        valuation_tms = (strategy_tms-1) / (one_sigma_tms-1)  # type: QFSeries
        valuation_total = valuation_tms.mean()
        total_days = valuation_tms.size - 1

        if valuation_tms.size > 20:
            valuation20d = valuation_tms.head(20).mean()
            textstr = 'Valuation 20D = {:.2f}\nValuation {}D = {:.2f}'.format(valuation20d, total_days, valuation_total)
        else:
            textstr = 'Valuation {}D = {:.2f}'.format(total_days, valuation_total)

        props = dict(boxstyle='square', facecolor='white', alpha=0.5, edgecolor='grey')
        font_size = mpl.rcParams['legend.fontsize']
        self.axes.text(0.05, 0.95, textstr, transform=self.axes.transAxes, bbox=props,
                       verticalalignment='top', fontsize=font_size)

    def apply_data_element_decorators(self, data_element_decorators: List["DataElementDecorator"]):
        pass
