#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Senzing starter-kit prototype
graph viz code
by Jeff Butcher
"""


import json
import pathlib

from networkx.readwrite import json_graph
from pyvis.network import Network
import networkx as nx


# load the json graph for source and senzing
export_path: pathlib.Path = pathlib.Path("./")
sz_graph = json_graph.node_link_graph(json.load(open(export_path / "senzing_graph.json")))
src_graph = json_graph.node_link_graph(json.load(open(export_path / "source_graph.json")))


def pyv_add_node(net, n, d):
    alert_sources = ("OPEN-SANCTIONS",)
    title = n

    for attr in [x for x in d if x not in ("label", "title", "color", "shape")]:
        if isinstance(d[attr], list):
            for val in d[attr]:
                title += f"\n{attr}: {val}"
        else:
            title += f"\n{attr}: {d.get(attr)}"        

    if d.get("node_type")  == "PERSON":
        node_shape = "dot"
    else:
        node_shape = "square"

    if d.get("node_class") == "ENTITY":
        node_color = "purple"
    elif d.get("data_source", "unknown") in alert_sources:
        node_color = "red"
    else:
        node_color = "blue"
    
    d["label"] = d.get("node_name", n)
    d["title"] = title
    d["color"] = node_color
    d["size"] = min(50 + d.get("record_count", 0) * 10, 100) if d.get("node_class") == "ENTITY" else 50
    d["shape"] = node_shape
    
    net.add_node(n, **d)


def pyv_add_edge(net, u, v, d):
    edge_style = "-"

    if d.get("edge_type") == "Resolved To":
        edge_color = "purple"
    elif d.get("edge_type") == "Possible Match":
        edge_color = "gray"
    elif d.get("edge_type") == "Possibly Related":
        edge_color = "gray"
        edge_style = "."
    elif d.get("edge_type") == "Disclosed":
        edge_color = "blue"
    else:
        edge_color = "black"

    d["label"] = d.get("edge_type")
    d["title"] = d.get("edge_details") if d.get("edge_details") else "first in entity"
    d["color"] = edge_color
    #d["style"] = edge_style
    
    net.add_edge(u, v, **d, physics=False)


def pyv_add_nodes_and_edges(node_id, edge_class = None):
    node_list = []

    for u, v, d in sz_graph.in_edges(node_id, data=True):
        if not edge_class or d.get("edge_class") == edge_class:
            node_list.append(u)
            pyv_add_node(net, u, sz_graph.nodes[u])
            pyv_add_edge(net, u, v, d)
    
    for u, v, d in sz_graph.out_edges(node_id, data=True):
        if not edge_class or d.get("edge_class") == edge_class:
            node_list.append(v)
            pyv_add_node(net, v, sz_graph.nodes[v])
            pyv_add_edge(net, u, v, d)

    return node_list



if __name__ == "__main__":
    # add the source nodes and edges to the senzing graph
    for n, d in src_graph.nodes(data=True):
        sz_graph.add_node(n, **d)

    for u, v, d in src_graph.edges(data=True):
        sz_graph.add_edge(u, v, **d)

    net = Network(height="1000px", width="100%", notebook=False, directed=True)
    net.repulsion(node_distance=200, spring_length=200)

    #primary_node_id = "SENZING:1"
    #primary_node_id = "SENZING:89" # Natixis
    primary_node_id = "SENZING:84" # Abassin Badshah
    #primary_node_id = "SENZING:103" # james elliot

    pyv_add_node(net, primary_node_id, sz_graph.nodes[primary_node_id])
    related_entity_list = pyv_add_nodes_and_edges(primary_node_id, "Derived")

    net.show("entity_graph.1.html", notebook=False)


    # add resolved records
    resolved_record_list = pyv_add_nodes_and_edges(primary_node_id, "Resolved")

    for node_id in related_entity_list:
        record_list = pyv_add_nodes_and_edges(node_id, "Resolved")
        resolved_record_list.extend(record_list)

    net.show("entity_graph.3.html", notebook=False)


    ## add disclosed relationships between records
    for node_id in resolved_record_list:
        record_list = pyv_add_nodes_and_edges(node_id, "Disclosed")

    net.show("entity_graph.4.html", notebook=False)


    ## only show the data records and their disclosed relationships
    net = Network(height="1000px", width="100%", notebook=False, directed=True)
    net.repulsion(node_distance=200)

    for node_id in resolved_record_list:
        pyv_add_node(net, node_id, sz_graph.nodes[node_id])

    for node_id in resolved_record_list:
        record_list = pyv_add_nodes_and_edges(node_id, "Disclosed")

    net.show("entity_graph.2.html", notebook=False)
