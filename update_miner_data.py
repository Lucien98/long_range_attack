import pymysql
from long_range_attack import miners

def get_field(miner_id, is_in_attack_chain, field):
	sql_field = "select " + field + " from miners where id = "\
		+ str(miner_id) + ";"
	db = pymysql.connect("localhost", "root", "root", "attack_casper")
	cur = db.cursor()
	cur.execute(sql_field)
	res = cur.fetchall()
	db.commit()
	cur.close()
	db.close()

	value = res[0][0]
	if miner_id not in miners['honest']:
		value = value.split(";")[is_in_attack_chain]
	return eval(value)


def update_field(miner_id, is_in_attack_chain, field, new_value):
	if miner_id in miners['attacker']:
		ano_half = get_field(miner_id, 1 - is_in_attack_chain, field)
		new_value = str(ano_half) + ";" + str(new_value) \
			if is_in_attack_chain else str(new_value) + ";" + str(ano_half)
	else:
		new_value = str(new_value)
	sql_update_field = "update miners set " + field + \
		" = \"" + new_value + "\" where id = " + str(miner_id) + ";"
	
	db = pymysql.connect("localhost", "root", "root", "attack_casper")
	cur = db.cursor()
	cur.execute(sql_update_field)
	db.commit()
	cur.close()
	db.close()

def get_block_field(hash,field):
	sql = "select " + field + " from block where hash = '" + str(hash) + "';"
	db = pymysql.connect("localhost", "root", "root", "attack_casper")
	cur = db.cursor()
	cur.execute(sql)
	res = cur.fetchall()[0][0]
	db.commit()
	cur.close()
	db.close()

	return res

def update_msg_time(miner_id, hash):
	sql = "update msg_receival set receive_time = 0 where miner_id = "\
		+ str(miner_id) + " and msg_id = '" + str(hash) + "';"
	db = pymysql.connect("localhost", "root", "root", "attack_casper")
	cur = db.cursor()
	cur.execute(sql)
	db.commit()
	cur.close()
	db.close()

def get_vote_field(hash,field):
	sql = "select " + field + " from vote where hash = '" + str(hash) + "';"
	db = pymysql.connect("localhost", "root", "root", "attack_casper")
	cur = db.cursor()
	cur.execute(sql)
	res = cur.fetchall()[0][0]
	db.commit()
	cur.close()
	db.close()

	return res
