import graphviz
from copy import deepcopy
from collections import OrderedDict

from pycompile.parser.syntax.node import *


class Collector:

    def __init__(self):

        self.levels: dict = {

        }

        self.num_nodes = 0

        self.level_info: dict = {
            'nodes': [],
            'largest': 0,
        }

        self.grph: graphviz.Digraph = graphviz.Digraph()
        self.node_names = {}

    def collect(self, head_node: AbstractSyntaxNode):
        head_node.collect(self, 0)

    def add(self, node: AbstractSyntaxNode, level):
        if level not in self.levels.keys():
            self.levels[level] = deepcopy(self.level_info)

        self.levels[level]['nodes'].append(node)
        self.num_nodes += 1


    def create_array_repr(self):
        for key, level_dict in self.levels.items():
            level_dict['largest'] = max([len(node.as_array()) for node in level_dict['nodes']])
        lines = []

        current_idx = 0
        for k, key in enumerate(sorted(list(self.levels.keys()), reverse=True)):
            req_size = self.levels[key]['largest']
            for i, node in enumerate(self.levels[key]['nodes']):
                arr_rep = node.as_array()
                longest = max([len(l) for l in arr_rep])
                missing = req_size - len(arr_rep)
                arr_rep = arr_rep[:-1] + ['' for i in range(missing)] + [arr_rep[-1]]
                close = ' ' + ('-' * (longest + 2)) + ' '
                arr_rep = [close] + arr_rep[-1::-1] + [close]
                for j, line in enumerate(arr_rep):
                    if j not in [0, len(arr_rep) - 1]:
                        right_pad = (longest - len(line)) * ' '

                        line = f'| {line}{right_pad} |'
                    mid_pad = '  ' if i > 0 else ''
                    line = f'{mid_pad}{line}'
                    if i == 0:
                        lines.append(line)
                    else:
                        lines[current_idx + j] += line
            links = self.get_linkages(key)
            lines += links
            current_idx += req_size + len(links) + 2
        return lines[-1::-1]

    def get_linkages(self, level):
        if level == 0:
            return []
        # else:
        #     return ['','']

        # parents
        parents = []
        child_inf = self.gen_level_info(level)
        par_inf = self.gen_level_info(level - 1)
        links = OrderedDict()
        for k in par_inf.keys():
            links[k] = []
        child_links = OrderedDict()

        for i, node in enumerate(self.levels[level]['nodes']):
            for j, pot_parent in enumerate(self.levels[level - 1]['nodes']):
                if pot_parent.is_child(node):
                    if all([pot_parent != p for p in parents]):
                        parents.append(pot_parent)
                    links[pot_parent.unique_id].append(node.unique_id)
                    child_links[node.unique_id] = pot_parent.unique_id

        link_mid = -1
        for i, (cid, pid) in enumerate(child_links.items()):
            # look for the middle point
            if child_inf[cid]['middle'] > par_inf[pid]['middle']:
                link_mid = (i, cid)

        num_link_lines = len(set(v for v in child_links.values())) + 4
        num_link_lines = num_link_lines if num_link_lines == 8 else 8
        lines = []
        joined_middles = OrderedDict()
        for i in range(num_link_lines):
            if i == 0:
                line = ''
                last_idx = 0
                for k, v in child_inf.items():
                    num_spaces = (v['middle'] - 1) - last_idx
                    spaces = num_spaces * ' '
                    line += spaces + "|"
                    last_idx = v['middle']
                lines.append(line)
            elif i == 1:
                line = ''
                last_idx = 0
                for k, v in links.items():
                    if len(v) > 1:
                        new_mid = 0
                        for j, cid in enumerate(v):
                            new_mid += child_inf[cid]['middle']
                            if j == 0:
                                num_spaces = child_inf[cid]['middle'] - last_idx
                                spaces = num_spaces * ' '
                                line += spaces
                                last_idx = child_inf[cid]['middle']
                            else:
                                num_dashes = (child_inf[cid]['middle'] - 1) - last_idx
                                line += num_dashes * '-'
                                last_idx = child_inf[cid]['middle'] - 1
                        mid = int( new_mid / len(v) )
                        joined_middles[k] = mid
                        if mid > par_inf[k]['middle']:
                            link_mid = k
                    elif len(v) == 1:
                        cid = v[0]
                        joined_middles[k] = child_inf[cid]['middle']
                        num_spaces = child_inf[cid]['middle'] - last_idx - 1
                        spaces = num_spaces * ' '
                        line += spaces + "|"
                        last_idx = child_inf[cid]['middle']

                lines.append(line)
            elif i == 2:
                line = ''
                last_idx = 0
                for k, v in joined_middles.items():
                    num_spaces = v - 1 - last_idx
                    line += (num_spaces * ' ') + '|'
                    last_idx = v

                lines.append(line)
            elif i == num_link_lines - 1:
                line = ''
                last_idx = 0
                for k, v in par_inf.items():
                    if k in child_links.values():
                        num_spaces = (v['middle'] - 1) - last_idx
                        spaces = num_spaces * ' '
                        line += spaces + "|"
                        last_idx = v['middle']
                lines.append(line)
            elif i == 3:
                line = ''
                last_idx = 0
                for j, (_, v) in enumerate(joined_middles.items()):
                    as_str = str(j)
                    rem = int(len(as_str) / 2)
                    num_spaces = (v - rem - 1) - last_idx
                    line += (num_spaces * ' ') + as_str
                    last_idx = v + rem
                lines.append(line)
            elif i == num_link_lines - 2:
                line = ''
                last_idx = 0
                for j, (k, _) in enumerate(joined_middles.items()):
                    as_str = str(j)
                    rem = int(len(as_str) / 2)
                    num_spaces = par_inf[k]['middle'] - last_idx - rem - 1
                    line += (num_spaces * ' ') + as_str
                    last_idx = par_inf[k]['middle'] + rem
                lines.append(line)

            else:
                lines.append('')


        return lines

    def gen_level_info(self, level):
        level_inf = OrderedDict()
        lens = []
        for i, node in enumerate(self.levels[level]['nodes']):
            level_inf[node.unique_id] = {'middle': None, 'len': None, 'row_len': None}
            nlen = node.node_length_as_str()
            row_len = sum(lens) + (2 * len(lens))
            lens.append(nlen)
            level_inf[node.unique_id]['middle'] = row_len + int(nlen / 2)
            level_inf[node.unique_id]['len'] = nlen
            level_inf[node.unique_id]['row_len'] = row_len
        return level_inf




