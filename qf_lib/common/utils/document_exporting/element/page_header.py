import datetime

from qf_lib.common.enums.grid_proportion import GridProportion
from qf_lib.common.utils.dateutils.date_format import DateFormat
from qf_lib.common.utils.dateutils.date_to_string import date_to_str
from qf_lib.common.utils.document_exporting import templates
from qf_lib.common.utils.document_exporting.document import Document
from qf_lib.common.utils.document_exporting.element import Element


class PageHeaderElement(Element):
    """
    A stylised header element, consists of a major title (on left and right), subtitle and logo (loaded from specified
    path).
    """

    def __init__(self, logo_path: str=None, major_line: str = "", minor_line: str = "", date: datetime = None,
                 grid_proportion=GridProportion.Eight):
        """
        Constructs a new Header element.

        Parameters
        ----------
        title - The header title.
        logo - A filepath to the logo to display on the left of the header.
        """
        super().__init__(grid_proportion)
        self.logo_path = logo_path

        self.major_line = major_line
        self.minor_line = minor_line

        if date is None:
            date = datetime.date.today()

        self.date = date_to_str(date, DateFormat.LONG_DATE)

    def generate_html(self, document: Document) -> str:
        """
        Generates the HTML that represents the underlying header.
        """
        env = templates.environment

        template = env.get_template("page_header.html")
        return template.render(logo_path=self.logo_path,
                               major_line=self.major_line,
                               minor_line=self.minor_line,
                               date=self.date)
