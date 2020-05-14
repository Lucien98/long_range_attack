def write_txt(filename, content):
	filename = filename + ".txt"
	file = open(filename, 'w')
	file.write(str(content))
	file.close()

def read_txt(filename):
	filename = filename + ".txt"
	file = open(filename)
	line = file.readline()
	file.close()
	return eval(line)

#a = read_txt('voting_power_honest')
#print(type(a))
#voting_power = eval(read_txt('voting_power_honest'))
#print(voting_power[0])
#write_txt('voting_power_attack', voting_power)