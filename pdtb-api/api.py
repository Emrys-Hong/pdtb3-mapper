import codecs
import json

class PDTB3:
    def __init__(self, parse_data_path, parse_dict_path):
        self.parse_data = [json.loads(o) for o in codecs.open(parse_data_path).readlines()]
        self.parse_dict = json.loads(codecs.open(parse_dict_path).read())
        
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
            dep_text = self.get_token_dependency(sent_dependency, token_id)
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
    
    def get_token_dependency(self, sent_dependency, token_id):
        const = token_id+1
        dep_index = self.get_dep_index(token_id, sent_dependency)
        while const != dep_index:
            token_id -= (dep_index - const)
            dep_index = self.get_dep_index(token_id, sent_dependency)
        return sent_dependency[token_id]
    
    def get_dep_index(self, index, sent_dependency):
#         return int(sent_dependency[index][2].split('-')[-1])
        return self.get_index(sent_dependency[index][2])
    
    def get_index(self, text):
        return int(text.split('-')[-1])
    
