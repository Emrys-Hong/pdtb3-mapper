import re


class ProcessTree:
    def __init__(self):
        pass
    
    def get_simplified_tree_string(self, tree):
        tree_name = self.simplify_tree_with_word(tree)
        tree = self.more_simplify_tree_with_word(tree)
        tree = self.most_simplify_tree_with_word(tree)
        tree_string = self.tree2string(tree)
        sentence = ' '.join([o.split()[-1] for o in re.findall(r'\((.+?)\)', tree_string)])
        return tree_string, sentence
    
    
    def simplify_tree_with_word(self, tree):
        temp = []
        tag = tree.name.split()[0]
        if tag in ['Arg1', 'Arg2', 'none', 'Conn']:
            return tree.name
        for c in tree.children:
            child_name = self.simplify_tree_with_word(c)
            temp.append(child_name.split()[0])
        if len(set(temp)) == 1:
            tree.name = temp[0] + ' ' + ' '.join([c.name[4:] for c in tree.children])
            tree.children = []
        return tree.name


    def more_simplify_tree_with_word(self, tree):
        temp = []
        # simplify among siblings
        prev_c = None
        for c in tree.children:
            c = self.more_simplify_tree_with_word(c)
            if prev_c == None:
                temp.append(c)
                prev_c = c
                continue
            if c.name.split()[0] != prev_c.name.split()[0]:
                temp.append(c)
                prev_c = c
            else:
                prev_c.name = prev_c.name + c.name[4:]
        tree.children = temp
        return tree

    def most_simplify_tree_with_word(self, tree):
        for i, c in enumerate(tree.children):
            tree.children[i] = self.most_simplify_tree_with_word(c)
        if len(tree.children) == 2:
            # for left branch
            if len(tree.children[1].children) >= 1:
                if tree.children[1].children[0].name.split()[0] == tree.children[0].name.split()[0]:
                    downup = tree.children[1].children[0]
                    downup.name = downup.name.split()[0] + tree.children[0].name[4:] + downup.name[4:]
                    tree = tree.children[1]
            # for right branch
            if len(tree.children[0].children) >= 1:
                if tree.children[0].children[1].name.split()[0] == tree.children[1].name.split()[0]:
                    updown = tree.children[0].children[1]
                    updown.name = updown.name + tree.children[1].name[4:]
                    tree = tree.children[0]
        tree = self.more_simplify_tree_with_word(tree)
        return tree


    def tree2string(self, tree):
        tree_string = ""
        if len(tree.children) == 0:
            return ''.join(["(" + tree.name.split()[0] + " " + o + ")" for o in tree.name.split()[1:]])
        tree_string += "(" + tree.name + " "
        for c in tree.children:
            tree_string += self.tree2string(c)
        tree_string += ")"
        return tree_string
