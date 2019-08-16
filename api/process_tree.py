from ete3 import TreeNode

class ProcessTree:
    def __init__(self):
        pass
        
    def _simplify_tree(self, tree):
        # tree.label is the word
        # tree.name is arg1 arg2 or pos tag
        temp = []
        if len(tree.children) == 0:
            return tree.label
        for c in tree.children:
            child_label = self._simplify_tree(c)
            temp.append(child_label)
        if len(set(temp)) == 1:
            tree.label = temp[0]
        else:
            tree.label = tree.name
        return tree.label
    
    def simplify_tree(self, tree):
        root_label = self._simplify_tree(tree)
        if tree.label in ['Arg1', 'Arg2', 'Conn', 'none']:
            tree.children = self.get_leave_node(tree)
            return
        for i, c in enumerate(tree.children):
            if self.deeperthan1(c):
                self.simplify_tree(c)
            else:
                n = TreeNode()
                n.children = [c]
                n.label = c.label
                tree.children[i] = n
                
    
    def deeperthan1(self, c):
        for cc in c.children:
            if len(cc.children) > 0:
                return True
        return False

    def get_leave_node(self, tree):
        leave_nodes = tree.get_leaves()
        preterminals = [n.up for n in leave_nodes]
        return preterminals
    
    def print_tree_label(self, tree):
        """this is for debug purpose and wont be used normally"""
        if self.deeperthan1(tree):
            tree.name = tree.label
        for c in tree.children:
            c = self.print_tree_label(c)
        return tree
