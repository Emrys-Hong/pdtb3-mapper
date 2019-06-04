import os
from pathlib import Path
import pandas as pd 

def read_file(filename, fields_dict, index):
    with open(filename) as f:
        rawtext = f.readlines()
    for relation in rawtext:
        relation = relation.strip()
        fields = relation.split('|')
        fields_dict[index] = fields
        index+=1
    return fields_dict, index

def generate_df(main_foldername='/home/pengfei/data/PDTB-3.0/data/gold/'):
    main_foldername = Path(main_foldername)
    filepaths = get_filepaths(main_foldername)
    
    fields_dict = {}
    cols = ['Relation_Type','Conn_SpanList','Conn_Src','Conn_Type','Conn_Pol','Conn_Det','Conn_Feat_SpanList','Conn1','SClass1A','SClass1B','Conn2','SClass2A','SClass2B','Sup1_SpanList','Arg1_SpanList','Arg1_Src','Arg1_Type','Arg1_Pol','Arg1_Det','Arg2_Feat_SpanList','Arg2_SpanList','Arg2_Src','Arg2_Type','Arg2_Pol','Arg2_Det','Arg2_Feat_SpanList','Sup2_SpanList','Adju_Reason','Adju_Disagr','PB_Role','PB_Verb','Offset','Provenance','Link']
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

if __name__ == "__main__":
    main_foldername = '/home/pengfei/data/PDTB-3.0/data/gold/'
    df = generate_df(main_foldername)
    df.to_csv('pdtb3.csv', index=False)
