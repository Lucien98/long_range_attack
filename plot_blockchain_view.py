import networkx as nx
from long_range_attack import get_processed
from long_range_attack import miners
import pygraphviz
import matplotlib.pyplot as plt
import random
import pymysql
import pdb

def miner_view(miner_id):
	blocks = []
	#pdb.set_trace()
	if miner_id in miners['attacker']:
		processed = get_processed(miner_id, 0)
		for block_hash in processed:
			blocks.append(str(block_hash))
		#pdb.set_trace()
		processed = get_processed(miner_id, 1)
		for block_hash in processed:
			blocks.append(str(block_hash))
	else:
		processed = get_processed(miner_id, 0)
		for block_hash in processed:
			blocks.append(str(block_hash))
	
	blocks = str(blocks)
	blocks = blocks.replace("[","(")
	blocks = blocks.replace("]",")")
	sql_get_block_info = "select hash, pre_hash, is_in_attack_chain, type, height"\
		" from block where hash in " + blocks + " ;"
	db = pymysql.connect("localhost", "root", "root", "attack")
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
		G.add_node(hash, object = [item[3],height])#item[3]是字符串类型,type
		if hash != pre_hash:
			G.add_edge(hash, pre_hash, object = item[2])#item[2]是int型,is_in_attack_chain
	#pdb.set_trace()
	assert G.number_of_nodes() == G.number_of_edges() + 1, "Something Wrong! "
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
			else:
				color = 'r'
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
