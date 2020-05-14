from long_range_attack import partition
from parameters import *
from long_range_attack import miners
from long_range_attack import broadcast
from update_miner_data import update_field
from update_miner_data import get_field
from update_miner_data import get_block_field
from update_miner_data import update_msg_time
from get_voting_power import write_txt
from get_voting_power import read_txt

import random
import pymysql
import pdb

stake = []
voting_power_honest = []
voting_power_attack = []
stake = \
	[0.28888417, 0.0820192, 0.06432365, 0.11630922, \
	0.12024268, 0.13770893, 0.01833147, 0.02759777, \
	0.05940994, 0.08517291]
for item in stake:
	voting_power_honest.append(item)
	voting_power_attack.append(item)

deposit_honest = deposit_attack = {1: 0.0410096, 2: 0.032161825, 3: 0.05815461, 4: 0.06012134, 6: 0.009165735, 7: 0.013798885, 8: 0.02970497, 9: 0.042586455}#{}
validator = [1, 2, 3, 4, 6, 7, 8, 9]#[]

"""产生weighted验证者，其中以某一比例产生验证者
"""
def generate_validators():
	for miner in range(0, Num_miners):
		if random.random() < Validator_ratio:
			deposit_honest[miner] = deposit_attack[miner] = \
				0.5*voting_power_attack[miner]
	for key in deposit_honest.keys():
		validator.append(key)

def init():
	hash = random.randint(1, 10**30)
	type = 'regular'
	pre_hash = hash
	height = 0
	is_in_attack_chain = 2
	accu_regular_num = 1
	attacker_ratio = 0
	epoch = 0
	for i in miners['attacker']:
		attacker_ratio = attacker_ratio + stake[i]
	sql_block = "insert into block values('" \
		+ str(hash) + "'," \
		+ "'" + str(type) + "'" + "," \
		+ "'" + str(stake) + "'" + "," \
		+ "'" + str(pre_hash) + "'" + "," \
		+       str(height)        +"," \
		+       str(is_in_attack_chain)        +"," \
		+ "'" + str(voting_power_honest) + "'" + "," \
		+       str(accu_regular_num)        +"," \
		+ "'" + str(attacker_ratio) + "'" + "," \
		+		str(epoch) + 	");" 
	sql_miners = "insert into miners values"
	for i in miners['attacker']:
		id = i
		processed = str((hash,)) + ";" + str((hash,))
		dependencies = "{};{}"
		is_attacker = 1
		current_epoch = "0;0"
		votes = "{};{}"
		justified = str([hash]) + ";" + str([hash])
		finalized = str([hash]) + ";" + str([hash])
		highest_justified_checkpoint = str(hash) + ";" + str(hash)
		tails = str({hash: hash}) + ";" + str({hash: hash})
		tail_membership = str({hash: hash}) + ";" + str({hash: hash})
		vote_count = "{};{}"
		head = str(hash) + ";" + str(hash)
		sql_miners += "(" \
			+ str(i) + "," \
			+ "'" + processed + "'" + "," \
			+ "'" + dependencies + "'" + "," \
			+ str(is_attacker) + ","\
			+ "'" + str(current_epoch) + "',"\
			+ "'" + str(votes) + "'" + ","\
			+ "'" + str(justified) + "'" + ","\
			+ "'" + str(finalized) + "'" + ","\
			+ "'" + str(highest_justified_checkpoint) + "'" + ","\
			+ "'" + str(tails) + "'" + ","\
			+ "'" + str(tail_membership) + "'" + ","\
			+ "'" + str(vote_count) + "'" + ","\
			+ "'" + str(head) + "'" + "),"
	for i in miners['honest']:
		id = i
		processed = str((hash,))
		dependencies = "{}"
		is_attacker = 0
		current_epoch = 0
		votes = "{}"
		justified = str([hash])
		finalized = str([hash])
		highest_justified_checkpoint = str(hash)
		tails = {hash: hash}
		tail_membership = {hash: hash}
		vote_count = "{}"
		head = hash
		sql_miners += "(" \
			+ str(i) + "," \
			+ "'" + processed + "'" + "," \
			+ "'" + dependencies + "'" + "," \
			+ str(is_attacker) + ","\
			+ "'" +str(current_epoch) + "',"\
			+ "'" + str(votes) + "'" + ","\
			+ "'" + str(justified) + "'" + ","\
			+ "'" + str(finalized) + "'" + ","\
			+ "'" + str(highest_justified_checkpoint) + "'" + ","\
			+ "'" + str(tails) + "'" + ","\
			+ "'" + str(tail_membership) + "'" + ","\
			+ "'" + str(vote_count) + "'" + ","\
			+ "'" + str(head) + "'" + "),"
	
	sql_miners = sql_miners[0:-1]
	sql_miners += ";"
	db = pymysql.connect("localhost", "root", "root", "attack_casper")
	cursor = db.cursor()
	#pdb.set_trace()
	cursor.execute(sql_block)
	print("生成创世块信息")
	cursor.execute(sql_miners)
	print("生成矿工信息")
	db.commit()
	cursor.close()
	db.close()

def propose_block(chain, N):
	max_voting_power = 0
	voting_power_honest = read_txt('voting_power_honest')
	voting_power_attack = read_txt('voting_power_attack')
	if chain == 'attack':
		max_voting_power = sorted(voting_power_attack,\
		 reverse=True)[0]
	if chain == 'honest':
		max_voting_power = sorted(voting_power_honest,\
		 reverse=True)[0]
	proposal_id = -1
	if chain == 'honest':
		for i in range(0, Num_miners):
			if voting_power_honest[i] == max_voting_power:
				proposal_id = i
				break
	if chain == 'attack':
		for i in range(0, Num_miners):
			if voting_power_attack[i] == max_voting_power:
				proposal_id = i
				break
	
	head_id = proposal_id
	if chain == 'attack' and proposal_id in miners['honest']:
		head_id = miners['attacker'][0]
	
	
	#pdb.set_trace()
	sql_head_hash = "select head from miners where id = "\
		+ str(head_id) + ";"
	db = pymysql.connect("localhost", "root", "root", "attack_casper")
	cur = db.cursor()
	cur.execute(sql_head_hash)
	head_hash = cur.fetchall()[0][0]
	if chain == 'attack':
		head_hash = head_hash.split(";")[1]
	if chain == 'honest' and proposal_id in miners['attacker']:
		head_hash = head_hash.split(";")[0]
	if isinstance(head_hash,str) == False:
		head_hash = str(head_hash)

	sql_get_block_info = "select hash, stake, height,\
		accu_regular_num from block where \
		hash = '" + str(head_hash) + "';"
	cur.execute(sql_get_block_info)
	res = cur.fetchall()[0]
	pre_hash = eval(res[0])
	stake = eval(res[1])
	height = res[2] + 1
	accu_regular_num = res[3]
	
	hash = random.randint(1, 10**30)
	type = ''
	is_in_attack_chain = -1
	epoch = height // EPOCH_SIZE
	if chain == 'honest':
		if proposal_id in miners['honest']:
			receiver = random.randint(0, Num_miners - 1)
			transfer_stake = stake[proposal_id] * Transfer_Ratio * random.random()
			transfer_stake = int(transfer_stake*(10**Precision))/\
								(10**Precision)
			is_copied = 0
			sql_transfer = "insert into transfer values(" \
				+ str(proposal_id) +"," \
				+ str(receiver) + "," \
				+ "'" + str(transfer_stake) + "'" + "," \
				+ str(is_copied)+");"
			stake[proposal_id] -= transfer_stake
			stake[proposal_id] = int(stake[proposal_id]*(10**Precision))/\
						(10**Precision)
			stake[receiver] += transfer_stake
			stake[receiver] = int(stake[receiver]*(10**Precision))/\
						(10**Precision)
			type = 'regular'
			is_in_attack_chain = 0
			accu_regular_num += 1
			cur.execute(sql_transfer)
		else:
			type = 'stale'
			is_in_attack_chain = 0
	if chain == 'attack':
		if proposal_id in miners['honest']:
			type = 'stale'
			is_in_attack_chain = 1
		else:
			sql_get_transfer = \
				"select * from transfer where is_copied = 0"
			cur.execute(sql_get_transfer)
			result = cur.fetchall()
			
			if len(result) != 0:
				sender = result[0][0]
				receiver = result[0][1]
				transfer_stake = int(float(result[0][2])*(10**Precision))/\
						(10**Precision)
				
				stake[sender] -= transfer_stake + Transaction_Fees
				stake[sender] = int(stake[sender]*(10**Precision))/\
						(10**Precision)
				stake[receiver] += transfer_stake
				stake[receiver] = int(stake[receiver]*(10**Precision))/\
						(10**Precision)
				sql_update_transfer = \
					"update transfer set is_copied = 1 \
					 where sender_id = " + str(sender) \
					 + " and receiver_id = " + str(receiver) \
					 + " and stake = '" + str(result[0][2]) + "';"
				cur.execute(sql_update_transfer)
			type = 'regular'
			is_in_attack_chain = 1
			accu_regular_num += 1

	voting_power = []
	if chain == 'honest':
		minus = 0
		for i in range(0, Num_miners):
			if i != proposal_id:
				voting_power_honest[i] += stake[i]
				minus += stake[i]
		voting_power_honest[proposal_id] -= minus
		for i in range(0, Num_miners):
			voting_power_honest[i] = float(("%."+str(Precision)\
				+ "f") % voting_power_honest[i])			
		voting_power = voting_power_honest
		write_txt('voting_power_honest', voting_power_honest)
	else:
		minus = 0
		for i in range(0, Num_miners):
			if i != proposal_id:
				voting_power_attack[i] += stake[i]
				minus += stake[i]
		voting_power_attack[proposal_id] -= minus
		for i in range(0, Num_miners):
			voting_power_attack[i] = float(("%."+str(Precision)\
				+ "f") % voting_power_attack[i])			
		voting_power = voting_power_attack
		write_txt('voting_power_attack', voting_power_attack)
	print("voting_power_honest: " + str(voting_power_honest))
	print("voting_power_attack: " + str(voting_power_attack))
	attacker_ratio = 0
	for id in miners['attacker']:
		attacker_ratio += stake[id]
	attacker_ratio = int(attacker_ratio*(10**Precision))/\
		(10**Precision)

	sql_block = "insert into block values('" \
		+ str(hash) + "'," \
		+ "'" + str(type) + "'" + "," \
		+ "'" + str(stake) + "'" + "," \
		+ "'" + str(pre_hash) + "'" + "," \
		+       str(height)        +"," \
		+       str(is_in_attack_chain)        +"," \
		+ "'" + str(voting_power) + "'" + "," \
		+       str(accu_regular_num)        +"," \
		+ "'" + str(attacker_ratio) + "'," \
		+ 		str(epoch) + ");"
	sql_broadcast = broadcast(chain, hash, (N+1)*Block_Proposal_Time, proposal_id)
	cur.execute(sql_block)
	print("miner "+ str(proposal_id) + " propose "+ str(N + 1) + "th block " + str(hash) + " in " + chain + " chain")
	cur.execute(sql_broadcast)
	print("this block is broadcasted by inserting some records in msg_receival table")
	db.commit()
	cur.close()
	db.close()

def msg_rcv(N):
	sql_receive_block = "select * from msg_receival "\
			"where receive_time >= " + str(N*Block_Proposal_Time)\
			+ " and receive_time < " + str((N+1)*Block_Proposal_Time) + " ;"
	db = pymysql.connect("localhost", "root", "root", 'attack_casper')
	cursor = db.cursor()
	cursor.execute(sql_receive_block)
	result = cursor.fetchall()
	db.commit()
	cursor.close()
	db.close()
	if len(result) == 0:
		return
	
	for msg in result:
		receiver = msg[0]
		type = msg[1]
		msg_hash = msg[2]# typr:str
		on_receive(receiver, type, msg_hash)
		update_msg_time(receiver, msg_hash)

def on_receive(receiver, type, msg_hash):
	if type == 'block':
		res = accept_block(receiver, msg_hash)
	else:
		res =  accept_vote(receiver, msg_hash)
	if res :
		is_in_attack_chain = get_block_field(msg_hash, 'is_in_attack_chain')
		dep = get_field(receiver, is_in_attack_chain, 'dependencies')
		if int(msg_hash) in dep.keys():
			dep = get_field(receiver, is_in_attack_chain, 'dependencies')
			for child_hash in dep[int(msg_hash)][0]:
				on_receive(receiver,'block', child_hash)
			for child_hash in dep[int(msg_hash)][1]:
				on_receive(receiver, 'vote', child_hash)
			# print("miner " + str(receiver) + " deletes " + \
			# 	str(str(hash) +":" + str(dep[int(hash)])) + "from its dependencies")
			del dep[int(msg_hash)]
			print("删除依赖")
			update_field(receiver, is_in_attack_chain, 'dependencies', dep)

def accept_block(receiver, hash):
	sql_get_block_info = "select pre_hash, is_in_attack_chain, height from "\
			+ "block where hash = '" + str(hash) +"';" 
	db = pymysql.connect("localhost", "root", "root", "attack_casper")
	cursor = db.cursor()
	
	cursor.execute(sql_get_block_info)
	res_info = cursor.fetchall()
	db.commit()
	cursor.close()
	db.close()

	pre_hash = int(res_info[0][0])
	is_in_attack_chain = res_info[0][1]
	height = res_info[0][2]

	processed = get_field(receiver, is_in_attack_chain, 'processed')
	dep = get_field(receiver, is_in_attack_chain, 'dependencies')
	
	if pre_hash not in processed:
		if pre_hash not in dep.keys():
			dep[pre_hash] = [[],[]]#依赖分为两种，一种是区块，一种是vote，第一个list记录
		dep[pre_hash][0].append(int(hash))
		update_field(receiver, is_in_attack_chain, 'dependencies', dep)
		return

	print(f"miner %d accept the block of hash {hash}" %receiver)
	
	processed = processed + (int(hash),)
	update_field(receiver, is_in_attack_chain, 'processed', processed)
	
	tail_membership = get_field(receiver, is_in_attack_chain, 'tail_membership')
	tails = get_field(receiver, is_in_attack_chain, 'tails')
	if height % EPOCH_SIZE == 0:
		tail_membership[int(hash)] = int(hash)
		tails[int(hash)] = int(hash)
		update_field(receiver, is_in_attack_chain, 'tail_membership', tail_membership )
		update_field(receiver, is_in_attack_chain, 'tails', tails)
	else:
		
		tail_membership[int(hash)] = tail_membership[pre_hash]
		update_field(receiver, is_in_attack_chain, 'tail_membership', tail_membership )
		sql_get_height = "select height from block where hash = '"\
			+ str(tails[tail_membership[int(hash)]]) + "';" 
		
		db = pymysql.connect("localhost", "root", "root", "attack_casper")
		cur = db.cursor()
		cur.execute(sql_get_height)
		tail_height = cur.fetchall()[0][0]
		db.commit()
		cur.close()
		db.close()
		if height > tail_height:
			tails[tail_membership[int(hash)]] = int(hash)
			
			update_field(receiver, is_in_attack_chain, 'tails', tails)

	check_head(receiver, hash, is_in_attack_chain)
	return True

def get_checkpoint_parent(receiver, is_in_attack_chain, hash):
	sql_block_info = "select height, pre_hash from block where hash = '" + str(hash) + "';"
	db = pymysql.connect("localhost", "root", "root", "attack_casper")
	cur = db.cursor()
	cur.execute(sql_block_info)
	res = cur.fetchall()
	db.commit()
	cur.close()
	db.close()

	height = res[0][0]
	pre_hash = res[0][1]

	tail_membership = get_field(receiver, is_in_attack_chain, 'tail_membership')
	
	print("观察height 和 tail_membership[pre_hash]的值为多少")
	if height == 0:
		return None
	return tail_membership[int(pre_hash)]

def is_ancestor(receiver, anc, desc, is_in_attack_chain):
	while True:
		if desc is None:
			return False
		if desc == anc:
			return True
		desc = get_checkpoint_parent(receiver, is_in_attack_chain, desc)

def check_head(receiver, hash, is_in_attack_chain):
	highest_justified_checkpoint_hash = get_field(receiver, is_in_attack_chain, 'highest_justified_checkpoint')
	tail_membership = get_field(receiver, is_in_attack_chain, 'tail_membership')
	
	print("观察is_ancestor函数")
	if is_ancestor(receiver, highest_justified_checkpoint_hash, \
		tail_membership[int(hash)], is_in_attack_chain):
		update_field(receiver, is_in_attack_chain, 'head', hash)
	else:
		print('Wrong chain, reset the chain to be a descendant of the '
			'highest justified checkpoint.')
		max_height = get_block_field(highest_justified_checkpoint_hash, 'height')
		max_descendant = highest_justified_checkpoint_hash
		tails = get_field(receiver, is_in_attack_chain, 'tails')
		for _hash in tails:
			if is_ancestor(receiver, highest_justified_checkpoint_hash, _hash, is_in_attack_chain):
				new_height = get_block_field(tails[_hash], 'height')
				if new_height > max_height:
					max_descendant = tails[_hash]
		update_field(receiver, is_in_attack_chain, 'head', max_descendant)

def maybe_vote_last_checkpoint(miner, hash, is_in_attack_chain):
	target_block = hash
	source_block = get_field(miner, is_in_attack_chain, 'highest_justified_checkpoint')

	target_block_epoch = get_block_field(target_block, 'height')

def accept_vote(receiver, hash):
	
