from parameters import *
from get_voting_power import write_txt
from get_voting_power import read_txt

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
	# is_in_attack_chain 字段用于判断此区块是否位于攻击链上
	# 即位于攻击链又位于诚实链的字段值为2
	# 目前由于长程攻击从创世块开始发起，故仅有前面一两块为2
	is_in_attack_chain = 2
	accu_regular_num = 1
	# 权益分配
	voting_power = stake = partition(Num_miners)#[0.28888417, 0.0820192, 0.06432365,\
	 # 0.11630922, 0.12024268, 0.13770893, 0.01833147, 0.02759777,\
	 #  0.05940994, 0.08517291]#
	write_txt('vpa_lr', voting_power)
	write_txt('vph_lr', voting_power)
	attacker_ratio = 0
	for i in miners['attacker']:
		attacker_ratio = attacker_ratio + stake[i]
	sql_block = "insert into block values('" \
		+ str(hash) + "'," \
		+ "'" + str(type) + "'" + "," \
		+ "'" + str(stake) + "'" + "," \
		+ "'" + str(pre_hash) + "'" + "," \
		+       str(height)        +"," \
		+       str(is_in_attack_chain)        +"," \
		+ "'" + str(voting_power) + "'" + "," \
		+       str(accu_regular_num)        +"," \
		+ "'" + str(attacker_ratio) + "',0" + ");" 
	sql_miners = "insert into miners values"
	for i in miners['attacker']:
		id = i
		processed = str((hash,)) + ";" + str((hash,))
		dependencies = "{};{}"
		is_attacker = 1
		sql_miners += "(" \
			+ str(i) + "," \
			+ "'" + processed + "'" + "," \
			+ "'" + dependencies + "'" + "," \
			+ str(is_attacker) + ")," 
	for i in miners['honest']:
		id = i
		processed = str((hash,))
		dependencies  = "{}"
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
		print("生成创世块信息")
		cursor.execute(sql_miners)
		print("生成矿工信息")
		db.commit()
	except:
		db.rollback()
	cursor.close()
	db.close()

def is_not_succeed():
	sql_is_succeed = "select (select max(accu_regular_num) from block "\
		+"where is_in_attack_chain = 1 or is_in_attack_chain = 2) " \
		+"<= (select max(accu_regular_num) from block " \
		+ "where is_in_attack_chain = 0 or is_in_attack_chain = 2);"	
	db = pymysql.connect("localhost", "root", "root", "attack")
	cur = db.cursor()
	cur.execute(sql_is_succeed)
	res = cur.fetchall()[0][0]
	db.commit()
	cur.close()
	db.close()
	return res

def elect_proposal(chain):
	max_voting_power = 0
	if chain == 'attack':
		voting_power = read_txt('vpa_lr')
	if chain == 'honest':
		voting_power = read_txt('vph_lr') if is_not_succeed() else read_txt('vpa_lr')
	max_voting_power = sorted(voting_power, reverse = True)[0]
	for i in range(0, Num_miners):
		if voting_power[i] == max_voting_power:
			return i

""" 获取某矿工在某链上的最高点区块hash
	returns hash of highest block 
"""
def propose_block(chain, id, N):
	#若攻击成功，则诚实链中攻击者不提出区块，因为已经没有必要在其上挖矿
	#而在攻击链轮到诚实者出块时，诚实者也不出，它会在自己的诚实链中轮到自己出块时
	#选择攻击链出块
	if not is_not_succeed():
		if chain == 'attack' and id in miners['honest'] or\
			chain == 'honest' and id in miners['attacker']:
			print("Now attack succeeds and no block was proposed at {}th slot in {} chain".format(N+1,chain))
			return
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
	processed = processed.replace(",)",")")
	processed = processed.replace("(","")
	processed = processed.replace(")","")
	if chain == 'honest':
		if id in miners['honest']:
			#诚实链中的诚实者的区块链视图
			blocks = str(processed.split(", "))

		else:
			#诚实链中的攻击者的区块链视图
			blocks = str(processed.split(";")[0].split(", "))
	else:
		#由于假设在攻击链中攻击者拥有极大优势，
		#出块之后各节点瞬间收块，瞬间接收达成共识
		#故其只需要一个节点进行出块者的计算即可
		blocks = str(processed.split(";")[1].split(", "))
	#取出accu_regular_num的最大值
	blocks = blocks.replace('[','(')
	blocks = blocks.replace(']',')')
	# 在只有创世块的时候，blocks会包含一个空串，目测对结果不产生影响
	#print(str(blocks)),exit()
	sql_max_regnum = \
		"select max(accu_regular_num) from block where hash in "\
		+ blocks + ";"
	cursor.execute(sql_max_regnum)
	max_regnum = cursor.fetchall()[0][0]
	# 选出拥有该最大值的最高区块
	sql_all_height = "select height from block where accu_regular_num = " \
		+ str(max_regnum) + " and hash in " + blocks
	sql_max_height = "select  max(height) from (" + sql_all_height + ") processed "
	sql_head = \
		"select hash, stake, height, \
		 	voting_power, accu_regular_num \
			from block where accu_regular_num = "\
			+ str(max_regnum) + " and height = (" + \
			sql_max_height + ") and hash in " + blocks
	cursor.execute(sql_head)
	result = cursor.fetchall()[0]
	pre_hash = eval(result[0]) # field pre_hash
	stake = eval(result[1]) #field stake
	height = result[2] + 1 #field height
	voting_power = eval(result[3]) #field voting_power
	accu_regular_num = result[4] #field accu_regular_num
	proposal_id = id
	hash = random.randint(1,10**30) #field hash
	type = ''
	is_in_attack_chain = -1 
	if chain == 'honest' and proposal_id == id:
		if id in miners['honest']:
			#进行股份的转移
			receiver = random.randint(0, Num_miners - 1)
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
						(10**Precision)
			type = 'regular'
			is_in_attack_chain = 0
			accu_regular_num += 1
			cursor.execute(sql_transfer)
		else:
			type = 'stale'
			is_in_attack_chain = 0
	if chain == 'attack' and proposal_id == id:
		if id in miners['honest']:
			type = 'stale'
			is_in_attack_chain = 1
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
				
				if stake[sender] - (transfer_stake + Transaction_Fees) > 0:
					stake[sender] -= (transfer_stake + Transaction_Fees)
					stake[sender] = int(stake[sender]*(10**Precision))/\
							(10**Precision)
					stake[receiver] += transfer_stake
					stake[receiver] = int(stake[receiver]*(10**Precision))/\
							(10**Precision)
					stake[id] += Transaction_Fees
					stake[id] = int(stake[id]*(10**Precision))/\
							(10**Precision)
				sql_update_transfer = \
					"update transfer set is_copied = 1 \
					 where sender_id = " + str(sender) \
					 + " and receiver_id = " + str(receiver) \
					 + " and stake = '" + str(result[0][2]) + "';"
				cursor.execute(sql_update_transfer)
			type = 'regular'
			is_in_attack_chain = 1
			accu_regular_num += 1
	#更新voting_power
	if chain == 'attack':
		voting_power = read_txt('vpa_lr')
	if chain == 'honest':
		voting_power = read_txt('vph_lr') if is_not_succeed() else read_txt('vpa_lr')
	#取消stale区块的存在，所以相应的攻击者在攻击成功前将voting_power更新就OK了
	minus = 0
	for i in range(0, Num_miners):
		if i != proposal_id:
			voting_power[i] += stake[i]
			minus += stake[i]
	voting_power[proposal_id] -= minus
	if chain == 'attack':
		write_txt('vpa_lr', voting_power)
	if chain == 'honest':
		write_txt('vph_lr', voting_power) if is_not_succeed() else write_txt('vpa_lr', voting_power)
	if is_not_succeed():
		if chain == 'attack' and id in miners['honest'] or\
			chain == 'honest' and id in miners['attacker']:
			print("Now attack is undergoing and no block was proposed at {}th slot in {} chain".format(N+1,chain))
			return		
	for i in range(0, Num_miners):
		voting_power[i] = float(("%."+str(Precision)+ "f") % voting_power[i])			
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
		+ "'" + str(attacker_ratio) + "'," + str(N) + ");"
	sql_broadcast = broadcast(chain, hash, (N+1)*Block_Proposal_Time, proposal_id)
	cursor.execute(sql_block)
	print("miner "+ str(proposal_id) + " propose "+ str(N + 1) + "th block " + str(hash) + " in " + chain + " chain")
	cursor.execute(sql_broadcast)
	print("this block is broadcasted by inserting some records in msg_receival table")
	db.commit()
	cursor.close()
	db.close()
	# return hash		

"""广播区块"""
def broadcast(chain, hash, time, proposal_id):
	sql_msg_receival = ''
	if chain == 'honest':
		sql_msg_receival = "insert into msg_receival values("\
			+ str(proposal_id) + "," \
			+ "'block'," \
			+ "'" + str(hash) + "',"\
			+ str(time+1) + "),"
		for i in range(0, Num_miners) :
			if i != proposal_id:
				delay = 1 + int(random.expovariate(1)*100)
				if delay > 1.5*EPOCH_SIZE*Block_Proposal_Time:
					delay = 1.5*EPOCH_SIZE*Block_Proposal_Time
				sql_msg_receival += "(" + str(i) + ","\
						+ "'block'," \
						+ "'" + str(hash) + "',"\
						+ str(time+delay) + "),"
	if chain == 'attack':
		if proposal_id in miners['attacker']:
			sql_msg_receival = "insert into msg_receival values("\
				+ str(proposal_id) + "," \
				+ "'block'," \
				+ "'" + str(hash) + "',"\
				+ str(time+1) + "),"
			for i in miners['attacker']:
				if i != proposal_id:
					delay = 1 + int(random.expovariate(1)*100)
					sql_msg_receival += "(" + str(i) + ","\
							+ "'block'," \
							+ "'" + str(hash) + "',"\
							+ str(time+delay) + "),"
		else:
			sql_msg_receival = "insert into msg_receival values"
			for i in miners['attacker']:
				delay = 1 + int(random.expovariate(1)*100)
				sql_msg_receival += "(" + str(i) + ","\
						+ "'block'," \
						+ "'" + str(hash) + "',"\
						+ str(time+delay) + "),"
	sql_msg_receival = sql_msg_receival[0:-1]
	sql_msg_receival += ';'
	return sql_msg_receival

def brdcst_atk_blk(time):
	sql_get_attack_blocks = "select hash from block where is_in_attack_chain = 1 and length(voting_power) != 1;"
	db = pymysql.connect("localhost", "root", "root", "attack")
	cur = db.cursor()
	cur.execute(sql_get_attack_blocks)
	res = cur.fetchall()
	blocks = ()

	if len(res) == 0:
		return
	sql_msg_receival = 'insert into msg_receival values'
	for i in range(len(res)):
		for miner in miners['honest']:
			# sql_update_block = "update block set is_in_attack_chain = 2 where hash = '" + str(res[i][0]) + "';"
			# cur.execute(sql_update_block)
			delay = 1 + int(random.expovariate(1)*300)
			sql_msg_receival += "(" + str(miner) + ","\
						+ "'block'," \
						+ "'" + str(res[i][0]) + "',"\
						+ str(time+delay) + "),"
			blocks = blocks + (str(res[i][0]),)
	blocks = str(blocks).replace(",)", ")")
	sql_update_block = "update block set voting_power = '0' where hash in " + blocks + ";"
	#print(sql_update_block)
	sql_msg_receival = sql_msg_receival[0:-1]
	sql_msg_receival += ";"

	if blocks != '()': cur.execute(sql_update_block)
	cur.execute(sql_msg_receival)
	db.commit()
	cur.close()
	db.close()


def is_attacker(miner_id):
	db = pymysql.connect("localhost", "root", "root", "attack")
	cur = db.cursor()
	sql_is_attacker = "select is_attacker from miners where id = " + str(miner_id) + ";"
	cur.execute(sql_is_attacker)
	res = cur.fetchall()[0][0]
	db.commit()
	cur.close()
	db.close()

	return int(res)

"""获取一个节点的processed视图
返回的是一个int型元组，其中元素为hash值
"""
def get_processed(miner_id, is_in_attack_chain):
	sql_processed = "select processed from miners where id =" \
			+ str(miner_id) + ";"
	db = pymysql.connect("localhost", "root", "root", "attack")
	cursor = db.cursor()
	cursor.execute(sql_processed)
	res_pro = cursor.fetchall()
	db.commit()
	cursor.close()
	db.close()
	#返回的结果是一个字符串'(1,)'，将其解析为元组之后返回
	processed = res_pro[0][0]
	if is_attacker(miner_id):
		if is_in_attack_chain:
			processed = processed.split(";")[1]
		else:
			processed = processed.split(";")[0]
	return eval(processed)

"""	更新某个节点的processed视图，
	参数包含了要更新的字段的值,其中processed是一个元组
"""
def update_processed(miner_id, is_in_attack_chain, processed):
	if miner_id in miners['attacker']:
		ano_half_view = get_processed(miner_id, 1 - is_in_attack_chain)
		if is_in_attack_chain:
			processed = str(ano_half_view) + ";" + str(processed)
		else:
			processed = str(processed) + ";" + str(ano_half_view)
	else:
		processed = str(processed)
	sql_update_processed = "update miners set processed = '"\
				+ processed + "'where id = " + str(miner_id) + ";"
	db = pymysql.connect("localhost", "root", "root", "attack")
	cursor = db.cursor()
	cursor.execute(sql_update_processed)
	db.commit()
	#db.rollback()
	cursor.close()
	db.close()

"""获取一个节点的dependencies视图
返回的是一个键为int型数据，值为int型list的字典
"""	
def get_dependencies(miner_id, is_in_attack_chain):
	sql_get_dep = "select dependencies from miners where id ="\
			+ str(miner_id) + ";"
	db = pymysql.connect("localhost", "root", "root", "attack")
	cursor = db.cursor()
	cursor.execute(sql_get_dep)
	res_dep = cursor.fetchall()
	db.commit()
	cursor.close()
	db.close()
	dep = res_dep[0][0]
	if miner_id not in miners['honest']:
		if is_in_attack_chain:
			dep = dep.split(";")[1]
		else:
			dep = dep.split(";")[0]
	return eval(dep)

def update_dependencies(miner_id, is_in_attack_chain, dep):
	if miner_id in miners['attacker']:
		ano_half_view = get_dependencies(miner_id, 1 - is_in_attack_chain)
		if is_in_attack_chain:
			dep = str(ano_half_view) + ";" + str(dep)
		else:
			dep = str(dep) + ";" + str(ano_half_view)
	else:
		dep = str(dep)
	sql_update_dep = "update miners set dependencies = \""\
				+ dep + "\" where id = " + str(miner_id) + ";"
	db = pymysql.connect("localhost", "root", "root", "attack")
	cursor = db.cursor()
	cursor.execute(sql_update_dep)
	db.commit()
	#db.rollback()
	cursor.close()
	db.close()

def on_receive(receiver, hash):
	#miners表,此处的processed应为一个由字符串解析出来的元组
	#形如字符串"1,2,3,4"解析出来的(1,2,3,4)
	sql_get_block_info = "select pre_hash, is_in_attack_chain from "\
			+ "block where hash ='" + str(hash) +"';" 
	db = pymysql.connect("localhost", "root", "root", "attack")
	cursor = db.cursor()
	cursor.execute(sql_get_block_info)
	res_info = cursor.fetchall()
	db.commit()
	cursor.close()
	db.close()

	pre_hash = int(res_info[0][0]) #res_info[0][0]是字符串类型的数据，需要转为int
	is_in_attack_chain = res_info[0][1] # 为int型数据
	processed = get_processed(receiver, is_in_attack_chain)
	dep = get_dependencies(receiver, is_in_attack_chain)
	if pre_hash in processed:
		processed = processed + (int(hash),)
		update_processed(receiver, is_in_attack_chain, processed)
		#print("miner " + str(receiver) + " adds " + str(hash) + "to its processed")
		if int(hash) in dep.keys():
			for child_hash in dep[int(hash)]:
				on_receive(receiver, child_hash)
			# print("miner " + str(receiver) + " deletes " + \
			# 	str(str(hash) +":" + str(dep[int(hash)])) + "from its dependencies")
			del dep[int(hash)]
			update_dependencies(receiver, is_in_attack_chain, dep)
			
	else:
		if pre_hash not in dep.keys():
			dep[pre_hash] = []
		dep[pre_hash].append(int(hash))
		update_dependencies(receiver, is_in_attack_chain, dep)
		# print("miner " + str(receiver) + " updates " + str(str(pre_hash) +":"\
		# 	+ str(dep[pre_hash])) + " as its dependencies" )

"""收块
Args: N 取出在[(N-1)*Block_Proposal_Time, N*Block_Proposal_Time)
	到达各节点的区块
"""
def process_block(N):
	sql_receive_block = "select * from msg_receival "\
			"where receive_time >= " + str(N*Block_Proposal_Time)\
			+ " and receive_time < " + str((N+1)*Block_Proposal_Time) + " ;"
	db = pymysql.connect("localhost", "root", "root", 'attack')
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
		block_hash = msg[2]# typr:str
		on_receive(receiver, block_hash)
miners = generate_attacker()
# miners['attacker'] = [2, 3, 6,7,8]
# miners['honest'] = [0, 1, 4, 5, 9]