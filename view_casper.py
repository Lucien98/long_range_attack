import networkx as nx
from update_miner_data import get_field
from long_range_attack import miners
import pygraphviz
import matplotlib.pyplot as plt
import random
import pymysql

def miner_view(miner_id):
	blocks = []
	finalized = []
	if miner_id in miners['attacker']:
		processed = get_field(miner_id, 0, 'processed')
		for block_hash in processed:
			blocks.append(str(block_hash))
		processed = get_field(miner_id, 1, 'processed')
		for block_hash in processed:
			blocks.append(str(block_hash))
		finalized = get_field(miner_id, 0, 'finalized')
		finalized += get_field(miner_id, 1, 'finalized')
	else:
		processed = get_field(miner_id, 0, 'processed')
		for block_hash in processed:
			blocks.append(str(block_hash))
		finalized = get_field(miner_id, 0, 'finalized')
	blocks = str(blocks)
	blocks = blocks.replace("[","(")
	blocks = blocks.replace("]",")")
	sql_get_block_info = "select hash, pre_hash, is_in_attack_chain, type, height"\
		" from block where hash in " + blocks + " ;"
	db = pymysql.connect("localhost", "root", "root", "attack_casper")
	cur = db.cursor()
	cur.execute(sql_get_block_info)
	result = cur.fetchall()
	db.commit()
	cur.close()
	db.close()
	
	G = nx.DiGraph()
	for item in result:
		hash = item[0]
		pre_hash = item[1]
		height = item[4]
		if int(hash) in finalized:
			G.add_node(hash, object = ['finalized',height])
		else:
			G.add_node(hash, object = [item[3],height])#item[3]是字符串类型,type
		if hash != pre_hash:
			G.add_edge(hash, pre_hash, object = item[2])#item[2]是int型,is_in_attack_chain
	return G

def plot_miner_view(miners, image_file):
	num_miners = len(miners)

	nrows = 1
	ncols = num_miners

	node_colors = []
	pos = {}
	edge_colors = []

	i = 1
	plt.figure(figsize=(14,7))
	for miner in miners:
		node_colors = []
		pos = {}
		edge_colors = []
		G = miner_view(miner)
		for node in G.nodes():
			if G.nodes()[node]['object'][0] == 'stale':
				color = 'g'
			elif G.nodes()[node]['object'][0] == 'regular':
				color = 'r'
			else:
				color = 'b'
			node_colors.append(color)

			height = G.nodes()[node]['object'][1]
			pos[node] = (random.gauss(0, 1), height)
		for edge in G.edges():
			if G.edges()[edge]['object'] == 1:
				color = 'g'
			else:
				color = 'r'
			edge_colors.append(color)

		ax = plt.subplot(nrows, ncols, i)
		i = i + 1
		ax.set_title("Miner %d" % miner)
		ax.spines['top'].set_visible(False)
		ax.spines['right'].set_visible(False)
		ax.spines['bottom'].set_visible(False)
		ax.spines['left'].set_visible(False)
		pos = nx.drawing.nx_agraph.pygraphviz_layout(G, prog='dot')
		nx.draw_networkx_nodes(G, pos, None, 10, node_colors, 'o', 1.0)
		nx.draw_networkx_edges(G, pos, None, 1.0, edge_colors, 'solid', alpha=1.0,arrows = False)
	plt.savefig(image_file)
	plt.close()
