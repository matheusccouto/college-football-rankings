""" Rankings web app section. """

from typing import Dict, List

import pandas as pd
import streamlit as st

import college_football_rankings as cfr
import ui


def comparison(rankings: Dict[str, List[str]], teams: Dict[str, cfr.Team], length: int):
    """ Create rankings comparison table. """

    # Select ranks to show.
    options = list(rankings.keys())
    selected_names = st.multiselect(
        "Select rankings to compare", options=options, default=options
    )
    selected = {name: rankings[name] for name in selected_names}

    # Create index column
    index = [f"#{i}" for i in range(1, length + 1)]

    selected = {key: val[:length] for key, val in selected.items()}
    if not selected:
        return

    selected = {
        key: val + [None] * (length - len(val)) for key, val in selected.items()
    }

    # Transform data into a dataframe and show it.
    data_frame = pd.DataFrame(selected, index=index)
    data_frame = data_frame.apply(ui.add_logos_and_records, args=(teams,))
    html_table = data_frame.to_html(escape=False)
    html_table = ui.format_html_table(html_table)
    st.write(html_table, unsafe_allow_html=True)
