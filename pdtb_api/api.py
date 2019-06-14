import codecs
import json
from syntax_tree import Syntax_tree

class PDTB3:
    def __init__(self, data_path='/home/pengfei/data/PDTB-3.0/all/conll/'):
        """Args:
            data_path(str): path to all/conll folder
        """
        self.parse_data_train = [json.loads(o) for o in codecs.open(data_path + 'train/relations.json').readlines()]
        self.parse_dict_train = json.loads(codecs.open(data_path + 'train/pdtb-parses.json').read())

        self.parse_data_dev = [json.loads(o) for o in codecs.open(data_path + 'dev/relations.json').readlines()]
        self.parse_dict_dev = json.loads(codecs.open(data_path + 'dev/pdtb-parses.json').read())

        self.parse_data_test = [json.loads(o) for o in codecs.open(data_path + 'test/relations.json').readlines()]
        self.parse_dict_test = json.loads(codecs.open(data_path + 'test/pdtb-parses.json').read())

        self.parse_data = self._merge_parse_data()
        self.parse_dict = self._merge_parse_dict()

    def get_dependency(self, docid, token_indices):
        """
        Args:
                docid(str)
                token_indices[(sent#, token#), ...]
        Returns:
                dependencies[list[relation, (head(int), token(int))], ...]
        """
        doc = self.parse_dict[docid]['sentences']
        dependencies = []
        for sent_id, token_id in token_indices:
            sent_dependency = doc[sent_id]['dependencies']
            dep_text = self._get_token_dependency(sent_dependency, token_id)
            dep_relation = dep_text[0]
            head_id = self.get_index(dep_text[1]) - 1 
            token_id = self.get_index(dep_text[2]) - 1
            dependencies.append([dep_relation, head_id, token_id])
        return dependencies
    
    def get_tokens(self, docid, token_indices):
        """
        Args:
                docid(str)
                token_indices[(sent#, token#), ...]
        Returns:
                token_list[token(str], ...]
        """
        doc = self.parse_dict[docid]['sentences']
        token_list = []
        for sent_id, token_id in token_indices:
            token_text = doc[sent_id]['words'][token_id][0]
            token_list.append(token_text)
        return token_list
    
    def get_parse_tree(self, docid, sentid):
        """
        Args:
                docid(str)
                sentid(int)
        Returns:
                parse_tree(str)
        """
        return self.parse_dict[docid]['sentences'][sentid]['parsetree'] 

    def get_syntax_tree(self, docid, sentid):
        """
        Args:
                docid(str)
                sentid(int)
        Returns:
                (Syntax_tree)
        """
        return Syntax_tree(self.get_parse_tree(docid, sentid))

    def get_highlighted_relation(self, i, verbose=False):
        """
        Args:
                i(int): position in self.parse_data
                verbose(bool): whether print other related info, docid, and sense
        Returns:
                hstr(str):
                    highlighted sentence for each relation i
                    arg1 is highlighted using red color
                    connective(if any) is highlighted using underline
                    arg2 is highlighted blue 
        """
        hstr = ""
        r = self.parse_data[i]
        relation_sent_id = list(set([o[3] for o in r['Arg1']['TokenList']] + [o[3] for o in r['Arg2']['TokenList']]))
        sense = r['Sense']
        docid = r['DocID']
        Type = r['Type']
        Arg1_token_id = [(o[3],o[4]) for o in r['Arg1']['TokenList']]
        Arg2_token_id = [(o[3],o[4]) for o in r['Arg2']['TokenList']]
        if Type in ['Explicit', 'AltLex', 'AltLexC']: Conn_token_id = [(o[3],o[4]) for o in r['Connective']['TokenList']]
        if verbose: hstr += 'DocID: ' + docid + ',\t' + 'Type: ' + Type + ',\t' + 'Sense: ' + sense[0] + '\n' 

        for sent_id in relation_sent_id:
            sent = self.get_sent_words(docid, sent_id)
            for token_id, word in enumerate(sent):
                if check_if_arg(token_id, sent_id, Arg1_token_id):
                    hstr += color.RED + word[0] + color.END + ' '
                elif check_if_arg(token_id, sent_id, Arg2_token_id):
                    hstr += color.BLUE + word[0] + color.END + ' '
                elif Type in ['Explicit', 'AltLex', 'AltLexC']:
                    if check_if_arg(token_id, sent_id, Conn_token_id):
                        hstr += color.UNDERLINE + word[0] + color.END + ' '
                else:
                    hstr += word[0] + ' '
        return hstr

    def get_highlighted_parsetree(self, i):
        trees = ""
        r = self.parse_data[i]
        relation_sent_id = list(set([o[3] for o in r['Arg1']['TokenList']] + [o[3] for o in r['Arg2']['TokenList']]))
        sense = r['Sense']
        docid = r['DocID']
        Type = r['Type']
        Arg1_token_id = [(o[3],o[4]) for o in r['Arg1']['TokenList']]
        Arg2_token_id = [(o[3],o[4]) for o in r['Arg2']['TokenList']]
        if Type in ['Explicit', 'AltLex', 'AltLexC']: Conn_token_id = [(o[3],o[4]) for o in r['Connective']['TokenList']]

        for sent_id in relation_sent_id:
            parse_tree_list = str(self.get_syntax_tree(docid, sent_id).tree).split('\n')
            token_id = -1
            for prefix in parse_tree_list:
                if self._replace(prefix) == '':
                    trees += prefix + '\n'
                    continue
                token_id += 1 
                word = prefix.split('/-')[-1]
                prefix = prefix.replace(word, '')
                if check_if_arg(token_id, sent_id, Arg1_token_id):
                    trees += prefix + color.RED + word + color.END + '\n'
                elif check_if_arg(token_id, sent_id, Arg2_token_id):
                    trees += prefix + color.BLUE + word + color.END + '\n'
                elif Type in ['Explicit', 'AltLex', 'AltLexC']:
                    if check_if_arg(token_id, sent_id, Conn_token_id):
                        trees += prefix + color.UNDERLINE + word + color.END + '\n'
                else:
                    trees += prefix + word + '\n'
        return trees 

    def _replace(self, string):
        return string.replace('|', '').replace(' ', '').replace('-', '').replace('/', '').replace('\\', '').replace('\t','')

    def get_sent_words(self, docid, sent_id):
        return self.parse_dict[docid]['sentences'][sent_id]['words']

    def get_related_doc(parse_data, docid):
        ret = []
        for i, r in enumerate(parse_data):
            if r['DocID'] == docid:
                ret.append(r)
        return ret

    def _get_token_dependency(self, sent_dependency, token_id):
        const = token_id+1
        dep_index = self._get_dep_index(token_id, sent_dependency)
        while const != dep_index:
            token_id -= (dep_index - const)
            dep_index = self.get_dep_index(token_id, sent_dependency)
        return sent_dependency[token_id]

    def _get_dep_index(self, index, sent_dependency):
#         return int(sent_dependency[index][2].split('-')[-1])
        return self._get_index(sent_dependency[index][2])

    def _get_index(self, text):
        return int(text.split('-')[-1])

    def _merge_parse_data(self):
        parse_data = []
        parse_data.extend(self.parse_data_train)
        parse_data.extend(self.parse_data_dev)
        parse_data.extend(self.parse_data_test)
        return parse_data

    def _merge_parse_dict(self):
        parse_dict = {}
        parse_dict.update(self.parse_dict_train)
        parse_dict.update(self.parse_dict_dev)
        parse_dict.update(self.parse_dict_test)
        return parse_dict


def check_if_arg(token_id, sent_id, Arg_token_list):
    return (sent_id, token_id) in Arg_token_list


class color:
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    DARKCYAN = '\033[36m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    BACKGROUND = '\033[7m'
    END = '\033[0m'


if __name__ == "__main__":
    pdtb3 = PDTB3()
    pdtb3.get_highlighted_relation(100)
