import long_range_attack 
from parameters import *
from plot_blockchain_view import plot_miner_view
import os
import pymysql

def is_not_succeed():
	sql_is_succeed = "select (select max(accu_regular_num) from block "\
		+"where is_in_attack_chain = 1 or is_in_attack_chain = 2) " \
		+"<= (select max(accu_regular_num) from block " \
		+ "where is_in_attack_chain = 0 or is_in_attack_chain = 2);"	
	db = pymysql.connect("localhost", "root", "root", "attack")
	cur = db.cursor()
	cur.execute(sql_is_succeed)
	#import pdb; pdb.set_trace()
	res = cur.fetchall()[0][0]
	db.commit()
	cur.close()
	db.close()

	return res

#long_range_attack.init()
N = 0
while is_not_succeed():
	long_range_attack.process_block(N)
	for miner in range(0, Num_miners):
		long_range_attack.propose_block('honest', miner, N)
		long_range_attack.propose_block('attack', miner, N)
	N = N + 1

LOG_DIR = "plot"
if not os.path.exists(LOG_DIR):
	os.makedirs(LOG_DIR)
filename = os.path.join(LOG_DIR, "honest.png")
plot_miner_view([0,2,4], filename)
filename = os.path.join(LOG_DIR, "attacker.png")
plot_miner_view([1,3,8], filename)
