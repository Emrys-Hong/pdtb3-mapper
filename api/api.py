import codecs
import json
from .syntax_tree import Syntax_tree
from nltk.tree import Tree
import itertools
import copy
import re

class PDTB:
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

    def get_tokens_text(self, docid, token_indices):
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

    def get_tokens_indices_with_text(self, docid, sent_id):
        """
        Args:
                docid(str)
                sent_id(int)
        Returns:
                token_list[ (sent_number(int), token_index_in_sent(int), token(str)), ...]
        """
        doc = self.parse_dict[docid]['sentences']
        token_list = []
        for i, token in enumerate(doc[sent_id]['words']):
            token_list.append( (sent_id, i, token[0]) )
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

    def get_arg_sent_id(self, i, x):
        """
        Args:
                i: relation number
                x(str): Arg1, Arg2, Connective
        Returns: list of all the sentence id containing x
        """
        return list(set([o[3] for o in self.parse_data[i][x]['TokenList']]))

    def arg_is_whole_sentence(self, i, arg):
        """Args:
                i(int): parse_data index
                arg(str): Arg1, Arg2
        Returns:
                whether arg takes entire span
        """
        docid = self.parse_data[i]['DocID']
        arg_token_list = self.get_arg_token_list(i, arg)
        arg_sent_id = self.get_arg_sent_id(i, arg)
        sent_token_list = []
        for sentid in arg_sent_id:
            sent_token_list.extend(self.get_tokens_indices_with_text(docid, sentid))
        return same_sentence(sent_token_list, arg_token_list)

    def get_arg_token_list(self, i, x):
        """
        Args:
                i: relation number
                x(str): Arg1, Arg2, Connective
        Returns: [ (sent_id, token_id_in_sent), ...]
        """
        return [(o[3], o[4]) for o in self.parse_data[i][x]['TokenList']]

    def get_arg_token_list_in_doc(self, i, x):
        """
        Args:
                i: relation number
                x(str): Arg1, Arg2, Connective
        Returns: [ token_id_in_doc, ...]
        """
        return [(o[2]) for o in self.parse_data[i][x]['TokenList']]

    def get_syntax_tree(self, docid, sentid):
        """
        Args:
                docid(str)
                sentid(int)
        Returns:
                (Syntax_tree)
        """
        parse_tree = self.get_parse_tree(docid, sentid)
        if parse_tree == None:
            raise Exception('Parse tree is not generated')
        if parse_tree.strip() == '':
            raise Exception('Parse tree is not generated')
        return Syntax_tree()

    def get_relation_chomsky_syntax_tree(self, i):
        """
        Args:
                i: relation number
        Returns:
            if arg1 and arg2 have different sentence:
                {'Arg1': [arg1_parse_trees], 'Arg2', [arg2_parse_trees]}
            if arg1 and arg2 have the same sentence:
                (syntax_tree)
            if arg1 or arg2 contains more than 1 sentence:
                None
        """
        arg1_sent_id = self.get_arg_sent_id(i, 'Arg1')
        arg2_sent_id = self.get_arg_sent_id(i, 'Arg2')
        if len(arg1_sent_id) == len(arg2_sent_id) == 1:
            # SS case
            if arg1_sent_id[0] == arg2_sent_id[0]:
                nltk_tree = Tree.fromstring(self.get_parse_tree(self.parse_data[i]['DocID'], arg1_sent_id[0]))
                nltk_tree.chomsky_normal_form()
                chomsky_tree = str(nltk_tree)
                return Syntax_tree(chomsky_tree)
            # PS case
            elif arg1_sent_id[0] < arg2_sent_id[0]:
                nltk_arg1_tree = Tree.fromstring(self.get_parse_tree(self.parse_data[i]['DocID'], arg1_sent_id[0]))
                nltk_arg2_tree = Tree.fromstring(self.get_parse_tree(self.parse_data[i]['DocID'], arg2_sent_id[0]))
                nltk_arg1_tree.chomsky_normal_form()
                nltk_arg2_tree.chomsky_normal_form()
                chomsky_arg1_tree = str(nltk_arg1_tree)
                chomsky_arg2_tree = str(nltk_arg2_tree)
                return {'Arg1': Syntax_tree(chomsky_arg1_tree), \
                        'Arg2': Syntax_tree(chomsky_arg2_tree)  }
        else:
            return None

    def get_relation_chomsky_parse_tree(self, i):
        arg1_sent_id = self.get_arg_sent_id(i, 'Arg1')
        arg2_sent_id = self.get_arg_sent_id(i, 'Arg2')
        if len(arg1_sent_id) == len(arg2_sent_id) == 1:
            # SS case
            if arg1_sent_id[0] == arg2_sent_id[0]:
                nltk_tree = Tree.fromstring(self.get_parse_tree(self.parse_data[i]['DocID'], arg1_sent_id[0]))
                nltk_tree.chomsky_normal_form()
                chomsky_tree = str(nltk_tree)
                return chomsky_tree
            # PS case
            elif arg1_sent_id[0] < arg2_sent_id[0]:
                nltk_arg1_tree = Tree.fromstring(self.get_parse_tree(self.parse_data[i]['DocID'], arg1_sent_id[0]))
                nltk_arg2_tree = Tree.fromstring(self.get_parse_tree(self.parse_data[i]['DocID'], arg2_sent_id[0]))
                nltk_arg1_tree.chomsky_normal_form()
                nltk_arg2_tree.chomsky_normal_form()
                chomsky_arg1_tree = str(nltk_arg1_tree)
                chomsky_arg2_tree = str(nltk_arg2_tree)
                return {'Arg1': chomsky_arg1_tree, \
                        'Arg2': chomsky_arg2_tree  }
        else:
            return None


    def get_highlighted_relation(self, i, v=False):
        """
        args:
                i(int): position in self.parse_data
                verbose(bool): whether print other related info, docid, and sense
        returns:
                hstr(str):
                    highlighted sentence for each relation i
                    arg1 is highlighted using red color
                    connective(if any) is highlighted green
                    arg2 is highlighted blue 
        """
        r = self.parse_data[i]
        relation_sent_id = list(set([o[3] for o in r['Arg1']['TokenList']] + [o[3] for o in r['Arg2']['TokenList']]))
        sense = r['Sense']
        docid = r['DocID']
        Type = r['Type']
        Arg1_token_id = [(o[3],o[4]) for o in r['Arg1']['TokenList']]
        Arg2_token_id = [(o[3],o[4]) for o in r['Arg2']['TokenList']]
        if Type in ['Explicit', 'AltLex', 'AltLexC']: Conn_token_id = [(o[3],o[4]) for o in r['Connective']['TokenList']]
        hstr = "Relation: " + str(i) + ",  Green for Connective(if any), Red for Arg1 and Blue for Arg2. \n" + \
                'DocID: ' + docid + ',\t' + 'Type: ' + Type + ',\t' + 'Sense: ' + sense[0] + ',\n' + \
                'Arg1_sent_id: ' + ' '.join(list(set([str(o[3]) for o in r['Arg1']['TokenList']])))  + '\t' \
                ',\t' + 'Arg2_sent_id: ' + ' '.join(list(set([str(o[3]) for o in r['Arg2']['TokenList']]))) + '\n' if v else ''

        for sent_id in relation_sent_id:
            sent = self.get_sent_words(docid, sent_id)
            for token_id, word in enumerate(sent):
                if check_if_arg(token_id, sent_id, Arg1_token_id):
                    hstr += color.RED + word[0] + color.END + ' '
                elif check_if_arg(token_id, sent_id, Arg2_token_id):
                    hstr += color.BLUE + word[0] + color.END + ' '
                elif Type in ['Explicit', 'AltLex', 'AltLexC']:
                    if check_if_arg(token_id, sent_id, Conn_token_id):
                        hstr += color.GREEN + word[0] + color.END + ' '
                else:
                    hstr += word[0] + ' '
        return hstr

    def get_highlighted_parsetree(self, i, v=True):
        """
        args:
                i(int): position in self.parse_data
                v(boolean): verbose
        returns:
                trees(str):
                    highlighted sentence for each relation i
                    arg1 is highlighted using red color
                    connective(if any) is highlighted green
                    arg2 is highlighted blue 
        """

        r = self.parse_data[i]
        relation_sent_id = list(set([o[3] for o in r['Arg1']['TokenList']] + [o[3] for o in r['Arg2']['TokenList']]))
        sense = r['Sense']
        docid = r['DocID']
        Type = r['Type']
        Arg1_token_id = [(o[3],o[4]) for o in r['Arg1']['TokenList']]
        Arg2_token_id = [(o[3],o[4]) for o in r['Arg2']['TokenList']]
        Conn_token_id = [(o[3],o[4]) for o in r['Connective']['TokenList']] if Type in ['Explicit', 'AltLex', 'AltLexC'] else []
        trees = "Relation: " + str(i) + ",  Green for Connective(if any), Red for Arg1 and Blue for Arg2. \n" + \
                'DocID: ' + docid + ',\t' + 'Type: ' + Type + ',\t' + 'Sense: ' + sense[0] + ',\n' + \
                'Arg1_sent_id: ' + ' '.join(list(set([str(o[3]) for o in r['Arg1']['TokenList']])))  + '\t' \
                ',\t' + 'Arg2_sent_id: ' + ' '.join(list(set([str(o[3]) for o in r['Arg2']['TokenList']]))) + '\n' if v else ''

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
                elif check_if_arg(token_id, sent_id, Conn_token_id):
                        trees += prefix + color.GREEN + word + color.END + '\n'
                else:
                    trees += prefix + word + '\n'
        return trees 


    def print_highlighted_parsetree(self, i, v=True):
        """
        prints out parse tree with color coded relationship
        """
        r = self.parse_data[i]
        relation_sent_id = list(set([o[3] for o in r['Arg1']['TokenList']] + [o[3] for o in r['Arg2']['TokenList']]))
        sense = r['Sense']
        docid = r['DocID']
        Type = r['Type']
        Arg1_token_id = [(o[3],o[4]) for o in r['Arg1']['TokenList']]
        Arg2_token_id = [(o[3],o[4]) for o in r['Arg2']['TokenList']]
        Conn_token_id = [(o[3],o[4]) for o in r['Connective']['TokenList']] if Type in ['Explicit', 'AltLex', 'AltLexC'] else []
        verbose = "Relation: " + str(i) + ",  Green for Connective(if any), Red for Arg1 and Blue for Arg2. \n" + \
                'DocID: ' + docid + ',\t' + 'Type: ' + Type + ',\t' + 'Sense: ' + sense[0] + ',\n' + \
                'Arg1_sent_id: ' + ' '.join(list(set([str(o[3]) for o in r['Arg1']['TokenList']])))  + '\t' \
                ',\t' + 'Arg2_sent_id: ' + ' '.join(list(set([str(o[3]) for o in r['Arg2']['TokenList']]))) + '\n' if v else ''
        if v: print(verbose)
        for sent_id in relation_sent_id:
            try:
                syntax_tree = self.get_syntax_tree(docid, sent_id)
                leaves = syntax_tree.tree.get_leaves()
                for token_id,l in enumerate(leaves):
                    if check_if_arg(token_id, sent_id, Arg1_token_id):
                        l.name = color.RED + l.name + color.END
                    elif check_if_arg(token_id, sent_id, Arg2_token_id):
                        l.name = color.BLUE + l.name + color.END
                    elif check_if_arg(token_id, sent_id, Conn_token_id):
                        l.name = color.GREEN + l.name + color.END
                syntax_tree.print_tree()
                print('\n\n')
            except Exception as e:
                print(e)



    def get_num_of_seg_of_arg(self, i, x):
        arg = self.get_arg_token_list_in_doc(i, x)
        n=0
        pred_index = -1
        for token in arg:
            if token != pred_index:
                pred_index = token
                n += 1
            pred_index += 1
        return n

    def get_subtree_length(self, i, arg):
        """Returns len of potential segments for explicit SS case"""
        docid = self.parse_data[i]['DocID']
        sentid = self.get_arg_sent_id(i, arg)
        conn_indices = [o[1] for o in self.get_arg_token_list(i, 'Connective')]
        subtree_list = self._get_constituents(docid, sentid[0], conn_indices)
        return len(subtree_list)

    def _replace(self, string):
        return string.replace('|', '').replace(' ', '').replace('-', '').replace('/', '').replace('\\', '').replace('\t','')

    def get_sent_words(self, docid, sent_id):
        return self.parse_dict[docid]['sentences'][sent_id]['words']

    def get_related_doc(self, docid):
        ret = []
        for i, r in enumerate(self.parse_data):
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

    def _get_constituents(self, docid, sentid, conn_index):
        """
        Args:
                docid(str)
                sentid(int)
                conn_index(list[int])
        Returns:
                [ [(token_index, text),...], ...]"""
        syntax_tree = self.get_syntax_tree(docid, sentid)
        if syntax_tree.tree == None:
            return []
        all_leaves = syntax_tree.tree.get_leaves()
        conn_indices = conn_index
        constituent_nodes = []
        if len(conn_indices) == 1:# like and or so...
            conn_node = syntax_tree.get_leaf_node_by_token_index(conn_indices[0]).up
        else:
            conn_node = syntax_tree.get_common_ancestor_by_token_indices(conn_indices)
            conn_leaves = set([all_leaves.index(syntax_tree.get_leaf_node_by_token_index(conn_index)) for conn_index in conn_indices])
            children = conn_node.get_children()
            for child in children:
                leaves = set([all_leaves.index(n) for n in child.get_leaves()])
                if list(leaves-conn_leaves)!=[]: constituent_nodes.append(list(leaves-conn_leaves))
        curr = conn_node
        while not curr.is_root():
            sibs = [ [all_leaves.index(n) for n in sib] for sib in syntax_tree.get_siblings(curr)]
            constituent_nodes.extend(sibs)
            curr = curr.up

        tokens_indices_with_text = self.get_tokens_indices_with_text(docid, sentid)
        subtree_list = [ [(o,tokens_indices_with_text[o][2]) for o in node] for node in constituent_nodes]
        return subtree_list


    def _arg_clauses(self, docid, sentid):
        token_indices_with_text = self.get_tokens_indices_with_text(docid, sentid)
        sent_tokens = [(i,t) for _,i,t in token_indices_with_text]
        # step 1: split the word
        punctuation = "...,:;?!~--"
        _clause_indices_list = []#[[(1,"I")..], ..]
        temp = []
        for index, word in sent_tokens:
            if word not in punctuation:
                temp.append((index, word))
            else:
                if temp != []:
                    _clause_indices_list.append(temp)
                    temp = []
        if temp != []: _clause_indices_list.append(temp)
        # strip punctuations in the start or end 
        clause_indices_list = []
        for clause_indices in _clause_indices_list:
            temp = list_strip_punctuation(clause_indices)
            if temp != []:
                clause_indices_list.append([item[0] for item in temp])

        # step2: then use SBAR tag in its parse tree to split each part into clauses.
        syntax_tree = self.get_syntax_tree(docid, sentid)
        if syntax_tree.tree == None:
            return []
        clause_list = []
        for clause_indices in clause_indices_list:
            clause_tree = _get_subtree(syntax_tree, clause_indices)
            flag = 0
            for node in clause_tree.tree.traverse(strategy="levelorder"):
                if node.name == "SBAR":
                    temp1 = [node.index for node in node.get_leaves()]
                    temp2 = sorted(list(set(clause_indices) - set(temp1)))

                    if temp2 == []:
                        clause_list.append(temp1)
                    else:
                        if temp1[0] < temp2 [0]:
                            clause_list.append(temp1)
                            clause_list.append(temp2)
                        else:
                            clause_list.append(temp2)
                            clause_list.append(temp1)
                    flag = 1
                    break
            if flag == 0:
                clause_list.append(clause_indices)
        clauses = []
        for clause_indices in clause_list:
            clauses.append(clause_indices)
        return [ [(o,token_indices_with_text[o][2]) for o in c] for c in clauses]

    def arg_is_contained(self, i, arg):
        docid = self.parse_data[i]['DocID']
        sentid = self.get_arg_sent_id(i, arg)
        conn_indices = [o[1] for o in self.get_arg_token_list(i, 'Connective')]
        subtree_list = self._get_constituents(docid, sentid[0], conn_indices)
        merged_consti_list = merge_consti(subtree_list)
        token_list = self.get_arg_token_list(i, arg)
        start,end = token_list[0][1], token_list[-1][1]
        # filter results
        consti_list = [k for k in merged_consti_list.keys() if k[0]>=start and k[1]<=end]
        # generate results
        results = []
        for i in range(1, len(consti_list)+1):
            for subset in itertools.combinations(consti_list, i):
                results.append(expand(subset))
        # check
        return [o[1] for o in token_list] in results

    def arg_is_contained_clause(self, i, arg):
        docid = self.parse_data[i]['DocID']
        sentid = self.get_arg_sent_id(i, arg)
        clause_list = self._arg_clauses(docid, sentid[0])
        merged_clause_list = merge_consti(clause_list)
        token_list = self.get_arg_token_list(i, arg)
        token_text = self.get_tokens_text(docid, token_list)
        assert(len(token_list) == len(token_text))
        start,end = token_list[0][1], token_list[-1][1]
        # filter results
        clause_list = [k for k in merged_clause_list.keys() if k[0]>=start and k[1]<=end]
        # generate results
        results = []
        for i in range(1, len(clause_list)+1):
            for subset in itertools.combinations(clause_list, i):
                results.append(expand(subset))
        # check
        return contained([o[1] for o in token_list], results, token_text)


def check_if_arg(token_id, sent_id, Arg_token_list):
    return (sent_id, token_id) in Arg_token_list

def merge_consti(subtree_list):
    return {(o[0][0],o[-1][0]):i for i,o in enumerate(subtree_list)}

def expand(subset):
    ret = []
    for subsubset in subset:
        for i in range(subsubset[0], subsubset[1]+1):
            ret.append(i)
    return sorted(ret)

def contained(token_list, results, token_text):
    punctuation = """!"#&'*+,-..../:;<=>?@[\]^_`|~""" + "``" + "''"
    for result in results:
        remain = set(token_list).symmetric_difference(set(result))
        whether = True
        for r in remain:
            if r not in token_list: continue
            if token_text[token_list.index(r)] not in punctuation:
                whether = False
        if whether: return True
    return False

def list_strip_punctuation(list):
    punctuation = """!"#&'*+,-..../:;<=>?@[\]^_`|~""" + "``" + "''"
    i = 0
    while i < len(list) and list[i][1] in punctuation + "-LCB--LRB-":
        i += 1
    if i == len(list):
        return []
    j = len(list) - 1
    while j >= 0 and list[j][1] in punctuation + "-RRB--RCB-":
        j -= 1
    return list[i: j+1]

def _get_subtree(syntax_tree, clause_indices):
    copy_tree = copy.deepcopy(syntax_tree)

    for index, leaf in enumerate(copy_tree.tree.get_leaves()):
        leaf.add_feature("index",index)

    clause_nodes = []
    for index in clause_indices:
        node = copy_tree.get_leaf_node_by_token_index(index)
        clause_nodes.append(node)

    for node in copy_tree.tree.traverse(strategy="levelorder"):
        node_leaves = node.get_leaves()
        if set(node_leaves) & set(clause_nodes) == set([]):
            node.detach()
    return copy_tree

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


def same_sentence(sent, arg):
    punct = """!"#&'*+,-..../:;<=>?@[\]^_`|~""" + "`" + "''"
    while sent[-1][2] in punct:
        sent.pop()
    while sent[0][2] in punct:
        sent.pop(0)
    return arg == [(o[0],o[1]) for o in sent]

if __name__ == "__main__":
    pdtb2 = '/home/pengfei/data/pdtb_v2/all/conll/'
    pdtb3 = PDTB()
    #print(pdtb3.arg_is_whole_sentence(2535, 'Arg1'))
    #print(pdtb3.arg_is_contained(34, 'Arg1'))
