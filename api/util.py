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

def simplify_tree(tree):
    # merge big chunks of trees
    temp = []
    if tree.name in ['Arg1', 'Arg2', 'none', 'Conn']:
        return tree.name
    for c in tree.children:
        child_label = simplify_tree(c)
        temp.append(child_label)
    if len(set(temp)) == 1:
        tree.name = temp[0]
        tree.children = []
    return tree.name

def more_simplify_tree(tree):
    temp = []
    
    ## simplify among siblings
    prev_c = None
    for c in tree.children:
        c = more_simplify_tree(c)
        if c.name != prev_c:
            temp.append(c)
            prev_c = c.name
    tree.children = temp
    return tree

def most_simplify_tree(tree):
    for i, c in enumerate(tree.children):
        tree.children[i] = most_simplify_tree(c)
    if len(tree.children) == 2:
        # for left branch
        if len(tree.children[1].children) >= 1:
            if tree.children[1].children[0].name == tree.children[0].name:
                tree = tree.children[1]
        # for right branch
        if len(tree.children[0].children) >= 1:
            if tree.children[0].children[1].name == tree.children[1].name:
                tree = tree.children[0]
    return tree

def get_tree_rules(tree, rules):
    for c in tree.children:
        rules = get_tree_rules(c, rules)
    children = list(map(lambda x:x.name, tree.children))
    if children != []:
        rules.append( (tree.name, children ) )
    return rules



