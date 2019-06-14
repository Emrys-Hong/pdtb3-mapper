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
                token_list[list[token(str)], ...]
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
        return self.parse_tree[docid]['sentences'][sentid]['parsetree'] 

    def get_syntax_tree(self, docid, sentid):
        """
        Args:
                docid(str)
                sentid(int)
        Returns:
                (Syntax_tree)
        """
        return Syntax_tree(self.get_parse_tree(docid, sentid))

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
        parse_data.append(self.parse_data_train)
        parse_data.append(self.parse_data_dev)
        parse_data.append(self.parse_data_test)
        return parse_data

    def _merge_parse_dict(self):
        parse_dict = {}
        parse_dict.update(self.parse_dict_train)
        parse_dict.update(self.parse_dict_dev)
        parse_dict.update(self.parse_dict_test)
        return parse_dict
