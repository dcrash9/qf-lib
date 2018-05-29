import datetime
from typing import Any, Tuple

import pandas

from qf_lib.plotting.decorators.chart_decorator import ChartDecorator
from qf_lib.plotting.decorators.simple_legend_item import SimpleLegendItem


class PointEmphasisDecorator(ChartDecorator, SimpleLegendItem):
    def __init__(self, series_data_element, coordinates: Tuple[Any, Any], color: str=None, decimal_points: int=2,
                 label_format='  {1:g}', key=None, use_secondary_axes: bool=False, move_point=True, font_size=15):
        """
        Creates a new marker for `series_data_element` for `x=series_index`. For a timeseries, you can specify
        the time that you wish to be emphasised.

        Parameters
        ----------
        series_data_element: DataElementDecorator
            The DataElementDecorator which should be decorated with an emphasised point.
        coordinates
            The x and y coordinate of the point that should be emphasised. The x and y coordinates should be expressed
            in data coordinates (e.g. the x coordinate should be a date if x-axis contains dates).
        color: str, optional
            color of the marker; by default it will be the same as the decorated line
        decimal_points: int, optional
            number of decimal points that should be shown in the point's label
        label_format: str, optional
            A format string specifying how the label should be displayed. Takes two parameters: the index and value.
        key: str, optional
            see: ChartDecorator.__init__#key
        use_secondary_axes
            determines whether this PointEmphasis belongs on the secondary axis.
        """
        ChartDecorator.__init__(self, key)
        SimpleLegendItem.__init__(self)

        assert isinstance(series_data_element.data, pandas.Series)

        assert not pandas.isnull(coordinates[0])
        assert not pandas.isnull(coordinates[1])

        self._series_data_element = series_data_element
        self._series_point = coordinates
        self._color = color
        self._decimal_points = decimal_points
        self._label_format = label_format
        self._text_pos = None
        self._use_secondary_axes = use_secondary_axes
        self.move_point = move_point
        self.font_size = font_size

    def decorate(self, chart):
        ax = chart.secondary_axes if self._use_secondary_axes else chart.axes

        decorated_line = self._series_data_element.legend_artist

        if self._color is None:
            self._color = decorated_line.get_color()

        x = self._series_point[0]
        y = self._series_point[1]

        self.legend_artist = ax.plot([x], [y], 'o', color=self._color)[0]

        # Format label based on specified format string.
        if isinstance(x, datetime.datetime):
            label = self._label_format.format(x, round(y, self._decimal_points))
        else:
            label = self._label_format.format(round(x, self._decimal_points), round(y, self._decimal_points))

        if self.move_point:
            # Calculate where the text should be positioned.
            self._text_pos = self._calculate_text_position(chart, x, y)
            # Draw the text on the graph.
            ax.text(self._text_pos[0], self._text_pos[1], label, size=self.font_size,
                    weight="bold", family="Arial", color=self._color)
        else:
            ax.text(x, y, label, size=self.font_size, weight="bold", family="Arial", color=self._color)

    def _calculate_text_position(self, line_chart, x, y) -> (object, float):
        axes = line_chart.axes
        pos = [x, y]

        # Calculate how much we need to move the label based on the y axis limits.
        movement_constant = (axes.get_ylim()[1] - axes.get_ylim()[0]) / 10

        # Calculate the max distance between two labels that still counts as a collision.
        proximity = (axes.get_ylim()[1] - axes.get_ylim()[0]) / 20

        # Go through each each decorator, to see if any point emphasis decorators overlap this one.
        for key, decorator in line_chart._decorators.items():
            if isinstance(decorator, PointEmphasisDecorator) and decorator._text_pos is not None and key != self.key:
                if abs(pos[1] - decorator._text_pos[1]) < proximity:
                    # If we are overlapping, move the label up.
                    pos[1] += movement_constant

        return pos