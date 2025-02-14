import pandas as pd

from yfinance import utils
from yfinance.data import YfData
from yfinance.exceptions import YFNotImplementedError
import dateutil


class Analysis:
    _SCRAPE_URL_ = 'https://finance.yahoo.com/quote'

    def __init__(self, data: YfData, symbol: str, proxy=None):
        self._data = data
        self._symbol = symbol
        self.proxy = proxy

        self._earnings_trend = None
        self._analyst_trend_details = None
        self._analyst_growth_estimates = None
        self._rev_est = None
        self._eps_est = None
        self._eps_rev = None
        self._already_scraped = False

    @property
    def earnings_trend(self) -> pd.DataFrame:
        if self._earnings_trend is None and not self._already_scraped:
            self._scrape(self.proxy)
        return self._earnings_trend

    @property
    def analyst_trend_details(self) -> pd.DataFrame:
        if self._analyst_trend_details is None and not self._already_scraped:
            self._scrape(self.proxy)
        return self._analyst_trend_details

    @property
    def analyst_growth_estimates(self) -> pd.DataFrame:
        if self._analyst_growth_estimates is None and not self._already_scraped:
            self._scrape(self.proxy)
        return self._analyst_growth_estimates

    @property
    def rev_est(self) -> pd.DataFrame:
        if self._rev_est is None and not self._already_scraped:
            self._scrape(self.proxy)
        return self._rev_est

    @property
    def eps_est(self) -> pd.DataFrame:
        if self._eps_est is None and not self._already_scraped:
            self._scrape(self.proxy)
        return self._eps_est

    @property
    def eps_rev(self) -> pd.DataFrame:
        if self._eps_rev is None and not self._already_scraped:
            self._scrape(self.proxy)
        return self._eps_rev


    def _scrape(self, proxy):
        ticker_url = f"{self._SCRAPE_URL_}/{self._symbol}"
        try:
            resp = self._data.cache_get(ticker_url + '/analysis', proxy=proxy)
            analysis = pd.read_html(resp.text)
        except Exception:
            analysis = []

        analysis_dict = {df.columns[0]: df for df in analysis}

        for key, item in analysis_dict.items():
            # Set index
            item = item.set_index(key)
            if key in ['Earnings History', 'Revenue Estimate']:
                # Flip rows/columns
                item = item.T
            if key == 'Earnings History':
                try:
                    item.index = pd.to_datetime(item.index)
                except dateutil.parser._parser.ParserError:
                    pass


            for c in item.columns:
                # Format % columns
                if item[c].dtype in ['str', 'object']:
                    if item[c].str.endswith('%').sum() == item.shape[0]:
                        # All % so convert to numeric
                        item[c] = item[c].str.rstrip('%').str.replace(',','').astype("float")
                        if not '%' in c:
                            item = item.rename(columns={c:c+' %'})
                            c += ' %'

                    else:
                        # convert number-like values to integer type
                        f = item[c].str.endswith(('K', 'M', 'B', 'T', 'k', 'm', 'b', 't'))
                        if f.any():
                            fB = item[c].str.endswith(('B','b')).fillna(False)
                            fM = item[c].str.endswith(('M', 'm')).fillna(False)
                            fK = item[c].str.endswith(('K', 'k')).fillna(False)
                            fT = item[c].str.endswith(('T', 't')).fillna(False)
                            item[c] = item[c].str.rstrip('KMBTkmbt').astype("float")
                            item.loc[fB, c] *= 1e9
                            item.loc[fM, c] *= 1e6
                            item.loc[fK, c] *= 1e3
                            item.loc[fT, c] *= 1e12

            if key == 'Earnings History':
                self._earnings_trend = item
            elif key == 'EPS Trend':
                self._analyst_trend_details = item
            elif key == 'Growth Estimates':
                self._analyst_growth_estimates = item
            elif key == 'Revenue Estimate':
                self._rev_est = item
            elif key == 'Earnings Estimate':
                self._eps_est = item
            elif key == 'EPS Revisions':
                self._eps_rev = item

        self._already_scraped = True
