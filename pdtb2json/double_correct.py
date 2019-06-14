import os
from pathlib import Path
import pandas as pd
import re
import json
import codecs
import numpy as np



def correct_conn_char_span(pdtb3):
    false_conn_list = []
    for i in range(len(pdtb3)):
        if i == 41854:
            pdtb3.loc[i,'Conn_SpanList'] = "4330..4335"
    return pdtb3








if __name__ == "__main__":
    df = pd.read_csv('pdtb3.csv')
    df = correct_conn_char_span(df,)
    df.to_csv('pdtb3.csv', index=False)
