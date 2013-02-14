#!/usr/bin/env python
#
# Copyright 2013 Paul Sokolovsky
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

#
# Please note that unlike xdot module, this application is licensed
# under GPLv3, not LGPLv3.
#

import sys
from pprint import pprint

import gtk

import xdot


def is_hidden(graph, node):
    return graph.get(node, {}).get("hide", False)

def graph2dot(graph):
    res = "digraph G {\n"
    for n, meta in graph.iteritems():
        if meta.get("hide", False):
            continue
        res += n + " " + meta.get("attrs", "") + "\n"
        for dst in meta.get("edges_to", []):
            if not is_hidden(graph, dst):
                res += "%s -> %s\n" % (n, dst)
    return res + "}\n"

def dot2graph(dot):
    graph = {}
    first = True
    for l in dot:
        if first:
            first = False
            continue
        l = l.strip()
        if l[-1] == ";":
            l = l[:-1]
        if l == "}":
            break
        if "->" in l:
            src, dst = [x.strip() for x in l.split("->", 1)]
            graph.setdefault(src, {}).setdefault("edges_to", []).append(dst)
            graph.setdefault(dst, {})
        else:
            n, attrs = l.split("[", 1)
            attrs = "[" + attrs
            graph.setdefault(n, {})["attrs"] = attrs
    return graph


def subgraph(graph, node, newgraph={}):
    newgraph[node] = graph[node]
    for n in graph[node].get("edges_to", []):
        subgraph(graph, n, newgraph)


class ViewerDotWidget(xdot.DotWidget):

    def __init__(self):
        xdot.DotWidget.__init__(self)
        self.main_graph = None

    def set_graph(self, graph):
        if self.main_graph is None:
            self.main_graph = graph
        self.view_graph = graph
        self.set_dotcode(graph2dot(graph))

    def re_render(self):
        self.set_graph(self.view_graph)

    @staticmethod
    def make_menu(items, obj, handler):
        menu = gtk.Menu()
        for i in items:
            menu_item = gtk.MenuItem(i)
            menu.append(menu_item)
            menu_item.show()
            menu_item.connect("activate", handler, (i, obj))
        return menu

    def on_click(self, element, event):

        if event.button == 3:
            print "right clicked:", element

            if not element:
                def menu_handler(widget, data):
                    print widget, data
                    action, el = data
                    if action == "Unhide all":
                        for n in self.view_graph.itervalues():
                            n["hide"] = False
                        self.re_render()
                    if action == "Back to whole":
                        self.set_graph(self.main_graph)

                menu = self.make_menu(["Unhide all", "Back to whole"], None, menu_handler)

            else:
                def menu_handler(widget, data):
                    print widget, data
                    action, el = data
                    if action == "Hide":
                        self.view_graph[el.id]["hide"] = True
                        self.re_render()
                    elif action == "Collapse":
                        n = self.view_graph[el.id]
                        n["edges_to.hide"] = n["edges_to"]
                        n["edges_to"] = []
                        self.re_render()
                    elif action == "Uncollapse":
                        n = self.view_graph[el.id]
                        n["edges_to"] = n["edges_to.hide"]
                        del n["edges_to.hide"]
                        self.re_render()
                    elif action == "Subgraph":
                        new = {}
                        subgraph(self.view_graph, el.id, new)
                        self.set_graph(new)

                node = self.view_graph[element.id]
                items = ["Hide"]
                if "edges_to.hide" in node:
                    items.append("Uncollapse")
                else:
                    items.append("Collapse")
                items.append("Subgraph")
                menu = self.make_menu(items, element, menu_handler)

            menu.popup(None, None, None, event.button, event.time)
            return True


class MyDotWindow(xdot.DotWindow):

    def __init__(self):
        xdot.DotWindow.__init__(self, widget=ViewerDotWidget())


# Example of graph representation
graph = {
    "Hello": {"attrs": '[URL="http://en.wikipedia.org/wiki/Hello"]', "edges_to": ["World"]},
    "World": {"attrs": '[URL="http://en.wikipedia.org/wiki/World"]', "edges_to": ["foo"], "hide": False},
    "foo": {"attrs": "[foo=1]", "hide": False},
    "baz": {"attrs": "[foo=1]"},
}


def main():
    window = MyDotWindow()
    window.widget.set_graph(dot2graph(open(sys.argv[1])))
    window.widget.zoom_to_fit()
    window.connect('destroy', gtk.main_quit)
    gtk.main()


if __name__ == '__main__':
    main()
