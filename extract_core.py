"""
a script to compute the core

the core consists of nodes that were the top contributors of activity
across time

we need to be careful and normalize somehow by the total activity we have
per interval
"""

import sys, os
import polarlib.file_utils as file_utils
import polarlib.polar_utils as polar_utils
import polarlib.math_utils as math_utils
import polarlib.network_utils as network_utils
import argparse
import json
import re
import networkx as nx

PERIOD_THRESHOLD = 45 # how many months active

def find_core(topic_networks_folder, period_threshold):
	active_intervals_of_nodes = {}

	for filename in os.listdir(topic_networks_folder):

		try:

			pattern = "".join([args.granularity, "([0-9]+)$"])
			match = re.search(pattern, filename)

			if match is not None:

				print("[find_core] At filename:", filename)
				
				num = match.group(1) # the id of the interval

				network_str = "/".join([topic_networks_folder, filename])

				full_network = file_utils.load_network_from_file(network_str,
					is_directed = True)

				for node in full_network:

					active_intervals_of_nodes[node] = 1 + active_intervals_of_nodes.get(node, 0)

			else:
				print("[find_core] Skipped file:", filename)


		except Excpeption as e:
			raise e

	max_period = max(active_intervals_of_nodes.values())
	print("[find_core] Maximum active period in data is", max_period)

	core_set = set()
	for node, period_length in active_intervals_of_nodes.items():
		if period_length >= period_threshold:
			core_set.add(node)

	return core_set


if __name__ == '__main__' :

	# parse arguments

	parser = argparse.ArgumentParser()
	# parser.add_argument('kind', choices = ['retweets'], # only retweets are allowed!
	# 	default = 'retweets',
	# 	help = 'What kind of networks to analyze.')
	parser.add_argument('topic', help = 'keyword defining the topic')
	parser.add_argument('granularity', choices = ['month'], # only month is allowed!
		help = 'Granularity.')
	parser.add_argument('--core', action = 'store_true',
		help = 'Perform analysis only core')
	parser.add_argument('--period', '-p', type = int,
		default = PERIOD_THRESHOLD,
		help = 'Active period in months')
	parser.add_argument('-o', '--output_folder',
		default = 'data/cores',
		help = 'Folder where to store results.')

	args = parser.parse_args()

	side_1_file = "".join(['data/twitter_under_stress/communities/',
		args.topic,'/liberals_full.txt'])
	side_1 = file_utils.load_side_from_file(side_1_file)

	side_2_file = "".join(['data/twitter_under_stress/communities/',
		args.topic,'/conservatives_full.txt'])
	side_2 = file_utils.load_side_from_file(side_2_file)

	output_filename = ".".join((["core"] if args.core else []) + [args.topic, "core"])
	output_path = '/'.join([args.output_folder, output_filename])


	# go over networks
	ALL_RT_NETWORKS_FOLDER = 'data/twitter_under_stress/networks'
	ALL_RE_NETWORKS_FOLDER = 'data/twitter_under_stress/reply_networks'


	# these networks are constructed from both the 1% sample and the 
	# twitter crawl
	topic_rt_networks_folder = "/".join([ALL_RT_NETWORKS_FOLDER, args.topic])
	topic_re_networks_folder = "/".join([ALL_RE_NETWORKS_FOLDER, args.topic])

	rt_core = find_core(topic_rt_networks_folder, args.period)
	re_core = find_core(topic_re_networks_folder, args.period)

	union_core = rt_core | re_core

	print("Will output {} nodes in: {}".format(len(union_core), output_path))
	with open(output_path, 'w') as out:
		for node in union_core:
				if node in side_1:
					print(node, 1, sep = ',', file = out)
				elif node in side_2:
					print(node, 2, sep = ',', file = out)

