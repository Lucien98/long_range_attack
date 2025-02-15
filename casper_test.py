from attack_casper import generate_validators
from attack_casper import init
from attack_casper import propose_block
from attack_casper import msg_rcv
from attack_casper import check_head
from attack_casper import accept_block
from attack_casper import on_receive
from attack_casper import maybe_vote_last_checkpoint
from attack_casper import brdcst_atk_bv

from update_miner_data import update_msg_time
from parameters import *
from view_casper import plot_miner_view

import os
import pymysql
import sys
import time
def is_not_succeed():
	sql_is_succeed = "select (select max(accu_regular_num) from block "\
		+"where is_in_attack_chain = 1 or is_in_attack_chain = 2) " \
		+"<= (select max(accu_regular_num) from block " \
		+ "where is_in_attack_chain = 0 or is_in_attack_chain = 2);"	
	db = pymysql.connect("localhost", "root", "root", "attack_casper")
	cur = db.cursor()
	cur.execute(sql_is_succeed)
	res = cur.fetchall()[0][0]
	db.commit()
	cur.close()
	db.close()

	return res


if len(sys.argv) == 1:
	start_time = time.time()
	init()
	N = 0
	while is_not_succeed():
		msg_rcv(N)
		propose_block('honest', N)
		propose_block('attack', N)
		N = N + 1
	print("")
	print("")
	print(N)
	print("")
	print("")
	
	for M in range(N,N + 50):
		brdcst_atk_bv(M*Block_Proposal_Time)
		msg_rcv(M)
		propose_block('honest', M)
		propose_block('attack', M)
		# filename = os.path.join(LOG_DIR, "honest{}.png".format(M))
		# plot_miner_view(miners['honest'], filename)
		# filename = os.path.join(LOG_DIR, "attacker{}.png".format(M))
		# plot_miner_view(miners['attacker'], filename)
	print("Took {} seconds for one simulation ".format(time.time()-start_time))
else:
	LOG_DIR = "ac_simu\simu{}".format(sys.argv[1])
	if not os.path.exists(LOG_DIR):
		os.makedirs(LOG_DIR)

	miners['honest'] = eval(sys.argv[2])
	miners['attacker'] = eval(sys.argv[3])
	filename = os.path.join(LOG_DIR, "honest_final.png")
	plot_miner_view(miners['honest'], filename)
	filename = os.path.join(LOG_DIR, "attacker_final.png")
	plot_miner_view(miners['attacker'], filename)
