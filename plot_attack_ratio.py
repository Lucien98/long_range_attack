import pymysql
import matplotlib.pyplot as plt

db = pymysql.connect("localhost", "root", "root", "attack")
cur = db.cursor()
"""获取攻击链中攻击者的权益变化"""

sql_head="""select hash from block 
where accu_regular_num = 
	(select max(accu_regular_num) from block where is_in_attack_chain = 1) 
and height = 
		(select max(height) from 
					(select hash,height from block where accu_regular_num = 
								(select max(accu_regular_num)
								from block where is_in_attack_chain = 1)
					)C
		)
and is_in_attack_chain = 1;"""
cur.execute(sql_head)
hash = cur.fetchall()[0][0]
#print(res)

ratio_list_attack = []
time_attack = []
sql_parent = "select pre_hash,attacker_ratio,N from block where hash = '" + str(hash) + "';"
cur.execute(sql_parent)
res = cur.fetchall()[0]
pre_hash = res[0]
attacker_ratio = float(res[1])
N = res[2]
ratio_list_attack.append(attacker_ratio)
time_attack.append(N)
while pre_hash != hash:
	hash = pre_hash
	sql_parent = "select pre_hash,attacker_ratio,N from block where hash = '" + str(hash) + "';"
	cur.execute(sql_parent)
	res = cur.fetchall()[0]
	pre_hash = res[0]
	attacker_ratio = float(res[1])
	N = res[2]
	ratio_list_attack.append(attacker_ratio)
	time_attack.append(N)
print(time_attack)
print(ratio_list_attack)

sql_head="""select hash from block 
where accu_regular_num = 
	(select max(accu_regular_num) from block where is_in_attack_chain = 0) 
and height = 
		(select max(height) from 
					(select hash,height from block where accu_regular_num = 
								(select max(accu_regular_num)
								from block where is_in_attack_chain = 0)
					)C
		)
and is_in_attack_chain = 0;"""
cur.execute(sql_head)
hash = cur.fetchall()[0][0]
#print(res)

ratio_list_honest = []
time_honest = []
sql_parent = "select pre_hash,attacker_ratio,N from block where hash = '" + str(hash) + "';"
cur.execute(sql_parent)
res = cur.fetchall()[0]
pre_hash = res[0]
honest_ratio = float(res[1])
N = res[2]
ratio_list_honest.append(1 - honest_ratio)
time_honest.append(N)
while pre_hash != hash:
	hash = pre_hash
	sql_parent = "select pre_hash,attacker_ratio,N from block where hash = '" + str(hash) + "';"
	cur.execute(sql_parent)
	res = cur.fetchall()[0]
	pre_hash = res[0]
	honest_ratio = float(res[1])
	N = res[2]
	ratio_list_honest.append(1 - honest_ratio)
	time_honest.append(N)
print(time_honest)
print(ratio_list_honest)


plt.plot(time_attack,ratio_list_attack,label='attacker ratio in attack chain',linewidth=3,color='r',marker='o',
	markerfacecolor='blue',markersize=12)
plt.plot(time_honest,ratio_list_honest,label='honest ratio in honest chain',linewidth=3,color='r',marker='o',
	markerfacecolor='green',markersize=12)
plt.legend()
plt.show()