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
        if pdtb3.loc[i, 'Relation_Type'] == 'Explicit':
            spanlist = get_span_list(pdtb3.loc[i, 'Conn_SpanList'])
            with open(main_folder + pdtb3.loc[i, 'DocID'], ) as f:
                rawtext = f.read()
                expected = ' '.join([rawtext[o[0]: o[1]] for o in spanlist]).lower()
            if pdtb3.loc[i, 'Conn1'] not in expected:
                false_conn_list.append(i)
    print("Number of incorrect conn span list", len(false_conn_list))
    print("begin correcting")
    for i in false_conn_list:
        with open(main_folder+pdtb3.loc[i,'DocID'], ) as f:
            rawtext = f.read().lower()
            start = int(pdtb3.loc[i, 'Conn_SpanList'].split('..')[0])
            #TODO: dirty fix at 41854, "still", "till"
            distance = [abs(m.start() - start) for m in re.finditer(pdtb3.loc[i,'Conn1'], rawtext, )]
            start = [m.start() for m in re.finditer(pdtb3.loc[i, 'Conn1'], rawtext)]
            if distance != []:
                index = distance.index(min(distance))
                start = start[index]
                span = str(start) + '..' + str(start+len(pdtb3.loc[i, 'Conn1']))
                pdtb3.loc[i, 'Conn_SpanList'] = span
    print("connective char span are complete")
    false_conn_list = []
    for i in range(len(pdtb3)):
        if pdtb3.loc[i, 'Relation_Type'] == 'Explicit':
            spanlist = get_span_list(pdtb3.loc[i, 'Conn_SpanList'])
            with open(main_folder + pdtb3.loc[i, 'DocID']) as f:
                rawtext = f.read()
                expected = ' '.join([rawtext[o[0]: o[1]] for o in spanlist]).lower()
            if pdtb3.loc[i, 'Conn1'] not in expected:
                false_conn_list.append(i)
    print("Number of incorrect conn span left", len(false_conn_list))
    return pdtb3


def correct_arg_span(parse_dict, pdtb3):
    """change are smaller than 2 char span"""
    for i in range(len(pdtb3)):
        if i%100==0:print(i)
        if pdtb3.loc[i, 'DocID'] in parse_dict.keys():
            char_start_list, char_end_list = get_list(parse_dict, pdtb3.loc[i, 'DocID'])

            spanlist = get_span_list(pdtb3.loc[i, 'Arg1_SpanList'])
            for span in spanlist:
                if span[0] not in char_start_list:
                    distance = [abs(span[0]-o) for o in char_start_list]
                    index = distance.index(min(distance))
                    span[0] = char_start_list[index]
                if span[1] not in char_end_list:
                    distance = [abs(span[1]-o) for o in char_end_list]
                    index = distance.index(min(distance))
                    span[1] = char_end_list[index]
            span_string = get_span_string(spanlist)
            pdtb3.loc[i, 'Arg1_SpanList'] = span_string

            spanlist = get_span_list(pdtb3.loc[i, 'Arg2_SpanList'])
            for span in spanlist:
                if span[0] not in char_start_list:
                    distance = [abs(span[0]-o) for o in char_start_list]
                    index = distance.index(min(distance))
                    span[0] = char_start_list[index]
                if span[1] not in char_end_list:
                    distance = [abs(span[1]-o) for o in char_end_list]
                    index = distance.index(min(distance))
                    span[1] = char_end_list[index]
            span_string = get_span_string(spanlist)
            pdtb3.loc[i, 'Arg2_SpanList'] = span_string

    return pdtb3


def merge3dicts(x, y, z):
    m = x.copy()
    m.update(y)
    m.update(z)
    return m


def get_list(parse_dict, doc):
    doc = parse_dict[doc]['sentences']
    char_start_list = []
    char_end_list = []
    for sentence in doc:
        for word in sentence['words']:
            char_start_list.append(word[1]['CharacterOffsetBegin'])
            char_end_list.append(word[1]['CharacterOffsetEnd'])
    return char_start_list, char_end_list


def get_span_string(span_list):
    ret = ''
    for span in span_list:
        ret += str(span[0])
        ret += '..'
        ret += str(span[1])
        ret += ';'
    return ret[:-1]

if __name__ == "__main__":
    gold_folder = '/home/pengfei/data/PDTB-3.0/data/gold/'
    df = generate_df(gold_folder)
    raw_folder = '/home/pengfei/data/PDTB-3.0/all/raw/'
    df = correct_conn_char_span(df, raw_folder)
    print("loading conll datasets")
    conll_train = '/home/pengfei/data/2015-2016_conll_shared_task/data/conll16st-en-03-29-16-train/pdtb-parses.json'
    parse_dict_train = json.loads(codecs.open(conll_train, encoding='utf-8', errors='ignore').read())
    conll_dev = '/home/pengfei/data/2015-2016_conll_shared_task/data/conll16st-en-03-29-16-dev/pdtb-parses.json'
    parse_dict_dev = json.loads(codecs.open(conll_dev, encoding='utf-8', errors='ignore').read())
    conll_test = '/home/pengfei/data/2015-2016_conll_shared_task/data/conll16st-en-03-29-16-test/pdtb-parses.json'
    parse_dict_test = json.loads(codecs.open(conll_test, encoding='utf-8', errors='ignore').read())
    print("datasets loaded")
    parse_dict = merge3dicts(parse_dict_train, parse_dict_dev, parse_dict_test)
    df = correct_arg_span(parse_dict, df)
    df.to_csv('pdtb3.csv', index=False)
