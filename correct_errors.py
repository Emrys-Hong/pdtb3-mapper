import os
from pathlib import Path
import pandas as pd
import re
import json
import codecs
import numpy as np


def read_file(filename, fields_dict, index):
    with open(filename) as f:
        rawtext = f.readlines()
    for relation in rawtext:
        relation = relation.strip()
        fields = relation.split('|')
        fields = [str(filename).split('/')[-1]] + fields
        fields_dict[index] = fields
        index+=1
    return fields_dict, index

def generate_df(main_foldername='/home/pengfei/data/PDTB-3.0/data/gold/'):
    main_foldername = Path(main_foldername)
    filepaths = get_filepaths(main_foldername)
    
    fields_dict = {}
    cols = ['DocID','Relation_Type','Conn_SpanList','Conn_Src','Conn_Type','Conn_Pol','Conn_Det','Conn_Feat_SpanList','Conn1','SClass1A','SClass1B','Conn2','SClass2A','SClass2B','Sup1_SpanList','Arg1_SpanList','Arg1_Src','Arg1_Type','Arg1_Pol','Arg1_Det','Arg1_Feat_SpanList','Arg2_SpanList','Arg2_Src','Arg2_Type','Arg2_Pol','Arg2_Det','Arg2_Feat_SpanList','Sup2_SpanList','Adju_Reason','Adju_Disagr','PB_Role','PB_Verb','Offset','Provenance','Link']
    index=0
    for filepath in filepaths:
        fields_dict, index = read_file(filepath, fields_dict, index)
    
    df = pd.DataFrame.from_dict(fields_dict, orient='index', columns=cols)
    return df

def get_filepaths(main_foldername):
    filepaths = []
    for folder in os.listdir(main_foldername):
        for filename in os.listdir(main_foldername/folder):
            filepaths.append(main_foldername/folder/filename)
    return filepaths

def write_all_files():
    main_folder = '/home/pengfei/data/PDTB-3.0/data/raw/'
    write_folder = '/home/pengfei/data/PDTB-3.0/all/raw/'
    filepaths = [main_folder+folder+'/'+o for folder in os.listdir(main_folder) for o in os.listdir(main_folder+folder)]
    for filename in filepaths:
        with open(filename, encoding='latin1') as f:
            rawtext = f.read()
        with open(write_folder + filename.split('/')[-1], 'a') as f:
            f.write(rawtext) 
    pass

def get_span_list(span):
    if span == '':
        assert(False)
    spans = span.split(';')
    return [[int(k) for k in o.split('..')] for o in spans if o != '']


def correct_conn_char_span(pdtb3, main_folder):
    false_conn_list = []
    for i in range(len(pdtb3)):
        if i == 41854:
            pdtb3.loc[i,'Conn_SpanList'] = "4330..4335"
    return pdtb3








if __name__ == "__main__":
    gold_folder = '/home/pengfei/data/PDTB-3.0/data/gold/'
    df = pd.read_csv('pdtb3.csv')
    raw_folder = '/home/pengfei/data/PDTB-3.0/all/raw/'
    df = correct_conn_char_span(df, raw_folder)
    df.to_csv('pdtb3.csv', index=False)
