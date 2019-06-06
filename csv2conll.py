import os
from pathlib import Path
import pandas as pd
import json
import codecs
import numpy as np
import re
from collections import OrderedDict

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

def get_span_list(span):
    if span == '':
        assert(False)
    spans = span.split(';')
    return [[int(k) for k in o.split('..')] for o in spans if o != '']

def get_doc_word_dict(parse_dict, DocID):
    ret={}
    doc_token_index = 0
    for sent_index, sentence in enumerate(parse_dict[DocID]['sentences']):
        for token_index, token in enumerate(sentence['words']):
            start = token[1]['CharacterOffsetBegin']
            end = token[1]['CharacterOffsetEnd']
            ret[(start, end)] = [start, end, doc_token_index, sent_index, token_index]
            doc_token_index += 1
    return ret

def get_token_list(char_span_list, doc_word_dict):
    tokenlist = []
    doc_word_dict = OrderedDict(sorted(doc_word_dict.items()), keys=lambda x:x[0][0])
    for span in char_span_list:
        for key, value in doc_word_dict.items():
            if type(key) == str:
                continue
            if key[1] > span[1]:
                break
            if key[0] >= span[0]:
                tokenlist.append(value)

    return tokenlist

def merge3dicts(x, y, z):
    m = x
    m.update(y)
    m.update(z)
    return m

def main(pdtb3, parse_dict, rawtext_foldername):
    relations = []
    unattended = []
    for i in range(len(pdtb3)):
        if i%1000 == 0:print(i)
        if pdtb3.loc[i,'DocID'] not in parse_dict.keys(): unattended.append(pdtb3.loc[i,'DocID']);continue
        relation = {}

        relation['DocID'] = pdtb3.loc[i, 'DocID']

        relation['ID'] = i

        relation['Type'] = pdtb3.loc[i, 'Relation_Type']

        if relation['Type'] not in ['Hypophora', 'NoRel', 'EntRel']:
            Sense = [pdtb3.loc[i,'SClass1A']]
            if type(pdtb3.loc[i,'SClass1B']) != float: Sense.append(pdtb3.loc[i,'SClass1B'])
            if type(pdtb3.loc[i,'SClass2A']) != float: Sense.append(pdtb3.loc[i,'SClass2A'])
            if type(pdtb3.loc[i,'SClass2B']) != np.float64: Sense.append(pdtb3.loc[i,'SClass2B'])
        else:
            Sense = [relation['Type']]
        relation['Sense'] = Sense

        
        doc_word_dict = get_doc_word_dict(parse_dict, pdtb3.loc[i, 'DocID'])
        rawtext = codecs.open(rawtext_foldername/pdtb3.loc[i,'DocID'],).read()

        # connective
        relation['Connective'] = {}
        if relation['Type'] in ['Explicit', 'AltLex', 'AltLexC']:
            relation['Connective']['CharacterSpanList'] = get_span_list(pdtb3.loc[i, 'Conn_SpanList'])
            # TODO: this may be a problem to put just one connective
            relation['Connective']['RawText'] = pdtb3.loc[i, 'Conn1']
            relation['Connective']['TokenList'] = get_token_list(relation['Connective']['CharacterSpanList'], doc_word_dict)
            # DONE: dirty fix removed
            assert(relation['Connective']['TokenList'] != [])
            if relation['Type'] in ['AltLex', 'AltLexC']:
                relation['Connective']['RawText'] = ' '.join([rawtext[o[0]:o[1]] for o in relation['Connective']['CharacterSpanList']]) 
        elif relation['Type'] == 'Implicit':
            relation['Connective']['CharacterSpanList'] = []
            relation['Connective']['RawText'] = pdtb3.loc[i, 'Conn1']
        else:
            relation['Connective']['CharacterSpanList'] = []
            relation['Connective']['RawText'] = ""

        # Arg1
        relation['Arg1'] = {}
        char_span_list = get_span_list(pdtb3.loc[i,'Arg1_SpanList'])
        relation['Arg1']['CharacterSpanList'] = char_span_list
        arg_rawtext = ' '.join([rawtext[o[0]:o[1]] for o in char_span_list])
        # TODO: get rid of all the \n if it appear in the arg?
        relation['Arg1']['RawText'] = arg_rawtext
        arg_tokenlist = get_token_list(char_span_list, doc_word_dict)
        relation['Arg1']['TokenList'] = arg_tokenlist

        # Arg2
        relation['Arg2'] = {}
        char_span_list = get_span_list(pdtb3.loc[i,'Arg2_SpanList'])
        relation['Arg2']['CharacterSpanList'] = char_span_list
        arg_rawtext = ' '.join([rawtext[o[0]:o[1]] for o in char_span_list])
        relation['Arg2']['RawText'] = arg_rawtext
        arg_tokenlist = get_token_list(char_span_list, doc_word_dict)
        relation['Arg2']['TokenList'] = arg_tokenlist

        relations.append(relation)
    return relations, unattended




def relations_to_file(relations):
    f = open('pdtb3.json', 'a')
    for relation in relations:
        f.write(json.dumps(relation))
        f.write('\n')
    f.close()

if __name__=="__main__":
    pdtb3 = pd.read_csv('pdtb3.csv')
    print("loading parse dict")
    conll_train = '/home/pengfei/data/2015-2016_conll_shared_task/data/conll16st-en-03-29-16-train/pdtb-parses.json'
    parse_dict_train = json.loads(codecs.open(conll_train, encoding='utf-8', errors='ignore').read())
    conll_dev = '/home/pengfei/data/2015-2016_conll_shared_task/data/conll16st-en-03-29-16-dev/pdtb-parses.json'
    parse_dict_dev = json.loads(codecs.open(conll_dev, encoding='utf-8', errors='ignore').read())
    conll_test = '/home/pengfei/data/2015-2016_conll_shared_task/data/conll16st-en-03-29-16-test/pdtb-parses.json'
    parse_dict_test = json.loads(codecs.open(conll_test, encoding='utf-8', errors='ignore').read())
    print("parse_dict loaded")
    parse_dict = merge3dicts(parse_dict_train, parse_dict_dev, parse_dict_test)
    rawtext_foldername = Path('/home/pengfei/data/PDTB-3.0/all/raw')
    relations, unattended = main(pdtb3, parse_dict, rawtext_foldername)
    relations_to_file(relations)
    print("files not contained in conll dataset:")
    print(set(unattended))
