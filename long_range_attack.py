from parameters import *
import pymysql
import random

# 全局变量 miners
miners = {}
"""分配stake"""
def partition(n):
	seq = [0 for i in range(0,n-1)]
	for i in range(0,n-1):
		seq[i] = random.random()
	seq.sort();
	stake = [0 for i in range(0,n)]
	stake[0] = seq[0]
	for i in range(1,n-1):
		stake[i] = seq[i] - seq[i-1]
	stake[n-1] = 1 - seq[i]
	for i in range(0,n):
		stake[i] = int(stake[i]*(10**Precision))/\
		(10**Precision)
	return stake

"""产生攻击者"""
def generate_attacker():
	miners['attacker'] = []
	miners['honest'] = []
	for i in range(0, Num_miners):
		if random.random() < Number_Ratio_of_Attackers:
			miners['attacker'].append(i)
		else:
			miners['honest'].append(i)
	return miners

""" 对协议运行进行初始化，包括对miners，以及创世块的初始化
	Args：miners字典，即攻击者与诚实者的字典
	还需要权益的分配信息，
	ie. 权益分配，角色分配
	对自己的提示：角色分配时全局要使用的信息，
	而权益分配只用于创世块
"""
def init():
	# 产生创世区块的信息
	hash = random.randint(1,10**30)
	type = 'regular'
	pre_hash = hash
	height = 0
	# is_in_attack__chain 字段用于判断此区块是否位于攻击链上
	# 即位于攻击链又位于诚实链的字段值为2
	# 目前由于长程攻击从创世块开始发起，故仅有前面一两块为2
	is_in_attack__chain = 2
	accu_regular_num = 1
	# 权益分配
	voting_power = stake = [0.28888417, 0.0820192, 0.06432365,\
	 0.11630922, 0.12024268, 0.13770893, 0.01833147, 0.02759777,\
	  0.05940994, 0.08517291]#partition(Num_miners)
	attacker_ratio = 0
	for i in miners['attacker']:
		attacker_ratio = attacker_ratio + stake[i]
	sql_block = "insert into block values('" \
		+ str(hash) + "'," \
		+ "'" + str(type) + "'" + "," \
		+ "'" + str(stake) + "'" + "," \
		+ "'" + str(pre_hash) + "'" + "," \
		+       str(height)        +"," \
		+       str(is_in_attack__chain)        +"," \
		+ "'" + str(voting_power) + "'" + "," \
		+       str(accu_regular_num)        +"," \
		+ "'" + str(attacker_ratio) + "'" + ");" 
	sql_miners = "insert into miners values"
	for i in miners['attacker']:
		id = i
		processed = str(hash) + ";" + str(hash)
		dependencies = ";"
		is_attacker = 1
		sql_miners += "(" \
			+ str(i) + "," \
			+ "'" + processed + "'" + "," \
			+ "'" + dependencies + "'" + "," \
			+ str(is_attacker) + ")," 
	for i in miners['honest']:
		id = i
		processed = str(hash)
		dependencies  = ""
		is_attacker = 0
		sql_miners += "(" \
			+ str(i) + "," \
			+ "'" + processed + "'" + "," \
			+ "'" + dependencies + "'" + "," \
			+ str(is_attacker) + ")," 
	sql_miners = sql_miners[0:-1]
	sql_miners += ";"
	# 连接数据库，将初始区块的信息
	db = pymysql.connect("localhost", "root", "root", "attack")
	cursor = db.cursor()
	try :
		cursor.execute(sql_block)
		cursor.execute(sql_miners)
		db.commit()
	except:
		db.rollback()

""" 获取某矿工在某链上的最高点区块hash
	returns hash of highest block 
"""
def propose_block(chain,id):
	#取出processed字段，查询出processed字段
	view_id = id
	if chain == 'attack':
		view_id = miners['attacker'][0]
	sql_processed = "select processed, id from miners where id =" \
			+ str(view_id) + ";"
	db = pymysql.connect("localhost", "root", "root", "attack")
	cursor = db.cursor()
	cursor.execute(sql_processed)
	processed = cursor.fetchall()[0][0]
	if chain == 'honest':
		if id in miners['honest']:
			#诚实链中的诚实者的区块链视图
			blocks = str(processed.split(","))
		else:
			#诚实链中的攻击者的区块链视图
			blocks = str(processed.split(";")[0].split(","))
	else:
		#由于假设在攻击链中攻击者拥有极大优势，
		#出块之后各节点瞬间收块，瞬间接收达成共识
		#故其只需要一个节点进行出块者的计算即可
		blocks = str(processed.split(";")[1].split(","))
	#取出accu_regular_num的最大值
	blocks = blocks.replace('[','(')
	blocks = blocks.replace(']',')')
	sql_max_regnum = \
		"select max(accu_regular_num) from block where hash in "\
		+ blocks + ";"
	cursor.execute(sql_max_regnum)
	max_regnum = cursor.fetchall()[0][0]
	# 选出拥有该最大值的最高区块
	sql_head = \
		"select hash, stake, max(height), \
		 	voting_power, accu_regular_num \
			from block where accu_regular_num = "\
			+ str(max_regnum) + ' and hash in ' + blocks + ";"
	
	cursor.execute(sql_head)
	result = cursor.fetchall()[0]
	# 取出voting_power
	pre_hash = eval(result[0])
	stake = eval(result[1])
	height = result[2]
	voting_power = eval(result[3])
	accu_regular_num = result[4]
	max_voting_power = sorted(voting_power,reverse = True)[0]
	proposal_id = -1
	for i in range(0,Num_miners):
		if voting_power[i] == max_voting_power:
			proposal_id = i
			break
	#import pdb; pdb.set_trace()
	if proposal_id != id:
		return
	hash = random.randint(1,10**30) 
	if chain == 'honest' and proposal_id == id:
		if id in miners['honest']:
			#进行股份的转移
			receiver = random.randint(0, Num_miners)
			transfer_stake = stake[id] * Transfer_Ratio * random.random()
			transfer_stake = int(transfer_stake*(10**Precision))/\
								(10**Precision)
			is_copied = 0
			sql_transfer = "insert into transfer values(" \
				+ str(id) +"," \
				+ str(receiver) + "," \
				+ "'" + str(transfer_stake) + "'" + "," \
				+ str(is_copied)+");"
			#设置当前区块的stake
			stake[id] -= transfer_stake
			stake[id] = int(stake[id]*(10**Precision))/\
						(10**Precision)
			stake[receiver] += transfer_stake
			stake[receiver] = int(stake[receiver]*(10**Precision))/\
						(10**Precision)#设置当前区块的voting_power
			minus = 0
			for i in range(0, Num_miners):
				if i != proposal_id:
					voting_power[i] += stake[i]
					minus += stake[i]
			voting_power[proposal_id] -= minus
			for i in range(0, Num_miners):
				voting_power[i] = float(("%."+str(Precision)+ "f") % voting_power[i])
			type = 'regular'
			height += 1
			is_in_attack__chain = 0
			accu_regular_num += 1
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
				+       str(is_in_attack__chain)        +"," \
				+ "'" + str(voting_power) + "'" + "," \
				+       str(accu_regular_num)        +"," \
				+ "'" + str(attacker_ratio) + "'" + ");"
			cursor.execute(sql_transfer)
			cursor.execute(sql_block)
		else:
			type = 'stale'
			height += 1
			is_in_attack__chain = 0
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
				+       str(is_in_attack__chain)        +"," \
				+ "'" + str(voting_power) + "'" + "," \
				+       str(accu_regular_num)        +"," \
				+ "'" + str(attacker_ratio) + "'" + ");"
			cursor.execute(sql_block)
	if chain == 'attack' and proposal_id == id:
		if id in miners['honest']:
			type = 'stale'
			height += 1
			is_in_attack__chain = 1
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
				+       str(is_in_attack__chain)        +"," \
				+ "'" + str(voting_power) + "'" + "," \
				+       str(accu_regular_num)        +"," \
				+ "'" + str(attacker_ratio) + "'" + ");"
			cursor.execute(sql_block)
		else:
			sql_get_transfer = \
				"select * from transfer where is_copied = 0"
			cursor.execute(sql_get_transfer)
			result = cursor.fetchall()
			
			if len(result) != 0:
				sender = result[0][0]
				receiver = result[0][1]
				transfer_stake = int(float(result[0][2])*(10**Precision))/\
						(10**Precision)
				
				#import pdb; pdb.set_trace()
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
			minus = 0
			for i in range(0, Num_miners):
				if i != proposal_id:
					voting_power[i] += stake[i]
					minus += stake[i]
			voting_power[proposal_id] -= minus
			for i in range(0, Num_miners):
				voting_power[i] = float(("%."+str(Precision)+ "f") % voting_power[i])
			type = 'regular'
			height += 1
			is_in_attack__chain = 1
			accu_regular_num += 1
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
				+       str(is_in_attack__chain)        +"," \
				+ "'" + str(voting_power) + "'" + "," \
				+       str(accu_regular_num)        +"," \
				+ "'" + str(attacker_ratio) + "'" + ");"
			cursor.execute(sql_block)
	return hash		

"""广播区块"""
def broadcast():
	
	# 接下来根据取出的区块信息进行加工区块
# miners = generate_attacker()
miners['attacker'] = [1, 3, 8]
miners['honest'] = [0, 2, 4, 8, 6, 7, 9]
# 第一部分完成了
# init()
propose_block('honest', 0)
exit()
slot = 0
while True:
	slot = slot + 1
